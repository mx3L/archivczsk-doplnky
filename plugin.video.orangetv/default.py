# -*- coding: utf-8 -*-
#
# plugin.video.orangetv
# based od o2tvgo by Stepan Ort
#
# (c) Michal Novotny
#
# original at https://www.github.com/misanov/
#
# free for non commercial use with author credits
#

import urllib2,urllib,re,sys,os,string,time,base64,datetime,json,aes,requests,random
import email.utils as eut
from urlparse import urlparse, urlunparse, parse_qs
from uuid import getnode as get_mac
from datetime import date, timedelta
from Components.config import config
from Plugins.Extensions.archivCZSK.engine import client
from Plugins.Extensions.archivCZSK.engine.client import add_video

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
getquality = "1080p"
otvusr = addon.getSetting('orangetvuser')
otvpwd = addon.getSetting('orangetvpwd')
_deviceid = addon.getSetting('deviceid')
_quality = 'MOBILE'
try:
	with open(profile + "/epg.dat", "r") as file:
		epgcache = json.load(file)
except IOError:
	epgcache = {}

_COMMON_HEADERS = {
	"X-NanguTv-Platform-Id": "b0af5c7d6e17f24259a20cf60e069c22",
	"X-NanguTv-Device-size": "normal",
	"X-NanguTv-Device-Name": "Nexus 7",
	"X-NanguTv-App-Version": "Android#7.6.3-release",
	"X-NanguTv-Device-density": "440",
	"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; Nexus 7 Build/LMY47V)",
	"Connection": "keep-alive"}


def device_id():
	mac = get_mac()
	hexed	= hex((mac * 7919) % (2 ** 64))
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
	def __init__(self, o2tv, channel_key, name, logo_url, weight, quality, timeshift, number):
		self._o2tv = o2tv
		self.channel_key = channel_key
		self.name = name
		self.weight = weight
		self.logo_url = logo_url
		self.quality = quality
		self.timeshift = timeshift
		self.number = number


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
		self.devices = None

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
		req = requests.post('https://oauth01.gtm.orange.sk/oauth/token', data=data, headers=headers, verify=False)
		j = req.json()
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

	def device_remove(self,did):
		if not self.access_token:
			self.refresh_access_token()
		headers = _COMMON_HEADERS
		cookies = {"access_token": self.access_token, "deviceId": self.device_id}
		if did is None:
			did = ''
		params = {"deviceId": did}
		req = requests.get('https://app01.gtm.orange.sk/sws/subscription/settings/remove-device.json', params=params, headers=headers, cookies=cookies)
		j = req.json()

	def refresh_configuration(self):
		if not self.access_token:
			self.refresh_access_token()
		access_token = self.access_token
		headers = _COMMON_HEADERS
		cookies = {"access_token": access_token, "deviceId": self.device_id}
		req = requests.get('https://app01.gtm.orange.sk/sws//subscription/settings/subscription-configuration.json', headers=headers, cookies=cookies)
		j = req.json()
		if 'errorMessage' in j:
			client.showInfo('Err: '+j['errorMessage'])
		self.subscription_code = _to_string(j["subscription"])
		self.offer = j["billingParams"]["offers"]
		self.tariff = j["billingParams"]["tariff"]
		self.locality = j["locality"]
		self.devices = j["pairedDevices"]

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
		quality = self.quality
		timeshift = 0
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
			req = requests.get('http://app01.gtm.orange.sk/sws/server/tv/channels.json', params=params, headers=headers, cookies=cookies)
			j = req.json()
			purchased_channels = j['purchasedChannels']
			if len(purchased_channels) == 0:  # JiRo - doplněna kontrola zaplacené služby
				raise NoPurchasedServiceError()  # JiRo - doplněna kontrola zaplacené služby
			items = j['channels']
			for channel_id, item in items.iteritems():
				if channel_id in purchased_channels:
					live = item['liveTvPlayable']
					live = True # reseni nekterych nezobrazovanych kanalu?
					if item['timeShiftDuration']:
						timeshift = int(item['timeShiftDuration'])/60/24	# pocet dni zpetneho prehravani
					if live:
						channel_key = _to_string(item['channelKey'])
						logo = _to_string(item['screenshots'][0])
						if not logo.startswith('http://'):
							logo = 'http://app01.gtm.orange.sk/' + logo
						name = _to_string(item['channelName'])
						weight = item['weight']
						self._live_channels[channel_key] = LiveChannel(
							self, channel_key, name, logo, weight, quality, timeshift, item['channelNumber'])
			done = False
			offset = 0

		return self._live_channels

	def getChannelPrograms(self,ch):
		fromts = int(time.time())*1000
		tots = (int(time.time())+60)*1000
		hodiny = [0,21600,43200,86400,172800]
		title = ""
		desc = ""
		if int(addon.getSetting('epgcache')) != 0:
			tots = (int(time.time())+hodiny[int(addon.getSetting('epgcache'))])*1000
			if ch in epgcache:
				for epg in epgcache[ch]:
					if epg["start"] < fromts and epg["end"] > fromts:
						title = epg["title"]
						desc = epg["desc"]
						break
		if title == "":
			headers = _COMMON_HEADERS
			cookies = {"access_token": self.access_token, "deviceId": self.device_id}
			params = {"channelKey": ch, "fromTimestamp": fromts, "imageSize": "LARGE", "language": "ces", "offer": self.offer, "toTimestamp": tots}
			req = requests.get('https://app01.gtm.orange.sk/sws/server/tv/channel-programs.json', params=params, headers=headers, cookies=cookies)
			j = req.json()
			epgcache[ch] = []
			for one in j:
				title = _to_string(one["name"]) + " - " + datetime.datetime.fromtimestamp(one["startTimestamp"]/1000).strftime('%H:%M') + "-" + datetime.datetime.fromtimestamp(one["endTimestamp"]/1000).strftime('%H:%M')
				epgcache[ch].append({"start": one["startTimestamp"], "end": one["endTimestamp"], "title": title, "desc": one["shortDescription"]})
			title = _to_string(j[0]["name"]) + " - " + datetime.datetime.fromtimestamp(j[0]["startTimestamp"]/1000).strftime('%H:%M') + "-" + datetime.datetime.fromtimestamp(j[0]["endTimestamp"]/1000).strftime('%H:%M')
			desc = _to_string(j[0]["shortDescription"])
		return {"title": title, "desc": desc}

	def getArchivChannelPrograms(self,ch,day):
		if not self.access_token:
			self.refresh_access_token()
		access_token = self.access_token
		if not self.offer:
			self.refresh_configuration()
		fromts = int(day)*1000
		tots = (int(day)+86400)*1000
		headers = _COMMON_HEADERS
		cookies = {"access_token": self.access_token, "deviceId": self.device_id}
		params = {"channelKey": ch, "fromTimestamp": fromts, "imageSize": "LARGE", "language": "ces", "offer": self.offer, "toTimestamp": tots}
		req = requests.get('https://app01.gtm.orange.sk/sws/server/tv/channel-programs.json', params=params, headers=headers, cookies=cookies)
		j = req.json()
		for program in j:
			if int(time.time())*1000 > program["startTimestamp"]:
				title = _to_string(program["name"]) + " - [COLOR yellow]" + datetime.datetime.fromtimestamp(program["startTimestamp"]/1000).strftime('%H:%M') + "-" + datetime.datetime.fromtimestamp(program["endTimestamp"]/1000).strftime('%H:%M') + "[/COLOR]"
				addDir(title,ch+"|"+str(program["epgId"])+"|"+str(program["startTimestamp"])+"|"+str(program["endTimestamp"]),8,program["picture"],1, infoLabels={'plot':program["shortDescription"]})

#### MAIN

authent_error = 'AuthenticationError'
toomany_error = 'TooManyDevicesError'
nopurch_error = 'NoPurchasedServiceError'

def OBSAH():
	addDir("Naživo", 'live', 1, None, infoLabels={'plot':"Prvýkrát sa vďaka kešovania EPG načíta dlhšiu dobu, potom bude už načítať rýchlejšie podľa času v Nastavenie, ktorý si môžete zmeniť (defaultne 24 hodín)."})
	addDir("Archív", 'archiv', 2, None, infoLabels={'plot':"Tu nájdete spätné prehrávanie vašich kanálov, pokiaľ máte zaplatenú službu archívu."})
#	addDir("Playlist", 'playlist', 5, None, infoLabels={'plot':"Tímto sa vytvorí orangetv.pls v tmp pro bouguet."})
	if addon.getSetting('showdevices')=='true':
		addDir("Zariadenia", 'devices', 9, None, infoLabels={'plot':"Tu si môžete zobraziť a prípadne vymazať/odregistrovať zbytočná zariadenia, aby ste sa mohli znova inde prihlásiť."})

def DEVICES():
	o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
	o2tv.refresh_configuration()
	for pdev in o2tv.devices:
		title = _to_string(pdev["deviceName"]) + " - " + datetime.datetime.fromtimestamp(int(pdev["lastLoginTimestamp"]/1000)).strftime('%d.%m.%Y %H:%M') + " - " + pdev["lastLoginIpAddress"] + " - " + _to_string(pdev["deviceId"])
		addDir(title, 'device', 0, None, menuItems={'Zmazať zariadenie!': {'url': 'deldev', 'name': pdev["deviceId"]}}, infoLabels={'plot':"V menu môžete zariadenie vymazať pomocou Zmazať zariadenie!"})

def DEVICEREMOVE(did):
	o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
	o2tv.device_remove(did)
	addLink("[COLOR red]Zariadenie vymazané[/COLOR]","#",None,"")

def ARCHIV():
	o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
	channels = o2tv.live_channels()
	channels_sorted = sorted(channels.values(), key=lambda _channel: _channel.number)
	for channel in channels_sorted:
		if channel.timeshift > 0:
			tsd = channel.timeshift
			if tsd == 1: dtext=" den"
			elif tsd <5: dtext=" dny"
			else: dtext=" dní"
			addDir(_to_string(channel.name)+" [COLOR green]["+str(tsd)+dtext+"][/COLOR]",channel.channel_key+'|'+str(tsd),3,channel.logo_url,1)

def ARCHIVDAYS(url):
	cid,days = url.split("|")
#	addDir('Budoucí (nastavení nahrávek)', get_url(action='future_days', cid=cid), 1, None)
	for i in range(int(days)+1):
		day = date.today() - timedelta(days = i)
		if i == 0:
			den = "Dnes"
		elif i == 1:
			den = "Včera"
		else:
			den = day_translation[day.strftime("%A")].decode("utf-8") + " " + day.strftime("%d.%m.%Y") if day.strftime("%A") in day_translation else day.strftime("%A").decode("utf-8") + " " + day.strftime("%d.%m.%Y")
		addDir(den, cid+'|'+day.strftime("%s"), 4, None, 1)

def ARCHIVVIDEOS(url):
	cid,day = url.split("|")
	o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
	o2tv.getArchivChannelPrograms(cid,day)

def LIVE():
	o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
	channels = o2tv.live_channels()
	channels_sorted = sorted(channels.values(), key=lambda _channel: _channel.number)
	for channel in channels_sorted:
		if addon.getSetting('showliveepg')=='true':
			epg=o2tv.getChannelPrograms(channel.channel_key)
			addDir(_to_string(channel.name)+' [COLOR yellow]'+epg["title"]+'[/COLOR]',channel.channel_key+"|||",8,channel.logo_url,1, infoLabels={'plot':epg["desc"]})
		else:
			addDir(_to_string(channel.name),channel.channel_key+"|||",8,channel.logo_url,1)
	with open(profile + '/epg.dat', 'w') as file:
		json.dump(epgcache, file)

def PLAYLIST():
	playlistFHD = "#NAME Orange TV FHD\n"
	playlist = "#NAME Orange TV\n"
	count = 0
	o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
	channels = o2tv.live_channels()
	channels_sorted = sorted(channels.values(), key=lambda _channel: _channel.number)
	if not o2tv.access_token:
		o2tv.refresh_access_token()
	if not o2tv.subscription_code:
		o2tv.refresh_configuration()
	for channel in channels_sorted:
		print(channel.channel_key)
		params = {"serviceType": "LIVE_TV", "subscriptionCode": o2tv.subscription_code,	"channelKey": channel.channel_key, "deviceType": _quality }
		headers = _COMMON_HEADERS
		cookies = {"access_token": o2tv.access_token, "deviceId": _deviceid}
		req = requests.get('http://app01.gtm.orange.sk/sws/server/streaming/uris.json', params=params, headers=headers, cookies=cookies)
		uris = req.json()
		try:
			result = []
			r = requests.get(uris['uris'][0]['uri'], headers=_COMMON_HEADERS).text
			for m in re.finditer('#EXT-X-STREAM-INF:PROGRAM-ID=\d+,BANDWIDTH=(?P<bandwidth>\d+),AUDIO="\d+"\s(?P<chunklist>[^\s]+)', r, re.DOTALL):
				bandwidth = int(m.group('bandwidth'))
				quality = ""
				if bandwidth < 2000000:
					quality = "480p"
				elif bandwidth < 3000000:
					quality = "576p"
				elif bandwidth < 6000000:
					quality = "720p"
				else:
					quality = "1080p"
				url = m.group('chunklist')
				if quality == "1080p":
					playlistFHD += "#SERVICE 4097:0:1:"+str(count)+":0:0:0:0:0:0:"+url.replace(":","%3a")+": "+_to_string(channel.name)+"\n#DESCRIPTION "+_to_string(channel.name)+"\n"
					continue
				result.append({"url":url,"title":'['+quality+'] '+name})
			for one in reversed(result):
				playlist += "#SERVICE 4097:0:1:"+str(count)+":0:0:0:0:0:0:"+one['url'].replace(":","%3a")+": "+_to_string(channel.name)+"\n#DESCRIPTION "+_to_string(channel.name)+"\n"
				break
			count=count+1
		except:
			pass
	f = open(os.path.join(config.plugins.archivCZSK.logPath.getValue(),'orangetvFHD.pls'), 'w')
	f.write(playlistFHD)
	f.close()
	f = open(os.path.join(config.plugins.archivCZSK.logPath.getValue(),'orangetv.pls'), 'w')
	f.write(playlist)
	f.close()

def VIDEOLINK(name, url):
	channel_key,pid,fts,tts = url.split("|")
	o2tv = O2TVGO(_deviceid, otvusr, otvpwd, _quality, None)
	if not o2tv.access_token:
		o2tv.refresh_access_token()
	access_token = o2tv.access_token
	if not o2tv.subscription_code:
		o2tv.refresh_configuration()
	subscription_code = o2tv.subscription_code
	playlist = None
	while access_token:
		if pid:
			params = {"serviceType": "TIMESHIFT_TV",
				"contentId": pid,
				"subscriptionCode": subscription_code,
				"channelKey": channel_key,
				"deviceType": _quality,
				"fromTimestamp": fts,
				"toTimestamp": tts
			}
		else:
			params = {"serviceType": "LIVE_TV",
				"subscriptionCode": subscription_code,
				"channelKey": channel_key,
				"deviceType": _quality
			}
		headers = _COMMON_HEADERS
		cookies = {"access_token": access_token, "deviceId": _deviceid}
		req = requests.get('http://app01.gtm.orange.sk/sws/server/streaming/uris.json', params=params, headers=headers, cookies=cookies)
		json_data = req.json()
		access_token = None
		if 'statusMessage' in json_data:
			status = json_data['statusMessage']
			if status == 'bad-credentials':
				access_token = o2tv.refresh_access_token()
			else:
				client.showInfo("Err: "+status)
		else:
			playlist = ""
			for uris in json_data["uris"]:
				if o2tv.quality == "STB" or o2tv.quality == "PC":
					if uris["resolution"] == "HD" and playlist == "":
						playlist = uris["uri"]
				else:
					if uris["resolution"] == "SD" and playlist == "":
						playlist = uris["uri"]
			if playlist == "":
				playlist = json_data["uris"][0]["uri"]
	result = []
	r = requests.get(playlist, headers=_COMMON_HEADERS).text
	for m in re.finditer('#EXT-X-STREAM-INF:PROGRAM-ID=\d+,BANDWIDTH=(?P<bandwidth>\d+),AUDIO="\d+"\s(?P<chunklist>[^\s]+)', r, re.DOTALL):
		bandwidth = int(m.group('bandwidth'))
		quality = ""
		if bandwidth < 2000000:
			quality = "480p"
		elif bandwidth < 3000000:
			quality = "576p"
		elif bandwidth < 6000000:
			quality = "720p"
		else:
			quality = "1080p"
		url = m.group('chunklist')
		result.append({"url":url,"title":'['+quality+'] '+name})
	for one in reversed(result):
		add_video(one["title"], one["url"])

name=None
url=None
mode=None
thumb=None
page=None
desc=None

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

if _deviceid == "":
	_deviceid = device_id()
	if _deviceid == "":
	    _deviceid = 'Nexus7'
	addon.setSetting('deviceid',_deviceid)

day_translation = {"Monday": "Pondelok", "Tuesday": "Utorok", "Wednesday": "Streda", "Thursday": "Štvrtok", "Friday": "Piatok", "Saturday": "Sobota", "Sunday": "Nedeľa"}
day_translation_short = {"Monday": "Po", "Tuesday": "Ut", "Wednesday": "St", "Thursday": "Št", "Friday": "Pi", "Saturday": "So", "Sunday": "Ne"}

if otvusr == "" or otvpwd == "":
	client.add_operation("SHOW_MSG", {'msg': 'Prosim, vlozte nejdrive prihlasovaci udaje', 'msgType': 'error', 'msgTimeout': 30, 'canClose': True})
elif url=='deldev' and name!='':
	DEVICEREMOVE(name)
elif mode==None or url==None or len(url)<1:
	OBSAH()
elif mode==1:
	LIVE()
elif mode==2:
	ARCHIV()
elif mode==3:
	ARCHIVDAYS(url)
elif mode==4:
	ARCHIVVIDEOS(url)
elif mode==5:
	PLAYLIST()
elif mode==9:
	DEVICES()
elif mode==8:
	VIDEOLINK(name, url)
