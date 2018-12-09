################################################################################################################
################################################################################################################
################################################################################################################
## @TODO for boddie
#   - (feature) cachovanie requestov ako optimalizacia vykonu vid. lru_cache u stream-cinema
################################################################################################################
################################################################################################################
################################################################################################################




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


import urllib2,urllib,re,os,string,time,base64,datetime
from urlparse import urlparse, urlunparse, parse_qs
from cachestack import lru_cache
import datetime
from time import strftime
import cookielib
try:
    import hashlib
except ImportError:
    import md5

from Components.config import config
from provider import ContentProvider
from mmodules import read_page

_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'

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
    logDebugEnabled = False
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

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'videoarchiv.markiza.sk', 'http://videoarchiv.markiza.sk', username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['categories', 'resolve']

    def addDir(self, name, url, mode, thumb = None):
        img = None;
        if thumb != None:
            img = thumb
        return {'type': 'dir', 'title': name, 'size': '0', 'url': '%s##%s##%s'%(name, url, mode), 'img': img}

    def addLink(self, title, url):
        item = self.video_item()
        item['url'] = url
        item['title'] = title
        return item

    def getMode(self, url):
        tmp = url.split('##')
        return tmp[0], tmp[1], int(tmp[2])

    def top(self, url):
        result = []
        doc = read_page(url)

        for section in doc.findAll('section', 'b-main-section my-sm-5'):
            if section.div.h3.getText(" ").encode('utf-8') == 'TOP relácie':
                for article in section.findAll('article'):
                    url = article.a['href'].encode('utf-8')
                    title = article.a['title'].encode('utf-8')
                    thumb = article.a.div.img['data-original'].encode('utf-8')
                    result.append(self.addDir(title, url, 3,thumb))

        return result

    def newEpisodes(self, url):
        result = []
        doc = read_page(url)

        for section in doc.findAll('section', 'b-main-section b-section-articles my-5'):
            if section.div.h3.getText(" ").encode('utf-8') == 'Najnovšie epizódy':
                for article in section.findAll('article'):
                    url = article.a['href'].encode('utf-8')
                    title1 = article.h3.getText(" ").encode('utf-8')
                    title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                    title = str(title1) + ' - ' + str(title2)
                    thumb = article.a.div.img['data-original'].encode('utf-8')
                    result.append(self.addDir(title, url, 3, thumb))

        return result

    def mostViewed(self, url):
        result = []
        doc = read_page(url)

        for section in doc.findAll('section', 'b-main-section b-section-articles b-section-articles-primary my-5'):
            if section.div.h3.getText(" ").encode('utf-8') == 'Najsledovanejšie':
                for article in section.findAll('article'):
                    url = article.a['href'].encode('utf-8')
                    title1 = article.h3.getText(" ").encode('utf-8')
                    title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                    title = str(title1) + ' - ' + str(title2)
                    thumb = article.a.div.img['data-original'].encode('utf-8')
                    result.append(self.addDir(title, url, 3, thumb))

        return result

    def recommended(self, url):
        result = []
        doc = read_page(url)

        for section in doc.findAll('section', 'b-main-section b-section-articles b-section-articles-primary my-5'):
            if section.div.h3.getText(" ").encode('utf-8') == 'Odporúčame':
                for article in section.findAll('article'):
                    url = article.a['href'].encode('utf-8')
                    title1 = article.h3.getText(" ").encode('utf-8')
                    title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                    title = str(title1) + ' - ' + str(title2)
                    thumb = article.a.div.img['data-original'].encode('utf-8')
                    result.append(self.addDir(title, url, 3, thumb))
        return result

    def episodes(self, url):
        result = []
        doc = read_page(url)

        for article in doc.findAll('article', 'b-article b-article-text b-article-inline'):
            url = article.a['href'].encode('utf-8')
            thumb = article.a.div.img['data-original'].encode('utf-8')
            title1 = article.a['title'].encode('utf-8')
            title2 = article.find('div', 'e-date').span.getText(" ").encode('utf-8')
            title = str(title1) + ' - ' + str(title2)
            result.append(self.addDir(title,url,3, thumb))

        main = doc.find('main')
        for section in main.findAll('section'):
            titleSection = section.find('h3','e-articles-title').getText(" ").encode('utf-8')
            result.append(self.addDir(titleSection, url, 4))

        return result

    def videoLink(self, url):
        result = []
        doc = read_page(url)
        main = doc.find('main')
        url = main.find('iframe')['src']

        req = urllib2.Request(url)
        req.add_header('User-Agent', _UserAgent_)
        response = urllib2.urlopen(req)
        httpdata = response.read()
        response.close()

        httpdata = httpdata.replace("\r","").replace("\n","").replace("\t","")

        thumb = re.compile('<meta property="og:image" content="(.+?)">').findall(httpdata)
        thumb = thumb[0] if len(thumb) > 0 else ''

        desc = re.compile('<meta name="description" content="(.+?)">').findall(httpdata)
        desc = desc[0] if len(desc) > 0 else ''

        name = re.compile('<meta property="og:title" content="(.+?)">').findall(httpdata)
        name = name[0] if len(name) > 0 else '?'

        renditions = re.compile('renditions: \[(.+?)\]').findall(httpdata)
        if len(renditions) > 0:
            renditions = re.compile('[\'\:](.+?)[\'\:]').findall(renditions[0])

        bitrates = re.compile('src = {(.+?):(.+?)}').findall(httpdata);
        if len(bitrates) > 0:
            urls = re.compile('[\'\"](.+?)[\'\"]').findall(bitrates[0][1])
            markizalog.logDebug('URLS=%s'%urls)
            for num, url in enumerate(urls):
                markizalog.logDebug('URL=%s\nNUM=%s'%(url, num))
                if num < len(renditions):
                    result.append(self.addLink(renditions[num],url))
                else:
                    result.append(self.addLink(name,url))
        else:
            markizalog.logError('Chyba - Video nejde prehrat')

        return result

    def list(self, url):
        result = []
        name, url, mode = self.getMode(url)
        markizalog.logDebug('list hit name=%s, mode=%s, url=%s'%(name, mode, url))
        if mode==5:
            # az
            doc = read_page(url)
            for article in doc.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = article.a['title'].encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                result.append(self.addDir(title,url,2, thumb))
        elif mode==4:
            # podsekce na strance
            doc = read_page(url)
            sectionName = doc.find('h3', 'e-articles-title', text=name)
            section = sectionName.findParent('section')
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.a['title'].encode('utf-8')
                title2 = article.find('div', 'e-date').span.getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                result.append(self.addDir(title, url, 3, thumb))
        elif mode==2:
            # episodes
            result = self.episodes(url)
            pass
        elif mode==9:
            # top relacie
            result = self.top(url)
            pass
        elif mode==8:
            # new epizody
            result = self.newEpisodes(url)
            pass
        elif mode==6:
            # najsledovanejsie
            result = self.mostViewed(url)
            pass
        elif mode==7:
            # odporucane
            result = self.recommended(url)
            pass
        elif mode==3:
            # video link
            result = self.videoLink(url)
        return result

    def categories(self):
        result = []
        result.append(self.addDir('Relácie a seriály A-Z','http://videoarchiv.markiza.sk/relacie-a-serialy',5))
        # @TODO
        result.append(self.addDir('Televízne noviny','http://videoarchiv.markiza.sk/video/televizne-noviny',2))
        result.append(self.addDir('TOP relácie','http://videoarchiv.markiza.sk', 9))
        result.append(self.addDir('Najnovšie epizódy','http://videoarchiv.markiza.sk',8))
        result.append(self.addDir('Najsledovanejšie','http://videoarchiv.markiza.sk',6))
        result.append(self.addDir('Odporúčame','http://videoarchiv.markiza.sk',7))
        return result

    def resolve(self, item, captcha_cb=None, select_cb=None):
        markizalog.logDebug('resolve hit ...')
        result = []
        itm = self.video_item()
        #item['title'] = v['title'] or details['name']
        #item['date'] = details['date']
        #item['lenght'] = details['duration']
        itm['url'] = item['url']
        itm['surl'] = item['title']
        itm['title'] = item['title']
        #item['img'] = v['image']
        #item['plot'] = v['description']
        markizalog.logDebug("itemurl=%s"%itm['url'])
        result.append(itm)
        if len(result) > 0 and select_cb:
            return select_cb(result)
        return result
    