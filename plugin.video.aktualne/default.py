# -*- coding: utf-8 -*-
#
# plugin.video.aktualne
#
# (c) Michal Novotny
#
# original at https://www.github.com/misanov/
#
# Free for non-commercial use under author's permissions
# Credits must be used

import urllib2,urllib,re,sys,os,string,time,base64,datetime,json,aes
import email.utils as eut
from urlparse import urlparse, urlunparse, parse_qs
from Components.config import config
try:
    import hashlib
except ImportError:
    import md5

from parseutils import *
from util import addDir, addLink, addSearch, getSearch
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__baseurl__ = 'https://video.aktualne.cz/rss/'
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
addon =  ArchivCZSK.get_xbmc_addon('plugin.video.aktualne')
profile = addon.getAddonInfo('profile')
__settings__ = addon
home = __settings__.getAddonInfo('path')
icon =  os.path.join( home, 'icon.png' )
fanart = os.path.join( home, 'fanart.jpg' )

class loguj(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False
    LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'aktualne.log')

    @staticmethod
    def logDebug(msg):
        if loguj.logDebugEnabled:
            loguj.writeLog(msg, 'DEBUG')

    @staticmethod
    def logInfo(msg):
        loguj.writeLog(msg, 'INFO')

    @staticmethod
    def logError(msg):
        loguj.writeLog(msg, 'ERROR')

    @staticmethod
    def writeLog(msg, type):
        try:
            if not loguj.logEnabled:
                return
            f = open(loguj.LOG_FILE, 'a')
            dtn = datetime.datetime.now()
            f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
            f.close()
        except:
            pass

def get_url(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    return data

def listItems(offset):
    url = __baseurl__
    if offset > 0:
        url += '?offset=' + str(offset)
    html = get_url(url)
    articles = re.findall("<item>(.*?)</item>", html, re.S)
    if articles != None:
        for article in articles:
            try:
                url = re.search("<link>(.*?)</link>", article, re.S).group(1)
            except:
                url = ""
            try:
                category = re.search("<category.*?>(.*?)</category>", article, re.S).group(1) + " - "
            except:
                category = ""
            try:
                title = re.search("<title>(.*?)</title>", article, re.S).group(1)
            except:
                title = ""
            try:
                thumb = re.search("<img.*?src=\"(.*?)\"", article, re.S).group(1)
            except:
                thumb = ""
            try:
                pdate = re.search("<pubDate>(.*?)</pubDate>", article, re.S).group(1)
                pdats = re.sub('\s+',' ',pdate).strip()
                pdato = eut.parsedate(pdats)
                pdate = time.strftime('%d.%m. %H:%M',pdato) + " "
            except:
                pdate = ""
            if url != "" and title != "":
                if thumb != "":
                    addDir(pdate + category + title, url, 3, thumb, 1)
                else:
                    addDir(pdate + category + title, url, 3, None, 1)
        o = offset + 30
        u = __baseurl__ + '?offset=' + urllib.quote_plus(str(o))
        addDir('Další', u, None, None, 1)
    else:
        addLink("[COLOR red]Chyba načítání pořadů[/COLOR]","#",None,"")

def videoLink(url):
    html = get_url(url)

    title = re.search('<meta property="og:title" content="(.*?)"', html, re.S).group(1) or ""
    image = re.search('<meta property="og:image" content="(.*?)"', html, re.S).group(1) or None
    descr = re.search('<meta property="og:description" content="(.*?)"', html, re.S).group(1) or None

    bbx = re.search('BBXPlayer.setup\((.*?)\)', html, re.S)
    bbxg = bbx.group(1)
    bbxj = json.loads(re.sub('\s+',' ',bbxg).strip())

    if bbxj['tracks']['MP4']:
        for version in bbxj['tracks']['MP4']:
            addLink(version['label'] + " " + title,version['src'],image,descr)


url=None
name=None
thumb=None
mode=None
page=None
offset=0

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        page=int(params["page"])
except:
        pass
try:
        offset=int(urllib.unquote_plus(re.search('offset=([0-9]+)', url, re.S).group(1)))
except:
        pass

#loguj.logInfo(str(url))
#loguj.logInfo(str(offset))

if mode==None or url==None or len(url)<1:
        listItems(offset)
elif mode==3:
        videoLink(url)
