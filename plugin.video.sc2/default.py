# -*- coding: utf-8 -*-
#
# misanov version of SC2 for Enigma2 plugin archivczsk
#
import sys
import requests
import urllib
import urlparse
from xml.etree import ElementTree as ET
import hashlib
from string import ascii_uppercase, ascii_lowercase, digits
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.tools.util import unescapeHTML
from Plugins.Extensions.archivCZSK.engine.client import add_dir, add_video
from Plugins.Extensions.archivCZSK.engine import client
from Components.config import config
import re, datetime, util, json, search, math, uuid
from md5crypt import md5crypt

addon = ArchivCZSK.get_xbmc_addon('plugin.video.sc2')
home = addon.getAddonInfo('path')
icon = os.path.join(home, 'icon.png')
hotshot_url = 'https://beta.plugin.sc2.zone'
ws_api = 'https://webshare.cz/api'
UA = "KODI/18.6 (Windows; U; Windows NT; en) ver1.3.26"
UA2 = 'Kodi/18.6 (Windows NT 10.0.18363; Win64; x64) App_Bitness/64 Version/18.6-Git:20200229-8e967df921'
realm = ':Webshare:'
base_url = ""
LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'sc2.log')
CACHE_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'sc2.')
langFilter = addon.getSetting('item_filter_lang')

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
	if not username and not password:
		return ""
	elif username and password and len(username)>0 and len(password)>0:
		req = ws_api_request('/salt/', { 'username_or_email': username })
		xml = ET.fromstring(req.text)
		if not xml.find('status').text == 'OK':
			return ""
		salt = xml.find('salt').text
		if salt is None:
			salt = ''
		encrypted_pass = hashlib.sha1(md5crypt(password.encode('utf-8'), salt.encode('utf-8'))).hexdigest()
		digest = hashlib.md5(username.encode('utf-8') + realm + encrypted_pass.encode('utf-8')).hexdigest()
		req = ws_api_request('/login/', { 'username_or_email': username, 'password': encrypted_pass, 'digest': digest, 'keep_logged_in': 1 })
		xml = ET.fromstring(req.text)
		if not xml.find('status').text == 'OK':
			return ""
		token = xml.find('token').text
		req = ws_api_request('/user_data/', {'wst': token})
		xml = ET.fromstring(req.text)
		if xml.find('vip_days').text:
			addon.setSetting('wsvipdays', xml.find('vip_days').text)
#			client.add_operation("SHOW_MSG", {'msg': 'Mate jeste %s VIP dnu'%xml.find('vip_days').text, 'msgType': 'info', 'msgTimeout': 2, 'canClose': True })
		return token
	return ""

def get_stream_url(ident):
	token = login()
	if token == "":
		client.add_operation("SHOW_MSG", {'msg': 'Nelze se prihlasit na WS, pokracuji s uctem zdarma...', 'msgType': 'error', 'msgTimeout': 1, 'canClose': True })
	req = ws_api_request('/file_link/', { 'wst': token, 'ident': ident })
	xml = ET.fromstring(req.text)
	if not xml.find('status').text == 'OK':
		client.add_operation("SHOW_MSG", {'msg': 'Nelze ziskat odkaz na video', 'msgType': 'error', 'msgTimeout': 20, 'canClose': True })
		return None
	return xml.find('link').text

def api_request(url,post_data=''):
	url = hotshot_url + url
#	tout = addon.getSetting('loading_timeout')
#	if not tout: tout = 15
	try:
		data = requests.post(url=url, data=post_data, headers={'User-Agent': UA2, 'X-Uuid': xuuid, 'Content-Type': 'application/json'}, timeout=15)
		if data.status_code != 200:
			client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat ze serveru', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
			return {'data': "" }
		else:
			return json.loads(data.content)
#			return data.json()
	except Exception as e:
		client.add_operation("SHOW_MSG", {'msg': 'Nepodařilo se stáhnout data ze serveru v časovém limitu', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
		pass
	return {'data': "" }

def get_media_data(url,post_data=''):
	data = api_request(url,post_data)
#	set_cache('media', data)
	return data

def get_media_from_cache(mediaId):
	mediaList = get_cache('media')
	for media in mediaList['data']:
		if media['_id'] == mediaId:
			return media['_source']

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
	if not s: return s
	regex = re.compile(r'\$(\d+)', re.S)
	return regex.sub(lambda m: m.group().replace(m.group(),addon.getLocalizedString(int(m.group()[1:])),1), s)

def convert_size(size_bytes):
	if size_bytes == 0 or size_bytes is None:
		return "0 B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1024)))
	p = math.pow(1024, i)
	s = round(size_bytes / p, 2)
	return "%s %s" % (s, size_name[i])

def convert_bitrate(mbit):
	if mbit == 0 or mbit is None:
		return "0 Mbit/s"
	p = math.pow(1024, 2)
	s = round(mbit / p, 2)
	return "%s %s" % (s, "Mbit/s")

def stream_title(title,stream):
	lang = []
	if 'audio' in stream:
		for temp in stream['audio']:
			if 'language' in temp: lang.append(temp['language'])
	if lang:
		langset = set(lang)
		lang = list(langset)
		lang.sort()
	return title + " - " + ', '.join(lang) + ' (' + stream['quality'] + ', ' + convert_size(stream['size']) + ', ' + stream['codec'] + ', '+ convert_bitrate(stream['bitrate']) + ')'

def get_langs(media):
	lang = []
	if 'streams' in media:
		for stream in media['streams']:
			if 'audio' in stream:
				for temp in stream['audio']:
					if 'language' in temp: lang.append(temp['language'])
	if lang:
		langset = set(lang)
		lang = list(langset)
		lang.sort()
		return ', '.join(lang)
	return ''

def get_info(media,st=False):
	year = media['info_labels']['year'] if 'info_labels' in media and 'year' in media['info_labels'] else 0
	if year == 0 and 'aired' in media['info_labels'] and media['info_labels']['aired']: year = media['info_labels']['aired'][0:4]
	title = media['info_labels']['title'] if 'info_labels' in media and 'title' in media['info_labels'] else ""
	title = ' ' + media['info_labels']['originaltitle'] + get_langs(media) if 'info_labels' in media and 'originaltitle' in media['info_labels'] and title == "" else title
	langs = get_langs(media)
	if not st: title += ' - ' + langs + ' (' + str(year) + ')'
	genres = ""
	if 'info_labels' in media and 'genre' in media['info_labels']:
		genreL = []
		for genre in media['info_labels']['genre']:
			if genre in api_genres_langs: genreL.append(api_genres_langs[genre])
			genres = ', '.join(genreL)
	plot = '[' + genres + '] ' if genres else ""
	plot += media['info_labels']['plot'] if 'info_labels' in media and 'plot' in media['info_labels'] else ""
	rating = media['info_labels']['rating'] if 'info_labels' in media and 'rating' in media['info_labels'] else 0
	duration = media['info_labels']['duration'] if 'info_labels' in media and 'duration' in media['info_labels'] else 0
	if duration == 0 and 'streams' in media and len(media['streams'])>0 and 'duration' in media['streams'][0]: duration = media['streams'][0]['duration']
	poster = media['art']['poster'] if 'art' in media and 'poster' in media['art'] and media['art']['poster'] != "" else None
	return {'title': title, 'plot': plot, 'rating': rating, 'duration': duration, 'poster': poster, 'year': year, 'genres': genres, 'langs': langs}

def add_paging(page, pageCount):
	if page <= pageCount:
		addDir(add_translations(addon.getLocalizedString(30203) + ' ('+ str(page) + '/' + str(pageCount) +') '), build_plugin_url({ 'action': action[0], 'action_value': action_value[0], 'page': page }), 1, None)

def isExplicit(media):
	if addon.getSetting('explicit_content') == 'false':
		if 'info_labels' in media and 'genre' in media['info_labels']: return bool(set(media['info_labels']['genre']).intersection(explicit_genres))
	return False

def isFilterLangStream(stream):
	# 0 all, 1-CZ&SK, 2-CZ 3-SK, 4-EN
	if langFilter != 0:
		lang = []
		if 'audio' in stream:
			for temp in stream['audio']:
				if 'language' in temp: lang.append(temp['language'].lower())
			if len(lang)>0 and langFilter is 1 and 'cz' in lang or 'sk' in lang: return False
			if len(lang)>0 and langFilter is 2 and 'cz' in lang: return False
			if len(lang)>0 and langFilter is 3 and 'sk' in lang: return False
			if len(lang)>0 and langFilter is 4 and 'en' in lang: return False
	return True

def isFilterLang(media):
	if langFilter != 0:
		if 'streams' in media:
			for stream in media['streams']:
				return isFilterLangStream(stream)
	return True

def process_episodes(mediaList):
	(sid, ss) = action_value[0].split(',')
	for i, media in enumerate(mediaList):
		info = get_info(media)
		title = str(int(ss)+1).zfill(2)+'x'+str(int(media['info_labels']['episode'])).zfill(2)+' ' if ss and 'episode' in media['info_labels'] else ''
		title += info['title'].replace('${30921}',addon.getLocalizedString(30921))
		addDir(title, build_plugin_url({ 'action': 'series.streams', 'action_value': sid + ',' + ss + ',' + str(i) }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year']})

def process_seasons(mediaList):
	for i, media in enumerate(mediaList):
		year = media['info_labels']['year'] if 'info_labels' in media and 'year' in media['info_labels'] else 0
		if year == 0 and 'aired' in media['info_labels'] and media['info_labels']['aired']: year = media['info_labels']['aired'][0:4]
		poster = media['art']['poster'] if 'art' in media and 'poster' in media['art'] else None
		addDir(addon.getLocalizedString(30919) + ' ' + str(i+1).zfill(2) + ' (' + year + ')', build_plugin_url({ 'action': 'episodes', 'action_value': action_value[0] + ',' + str(i) }), 1, poster)

def process_series(mediaList):
	for media in mediaList:
		if isExplicit(media): continue
		if not isFilterLang(media['_source']): continue
		info = get_info(media['_source'])
		addDir(info['title'], build_plugin_url({ 'action': 'seasons', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year']})

def process_movies(mediaList):
	for media in mediaList:
		if isExplicit(media['_source']): continue
		if not isFilterLang(media['_source']): continue
		info = get_info(media['_source'])
		if info['langs']: # pokud nejsou langs, tak neni zadny stream, zbytecne zobrazovat
			addDir(info['title'], build_plugin_url({ 'action': 'movies.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year']})

def show_stream_dialog(media):
	if ',' in action_value[0]:
		(sid, ss, ep) = action_value[0].split(',')
	else:
		ss = ''
	info = get_info(media,st=True)
	for stream in media['streams']:
		if addon.getSetting('filter_hevc') == 'true' and stream['codec'] == 'h265': continue
		if not isFilterLangStream(stream): continue
		title = str(int(ss)+1).zfill(2)+'x'+str(int(ep)+1).zfill(2)+' ' if ss and ep else ''
		title += stream_title(info['title'],stream)
		title = title.replace('${30921}',addon.getLocalizedString(30921))
		duration = stream['duration'] if 'duration' in stream else 0
		addDir(title,build_plugin_url({ 'action': 'play', 'action_value': stream['ident'], 'name': title }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': duration, 'year': info['year']})

def play(ident,title):
	gurl = get_stream_url(ident)
	if gurl is not None:
		add_video(title,gurl,None,None)

api_genres_langs = {
 'Action': addon.getLocalizedString(30501),
 'Animated': addon.getLocalizedString(30502),
 'Adventure': addon.getLocalizedString(30503),
 'Biographical': addon.getLocalizedString(30504),
 'Catastrophic': addon.getLocalizedString(30505),
 'Comedy': addon.getLocalizedString(30506),
 'Competition': addon.getLocalizedString(30507),
 'Crime': addon.getLocalizedString(30508),
 'Documentary': addon.getLocalizedString(30509),
 'Fairytale': addon.getLocalizedString(30510),
 'Drama': addon.getLocalizedString(30511),
 'Family': addon.getLocalizedString(30512),
 'Fantasy': addon.getLocalizedString(30513),
 'Historical': addon.getLocalizedString(30514),
 'Horror': addon.getLocalizedString(30515),
 'IMAX': addon.getLocalizedString(30516),
 'Educational': addon.getLocalizedString(30517),
 'Music': addon.getLocalizedString(30518),
 'Journalistic': addon.getLocalizedString(30519),
 'Military': addon.getLocalizedString(30520),
 'Musical': addon.getLocalizedString(30521),
 'Mysterious': addon.getLocalizedString(30522),
 'Psychological': addon.getLocalizedString(30523),
 'Reality': addon.getLocalizedString(30524),
 'Romantic': addon.getLocalizedString(30525),
 'Sci-Fi': addon.getLocalizedString(30526),
 'Short': addon.getLocalizedString(30527),
 'Sports': addon.getLocalizedString(30528),
 'Stand-Up': addon.getLocalizedString(30529),
 'Talk-Show': addon.getLocalizedString(30530),
 'Telenovela': addon.getLocalizedString(30531),
 'Thriller': addon.getLocalizedString(30532),
 'Travel': addon.getLocalizedString(30533),
 'Western':addon.getLocalizedString(30534),
 'War':addon.getLocalizedString(30535)
}
explicit_genres_langs = {'Erotic': addon.getLocalizedString(30551), 'Pornographic': addon.getLocalizedString(30552)}
api_genres = list(api_genres_langs.keys())
explicit_genres = list(explicit_genres_langs.keys())
if addon.getSetting('explicit_content') == 'true': api_genres += explicit_genres
api_genres.sort()
# Python 3.x
#api_genres_langs_items = sorted(api_genres_langs.items(), key=lambda x: x[1])
# Python 2.x
api_genres_langs_items = sorted(api_genres_langs.iteritems(), key=lambda x: x[1])

xuuid = addon.getSetting('uuid')
if xuuid == "":
	xuuid = str(uuid.uuid4())
	addon.setSetting('uuid',xuuid)

limitMovies=100
limitSeries=14
page=1
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
	page=urlparse.parse_qs(urlparse.urlparse(url).query)['page'][0]
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

#writeLog('PAGE: '+str(page))
#writeLog('URL: '+str(url))
#writeLog('NAME: '+str(name))
#writeLog('ACT: '+str(action))
#writeLog('ACTVAL: '+str(action_value))

menu = {
	'root': [
		build_item(addon.getLocalizedString(30200), 'folder','movies'),
		build_item(addon.getLocalizedString(30201), 'folder', 'series')
	],
	'movies': [
		build_item(addon.getLocalizedString(30204), 'search', 'movies'),
		build_item(addon.getLocalizedString(30211), 'movies','popular'),
		build_item('Novinky', 'movies','aired'),
		build_item('Naposledy přidané', 'movies','dateadded'),
		build_item(addon.getLocalizedString(30206), 'folder','movies.a-z'),
		build_item(addon.getLocalizedString(30205), 'folder','movies.genre')
	],
	'series': [
		build_item(addon.getLocalizedString(30204), 'search', 'tvshows'),
		build_item(addon.getLocalizedString(30211), 'series','popular'),
		build_item('Novinky', 'series','aired'),
		build_item('Naposledy přidané', 'series','dateadded'),
		build_item(addon.getLocalizedString(30206), 'folder','series.a-z'),
		build_item(addon.getLocalizedString(30205), 'folder','series.genre')
	],
	'series.genre': [build_item(d, 'series', 'genre,'+c) for c,d in api_genres_langs_items],
	'movies.genre': [build_item(d, 'movies', 'genre,'+c) for c,d in api_genres_langs_items]
}

if action_value and 'movies.a-z' in action_value[0]:
	moviesCountAZ = get_media_data('/api/media/movies/count/filter/startsWith','{"filter_values": '+str([c for c in ascii_lowercase]+[c for c in digits]).replace('\'','"')+'}')
	if not 'c' in moviesCountAZ:
		client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat ze serveru', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
	else:
		moviesCountAZ['0-9'] = 0
		for c in digits:
			if c in moviesCountAZ: moviesCountAZ['0-9']+=moviesCountAZ[c]
		menu['movies.a-z']=[build_item('0-9 ('+str(moviesCountAZ['0-9'])+')', 'movies', '0-9')] + [build_item(c+' ('+str(moviesCountAZ[c.lower()])+')', 'folder', 'movies.a-z.'+c.lower()) for c in ascii_uppercase]

if action_value and 'series.a-z' in action_value[0]:
	seriesCountAZ = get_media_data('/api/media/tvshows/count/filter/startsWith','{"filter_values": '+str([c for c in ascii_lowercase]+[c for c in digits]).replace('\'','"')+'}')
	if not 'c' in seriesCountAZ:
		client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat ze serveru', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
	else:
		seriesCountAZ['0-9'] = 0
		for c in digits:
			if c in seriesCountAZ:  seriesCountAZ['0-9']+=seriesCountAZ[c]
		menu['series.a-z']=[build_item('0-9 ('+str(seriesCountAZ['0-9'])+')', 'series', '0-9')] + [build_item(c+' ('+str(seriesCountAZ[c.lower()])+')', 'folder', 'series.a-z.'+c.lower()) for c in ascii_uppercase]

if action_value and 'movies.a-z.' in action_value[0]:
	(mm,aa,cc) = action_value[0].split('.')
	moviesCountAZsec = get_media_data('/api/media/movies/count/filter/startsWith','{"filter_values": '+str([cc+c for c in ascii_lowercase]).replace('\'','"')+'}')
	menu['movies.a-z.'+cc]=[build_item('Zobrazit vše od '+cc.upper()+' ('+str(moviesCountAZ[cc.lower()])+')', 'movies', cc.lower())] + [build_item(cc.upper()+c+' ('+str(moviesCountAZsec[cc.lower()+c.lower()])+')', 'movies', (cc+c).lower()) for c in ascii_uppercase]
if action_value and 'series.a-z.' in action_value[0]:
	(mm,aa,cc) = action_value[0].split('.')
	seriesCountAZsec = get_media_data('/api/media/tvshows/count/filter/startsWith','{"filter_values": '+str([cc+c for c in ascii_lowercase]).replace('\'','"')+'}')
	menu['series.a-z.'+cc]=[build_item('Zobrazit vše od '+cc.upper()+' ('+str(seriesCountAZ[cc.lower()])+')', 'series', cc.lower())] + [build_item(cc.upper()+c+' ('+str(seriesCountAZsec[cc.lower()+c.lower()])+')', 'series', (cc+c).lower()) for c in ascii_uppercase]

if action is None:
	for c in menu['root']:
		render_item(c)
elif action[0] == 'folder':
	if action_value[0] in menu:
		for c in menu[action_value[0]]:
			render_item(c)
elif action[0] == 'movies' or action[0] == 'series':
	mos = 'movies' if action[0] == 'movies' else 'tvshows'
	limitRec = limitMovies if action[0] == 'movies' else limitSeries
	if action_value[0] == 'popular':
		data = get_media_data('/api/media/'+mos+'/popular/desc?limit=%s&page=%s'%(limitRec,page),'')
	elif action_value[0] == 'aired':
		data = get_media_data('/api/media/'+mos+'/sort/aired/desc?limit=%s&page=%s'%(limitRec,page),'')
	elif action_value[0] == 'dateadded':
		data = get_media_data('/api/media/'+mos+'/sort/dateAdded/desc?limit=%s&page=%s'%(limitRec,page),'')
	elif 'genre' in action_value[0]:
		(t,g) = action_value[0].split(',')
		data = get_media_data('/api/media/'+mos+'/filter/genre/desc?limit=%s&page=%s'%(limitRec,page),'{"filter_values": ["%s"]}'%g)
	else:
		if action_value[0] == '0-9':
			data = get_media_data('/api/media/'+mos+'/filter/startsWith/asc?limit=%s&page=%s'%(limitRec,page),'{"filter_values": ["0","1","2","3","4","5","6","7","8","9"]}')
		else:
			data = get_media_data('/api/media/'+mos+'/filter/startsWith/asc?limit=%s&page=%s'%(limitRec,page),'{"filter_values": ["%s"]}'%action_value[0])
	if action[0] == 'movies' and 'data' in data: process_movies(data['data'])
	if action[0] == 'series' and 'data' in data: process_series(data['data'])
	if 'pagination' in data and 'pageCount' in data['pagination'] and 'page' in data['pagination'] and data['pagination']['pageCount']>1:
		add_paging(int(data['pagination']['page'])+1, data['pagination']['pageCount'])
elif action[0] == 'movies.streams':
#	media = get_media_from_cache(action_value[0])
	media = get_media_data('/api/media/movies/'+action_value[0],'')
	if '_source' in media: show_stream_dialog(media['_source'])
elif action[0] == 'series.streams':
	(sid, ss, ep) = action_value[0].split(',')
	media = get_media_data('/api/media/tvshows/'+sid,'')
#	media = get_media_from_cache(sid)
	if '_source' in media: show_stream_dialog(media['_source']['seasons'][int(ss)]['episodes'][int(ep)])
elif action[0] == 'episodes':
	(sid, ss) = action_value[0].split(',')
	media = get_media_data('/api/media/tvshows/'+sid,'')
#	media = get_media_from_cache(sid)
	if '_source' in media: process_episodes(media['_source']['seasons'][int(ss)]['episodes'])
elif action[0] == 'seasons':
	media = get_media_data('/api/media/tvshows/'+action_value[0],'')
#	media = get_media_from_cache(action_value[0])
	if '_source' in media: process_seasons(media['_source']['seasons'])
elif action[0] == 'search':
	searchValue = client.getTextInput(session, addon.getLocalizedString(30207))
	if searchValue is not "":
		url = '/api/media/' + action_value[0] + '/filter/fuzzySearch/desc'
		if action_value[0] == 'movies':
			media = get_media_data(url + '?limit=%s&page=%s'%(limitMovies,page),'{"filter_values": ["%s"]}'%searchValue)
			if 'data' in media: process_movies(media['data'])
		if action_value[0] == 'tvshows':
			media = get_media_data(url + '?limit=%s&page=%s'%(limitSeries,page),'{"filter_values": ["%s"]}'%searchValue)
			if 'data' in media: process_series(media['data'])
#		if 'pagination' in data and 'pageCount' in data['pagination'] and 'page' in data['pagination'] and data['pagination']['pageCount']>1:
#			page=int(data['pagination']['page'])+1
#			if page <= pageCount:
#				addDir(add_translations(addon.getLocalizedString(30203) + ' ('+ str(page) + '/' + str(data['pagination']['pageCount']) +') '), build_plugin_url({ 'action': action[0], 'action_value': action_value[0], 'page': page }), 1, None)
elif action[0] == 'play' and action_value[0] != "" and name !="":
	play(action_value[0],name)

#if len(client.GItem_lst[0]) == 0: render_item(build_item(addon.getLocalizedString(30202), ''))
if len(client.GItem_lst[0]) == 0: render_item(build_item(None, ''))
