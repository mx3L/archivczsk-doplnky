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
addon =  ArchivCZSK.get_xbmc_addon('plugin.video.dmd-czech.novaplus')
profile = addon.getAddonInfo('profile')
__settings__ = addon
home = __settings__.getAddonInfo('path')
icon =  os.path.join( home, 'icon.png' )
fanart = os.path.join( home, 'fanart.jpg' )

def OBSAH():
    addDir('Seriály a pořady','http://novaplus.nova.cz/porady/',5,icon,1)
    addDir('Televizní noviny','http://novaplus.nova.cz/porad/televizni-noviny',1,icon,1)
    addDir('TOP pořady','http://novaplus.nova.cz',9,icon,1)
    addDir('Poslední epizody','http://novaplus.nova.cz',8,icon,1)
    addDir('Nejsledovanější','http://novaplus.nova.cz',6,icon,1)
    addDir('Nova Plus Originals','http://novaplus.nova.cz',10,icon,1)
    addDir('Doporučujeme','http://novaplus.nova.cz',7,icon,1)

def HOME_NEJSLEDOVANEJSI(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles b-section-articles-primary my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Nejsledovanější':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.h3.getText(" ").encode('utf-8')
                title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb,1)

def HOME_DOPORUCUJEME(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles b-section-articles-primary my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Doporučujeme':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.h3.getText(" ").encode('utf-8')
                title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb,1)

def HOME_POSLEDNI(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Poslední epizody':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.h3.getText(" ").encode('utf-8')
                title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb,1)

def HOME_TOPPORADY(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section my-sm-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'TOP pořady':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = article.a['title'].encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,2,thumb,1)

def HOME_ORIGINALS(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Nova Plus Originals':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.h3.getText(" ").encode('utf-8')
                title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb,1)

def CATEGORIES(url,page):
    #print 'CATEGORIES *********************************' + str(url)
    doc = read_page(url)

    for article in doc.findAll('article'):
        url = article.a['href'].encode('utf-8')
        title = article.a['title'].encode('utf-8')
        thumb = article.a.div.img['data-original'].encode('utf-8')
        addDir(title,url,1,thumb,1)

def FULL_EPISODES(url,page):
    #print 'FULL EPISODES *********************************' + str(url)
    doc = read_page(url)

    section = doc.find('section', 'b-main-section')
    if section.div.h3.getText(" ").encode('utf-8').startswith('Celé'):
        for article in section.findAll('article'):
            url = article.a['href'].encode('utf-8')
            title = article.a['title'].encode('utf-8')
            thumb = article.a.div.img['data-original'].encode('utf-8')
            addDir(title,url,3,thumb,1)
    else:
        for article in doc.findAll('article', 'b-article b-article-text b-article-inline'):
            url = article.a['href'].encode('utf-8')
            title = article.a['title'].encode('utf-8')
            thumb = article.a.div.img['data-original'].encode('utf-8')
            addDir(title,url,3,thumb,1)

def EPISODES(url,page):
    #print 'EPISODES *********************************' + str(url)
    doc = read_page(url)

    for article in doc.findAll('article', 'b-article b-article-text b-article-inline'):
        url = article.a['href'].encode('utf-8')
        title = article.a['title'].encode('utf-8')
        thumb = article.a.div.img['data-original'].encode('utf-8')
        addDir(title,url,3,thumb,1)

def VIDEOLINK(url,name):
    #print 'VIDEOLINK *********************************' + str(url)
    doc = read_page(url)
    main = doc.find('main')
    url = main.find('iframe')['src']

    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()

    httpdata   = httpdata.replace("\r","").replace("\n","").replace("\t","")

    thumb = re.compile('<meta property="og:image" content="(.+?)">').findall(httpdata)
    if (len(thumb) > 0):
      thumb = thumb[0]
    else:
      thumb = ''

    desc = re.compile('<meta name="description" content="(.+?)">').findall(httpdata)
    if (len(desc) > 0):
      desc = desc[0]
    else:
      desc = ''

    name = re.compile('<meta property="og:title" content="(.+?)">').findall(httpdata)
    if (len(name) > 0):
      name = name[0]
    else:
      name = '?'

    renditions = re.compile('renditions: \[(.+?)\]').findall(httpdata)
    if (len(renditions) > 0):
      renditions = re.compile('\'(.+?)\'').findall(renditions[0])

    bitrates = re.compile('src = {(.+?)\[(.+?)\]').findall(httpdata);
    if (len(bitrates) > 0):
      urls = re.compile('\'(.+?)\'').findall(bitrates[0][1])

      for num, url in enumerate(urls):
        addLink(renditions[num],url,thumb,desc)
    else:
      xbmcgui.Dialog().ok('Chyba', 'Video nelze přehrát', '', '')

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
        HOME_NEJSLEDOVANEJSI(url,page)
elif mode==7:
        HOME_DOPORUCUJEME(url,page)
elif mode==8:
        HOME_POSLEDNI(url,page)
elif mode==9:
        HOME_TOPPORADY(url,page)
elif mode==10:
        HOME_ORIGINALS(url,page)
elif mode==5:
        CATEGORIES(url,page)
elif mode==2:
        EPISODES(url,page)
elif mode==1:
        FULL_EPISODES(url,page)
elif mode==3:
        VIDEOLINK(url,page)