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
import os
import urllib
import urllib2
import shutil
import traceback
import cookielib
import md5
import calendar
from time import sleep
from datetime import date

import util
from provider import ContentProvider

START_TOP = '<h2 class="nadpis">Najsledovanejšie</h2>'
END_TOP = '<h2 class="nadpis">Najnovšie</h2>'
TOP_ITER_RE = '<li(.+?)<a title=\"(?P<title>[^"]+)\"(.+?)href=\"(?P<url>[^"]+)\"(.+?)<img src=\"(?P<img>[^"]+)\"(.+?)<p class=\"day\">(?P<date>[^<]+)<\/p>(.+?)<span class=\"programmeTime\">(?P<time>[^<]+)(.+?)<\/li>'

START_NEWEST = END_TOP
END_NEWEST = '<div class="footer'
NEWEST_ITER_RE = '<li(.+?)<a href=\"(?P<url>[^"]+)\"(.+?)title=\"(?P<title>[^"]+)\"(.+?)<img src=\"(?P<img>[^"]+)\"(.+?)<p class=\"day\">(?P<date>[^<]+)<\/p>(.+?)<span class=\"programmeTime\">(?P<time>[^<]+)(.+?)<\/li>'

START_AZ = '<h2 class="az"'
END_AZ = START_TOP
AZ_ITER_RE = TOP_ITER_RE

START_DATE = '<div class="row verticalLine tvarchivDate">'
END_DATE = START_TOP
DATE_ITER_RE = '<div class=\"media\">\s*<a href=\"(?P<url>[^\"]+)\"[^<]+>\s*<img src=\"(?P<img>[^\"]+)\".+?</a>\s*<div class=\"media-body\">.+?<span class=\"programmeTime\">(?P<time>[^\<]+)<\/span>.+?<a class=\"link\".+?title=\"(?P<title>[^\"]+)\">.+?<\/div>'

START_LISTING = "<div class='calendar modal-body'>"
END_LISTING = '</table>'
LISTING_PAGER_RE = "<a class=\'prev calendarRoller' href=\'(?P<prevurl>[^\']+)\'.+?<a class=\'next calendarRoller\' href=\'(?P<nexturl>[^\']+)"
LISTING_DATE_RE = '<div class=\'calendar-header\'>\s+<h6>(?P<date>[^<]+)</h6>'
LISTING_ITER_RE = '<td class=(\"day\"|\"active day\")>\s+<a href=[\'\"](?P<url>[^\"^\']+)[\"\']>(?P<daynum>[\d]+)</a>\s+</td>'

EPISODE_START = '<div class="span9">'
EPISODE_END = '<div class="footer'
EPISODE_RE = '<div class=\"article-header\">\s+?<h2>(?P<title>[^<]+)</h2>.+?(<div class=\"span6">\s+?<div[^>]+?>(?P<plot>[^<]+)</div>)?'

def to_unicode(text, encoding='utf-8'):
    if isinstance(text, unicode):
        return text
    return unicode(text, encoding, errors='replace')


class RtvsContentProvider(ContentProvider):

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'rtvs.sk', 'http://www.rtvs.sk/televizia/archiv', username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def _fix_url(self, url):
        if url.startswith('/json/') or url.startswith('/televizia/archiv/'):
            return 'http://www.rtvs.sk' + url
        return self._url(url)

    def capabilities(self):
        return ['categories', 'resolve', '!download']

    def list(self, url):
        if url.find('#az#') == 0:
            return self.az()
        elif url.find("#date#") == 0:
            month, year = url.split('#')[-1].split('.')
            return self.date(int(year), int(month))
        elif url.find('ord=az') != -1 and url.find('l=') != -1:
            self.info('AZ listing: %s' % url)
            return self.list_az(util.request(self._fix_url(url)))
        elif url.find('ord=dt') != -1 and url.find('date=') != -1:
            self.info('DATE listing: %s' % url)
            return self.list_date(util.request(self._fix_url(url)))
        elif url.find('/json/') != -1:
            if url.find('snippet_archive_series_calendar.json'):
                self.info("EPISODE listing (JSON): %s" % url)
                return self.list_episodes(util.json.loads(util.request(self._fix_url(url)))['snippets']['snippet-calendar-calendar'])
            else:
                self.error("unknown JSON listing request: %s"% url)
        else:
            self.info("EPISODE listing: %s" % url)
            return self.list_episodes(util.request(self._fix_url(url)))

    def categories(self):
        result = []
        item = self.dir_item()
        item['title'] = '[B]A-Z[/B]'
        item['url'] = "#az#"
        result.append(item)
        item = self.dir_item()
        item['title'] = '[B]Podľa dátumu[/B]'
        d = date.today()
        item['url'] = "#date#%d.%d" % (d.month, d.year)
        result.append(item)
        return result

    def az(self):
        result = []
        item = self.dir_item()
        item['title'] = '0-9'
        item['url'] = '?l=9&ord=az'
        self._filter(result, item)
        for c in xrange(65, 90, 1):
            chr = str(unichr(c))
            item = self.dir_item()
            item['title'] = chr
            item['url'] = '?l=%s&ord=az' % chr.lower()
            self._filter(result, item)
        return result

    def date(self, year, month):
        result = []
        today = date.today()
        prev_month = month > 0 and month - 1 or 12
        prev_year = prev_month == 12 and year - 1 or year
        item = self.dir_item()
        item['type'] = 'prev'
        item['url'] = "#date#%d.%d" % (prev_month, prev_year)
        result.append(item)
        for d in calendar.LocaleTextCalendar().itermonthdates(year, month):
            if d.month != month:
                continue
            if d > today:
                break
            item = self.dir_item()
            item['title'] = "%d.%d %d" % (d.day, d.month, d.year)
            item['url'] = "?date=%d-%02d-%02d&ord=dt" % (d.year, d.month, d.day)
            self._filter(result, item)
        result.reverse()
        return result

    def list_az(self, page):
        result = []
        images = []
        page = util.substr(page, START_AZ, END_AZ)
        for m in re.finditer(AZ_ITER_RE, page, re.IGNORECASE | re.DOTALL):
            img = {'remote':self._fix_url(m.group('img')),
                   'local' :self._get_image_path(self._fix_url(m.group('img')))}
            item = self.dir_item()
            semicolon = m.group('title').find(':')
            if semicolon != -1:
                item['title'] = m.group('title')[:semicolon].strip()
            else:
                item['title'] = m.group('title')
            item['img'] = img['local']
            item['url'] = m.group('url')
            self._filter(result, item)
            images.append(img)
        self._get_images(images)
        return result

    def list_date(self, page):
        result = []
        images = []
        page = util.substr(page, START_DATE, END_DATE)
        for m in re.finditer(DATE_ITER_RE, page, re.IGNORECASE | re.DOTALL):
            img = {'remote':self._fix_url(m.group('img')),
                   'local' :self._get_image_path(self._fix_url(m.group('img')))}
            item = self.video_item()
            item['title'] = "%s (%s)" % (m.group('title'), m.group('time'))
            item['img'] = img['local']
            item['url'] = m.group('url')
            item['menu'] = {'$30070':{'list':item['url'], 'action-type':'list'}}
            self._filter(result, item)
            images.append(img)
        self._get_images(images)
        return result

    def list_episodes(self, page):
        result = []
        episodes = []
        page = util.substr(page, START_LISTING, END_LISTING)
        current_date = to_unicode(re.search(LISTING_DATE_RE, page, re.IGNORECASE | re.DOTALL).group('date'))
        self.info("<list_episodes> current_date: %s" % current_date)
        prev_url = re.search(LISTING_PAGER_RE, page, re.IGNORECASE | re.DOTALL).group('prevurl')
        prev_url = re.sub('&amp;', '&', prev_url)
        #self.info("<list_episodes> prev_url: %s" % prev_url)
        for m in re.finditer(LISTING_ITER_RE, page, re.IGNORECASE | re.DOTALL):
            episodes.append([self._fix_url(re.sub('&amp;', '&', m.group('url'))), m])
        self.info("<list_episodes> found %d episodes" % len(episodes))
        res = self._request_parallel(episodes)
        for p, m in res:
            m = m[0]
            dnum = to_unicode(m.group('daynum'))
            item = self.list_episode(p)
            item['title'] = "%s (%s. %s)" % (item['title'], dnum, current_date)
            item['date'] = dnum
            item['url'] = re.sub('&amp;', '&', m.group('url'))
            self._filter(result, item)
        result.sort(key=lambda x:int(x['date']), reverse=True)

        item = self.dir_item()
        item['type'] = 'prev'
        item['url'] = prev_url
        self._filter(result, item)
        return result

    def list_episode(self, page):
        item = self.video_item()
        episode = re.search(EPISODE_RE, page, re.DOTALL)
        if episode:
            item['title'] = to_unicode(episode.group('title').strip())
            if episode.group('plot'):
                item['plot'] = to_unicode(episode.group('plot').strip())
        return item

    def resolve(self, item, captcha_cb=None, select_cb=None):
        result = []
        item = item.copy()
        video_id = item['url'].split('/')[-1]
        self.info("<resolve> videoid: %s" % video_id)
        videodata = util.json.loads(util.request("http://www.rtvs.sk/json/archive.json?id=" + video_id))
        for v in videodata['playlist']:
            url = "%s/%s" % (v['baseUrl'], v['url'].replace('.f4m', '.m3u8'))
            #http://cdn.srv.rtvs.sk:1935/vod/_definst_//smil:fZGAj3tv0QN4WtoHawjZnKy35t7dUaoB.smil/manifest.m3u8
            if '/smil:' in url:
                manifest = util.request(url)
                for m in re.finditer('#EXT-X-STREAM-INF:PROGRAM-ID=\d+,BANDWIDTH=\d+,RESOLUTION=(?P<resolution>\d+x\d+)\s(?P<chunklist>[^\s]+)', manifest, re.DOTALL):
                    item = self.video_item()
                    item['title'] = v['details']['name']
                    item['surl'] = item['title']
                    if m.group('resolution') == '1280x720':
                        item['quality'] = '720p'
                    elif m.group('resolution') == '852x480':
                        item['quality'] = '480p'
                    elif m.group('resolution') == '640x360':
                        item['quality'] = '360p'
                    elif m.group('resolution') == '426x240':
                        item['quality'] = '240p'
                    else:
                        item['quality'] = '???'
                    item['url'] = url[:url.rfind('/')+1] + m.group('chunklist')
                    result.append(item)
            else:
                item = self.video_item()
                item['title'] = v['details']['name']
                item['surl'] = item['title']
                item['quality'] = '???'
                item['url'] = url
                result.append(item)
        self.info("<resolve> playlist: %d items" % len(result))
        map(self.info, ["<resolve> item(%d): title= '%s', url= '%s'" % (i, it['title'], it['url']) for i, it in enumerate(result)])
        if len(result) > 0 and select_cb:
            return select_cb(result)
        return result

    def _request_parallel(self, requests):
        def fetch(req, *args):
            return util.request(req), args
        pages = []
        q = util.run_parallel_in_threads(fetch, requests)
        while True:
            try:
                page, args = q.get_nowait()
            except:
                break
            pages.append([page, args])
        return pages

    def _get_image_path(self, name):
        local = self.tmp_dir
        m = md5.new()
        m.update(name)
        image = os.path.join(local, m.hexdigest() + '_img.png')
        return image

    def _get_images(self, images):
        def download(remote, local):
            util.save_data_to_file(util.request(remote), local)
        not_cached = [(img['remote'], img['local'])
                       for img in images if not os.path.exists(img['local'])]
        util.run_parallel_in_threads(download, not_cached)
