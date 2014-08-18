# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,string,time,base64,datetime
from urlparse import urlparse
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
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
addon =  ArchivCZSK.get_xbmc_addon('plugin.video.dmd-czech.novaplus')
profile = addon.getAddonInfo('profile')
__settings__ = addon
home = __settings__.getAddonInfo('path')
icon =  os.path.join( home, 'icon.png' )
nexticon = os.path.join( home, 'nextpage.png' )
fanart = os.path.join( home, 'fanart.jpg' )
nova_service_url = 'http://cdn-lb.cdn.cra.cz/'
nova_app_id = 'nova-vod'

def OBSAH():
    addDir('Nejnovější','http://novaplus.nova.cz',6,icon,1)
    addDir('Seriály a pořady','http://novaplus.nova.cz/porady/',5,icon,1)
    addDir('Televizní noviny','http://novaplus.nova.cz/porad/televizni-noviny',1,icon,1)

def NEW(url,page):
    doc = read_page(url)
    items = doc.find('div', 'latest_videos')
    items = items.find('div', 'items')
    for item in items.findAll('div','item'):
            item2 = item.find('h3')
            item3 = item.find('div','img')
            url = item3.h3.a['href'].encode('utf-8')
            title = item3.h3.a.getText(" ").encode('utf-8')
            thumb = item3.a.span.img['src']
            print title,url,thumb
            addDir(title,__baseurl__+url,3,thumb,1)

def TN(url,page):
    doc = read_page(url)
    items = doc.find('div', 'items')
    for item in items.findAll('div','item'):
            item2 = item.find('h3')
            item3 = item.find('div','img')
            url = item2.a['href'].encode('utf-8')
            title = item2.a.getText(" ").encode('utf-8')
            thumb = item3.a.span.img['src']
            print title,url,thumb
            addDir(title,__baseurl__+url,3,thumb,1)

def CATEGORIES(url,page):
    doc = read_page(url)
    items = doc.find('ul', 'show-list')
    for item in items.findAll('li'):
            if re.search('ad-placeholder', str(item), re.U):
                continue
            url = item.a['href'].encode('utf-8')
            title = item.a.span.getText(" ").encode('utf-8')
            match = re.compile('porad/(.+?)').findall(url)
            thumb = 'http://static.cz.prg.cmestatic.com/static/cz/microsites/avod/img/porady/'+match[0]+'.jpg'
            addDir(title,__baseurl__ + url,2,thumb,1)


def INDEX(url,page):
    doc = read_page(url)
    items = doc.find('div', 'show_videos')
    items = items.find('div', 'items')
    for item in items.findAll('div','item'):
            item2 = item.find('h3')
            item3 = item.find('div','img')
            url = item3.h3.a['href'].encode('utf-8')
            title = item3.h3.a.getText(" ").encode('utf-8')
            thumb = item3.a.img['src']
            if re.search('voyo.nova.cz', str(url), re.U):
                continue
            addDir(title,__baseurl__+url,3,thumb,1)


def VIDEOLINK(url,name):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    thumb = re.compile('<meta property="og:image" content="(.+?)" />').findall(httpdata)
    popis = re.compile('<meta property="og:description" content="(.+?)" />').findall(httpdata)
    config = re.compile('config.php?(.+?)"></script>', re.S).findall(httpdata)
    config = 'http://tn.nova.cz/bin/player/flowplayer/config.php'+config[0]
    try:
        desc = popis[0]
    except:
        desc = name
    req = urllib2.Request(config)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile("'(.+?)';").findall(httpdata)
    key = 'EaDUutg4ppGYXwNMFdRJsadenFSnI6gJ'
    aes_decrypt = aes.decrypt(match[0],key,128).encode('utf-8')
    aes_decrypt = aes_decrypt.replace('\/','/')
    secret_token = re.compile('secret":"(.+?)"', re.S).findall(aes_decrypt)
    mediaid = re.compile('"mediaId":(.+?),').findall(aes_decrypt)
    datum = datetime.datetime.now()
    timestamp = datum.strftime('%Y%m%d%H%M%S')
    videoid = urllib.quote(nova_app_id + '|' + mediaid[0])
    md5hash = nova_app_id + '|' + mediaid[0] + '|' + timestamp + '|' + secret_token[0]
    try:
        md5hash = hashlib.md5(md5hash)
    except:
        md5hash = md5.new(md5hash)
    signature = urllib.quote(base64.b64encode(md5hash.digest()))
    config = nova_service_url + '?t=' + timestamp + '&d=1&tm=nova&h=0&c='+videoid+ '&s='+signature
    req = urllib2.Request(config)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    baseurl = re.compile('<baseUrl>(.+?)</baseUrl>').findall(httpdata)
    streamurl = re.compile('<media>\s<quality>(.+?)</quality>.\s<url>(.+?)</url>\s</media>').findall(httpdata)
    swfurl = 'http://voyo.nova.cz/static/shared/app/flowplayer/13-flowplayer.commercial-3.1.5-19-003.swf'
    for kvalita,odkaz in streamurl:
        rtmp_url = baseurl[0]+'/'+odkaz
        addLink(name,rtmp_url,thumb[0],desc)


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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Page: "+str(page)

if mode==None or url==None or len(url)<1:
        print ""
        OBSAH()

elif mode==1:
        print ""+url
        print ""+str(page)
        TN(url,page)

elif mode==6:
        print ""+url
        print ""+str(page)
        NEW(url,page)

elif mode==5:
        print ""+url
        print ""+str(page)
        CATEGORIES(url,page)

elif mode==2:
        print ""+url
        print ""+str(page)
        INDEX(url,page)

elif mode==3:
        print ""+url
        try:
            VIDEOLINK(url, name)
        except IndexError:
            INDEX(url, name)
