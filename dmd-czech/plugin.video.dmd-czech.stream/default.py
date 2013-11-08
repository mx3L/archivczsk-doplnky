# -*- coding: utf-8 -*-
import urllib2, urllib, re, os
from parseutils import *
from urlparse import urlparse
from util import addDir, addLink,addSearch, getSearch,showWarning
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__baseurl__ = 'http://old.stream.cz'
__dmdbase__ = 'http://iamm.netuje.cz/xbmc/stream/'
__cdn_url__ = 'http://cdn-dispatcher.stream.cz/?id='
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.stream')
home = __settings__.get_info('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png') 
page_pole_url = []
page_pole_no = []
searchurl = 'http://old.stream.cz/?a=search&search_text='
user_name = __settings__.get_setting('user_name')

def OBSAH():
    addSearch('Hledat...', __baseurl__, 13, icon)
    addDir('Všechny Pořady','http://old.stream.cz/televize/nazev',1,icon)
    addDir('Pořady Stream.cz','http://old.stream.cz/televize/429-stream',3,icon)
    addDir('Partnerské pořady','http://old.stream.cz/',4,icon)
    addDir('Komerční videa','http://old.stream.cz/?m=stream&a=commercial_channel',5,icon)  
    addDir('Uživatelská videa','http://old.stream.cz/kategorie/2-uzivatelska-videa',2,icon)
    addDir('Moje videa',__baseurl__,15,icon)
    
def INDEX_TV(url):
    doc = read_page(url)
    items = doc.find('div', 'vertical540Box')
    for item in items.findAll('div', 'matrixThreeVideoList'):
            name_a = item.find('div', 'matrixThreeData')
            name_a = name_a.find('h5')            
            name_a = name_a.find('a') 
            name = name_a.getText(" ").encode('utf-8')
            url = __baseurl__ + str(item.a['href'])
            thumb = item.find('a', 'videoListImg')
            thumb = thumb['style']
            thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
            thumb = thumb[:(thumb.find(')') - 1)]
            #print name, thumb, url
            addDir(name, url, 6, thumb)
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page)
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no) - 1
        url_page = int(max_page_count) - 1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = item['href']
            #next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu ' + str(next_page) + ' z ' + max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label, __baseurl__ + next_url, 1, nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'

def INDEX_UZIVATEL(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<li><a  href="(.+?)">(.+?)</a>').findall(httpdata)
    for link, name in match:
        if not re.match('http://old.stream.cz', link, re.U):
                link = 'http://old.stream.cz' + link
        #print name,link
        addDir(name, link, 6, icon)

def INDEX_STREAM(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<h4 class="redTitelBox">Pořady Stream.cz</h4>(.+?)<h4 class="redTitelBox">Partnerské pořady</h4>', re.S).findall(httpdata)
    item = re.compile('<a href="(.+?)">(.+?)</a>').findall(match[0])
    for link,name in item:
        if not re.match('http://old.stream.cz', link, re.U):
                link = 'http://old.stream.cz'+link
        #print name,link
        addDir(name,link,7,icon)

def INDEX_PARTNERSKE(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<h4 class="redTitelBox">Partnerské pořady</h4>(.+?)<h4 class="redTitelBox">Uživatelská videa</h4>', re.S).findall(httpdata)
    item = re.compile('<a href="(.+?)">(.+?)</a>').findall(match[0])
    for link,name in item:
        if not re.match('http://old.stream.cz', link, re.U):
                link = 'http://old.stream.cz'+link
        #print name,link
        addDir(name,link,7,icon)

def INDEX_KOMERCNI(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<div class="themesList">(.+?)<div class="vertical300Box">', re.S).findall(httpdata)
    item = re.compile('<a href="(.+?)">(.+?)</a>').findall(match[0])
    for link,name in item:
        if not re.match('http://old.stream.cz', link, re.U):
                link = 'http://old.stream.cz'+link
        #print name,link
        addDir(name,link,7,icon)


def MY_VIDEO(url):
    if url == __baseurl__:
        if user_name == '':
            showWarning(u"Doplněk DMD JOJ. Zadejte uživ.jméno nebo email!")
            #__settings__.open_settings(session)
        if re.search('@', user_name, re.U):
            match = re.compile('(.+?)@(.+)').findall(user_name)
            for name, email in match:
                url = __baseurl__ + '/profil/' + email + '/' + name
        else:
            url = __baseurl__ + '/profil/' + user_name
        print url            
        doc = read_page(url)
        items = doc.find('div', 'boxVideo txtRight')
        url = __baseurl__ + str(items.a['href'])
        print url
    doc = read_page(url)
    items = doc.find('div', 'vertical670Box')
    for item in items.findAll('div', 'videoList'):
            name_a = item.find('h5')
            name_a = name_a.find('a') 
            name = name_a.getText(" ").encode('utf-8')
            link = __baseurl__ + str(item.a['href'])
            thumb = item.find('a', 'videoListImg')
            thumb = thumb['style']
            thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
            thumb = thumb[:(thumb.find(')') - 1)]
            #print name, thumb, url
            addDir(name, link, 20, thumb)
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page) - 1
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no) - 1
        url_page = int(max_page_count) - 1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = item['href']
            #next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu ' + str(next_page) + ' z ' + max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label, __baseurl__ + next_url, 15, nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'

def LIST_TV(url):
    doc = read_page(url)
    items = doc.find('div', id='videa_kanalu_list')
    for item in items.findAll('div', 'kanal_1video'):
            thumb = item.find('a', 'kanal_1video_pic')
            thumb = thumb['style']
            thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
            thumb = thumb[:(thumb.find(')') - 1)]
        
            item = item.find('div', 'kanal_1video_content')
            name_a = item.find('a') 
            name = name_a.getText(" ").encode('utf-8')
            url = __baseurl__ + str(item.a['href'])
            #print name, thumb, url
            addDir(name, url, 20, thumb)
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page)
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no) - 1
        url_page = int(max_page_count) - 1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = item['href']
            #next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu ' + str(next_page) + ' z ' + max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label, __baseurl__ + next_url, 7, nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'

def LIST_UZIVATEL(url):
    doc = read_page(url)
    items = doc.find('div', 'vertical670Box')
    for item in items.findAll('div', 'matrixThreeVideoList'):
            name_a = item.find('h5')
            name_a = name_a.find('a') 
            name = name_a.getText(" ").encode('utf-8')
            link = __baseurl__ + str(item.a['href'])
            thumb = item.find('a', 'videoListImg')
            thumb = thumb['style']
            thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
            thumb = thumb[:(thumb.find(')') - 1)]
            #print name, thumb, url
            addDir(name, link, 20, thumb)
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page) - 1
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no) - 1
        url_page = int(max_page_count) - 1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = item['href']
            #next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu ' + str(next_page) + ' z ' + max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label, __baseurl__ + next_url, 6, nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'


def SEARCH():
    
            
        	search = getSearch(session)
	        encode = urllib.quote(search)
		link = searchurl + encode
                doc = read_page(link)
                #items = doc.find('div', 'orderTabInner orderTabInnerG')
                #for item in items.findAll('a'):
                #    name = '>> '+item.getText(" ").encode('utf-8')+' <<'
                #    url = __baseurl__+str(item['href'])
                #    if re.match('>> Vše <<', name, re.U):
                #        continue
                #   #print name, url
                #    addDir(name,url,6,icon)		
                items = doc.find('div', 'vertical540Box')
                for item in items.findAll('div', 'videoList'):
                    name_a = item.find('h5')
                    name_a = name_a.find('a') 
                    name = name_a.getText(" ").encode('utf-8')
                    url = __baseurl__ + str(item.a['href'])
                    thumb = item.find('a', 'videoListImg')
                    thumb = thumb['style']
                    thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
                    thumb = thumb[:(thumb.find(')') - 1)]
                    #print name, thumb, url
                    addDir(name, url, 20, thumb)
                try:
                    pager = doc.find('div', 'paging')
                    act_page_a = pager.find('strong',)
                    act_page = act_page_a.getText(" ").encode('utf-8')
                    next_page = int(act_page) + 1        
                    next_url_no = int(act_page)
                    for item in pager.findAll('a'):
                        page_url = item['href'].encode('utf-8')
                        page_no = item.getText(" ").encode('utf-8')
                        page_pole_url.append(page_url)
                        page_pole_no.append(page_no)
                        max_page_count = len(page_pole_no) - 1
                        url_page = int(max_page_count) - 1
                        if  re.match('další', page_pole_no[max_page_count], re.U):
                            next_url = item['href']
                            #next_url = page_pole_url[next_url_no]
                            max_page = page_pole_no[url_page]
                            next_label = '>> Přejít na stranu ' + str(next_page) + ' z ' + max_page
                            #print next_label,__baseurl__+next_url
                            addDir(next_label, __baseurl__ + next_url, 14, nexticon)
                except:
                    print 'STRANKOVANI NENALEZENO!'

def SEARCH2(url):
                doc = read_page(url)
                #items = doc.find('div', 'orderTabInner orderTabInnerG')
                #for item in items.findAll('a'):
                #    name = '>> '+item.getText(" ").encode('utf-8')+' <<'
                #    url = __baseurl__+str(item['href'])
                #    if re.match('>> Vše <<', name, re.U):
                #        continue
                #   #print name, url
                #    addDir(name,url,6,icon)		
                items = doc.find('div', 'vertical540Box')
                for item in items.findAll('div', 'videoList'):
                    name_a = item.find('h5')
                    name_a = name_a.find('a') 
                    name = name_a.getText(" ").encode('utf-8')
                    url = __baseurl__ + str(item.a['href'])
                    thumb = item.find('a', 'videoListImg')
                    thumb = thumb['style']
                    thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
                    thumb = thumb[:(thumb.find(')') - 1)]
                    #print name, thumb, url
                    addDir(name, url, 20, thumb)
                try:
                    pager = doc.find('div', 'paging')
                    act_page_a = pager.find('strong',)
                    act_page = act_page_a.getText(" ").encode('utf-8')
                    next_page = int(act_page) + 1        
                    next_url_no = int(act_page)
                    for item in pager.findAll('a'):
                        page_url = item['href'].encode('utf-8')
                        page_no = item.getText(" ").encode('utf-8')
                        page_pole_url.append(page_url)
                        page_pole_no.append(page_no)
                        max_page_count = len(page_pole_no) - 1
                        url_page = int(max_page_count) - 1
                        if  re.match('další', page_pole_no[max_page_count], re.U):
                            next_url = item['href']
                            #next_url = page_pole_url[next_url_no]
                            max_page = page_pole_no[url_page]
                            next_label = '>> Přejít na stranu ' + str(next_page) + ' z ' + max_page
                            #print next_label,__baseurl__+next_url
                            addDir(next_label, __baseurl__ + next_url, 14, nexticon)
                except:
                    print 'STRANKOVANI NENALEZENO!'
    
                
def VIDEOLINK(url, name):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    try:
        hd_video = re.compile('cdnHD=([0-9]+)').findall(httpdata)
    except:
        print 'HD stream nenalezen'
    try:
        hq_video = re.compile('cdnHQ=([0-9]+)').findall(httpdata)
    except:
        print 'HQ stream nenalezen'
    try:
        lq_video = re.compile('cdnLQ=([0-9]+)').findall(httpdata)
    except:
        print 'LQ stream nenalezen'
    thumb = re.compile('<link rel="image_src" href="(.+?)" />').findall(httpdata)
    popis = re.compile('<meta name="title" content="(.+?)" />').findall(httpdata)
    if not len(popis) > 0:
        popis = re.compile('<title>(.+?)</title>').findall(httpdata)   

    #print name,urlhq,thumb
    if len(hd_video) > 0:
        hdurl = __cdn_url__ + hd_video[0]
        #print 'HD '+'name',hdurl,popis[0]
        addLink('HD ' + name, hdurl, '', popis[0])
    if len(hq_video) > 0:
        hqurl = __cdn_url__ + hq_video[0]
        #print 'HQ '+'name',hqurl,'',popis[0]
        addLink('HQ ' + name, hqurl, '', popis[0])
    if len(lq_video) > 0:
        lqurl = __cdn_url__ + lq_video[0]
        #print'LQ '+'name',lqurl,'',popis[0]
        addLink('LQ ' + name, lqurl, '', popis[0])

def PAGER(doc):
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page) - 1
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no) - 1
        url_page = int(max_page_count) - 1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu ' + str(next_page) + ' z ' + max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label, __baseurl__ + next_url, 5, nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'

url = None
name = None
thumb = None
mode = None

try:
        url = urllib.unquote_plus(params["url"])
except:
        pass
try:
        name = urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode = int(params["mode"])
except:
        pass

print "Mode: " + str(mode)
print "URL: " + str(url)
print "Name: " + str(name)

if mode == None or url == None or len(url) < 1:
        print ""
        OBSAH()
       
elif mode == 1:
        print ""
        INDEX_TV(url)

elif mode == 2:
        print "" + url
        INDEX_UZIVATEL(url)

elif mode == 3:
        print "" + url
        INDEX_STREAM(url)

elif mode == 4:
        print "" + url
        INDEX_PARTNERSKE(url)

elif mode == 5:
        print "" + url
        INDEX_KOMERCNI(url)


elif mode == 6:
        print "" + url
        LIST_UZIVATEL(url)

elif mode == 7:
        print "" + url
        LIST_TV(url)


elif mode == 13:
        print "" + url
        SEARCH()
elif mode == 14:
        print "" + url
        SEARCH2(url)  

elif mode == 15:
        print "" + url
        MY_VIDEO(url)       

elif mode == 20:
        print "" + url
        VIDEOLINK(url, name)
