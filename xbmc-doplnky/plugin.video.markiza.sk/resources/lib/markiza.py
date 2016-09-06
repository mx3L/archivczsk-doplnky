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

import re
import cookielib
import urllib2
from urlparse import urlparse

import util
from provider import ContentProvider


class MarkizaContentProvider(ContentProvider):

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'videoarchiv.markiza.sk', 'http://videoarchiv.markiza.sk', username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['categories', 'resolve']

    def list(self, url):
        self.info('list - %s'% url )
        result = []
        purl = urlparse(url)
        if purl.path == '/video/':
            if purl.fragment == 'az':
                self.info('list - detected az url')
                result += self.list_base(url, az=True)
        else:
            if purl.fragment == 'categories':
                self.info('list - detected categories url')
                result += self.list_show(url, episodes=False, categories=True)
                if not result:
                    result += self.list_show(url, episodes=True, categories=False)
            else:
                self.info('list - detected episodes url')
                result += self.list_show(url, episodes=True, categories=False)
        return result

    def categories(self):
        result = []
        # TODO
        #result.append(self.dir_item(self.base_url + 'video/#latest', type='new'))
        #result.append(self.dir_item(self.base_url + 'video/#top', type='top'))
        #result.append(self.dir_item('A-Z', self.base_url+ 'video/#az'))
        result += self.list_base(self.base_url)
        return result

    def list_base(self, url, az=True, top=True):
        result = []
        data = util.request(url)
        if az:
            az_data = util.substr(data, '<li class="dropdown mega-dropdown main-kategoria">',
                    '<li class="dropdown mega-dropdown main-kategoria open_top_formats">')
            az_json_data = re.search(r'var VIDEO_ITEMS = (\[.+?\]);', az_data, re.DOTALL)
            if not az_json_data:
                self.error('list_base - no az data found!')
            else:
                for i in util.json.loads(az_json_data.group(1)):
                    item = self.dir_item(i['title'], i['url']+ "#categories")
                    item['img'] = i['image']
                    result.append(item)
        return result

    def list_show(self, url, categories=True, episodes=True):
        result = []
        data = util.request(url)
        if categories:
            categories_data = util.substr(data, '<section class="col-md-12 videoarchiv_navi">','</section>')
            categories_data = util.substr(categories_data, '<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-2">', '</div>')
            for i in re.findall(r'<li>(.+?)</li>', categories_data, re.DOTALL):
                item = self.dir_item()
                item['url'] = self._url(re.search(r'<a href="([^"]+)', i).group(1))
                item['title'] = re.search(r'title="([^"]+)', i).group(1)
                result.append(item)

        if episodes:
            row_list = []
            row_pattern = re.compile(r'<div class="item row ">(.+?)</div>\s+</div>', re.DOTALL)
            # latest episode
            episodes_data = util.substr(data, '<section class="col-md-12 info_new row">', '</section>')
            row_match = row_pattern.search(episodes_data)
            if row_match:
                row_list.append(row_match.group(1))
            # other episodes
            episodes_data = util.substr(data, '<section class="col-md-12 article-view homepage">','</section>')
            row_list += row_pattern.findall(episodes_data)
            for row in row_list:
                title_and_url_match = re.search(r'<a href="(?P<url>[^"]+") title="(?P<title>[^"]+)', row)
                if not title_and_url_match:
                    self.error('list_show - cannot get video item from "%s"'%row.strip())
                    continue
                item = self.video_item()
                item['url'] = self._url(title_and_url_match.group('url'))
                item['title'] = title_and_url_match.group('title')
                img_match = re.search(r'<img.+?src="([^"]+)', row)
                if img_match:
                    item['img'] = self._url(img_match.group(1))
                countdown_match = re.search(r'<span class="archiv-countdown">.+?</i>([^<]+)', row)
                if countdown_match:
                    item['countdown'] = countdown_match.group(1).strip()
                time_match = re.search(r'<div class="time">([^<]+)', row)
                if time_match:
                    length_str, date_str = time_match.group(1).split('&bull;')
                    item['length'] = length_str.strip()
                    item['date'] = date_str.strip()
                result.append(item)
        return result

    def resolve(self, item, captcha_cb=None, select_cb=None):
        result = []
        item = item.copy()
        video_id = urlparse(item['url']).path.split('/')[-1].split('_')[0]
        videodata = util.json.loads(util.request('http://www.markiza.sk/json/video.json?id=' + video_id))
        for v in videodata['playlist']:
            item = self.video_item()
            item['title'] = v['title']
            item['surl'] = v['title']
            item['url'] = "%s/%s" % (v['baseUrl'].replace(':1935',''), v['url'].replace('.f4m', '.m3u8'))
            result.append(item)
        if len(result) > 0 and select_cb:
            return select_cb(result)
        return result

