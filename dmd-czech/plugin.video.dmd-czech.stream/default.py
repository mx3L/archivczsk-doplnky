# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,random,decimal
from parseutils import *
from urlparse import urlparse
from util import addDir, addLink,addSearch, getSearch,showWarning
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
import simplejson as json
__baseurl__ = 'http://www.stream.cz/ajax/'
__dmdbase__ = 'http://iamm.netuje.cz/xbmc/stream/'
__cdn_url__ = 'http://cdn-dispatcher.stream.cz/?id='
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.stream')
home = __settings__.get_info('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png')

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
    addDir('Nejnovější videa','http://www.stream.cz//ajax/get_timeline?context=latest&0.'+str(gen_random_decimal(9999999999999999)),3,icon)
    addDir('Všechny pořady','listShows',1,icon)
    addDir('Komerční pořady','listCommercials',1,icon)
    addDir('Pohádky','dreams',1,icon)

def INDEX(url):
    link = __baseurl__+'get_catalogue?0.'+str(gen_random_decimal(9999999999999999))
    temp = 'porady'
    if url == 'dreams':
        link = __baseurl__+'get_catalogue?dreams&0.'+str(gen_random_decimal(9999999999999999))
        temp = 'pohadky'
        url = 'listShows'
    req = urllib2.Request(link)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<ul id="'+url+'" class="shows clearfix">(.+?)</ul>', re.S).findall(httpdata)

    if temp == 'porady':
        match2 = re.compile('<a href="/porady/(.+?)" class=".+?" data-show-id="(.+?)" data-action=".+?">(.+?)<img src="(.+?)"', re.S).findall(match[0])

    else:
        match2 = re.compile('<a href="/pohadky/(.+?)" class=".+?" data-show-id="(.+?)" data-action=".+?">(.+?)<img src="(.+?)"', re.S).findall(match[0])

    for link, id, name, thumb in match2:
            name = str.strip(name)
            link = __baseurl__+'get_series?show_url='+link+'&0.'+str(gen_random_decimal(9999999999999999))
            addDir(name,link,2,thumb)

def LIST(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<a href=".+?" data-action=".+?" data-params=\'\{".+?"\}\' data-episode-id="(.+?)">(.+?)</a>', re.S).findall(httpdata)
    for id, name in match:
            link = __baseurl__+'get_video_source?context=catalogue&id='+id+'&0.'+str(gen_random_decimal(9999999999999999))
            addDir(name,link,10,icon)

def LATESTLIST(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<li data-episode-id="(.+?)" data-timestamp="(.+?)"> <a href=".+?<img src="//(.+?)/80/80" alt=""/> </span> <span class="texts"> <span class="h2">(.+?)</span> <span class="description">(.+?)</span>', re.S).findall(httpdata)
    for id, timestamp, img, episodename, serialname in match:
            link = __baseurl__+'get_video_source?context=catalogue&id='+id+'&0.'+str(gen_random_decimal(9999999999999999))
            image = 'http://'+img+'/320'
            print image
            name = serialname+' | '+episodename
            addDir(name,link,10,image)

def VIDEOLINK(url,name):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    httpdata = replace_words(httpdata, word_dic)
    data = json.loads(httpdata)
    name = data[u'episode_name']
    thumb = data[u'episode_image_original_url']
    for item in data[u'instances']:
        try:
            stream_url = item[u'instances'][0][u'source']
            quality = item[u'instances'][0][u'quality']
            addLink(quality+' '+name,stream_url,'',name)
        except:
            continue

def gen_random_decimal(d):
        return decimal.Decimal('%d' % (random.randint(0,d)))


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

elif mode==2:
        print ""+url
        LIST(url)

elif mode==3:
        print ""+url
        LATESTLIST(url)

elif mode==10:
        print ""+url
        VIDEOLINK(url,name)
