# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,string,time,base64,datetime
from urlparse import urlparse, urlunparse, parse_qs
import aes
try:
    import hashlib
except ImportError:
    import md5

from parseutils import *
from util import addDir, addLink, addSearch, getSearch
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__baseurl__ = 'http://novaplus.nova.cz'
__dmdbase__ = 'http://iamm.uvadi.cz/xbmc/voyo/'
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
addon =  ArchivCZSK.get_xbmc_addon('plugin.video.novaplus')
profile = addon.getAddonInfo('profile')
__settings__ = addon
home = __settings__.getAddonInfo('path')
icon =  os.path.join( home, 'icon.png' )
fanart = os.path.join( home, 'fanart.jpg' )

def get_url(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    return data

class loguj(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False
    LOG_FILE = os.path.join(home,'novaplus.log')

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
            print "####NOVAPLUS#### write log failed!!!"
            pass
        finally:
            print "####NOVAPLUS#### [" + type + "] " + msg

def OBSAH():
    addDir('Úvodní stránka','http://novaplus.nova.cz/',6,icon,1)
    addDir('Seriály a pořady','http://novaplus.nova.cz/porady/',5,icon,1)
    addDir('Televizní noviny','http://novaplus.nova.cz/porad/televizni-noviny',2,icon,1)
    addDir('Víkend','http://novaplus.nova.cz/porad/vikend',2,icon,1)
    addDir('Koření','http://novaplus.nova.cz/porad/koreni',2,icon,1)
    addDir('Střepiny','http://novaplus.nova.cz/porad/strepiny',2,icon,1)


def HOMEPAGE(url,page):  # new by MN
    html = get_url(url)

    # carousel
    sections = re.search("<section class=\"b-main-section\">.*?<div class=\"b-carousel\">.*?<a href=\"(.*?)\" title=\"(.*?)\">.*?<img.*?data-original=\"(.*?)\"", html, re.S)
    if sections != None:
        addDir(sections.group(2).replace('&nbsp;', ' '), sections.group(1), 3, sections.group(3), 1);

    # articles
    sections = re.findall("<h3 class=\"e-articles-title\">(.*?)</h3>(.*?)</section>", html, re.S)
    if sections != None:
        for section in sections:
            category = re.sub(r'<[^>]*?>', '',section[0]).replace('&nbsp;', ' ').replace(' ','').replace('\n','')
            articles = re.findall("<article(.*?)</article>", section[1], re.S)
            if category == "TOP POŘADY":
                Hmode = 2
            else:
                Hmode = 3
            if articles != None:
                for article in articles:
                    url = re.search("<a href=\"(.*?)\"", article, re.S) or ""
                    title = re.search("<a.*?title=\"(.*?)\"", article, re.S) or ""
                    thumb = re.search("<img.*?data-original=\"(.*?)\"", article, re.S) or ""
                    if url != "" and title != "":
                        if thumb != "":
                            addDir(category + " - " + title.group(1).replace('&nbsp;', ' '),url.group(1),Hmode,thumb.group(1),1)
                        else:
                            addDir(category + " - " + title.group(1).replace('&nbsp;', ' '),url.group(1),Hmode,None,1)
            else:
                addLink("[COLOR red]Chyba načítání pořadů[/COLOR]","#",None,"")
    else:
        addLink("[COLOR red]Chyba načítání kategorie[/COLOR]","#",None,"")

def CATEGORIES(url,page):  # rewrite by MN
    html = get_url(url)
    section = re.search("<div class=\"b-show-listing\".*?ady</h3>(.*?)</section>", html, re.S)
    if section != None:
        articles = re.findall("<article(.*?)</article>", section.group(1), re.S)
        if articles != None:
            for article in articles:
                url = re.search("<a href=\"(.*?)\"", article, re.S) or ""
                title = re.search("<a.*?title=\"(.*?)\"", article, re.S) or ""
                thumb = re.search("<img.*?data-original=\"(.*?)\"", article, re.S) or ""
                if url != "" and title != "":
                    if thumb != "":
                        addDir(title.group(1).replace('&nbsp;', ' '),url.group(1),2,thumb.group(1),1)
                    else:
                        addDir(title.group(1).replace('&nbsp;', ' '),url.group(1),2,None,1)
        else:
            addLink("[COLOR red]Chyba načítání pořadů[/COLOR]","#",None,"")
    else:
        addLink("[COLOR red]Chyba načítání kategorie[/COLOR]","#",None,"")

def EPISODES(url,name): # rewrite by MN
    html = get_url(url)

    # zalozky
    section = re.search("<nav class=\"navigation js-show-detail-nav\">(.*?)</nav>", html, re.S)
    if section != None:
        lis = re.findall("<li(.*?)</li>", section.group(1), re.S)
        if lis != None:
            for li in lis:
                url2 = re.search("<a href=\"(.*?)\"", li, re.S) or ""
                title = re.search("<a.*?title=\"(.*?)\"", li, re.S) or ""
                if url2 != "" and title != "":
                    if url == url2.group(1):
                        addDir('[I][COLOR yellow]' + title.group(1).replace('&nbsp;', ' ') + '[/COLOR][/I]',url2.group(1),2,None,1)
                    else:
                        addDir('[COLOR yellow]' + title.group(1).replace('&nbsp;', ' ') + '[/COLOR]',url2.group(1),2,None,1)

    # dalsi dily poradu
    articles = re.findall("<article class=\"b-article-news m-layout-playlist\">(.*?)</article>", html, re.S)
    if articles != None:
        for article in articles:
            url = re.search("<a href=\"(.*?)\"", article, re.S) or ""
            if url != "" and url.group(1).find('voyo') == -1:
                title = re.search("<a.*?title=\"(.*?)\"", article, re.S) or ""
                thumb = re.search("<img.*?data-original=\"(.*?)\"", article, re.S) or ""
                if thumb != "":
                    addDir(title.group(1).replace('&nbsp;', ' '),url.group(1),3,thumb.group(1),1)
                else:
                    addDir(title.group(1).replace('&nbsp;', ' '),url.group(1),3,None,1)

def VIDEOLINK(url,name):    # rewrite by MN
    html = get_url(url)

    # nalezeni hlavniho article
    aarticle = re.search("<div class=\"b-article b-article-main\">(.*?)", html, re.S)

    # pokud hlavni article neexistuje, jsme na specialni strance se seznamem dilu a hledame odkaz
    if aarticle is None and html.find('property="og:url" content="http://voyo.nova.cz/') != -1:
        addLink("[COLOR red]Chyba: Video lze přehrát jen na voyo.nova.cz[/COLOR]","#",None,"")
        return

    # pokud stale hlavni article neexistuje, chyba
    if aarticle is None:
        article = None
        print "Na stránce nenalezena sekce s videi. Program nebude fungovat správně."+url
        addLink("[COLOR red]Na stránce nenalezena sekce s videi: "+url+"[/COLOR]","#",None,"")
        #xbmcgui.Dialog().ok("Nova Plus TV Archiv", "Na stránce nenalezena sekce s videi. Program nebude fungovat správně.", url)
        return
    else:
        article = aarticle.group(1)

    # nazev
    aname = re.search("<h2 class=\"subtitle\">(.*?)</h2>", html, re.S)
    if aname is None:
        name = "Jméno pořadu nenalezeno"
    else:
        name = aname.group(1)

    # popis (nemusi byt vzdy uveden)
    adesc = re.search("<div class=\"e-description\">(.*?)</div>", article, re.S)
    if adesc is None:
        desc = ""
    else:
        desc = adesc.group(1).re.sub(r'<[^>]*?>', '', value).replace('&nbsp;', ' ')

    # nalezeni iframe
    iframe = re.search("<div class=\"video-holder\">.*?iframe src=\"(.*?)\"", html, re.S)
    if iframe != None:
        url = iframe.group(1)
    else:
        url = None
    print ' - iframe src ' + url

    # nacteni a zpracovani iframe
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()

    httpdata   = httpdata.replace("\r","").replace("\n","").replace("\t","")

    thumb = re.compile('<meta property="og:image" content="(.+?)">').findall(httpdata)
    thumb = thumb[0] if len(thumb) > 0 else ''

    re_src = re.compile('var src = \{(.*?)\}').findall(httpdata);
    if len(re_src) > 0:
      urls = re.compile('\"(.*?)\"\:\"(.*?)\"\,?').findall(re_src[0].replace(" ", ""))

      for num, url in enumerate(urls):
        addLink('[B]' + name.replace('&nbsp;', ' ') + '[/B]',url[1],thumb,desc.replace('&nbsp;', ' '))
    else:   # jeste zkusim najit mpd (MN)
        urls = re.search("\"src\":\"(.*?)\.m3u8\"",httpdata,re.M)
        if urls != None:
            addLink('[B] DRM! - ' + name.replace('&nbsp;', ' ') + '[/B]',urls.group(1).replace("\\","")+".m3u8",thumb,desc.replace('&nbsp;', ' '))
        else:
            print 'Chyba: Video nelze přehrát'
            addLink("[COLOR red]Chyba: Video nelze přehrát[/COLOR]","#",None,"")
            #xbmcgui.Dialog().ok('Chyba', 'Video nelze přehrát', '', '')

    # dalsi dily poradu
#    for article in doc.findAll('article', 'b-article b-article-text b-article-inline'):
#        url = article.a['href'].encode('utf-8')
#        title = article.a['title'].encode('utf-8')
#        thumb = article.a.div.img['data-original'].encode('utf-8')
#        addDir(title,url,3,thumb,1)

    # stranka poradu
    section = re.search("<h1 class=\"title\"><a href=\"(.*?)\">(.*?)</a>", html, re.S)
    if section != None:
        url = section.group(1)
        title = section.group(2)+' - stránka pořadu'
        thumb = None
        addDir(title.replace('&nbsp;', ' '),url,2,thumb,1)

url=None
name=None
thumb=None
mode=None
page=None

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

#print "Mode: %s, Url: %s, Name: %s, Page: %s"%(mode, url, name, page)

if mode==None or url==None or len(url)<1:
        OBSAH()
elif mode==6:
        HOMEPAGE(url,page)
elif mode==5:
        CATEGORIES(url,page)
elif mode==2:
        EPISODES(url,page)
        #VIDEOLINK(url, page)
elif mode==3:
        VIDEOLINK(url,page)