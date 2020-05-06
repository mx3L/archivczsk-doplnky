# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,string,time,base64,datetime
from urlparse import urlparse, urlunparse, parse_qs
import aes
import json
try:
    import hashlib
except ImportError:
    import md5

from Components.config import config
from parseutils import *
from util import addDir, addLink, addSearch, getSearch
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__baseurl__ = 'http://videoarchiv.markiza.sk'
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
addon =  ArchivCZSK.get_xbmc_addon('plugin.video.markiza')
profile = addon.getAddonInfo('profile')
__settings__ = addon
home = __settings__.getAddonInfo('path')
icon =  os.path.join( home, 'icon.png' )
fanart = os.path.join( home, 'fanart.jpg' )
loginurl = 'https://moja.markiza.sk/'
settings = {'username': __settings__.get_setting('markiza_user'), 'password': __settings__.get_setting('markiza_pass')}
cookiepath = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'markiza.cookies')

class loguj(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False
    LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'markiza.log')

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
            print "####MARKIZA#### write log failed!!!"
            pass
        finally:
            print "####MARKIZA#### [" + type + "] " + msg

def fetchUrl(url):
#    loguj.logInfo("fetchUrl " + url)
    httpdata = ''	
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    resp = urllib2.urlopen(req)
    httpdata = resp.read()
    resp.close()
    return httpdata

def get_url(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    return data

def OBSAH():
    addDir('Relácie a seriály A-Z','http://videoarchiv.markiza.sk/relacie-a-serialy',5,icon)
    addDir('Televízne noviny','http://videoarchiv.markiza.sk/video/televizne-noviny',2,icon)
    addDir('TOP relácie','http://videoarchiv.markiza.sk',9,icon)
    addDir('Najnovšie epizódy','http://videoarchiv.markiza.sk',8,icon)
    addDir('Live Markiza','https://videoarchiv.markiza.sk/live/1-markiza',10,icon,1)
    addDir('Live Doma','https://videoarchiv.markiza.sk/live/3-doma',10,icon,1)
    addDir('Live Dajto','https://videoarchiv.markiza.sk/live/2-dajto',10,icon,1)

def HOME_NEJSLEDOVANEJSI(url):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles b-section-articles-primary my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Najsledovanejšie':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = article.a.find('div', {'class': 'e-text-row'}).getText(" ").encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb)

def HOME_DOPORUCUJEME(url):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles b-section-articles-primary my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Odporúčame':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = article.a.find('div', {'class': 'e-info'}).getText(" ").encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb)

def HOME_POSLEDNI(url):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section'):
        if section.div.h3 and section.div.h3.getText(" ").encode('utf-8') == 'Najnovšie epizódy':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = article.a.find('div', {'class': 'e-info'}).getText(" ").encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb)

def HOME_TOPPORADY(url):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'TOP relácie':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = article.a['title'].encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,2,thumb)

def CATEGORIES(url):
#    print 'CATEGORIES *********************************' + str(url)
    doc = read_page(url)

    for article in doc.findAll('article'):
        url = article.a['href'].encode('utf-8')
        title = article.a['title'].encode('utf-8')
        thumb = article.a.div.img['data-original'].encode('utf-8')
        addDir(title,url,2,thumb)

def EPISODES(url):
#    print 'EPISOD9ES *********************************' + str(url)
    try:
        doc = read_page(url)
    except urllib2.HTTPError:
        addLink("[COLOR red]Stranka nenalezena: "+url+"[/COLOR]","#",None,"")
#        xbmcgui.Dialog().ok('Chyba', 'CHYBA 404: STRÁNKA NEBOLA NÁJDENÁ', '', '')
        return False

    for article in doc.findAll('article', 'b-article b-article-text b-article-inline'):
        url = article.a['href'].encode('utf-8')
        title = article.a.find('div', {'class': 'e-info'}).getText(" ").encode('utf-8').strip() 
        thumb = article.a.div.img['data-original'].encode('utf-8')
        addDir(title,url,3,thumb)

    for section in doc.findAll('section', 'b-main-section'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Celé epizódy':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                if (article.a.find('div', {'class': 'e-date'})):
                   title = 'Celé epizódy - ' + article.a.find('div', {'class': 'e-info'}).getText(" ").encode('utf-8')
                else:
                   title = 'Celé epizódy - ' + article.a['title'].encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb)

        if section.div.h3.getText(" ").encode('utf-8') == 'Mohlo by sa vám páčiť':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = 'Mohlo by sa vám páčiť - ' + article.a.find('div', {'class': 'e-info'}).getText(" ").encode('utf-8') 
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb)

        if section.div.h3.getText(" ").encode('utf-8') == 'Zo zákulisia':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = 'Zo zákulisia - ' + article.a['title'].encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb)
                
def VIDEOLINK(url):
#    print 'VIDEOLINK *********************************' + str(url)

    doc = read_page(url)
    main = doc.find('main')
    if (not main.find('iframe')):
       addLink("[COLOR red]Platnost tohoto videa už vypršala[/COLOR]","#",None,"")
#       xbmcgui.Dialog().ok('Chyba', 'Platnost tohoto videa už vypršala', '', '')
       return False
    url = main.find('iframe')['src']
    httpdata = fetchUrl(url)
    httpdata = httpdata.replace("\r","").replace("\n","").replace("\t","")
    if '<title>Error</title>' in httpdata:
        error=re.search('<h2 class="e-title">(.*?)</h2>', httpdata).group(1) #Video nie je dostupné vo vašej krajine
        addLink("[COLOR red]"+error+"[/COLOR]","#",None,"")
#        xbmcgui.Dialog().ok('Chyba', error, '', '')
        return False

    url = re.search('src = {\s*\"hls\": [\'\"](.+?)[\'\"]\s*};', httpdata)
    if (url):
       url=url.group(1)

       thumb = re.search('<meta property="og:image" content="(.+?)">', httpdata)
       thumb = thumb.group(1) if thumb else ''
       desc = re.search('<meta name="description" content="(.+?)">', httpdata)
       desc = desc.group(1) if desc else ''
       name = re.search('<meta property="og:title" content="(.+?)">', httpdata)
       name = name.group(1) if name else '?'

       httpdata = fetchUrl(url)

       streams = re.compile('RESOLUTION=\d+x(\d+).*\n([^#].+)').findall(httpdata) 
       url = url.rsplit('/', 1)[0] + '/'
       streams.sort(key=lambda x: int(x[0]),reverse=True)
       for (bitrate, stream) in streams:
           bitrate=' [' + bitrate + 'p]'
           addLink(name + bitrate,url + stream,thumb,desc)

    else:
       #televizne noviny
       url = re.search('relatedLoc: [\'\"](.+?)[\'\"]', httpdata).group(1)
       url = url.replace("\/","/")
       httpdata = fetchUrl(url)
       
       decoded=json.loads(httpdata)
       for chapter in decoded["playlist"]:
          name=chapter["contentTitle"]
          url=chapter["src"]["hls"]
          url=url.rsplit('/', 1)[0] + '/' + 'index-f3-v1-a1.m3u8' #auto select 720p quality
          thumb=chapter.get("thumbnail",'')
          desc=chapter["contentTitle"]
          addLink(name,url,thumb,desc)

def LIVE(url, relogin=False):
    if not (settings['username'] and settings['password']):
        addLink("[COLOR red]Nastavte prosím moja.markiza.sk konto[/COLOR]","#",None,"")
        return
#        xbmcgui.Dialog().ok('Chyba', 'Nastavte prosím moja.markiza.sk konto', '', '')
#        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
#        raise RuntimeError
    cj = MozillaCookieJar()	
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    if not relogin:
       try:
          cj.load(cookiepath)
       except IOError:
          relogin=True
    if relogin:
       response = opener.open(loginurl).read()
       token = re.search(r'name=\"_token_\" value=\"(\S+?)\">',response).group(1)
       logindata = urllib.urlencode({'email': settings['username'], 'password': settings['password'], '_token_': token, '_do': 'content1-loginForm-form-submit' }) + '&login=Prihl%C3%A1si%C5%A5+sa'
       opener.open(loginurl, logindata)
       log('Saving cookies') 
       cj.save(cookiepath)
   
    response = opener.open(url).read()
    link = re.search(r'<iframe src=\"(\S+?)\"',response).group(1) #https://videoarchiv.markiza.sk/api/v1/user/live
    try:
       response = opener.open(link).read()
    except urllib2.HTTPError: #handle expired cookies
       if relogin:
          addLink("[COLOR red]Skontrolujte prihlasovacie údaje[/COLOR]","#",None,"")
          return
#          xbmcgui.Dialog().ok('Chyba', 'Skontrolujte prihlasovacie údaje', '', '')
#          raise RuntimeError # loop protection
       else:
          LIVE(url, relogin=True) 
          return
    opener.addheaders = [('Referer',link)]
    link = re.search(r'<iframe src=\"(\S+?)\"',response).group(1) #https://media.cms.markiza.sk/embed/
    response = opener.open(link).read()
    link = re.search(r'\"hls\": \"(\S+?)\"',response).group(1) #https://h1-s6.c.markiza.sk/hls/markiza-sd-master.m3u8
    response = opener.open(link).read()
    
    cookies='|Cookie='
    for cookie in cj:
      cookies+=cookie.name+'='+cookie.value+';'
    cookies=cookies[:-2]
#    play_item = xbmcgui.ListItem(path=link+cookies)
#    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=play_item)
	
url=None
name=None
thumb=None
mode=None

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

#print "Mode: "+str(mode)
#print "URL: "+str(url)
#print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
#        STATS("OBSAH", "Function")
        OBSAH()

elif mode==6:
#        STATS("HOME_NEJSLEDOVANEJSI", "Function")
        HOME_NEJSLEDOVANEJSI(url)

elif mode==7:
#        STATS("HOME_DOPORUCUJEME", "Function")
        HOME_DOPORUCUJEME(url)

elif mode==8:
#        STATS("HOME_POSLEDNI", "Function")
        HOME_POSLEDNI(url)

elif mode==9:
#        STATS("HOME_TOPPORADY", "Function")
        HOME_TOPPORADY(url)

elif mode==5:
#        STATS("CATEGORIES", "Function")
        CATEGORIES(url)

elif mode==2:
#        STATS("EPISODES", "Function")
        EPISODES(url)

elif mode==3:
#        STATS("VIDEOLINK", "Function")
        VIDEOLINK(url)

elif mode==10:
#        STATS("LIVE", "Function")
        LIVE(url)
