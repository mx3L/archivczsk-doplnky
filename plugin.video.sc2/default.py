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
hotshot_url = 'https://plugin.sc2.zone'
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
#		data = requests.post(url=url, data=post_data, headers={'User-Agent': UA2, 'X-Uuid': xuuid, 'Content-Type': 'application/json'}, timeout=15)
		data = requests.get(url=url, data=post_data, headers={'User-Agent': UA2, 'X-Uuid': xuuid, 'Content-Type': 'application/json'}, timeout=15)
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

def get_info(media,st=False):
	year = media['info_labels']['year'] if 'info_labels' in media and 'year' in media['info_labels'] else 0
	if year == 0 and 'aired' in media['info_labels'] and media['info_labels']['aired']: year = media['info_labels']['aired'][0:4]
	langs = (', '.join(media['available_streams']['audio_languages'])).upper() if 'available_streams' in media and 'audio_languages' in media['available_streams'] else ''
	title = media['i18n_info_labels'][0]['title'] if 'i18n_info_labels' in media and 'title' in media['i18n_info_labels'][0] else ""
	title = ' ' + media['info_labels']['originaltitle'] + langs if 'info_labels' in media and 'originaltitle' in media['info_labels'] and title == "" else title
#	title = media['info_labels']['originaltitle'] if 'info_labels' in media and 'originaltitle' in media['info_labels'] else ''
	if not st: title += ' - ' + langs + ' (' + str(year) + ')'
	genres = ""
	if 'info_labels' in media and 'genre' in media['info_labels']:
		genreL = []
		for genre in media['info_labels']['genre']:
			if genre in api_genres_langs: genreL.append(api_genres_langs[genre])
			genres = ', '.join(genreL)
	plot = '[' + genres + '] ' if genres else ""
	plot += media['i18n_info_labels'][0]['plot'] if 'i18n_info_labels' in media and 'plot' in media['i18n_info_labels'][0] else ""
	rating = media['i18n_info_labels'][0]['rating'] if 'i18n_info_labels' in media and 'rating' in media['i18n_info_labels'][0] else 0
	duration = media['info_labels']['duration'] if 'info_labels' in media and 'duration' in media['info_labels'] else 0
	if duration == 0 and 'streams' in media and len(media['streams'])>0 and 'duration' in media['streams'][0]: duration = media['streams'][0]['duration']
	poster = media['i18n_info_labels'][0]['art']['poster'] if 'i18n_info_labels' in media and 'art' in media['i18n_info_labels'][0] and 'poster' in media['i18n_info_labels'][0]['art'] and media['i18n_info_labels'][0]['art']['poster'] != "" else None
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
	for media in mediaList:
		if isExplicit(media): continue
		if not isFilterLang(media['_source']): continue
		info = get_info(media['_source'])
		title = ""
		if 'info_labels' in media['_source'] and 'episode' in media['_source']['info_labels']:
			title = str(int(media['_source']['info_labels']['season'])).zfill(2)+'x'+str(int(media['_source']['info_labels']['episode'])).zfill(2)+' '
		addDir(title+info['title'], build_plugin_url({ 'action': 'series.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year']})

def process_seasons(mediaList):
	for media in mediaList:
		if isExplicit(media): continue
		if not isFilterLang(media['_source']): continue
		info = get_info(media['_source'])
		if 'info_labels' in media['_source'] and 'episode' in media['_source']['info_labels']:
			title = str(int(media['_source']['info_labels']['season'])).zfill(2)+'x'+str(int(media['_source']['info_labels']['episode'])).zfill(2)+' '
		if 'info_labels' in media['_source'] and 'episode' in media['_source']['info_labels'] and media['_source']['info_labels']['episode'] == 0:
			addDir(info['title'], build_plugin_url({ 'action': 'episodes', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year']})
		else:
			addDir(title+info['title'], build_plugin_url({ 'action': 'series.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year']})

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
		addDir(info['title'], build_plugin_url({ 'action': 'movies.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year']})

def process_genres(mediaList):
	genres = {}
	for genre in mediaList:
		genres[genre['key']] = genre['doc_count']
	for c,d in api_genres_langs_items:
		if c in genres: addDir(d+' ('+str(genres[c])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'genre,'+c }), 1, None, None, None)
#		else: addDir(d+' ()', build_plugin_url({ 'action': action_value[0], 'action_value': 'genre,'+c }), 1, None, None, None)

def show_stream_dialog(id,ss=None,ep=None):
	media = get_media_data('/api/media/filter/ids?id='+id,'')
	if 'data' not in media or len(media['data'])==0: return False
	info = get_info(media['data'][0]['_source'],st=True)
	streams = get_media_data('/api/media/'+id+'/streams','')
	for stream in streams:
		title = ""
		if 'info_labels' in media['data'][0]['_source'] and 'episode' in media['data'][0]['_source']['info_labels'] and media['data'][0]['_source']['info_labels']['episode'] != 0:
			title += str(int(media['data'][0]['_source']['info_labels']['season'])).zfill(2)+'x'+str(int(media['data'][0]['_source']['info_labels']['episode'])).zfill(2)+' '
		if addon.getSetting('filter_hevc') == 'true' and stream['video'][0]['codec'].upper() == 'HEVC': continue
#		if not isFilterLangStream(stream): continue
#		title += stream_title(info['title'],stream)
		auds = []
		for audio in stream['audio']:
			if 'language' in audio:
				if audio['language'] == "": auds.append("??")
				else: auds.append(audio['language'])
		audset = set(auds)
		auds = list(audset)
		auds.sort()
		title += '['+str(stream['video'][0]['height'])+'p] ' if 'video' in stream and 'height' in stream['video'][0] else ''
		title += '['+str(stream['video'][0]['codec'])+'] ' if 'video' in stream and 'codec' in stream['video'][0] else ''
		title += '[3D] ' if 'video' in stream and '3d' in stream['video'][0] and stream['video'][0]['3d']=='true' else ''
		title += info['title']
		title += ' - '+(', '.join(auds)).upper() if len(auds)>0 else ''
		title += ' ('+convert_size(stream['size'])+')' if 'size' in stream else ''
		duration = stream['duration'] if 'duration' in stream else 0
		addDir(title,build_plugin_url({ 'action': 'play', 'action_value': stream['ident'], 'name': title.encode('utf-8') }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': duration, 'year': info['year']})

def play(ident,title):
	gurl = get_stream_url(ident)
	if gurl is not None:
		add_video(title,gurl,None,None)

def get_csfd_tips():
	data_url = 'https://www.csfd.cz/televize/'
	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}
	result = requests.get(data_url, headers=headers, timeout=15, verify=False)
	if result.status_code != 200:
		client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat z CSFD', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
		return
	data = re.search('<ul class="content ui-image-list">(.*?)</ul>', result.content, re.S)
	if data:
		articles = re.findall('<img src="(.*?)\?.*?<a href.*?>(.*?)<.*?film-year.*?>\((.*?)\).*?<p>(.*?)<', data.group(1), re.S)
		for article in articles:
			addDir(article[1]+' ('+article[2]+')',build_plugin_url({'action': 'search', 'action_value': article[1]}), 1, 'http:'+article[0], None, None, { 'plot': article[3]})

api_genres_langs = {
 'Action': addon.getLocalizedString(30501),
 'Animated': addon.getLocalizedString(30502),
 'Animation': 'Animation',
 'Anime': 'Anime',
 'Adventure': addon.getLocalizedString(30503),
 'Biographical': addon.getLocalizedString(30504),
 'Catastrophic': addon.getLocalizedString(30505),
 'Comedy': addon.getLocalizedString(30506),
 'Competition': addon.getLocalizedString(30507),
 'Crime': addon.getLocalizedString(30508),
 'Documentary': addon.getLocalizedString(30509),
 'Fairy Tale': addon.getLocalizedString(30510),
 'Drama': addon.getLocalizedString(30511),
 'Family': addon.getLocalizedString(30512),
 'Fantasy': addon.getLocalizedString(30513),
 'History': addon.getLocalizedString(30514),
 'Historic': 'Historic',
 'Horror': addon.getLocalizedString(30515),
 'Children': 'Children',
 'IMAX': addon.getLocalizedString(30516),
 'Educational': addon.getLocalizedString(30517),
 'Music': addon.getLocalizedString(30518),
 'Journalistic': addon.getLocalizedString(30519),
 'Military': addon.getLocalizedString(30520),
 'Musical': addon.getLocalizedString(30521),
 'Mysterious': addon.getLocalizedString(30522),
 'Mystery': 'Mystery',
 'News': 'News',
 'Psychological': addon.getLocalizedString(30523),
 'Puppet': 'Puppet',
 'Reality': addon.getLocalizedString(30524),
 'Reality-TV': 'Reality-TV',
 'Road movie': 'Road movie',
 'Romance': 'Romance',
 'Romantic': addon.getLocalizedString(30525),
 'Sci-Fi': addon.getLocalizedString(30526),
 'Short': addon.getLocalizedString(30527),
 'Short story': 'Short story',
 'Soap': 'Soap',
 'Special-interest': 'Special-interest',
 'Sports': addon.getLocalizedString(30528),
 'Stand-Up': addon.getLocalizedString(30529),
 'Superhero': 'Superhero',
 'Suspense': 'Suspense',
 'Talk-Show': addon.getLocalizedString(30530),
 'Telenovela': addon.getLocalizedString(30531),
 'Thriller': addon.getLocalizedString(30532),
# 'Travel': addon.getLocalizedString(30533),
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
limitSeries=50
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
		build_item(addon.getLocalizedString(30201), 'folder', 'series'),
#		build_item('CSFD TIPS', 'csfd', 'tips')
	],
	'movies': [
		build_item(addon.getLocalizedString(30204), 'search', 'movies'),
		build_item(addon.getLocalizedString(30211), 'movies','popular'),
		build_item('Novinky', 'movies','aired'),
		build_item('Novinky dabované', 'movies','dubbed'),
		build_item('Naposledy přidané', 'movies','dateadded'),
		build_item(addon.getLocalizedString(30206), 'folder','movies.a-z'),
		build_item(addon.getLocalizedString(30205), 'genres','movies')
	],
	'series': [
		build_item(addon.getLocalizedString(30204), 'search', 'tvshows'),
		build_item(addon.getLocalizedString(30211), 'series','popular'),
		build_item('Novinky', 'series','aired'),
		build_item('Novinky dabované', 'series','dubbed'),
		build_item('Naposledy přidané', 'series','dateadded'),
		build_item(addon.getLocalizedString(30206), 'folder','series.a-z'),
		build_item(addon.getLocalizedString(30205), 'genres','series')
	],
	'series.genre': [build_item(d, 'series', 'genre,'+c) for c,d in api_genres_langs_items],
	'movies.genre': [build_item(d, 'movies', 'genre,'+c) for c,d in api_genres_langs_items]
}

if action_value and 'movies.a-z' in action_value[0]:
	moviesCount = get_media_data('/api/media/filter/startsWithSimple/count/titles?type=movie&value=','')
	moviesCountAZ = {}
	if not 'data' in moviesCount:
		client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat ze serveru', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
	else:
		for count in moviesCount['data']:
			moviesCountAZ[count['key']] = count['doc_count']
		for c in digits:
			if c in moviesCountAZ: moviesCountAZ['0-9']+=moviesCountAZ[c]
		menu['movies.a-z']=[build_item(c+' ('+str(moviesCountAZ[c])+')', 'folder', 'movies.a-z.'+c) for c in ascii_uppercase]

if action_value and 'series.a-z' in action_value[0]:
	seriesCount = get_media_data('/api/media/filter/startsWithSimple/count/titles?type=tvshow&value=','')
	seriesCountAZ = {}
	if not 'data' in seriesCount:
		client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat ze serveru', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
	else:
		for count in seriesCount['data']:
			seriesCountAZ[count['key']] = count['doc_count']
		for c in digits:
			if c in seriesCountAZ: seriesCountAZ['0-9']+=seriesCountAZ[c]
		menu['series.a-z']=[build_item(c+' ('+str(seriesCountAZ[c])+')', 'folder', 'series.a-z.'+c) for c in ascii_uppercase]

if action_value and 'movies.a-z.' in action_value[0]:
	(mm,aa,cc) = action_value[0].split('.')
	moviesCount = get_media_data('/api/media/filter/startsWithSimple/count/titles?type=movie&value='+cc,'')
	moviesCountAZsec = {}
	if not 'data' in moviesCount:
		client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat ze serveru', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
	else:
		for count in moviesCount['data']:
			moviesCountAZsec[count['key']] = count['doc_count']
	menu['movies.a-z.'+cc]=[build_item('Zobrazit vše od '+cc.upper()+' ('+str(moviesCountAZ[cc])+')', 'movies', cc)] + [build_item(cc+c+' ('+str(moviesCountAZsec[cc+c])+')', 'movies', cc+c) for c in ascii_uppercase if cc+c in moviesCountAZsec]

if action_value and 'series.a-z.' in action_value[0]:
	(mm,aa,cc) = action_value[0].split('.')
	seriesCount = get_media_data('/api/media/filter/startsWithSimple/count/titles?type=tvshow&value='+cc,'')
	seriesCountAZsec = {}
	if not 'data' in seriesCount:
		client.add_operation("SHOW_MSG", {'msg': 'Chyba nacitani dat ze serveru', 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
	else:
		for count in seriesCount['data']:
			seriesCountAZsec[count['key']] = count['doc_count']
	menu['series.a-z.'+cc]=[build_item('Zobrazit vše od '+cc.upper()+' ('+str(seriesCountAZ[cc])+')', 'series', cc)] + [build_item(cc+c+' ('+str(seriesCountAZsec[cc+c])+')', 'series', cc+c) for c in ascii_uppercase if cc+c in seriesCountAZsec]

if action is None:
	for c in menu['root']:
		render_item(c)
elif action[0] == 'csfd':
	get_csfd_tips()
elif action[0] == 'folder':
	if action_value[0] in menu:
		for c in menu[action_value[0]]:
			render_item(c)
elif action[0] == 'movies' or action[0] == 'series':
	mos = 'movie' if action[0] == 'movies' else 'tvshow'
	limitRec = limitMovies if action[0] == 'movies' else limitSeries
	if action_value[0] == 'popular':
		data = get_media_data('/api/media/filter/all?sort=playCount&type='+mos+'&order=desc&limit=%s&page=%s'%(limitRec,page),'')
	elif action_value[0] == 'aired':
		data = get_media_data('/api/media/filter/all?sort=premiered&type='+mos+'&order=desc&limit=%s&page=%s'%(limitRec,page),'')
	elif action_value[0] == 'dateadded':
		data = get_media_data('/api/media/filter/all?sort=dateAdded&type='+mos+'&order=desc&limit=%s&page=%s'%(limitRec,page),'')
	elif action_value[0] == 'dubbed':
		data = get_media_data('/api/media/filter/dubbed?lang=cs&lang=sk&sort=premiered&type='+mos+'&order=desc&limit=%s&page=%s'%(limitRec,page),'')
	elif 'genre' in action_value[0]:
		(t,g) = action_value[0].split(',')
		data = get_media_data('/api/media/filter/genre?sort=year&type='+mos+'&order=desc&value=%s&limit=%s&page=%s'%(g,limitRec,page),'')
	else:
		data = get_media_data('/api/media/filter/startsWithSimple?type='+mos+'&value=%s&limit=%s&page=%s'%(action_value[0],limitRec,page),'')
	if action[0] == 'movies' and 'data' in data: process_movies(data['data'])
	if action[0] == 'series' and 'data' in data: process_series(data['data'])
	if 'pagination' in data and 'pageCount' in data['pagination'] and 'page' in data['pagination'] and data['pagination']['pageCount']>1:
		add_paging(int(data['pagination']['page'])+1, data['pagination']['pageCount'])
elif action[0] == 'movies.streams':
	show_stream_dialog(action_value[0])
elif action[0] == 'series.streams':
	show_stream_dialog(action_value[0])
elif action[0] == 'episodes':
	media = get_media_data('/api/media/filter/parent?sort=episode&value='+action_value[0],'')
	if 'data' in media: process_episodes(media['data'])
elif action[0] == 'seasons':
	media = get_media_data('/api/media/filter/parent?sort=episode&value='+action_value[0],'')
	if 'data' in media: process_seasons(media['data'])
elif action[0] == 'genres':
	mos = 'movie' if action_value[0] == 'movies' else 'tvshow'
	media = get_media_data('/api/media/filter/all/count/genres?type='+mos,'')
	if 'data' in media: process_genres(media['data'])
elif action[0] == 'search':
	if action_value[0] in ['movies','tvshows']:
		searchValue = client.getTextInput(session, addon.getLocalizedString(30207))
	else:
		searchValue = action_value[0]
		action_value[0] = 'movies'
	if searchValue is not "":
		if action_value[0] == 'movies':
			media = get_media_data('/api/media/filter/search?sort=score&type=movie&order=desc&value=%s&limit=%s&page=%s'%(searchValue,limitMovies,page),'')
			if 'data' in media: process_movies(media['data'])
		if action_value[0] == 'tvshows':
			media = get_media_data('/api/media/filter/search?sort=score&type=tvshow&order=desc&value=%s&limit=%s&page=%s'%(searchValue,limitSeries,page),'')
			if 'data' in media: process_series(media['data'])
elif action[0] == 'play' and action_value[0] != "" and name !="":
	play(action_value[0],name)

if len(client.GItem_lst[0]) == 0: render_item(build_item(None, ''))
