# -*- coding: utf-8 -*-
import urllib2,urllib,re,os
from parseutils import *
from util import addDir, addLink
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__baseurl__='http://www.b-tv.cz/videoarchiv'
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.btv')
home = __settings__.get_info('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png') 

def OBSAH():
    #self.core.setSorting('NONE')
    req = urllib2.Request(__baseurl__)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<li><a  href="(.+?)" title="(.+?)">.+?</a></li>').findall(httpdata)
    for url,name in match:
        addDir(name,__baseurl__+url,1,icon)    

            
def INDEX(url):
    doc = read_page(url)
    items = doc.find('table', 'norm')
    items = doc.find('tbody')
    for item in items.findAll('tr'):
        name = re.compile('<a href=".+?">(.+?)</a><br />').findall(str(item))
        link = 'http://www.b-tv.cz'+str(item.a['href']) 
        thumb = str(item.img['src'])  
        try:
            popis = item.find('p')
            popis = popis.getText(" ").encode('utf-8')
        except:
            popis = name[0]
        doc = read_page(link)
        video_url = re.compile('file=(.+?)&').findall(str(doc))
        addLink(name[0],'http://www.b-tv.cz'+video_url[0],'http://www.b-tv.cz'+thumb,popis)
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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
        print ""
        OBSAH()
       
elif mode==1:
        print ""
        INDEX(url)
