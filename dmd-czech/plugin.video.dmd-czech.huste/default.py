# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,time
from parseutils import *
from urlparse import urlparse
from datetime import datetime
from util import addDir, addLink
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.huste')
home = __settings__.get_info('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png') 

def OBSAH():
    #addDir('Hudba','http://hudba.huste.tv',0,1,icon)
    addDir2('Šport','http://sport.huste.tv',0,4,icon)
    addDir2('Relácie a seriály','http://zabava.huste.tv',0,4,icon)    
    addDir2('Filmy','http://filmy.huste.tv',0,4,icon)
    addDir2('Hlášky','http://hlasky.huste.tv',0,4,icon)
    addDir2('Sport Live & Archiv(BETA)','http://www.huste.tv/services/CurrentLive.xml?nc=6946',0,11,icon)     

    
def PROUZEK(url):
    doc = read_page(url)
    items = doc.find('select', 'j-selectmenu')
    for item in items.findAll('option'):
        name = item.getText(" ").encode('utf-8')
        url2 = url+str(item['value'])
        addDir2(name,url2,0,7,icon)

        
def NAZEV(url):
    doc = read_page(url)
    items = doc.find('div', 'b-wrap b-list-simple')
    for item in items.findAll('li'):
        name = item.a['title'].encode('utf-8')
        url = str(item.a['href']) 
        addDir2(name,url,7,icon)

    
def INDEX(url,page):
    
    doc = read_page(url+'?page='+str(page))
    items = doc.find('div', 'b-body')
    for item in items.findAll('li','i collapse'):
            title = item.a['title'].encode('utf-8')
            interpret = item.find('p')
            interpret = interpret.getText(" ").encode('utf-8')
            url2 = str(item.a['href']) 
            thumb = str(item.img['src'])   
            name = title+' - '+interpret
            if re.search('http', url2, re.U):
                addDir2(name,url2,0,10,thumb)
            else:
                cast_url = urlparse(url)
                url2 = 'http://'+cast_url[1] + url2
                addDir2(name,url2,0,10,thumb)
    page = page + 1
    addDir2('>> Další strana',url,page,7,nexticon)



def LIVE(url):
    doc = read_page(url)
    zapasy = doc.find('events')
    for zapas in zapasy.findAll('event'):
        title = str(zapas['title'].encode('utf-8'))
        nahled = str(zapas['large_image'])
        cas = str(zapas['starttime'])
        cas = cas.replace("+01:00", "");
        if hasattr(datetime, 'strptime'):
            #python 2.6
            strptime = datetime.strptime
        else:
            #python 2.4 equivalent
            strptime = lambda date_string, format: datetime(*(time.strptime(date_string, format)[0:6]))
        cas = strptime(cas, '%Y-%m-%dT%H:%M:%S')
        cas = cas.strftime('%d.%m. %H:%M')
        archiv = str(zapas['archive'])
        link = str(zapas['url'])
        #print title,nahled,cas,archiv,link
        try:
            soubory = zapas.find('files')
            for soubor in soubory.findAll('file'):
                rtmp_url = str(soubor['url'])
                kvalita = str(soubor['quality'])
                rtmp_cesta = str(soubor['path'])
                #print rtmp_url,kvalita,rtmp_cesta
            server = re.compile('rtmp://(.+?)/').findall(rtmp_url)
            tcurl = 'rtmp://'+server[0]
            swfurl = 'http://c.static.huste.tv/fileadmin/templates/swf/HusteMainPlayer.swf'
            if archiv == "1":
                rtmp_url = tcurl+' playpath='+rtmp_cesta+' pageUrl=http://live.huste.tv/ swfurl='+swfurl+' swfVfy=true'  
                name = 'Záznam - ' + cas + ' ' + title
            else:
                rtmp_url = tcurl+' playpath='+rtmp_cesta+' pageUrl=http://live.huste.tv/ swfurl='+swfurl+' swfVfy=true  live=true'
                name = 'Live - ' + cas + ' ' + title
            print name,rtmp_url,nahled
            addLink(name,rtmp_url,nahled,name)
        except:
            name = 'Nedostupné - ' + cas + ' ' + title
            addLink(name,'',nahled,name)
            continue
                
def VIDEOLINK(url,name):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    cast_url = urlparse(url)
    videoid = re.compile('videoId=(.+?)&').findall(httpdata)
    playlisturl = 'http://'+cast_url[1]+'/services/Video.php?clip='+videoid[0]
    print playlisturl
    doc = read_page(playlisturl)
    title = str(doc.event['title'].encode('utf-8'))    
    thumb = str(doc.event['image'])    
    items = doc.find('files')
    for item in items.findAll('file'):
        link = str(item['url'])    
        cesta = str(item['path'])
        kvalita = str(item['label'])             
        server = re.compile('rtmp://(.+?)/').findall(link)
        name = kvalita+ ' - ' + title
        tcurl = 'rtmp://'+server[0]
        swfurl = 'http://b.static.huste.tv/fileadmin/templates/swf/HusteMainPlayer.swf'
        rtmp_url = tcurl+' playpath='+cesta+' pageUrl='+url+' swfUrl='+swfurl+' swfVfy=true'  
        print name,rtmp_url,thumb[0]
        addLink(name,rtmp_url,thumb[0],name)
        
def addDir2(name,url,page,mode,iconimage):
    addDir(name,url,mode,iconimage,page)

url=None
page=None
name=None
thumb=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        page=int(params["page"])
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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Page: "+str(page)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
        print ""
        OBSAH()

elif mode==4:
        print ""+url
        PROUZEK(url)

elif mode==5:
        print ""+url
        ABC(url)

elif mode==6:
        print ""+url
        NAZEV(url)

elif mode==7:
        print ""+url
        print ""+str(page)
        INDEX(url,page)


elif mode==11:
        print ""+url
        LIVE(url)
        
elif mode==10:
        print ""+url
        VIDEOLINK(url,name)
