# -*- coding: utf-8 -*-
import sys
import requests
import urllib
import urlparse
from xml.etree import ElementTree as ET
import hashlib
from string import ascii_uppercase
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.tools.util import unescapeHTML
from Plugins.Extensions.archivCZSK.engine.client import add_dir, add_video
from Plugins.Extensions.archivCZSK.engine import client
from Components.config import config
import re, datetime, util, json, search
from md5crypt import md5crypt

addon =  ArchivCZSK.get_xbmc_addon('plugin.video.sc2')
home = addon.getAddonInfo('path')
icon = os.path.join(home, 'icon.png')
hotshot_url = 'https://plugin.sc2.zone'
ws_api = 'https://webshare.cz/api'
UA = "KODI/18.6 (Windows; U; Windows NT; en) ver1.3.26"
realm = ':Webshare:'
base_url = ""
LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'sc2.log')
CACHE_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'sc2.')

def writeLog(msg, type='INFO'):
    try:
        f = open(LOG_FILE, 'a')
        dtn = datetime.datetime.now()
        f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
        f.close()
    except:
        pass

def set_cache(key, value):
    try:
        with open(CACHE_FILE+key, 'w') as outfile:
            json.dump(value, outfile)
    except:
        pass

def get_cache(key):
    try:
        with open(CACHE_FILE+key) as json_file:
            return json.load(json_file)
    except:
        return None

def ws_api_request(url, data):
	return requests.post(ws_api + url, data=data)

def login():
	username = addon.getSetting('wsuser')
	password = addon.getSetting('wspass')
	if username == '' or password == '':
		client.add_operation("SHOW_MSG", {'msg': 'Vyplňte prosím přihlašovací údaje v nastavení', 'msgType': 'error', 'msgTimeout': 20, 'canClose': True })
		return
	req = ws_api_request('/salt/', { 'username_or_email': username })
	salt = ET.fromstring(req.text).find('salt').text
	pass_digest = get_pass_digest(username, realm, password, salt)
	req = ws_api_request('/login/', { 'username_or_email': username, 'password': pass_digest['password'], 'digest': pass_digest['digest'], 'keep_logged_in': 1 })
	token = ET.fromstring(req.text).find('token').text
	addon.setSetting('token', token)
	return token

def get_stream_url(ident):
	token = addon.getSetting('token')
	if len(token) == 0:
		token = login()
	if token:
		req = ws_api_request('/file_link/', { 'wst': token, 'ident': ident })
		try:
			link = ET.fromstring(req.text).find('link').text
			return link
		except:
			return None

def get_pass_digest(username, realm, password, salt):
	encrypted_pass = hashlib.sha1(md5crypt(password.encode('utf-8'), salt.encode('utf-8'))).hexdigest()
	return { 'password': encrypted_pass, 'digest': hashlib.md5(username.encode('utf-8') + realm + encrypted_pass.encode('utf-8')).hexdigest() }

def api_request(url):
	url = hotshot_url + url
	try:
		return requests.get(url=url).json()
	except Exception as e:
		pass
	return 

def get_media_data(url):
	data = api_request(url)
	set_cache('media', data)
	return data

def get_media_from_cache(mediaId):
	mediaList = get_cache('media')
	for media in mediaList['data']:
		if media['id'] == mediaId:
			return media

def addDir(name, url, mode, image, page=None, kanal=None, infoLabels={}, menuItems={}):
    params = {'name':name, 'url':url, 'mode':mode, 'page':page, 'kanal':kanal}
    add_dir(name, params, image, infoLabels=infoLabels, menuItems=menuItems)

def render_item(d, folder = True):
	addDir(d['name'], d['url'], 1, None)

def build_item(name, action, action_value = ''):
	return { 
		'name': add_translations(name),
		'url': build_plugin_url({ 'action': action, 'action_value': action_value })
	}

def build_plugin_url(query):
    return base_url + '?' + urllib.urlencode(query)

def add_translations(s):
	regex = re.compile(r'\$(\d+)', re.S)
	return regex.sub(lambda m: m.group().replace(m.group(),addon.getLocalizedString(int(m.group()[1:])),1), s)

def page_info(page, pageCount):
	return ' ('+ page + '/' + pageCount +') '

def stream_title(stream):
	vinfo=stream['vinfo'] if 'vinfo' in stream else ''
	sbitrate=' ['+stream['sbitrate']+']' if 'sbitrate' in stream else ''
	return "[B][" + stream['lang'] + '] ' + stream['quality'] + vinfo + '[/B] - ' + stream['size'] + stream['ainfo'] + sbitrate

def add_paging(page, pageCount, nextUrl):
	render_item(build_item(addon.getLocalizedString(30203) + page_info(str(page), pageCount), action[0], nextUrl))

def process_seasons(mediaList):
	for i, media in enumerate(mediaList):
		render_item(build_item(media['title'], 'episodes', i), folder = True)

def process_series(mediaList):
	for media in mediaList:
		render_item(build_item(media['title'], 'seasons', '/api/media/series/' + media['id']), folder = True)

def process_episodes(mediaList):
	for i, media in enumerate(mediaList):
		addDir(media['title'], build_plugin_url({ 'action': 'series.streams', 'action_value': action_value[0] + ' ' + str(i)}), 1, media['poster'] if 'poster' in media else None, None, None, { 'plot': media['plot'] if 'plot' in media else '', 'rating': media['rating'] if 'rating' in media else 0, 'duration': media['duration'] if 'duration' in media else 0})
#		render_item(build_item(media['title'], 'series.streams', action_value[0] + ' ' + str(i)), folder = False)

def process_movies(mediaList):
	for media in mediaList:
		addDir(media['title'], build_plugin_url({ 'action': 'movies.streams', 'action_value': media['id'] }), 1, media['poster'] if 'poster' in media else None, None, None, { 'plot': media['plot'] if 'plot' in media else '', 'rating': media['rating'] if 'rating' in media else 0, 'duration': media['duration'] if 'duration' in media else 0})
#		render_item(build_item(media['title'], 'movies.streams', media['id'], media), folder = False)

def show_stream_dialog(streams):
	for stream in streams:
		add_video(stream_title(stream),get_stream_url(stream['ident']),None,None)

menu = {
	'root': [
		build_item(addon.getLocalizedString(30200), 'folder','movies'),
		build_item(addon.getLocalizedString(30201), 'folder', 'series'),
	],
	'movies': [
		build_item(addon.getLocalizedString(30204), 'search', 'movies'),
		#build_item(addon.getLocalizedString(30211), 'folder','popular'),
		#build_item(addon.getLocalizedString(30212), 'folder','watching now'),
		#build_item(addon.getLocalizedString(30205), 'folder','genre'),
		build_item(addon.getLocalizedString(30206), 'folder','movies.a-z'),
	],
	'series': [
		build_item(addon.getLocalizedString(30204), 'search', 'series'),
		#build_item(addon.getLocalizedString(30211), 'folder','popular'),
		#build_item(addon.getLocalizedString(30212), 'folder','watching now'),
		#build_item(addon.getLocalizedString(30205), 'folder','genre'),
		build_item(addon.getLocalizedString(30206), 'folder','series.a-z'),
	],
	'series.a-z': [build_item('0-9', 'series', '/api/media/series/filter/startsWithL/0-9')] + [build_item(c, 'series', '/api/media/series/filter/startsWithL/' + c) for c in ascii_uppercase],
	'movies.a-z': [build_item('0-9', 'movies', '/api/media/movies/filter/startsWithL/0-9')] + [build_item(c, 'movies', '/api/media/movies/filter/startsWithL/' + c) for c in ascii_uppercase]
}

name=None
url=None
action=None
action_value=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        action=urlparse.parse_qs(urlparse.urlparse(url).query)['action']
except:
        pass
try:
        action_value=urlparse.parse_qs(urlparse.urlparse(url).query)['action_value']
except:
        pass

#writeLog('URL: '+str(url))
#writeLog('NAME: '+str(name))
#writeLog('ACT: '+str(action))
#writeLog('ACTVAL: '+str(action_value))

if action is None:
	for c in menu['root']:
		render_item(c)
elif action[0] == 'folder':
	for c in menu[action_value[0]]:
		render_item(c)
elif action[0] == 'movies':
	data = get_media_data(action_value[0])
	process_movies(data['data'])
	if 'next' in data:
		add_paging(data['page'], data['pageCount'], data['next'])
	render_item(build_item(addon.getLocalizedString(30202), ''))
elif action[0] == 'series':
	data = get_media_data(action_value[0])
	process_series(data['data'])
	if 'next' in data:
		add_paging(data['page'], data['pageCount'], data['next'])
	render_item(build_item(addon.getLocalizedString(30202), ''))
elif action[0] == 'series.streams':
	media = get_cache('media')
	s_e = action_value[0].split()
	show_stream_dialog(media['seasons'][int(s_e[0])]['episodes'][int(s_e[1])]['strms'])
elif action[0] == 'movies.streams':
	media = get_media_from_cache(action_value[0])
	show_stream_dialog(media['streams'])
elif action[0] == 'search':
	searchValue = client.getTextInput(session, addon.getLocalizedString(30207))
	if searchValue is not "":
		url = '/api/media/' + action_value[0] + '/filter/titleOrActor/' + searchValue
		if action_value[0] == 'movies':
			media = get_media_data(url)
			process_movies(media['data'])
		if action_value[0] == 'series':
			media = api_request(url)
			process_series(media['data'])
		if 'next' in media:
			add_paging(media['page'], media['pageCount'], media['next'])
elif action[0] == 'episodes':
	media = get_cache('media')
	process_episodes(media['seasons'][int(action_value[0])]['episodes'])
elif action[0] == 'seasons':
	media = get_media_data(action_value[0])
	process_seasons(media['seasons'])
