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

import util
from provider import ContentProvider

_htmlParser_ = HTMLParser.HTMLParser()
_rssUrl_ = 'http://video.aktualne.cz/rss/dvtv/'

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
        item = item.copy()
        httpdata = util.request(item['url'])
        videos = re.compile('{[^i]*?image.*?sources:[^]]*?][^}]*?}', re.S).findall(httpdata)
        if videos:
            for video in videos:
                image = 'http:' + re.compile('image: ?\'([^\']*?)\'').search(video).group(1).strip()
                title = _htmlParser_.unescape(re.compile('title: ?\'([^\']*?)\'').search(video).group(1).strip())
                description = re.compile('description: ?\'([^\']*?)\'').search(video);
                if description:
                    description = _htmlParser_.unescape(description.group(1).strip())
                sources = re.compile('sources: ?(\[[^\]]*?])', re.S).search(video).group(1)
                if sources:
                    versions = re.compile('{[^}]*?}', re.S).findall(sources)
                    if versions:
                        for version in versions:
                            url = re.compile('"file":"([^"]*)"').search(version).group(1).replace('\/','/').strip()
                            mime = re.compile('"type":"([^"]*)"').search(version).group(1).replace('\/','/').strip()
                            quality = re.compile('"label":"([^"]*)"').search(version).group(1).strip()
                            if mime =='video/webm':
                                continue
                            vitem = self.video_item()
                            vitem['title'] = title
                            vitem['surl'] = str(len(title))
                            vitem['img'] = image
                            vitem['url'] = url
                            vitem['quality'] = quality
                            result.append(vitem)
        result.sort(key=lambda x:x['quality'], reverse=True)
        if len(result) > 0 and select_cb:
            return select_cb(result)
        return result
