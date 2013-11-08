# -*- coding: utf-8 -*-
import urllib2, urllib, re, os, random, decimal
from parseutils import *
from util import addDir, addLink
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK


__baseurl__ = 'http://play.iprima.cz'
__cdn_url__ = 'http://cdn-dispatcher.stream.cz/?id='
__dmdbase__ = 'http://iamm.netuje.cz/xbmc/prima/'
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.prima')
home = __settings__.get_info('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png') 
family = os.path.join(home, 'family.png') 
love = os.path.join(home, 'love.png') 
cool = os.path.join(home, 'cool.png')
zoom = os.path.join(home, 'zoom.png') 
fanart = os.path.join(home, 'fanart.jpg') 
vyvoleni = os.path.join( home, 'vyvoleni.png' )
kvalita = __settings__.get_setting('kvalita')

if kvalita == '':
    __settings__.open_settings(session) 

def replace_words(text, word_dic):
    rc = re.compile('|'.join(map(re.escape, word_dic)))
    def translate(match):
        return word_dic[match.group(0)]
    return rc.sub(translate, text)

word_dic = {
'\u00e1': 'á',
'\u00e9': 'é',
'\u00ed': 'í',
'\u00fd': 'ý',
'\u00f3': 'ó',
'\u00fa': 'ú',
'\u016f': 'ů',
'\u011b': 'ě',
'\u0161': 'š',
'\u0165': 'ť',
'\u010d': 'č',
'\u0159': 'ř',
'\u017e': 'ž',
'\u010f': 'ď',
'\u0148': 'ň',
'\u00C0': 'Á',
'\u00c9': 'É',
'\u00cd': 'Í',
'\u00d3': 'Ó',
'\u00da': 'Ú',
'\u016e': 'Ů',
'\u0115': 'Ě',
'\u0160': 'Š',
'\u010c': 'Č',
'\u0158': 'Ř',
'\u0164': 'Ť',
'\u017d': 'Ž',
'\u010e': 'Ď',
'\u0147': 'Ň',
'\\xc3\\xa1': 'á',
'\\xc4\\x97': 'é',
'\\xc3\\xad': 'í',
'\\xc3\\xbd': 'ý',
'\\xc5\\xaf': 'ů',
'\\xc4\\x9b': 'ě',
'\\xc5\\xa1': 'š',
'\\xc5\\xa4': 'ť',
'\\xc4\\x8d': 'č',
'\\xc5\\x99': 'ř',
'\\xc5\\xbe': 'ž',
'\\xc4\\x8f': 'ď',
'\\xc5\\x88': 'ň',
'\\xc5\\xae': 'Ů',
'\\xc4\\x94': 'Ě',
'\\xc5\\xa0': 'Š',
'\\xc4\\x8c': 'Č',
'\\xc5\\x98': 'Ř',
'\\xc5\\xa4': 'Ť',
'\\xc5\\xbd': 'Ž',
'\\xc4\\x8e': 'Ď',
'\\xc5\\x87': 'Ň',
}

def OBSAH():
    addDir('Prima Family','http://play.iprima.cz/primaplay/az_ajax?letter=vse&genres=vse&channel=family',4,family,0,'family')
    addDir('Prima Cool','http://play.iprima.cz/primaplay/az_ajax?letter=vse&genres=vse&channel=cool',4,cool,0,'cool')
    addDir('Prima Love','http://play.iprima.cz/primaplay/az_ajax?letter=vse&genres=vse&channel=love',4,love,0,'love')
    addDir('Prima zoom','http://play.iprima.cz/primaplay/az_ajax?letter=vse&genres=vse&channel=zoom',4,zoom,0,'zoom')
    url = 'http://play.iprima.cz/az'
    request = urllib2.Request(url)
    con = urllib2.urlopen(request)
    data = con.read()
    con.close()
    match = re.compile('callbackItem" data-id="(.+?)" data-alias="(.+?)"><a href="(.+?)">(.+?)</a></div>').findall(data)
    for porad_id,data_alias,url,jmeno in match:
        if re.search('vse', data_alias, re.U):
                continue
        url = 'http://play.iprima.cz/primaplay/az_ajax?letter=vse&genres='+data_alias+'&channel=vse'
        #print porad_id,data_alias,url,jmeno
        addDir(replace_words(jmeno, word_dic),url,4,__dmdbase__+data_alias+'.jpg',0,jmeno)

   
def KATEGORIE(url,page,kanal):
    if re.search('page', url, re.U):
            match = re.compile('page=([0-9]+)').findall(url)
            strquery = '?page='+match[0]
            request = urllib2.Request(url, strquery)
    else:
        request = urllib2.Request(url)
    con = urllib2.urlopen(request)
    data = con.read()
    con.close()
    match = re.compile('<div class=".+?" data-video-id=".+?" data-thumbs-count=".+?"><div class="field-image-primary"><a href="(.+?)"><span class="container-image-195x110"><img src="(.+?)" alt="(.+?)"').findall(data)
    for url,thumb,name in match:
        #print url,thumb,name
        addDir(replace_words(name, word_dic),__baseurl__+url,10,__baseurl__+thumb,0,name)          
    try:
        match = re.compile('<li class="pager-next last"><a href="(.+?)"').findall(data)
        #print match[0]
        addDir('>> Další strana',__baseurl__+match[0],5,nexticon,'','')
    except:
        print 'strankovani nenalezeno'

   
def INDEX(url,page,kanal):
    doc = read_page(url)
    items = doc.find('div', 'items')
    for item in items.findAll('div', 'item'):
            item2 = item.find('div','field-image-primary')
            thumb = item2.img['src']
            item2 = item.find('div','field-title')
            name_a = item2.find('a')
            name = name_a.getText(" ").encode('utf-8')
            thumb = item.img['src']
            #name_a = item.find('a')
            #name = name_a.getText(" ").encode('utf-8')
            url = str(item2.a['href'])
            item2 = item.find('div','field-video-count')
            pocet = item2.getText(" ").encode('utf-8')
            #print name+pocet, thumb, url
            addDir(replace_words(name+' '+pocet, word_dic),__baseurl__+url,5,'http://play.iprima.cz'+thumb,0,name)          
    try:
        dalsi = doc.find('li', 'pager-next last')
        next_url = str(dalsi.a['href'])
        #print next_url
        addDir('>> Další strana',__baseurl__+next_url,4,nexticon,'','')
    except:
        print 'strankovani nenalezeno'

def VYVOLENI(url,page,kanal):
    if kanal !=1:
        addDir('Exkluzivně','http://www.iprima.cz/vyvoleni/videa-z-vily/exkluzivne',2,vyvoleni,'','1')
        addDir('Videa z TV','http://www.iprima.cz/vyvoleni/videa-z-vily/videa-z-tv',2,vyvoleni,'','1')        
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    items = re.compile('<div class="views-field-prima-field-image-primary-nid">(.+?)<span class="cover"></span></span></a></div>',re.S).findall(str(httpdata))
    match = re.compile('<a href="(.+?)"><span class="container-image-195x110"><img src="(.+?)" alt="(.+?)"',re.S).findall(str(items))    

    for url,thumb,name in match:  
            name = replace_words(name, word_dic)
            thumb = re.sub('98x55','280x158',thumb)
            req = urllib2.Request('http://www.iprima.cz'+url)
            req.add_header('User-Agent', _UserAgent_)
            response = urllib2.urlopen(req)
            httpdata = response.read()
            response.close()
            url = re.compile('"nid":"(.+?)","tid":"(.+?)"').findall(httpdata)    
            for nid,tid in url:
                url = 'http://play.iprima.cz/all/'+nid+'/all'
            addDir(name,url,10,'http://www.iprima.cz/'+thumb,'','')
        
def VIDEOLINK(url,name):
    request = urllib2.Request(url)
    con = urllib2.urlopen(request)
    data = con.read()
    con.close()
    print url
    stream_video = re.compile('cdnID=([0-9]+)').findall(data)
    if len(stream_video) > 0:
        print 'LQ '+__cdn_url__+name,stream_video[0],icon,''
        addLink('LQ '+name,__cdn_url__+stream_video[0],icon,'')        
    else:
        try:
            hd_stream = re.compile("'hd_id':'(.+?)'").findall(data)
            hd_stream = hd_stream[0]
        except:
            hd_stream = 'Null'        
        hq_stream = re.compile('"hq_id":"(.+?)"').findall(data)
        lq_stream = re.compile('"lq_id":"(.+?)"').findall(data)
        geo_zone = re.compile('"zoneGEO":(.+?),').findall(data)    
        try:
            thumb = re.compile("'thumbnail': '(.+?)'").findall(data)
            nahled = thumb[0]
        except:
            nahled = icon
        key = 'http://embed.livebox.cz/iprimaplay/player-embed-v2.js?__tok'+str(gen_random_decimal(1073741824))+'__='+str(gen_random_decimal(1073741824))
        req = urllib2.Request(key)
        req.add_header('User-Agent', _UserAgent_)
        req.add_header('Referer', url)
        response = urllib2.urlopen(req)
        keydata = response.read()
        response.close()
        keydata = re.compile("_any_(.*?)'").findall(keydata)
        #keydata = re.compile("auth='(.*?)'").findall(keydata)        
        print keydata
        if geo_zone[0] == "1":
            #hd_url = 'rtmp://bcastgw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+'/mp4:hq/'+hd_stream[0]
            hd_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token_'+geo_zone[0]+'?auth=_any_'+keydata[1]+' playpath=mp4:hq/'+hd_stream+ ' live=true'
            hq_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token_'+geo_zone[0]+'?auth=_any_'+keydata[1]+'/mp4:'+hq_stream[0]
            lq_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token_'+geo_zone[0]+'?auth=_any_'+keydata[1]+'/mp4:'+lq_stream[0]
            
            if __settings__.get_setting('proxy_use'):
                proxy_ip = __settings__.get_setting('proxy_ip')
                proxy_port = str(__settings__.get_setting('proxy_port'))
                hd_url = hd_url + ' socks=' + proxy_ip+':'+proxy_port
                hq_url = hq_url + ' socks=' + proxy_ip+':'+proxy_port
                lq_url = lq_url + ' socks=' + proxy_ip+':'+proxy_port
        else:
            if re.match('Prima', hq_stream[0], re.U):
                #hd_url = 'rtmp://bcastgw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+'/mp4:hq/'+hd_stream[0]
                hd_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+' playpath=mp4:hq/'+hd_stream+ ' live=true'
                hq_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+'/mp4:'+hq_stream[0]
                lq_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+'/mp4:'+lq_stream[0]
            else:
                hd_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+'/'+hd_stream
                hq_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+'/'+hq_stream[0]
                lq_url = 'rtmp://bcastmw.livebox.cz:80/iprima_token?auth=_any_'+keydata[1]+'/'+lq_stream[0]
                             

        #print nahled, hq_url, lq_url
        if kvalita == "HD":
            print 'HD '+name,hq_url,nahled,name
            if hd_stream != 'Null':
                addLink('HD '+name,hd_url,nahled,name)
            addLink('HQ '+name,hq_url,nahled,name)            
        elif kvalita == "HQ":
            print 'HQ '+name,lq_url,nahled,name
            addLink('HQ '+name,hq_url,nahled,name)
            addLink('LQ '+name,lq_url,nahled,name)
        else:            
            print 'LQ '+name,lq_url,nahled,name
            addLink('LQ '+name,lq_url,nahled,name)


def gen_random_decimal(d):
        return decimal.Decimal('%d' % (random.randint(0, d)))
    
url=None
name=None
thumb=None
mode=None
page=None
kanal=None
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
        kanal=int(params["kanal"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Page: "+str(page)
print "Kanal: "+str(kanal)

if mode==None or url==None or len(url)<1:
        OBSAH()
       
elif mode==1:
        print ""+str(url)
        print ""+str(kanal)
        print ""+str(page)
        KATEGORIE(url,page,kanal)

elif mode==2:
        print ""+str(url)
        print ""+str(kanal)
        print ""+str(page)
        VYVOLENI(url,page,kanal)
       
elif mode==4:
        print ""+str(url)
        print ""+str(kanal)
        print ""+str(page)
        INDEX(url,page,kanal)

elif mode==5:
        print ""+str(url)
        print ""+str(kanal)
        print ""+str(page)
        KATEGORIE(url,page,kanal)
       
elif mode==10:
        print ""+url
        VIDEOLINK(url,name)