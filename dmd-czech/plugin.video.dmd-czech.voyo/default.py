# -*- coding: utf-8 -*-

import  string, time, base64, datetime
from urlparse import urlparse
try:
    import hashlib
except ImportError:
    import md5

__dmdbase__ = 'http://iamm.uvadi.cz/xbmc/voyo/'
page_pole_url = []
page_pole_no = []
rtmp_token = 'h0M*t:pa$kA'
nova_service_url = 'http://master-ng.nacevi.cz/cdn.server/PlayerLink.ashx'
nova_app_id = 'nova-vod'


def VIDEOLINK_TEST(url, name):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    mediaid = re.compile('mainVideo = new mediaData\(.+?, .+?, (.+?),').findall(httpdata)
    thumb = re.compile('<link rel="image_src" href="(.+?)" />').findall(httpdata)
    popis = re.compile('<meta name="description" content="(.+?)" />').findall(httpdata)
    datum = datetime.datetime.now()
    timestamp = datum.strftime('%Y%m%d%H%M%S')
    videoid = urllib.quote(nova_app_id + '|' + mediaid[0])
    md5hash = nova_app_id + '|' + mediaid[0] + '|' + timestamp + '|' + secret_token
    try:
        md5hash = hashlib.md5(md5hash)
    except:
        md5hash = md5.new(md5hash)
    signature = urllib.quote(base64.b64encode(md5hash.digest()))
    config = nova_service_url + '?t=' + timestamp + '&d=1&tm=nova&h=0&c=' + videoid + '&s=' + signature    
    print config
    try:
        desc = popis[0]
    except:
        desc = name
    req = urllib2.Request(config)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    if __settings__.get_setting('test_nastaveni'):
        print httpdata
    error_secret_token = re.compile('<errorCode>(.+?)</errorCode>').findall(httpdata)
    try:
        chyba = int(error_secret_token[0])
    except:
        chyba = 0
    if chyba == 2:    
        print 'Nesprávné tajné heslo'
        showWarning(u"Doplněk DMD VOYO Nesprávné tajné heslo!")
        #__settings__.open_settings(session)        
    elif chyba == 1:    
        print 'Špatné časové razítko'
        showError(u"Doplněk DMD VOYO Pořad lze přehrát pouze na webu Voyo.cz!")
        #xbmc.executebuiltin("XBMC.Notification('Doplněk DMD VOYO','Pořad lze přehrát pouze na webu Voyo.cz!',30000,"+icon+")")      
    elif chyba == 0:
        baseurl = re.compile('<baseUrl>(.+?)</baseUrl>').findall(httpdata)
        streamurl = re.compile('<media>\s<quality>(.+?)</quality>.\s<url>(.+?)</url>\s</media>').findall(httpdata)        
        for kvalita, odkaz in streamurl:
            #print kvalita,odkaz
            if re.match('hd', kvalita, re.U):
                urlhd = odkaz.encode('utf-8')
            elif re.match('hq', kvalita, re.U):
                urlhq = odkaz.encode('utf-8')
            elif re.match('lq', kvalita, re.U):
                urllq = odkaz.encode('utf-8')
        print urlhq, urllq
        swfurl = 'http://voyo.nova.cz/static/shared/app/flowplayer/13-flowplayer.commercial-3.1.5-19-003.swf'
        if __settings__.get_setting('test_nastaveni'):          
            rtmp_url_lq = baseurl[0] + ' playpath=' + urllq + ' pageUrl=' + url + ' swfUrl=' + swfurl + ' swfVfy=true token=' + rtmp_token 
            rtmp_url_hq = baseurl[0] + ' playpath=' + urlhq + ' pageUrl=' + url + ' swfUrl=' + swfurl + ' swfVfy=true token=' + rtmp_token 
            try:
                rtmp_url_hd = baseurl[0] + ' playpath=' + urlhd + ' pageUrl=' + url + ' swfUrl=' + swfurl + ' swfVfy=true token=' + rtmp_token 
            except:
                rtmp_url_hd = 0
        else:
            rtmp_url_lq = baseurl[0] + ' playpath=' + urllq
            rtmp_url_hq = baseurl[0] + ' playpath=' + urlhq
            try:
                rtmp_url_hd = baseurl[0] + ' playpath=' + urlhd            
            except:
                rtmp_url_hd = 0
        if __settings__.get_setting('kvalita_sel') == "HQ":
            addLink("HQ " + name, rtmp_url_hq, icon, desc)
        elif __settings__.get_setting('kvalita_sel') == "LQ":
            addLink("LQ " + name, rtmp_url_lq, icon, desc)
        elif __settings__.get_setting('kvalita_sel') == "HD":
            if rtmp_url_hd == 0:
                addLink("HQ " + name, rtmp_url_hq, icon, desc)                
            else:
                addLink("HD " + name, rtmp_url_hd, icon, desc)
        else:
            addLink("HQ " + name, rtmp_url_hq, icon, desc)


#/*
# *      Copyright (C) 2013 mx3L
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

#
#  Credits to Jirka Vyhnalek - author of voyocz plugin from dmd-xbmc project
#  Some sources in this plugin are used from this project
#  
#

import urllib
import urllib2
import re
import os
import cookielib
import decimal
import random

import simplejson as json


from util import addDir, addLink, showInfo, showError, showWarning
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

sys.path.append(os.path.join (os.path.dirname(__file__), 'resources', 'lib'))

try:
    import voyo27 as voyo
except ImportError:
    import voyo26 as voyo

__baseurl__ = 'http://voyo.nova.cz'
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'
__settings__ = ArchivCZSK.get_xbmc_addon('plugin.video.dmd-czech.voyo')
home = __settings__.getAddonInfo('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png') 

username = __settings__.getSetting('username')
password = __settings__.getSetting('password')
dev_hash = __settings__.getSetting('devhash')
secret_token = __settings__.getSetting('secret_token')

user_php_url = __baseurl__ + '/bin/eshop/ws/user.php'
wallet_php_url = __baseurl__ + '/bin/eshop/ws/ewallet.php'
player_php_url = __baseurl__ + '/bin/eshop/ws/plusPlayer.php'

MAX_PAGE_ENTRIES = 35
PAGER_RE = "<span class=\'next next_set\'><a href=\'([^']+)"
LISTING_START = 'productsList series'
LISTING_END = 'productsList latestEpisodes'

VIDEOLINK_LIVE_RE = "clip:.+?url:.*?\'(?P<playpath>[^']+).+?plugins:.+?netConnectionUrl:.*?\'(?P<url>[^']+)"
CATEGORIES_ITER_RE = '<div class=\"item">.*?<div class=\"image\">.*?<img src=\"(?P<img>[^"]+).*?<div class=\"description\">.*?<a href=\"(?P<url>[^"]+).*?title=\"(?P<title>[^"]+).*?<\/div>.*?<\/div>.*?<\/div>'
LISTING_ITER_RE = '<li class=\"item_ul\">.*?<a href=\"(?P<url>[^"]+)".*?title=\"(?P<title>[^"]+).*?<img src=\"(?P<img>[^"]+).+?<\/li>'
LIVE_ITER_RE = '<a href=\"\?channel=(?P<channel>[^"]+).+?title=\"(?P<title>[^"]+)'


if  (username == "" or password == "") and secret_token == "":
    showInfo('VOYO CZ archív je prístupný po zadaní použivateľského mena a hesla')


def OBSAH():
    #addDir('Filmy', __baseurl__ + '/filmy/', 1, icon) #not working - use of silverlight
    addDir('Seriály', __baseurl__ + '/serialy/', 1, icon)
    addDir('Pořady', __baseurl__ + '/porady/', 1, icon)
    addDir('Zprávy', __baseurl__ + '/zpravy/', 1, icon)
    #addDir('Deti', __baseurl__ + '/deti/', 1, icon) #not working - use of silverlight
    addDir('Sport', __baseurl__ + '/sport/', 1, icon)
    addDir('Živé vysielanie', __baseurl__ + '/tv-zive/', 2, icon)
    
def VOYO_OBSAH_LIVE():
    addDir('VOYO Cinema', __baseurl__ + '/product/tv-zive/28995-simulcast-voyo-cinema', 3, None)
    addDir('Nova', __baseurl__ + '/product/tv-zive/28992-simulcast-nova', 3, None)
    addDir('Nova Sport', __baseurl__ + '/product/tv-zive/28993-simulcast-nova-sport', 3, None)
    addDir('Fanda', __baseurl__ + '/product/tv-zive/33097-simulcast-fanda', 3, None)
    addDir('Telka', __baseurl__ + '/product/tv-zive/33917-simulcast-telka', 3, None)

def VOYO_OBSAH(url, name='', page=None):
    i = 0
    iter1 = False
    iter2 = False
    data = voyo_read(url)
    start = data.find(LISTING_START)
    end = data.find(LISTING_END)
    if start != -1 and end != -1:
        data = data[start:end]
    elif end != -1:
        data = data[:end]
    elif start != -1:
        data = data[start:]

    for item in re.finditer(CATEGORIES_ITER_RE, data, re.DOTALL):
        iter1 = True
        i += 1
        addDir(item.group('title'), __baseurl__ + item.group('url'), 1, item.group('img'))
    
    if not iter1:
        for item in re.finditer(LISTING_ITER_RE, data, re.DOTALL):
            iter2 = True
            i += 1
            addDir(item.group('title'), __baseurl__ + item.group('url'), 1, item.group('img'))
    
    if i == MAX_PAGE_ENTRIES:
        if page is None:
            page = 1
        page += 1
        idx = url.find('?page=')
        if idx != -1:
            nexturl = url[:idx] + '?page=' + str(page)
        else:
            nexturl = url + '?page=' + str(page)
        addDir('Daľšia strana >>', nexturl, 1, nexticon, page=page)
        
    if not iter1 and not iter2:
        if username != "":
            VIDEOLINK(url, name)
        else:
            VIDEOLINK_TEST(url, name)
    
        
def VIDEOLINK(url, name, live=False):
    
    def gen_dev_hash():
        r = gen_random_decimal(0, 99999999999999)
        device_params = {'x':'device', 'a':'generateNewHash', 'userId':urllib.quote(username), 'r':r}
        devicehash_url = wallet_php_url + '?' + urllib.urlencode(device_params)
    
        print 'generating new devicehash'
        request = create_req(devicehash_url)
        response = urllib2.urlopen(request)
        data = json.load(response)
        response.close()
        return data[u'hash']
    
    def add_dev(hash):
        r = gen_random_decimal(0, 99999999999999)
        client_details = '{"b":"FF","bv":"18.0","ua":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0"}'
        adddevice_params = {'x':'device', 'a':'add', 'deviceCode':'PC', 'deviceHash':hash, 'client':client_details, 'r':r}
        adddevice_url = wallet_php_url + '?' + urllib.urlencode(adddevice_params)
    
        print 'trying to add new device'
        request = create_req(adddevice_url)
        response = urllib2.urlopen(request)
        data = json.load(response)
        response.close()
        
        succ = data[u'ok']
        dev_hash = data[u'hash']
        if not succ:
            print 'device cannot be added, exception or "Maximum of free devices already reached"'
            showError(data[u'msg'])
        else:
            print 'device was successfully added'
        return dev_hash
    
    if not islogged_in():
        log_in(username, password)

    if dev_hash == "":
        new_devhash = gen_dev_hash()
        add_dev(new_devhash)
        __settings__.setSetting('devhash', new_devhash)
    
    # to remove device
    # http://voyo.nova.cz/profil?sect=subscription
    
    request = urllib2.Request(url)
    request.add_header('User-Agent', _UserAgent_)
    request.add_header("Referer", url)
    response = urllib2.urlopen(request)
    httpdata = response.read()
    response.close()

    media_data = re.search('mainVideo = new mediaData\((.+?), (.+?), (.+?),', httpdata)
    
    prod = media_data.group(1)
    unit = media_data.group(2)
    media = media_data.group(3)
    site = re.search('siteId: ([0-9]+)', httpdata).group(1)
    section = re.search('sectionId: ([0-9]+)', httpdata).group(1)
    subsite = re.search('subsite: \'(.+?)\',', httpdata).group(1)
    width = re.search('width: ([0-9]+)', httpdata).group(1)
    height = re.search('height: ([0-9]+)', httpdata).group(1)
    thumb = re.search('<link rel="image_src" href="(.+?)" />', httpdata)
    desc = re.search('<meta name="description" content="(.+?)" />', httpdata)
    desc = (desc and desc.group(1)) or name
    thumb = thumb and thumb.group(1)
    
    r = gen_random_decimal(0, 99999999999999)
    
    player_params = {
                   'x':'playerFlash',
                   'prod':prod,
                   'unit':unit,
                   'media':media,
                   'site':site,
                   'section':section,
                   'subsite':subsite,
                   'embed':0,
                   'realSite':site,
                   'width':width,
                   'height':height,
                   'hdEnabled':1,
                   'hash':'',
                   'finish':'finishedPlayer',
                   'dev':dev_hash,
                   'sts':'undefined',
                   'r': r,
                   }
    
    player_url = player_php_url + '?' + urllib.urlencode(player_params)
    request = create_req(player_url)
    response = urllib2.urlopen(request)
    data = json.load(response)
    response.close()
    
    if data[u'error']:
        showError(data[u'msg'])
    elif data[u'html'].find('silverlight') != -1:
        showError("Požadované video je možné prehrať len na webe VOYO CZ")
    else:
        html = data[u'html']
        req = urllib2.Request(voyo.get_config_url(html))
        req.add_header('User-Agent', _UserAgent_)
        response = urllib2.urlopen(req)
        httpdata = response.read()
        response.close()
        baseurl = re.compile('<baseUrl>(.+?)</baseUrl>').findall(httpdata)
        streamurl = re.compile('<media>\s<quality>(.+?)</quality>.\s<url>(.+?)</url>\s</media>').findall(httpdata) 
        
        for kvalita, odkaz in streamurl:
            if re.match('hd', kvalita, re.U):
                urlhd = odkaz.encode('utf-8')
            elif re.match('hq', kvalita, re.U):
                urlhq = odkaz.encode('utf-8')
            elif re.match('lq', kvalita, re.U):
                urllq = odkaz.encode('utf-8')

        swfurl = 'http://voyo.nova.cz/static/shared/app/flowplayer/13-flowplayer.commercial-3.1.5-19-003.swf'
        if live:
            rtmp_url_lq = baseurl[0] + '/' + urllq + ' live=true'
            rtmp_url_hq = baseurl[0] + '/' + urllq + ' live=true'
        else:
            rtmp_url_lq = baseurl[0] + ' playpath=' + urllq
            rtmp_url_hq = baseurl[0] + ' playpath=' + urlhq
        try:
            if live:
                rtmp_url_hd = baseurl[0] + '/' + urlhd + ' live=true'
            else:
                rtmp_url_hd = baseurl[0] + ' playpath=' + urlhd
        except:
            rtmp_url_hd = 0
        if __settings__.get_setting('kvalita_sel') == "HQ":
            addLink("HQ " + name, rtmp_url_hq, icon, desc)
        elif __settings__.get_setting('kvalita_sel') == "LQ":
            addLink("LQ " + name, rtmp_url_lq, icon, desc)
        elif __settings__.get_setting('kvalita_sel') == "HD":
            if rtmp_url_hd == 0:
                addLink("HQ " + name, rtmp_url_hq, icon, desc)                
            else:
                addLink("HD " + name, rtmp_url_hd, icon, desc)
        else:
            addLink("HQ " + name, rtmp_url_hq, icon, desc)

def gen_random_decimal(i, d):
        return decimal.Decimal('%d.%d' % (random.randint(0, i), random.randint(0, d)))
    
def init_opener():
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
    urllib2.install_opener(opener) 


def create_req(url, postdata=None):
    request = urllib2.Request(url, postdata)
    request.add_header('User-Agent', _UserAgent_)
    request.add_header("Referer", __baseurl__)    
    request.add_header("Accept", "application/json, text/javascript, */*")
    request.add_header("X-Requested-With", "XMLHttpRequest")
    return request 

def islogged_in():
    print 'checking if logged in'
    r = gen_random_decimal(0, 99999999999999)
    isloggedin_params = {'x':'isLoggedIn', 'r':r}
    isloggedin_url = user_php_url + '?' + urllib.urlencode(isloggedin_params)
    request = create_req(isloggedin_url)
    response = urllib2.urlopen(request)
    logged_in = response.read() == 'true'
    response.close()
    if logged_in:
        print 'already logged in'
    else:
        print 'not logged in'
    return logged_in

def log_in(username, password):
    print 'logging in...'
    r = gen_random_decimal(0, 99999999999999)
    login_params = {'x':'login', 'regMethod':'', 'regId':'', 'r':r}
    login_url = user_php_url + '?' + urllib.urlencode(login_params)
    postdata = urllib.urlencode({'u':username, 'p':password})
    request = create_req(login_url, postdata)
    response = urllib2.urlopen(request)
    data = json.load(response)
    response.close()
    if not data[u'logged']:
        showError(data[u'msg'])
    #elif not data[u'subscription']:
    #    print 'you dont have any subscription'
    #    raise showError(session,"Nemáte predplatné")
    else:
        print 'succesfully logged in'   

def voyo_read(url):
    count = 0
    response = None
    while (count < 20):
        count += 1
        request = urllib2.Request(url)
        request.add_header('User-Agent', _UserAgent_)
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            if e.code == 404:
                continue
            raise
        else:
            data = response.read()
            return data
        finally:
            response and response.close()   


url = None
name = None
thumb = None
mode = None
page = None

try:
        url = urllib.unquote_plus(params["url"])
except:
        pass
try:
        name = params["name"]
except:
        pass
try:
        mode = int(params["mode"])
except:
        pass
try:
        page = int(params["page"])
except:
        pass

print "Mode: " + str(mode)
print "URL: " + str(url)
print "Name: " + str(name)
print "Page: " + str(page)

if mode == None or url == None or len(url) < 1:
    init_opener()
    OBSAH()
       
elif mode == 1:
    VOYO_OBSAH(url, name, page)
        
elif mode == 2:
    VOYO_OBSAH_LIVE()
        
elif mode == 3:
    VIDEOLINK(url, name, True)
