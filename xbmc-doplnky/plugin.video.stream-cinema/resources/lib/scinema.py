# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2017 bbaron
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

import urllib
import urllib2
import cookielib
import sys
import os
import json
import traceback

import util
from provider import ContentProvider, cached, ResolveException

sys.path.append( os.path.join ( os.path.dirname(__file__),'myprovider') )
#sys.setrecursionlimit(10000)

BASE_URL="http://stream-cinema.online"
MOVIES_BASE_URL = BASE_URL + "/json"
SERIES_BASE_URL = BASE_URL + "/json/series"

MOVIES_A_TO_Z_TYPE = "movies-a-z"

class StreamCinemaContentProvider(ContentProvider):
    ISO_639_1_CZECH = None
    par = None

    def __init__(self, username=None, password=None, filter=None, reverse_eps=False):
        ContentProvider.__init__(self, name='czsklib', base_url=MOVIES_BASE_URL, username=username,
                                 password=password, filter=filter)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)
        self.reverse_eps = reverse_eps
        self.ws = None
        self.wsuser = username
        self.wspass = password

    def write(self, str):
        return
        f = open('/tmp/.log', 'a')
        f.write("%s\n" % str)
        f.close()

    def on_init(self):
        kodilang = self.lang or 'cs'
        if kodilang == ISO_639_1_CZECH or kodilang == 'sk':
            self.ISO_639_1_CZECH = ISO_639_1_CZECH
        else:
            self.ISO_639_1_CZECH = 'en'

    def capabilities(self):
        return ['resolve', 'categories', 'search']

    def categories(self):
        result = []
        data = json.loads(self.get_data_cached(MOVIES_BASE_URL + '/list/hp'))
        for m in data:
            item = self.dir_item(title=m['title'], url=MOVIES_BASE_URL + str(m['url']))
            result.append(item)
        return result

    def a_to_z(self, url_type):
        result = []
        for letter in ['0-9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'e', 'h', 'i', 'j', 'k', 'l', 'm',
                       'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']:
            item = self.dir_item(title=letter.upper())
            item['url'] = self.base_url + "/movie/letter/" + letter
            result.append(item)
        return result

    def search(self, keyword):
        sq = {'search': keyword}
        return self.list_by_params(MOVIES_BASE_URL + '/list/search?' + urllib.urlencode(sq))

    def list(self, url):
        try:
            self.write("list: %s" % url)
            if MOVIES_A_TO_Z_TYPE in url:
                self.write("az")
                return self.a_to_z(MOVIES_A_TO_Z_TYPE)
            if "/letter/" in url:
                self.write("letter")
                return self.list_by_letter(url)
            if "/series/" in url:
                self.write("series")
                self.base_url = SERIES_BASE_URL
                return self.list_series(url)
            if "/list/" in url:
                self.write("list")
                return self.list_by_params(url)
        except:
            self.write(traceback.format_exc())
            pass
        self.write("I failed")
        return [self.dir_item(title="I failed", url="fail")]

    def list_by_letter(self, url):
        result = []
        data = json.loads(self.get_data_cached(url))
        for m in data:
            item = self.video_item()
            if '/json/series' in self.base_url:
                item = self.video_item(url=self.base_url + '/play/%s/%s/%s' % (m['id'], m['season'], m['episode']), img=m['poster'])
            else:
                item = self.video_item(url=self.base_url + '/play/' + m['id'], img=m['poster'])
            item['title'] = m['name']
            self._filter(result, item)
        util.debug(result)
        return result

    def list_by_params(self, url):
        data = json.loads(self.get_data_cached(url))
        result = []
        for m in data:
            if m['typ'] != 'latest':
                item = self.dir_item(title=m['title'], url=url + '/' + m['url'])
            else:
                if '/json/series' in self.base_url:
                    item = self.video_item(url=self.base_url + '/play/%s/%s/%s' % (m['id'], m['season'], m['episode']), img=m['poster'])
                else:
                    item = self.video_item(url=self.base_url + '/play/' + m['id'], img=m['poster'])
                item['title'] = m['name']
            self._filter(result, item)
        return result
        
    def list_series(self, url):
        result = []
        data = json.loads(self.get_data_cached(url))
        try:
            for m in data:
                if m['typ'] == 'latest':
                    if 'title' in m:
                        item = self.dir_item(title=m['title'], url=SERIES_BASE_URL + '/get/' + m['url'])
                    else:
                        item = self.dir_item(title=m['name'], url=SERIES_BASE_URL + '/get/' + m['url'])
                else:
                    if '/json/series' in self.base_url:
                        tmp = self.base_url + '/play/%s/%s/%s' % (m['id'], m['season'], m['episode'])
                        item = self.video_item(url=tmp)
                    else:
                        item = self.video_item(url=self.base_url + '/play/' + m['id'])
                    item['title'] = m['name']

                self._filter(result, item)
        except:
            self.write(traceback.format_exc())
            pass
            
        return result

    @cached(ttl=24)
    def get_data_cached(self, url):
        self.write("URL: %s" % url)
        return util.request(url)

    def _resolve(self, itm):
        if itm == None:
            return None;
        self.write("_resolve itm: " + str(itm))
        if itm['provider'] == 'plugin.video.online-files' and itm['params']['cp'] == 'webshare.cz':
            if self.wsuser != "":
                try:
                    if self.ws == None:
                        from webshare import Webshare as wx
                        self.write("\n\nws: [%s] [%s]\n\n" % (self.wsuser, self.wspass))
                        self.ws = wx(self.wsuser, self.wspass)
                    itm['url'] = self.ws.resolve(itm['params']['play']['ident'])
                except:
                    self.write(traceback.format_exc())
                    pass
            else:
                self.write("nemame meno/heslo pre ws")
        self.write("_resolve return itm: " + str(itm['url']))
        return itm
    
    def resolve(self, item, captcha_cb=None, select_cb=None):
        self.write("ITEM RESOLVE: " + str(item))
        data = json.loads(self.get_data_cached(item['url']))
        self.write("\n\n\ndata: " + str(data))
        try:
            if len(data) < 1:
                raise ResolveException('Video is not available.')
            res = []
            for m in data:
                tmp = self._resolve(m)
                self._filter(res, tmp)
            return res
        except:
            self.write(traceback.format_exc())
            pass
