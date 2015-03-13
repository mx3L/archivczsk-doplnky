# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2013 Maros Ondrasek
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import re
import urllib2
import cookielib
import random
import urlparse
from xml.etree.ElementTree import fromstring

import util
from provider import ContentProvider

VYSIELANE_START = '<div class="archiveList preloader">'
VYSIELANE_ITER_RE = '<ul class=\"clearfix\">.+?<div class="titleBg">.+?<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)".+?<p>(?P<desc>.*?)</p>(?P<itime>\s+<i class="icon-time"></i>)?.+?</ul>'
NEVYSIELANE_START = '<div class="archiveNev">'
NEVYSIELANE_END = '<footer class="mainFooter">'
NEVYSIELANE_ITER_RE = '<li.*?><a href=\"(?P<url>[^"]+).*?title=\"(?P<title>[^"]+).*?</li>'
EPISODE_START = '<div class="episodeListing relative overflowed">'
EPISODE_END = '<div class="centered pagerDots"></div>'
EPISODE_ITER_RE = '<li[^>]*>\s+?<a href=\"(?P<url>[^"]+)\" title=\"(?P<title>[^"]+)\">\s+?<span class=\"date\">(?P<date>[^<]+)</span>(.+?)<span class=\"episode\">(?P<episode>[^0]{1}[0-9]*)</span>(.+?)</li>'
EPISODE_ITER_RE2 = '<article>.+?<a href="(?P<url>.+?)" title="(?P<title>.+?)">.+?<time.+?>(?P<date>.+?)</time>.+?</article>'
SERIES_START = EPISODE_START
SERIES_END = EPISODE_END
SERIES_START2 = '<nav class="e-pager">'
SERIES_END2 = '</nav>'
SERIES_ITER_RE = '<option(.+?)data-ajax=\"(?P<url>[^\"]+)\">(?P<title>[^<]+)</option>'
SERIES_ITER_RE2 = '<option value="(?P<id>\d+)"[^>]*>(?P<title>.+?)</option>'
TOP_GENERAL_START = '<span class="subtitle">výber toho najlepšieho</span>'
TOP_GENERAL_END = '</div>'
TOP_GENERAL_ITER_RE = '<li>\s+?<a href=\"(?P<url>[^"]+)\" title=\"(?P<title>[^"]+)\">(.+?)<img src=\"(?P<img>[^"]+)\"(.+?)</li>'
NEWEST_STATION_START = '<span class="subtitle">najnovšie videá</span>'
NEWEST_STATION_END = '<ul class="listing preloader">'
NEWEST_STATION_ITER_RE = '<option(.+?)value=\"(?P<station>[^\"]+)\"(.+?)data-ajax=\"(?P<url>[^\"]+)\">(.+?)<\/option>'
NEWEST_ITER_RE = '<li><a href=\"(?P<url>[^\"]+)\" title=\"(?P<title>[^\"]+)\"><span class=\"time\">(?P<time>[^<]+)</span>(.+?)</li>'
JOJ_FILES_ITER_RE = '<file type=".+?" quality="(?P<quality>.+?)" id="(?P<id>.+?)" label=".+?" path="(?P<path>.+?)"/>'

JOJ_URL = 'http://www.joj.sk'
JOJ_PLUS_URL = 'http://plus.joj.sk'
WAU_URL = 'http://wau.joj.sk'
SENZI_URL = 'http://senzi.joj.sk'


def clean_path(path):
    if path:
        if path[0] == '/':
            path = path[1:]
    if path:
        if path[-1] == '/':
            path = path[:-1]
    return path


def unfragment(parsed_url):
    data = list(parsed_url[0:5])
    data.append("")
    return urlparse.urlunparse(data)


class JojContentProvider(ContentProvider):
    def __init__(self, username=None, password=None, filter=None):
        ContentProvider.__init__(self, 'joj.sk', 'http://www.joj.sk/', username, password, filter)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)
        self.debugging = True

    def debug(self, text):
        if self.debugging:
            print "[DEBUG][%s] %s" % (self.name, text)

    def capabilities(self):
        return ['categories', 'resolve', '!download']

    def list(self, url):
        self.info("list %s" % url)
        if url.find("#cat#") == 0:
            self.debug("listing subcategories...")
            return self.subcategories(url[5:])
        p_url = urlparse.urlparse(url)
        url = unfragment(p_url)
        s_path = clean_path(p_url.path).split("/")

        if "joj.sk" not in p_url.netloc:
            self.error("%s is not a joj.sk url!" % (url))
            return []

        if p_url.path == "/ajax.json":
            self.debug("listing episodes data (ajax)")
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': util.substr(url, url, url.split('/')[-1])
            }
            data = util.request(url, headers)
            data = util.json.loads(data)['content']
            return self.list_episodes_data(data, 1)
        elif "post=" in p_url.fragment:
            self.debug("listing episodes data (post)")
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': util.substr(url, url, url.split('/')[-1])
            }
            sid = p_url.fragment.split("post=")[1]
            data = {"do": "archive", "series": sid}
            data = util.post(url, data, headers)
            return self.list_episodes_data(data, 2)

        elif len(s_path) == 1 and s_path[0] == "":
            if p_url.fragment == "top":
                self.debug("listing base url - top part")
                return self.list_base_page(util.request(self.base_url), top=True)
            elif p_url.fragment == "new":
                self.debug("listing base url - new part")
                return self.list_base_page(util.request(self.base_url), new=True)
            else:
                self.debug("listing base url")
                return self.list_base_page(util.request(self.base_url), top=True, new=True)
        elif len(s_path) == 1:
            if s_path[0] not in ("archiv.html", "plus-archiv.html",
                                 "wau-archiv.html", "senzi-archiv.html"):
                self.error("unsupported listing for url - %s" % url)
                return []
            if p_url.fragment == "showon":
                self.debug("listing show archive url - showon part")
                return self.list_archive_page(util.request(url), showoff=True)
            elif p_url.fragment == "showoff":
                self.debug("listing show archive url - showoff part")
                return self.list_archive_page(util.request(url), showon=True)
            else:
                self.debug("listing show archive url")
                return self.list_archive_page(util.request(url), showon=True, showoff=True)
        elif len(s_path) == 2 or len(s_path) == 3:
            req = urllib2.Request(url)
            req.add_header("User-Agent", util.UA)
            resp = urllib2.urlopen(req)
            p_url2 = urlparse.urlparse(resp.geturl())
            page = resp.read()
            s_path = clean_path(p_url2.path).split("/")
            if len(s_path) == 2 and s_path[0] == "archiv":
                m = re.search(r'<li>[^<]+<a href="([^"]+)"\s+title="Archív".+?</li>', page, re.DOTALL)
                url = 'http://' + p_url2.netloc + m.group(1)
                self.debug("new url = %s" % url)
                page = util.request(url)
            if p_url.fragment == "episodes":
                self.debug("listing show url - episodes part")
                return self.list_show_page(url, page, episodes=True)
            elif p_url.fragment == "seasons":
                self.debug("listing show url - seasons part")
                return self.list_show_page(url, page, seasons=True)
            elif p_url.fragment == "season_episode":
                self.debug("listing show url - seasons/episodes")
                result = self.list_show_page(url, page, seasons=True)
                if len(result) == 0:
                    result = self.list_show_page(url, page, episodes=True)
                return result
            else:
                self.debug("listing show url")
                return self.list_show_page(url, page, seasons=True, episodes=True)
        else:
            self.error("unsupported listing for url - %s" % url)
            return []

    def categories(self):
        result = []
        item = self.dir_item()
        item['type'] = 'new'
        item['url'] = self.base_url + "#new"
        result.append(item)
        item = self.dir_item()
        item['type'] = 'top'
        item['url'] = self.base_url + "#top"
        result.append(item)
        item = self.dir_item()
        item['title'] = 'JOJ'
        item['url'] = "#cat#" + JOJ_URL + '/archiv.html'
        result.append(item)
        item = self.dir_item()
        item['title'] = 'JOJ Plus'
        item['url'] = "#cat#" + JOJ_PLUS_URL + '/plus-archiv.html'
        result.append(item)
        item = self.dir_item()
        item['title'] = 'WAU'
        item['url'] = "#cat#" + WAU_URL + '/wau-archiv.html'
        result.append(item)
        item = self.dir_item()
        item['title'] = 'Senzi'
        item['url'] = "#cat#" + SENZI_URL + '/senzi-archiv.html'
        result.append(item)
        return result

    def subcategories(self, url):
        result = []
        item = self.dir_item()
        item['title'] = "Všetky"
        item['url'] = url
        self._filter(result, item)
        item = self.dir_item()
        item['title'] = 'Relácie'
        item['url'] = url + '/?type=relacie'
        self._filter(result, item)
        item = self.dir_item()
        item['title'] = 'Seriály'
        item['url'] = url + '/?type=serialy'
        self._filter(result, item)
        item = self.dir_item()
        item['title'] = "Filmy"
        item['url'] = url + '/?type=filmy'
        self._filter(result, item)
        if 'senzi' not in url:
            item = self.video_item()
            item['title'] = 'Live'
            item['url'] = url.replace('archiv', 'live')
            self._filter(result, item)
        return result

    def list_base_page(self, base_page, top=False, new=False):
        result = []
        if top:
            for m_s in re.finditer(NEWEST_STATION_ITER_RE, base_page, re.DOTALL | re.IGNORECASE):
                url = 'http://' + urlparse.urlparse(self.base_url).netloc + '/ajax.json?' + m_s.group('url')
                headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': self.base_url}
                data = util.request(url, headers)
                data = util.json.loads(data)['content']
                for m_v in re.finditer(NEWEST_ITER_RE, data, re.DOTALL):
                    item = self.video_item()
                    item['title'] = "[%s] %s (%s)" % (m_s.group('station'), m_v.group('title'), m_v.group('time'))
                    item['url'] = m_v.group('url')
                    item['type'] = 'topvideo'
                    self._filter(result, item)
        if new:
            page = util.substr(base_page, TOP_GENERAL_START, TOP_GENERAL_END)
            for m in re.finditer(TOP_GENERAL_ITER_RE, page, re.DOTALL | re.IGNORECASE):
                item = self.video_item()
                item['title'] = m.group('title')
                item['url'] = m.group('url')
                item['img'] = m.group('img')
                item['type'] = 'newvideo'
                self._filter(result, item)
        return result

    def list_archive_page(self, show_page, showon=False, showoff=False):
        showonlist = []
        if showon:
            page = util.substr(show_page, VYSIELANE_START, NEVYSIELANE_START)
            for m in re.finditer(VYSIELANE_ITER_RE, page, re.DOTALL | re.IGNORECASE):
                item = self.dir_item()
                item['title'] = m.group('title')
                item['plot'] = m.group('desc')
                item['url'] = m.group('url') + "#season_episode"
                if m.group('itime') is not None:
                    item['type'] = "showon7d"
                else:
                    item['type'] = "showon"
                showonlist.append(item)
        showonlist.sort(key=lambda x: x['title'].lower())
        showofflist = []
        if showoff:
            page = util.substr(show_page, NEVYSIELANE_START, NEVYSIELANE_END)
            for m in re.finditer(NEVYSIELANE_ITER_RE, page, re.DOTALL | re.IGNORECASE):
                item = self.dir_item()
                item['title'] = m.group('title')
                item['url'] = m.group('url') + "#season_episode"
                item['type'] = "showoff"
                showofflist.append(item)
        showofflist.sort(key=lambda x: x['title'].lower())
        result = showonlist + showofflist
        return result

    def list_show_page(self, url, page, seasons=False, episodes=False):
        result = []
        if "/p/epizody" in url or "p/archiv" in url:
            if seasons:
                season_data = util.substr(page, SERIES_START2, SERIES_END2)
                for m in re.finditer(SERIES_ITER_RE2, season_data, re.DOTALL | re.IGNORECASE):
                    item = self.dir_item()
                    item['title'] = m.group('title')
                    item['url'] = url + '#post=%s' % (m.group('id'))
                    self._filter(result, item)
            if episodes:
                for m in re.finditer(EPISODE_ITER_RE2, page, re.DOTALL | re.IGNORECASE):
                    item = self.video_item()
                    item['title'] = "%s (%s)" % (m.group('title'), m.group('date'))
                    item['url'] = m.group('url')
                    self._filter(result, item)
        else:
            if seasons:
                season_data = util.substr(page, SERIES_START, SERIES_END)
                for m in re.finditer(SERIES_ITER_RE, season_data, re.DOTALL | re.IGNORECASE):
                    item = self.dir_item()
                    item['title'] = m.group('title')
                    item['url'] = 'http://' + urlparse.urlparse(url).netloc + '/ajax.json?' + m.group('url')
                    self._filter(result, item)
            if episodes:
                episodes_data = util.substr(page, EPISODE_START, EPISODE_END)
                for m in re.finditer(EPISODE_ITER_RE, page, re.DOTALL | re.IGNORECASE):
                    item = self.video_item()
                    item['title'] = "%s. %s (%s)" % (m.group('episode'), m.group('title'), m.group('date'))
                    item['url'] = m.group('url')
                    self._filter(result, item)
        return result

    def list_episodes_data(self, data, t):
        result = []
        if t == 1:
            iterre = EPISODE_ITER_RE
        elif t == 2:
            iterre = EPISODE_ITER_RE2
        for m in re.finditer(iterre, data, re.DOTALL):
            item = self.video_item()
            if m.groupdict().has_key("episode"):
                item['title'] = "%s. %s (%s)" % (m.group('episode'), m.group('title'), m.group('date'))
            else:
                item['title'] = "%s (%s)" % (m.group('title'), m.group('date'))
            item['url'] = m.group('url')
            self._filter(result, item)
        return result

    def rtmp_url(self, playpath, pageurl, type=None, balance=None):
        server = 'n11.joj.sk'
        if balance is not None and type is not None:
            try:
                nodes = balance.find('project[@id="joj"]').find('balance[@type="%s"]' % (type))
                min_node = int(nodes.find('node').attrib.get('id'))
                max_node = int(nodes.findall('node')[-1].attrib.get('id'))
                node_id = random.randint(min_node, max_node)
                server = balance.find('nodes').find('node[@id="%d"]' % node_id).attrib.get('url')
            except Exception as e:
                self.error("cannot get stream server: %s" % (str(e)))
                self.info("using default stream server")
        swfurl = 'http://player.joj.sk/JojPlayer.swf?no_cache=137034'
        return 'rtmp://' + server + ' playpath=' + playpath + ' pageUrl=' + pageurl + ' swfUrl=' + swfurl + \
               ' swfVfy=true'

    def resolve(self, item, captcha_cb=None, select_cb=None):
        result = []
        item = item.copy()
        url = item['url']
        if url.endswith('live.html'):
            channel = re.search(r'http://(\w+)\.joj\.sk', url).group(1)
            for original, replacement in {'www': 'joj', 'plus': 'jojplus'}.items():
                if channel == original:
                    channel = replacement
                    break
            for quality, resolution in {'lq': '180p', 'mq': '360p', 'hq': '540p'}.items():
                item = self.video_item()
                item['quality'] = resolution
                item['url'] = 'http://http-stream.joj.sk/joj/' + channel + '/index-' + quality + '.m3u8'
                result.append(item)
        else:
            data = util.request(url)
            playerdata = re.search(r'<div\ class=\"jn-player\"(.+?)>', data).group(1)
            pageid = re.search(r'data-pageid=[\'\"]([^\'\"]+)', playerdata).group(1)
            basepath = re.search(r'data-basepath=[\'\"]([^\'\"]+)', playerdata).group(1)
            videoid = re.search(r'data-id=[\'\"]([^\'\"]+)', playerdata).group(1)
            playlisturl = basepath + 'services/Video.php?clip=' + videoid + 'pageId=' + pageid
            playlist = fromstring(util.request(playlisturl))
            balanceurl = basepath + 'balance.xml?nc=%d' % random.randint(1000, 9999)
            balance = fromstring(util.request(balanceurl))
            for video in playlist.find('files').findall('file'):
                item = self.video_item()
                item['img'] = playlist.attrib.get('large_image')
                item['length'] = playlist.attrib.get('duration')
                item['quality'] = video.attrib.get('quality')
                item['url'] = self.rtmp_url(video.attrib.get('path'), playlist.attrib.get('url'),
                                            video.attrib.get('type'), balance)
                result.append(item)
            result.reverse()
        return select_cb(result)
