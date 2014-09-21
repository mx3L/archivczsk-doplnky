# -*- coding: UTF-8 -*-
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
#  Credits to Jirka Vyhnalek - author of markiza plugin from dmd-xbmc project
#  Some sources in this plugin are used from this project
#
#


import urllib
import urllib2
import base64
import hashlib
import re
import os
import cookielib
import decimal
import random

import aes
import simplejson as json
from parseutils import *

from util import addDir, addLink, showInfo, showError, showWarning
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__baseurl__ = 'http://voyo.markiza.sk'
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'

__settings__ = ArchivCZSK.get_xbmc_addon('plugin.video.voyosk')
home = __settings__.getAddonInfo('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png')

username = __settings__.getSetting('username')
password = __settings__.getSetting('password')
dev_hash = __settings__.getSetting('devhash')

user_php_url = 'http://voyo.markiza.sk/bin/eshop/ws/user.php'
wallet_php_url = 'http://voyo.markiza.sk/bin/eshop/ws/ewallet.php'
player_php_url = 'http://voyo.markiza.sk/bin/eshop/ws/plusPlayer.php'
livestream_php_url = 'http://voyo.markiza.sk/lbin/player/LiveStream.php'

MAX_PAGE_ENTRIES = 35

RECENT_START = 'trckproductrecent'
RECENT_ITER_RE = """
  <li\ class=\"item\">\s+
    <div\ class=\"poster\">\s+
    <a\ href=\"(?P<url>.+?)\"\ title=\"(?P<title>.+?)\"[^>]+>.+?
      <img\ src=\"(?P<img>.+?)\".+?/>.+?
    </a>.+?
  </li>
  """
RECENT_END = 'trckproducttopwatched'

TOP_WATCHED_START = RECENT_END
TOP_WATCHED_ITER_RE = RECENT_ITER_RE
TOP_WATCHED_END = 'trckproductrecenttv'

RECENT_TV_START = TOP_WATCHED_END
RECENT_TV_ITER_RE = RECENT_END
RECENT_TV_END = 'trckproductupcoming'

LISTING_START = 'productsList series'
LISTING_END = 'productsList latestEpisodes'
PAGER_RE = "<span class=\'next next_set\'><a href=\'([^']+)"
VIDEOLINK_LIVE_RE = "clip:.+?url:.*?\'(?P<playpath>[^']+).+?plugins:.+?netConnectionUrl:.*?\'(?P<url>[^']+)"
CATEGORIES_ITER_RE = '<div class=\"item">.*?<div class=\"image\">.*?<img src=\"(?P<img>[^"]+).*?<div class=\"description\">.*?<a href=\"(?P<url>[^"]+).*?title=\"(?P<title>[^"]+).*?<\/div>.*?<\/div>.*?<\/div>'
LISTING_ITER_RE = '<li class=\"item_ul\">.*?<a href=\"(?P<url>[^"]+)".*?title=\"(?P<title>[^"]+).*?<img src=\"(?P<img>[^"]+).+?<\/li>'
LIVE_ITER_RE = '<a href=\"\?channel=(?P<channel>[^"]+).+?title=\"(?P<title>[^"]+)'


if username == "" or password == "":
    showInfo('VOYO SK archív je prístupný po zadaní použivateľského mena a hesla')


def substr(data, start, end):
    start = data.find(start)
    end = data.find(end)
    if start != -1 and end != -1:
        data = data[start:end]
    elif end != -1:
        data = data[:end]
    elif start != -1:
        data = data[start:]
    return data

def OBSAH():
    addDir('[B]Najnovšie[/B]', __baseurl__, 4, icon)
    addDir('[B]Najsledovanejšie[/B]', __baseurl__, 5, icon)
    addDir('[B]Poznáte z TV[/B]', __baseurl__, 6, icon)
    addDir('Filmy', __baseurl__ + '/filmy/', 1, icon)
    addDir('Domáce Seriály', __baseurl__ + '/zoznam/serialy/', 1, icon)
    addDir('Naše show', __baseurl__ + '/zoznam/nase-show/',1, icon)
    addDir('Zahraničné Seriály', __baseurl__ + '/zoznam/serialy-zahranicne/', 1, icon)
    addDir('Zábava', __baseurl__ + '/zoznam/zabava/', 1, icon)
    addDir('Spravodajstvo', __baseurl__ + '/zoznam/spravodajstvo/', 1, icon)
    addDir('Dokumenty', __baseurl__ + '/dokumenty/', 1, icon)
    addDir('Deti', __baseurl__ + '/deti/', 1, icon)
    #addDir('Živé vysielanie', __baseurl__ + '/zive-vysielanie/', 2, icon)

def VOYO_OBSAH(url, name='', page=None):
    i = 0
    iter1 = False
    iter2 = False
    data = markiza_read(url)
    data = substr(data, LISTING_START, LISTING_END)

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
        addDir('[B]Daľšia strana[/B]', nexturl, 1, nexticon, page=page)

    if not iter1 and not iter2:
        VIDEOLINK(url, name)

def VOYO_OBSAH_RECENT():
    data = markiza_read(__baseurl__)
    data = substr(data, RECENT_START, RECENT_END)
    for item in re.finditer(RECENT_ITER_RE, data, re.DOTALL|re.VERBOSE):
        addDir(item.group('title'), __baseurl__ + item.group('url'), 1, item.group('img'))

def VOYO_OBSAH_TOP():
    data = markiza_read(__baseurl__)
    data = substr(data, TOP_WATCHED_START, TOP_WATCHED_END)
    for item in re.finditer(TOP_WATCHED_ITER_RE, data, re.DOTALL|re.VERBOSE):
        addDir(item.group('title'), __baseurl__ + item.group('url'), 1, item.group('img'))

def VOYO_OBSAH_RECENT_TV():
    data = markiza_read(__baseurl__)
    data = substr(data, RECENT_TV_START, RECENT_TV_END)
    for item in re.finditer(TOP_WATCHED_ITER_RE, data, re.DOTALL|re.VERBOSE):
        addDir(item.group('title'), __baseurl__ + item.group('url'), 1, item.group('img'))

def VOYO_OBSAH_LIVE():
    data = markiza_read(livestream_php_url)
    data = data[data.find('<div class="live_buttons_wrap">'):]
    for live in re.finditer(LIVE_ITER_RE, data, re.DOTALL):
        addDir(live.group('channel'), live.group('channel'), 3, None)

def VIDEOLINK_LIVE(channel, name):
    if not islogged_in():
        log_in(username, password)

    r = gen_random_decimal(0, 99999999999999)
    livestream_params = {'channel':channel, 'r':r}
    livestream_url = livestream_php_url + '?' + urllib.urlencode(livestream_params)
    request = urllib2.Request(livestream_url)
    request.add_header("Referer", 'http://voyo.markiza.sk/zive-vysielanie/')
    request.add_header("Accept", "application/json, text/javascript, */*")
    request.add_header("X-Requested-With", "XMLHttpRequest")
    request.add_header("User-Agent", _UserAgent_)
    response = urllib2.urlopen(request)
    data = response.read()
    response.close()

    video = re.search(VIDEOLINK_LIVE_RE, data, re.DOTALL)
    if video is not None:
        link = video.group('url') + '/' + video.group('playpath') + " pageUrl=" + livestream_php_url + '?' + channel + " live=1"
        addLink(name, link, None)

def VIDEOLINK(url, name):

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

    global dev_hash
    if dev_hash == "":
        new_devhash = gen_dev_hash()
        add_dev(new_devhash)
        dev_hash = new_devhash
        __settings__.setSetting('devhash', new_devhash)

    # to remove device
    # http://voyo.markiza.sk/profil?sect=subscription

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
    else:
        html = data[u'html']
        exec(base64.decodestring("Y29uZmlnX2FlcyA9IHJlLnNlYXJjaCgndmFyIHZveW9QbHVzQ29uZmlnLipbXiJdKyIoLis/KSI7\nJywgaHRtbCwgcmUuRE9UQUxMKS5ncm91cCgxKTtjb25maWcgPSBhZXMuZGVjcnlwdChjb25maWdf\nYWVzLCAnRWFEVXV0ZzRwcEdZWHdOTUZkUkpzYWRlbkZTbkk2Z0onLCAxMjgpLnJlcGxhY2UoJ1wv\nJywnLycpO3NlY3JldCA9IHJlLnNlYXJjaChyJyJzZWNyZXQiOiIoLis/KSInLCBjb25maWcpLmdy\nb3VwKDEpO2FwcF9pZCA9IHJlLnNlYXJjaChyJyJhcHBJZCI6IiguKz8pIicsIGNvbmZpZykuZ3Jv\ndXAoMSk7c2VydmljZV91cmwgPSByZS5zZWFyY2gocicic2VydmljZVVybCI6IiguKz8pIicsIGNv\nbmZpZykuZ3JvdXAoMSk7dGltZV9zZXJ2aWNlX3VybCA9IHJlLnNlYXJjaChyJyJ0aW1lU2Vydmlj\nZVVybCI6IiguKz8pIicsIGNvbmZpZykuZ3JvdXAoMSk7dGltZXN0YW1wID0gbWFya2l6YV9yZWFk\nKHRpbWVfc2VydmljZV91cmwpWzoxNF07c2lnbmF0dXJlID0gYmFzZTY0LmI2NGVuY29kZShoYXNo\nbGliLm1kNSgiezB9fHsxfXx7Mn18ezN9Ii5mb3JtYXQoYXBwX2lkLCBtZWRpYSwgdGltZXN0YW1w\nLCBzZWNyZXQpKS5kaWdlc3QoKSk7c2VydmljZV91cmwgPSAiezB9P3Q9ezF9JmQ9MSZjPXsyfXx7\nM30maD0wJnRtPW5vdmEmcz17NH0iLmZvcm1hdChzZXJ2aWNlX3VybCx0aW1lc3RhbXAsYXBwX2lk\nLG1lZGlhLHVybGxpYi5xdW90ZShzaWduYXR1cmUpKQ==\n")) in globals(),locals()
        service_xml = markiza_read(service_url)
        baseurl = re.compile('<baseUrl>(.+?)</baseUrl>').findall(service_xml)
        baseurl = re.sub(r'<!\[CDATA\[([^\]]+)\]\]>',r'\1',baseurl[0])
        streamurl = re.compile('<media>\s*<quality>(.+?)</quality>\s*<url>(.+?)</url>\s*</media>').findall(service_xml)
        for quality, playpath in streamurl:
            quality = re.sub(r'<!\[CDATA\[([^\]]+)\]\]>',r'\1', quality)
            playpath = re.sub(r'<!\[CDATA\[([^\]]+)\]\]>',r'\1', playpath)
            url = "%s playpath=%s" % (baseurl, playpath)
            if quality == 'hq':
                continue
            addLink(name, url, None)

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

def markiza_read(url):
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
        name = urllib.unquote_plus(params["name"])
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

if mode == None or url == None or len(url) < 1:
    init_opener()
    OBSAH()
elif mode == 1:
    VOYO_OBSAH(url, name, page)
elif mode == 2:
    VOYO_OBSAH_LIVE()
elif mode == 3:
    VIDEOLINK_LIVE(url, name)
elif mode == 4:
    VOYO_OBSAH_RECENT()
elif mode == 5:
    VOYO_OBSAH_TOP()
elif mode == 6:
    VOYO_OBSAH_RECENT_TV()