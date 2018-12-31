# source from dmd-czech dtvt plugin - https://code.google.com/p/dmd-xbmc/source/detail?r=206
# modded by mx3L for easy port to enigma2 archivczsk plugin

import calendar
import cookielib
import re
import urllib
import urllib2
import HTMLParser
import xml.etree.ElementTree as ET
import email.utils as eut
import time
import os,datetime
import simplejson as json
import util
from Components.config import config
from provider import ContentProvider

_htmlParser_ = HTMLParser.HTMLParser()
_rssUrl_ = 'http://video.aktualne.cz/rss/dvtv/'


class dvtvlog(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False
    LOG_FILE = ""

    @staticmethod
    def logDebug(msg):
        if dvtvlog.logDebugEnabled:
            dvtvlog.writeLog(msg, 'DEBUG')

    @staticmethod
    def logInfo(msg):
        dvtvlog.writeLog(msg, 'INFO')

    @staticmethod
    def logError(msg):
        dvtvlog.writeLog(msg, 'ERROR')

    @staticmethod
    def writeLog(msg, type):
        try:
            if not dvtvlog.logEnabled:
                return
            # if log.LOG_FILE=="":
            dvtvlog.LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(), 'dvtv.log')
            f = open(dvtvlog.LOG_FILE, 'a')
            dtn = datetime.datetime.now()
            f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg + '')
            f.close()
        except:
            print "####DVTV#### write log failed!!!"
            pass
        finally:
            print "####DVTV#### [" + type + "] " + msg

class DVTVContentProvider(ContentProvider):

    def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'dvtv.cz', 'http://video.aktualne.cz/dvtv/', username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['categories','resolve']

    def categories(self):
        return self.list("0")

    def list(self, offset):
        result = []
        url = _rssUrl_
        offset = int(offset)
        if offset > 0:
            url+="?offset=%d"%(offset)
        rss = util.request(url)
        root = ET.fromstring(rss)
        for item in root.find('channel').findall('item'):
            link  = item.find('link').text
            title = item.find('title').text
            description = item.find('description').text
            contentEncoded = item.find('{http://purl.org/rss/1.0/modules/content/}encoded').text
            extra = item.find('{http://i0.cz/bbx/rss/}extra')
            subtype = extra.get('subtype')
            dur = extra.get('duration')
            datetime = eut.parsedate(item.find('pubDate').text.strip())
            date = time.strftime('%d.%m.%Y', datetime)
            image = re.compile('<img.+?src="([^"]*?)"').search(contentEncoded).group(1)
            vitem = self.video_item()
            vitem['title'] = title
            if dur:
                d = re.compile('([0-9]?[0-9]):([0-9][0-9])').search(dur.strip())
                duration = (int(d.group(1))*60+int(d.group(2)))
                vitem['duration'] = duration
            if subtype == 'playlist':
                pass
            vitem['img'] = image
            vitem['plot'] = description
            vitem['url'] = link
            self._filter(result, vitem)
        nitem = self.dir_item()
        nitem['type'] = 'next'
        nitem['url'] = str(offset+30)
        self._filter(result, nitem)
        return result

    def resolve(self, item, captcha_cb=None, select_cb=None):
        result = []
        twice = False
        item = item.copy()
        httpdata = util.request(item['url'])
        videos = re.compile('tracks:(?:.(?!\}\]\}))*.\}\]\}', re.S).findall(httpdata)
        if len(videos) > 1:  # last item in playlist is doubled on page
            del videos[-1]
        if videos:
            title = re.compile('<meta property="og:title" content=".*">').search(httpdata).group(0)
            title = re.sub('<meta property="og:title" content="', '', title).replace('">', '')
            image = re.compile('<meta property="og:image" content=".*">').search(httpdata).group(0)
            image = re.sub('<meta property="og:image" content="', '', image).replace('">', '')
            description = re.compile('<meta property="og:description" content=".*">').search(httpdata).group(0)
            description = re.sub('<meta property="og:description" content="', '', description).replace('">', '')
            for video in videos:
                video = re.sub(re.compile('\sadverttime:.*', re.S), '', video)  # live streams workaround
                video = video.replace('tracks: ', '')
                video = re.sub(r'[,\w]*$', '', video)
                detail = json.loads(video)
                if detail.has_key('MP4'):
                    sources = detail['MP4']
                    for version in sources:
                        url = version['src']
                        quality = version['label']
                        vitem = self.video_item()
                        vitem['title'] = title
                        vitem['surl'] = str(len(title))
                        vitem['img'] = image
                        vitem['url'] = url
                        vitem['quality'] = quality
                        result.append(vitem)
        result.sort(key=lambda x:(len(x['quality']), x['quality']), reverse=True)
        if len(result) > 0 and select_cb:
            return select_cb(result)
        return result
