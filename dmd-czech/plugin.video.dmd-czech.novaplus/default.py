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
_UserAgent_ = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0'
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
    addDir('Nejsledovanější','http://novaplus.nova.cz',6,icon,1)
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
            id_porad = item['data-show-id']
            # pruhledna loga
            thumb = 'http://static.cz.prg.cmestatic.com/static/cz/microsites/avod/img/porady/logo/' + str(id_porad) + '.png'
            # loga s pozadim
            #thumb = 'http://static.cz.prg.cmestatic.com' + item.img['src']
            addDir(title,__baseurl__ + url,2,thumb,1)


def INDEX(url,page):
    doc = read_page(url)
    style = doc.find('div', id='extra_index')
    if style:
    # prvni styl stranky s poradem
        items = doc.find('div', id='extra_index')
        items = items.find('div', 'items')
        for item in items.findAll('div', 'item'):
                item2 = item.find('div', 'text')
                item3 = item.find('div', 'img')
                url = item3.a['href'].encode('utf-8')
                title = item2.h2.a.getText(" ").encode('utf-8')
                thumb = item3.a.img['src']
                if re.search('voyo.nova.cz', str(url), re.U):
                    continue
                addDir(title,__baseurl__+url,3,thumb,1)
 
    else:
    # druhy styl stranky s poradem
        items = doc.find('div', 'items')
        for item in items.findAll('div', 'item_container'):
                url = item.a['href'].encode('utf-8')
                if re.search('voyo.nova.cz', str(url), re.U):
                    continue
                item3 = item.find('div', 'img')
                url = item3.a['href'].encode('utf-8')
                title = item3.h3.a.getText(" ").encode('utf-8')
                thumb = item3.a.img['src']
                addDir(title,__baseurl__+url,3,thumb,1)  


def VIDEOLINK(url,name):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    
    httpdata   = httpdata.replace("\r","").replace("\n","").replace("\t","")
    
    thumb = re.compile('<meta property="og:image" content="(.+?)" />').findall(httpdata)
    popis = re.compile('<meta property="og:description" content="(.+?)" />').findall(httpdata)
    try:
        desc = popis[0]
    except:
        desc = name

    #Ziskani adresy configu ze stranky poradu, zacina u parametru configUrl - jen jsem slepil vsechny parametry k sobe a nacetl
    configUrl = re.compile('configUrl: \'(.+?)\'').findall(httpdata)
    print 'configUrl = ' + str(configUrl[0])

    parametry = re.compile('configParams: {(.+?)}').findall(httpdata)
    linkgenerator = parametry[0].replace(" ","").replace("?',","?").replace(":'","=").replace("',","&").replace("'","").replace(",","")
    print 'configParams = ' + str(linkgenerator)
    linkgenerator = str(configUrl[0]) + str(linkgenerator)

    print 'finalUrl = ' + str(linkgenerator)
    req = urllib2.Request(linkgenerator)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()

    #Dolovani rtmp adresy z configu
    rtmp_url = re.compile('src":"(.+?)"').findall(httpdata)
    rtmp_url = rtmp_url[0].replace("\\","")
    #Slozeni vysledneho linku, sklada se z adresy rtmp_url a pak jeste jednou z adresy rtmp_url, ale ta uz musi byt rozdelena a slouzi jako parametry playpath a tcUrl
    #rtmp://nova-voyo-cz-pc.service.cdn.cra.cz/vod/&mp4:oldcdn/2015/11/06/1561560/2015-11-19_ulice-218_cyklus_dil_2919-b041884-np-mp4-lq.mp4?SIGV=2&IS=0&ET=1448109213&CIP=31.30.37.226&KO=1&KN=1&US=2338c0708283dbc363f88ecdbf53233c27d52ef3 tcUrl=rtmp://nova-voyo-cz-pc.service.cdn.cra.cz/vod playpath=mp4:oldcdn/2015/11/06/1561560/2015-11-19_ulice-218_cyklus_dil_2919-b041884-np-mp4-lq.mp4?SIGV=2&IS=0&ET=1448109213&CIP=31.30.37.226&KO=1&KN=1&US=2338c0708283dbc363f88ecdbf53233c27d52ef3
    addLink(name,rtmp_url,'http:' + thumb[0],desc)


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
