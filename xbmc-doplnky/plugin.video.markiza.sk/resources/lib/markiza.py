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
import datetime
from time import strftime
from Components.config import config
import traceback

import os
import util
from cachestack import lru_cache
from provider import ContentProvider

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class MarkizaCache():
    __metaclass__ = Singleton

    def __init__(self):
        self.initialized = True

    def cache_request(self, url, timeout=30):
        if timeout == 8:
            return self.cache_request_8(url)

        return self.cache_request_30(url)

    # must be in Singleton or Static class/method because cachce store per instance but in plugin class create in each request
    @lru_cache(maxsize = 1000, timeout = 8*60*60)
    def cache_request_8(self, url):
        return util.request(url)
    @lru_cache(maxsize = 250, timeout = 30*60)
    def cache_request_30(self, url):
        return util.request(url)

class markizalog(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = True
    LOG_FILE = ""
    

    @staticmethod
    def logDebug(msg):
        if markizalog.logDebugEnabled:
            markizalog.writeLog(msg, 'DEBUG')
    @staticmethod
    def logInfo(msg):
        markizalog.writeLog(msg, 'INFO')
    @staticmethod
    def logError(msg):
        markizalog.writeLog(msg, 'ERROR')
    @staticmethod
    def writeLog(msg, type):
        try:
            if not markizalog.logEnabled:
                return
            #if log.LOG_FILE=="":
            markizalog.LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'markiza.log')
            f = open(markizalog.LOG_FILE, 'a')
            dtn = datetime.datetime.now()
            f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] +" ["+type+"] %s\n" % msg)
            f.close()
        except:
            print "####MARKIZA#### write log failed!!!"
            pass
        finally:
            print "####MARKIZA#### ["+type+"] "+msg


class MarkizaContentProvider(ContentProvider):

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp', newLoad=True):
        ContentProvider.__init__(self, 'videoarchiv.markiza.sk', 'http://oldvideoarchiv.markiza.sk', username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)
        self.newLoadMethod = newLoad

    def capabilities(self):
        return ['categories', 'resolve', '!download']

    def list(self, url):
        self.info('list - %s'% url )
        result = []
        purl = urlparse(url)
        if url.find("#") != -1:
            url = url[:url.find("#")]
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
        result.append(self.dir_item(url=self.base_url + 'najnovsie', type='new'))
        result.append(self.dir_item(url=self.base_url + 'najsledovanejsie', type='top'))
        result.append(self.dir_item('A-Z', self.base_url + 'video/#az'))
        return result

    def list_base(self, url, az=True, top=True):
        try:
            result = []
            data = MarkizaCache().cache_request(url, 8)
            if az:
                az_data = util.substr(data, '<li class="dropdown mega-dropdown main-kategoria">',
                        '<li class="dropdown mega-dropdown main-kategoria open_top_formats">')

                az_json_data = re.search(r'var VIDEO_ITEMS = (\[.+?\]);', az_data, re.DOTALL)
                markizalog.logDebug("list_base azdata: %s\n\naz_json_data: %s"%(az_data, az_json_data))
                if not az_json_data:
                    self.error('list_base - no az data found!')
                else:

                    ordered = util.json.loads(az_json_data.group(1))
                    ordered.sort(key=lambda x: x['title'], reverse=False)
                    for i in ordered:
                        item = self.dir_item(i['title'], i['url']+ "#categories")
                        item['img'] = i['image']
                        result.append(item)

            return result
        except:
            markizalog.logError("Method list_base failed '%s'\n%s"%(url,traceback.format_exc()))
            raise

    def list_show(self, url, categories=True, episodes=True):
        try:
            result = []
            if categories:
                data = MarkizaCache().cache_request(url, 8)
                categories_data = util.substr(data, '<section class="col-md-12 videoarchiv_navi">','</section>')
                categories_data = util.substr(categories_data, '<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-2">', '</div>')
                for i in re.findall(r'<li>(.+?)</li>', categories_data, re.DOTALL):
                    item = self.dir_item()
                    item['url'] = self._url(re.search(r'<a href="([^"]+)', i).group(1))
                    item['title'] = re.search(r'title="([^"]+)', i).group(1)
                    result.append(item)

            if episodes:
                data = MarkizaCache().cache_request(url, 30)
                row_list = []
                row_pattern = re.compile(r'<div class="item row ">(.+?)</div>\s+</div>', re.DOTALL)
                purl = urlparse(url)
                if not 'page=' in purl.query:
                    # latest episode
                    episodes_data = util.substr(data, '<section class="col-xs-12 detail_cont row">', '</section>')
                    row_match = row_pattern.search(episodes_data)
                    if row_match:
                        row_list.append(row_match.group(1))
                # other episodes
                episodes_data = util.substr(data, '<section class="col-md-12 article-view homepage ">','</section>')
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
                        # hot fix parse fail on TN
                        try:
                            length_str, date_str = time_match.group(1).split('&bull;')
                            item['length'] = length_str.strip()
                            item['date'] = date_str.strip()
                        except:
                            try:
                                markizalog.logDebug("Parse date and time failed, date only.")
                                time_match = re.search(r'<div class="time">([^<]+)', row)
                                item['length'] = 1
                                item['date'] = str(time_match.group(1)).strip()
                            except:
                                markizalog.logError("Fix parse date failed %s"%traceback.format_exc())
                                pass
                    result.append(item)
                next_match = re.search(r'<li class="pager-next"><a href="([^"]+)', data)
                if next_match:
                    result.append(self.dir_item(url = self._url(next_match.group(1)), type='next'))
            return result
        except:
            markizalog.logError("Method list_show failed '%s'\n%s"%(url,traceback.format_exc()))
            raise

    def resolve(self, item, captcha_cb=None, select_cb=None):
        try:
            result = []
            markizalog.logDebug("ITEM:\n%s"%item)
            item = item.copy()
            video_id = urlparse(item['url']).path.split('/')[-1].split('_')[0]
            #videodata = util.json.loads(util.request('http://videoarchiv.markiza.sk/json/video_jwplayer7.json?is_web=1&noads=1&nomidads=1&nopreads=1&nopostads=1&id=' + video_id))
            videodata = util.json.loads(MarkizaCache().cache_request('http://oldvideoarchiv.markiza.sk/json/video_jwplayer7.json?is_web=1&noads=1&nomidads=1&nopreads=1&nopostads=1&id=' + video_id, 8))
            markizalog.logDebug("videodata=\n%s"%videodata)
            details = videodata['details']
            playlist = videodata['playlist']
            sources = [p['sources'][0]['file'] for p in playlist]
            #print util.json.dumps(playlist, indent=True)
            add_idx = [n for n,s in enumerate(sources) if s not in sources[n+1:]]
            playlist = [v for n,v in enumerate(playlist) if n in add_idx]
            #print util.json.dumps(playlist, indent=True)

            if self.newLoadMethod:
                for pl in playlist:
                    manifestUrl = "%s"%(pl['sources'][0]['file'])
                    markizalog.logDebug("manifet url '%s'"%manifestUrl)
                    #manifest = util.request(manifestUrl)
                    manifest = MarkizaCache().cache_request(manifestUrl, 8)
                    markizalog.logDebug("manifet\n%s"%manifest)
                    itemTitle = "%s"%pl['title']
                    markizalog.logDebug("item title=%s"%itemTitle)
                    for m in re.finditer('#EXT-X-STREAM-INF:BANDWIDTH=(?P<bandwidth>\d+),RESOLUTION=(?P<resolution>\d+x\d+)\s(?P<chunklist>[^\s]+)', manifest, re.DOTALL):
                        item = self.video_item()
                        item['title']= itemTitle
                        item['bandwidth'] = int("%s"%m.group('bandwidth'))
                        item['quality'] = m.group('resolution')
                        item['resolveTitle'] = "%s - %s"%(item['quality'], itemTitle)
                        item['url'] = manifestUrl.replace("manifest.m3u8", m.group('chunklist'))
                        markizalog.logDebug("item \nurl=%s \nbandwith=%s \nquality=%s"%(item['url'], item['bandwidth'], item['quality']))
                        result.append(item)
                    result.sort(key=lambda x: x['bandwidth'], reverse=True)
            else:
                for v in playlist:
                    item = self.video_item()
                    item['title'] = v['title'] or details['name']
                    item['date'] = details['date']
                    item['lenght'] = details['duration']
                    item['url'] = v['sources'][0]['file']
                    item['surl'] = v['title']
                    item['img'] = v['image']
                    item['plot'] = v['description']
                    markizalog.logDebug("itemurl=%s"%item['url'])
                    result.append(item)

            if len(result) > 0 and select_cb:
                return select_cb(result)
            return result
        except:
            markizalog.logError("Method resolve failed '%s'\n%s"%(item, traceback.format_exc()))
            raise            