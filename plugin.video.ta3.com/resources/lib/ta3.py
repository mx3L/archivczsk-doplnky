# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2014 Maros Ondrasek
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
import calendar
import cookielib
import urllib
import urllib2
import urlparse
import re
from datetime import date

import util
from provider import ContentProvider


class TA3ContentProvider(ContentProvider):

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'ta3.com', 'http://www.ta3.com/', username, password, filter, tmp_dir)
        self.cp = urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())
        self.init_urllib()

    def init_urllib(self):
        opener = urllib2.build_opener(self.cp)
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['categories', 'resolve', '!download']

    def categories(self):
        result = []
        item = self.video_item()
        item['title'] = 'Live'
        item['url'] = "live.html"
        result.append(item)
        result.append(self.dir_item('Spravodajstvo', self.base_url + 'archiv.html#mycat'))
        result.append(self.dir_item('Publicistika', self.base_url + 'archiv/publicistika.html#mycat'))
        return result

    def list(self, url):
        # calendar listing
        if url.find("#date#") == 0:
            year = int(url.split("#")[2])
            month = int(url.split("#")[3])
            url = url.split("#")[-1]
            return self.date(year, month, url)

        purl = urlparse.urlparse(url)
        if url.find("#") != -1:
            url = url[:url.find("#")]

        # this is special for kodi
        if purl.fragment == "mycat":
            url = url.split("#")[0]
            result = []
            result.append(self.dir_item(url=url, type='new'))
            d = date.today()
            result.append(self.dir_item('[B]Podľa dátumu[/B]',
                "#date#%d#%d#%s" %(d.year, d.month, url)))
            result.extend(self.list_categories(url))
            return result

        if purl.fragment == "categories":
            return self.list_categories("http://"+ purl.netloc + purl.path)
        return self.list_videos(self._url(url))

    def list_categories(self, url):
        result = []
        page = util.request(url)
        if 'publicistika.html' in url:
            start = '<select id="articleArchivFilterPublicistika-c"'
        elif 'archiv.html' in url:
            start = '<select id="articleArchivFilterSpravodajstvo-c"'
        else:
            self.error("_list_categories: unknown category url: %s" % url)
            return []
        data = util.substr(page, start, '</select>')
        for m in re.finditer('<option\ value=\"(?P<id>\d+)\">(?P<title>[^<]+)</option>', data):
            item = self.dir_item()
            item['url'] = self._build_url(url, category=m.group('id'))
            item['title'] = m.group('title')
            self._filter(result, item)
        return result

    def list_videos(self, url):
        result = []
        page = util.request(url)
        data = util.substr(page, '<div class="articles">','<div class="paginator">')
        listing_iter_re = r"""
            <article\ class=\"row\">.+?
                <a\ href=\"(?P<url>[^\"]+)\"><i\ class=\"ta3-icon-video\"[^>]+>[^>]+>(?P<title>[^<]+)</a>.+?
            </article> """
        for m in re.finditer(listing_iter_re, data, re.DOTALL | re.VERBOSE):
            item = self.video_item()
            item['title'] = m.group('title').strip()
            #item['title'] = "%s (%s)" % (m.group('title').strip(), m.group('date').strip())
            item['url'] = m.group('url')
            self._filter(result, item)
        pager_data = util.substr(page,'<div class="paginator">', '</div>')
        next_page_match = re.search(r'<li class="next"><a href="(?P<url>[^"]+)', pager_data)
        if next_page_match:
            item = self.dir_item()
            item['type'] = 'next'
            next_url = next_page_match.group('url').replace('&amp;','&')
            # ta3.com gives invalid page urls for publicistika
            if "publicistika.html" in url:
                purl = urlparse.urlparse(url)
                pnext_url = urlparse.urlparse(next_url)
                next_url = "http://" + purl.netloc + purl.path + "?" + pnext_url.query
            item['url'] = next_url
            self._filter(result, item)
        return result

    def _build_url(self, url, category=None, date=None, by_date=None, to_date=None, page=None):
        purl = urlparse.urlparse(url)
        if "publicistika.html" in purl.path:
            date = date or by_date or to_date
            if date is not None:
                by_date = to_date = None
        else:
            if by_date is None or to_date is None:
                by_date = date or by_date or to_date
                to_date = by_date
                date = None

        # ommit query, we create our own
        url = "http://" + purl.netloc + purl.path
        params = {}
        if category is not None:
            params['c'] = category
        if date is not None:
            params['d'] = "%02d-%02d-%d" % (date)
        if by_date is not None:
            params['df'] = "%02d-%02d-%d" % (by_date)
        if to_date is not None:
            params['dt'] = "%02d-%02d-%d" % (to_date)
        if page is not None:
            params['p'] = page
        if params:
            url += "?" + urllib.urlencode(params)
        return url


    def date(self, year, month, url):
        result = []
        today = date.today()
        prev_month = month > 1 and month - 1 or 12
        prev_year = prev_month == 12 and year - 1 or year
        item = self.dir_item()
        item['type'] = 'prev'
        item['url'] = "#date#%d#%d#%s" % (prev_year, prev_month, url)
        result.append(item)
        for d in calendar.LocaleTextCalendar().itermonthdates(year, month):
            if d.month != month:
                continue
            if d > today:
                break
            item = self.dir_item()
            item['title'] = "%d.%d %d" % (d.day, d.month, d.year)
            item['url'] = self._build_url(url, date=(d.day, d.month, d.year))
            self._filter(result, item)
        result.reverse()
        return result

    def resolve(self, item, captcha_cb=None, select_cb=None):
       item = item.copy()
       if 'live.html' in item['url']:
           result = self._resolve_live(item)
           result = sorted(result, key=lambda x:x['quality'], reverse=True)
       else:
           result = self._resolve_vod(item)
       if len(result) > 0 and select_cb:
           return select_cb(result)
       return result

    def _resolve_vod(self, item):
        resolved = []
        data = util.request(self._url(item['url']))
        video_id = re.search("LiveboxPlayer.archiv\(.+?videoId:\s*'([^']+)'", data, re.DOTALL).group(1)
        #print "video_id", video_id
        player_data = util.request("http://embed.livebox.cz/ta3_v2/vod-source.js", {'Referer':self._url(item['url'])})
        #print "player_data", player_data
        url_format = re.search(r'my.embedurl = \[\{"src" : "([^"]+)"', player_data).group(1)
        #print "url_format", url_format
        manifest_url = "https:" + url_format.format(video_id)
        #print "manifest_url", manifest_url
        manifest = util.request(manifest_url)
        print "manifest", manifest
        for m in re.finditer('#EXT-X-STREAM-INF:PROGRAM-ID=\d+,BANDWIDTH=(?P<bandwidth>\d+).*?(,RESOLUTION=(?P<resolution>\d+x\d+))?\s(?P<chunklist>[^\s]+)', manifest, re.DOTALL):
            item = self.video_item()
            item['surl'] = item['title']
            item['quality'] = m.group('bandwidth')
            item['url'] = manifest_url[:manifest_url.rfind('/')+1] + m.group('chunklist')
            resolved.append(item)
        resolved = sorted(resolved, key=lambda x:int(x['quality']), reverse=True)
        if len(resolved) == 3:
            qualities = ['720p', '480p', '360p']
            for idx, item in enumerate(resolved):
                item['quality'] = qualities[idx]
        else:
            for idx, item in enumerate(resolved):
                item['quality'] += 'b/s'
        return resolved

    def _resolve_live(self, item):
        resolved = []
        data = util.request(self._url(item['url']))
        player_data = util.request("http://embed.livebox.cz/ta3_v2/live-source.js", {'Referer':self._url(item['url'])})
        #print "player_data", player_data
        for m_manifest in re.finditer(r'\{"src"\s*:\s*"([^"]+)"\s*\}', player_data, re.DOTALL):
            manifest_url = m_manifest.group(1)
            if manifest_url.startswith('//'):
               manifest_url = 'http:'+ manifest_url
            #print "manifest_url", manifest_url
            req = urllib2.Request(manifest_url)
            resp = urllib2.urlopen(req)
            manifest = resp.read()
            resp.close()
            #print "manifest", manifest
            for m in re.finditer('RESOLUTION=\d+x(?P<resolution>\d+)\s*(?P<chunklist>[^\s]+)', manifest, re.DOTALL):
                item = self.video_item()
                item['surl'] = item['title']
                item['quality'] = m.group('resolution') + 'p'
                item['url'] = resp.geturl().rsplit('/', 1)[0] + '/' + m.group('chunklist')
                resolved.append(item)
            # only first manifest url looks to be is valid
            break
        return resolved
