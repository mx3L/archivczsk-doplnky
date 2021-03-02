# -*- coding: utf-8 -*-
# /*
# *  Copyright (C) 2021 Michal Novotny https://github.com/misanov
# *  based od Kodi plugin https://github.com/sterd71/plugin.video.eurosporton
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

sys.path.append(os.path.dirname(__file__))

import sys, os, string, random, time, json, uuid, requests, re
from urllib import urlencode, quote, unquote_plus
from datetime import datetime
from dateutil.parser import parse as parse_date
from dateutil import tz
try:
	from urlparse import urlparse, parse_qs
except ImportError:
	from urllib.parse import urlparse, parse_qs

from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.client import add_dir, add_video
from Plugins.Extensions.archivCZSK.engine import client
from Components.config import config


############### Eurosport ###########

def addDir(name, url, mode, image, page=None, kanal=None, infoLabels={}, menuItems={}):
	params = {'name':name, 'url':url, 'mode':mode, 'page':page, 'kanal':kanal}
	add_dir(name, params, image, infoLabels=infoLabels, menuItems=menuItems)

def sport_sort_key(sport):
	attrs = sport['attributes']
	return attrs.get('name')

def name_sort_key(schedule):
	attrs = schedule['attributes']
	return attrs.get('name')

def date_sort_key(options):
	return options.get('value')

def schedule_start_key(video):
	attrs = video['attributes']
	return attrs.get('scheduleStart')

def publish_start_key(video):
	attrs = video['attributes']
	return attrs.get('publishStart')
	
def publish_end_key(video):
	attrs = video['attributes']
	return attrs.get('publishEnd')

def build_list(type, video, listing, response):

	engine = addon.getSetting('engine')
	streamType = addon.getSetting('streamType')

#	try:
	attrs = video['attributes']
	alternateTitle = attrs.get('alternateId')

	if type == 'sport':
		# Pull start time from availability window
		availability = video.get('attributes', {}).get('availabilityWindows', [])
		if len(availability) > 0:
			av_window = availability[0]
			av_start = parse_date(av_window['playableStart'])
			av_start_local = av_start.astimezone(tz.tzlocal())
			av_startstr = av_start_local.strftime("%d.%m.%Y %H:%M")
		title = av_startstr + ' - ' + attrs.get('name')
	elif type == 'daily':
		# Pull start time from schedule start
		av_start = parse_date(attrs['scheduleStart'])
		av_start_local = av_start.astimezone(tz.tzlocal())
		av_startstr = av_start_local.strftime("%d.%m.%Y %H:%M")
		title = av_startstr + ' - ' + attrs.get('name')
	else:
		# Set the base title
		title = attrs.get('name')

	# Add chanel details for on-air shows
	if type == 'daily':
		if attrs.get('materialType') == 'LINEAR':
			channel = attrs.get('path')
			if 'eurosport-1' in channel:
				title = title + ' - (E1)'
			if 'eurosport-2' in channel:
				title = title + ' - (E2)'
		if attrs.get('broadcastType') == 'LIVE':
			title = title + ' (Live)'

	# Get image and it's url
	images = video.get('relationships', {}).get('images', {}).get('data', [])
	image_url = ''
	if len(images) > 0:
		image_url = response.get_image_url(images[0]['id'])

	# Set the premiered date
	if type == 'daily':
		premiered = str(attrs.get('scheduleStart')[:10])
		timestamp = attrs.get('scheduleStart')
	
	if type == 'sport':
		premiered = str(attrs.get('publishStart')[:10])
		timestamp = attrs.get('publishStart')
	
	# Get the plot
	plot = attrs.get('description')
	if plot == '' or plot is None:
		plot = attrs.get('secondaryTitle')

	# Set the metadata
	if type == 'ondemand':
		labels = {
			'title': title
		}
	else:	
		labels = {
			'title': title,
			'plot': plot
		}

	if type == 'ondemand':
		isPlayable = 'false'
	else:	
		now = datetime.now(tz.tzutc())
		if av_start_local > now:
			isPlayable = 'false'
		else:
			isPlayable = 'true'

	# Ondemand brings up a list of items to select, not play
	if type == 'ondemand':
		url = '{0}?action=select-sport&sport={1}'.format('', alternateTitle)   
		isfolder = True
	else:	
		id = video.get('id')
		url = '{0}?action=play&id={1}'.format('', id)
		isfolder = False

	if isfolder:
		add_dir(title, {'url': url}, image_url, infoLabels=labels)
	else:
		add_dir(title, {'url': url}, image_url, infoLabels=labels)
#	except:
#		pass

"""
	Return list of available videos for this sport
"""	
def sport_list(eurosport,sport):
	sport = eurosport.sport(sport)
	videos = sport.videos()
	listing = []

	if sortOrder == "Ending soon":
		for video in sorted(videos, key=publish_end_key):
			build_list('sport', video, listing, sport)
	elif sortOrder == 'Earliest first':
		for video in sorted(videos, key=publish_start_key):
			build_list('sport', video, listing, sport)
	else:		
		for video in sorted(videos, key=publish_start_key, reverse=True):
			build_list('sport', video, listing, sport)

"""
	Return list of available videos for this day
"""	
def daily_list(eurosport,collid,day):
	dailyList = eurosport.dailyList(collid,day)
	videos = dailyList.videos()
	listing = []

	for video in sorted(videos, key=schedule_start_key):
		build_list('daily', video, listing, dailyList)

"""
	Return list of on demand sports
"""	
def ondemand_list(eurosport):
	ondemand = eurosport.ondemand()
	sports = ondemand.sports()
	listing = []
	for sport in sorted(sports, key=sport_sort_key):
		build_list('ondemand', sport,  listing, ondemand)

"""
	Return list of on available dates
"""	
def onschedule_list(eurosport):
	onschedule = eurosport.onschedule()
	scheduleCollection = onschedule.scheduleCollection()
	listing = []
	for schedule in scheduleCollection:		
		try:		
			collectionId = schedule.get('id')
			attrs = schedule['attributes']
			component = attrs.get('component')
			filters = component.get('filters')
			for scheduleFilter in filters:
				 options = scheduleFilter.get('options')
				 for option in options:
					scheduleStr = option.get('value')
					scheduleDate = datetime.strptime(scheduleStr, '%Y-%m-%d')   
					format = '%d %B'
					title = scheduleDate.strftime(format)  
					parameter = option.get('parameter')
					url = '{0}?action=select-date&collid={1}&day={2}'.format('', collectionId, parameter)   
					add_dir(title, { 'url': url }, None)
		except:	
			pass

"""
  Eurosport object checks session token
  and returns the list of items available to watch now, or scheduled for later
"""
class Eurosport(object):
	def __init__(self, token):
		self.token = token
		self.session = requests.Session()
		self.session.headers = {
			'cookie': 'st={}'.format(token),
			'X-disco-client': 'WEB:UNKNOWN:esplayer:prod',
			'X-disco-params': 'realm=eurosport,,'  
		}

	def onschedule(self):
		res = self.session.get('{}/cms/routes/schedule?include=default'.format(ROOT_URL)).json()
		return OnscheduleResponse(res)

	def dailyList(self, collid, day):
		res = self.session.get('{0}/cms/collections/{1}?include=default&{2}'.format(ROOT_URL,collid,day)).json()
		return DailyResponse(res)

	def ondemand(self):
		res = self.session.get('{}/cms/routes/on-demand?include=default'.format(ROOT_URL)).json()
		return OndemandResponse(res)

	def sport(self, sport):
		res = self.session.get('{0}/cms/routes/sport/{1}?include=default'.format(ROOT_URL,sport)).json()
		return SportResponse(res)

	def playback_info(self, video_id):
		res = self.session.get('{}/playback/v2/videoPlaybackInfo/{}?usePreAuth=true'.format(ROOT_URL,video_id)).json()
		return res

"""
	OnscheduleResponse sends back an object containing an id and an array of dates inthe current schedule
"""
class OnscheduleResponse(object):
	def __init__(self, data):
		self._data = data

	def scheduleCollection(self, onlyAvailable=True):

		def filterMethod(o):
			if o.get('type') != 'collection':
				return False
			if not onlyAvailable:
				return True
			return True	

		return filter(
			filterMethod,
			self._data.get('included', [])
		)

	def images(self):
		return filter(
			lambda o: o.get('type') == 'image',
			self._data.get('included', [])
		)

	def get_image_url(self, id):
		wanted_images = list(
			filter(
				lambda i: i['id'] == id,
				self.images()
			)
		)
		if len(wanted_images) > 0:
			return wanted_images[0]['attributes'].get('src')
		return None

"""
	OndemandResponse sends back a list of sports that have videos available
"""
class OndemandResponse(object):
	def __init__(self, data):
		self._data = data

	def sports(self, onlyAvailable=True):

		def filterMethod(o):

			if o.get('type') != 'taxonomyNode':
				return False
			if not onlyAvailable:
				return True
				
			return True	

		return filter(
			filterMethod,
			self._data.get('included', [])
		)

	def images(self):
		return filter(
			lambda o: o.get('type') == 'image',
			self._data.get('included', [])
		)

	def get_image_url(self, id):
		wanted_images = list(
			filter(
				lambda i: i['id'] == id,
				self.images()
			)
		)
		if len(wanted_images) > 0:
			return wanted_images[0]['attributes'].get('src')
		return None

"""
	SportResponse sends back a list of on demand videos that have a start time before now and
	and end time after now
"""	
class SportResponse(object):
	def __init__(self, data):
		self._data = data

	def videos(self, onlyAvailable=True):

		def filterMethod(o):

			if o.get('type') != 'video':
				return False
			if not onlyAvailable:
				return True

			availability = o.get('attributes', {}).get('availabilityWindows', [])
			if len(availability) > 0:
				av_window = availability[0]
				av_start = parse_date(av_window['playableStart'])
				av_end = parse_date(av_window['playableEnd'])
				now = datetime.now(tz.tzutc())
				return av_start <= now <= av_end

			return False

		return filter(
			filterMethod,
			self._data.get('included', [])
		)

	def images(self):
		return filter(
			lambda o: o.get('type') == 'image',
			self._data.get('included', [])
		)

	def get_image_url(self, id):
		wanted_images = list(
			filter(
				lambda i: i['id'] == id,
				self.images()
			)
		)
		if len(wanted_images) > 0:
			return wanted_images[0]['attributes'].get('src')
		return None


"""
	DailyResponse sends back a list of videos that are showing on the selected day
"""	
class DailyResponse(object):
	def __init__(self, data):
		self._data = data

	def videos(self, onlyAvailable=True):

		def filterMethod(o):

			if o.get('type') != 'video':
				return False
			if not onlyAvailable:
				return True

			return True

		return filter(
			filterMethod,
			self._data.get('included', [])
		)

	def images(self):
		return filter(
			lambda o: o.get('type') == 'image',
			self._data.get('included', [])
		)

	def get_image_url(self, id):
		wanted_images = list(
			filter(
				lambda i: i['id'] == id,
				self.images()
			)
		)
		if len(wanted_images) > 0:
			return wanted_images[0]['attributes'].get('src')
		return None

"""
Play video located at the URL
"""
def play_video(id):
	streamType = addon.getSetting('streamType') or 'hls'
	playback_info = eurosport.playback_info(id)

	if streamType == 'hls':
		stream_url = playback_info.get(
			'data', {}
		).get(
			'attributes', {}
		).get(
			'streaming', {}
		).get(
			'hls', {}
		).get('url')

	if streamType == 'ism':
		stream_url = playback_info.get(
			'data', {}
		).get(
			'attributes', {}
		).get(
			'streaming', {}
		).get(
			'mss', {}
		).get('url')

	if not stream_url: return []

	spliturl = stream_url.split('index.m3u8')

	data = requests.get(stream_url).content

	audenurl = ''
	audczurl = ''
	# default eng lang
	audio = re.search('#EXT-X-MEDIA:TYPE=AUDIO,.*?,LANGUAGE="eng",.*?,URI="(.*?)"', data, re.S)
	if audio:
		audenurl = audio.group(1)
	# cze lang
	audio = re.search('#EXT-X-MEDIA:TYPE=AUDIO,.*?,LANGUAGE="cze",.*?,URI="(.*?)"', data, re.S)
	if audio:
		audczurl = audio.group(1)

	res = []
	for m in re.finditer('#EXT-X-STREAM-INF:.*?RESOLUTION=\d+x(?P<quality>\d+),.*?\s(?P<chunklist>[^\s]+)', data, re.DOTALL):
		if int(m.group('quality')) < 720: continue
		if audczurl != '':
			itm = {}
			itm['quality'] = m.group('quality') + 'p'
			itm['lang'] = ' CZ'
			itm['url'] = spliturl[0] + m.group('chunklist') + '&suburi=' + spliturl[0] + audczurl
			res.append(itm)
		if audenurl != '':
			itm = {}
			itm['quality'] = m.group('quality') + 'p'
			itm['lang'] = ' EN'
			itm['url'] = spliturl[0] + m.group('chunklist') + '&suburi=' + spliturl[0] + audenurl
			res.append(itm)
	res = sorted(res,key=lambda i:(len(i['quality']),i['quality']), reverse = True)
	for item in res:
		add_video(item['quality'] + item['lang'], item['url'], None, None)


############### init ################
addon = ArchivCZSK.get_xbmc_addon('plugin.video.eurosport')
addon_userdata_dir = addon.getAddonInfo('profile')
home = addon.getAddonInfo('path')
icon = os.path.join(home, 'icon.png')

LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'eurosport.log')

ROOT_URL = 'https://eu3-prod-direct.eurosportplayer.com'
sortOrder = addon.getSetting('ondemand-sort-order')

def writeLog(msg, type='INFO'):
	try:
		f = open(LOG_FILE, 'a')
		dtn = datetime.now()
		f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
		f.close()
	except:
		pass

def addDir(name, url, mode, image, page=None, kanal=None, infoLabels={}, menuItems={}):
	params = {'name':name, 'url':url, 'mode':mode, 'page':page, 'kanal':kanal}
	add_dir(name, params, image, infoLabels=infoLabels, menuItems=menuItems)

def menu():
#	add_dir('Vyhledat', { 'url': '/search/'}, None)
	add_dir(addon.getLocalizedString(30030), { 'url': '?action=on-schedule'}, None)
	add_dir(addon.getLocalizedString(30031), { 'url': '?action=on-demand' }, None)

def router(params):
	if params:
		if params['action'][0] == "on-schedule":
			onschedule_list(eurosport)
		if params['action'][0] == 'select-date':
			daily_list(eurosport, params['collid'][0],params['day'][0])
		if params['action'][0] == 'on-demand':
			ondemand_list(eurosport)
		if params['action'][0] == 'select-sport':
			sport_list(eurosport, params['sport'][0])
		if params['action'][0] == 'play':
			play_video(params['id'][0])
	else:
		menu()

token = addon.getSetting('eurosporttoken')
if token:
	eurosport = Eurosport(token)

	url=params['url'][1:] if 'url' in params else urlencode(params)
	parsed_url = urlparse(params['url'] if 'url' in params else urlencode(params))
	params = parse_qs(parsed_url.query)
	page = int(params['page'][0]) if 'page' in params else 0
	adr = url.split('/')

	router(params)

	if len(client.GItem_lst[0]) == 0: addDir(None,'',1,None)
else:
	client.showInfo('Pro přehrávání pořadů je potřeba účet na eurosportplayer.com\n\nPokud účet máte, musíte vložit dlouhý token z webu.\n\nPřečtěte si prosím Změny nebo soubor readme.md v adresáři doplňku jak na to.', timeout=20)
