# -*- coding: utf-8 -*-
#
# plugin.video.orangetv
# based od o2tvgo by Stepan Ort
#
# (c) Michal Novotny
#
# original at https://www.github.com/misanov/
#
# free for non commercial use
#

import urllib2,urllib,re,sys,os,string,time,base64,datetime,json,aes,requests,random
import email.utils as eut
from urlparse import urlparse, urlunparse, parse_qs
from uuid import getnode as get_mac
from Components.config import config
from Plugins.Extensions.archivCZSK.engine import client

try:
    import hashlib
except ImportError:
    import md5

from parseutils import *
from util import addDir, addLink, addSearch, getSearch
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

addon =  ArchivCZSK.get_xbmc_addon('plugin.video.orangetv')
profile = addon.getAddonInfo('profile')
home = addon.getAddonInfo('path')
icon =  os.path.join( home, 'icon.png' )
otvusr = addon.getSetting('orangetvuser')
otvpwd = addon.getSetting('orangetvpwd')
_deviceid = addon.getSetting('deviceid')
_quality = 'PC'
_COMMON_HEADERS = {"X-NanguTv-App-Version": "Android#1.2.9",
                   "X-NanguTv-Device-Name": "Nexus 7",
                   "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1.1; Nexus 7 Build/LMY47V)",
                   "Accept-Encoding": "gzip",
                   "Connection": "Keep-Alive"}

def device_id():
    mac = get_mac()
    hexed    = hex((mac * 7919) % (2 ** 64))
    return ('0000000000000000' + hexed[2:-1])[16:]

def random_hex16():
    return ''.join([random.choice('0123456789abcdef') for x in range(16)])

def _to_string(text):
    if type(text).__name__ == 'unicode':
        output = text.encode('utf-8')
    else:
        output = str(text)
    return output

def _log(message):
   try:
        f = open(os.path.join(config.plugins.archivCZSK.logPath.getValue(),'orange.log'), 'a')
        dtn = datetime.datetime.now()
        f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " %s\n" % message)
        f.close()
   except:
       pass

class LiveChannel:
    def __init__(self, o2tv, channel_key, name, logo_url, weight, quality):
        self._o2tv = o2tv
        self.channel_key = channel_key
        self.name = name
        self.weight = weight
        self.logo_url = logo_url
        self.quality = quality

class ChannelIsNotBroadcastingError(BaseException):
    pass


class AuthenticationError(BaseException):
    pass


class TooManyDevicesError(BaseException):
    pass


# JiRo - doplněna kontrola zaplacené služby
class NoPurchasedServiceError(BaseException):
    pass


class O2TVGO:

    def __init__(self, device_id, username, password, quality, log_function=None):  # JiRo - doplněn parametr kvality
        self.username = username
        self.password = password
        self._live_channels = {}
        self.access_token = None
        self.subscription_code = None
        self.locality = None
        self.offer = None
        self.device_id = device_id
        self.quality = quality  # JiRo - doplněn parametr kvality
        self.log_function = log_function


    def get_access_token_password(self):
        _log('Getting Token via password...')
        if not self.username or not self.password:
            raise AuthenticationError()
        headers = _COMMON_HEADERS
        headers["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"
        data = {'grant_type': 'password',
                'client_id': 'orangesk-mobile',
                'client_secret': 'e4ec1e957306e306c1fd2c706a69606b',
                'isp_id': '5',
                'username': self.username,
                'password': self.password,
                'platform_id': 'b0af5c7d6e17f24259a20cf60e069c22',
                'custom': 'orangesk-mobile',
                'response_type': 'token'
                }
        req = requests.post('https://oauth01.gtm.orange.sk/oauth/token',
                            data=data, headers=headers, verify=False)
        j = req.json()
#        _log(j)
        if 'error' in j:
            error = j['error']
            if error == 'authentication-failed':
                _log('Authentication Error')
                return None
            else:
                raise Exception(error)
        self.access_token = j["access_token"]
        self.expires_in = j["expires_in"]
        _log('Token OK')
        return self.access_token

    def refresh_access_token(self):
        if not self.access_token:
            self.get_access_token_password()
        if not self.access_token:
            _log('Authentication Error (failed to get token)')
            raise AuthenticationError()
        return self.access_token

    def refresh_configuration(self):
        if not self.access_token:
            self.refresh_access_token()
        access_token = self.access_token
        headers = _COMMON_HEADERS
        cookies = {"access_token": access_token, "deviceId": self.device_id}
        req = requests.get(
            'https://app01.gtm.orange.sk/sws//subscription/settings/subscription-configuration.json', headers=headers,
            cookies=cookies)
        j = req.json()
#        _log(j)
        if 'errorMessage' in j:
            error_message = j['errorMessage']
            status_message = j['statusMessage']
            # JiRo - změna z 'unauthorized-device' na 'devices-limit-exceeded'
            if status_message == 'devices-limit-exceeded':
                raise TooManyDevicesError()
            else:
                raise Exception(error_message)
        self.subscription_code = _to_string(j["subscription"])
        self.offer = j["billingParams"]["offers"]
        self.tariff = j["billingParams"]["tariff"]
        self.locality = j["locality"]

    def live_channels(self):
        if not self.access_token:
            self.refresh_access_token()
        access_token = self.access_token
        if not self.offer:
            self.refresh_configuration()
        offer = self.offer
        if not self.tariff:
            self.refresh_configuration()
        tariff = self.tariff
        if not self.locality:
            self.refresh_configuration()
        locality = self.locality
        quality = self.quality  # JiRo - doplněn parametr kvality
        if len(self._live_channels) == 0:
            headers = _COMMON_HEADERS
            cookies = {"access_token": access_token,
                       "deviceId": self.device_id}
            params = {"locality": self.locality,
                      "tariff": self.tariff ,
                      "isp": "5",
                      "imageSize": "LARGE",
                      "language": "slo",
                      "deviceType": "PC",
                      "liveTvStreamingProtocol": "HLS",
                      "offer": self.offer}  # doplněn parametr kvality
            req = requests.get('http://app01.gtm.orange.sk/sws/server/tv/channels.json',
                               params=params, headers=headers, cookies=cookies)
            j = req.json()
#            _log(j)
            purchased_channels = j['purchasedChannels']
            if len(purchased_channels) == 0:  # JiRo - doplněna kontrola zaplacené služby
                raise NoPurchasedServiceError()  # JiRo - doplněna kontrola zaplacené služby
            items = j['channels']
            for channel_id, item in items.iteritems():
                if channel_id in purchased_channels:
                    live = item['liveTvPlayable']
                    if live:
                        channel_key = _to_string(item['channelKey'])
                        logo = _to_string(item['screenshots'][0])
                        if not logo.startswith('http://'):
                            logo = 'http://app01.gtm.orange.sk/' + logo
                        name = _to_string(item['channelName'])
                        weight = item['weight']
                        self._live_channels[channel_key] = LiveChannel(
                            self, channel_key, name, logo, weight, quality)  # doplněn parametr kvality
            done = False
            offset = 0

        return self._live_channels

#### MAIN

authent_error = 'AuthenticationError'
toomany_error = 'TooManyDevicesError'
nopurch_error = 'NoPurchasedServiceError'

def OBSAH():
    o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
    channels = o2tv.live_channels()
    channels_sorted = sorted(channels.values(), key=lambda _channel: _channel.weight)
    for channel in channels_sorted:
        addDir(_to_string(channel.name),channel.channel_key,4,channel.logo_url,1)

def VIDEOLINK(name, channel_key):
    o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
    if not o2tv.access_token:
        o2tv.refresh_access_token()
    access_token = o2tv.access_token
    if not o2tv.subscription_code:
        o2tv.refresh_configuration()
    subscription_code = o2tv.subscription_code
    playlist = None
    while access_token:
        params = {"serviceType": "LIVE_TV",
                  "subscriptionCode": subscription_code,
                  "channelKey": channel_key,
                  "deviceType": _quality,
                  "streamingProtocol": "HLS"}
        headers = _COMMON_HEADERS
        cookies = {"access_token": access_token, "deviceId": _deviceid}
        req = requests.get('http://app01.gtm.orange.sk/sws/server/streaming/uris.json', params=params, headers=headers, cookies=cookies)
        json_data = req.json()
#        _log(channel_key)
#        _log(json_data)
        access_token = None
        if 'statusMessage' in json_data:
            status = json_data['statusMessage']
            if status == 'bad-credentials':
                access_token = o2tv.refresh_access_token()
            elif status == 'channel.not-found':
                raise ChannelIsNotBroadcastingError()
            else:
                raise Exception(status)
        else:
            # Pavuucek: Pokus o vynucení HD kvality
            playlist = ""
            # pro kvalitu STB nebo PC se pokusíme vybrat HD adresu.
            # když není k dispozici, tak první v seznamu
            for uris in json_data["uris"]:
                if o2tv.quality == "STB" or o2tv.quality == "PC":
                    if uris["resolution"] == "HD" and playlist == "":
                        playlist = uris["uri"]
                else:
                    # pro ostatní vracíme SD adresu
                    if uris["resolution"] == "SD" and playlist == "":
                        playlist = uris["uri"]
            # playlist nebyl přiřazený, takže první adresa v seznamu
            if playlist == "":
                playlist = json_data["uris"][0]["uri"]
    # stahneme a zpracujeme playlist
    r = requests.get(playlist, headers=_COMMON_HEADERS).text
    for m in re.finditer('#EXT-X-STREAM-INF:PROGRAM-ID=\d+,BANDWIDTH=(?P<bandwidth>\d+),AUDIO="\d+"\s(?P<chunklist>[^\s]+)', r, re.DOTALL):
        bandwidth = int(m.group('bandwidth'))
        quality = ""
        if bandwidth < 2000000:
            quality = "480p"
        elif bandwidth >= 2000000 and bandwidth < 3000000:
            quality = "576p"
        elif bandwidth >= 3000000 and bandwidth < 6000000:
            quality = "720p"
        else:
            quality = "1080p"
        url = m.group('chunklist')
        addLink('['+quality+'] '+name, url, None, "")

name=None
url=None
mode=None
thumb=None
page=None
desc=None

if not _deviceid:
    first_device_id = device_id()
    second_device_id = device_id()
    if first_device_id == second_device_id:
        _device_id = first_device_id
    else:
        _device_id = random_hex16()
    addon.setSetting('deviceid', _deviceid)

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
        thumb=urllib.unquote_plus(params["thumb"])
except:
        pass

if otvusr == "" and otvpwd == "":
    client.add_operation("SHOW_MSG", {'msg': 'Prosim, vlozte nejdrive prihlasovaci udaje', 'msgType': 'error', 'msgTimeout': 30, 'canClose': True})
elif mode==None or url==None or len(url)<1:
    OBSAH()
elif mode==4:
    VIDEOLINK(name, url)
