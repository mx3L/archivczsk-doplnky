# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2013 Libor Zoubek
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
import urllib
import urllib2
import cookielib
import json
from xml.etree.ElementTree import fromstring

import util
import resolver
from provider import ResolveException
from provider import ContentProvider

class VideaceskyContentProvider(ContentProvider):

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'videacesky.cz', 'http://www.videacesky.cz', username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['categories', 'resolve', 'search']

    def list(self, url):
        if url.find('zebricky/') == 0:
            return self.list_top10(util.request(self.base_url+url))
        if url.find("#related#") == 0:
            return self.list_related(util.request(url[9:]))
        else:
            return self.list_content(util.request(self._url(url)), self._url(url))

    def search(self, keyword):
        return self.list('/hledat?q=' + urllib.quote(keyword))

    def categories(self):
        result = []
        item = self.dir_item()
        item['type'] = 'new'
        item['url'] = "?orderby=post_date"
        result.append(item)
        item = self.dir_item()
        item['title'] = 'Top of the month'
        item['url'] = "zebricky/mesic/vse"
        result.append(item)
        data = util.request(self.base_url)
        data = util.substr(data, '<ul class=\"nav categories m-b\">', '</div>')
        pattern = '<a href=\"(?P<url>[^\"]+)(.+?)>(?P<name>[^<]+)'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            if m.group('url') == '/':
                continue
            item = self.dir_item()
            item['title'] = m.group('name')
            item['url'] = m.group('url')
            result.append(item)
        return result

    def list_top10(self, page):
        result = []
        data = util.substr(page, '<div class=\"line-items no-wrapper no-padder', '<div class=\"my-pagination>')
        pattern = '<article class=\"video-line.+?<a href=\"(?P<url>[^\"]+)\" *title=\"(?P<title>[^\"]+)\"(.+?)<img src=\"(?P<img>[^\"]+)\"'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['url'] = self.base_url[:-1] + m.group('url')
            self._filter(result, item)
        return result

    def list_content(self, page, url=None):
        result = []
        if not url: url = self.base_url
        data = util.substr(page, '<div class=\"items no-wrapper no-padder', '<div class=\"my-pagination>')
        pattern = '<article class=\"video\".+?<a href=\"(?P<url>[^\"]+)\" *title=\"(?P<title>[^\"]+)\"(.+?)<img src=\"(?P<img>[^\"]+)\".+?<p>(?P<plot>[^<]+?)<\/p>.+?<li class=\"i-published\".+?title=\"(?P<date>[^\"]+)\"'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = m.group('img').strip()
            item['plot'] = self.decode_plot(m.group('plot'))
            item['url'] = self.base_url[:-1] + m.group('url')
            item['menu'] = {'$30060':{'list':'#related#' + item['url'], 'action-type':'list'}}
            print item
            self._filter(result, item)
        data = util.substr(page, '<ul class=\"my-pagination', '</div>')
        n = re.search('<li class=\"paginate_button previous *\"[^<]+<a href=\"(?P<url>[^\"]+)\">(?P<name>[^<]+)<', data)
        k = re.search('<li class=\"paginate_button next *\"[^<]+<a href=\"(?P<url>[^\"]+)\">(?P<name>[^<]+)<', data)
        if not n == None:
            item = self.dir_item()
            item['type'] = 'prev'
            # item['title'] = '%s - %s' % (m.group(1), n.group('name'))
            item['url'] = n.group('url')
            result.append(item)
        if not k == None:
            item = self.dir_item()
            item['type'] = 'next'
            # item['title'] = '%s - %s' % (m.group(1), k.group('name'))
            item['url'] = k.group('url')
            result.append(item)
        return result

    def list_related(self, page):
        result = []
        data = util.substr(page, '<div class=\"related\"', '<div class=\"postFooter\">')
        pattern = '<li[^>]+><div[^<]+<img\ src=\"(?P<img>[^\"]+)\"[^<]+</a>\s+</div><a href=\"(?P<url>[^\"]+)\" title=\"(?P<title>[^\"]+)\">.+?</li>'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = m.group('img')
            item['url'] = m.group('url')
            self._filter(result, item)
        return result

    def decode_plot(self, p):
        p = re.sub('<br[^>]*>', '', p)
        p = re.sub('<div[^>]+>', '', p)
        p = re.sub('<table.*', '', p)
        p = re.sub('</span>|<br[^>]*>|<ul>|</ul>|<hr[^>]*>', '', p)
        p = re.sub('<span[^>]*>|<p[^>]*>|<li[^>]*>', '', p)
        p = re.sub('<strong>|<a[^>]*>|<h[\d]+>', '[B]', p)
        p = re.sub('</strong>|</a>|</h[\d]+>', '[/B]', p)
        p = re.sub('</p>|</li>', '[CR]', p)
        p = re.sub('<em>', '[I]', p)
        p = re.sub('</em>', '[/I]', p)
        p = re.sub('<img[^>]+>', '', p)
        p = re.sub('\[B\]Edituj popis\[\/B\]', '', p)
        p = re.sub('\[B\]\[B\]', '[B]', p)
        p = re.sub('\[/B\]\[/B\]', '[/B]', p)
        p = re.sub('\[B\][ ]*\[/B\]', '', p)
        return util.decode_html(''.join(p)).encode('utf-8').strip()

    def resolve(self, item, captcha_cb=None, select_cb=None):
        result = []
        resolved = []
        item = item.copy()
        url = self._url(item['url'])
        data = util.substr(util.request(url), '<![CDATA[', '</script>')

        playlist = re.search('''ihv_video_instance_\d+\.setup.+?(?P<jsondata>'playlist':.+?)width:''', data, re.MULTILINE | re.DOTALL)
	jsondata = re.sub(' +',' ','{%s' % playlist.group('jsondata').replace('file:','"file":').replace('label:','"label":').replace('kind:','"kind":').replace('default:','"default":').replace('tracks','"tracks"').replace('true','"true"').replace('],',']'))+'}'
        jsondata = json.loads(jsondata.replace("'",'"'))

        for playlist_item in jsondata['playlist']:
            video_url = resolver.findstreams([playlist_item['file']])
            subs = playlist_item['tracks']
            if video_url and subs:
                for i in video_url:
                    i['subs'] = self.base_url[:-1]+subs[0]['file']
            resolved += video_url[:]

        if not resolved:
            raise ResolveException('Video nenalezeno')

        for i in resolved:
            item = self.video_item()
            try:
                item['title'] = i['title']
            except KeyError:
                pass
            item['url'] = i['url']
            item['quality'] = i['quality']
            item['surl'] = i['surl']
            item['subs'] = i['subs']
            item['headers'] = i['headers']
            try:
                item['fmt'] = i['fmt']
            except KeyError:
                pass
            result.append(item)
        if len(result) > 0 and select_cb:
            return select_cb(result)
        return result
