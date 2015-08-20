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
import re
import urllib
import urllib2
from datetime import date
from HTMLParser import HTMLParser

import util
from provider import ContentProvider


CATEGORIES_START = '<div class="left-column">'
CATEGORIES_END = '<div class="right-column">'
CATEGORIES_ITER_RE = '<li class=\"(?P<type>[^\"]+)\">\s+<a href=\"(?P<url>[^\"]+)\" title=\"(?P<title>[^\"]+)\">.+?</a>\s*</li>'
LISTING_START = CATEGORIES_END
LISTING_END = '<div class="bannerStip">'
PAGER_START = '<div class="paging-bar-section ">'
PAGER_END = '</div>'
PAGE_NEXT_RE = '<a\s+href=\"(?P<url>[^\"]+)\".+?class=\"next\">.+?</a>'
PAGE_PREV_RE = '<a\s+href=\"(?P<url>[^\"]+)\".+?class=\"prev\">.+?</a>'

# vim uncomment prints
# :50,$s/# print/print/g

# vim comment prints
# :50,$s/print/\# print/g

class MarkizaVideoListParser(HTMLParser):

    """<div class="item ">
        <div class="image">
                <a href="/video/ordinacia-v-ruzovej-zahrade/cele-epizody-iii/33769_ordinacia-v-ruzovej-zahrade-iii.-85">
                        <div class="play">&nbsp;</div>
                        <img alt="Ordinácia v ružovej záhrade III. 85" src="http://static.cdn.markiza.sk/media/a501/image/file/23/0144/VQSR.2015_08_04_ordinacia_85_1_mp4.jpg" />
                </a>

                        <span class="archiv-countdown">Zadarmo ešte 6d 22h 17 min </span>

        </div>
        <div class="info">
                <h2><a href="/video/ordinacia-v-ruzovej-zahrade/cele-epizody-iii/33769_ordinacia-v-ruzovej-zahrade-iii.-85">Ordinácia v ružovej záhrade III. 85</a></h2>
                <span class="date">04.august 2015</span>
                <span class="length"></span>
                <div class="clear"></div>
        </div>
        <div class="clear"></div>

    </div>
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_item = False
        self.in_item_image = False
        self.in_item_info = False
        self.in_title = False
        self.in_date = False
        self.in_length = False
        self.ignore_div = 0
        self.current_item = None
        self.video_list = []

    def get_video_list(self, data):
        self.feed(data)
        return self.video_list

    def handle_div_tag(self, attrs):
        if self.in_item and (self.in_item_image or self.in_item_info):
            # print 'ignoring div - "%r"'%(attrs)
            self.ignore_div += 1
        for k, v in attrs:
            if k == 'class':
                if v.startswith('item'):
                    # print '[div] in_item'
                    self.in_item = True
                    self.current_item = {}
                    break
                elif v == 'image':
                    # print '[div] in_image'
                    self.in_item_image = True
                    break
                elif v == 'info':
                    # print '[div] in_info'
                    self.in_item_info = True
                    break
        if not self.in_item and len(self.video_list):
            # print 'ignoring div - "%r"'%(attrs)
            self.ignore_div += 1

    def handle_image_tag(self, attrs):
        # print '[img] in_image = %s, %r'%(str(self.in_item_image), attrs)
        if not self.in_item_image:
            return
        for k, v in attrs:
            if k == 'src':
                self.current_item['img'] = v

    def handle_a_tag(self, attrs):
        # print '[a] in_info = %s, %r'%(str(self.in_item_info), attrs)
        if not self.in_item_info:
            return
        self.in_title = True
        for k, v in attrs:
            if k == 'href':
                self.current_item['url'] = v

    def handle_span_tag(self, attrs):
        # print '[span] in_image = %s, in_info = %s, %r'%(str(self.in_item_image), str(self.in_item_info), attrs)
        if not (self.in_item_image or self.in_item_info):
            return
        for k, v in attrs:
            if k == 'class' and self.in_item_info:
                if v == 'date':
                    self.in_date = True
                elif v == 'length':
                    self.in_length = True

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            self.handle_div_tag(attrs)
        elif tag == 'span':
           self.handle_span_tag(attrs)
        elif tag == 'a':
            self.handle_a_tag(attrs)
        elif tag == 'img':
            self.handle_image_tag(attrs)

    def handle_data(self, data):
        if self.in_title:
            # print 'in_title, data = ', data
            self.current_item['title'] = data
        elif self.in_date:
            # print 'in_date, data = ', data
            self.current_item['date'] = data
        elif self.in_length:
            # print 'in_length, data = ', data
            self.current_item['length'] = data

    def handle_endtag(self, tag):
        if tag == 'div':
            if self.ignore_div > 0:
                self.ignore_div -= 1
            elif self.in_item_image:
                self.in_item_image = False
            elif self.in_item_info:
                self.in_item_info = False
            elif self.in_item:
                # print "adding item: %s"%(self.current_item)
                self.video_list.append(self.current_item)
                self.current_item = None
                self.in_item = False
        elif tag == 'a':
            if self.in_title:
                self.in_title = False
        elif tag == 'span':
            if self.in_date:
                self.in_date = False
            if self.in_length:
                self.in_length = False


class MarkizaContentProvider(ContentProvider):

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'videoarchiv.markiza.sk', 'http://videoarchiv.markiza.sk', username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['categories', 'resolve']

    def list(self, url):
        if url.find('subcat') == 0:
            category_id = url.split("#")[1]
            return self.list_subcategories(util.request(self.base_url), category_id)
        elif url.find('calendar') == 0:
            year, month = url.split("#")[1].split("|")
            return self.calendar(int(year), int(month))
        return self.list_content(util.request(self._url(url)))

    def categories(self):
        result = []
        item = self.dir_item()
        item['type'] = 'new'
        item['url'] = 'najnovsie'
        result.append(item)
        item = self.dir_item()
        item['title'] = '[B]Podľa dátumu[/B]'
        d = date.today()
        item['url'] = 'calendar#%d|%d' % (d.year, d.month)
        result.append(item)
        data = util.request(self.base_url)
        data = util.substr(data, CATEGORIES_START, CATEGORIES_END)
        for m in re.finditer(CATEGORIES_ITER_RE, data, re.IGNORECASE | re.DOTALL):
            if m.group('type').strip().startswith('child'):
                continue
            item = self.dir_item()
            item['title'] = m.group('title')
            if m.group('type').strip() == 'has-child':
                item['url'] = "subcat#" + m.group('url')
            else:
                item['url'] = m.group('url')
            self._filter(result, item)
        return result

    def list_subcategories(self, page, category_id):
        result = []
        data = util.substr(page, CATEGORIES_START, CATEGORIES_END)
        data = util.substr(data, category_id, CATEGORIES_END)
        for m in re.finditer(CATEGORIES_ITER_RE, data, re.IGNORECASE | re.DOTALL):
            if not m.group('type').strip().startswith('child'):
                break
            item = self.dir_item()
            item['title'] = m.group('title')
            item['url'] = m.group('url')
            self._filter(result, item)
        return result

    def calendar(self, year, month):
        result = []
        today = date.today()
        prev_month = month > 1 and month - 1 or 12
        prev_year = prev_month == 12 and year - 1 or year
        item = self.dir_item()
        item['type'] = 'prev'
        item['url'] = 'calendar#%d|%d' % (prev_year, prev_month)
        result.append(item)
        for d in calendar.LocaleTextCalendar().itermonthdates(year, month):
            if d.month != month:
                continue
            if d > today:
                break
            item = self.dir_item()
            item['title'] = "%d.%d %d" % (d.day, d.month, d.year)
            item['url'] = "prehlad-dna/%02d-%02d-%d" % (d.day, d.month, d.year)
            self._filter(result, item)
        result.reverse()
        return result

    def list_content(self, page):
        result = []
        data = util.substr(page, LISTING_START, LISTING_END)
        for i in MarkizaVideoListParser().get_video_list(data):
            item = self.video_item()
            item['title'] = "%s - (%s)" % (i['title'].strip(), i['date'].strip())
            item['img'] = i.get('img')
            item['url'] = i['url']
            self._filter(result, item)
        pager_data = util.substr(page, PAGER_START, PAGER_END)
        for m in re.finditer("<a.+?</a>", pager_data, re.DOTALL):
            p = re.search(PAGE_PREV_RE, m.group(), re.DOTALL)
            n = re.search(PAGE_NEXT_RE, m.group(), re.DOTALL)
            if p:
                item = self.dir_item()
                item['type'] = 'prev'
                item['url'] = p.group('url')
                result.append(item)
            if n:
                item = self.dir_item()
                item['type'] = 'next'
                item['url'] = n.group('url')
                result.append(item)
        return result

    def resolve(self, item, captcha_cb=None, select_cb=None):
        result = []
        item = item.copy()
        urlpart = item['url'].split('/')[-1] or item['url'].split('/')[-2]
        video_id = re.search("(\d+)\_", urlpart).group(1)
        videodata = util.json.loads(util.request('http://www.markiza.sk/json/video.json?id=' + video_id))
        for v in videodata['playlist']:
            item = self.video_item()
            item['title'] = v['title']
            item['surl'] = v['title']
            item['url'] = "%s/%s" % (v['baseUrl'], v['url'].replace('.f4m', '.m3u8'))
            result.append(item)
        if len(result) > 0 and select_cb:
            return select_cb(result)
        return result
