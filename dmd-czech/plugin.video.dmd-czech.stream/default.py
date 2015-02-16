# -*- coding: utf-8 -*-
import urllib2,urllib,re,os
from util import addDir, addLink,addSearch, getSearch,showWarning
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
import json
from hashlib import md5
from time import time

__baseurl__ = 'http://www.stream.cz/API'
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.stream')
home = __settings__.get_info('path')
icon = os.path.join( home, 'icon.png' ) 
nexticon = os.path.join( home, 'nextpage.png' )

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

class loglevel:
    LOGDEBUG, LOGERROR = range(2)

def log(msg, level=loglevel.LOGDEBUG):
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    if level == loglevel.LOGDEBUG:
        levelstr = 'debug'
    elif level == loglevel.LOGERROR:
        levelstr = 'error'
    print ("[%s][%s] %s"%("stream.cz", levelstr, msg.__str__()))

def logDbg(msg):
    log(msg,level=loglevel.LOGDEBUG)

def logErr(msg):
    log(msg,level=loglevel.LOGERROR)

def makeImageUrl(rawurl):
    return 'http:'+rawurl.replace('{width}/{height}','360/360')

def getJsonDataFromUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    req.add_header('Api-Password', md5('fb5f58a820353bd7095de526253c14fd'+url.split(__baseurl__)[1]+str(int(round(int(time())/3600.0/24.0)))).hexdigest())
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    httpdata = replace_words(httpdata, word_dic)
    return json.loads(httpdata)

def OBSAH():
    addDir(u'Nejnovější videa',__baseurl__ + '/timeline/latest',3,icon)
    addDir(u'Všechny pořady',__baseurl__ + '/catalogue',1,icon)
    addDir(u'Pohádky',__baseurl__ + '/catalogue?channels=3',1,icon)

def LIST_SHOWS(url):
    data = getJsonDataFromUrl(url)
    for item in data[u'_embedded'][u'stream:show']:
            link = __baseurl__+item[u'_links'][u'self'][u'href']
            image = makeImageUrl(item[u'image'])
            name = item[u'name']
            addDir(name,link,2,image)

def LIST_SEASON(url):
    data = getJsonDataFromUrl(url)
    seasons = data[u'_embedded'][u'stream:season']
    if type(seasons) is dict:
        for item in seasons[u'_embedded'][u'stream:episode']:
            link = __baseurl__+item[u'_links'][u'self'][u'href']
            image = makeImageUrl(item[u'image'])
            name = item[u'name']
            addDir(name,link,10,image)
    elif type(seasons) is list:
        for season in seasons:
            try:
                for episode in season[u'_embedded'][u'stream:episode']:
                    link = __baseurl__+episode[u'_links'][u'self'][u'href']
                    image = makeImageUrl(episode[u'image'])
                    name = season[u'name'] +' | '+ episode[u'name']
                    addDir(name,link,10,image)
            except:
                continue
    try:
        link = __baseurl__+data[u'_links'][u'next'][u'href']
        addDir(u'[B]Další epizody pořadu >>[/B]',link,2,nexticon)
    except:
        logDbg('Další epizody nenalezeny')

def LIST_EPISODES(url):
    data = getJsonDataFromUrl(url)
    for item in data[u'_embedded'][u'stream:episode']:
        link = __baseurl__+item[u'_links'][u'self'][u'href']
        image = makeImageUrl(item[u'image'])
        name = item[u'_embedded'][u'stream:show'][u'name'] + ' | ' + item[u'name']
        addDir(name,link,10,image)
    try:
        link = __baseurl__+data[u'_links'][u'next'][u'href']
        addDir(u'[B]Další epizody pořadu >>[/B]',link,3,nexticon)
    except:
        logDbg('Další epizody nenalezeny')

def VIDEOLINK(url,name):
    data = getJsonDataFromUrl(url)
    name = data[u'name']
    thumb = makeImageUrl(data[u'image'])
    popis = data[u'detail']

    for item in data[u'video_qualities']:
        try:
            for fmt in item[u'formats']:
                if fmt[u'type'] == 'video/mp4':
                    stream_url = fmt[u'source']
                    quality = fmt[u'quality']
                    addLink(quality+' '+name,stream_url,thumb,popis)
        except:
            continue

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

logDbg("Mode: "+str(mode))
logDbg("URL: "+str(url))
strname = name is None and str(name) or name
logDbg("Name: "+ strname)

if mode==None or url==None or len(url)<1:
        OBSAH()
       
elif mode==1:
        LIST_SHOWS(url)

elif mode==2:
        LIST_SEASON(url)

elif mode==3:
        LIST_EPISODES(url)

elif mode==10:
        VIDEOLINK(url,name)
