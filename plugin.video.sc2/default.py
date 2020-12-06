# -*- coding: utf-8 -*-

sys.path.append(os.path.dirname(__file__))
import requests, urllib, urlparse, hashlib, re, datetime, util, json, search, math, uuid, unicodedata
from xml.etree import ElementTree as ET
from string import ascii_uppercase, ascii_lowercase, digits
from Screens.MessageBox import MessageBox
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.tools.util import unescapeHTML
from Plugins.Extensions.archivCZSK.engine.client import add_dir, add_video
from Plugins.Extensions.archivCZSK.engine import client
from Components.config import config
from Components.Language import language
from md5crypt import md5crypt
from bisect import bisect
from const import country_lang, genre_lang, language_lang

addon = ArchivCZSK.get_xbmc_addon('plugin.video.sc2')
addon_userdata_dir = addon.getAddonInfo('profile')+'/'
home = addon.getAddonInfo('path')
icon = os.path.join(home, 'icon.png')
hotshot_url = 'https://plugin.sc2.zone'
ws_api = 'https://webshare.cz/api'
UA = "KODI/18.6 (Windows; U; Windows NT; en) ver1.3.26"
UA2 = 'SCC Enigma2'
TK = 'asb6mnn72mqruo4v81tn'
AU2 = 'Basic '+TK
realm = ':Webshare:'
base_url = ""
lang_id=language.getLanguage()[:2]
LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'sc2.log')
langFilter = addon.getSetting('item_filter_lang')
langs_pref = ['cs','sk','en']
qualities = [0,144,240,360,480,720,1080,2160,4320]
sizes = [0,1,2,3,4,5,10,15,20]
bitrates = [0,1,2,3,4,5,10,15,20,30,40,50]
quality_map = {144: '144p',240: '240p',360: '360p',480: '480p',720: '720p',1080: '1080p',2160: '2160p',4320: '4320p'}
max_studios = 500
loading_timeout = int(addon.getSetting('loading_timeout')) if addon.getSetting('loading_timeout') else 15

def writeLog(msg, type='INFO'):
	try:
		f = open(LOG_FILE, 'a')
		dtn = datetime.datetime.now()
		f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
		f.close()
	except:
		pass

def strip_accents(s):
#	print s.decode('utf-8')
	return ''.join(c for c in unicodedata.normalize('NFD', s.decode('utf-8')) if unicodedata.category(c) != 'Mn')

def ws_api_request(url, data):
	return requests.post(ws_api + url, data=data, headers={'User-Agent': UA2, 'X-Uuid': xuuid}, timeout=loading_timeout)

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
		return token
	return ""

def get_stream_url(ident):
	token = login()
	if token == "":
		client.add_operation("SHOW_MSG", {'msg': addon.getLocalizedString(40501), 'msgType': 'error', 'msgTimeout': 1, 'canClose': True })
	req = ws_api_request('/file_link/', { 'wst': token, 'ident': ident })
	xml = ET.fromstring(req.text)
	if not xml.find('status').text == 'OK':
		client.add_operation("SHOW_MSG", {'msg': addon.getLocalizedString(40502), 'msgType': 'error', 'msgTimeout': 20, 'canClose': True })
		return None
	return xml.find('link').text

def api_request(url,post_data=''):
	url = hotshot_url + url
	if '?' in url: url = url + '&access_token=' + TK
	else: url = url + '?access_token=' + TK
	try:
		data = requests.get(url=url, data=post_data, headers={'User-Agent': UA2, 'Authorization': AU2, 'X-Uuid': xuuid, 'Content-Type': 'application/json'}, timeout=loading_timeout)
		if data.status_code != 200:
			client.add_operation("SHOW_MSG", {'msg': addon.getLocalizedString(30501), 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
			return {'data': "" }
		else:
			return json.loads(data.content)
	except Exception as e:
		client.add_operation("SHOW_MSG", {'msg': addon.getLocalizedString(30501), 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
		pass
	return {'data': "" }

def get_media_data(url,post_data=''):
	data = api_request(url,post_data)
	return data

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

def find_closest_resolution(height):
	keys = sorted(quality_map.keys())
	index = bisect(keys, height)
	return quality_map[keys[index]]

def resolution_to_quality(video, with_3d=True):
	height = video.get('height')
	quality = quality_map.get(height) or find_closest_resolution(height)
	if with_3d and video['3d']:
		quality += ' 3D'
	return quality

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

def get_info(media,st=False):
	try:
		dadded = " ["+datetime.datetime.strptime(media['info_labels']['dateadded'],'%Y-%m-%d %H:%M:%S').strftime("%d.%m.%Y %H:%M")+"]"
	except:
		dadded = ""
	year = media['info_labels']['year'] if 'info_labels' in media and 'year' in media['info_labels'] else 0
	if year == 0 and 'aired' in media['info_labels'] and media['info_labels']['aired']: year = media['info_labels']['aired'][0:4]
	try:
		alangs = []
		for lst in media['available_streams']['audio_languages']:
			alangs.append(lst['lang'])
		langs = (', '.join(alangs)).upper()
	except:
		langs = ''
	labels = {}
	if 'i18n_info_labels' in media:
		for label in media['i18n_info_labels']:
			labels[label['lang']] = label
	if abc:
		(m,v) = action_value[0].split(',')
		title = ''
		if 'i18n_info_labels' in media:
			for lang in langs_pref:
				if title == '' and lang in labels and 'title' in labels[lang] and re.sub(r'[^a-z0-9]','',strip_accents(labels[lang]['title']).lower())[:len(v)] == v.lower():
					title = labels[lang]['title']
		title = media['info_labels']['originaltitle'] if title == '' and 'info_labels' in media and 'originaltitle' in media['info_labels'] else title
	else:
		title = media['i18n_info_labels'][0]['title'] if 'i18n_info_labels' in media and 'title' in media['i18n_info_labels'][0] else ""
		title = ' ' + media['info_labels']['originaltitle'] + langs if 'info_labels' in media and 'originaltitle' in media['info_labels'] and title == "" else title
	if not st: title += ' - ' + langs + ' (' + str(year) + ')'
	genres = ""
	if 'info_labels' in media and 'genre' in media['info_labels']:
		genreL = []
		for genre in media['info_labels']['genre']:
			if genre in genre_lang: genreL.append(addon.getLocalizedString(genre_lang[genre]))
			genres = ', '.join(genreL)
	plot = '[' + genres + '] ' if genres else ""
	rating = media.get("ratings",{}).get("csfd",{}).get("rating",0)
	poster = None
	if lang_id in labels:
		if 'plot' in labels[lang_id] and labels[lang_id]['plot']: plot += labels[lang_id]['plot']
		if 'art' in labels[lang_id] and 'poster' in labels[lang_id]['art'] and labels[lang_id]['art']['poster'] != "": poster = labels[lang_id]['art']['poster']
	if poster is None and 'art' in labels['en'] and 'poster' in labels['en']['art'] and labels['en']['art']['poster'] != "": poster = labels['en']['art']['poster']
	duration = media['info_labels']['duration'] if 'info_labels' in media and 'duration' in media['info_labels'] else 0
	if duration == 0:
		try: duration = media['streams'][0]['duration'] or 0
		except:	pass
	if duration == 0:
		try: duration = media['stream_info']['video']['duration'] or 0
		except:	pass
	if 'play_count' in media: plot += "{"+str(media['play_count'])+"}"
	return {'title': title, 'plot': plot+dadded, 'rating': rating, 'duration': duration, 'poster': poster, 'year': year, 'genres': genres, 'langs': langs}

def add_paging(page, pageCount):
	if page <= pageCount:
		addDir(add_translations(addon.getLocalizedString(30203) + ' ('+ str(page) + '/' + str(pageCount) +') '), build_plugin_url({ 'action': action[0], 'action_value': action_value[0], 'page': page }), 1, None)

def save_search_history(query):
	max_history = 10
	cnt = 0
	history = []
	filename = addon_userdata_dir + "search_history.txt"
	try:
		with open(filename, "r") as file:
			for line in file:
				item = line[:-1]
				history.append(item)
	except IOError:
		history = []
	history.insert(0,query)
	with open(filename, "w") as file:
		for item  in history:
			cnt = cnt + 1
			if cnt <= max_history:
				file.write('%s\n' % item)

def load_search_history():
	history = []
	filename = addon_userdata_dir + "search_history.txt"
	try:
		with open(filename, "r") as file:
			for line in file:
				item = line[:-1]
				history.append(item)
	except IOError:
		history = []
	return history

def list_search():
	addDir("Nové hledání", build_plugin_url({'action': 'search', 'action_value': '-----'}), 1, None)
	history = load_search_history()
	for item in history:
		addDir(item, build_plugin_url({'action': 'search', 'action_value': item}), 1, None)

def search():
	query = action_value[0]
	if query == "-----":
		query = client.getTextInput(session, addon.getLocalizedString(30207))
		if len(query) == 0:
#			client.add_operation("SHOW_MSG", {'msg': 'Je potřeba zadat hledaný řetězec', 'msgType': 'error', 'msgTimeout': 1, 'canClose': True })
			client.showInfo('Je potřeba zadat hledaný řetězec')
#			client.refresh_screen()
			return
		else:
			if history == 1: save_search_history(query)
	if query is not "":
		mediaList = get_media_data('/api/media/filter/search?sort=score&type=%%2A&order=desc&value=%s'%query,'')
		if 'data' in mediaList:
			for media in mediaList['data']:
				if isExplicit(media['_source']): continue
				if isFilterLang(media['_source']): continue
				info = get_info(media['_source'])
				if 'i18n_info_labels' in media['_source'] and 'parent_titles' in media['_source']['i18n_info_labels'][0] and len(media['_source']['i18n_info_labels'][0]['parent_titles'])>0:
					info['title'] = ' - '.join(media['_source']['i18n_info_labels'][0]['parent_titles'])+' - '+info['title']
				if 'info_labels' in media['_source'] and 'mediatype' in media['_source']['info_labels'] and media['_source']['info_labels']['mediatype'] == 'tvshow':
					addDir(info['title'], build_plugin_url({ 'action': 'seasons', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year'], 'genre': info['genres']})
				else:
					addDir(info['title'], build_plugin_url({ 'action': 'movies.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year'], 'genre': info['genres']})


def isExplicit(media):
	if addon.getSetting('explicit_content') == 'false':
		if 'adult' in media and media['adult'] == True: return True
		if 'info_labels' in media and 'genre' in media['info_labels'] and ('Pornographic' in media['info_labels']['genre'] or 'Erotic' in media['info_labels']['genre']): return True
	return False

def isFilterLangStream(stream):
	# 0 all, 1-CZ&SK, 2-CZ 3-SK, 4-EN
	if langFilter != '0':
		lang = []
		if 'audio' in stream:
			for temp in stream['audio']:
				if 'language' in temp: lang.append(temp['language'].lower())
			if len(lang)>0 and '' in lang: return False # neuvedeny jazyk vzdy zobrazit
			if len(lang)>0 and langFilter is '1' and 'cs' in lang or 'sk' in lang: return False
			if len(lang)>0 and langFilter is '2' and 'cs' in lang: return False
			if len(lang)>0 and langFilter is '3' and 'sk' in lang: return False
			if len(lang)>0 and langFilter is '4' and 'en' in lang: return False
		return True
	return False

def isFilterLang(media):
	# 0 all, 1-CZ&SK, 2-CZ 3-SK, 4-EN
	alangs = []
	try:
		for lang in media['available_streams']['audio_languages']:
			if lang['lang']: alangs.append(lang['lang'])
	except:
		pass
	if langFilter != '0':
		if '' in alangs: return False # neuvedeny jazyk vzdy zobrazit
		if langFilter == '1' and 'cs' in alangs or 'sk' in alangs: return False
		if langFilter == '2' and 'cs' in alangs: return False
		if langFilter == '3' and 'sk' in alangs: return False
		if langFilter == '4' and 'en' in alangs: return False
		return True
	return False

def process_episodes(mediaList):
	for media in mediaList:
		if isExplicit(media): continue
		if isFilterLang(media['_source']): continue
		info = get_info(media['_source'])
		title = ""
		if 'info_labels' in media['_source'] and 'episode' in media['_source']['info_labels']:
			if int(media['_source']['info_labels']['season']) == 0: title = str(int(media['_source']['info_labels']['episode'])).zfill(2)+' '
			elif int(media['_source']['info_labels']['season']) != 0: title = str(int(media['_source']['info_labels']['season'])).zfill(2)+'x'+str(int(media['_source']['info_labels']['episode'])).zfill(2)+' '
		addDir(title+info['title'], build_plugin_url({ 'action': 'series.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year'], 'genre': info['genres']})

def process_seasons(mediaList):
	for media in mediaList:
		if isExplicit(media['_source']): continue
		if isFilterLang(media['_source']): continue
		info = get_info(media['_source'])
		if media.get('_source',{}).get('info_labels',{}).get('mediatype','') == 'season':
			addDir(info['title'], build_plugin_url({ 'action': 'episodes', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year'], 'genre': info['genres']})
		else:
			addDir(info['title'], build_plugin_url({ 'action': 'series.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year'], 'genre': info['genres']})

def process_movies_series(mediaList,sort=0):
	for media in mediaList:
		if isExplicit(media['_source']): continue
		if isFilterLang(media['_source']): continue
		info = get_info(media['_source'])
		cmenuItems = {}
		if media.get("_source",{}).get("info_labels",{}).get("trailer","") != "":
			cmenuItems['Přehrát trailer']={'action': 'trailer', 'id': media['_source']['info_labels']['trailer']}
		if media.get("_source",{}).get("services",{}).get("csfd","") != "":
			cmenuItems[addon.getLocalizedString(40503)]={'action': 'related', 'id': media['_source']['services']['csfd']}
			cmenuItems[addon.getLocalizedString(40504)]={'action': 'similar', 'id': media['_source']['services']['csfd']}
		if media.get("_source",{}).get("info_labels",{}).get("mediatype","") == 'tvshow':
			addDir(info['title'], build_plugin_url({ 'action': 'seasons', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year'], 'genre': info['genres']}, menuItems=cmenuItems)
		else:
			addDir(info['title'], build_plugin_url({ 'action': 'movies.streams', 'action_value': media['_id'] }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': info['duration'], 'year': info['year'], 'genre': info['genres']}, menuItems=cmenuItems)
	if abc or sort==1: client.GItem_lst[0].sort(key=lambda x:strip_accents(x.name))

def process_genres(mediaList):
	genres = {}
	for genre in mediaList:
		title = addon.getLocalizedString(genre_lang[genre['key']]) if genre['key'] in genre_lang else genre['key']
		addDir(title+' ('+str(genre['doc_count'])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'genre,'+genre['key'] }), 1, None, None, None)
	client.GItem_lst[0].sort(key=lambda x:strip_accents(x.name))

def process_studios(mediaList):
	cnt = 0
	studios = {}
	for p in mediaList:
		studios[p['key'].encode('utf-8')] = p['doc_count']
	studioss = sorted(studios.items(), key=lambda x: x[1], reverse=True)
	for studio in studioss:
		cnt+=1
		if cnt > max_studios: break
		addDir(studio[0]+' ('+str(studio[1])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'studio,'+studio[0] }), 1, None, None, None)
#	client.GItem_lst[0].sort(key=lambda x:x.name)

def process_years(mediaList):
	years = {}
	for year in mediaList:
		years[year['key']]=year['doc_count']
	yearss=sorted(years, key=lambda x:int(x), reverse=True)
	for year in yearss:
		addDir(year+' ('+str(years[year])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'year,'+year }), 1, None, None, None)
#	client.GItem_lst[0].sort(key=lambda x:int(x.name), reverse=True)

def process_languages(mediaList):
	if len(mediaList) == 0: return
	langs = {}
	langkeys = {}
	for lang in mediaList:
		langs[addon.getLocalizedString(language_lang.get(lang['key'],lang['key']))]=lang['doc_count']
		langkeys[addon.getLocalizedString(language_lang.get(lang['key'],lang['key']))]=lang['key']
	addDir(addon.getLocalizedString(language_lang['cs'])+' ('+str(langs[addon.getLocalizedString(language_lang['cs'])])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'language,cs'}), 1, None, None, None)
	addDir(addon.getLocalizedString(language_lang['sk'])+' ('+str(langs[addon.getLocalizedString(language_lang['sk'])])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'language,sk'}), 1, None, None, None)
	addDir(addon.getLocalizedString(language_lang['en'])+' ('+str(langs[addon.getLocalizedString(language_lang['en'])])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'language,en'}), 1, None, None, None)
	for lang in sorted(langs,key=strip_accents):
		if addon.getLocalizedString(language_lang['cs']) in lang or addon.getLocalizedString(language_lang['sk']) in lang or addon.getLocalizedString(language_lang['en']) in lang: continue
		addDir(lang+' ('+str(langs[lang])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'language,'+langkeys[lang] }), 1, None, None, None)
#	client.GItem_lst[0].sort(key=lambda x:strip_accents(x.name))

def process_countries(mediaList):
	countries = {}
	countriekeys = {}
	for country in mediaList:
		countries[addon.getLocalizedString(country_lang.get(country['key'],country['key']))]=country['doc_count']
		countriekeys[addon.getLocalizedString(country_lang.get(country['key'],country['key']))]=country['key']
	addDir(addon.getLocalizedString(country_lang['Czechia'])+' ('+str(countries[addon.getLocalizedString(country_lang['Czechia'])])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'country,Czechia'}), 1, None, None, None)
	addDir(addon.getLocalizedString(country_lang['Czechoslovakia'])+' ('+str(countries[addon.getLocalizedString(country_lang['Czechoslovakia'])])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'country,Czechoslovakia'}), 1, None, None, None)
	addDir(addon.getLocalizedString(country_lang['Slovakia'])+' ('+str(countries[addon.getLocalizedString(country_lang['Slovakia'])])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'country,Slovakia'}), 1, None, None, None)
	addDir(addon.getLocalizedString(country_lang['United States of America'])+' ('+str(countries[addon.getLocalizedString(country_lang['United States of America'])])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'country,United States of America'}), 1, None, None, None)
	for country in sorted(countries,key=strip_accents):
		if addon.getLocalizedString(country_lang['Czechia']) in country or addon.getLocalizedString(country_lang['Czechoslovakia']) in country or addon.getLocalizedString(country_lang['Slovakia']) in country or addon.getLocalizedString(country_lang['United States of America']) in country: continue
		addDir(country+' ('+str(countries[country])+')', build_plugin_url({ 'action': action_value[0], 'action_value': 'country,'+countriekeys[country]}), 1, None, None, None)
#	client.GItem_lst[0].sort(key=lambda x:strip_accents(x.name))

def process_az(mediaList):
	(m,v) = action_value[0].split(',')
	for az in mediaList:
		if az['doc_count'] < 50:
			addDir(az['key']+' ('+str(az['doc_count'])+')', build_plugin_url({ 'action': m, 'action_value': 'a-z,'+az['key'] }), 1, None, None, None)
		else:
			addDir(az['key']+' ('+str(az['doc_count'])+')', build_plugin_url({ 'action': action[0], 'action_value': m+','+az['key'] }), 1, None, None, None)

def show_stream_dialog(id,ss=None,ep=None):
	media = get_media_data('/api/media/filter/ids?id='+id,'')
	if 'data' not in media or len(media['data'])==0: return False
	info = get_info(media['data'][0]['_source'],st=True)
	streams = get_media_data('/api/media/'+id+'/streams','')
	for stream in streams:
		title = ""
		if 'info_labels' in media['data'][0]['_source'] and 'episode' in media['data'][0]['_source']['info_labels'] and media['data'][0]['_source']['info_labels']['episode']:
			title += str(int(media['data'][0]['_source']['info_labels']['season'])).zfill(2)+'x'+str(int(media['data'][0]['_source']['info_labels']['episode'])).zfill(2)+' '
		if addon.getSetting('filter_hevc') == 'true' and 'video' in stream and 'codec' in stream['video'][0] and stream['video'][0]['codec'].upper() == 'HEVC': continue
		if isFilterLangStream(stream): continue
		if addon.getSetting('max_size') != '0' and 'size' in stream and sizes[int(addon.getSetting('max_size'))]*1024*1024*1024 < stream['size']: continue
		if addon.getSetting('max_bitrate') != '0' and 'size' in stream and 'video' in stream and 'duration' in stream['video'][0] and bitrates[int(addon.getSetting('max_bitrate'))]*1024*1024 < stream['size'] / stream['video'][0]['duration'] * 8: continue
		if addon.getSetting('max_quality') != '0' and 'video' in stream and 'height' in stream['video'][0] and qualities[int(addon.getSetting('max_quality'))] < stream['video'][0]['height']: continue
		auds = []
		for audio in stream['audio']:
			if 'language' in audio:
				if audio['language'] == "": auds.append("??")
				else: auds.append(audio['language'])
		audset = set(auds)
		auds = list(audset)
		auds.sort()
		bit_rate = ' - '+convert_bitrate(stream['size'] / stream['video'][0]['duration'] * 8) if addon.getSetting('show_bitrate')=='true' and 'size' in stream and 'video' in stream and 'duration' in stream['video'][0] else ''
#		title += '['+str(stream['video'][0]['height'])+'p] ' if 'video' in stream and 'height' in stream['video'][0] else ''
		title += '['+resolution_to_quality(stream['video'][0])+'] ' if 'video' in stream and 'height' in stream['video'][0] else ''
		title += '['+str(stream['video'][0]['codec'])+'] ' if addon.getSetting('show_codec')=='true' and 'video' in stream and 'codec' in stream['video'][0] else ''
		title += '[3D] ' if 'video' in stream and '3d' in stream['video'][0] and stream['video'][0]['3d']=='true' else ''
		title += info['title']
		title += ' - '+(', '.join(auds)).upper() if len(auds)>0 else ''
		title += ' ('+convert_size(stream['size'])+bit_rate+')' if 'size' in stream else ''
		duration = stream['video'][0]['duration'] if 'video' in stream and 'duration' in stream['video'][0] else 0
		addDir(title,build_plugin_url({ 'action': 'play', 'action_value': stream['ident'], 'name': title.encode('utf-8') }), 1, info['poster'], None, None, { 'plot': info['plot'], 'rating': info['rating'], 'duration': duration, 'year': info['year'], 'genre': info['genres']})
#		gurl = get_stream_url(stream['ident'])
#		if gurl is not None:
#			add_video(title,gurl,None,info['poster'],infoLabels={ 'plot': info['plot'], 'rating': info['rating'], 'duration': duration, 'year': info['year'], 'genre': info['genres']})
#	client.GItem_lst[0].sort(key=lambda x:x.name)

def play(ident,title):
	gurl = get_stream_url(ident)
	if gurl is not None:
		add_video(title,gurl,None,None)
#		from Plugins.Extensions.archivCZSK.engine.player.player import Player
#		from Plugins.Extensions.archivCZSK.engine.items import PVideo
#		it = PVideo()
#		it.name = title
#		it.url = gurl
#		Player(session).play_item(item = it)
#		client.refresh_screen()

def play_trailer(turl):
	video_formats = client.getVideoFormats(turl)
	video_url = [video_formats[-1]]
	if video_url[0]['url']:
		add_video('Trailer',video_url[0]['url'],None,None)
#		from Plugins.Extensions.archivCZSK.engine.player.player import Player
#		from Plugins.Extensions.archivCZSK.engine.items import PVideo
#		it = PVideo()
#		it.name = 'Trailer'
#		it.url = video_url[0]['url']
#		Player(session).play_item(item = it)
#		client.refresh_screen()

def get_csfd_api(url):
	cookies = {'tv_stations':'2%2C3%2C4%2C5%2C24%2C19%2C26%2C33%2C16%2C78%2C1%2C8%2C93%2C13%2C22%2C14%2C41%2C88','tv_tips_order':'rating'}
	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}
	result = requests.get('https://www.csfd.cz'+url, headers=headers, cookies=cookies, timeout=loading_timeout, verify=False)
	if result.status_code != 200:
		client.add_operation("SHOW_MSG", {'msg': addon.getLocalizedString(30500), 'msgType': 'error', 'msgTimeout': 10, 'canClose': True })
		return None
	return result.content

def get_csfd_tips():
	html = get_csfd_api('/televize/')
	if html:
		data = re.search('<ul class="content ui-image-list">(.*?)</ul>', html, re.S)
		try:
			articles = re.findall('<img src="(.*?)\?.*?<a href="/film/([0-9]+?)-.*?>(.*?)<.*?film-year.*?>\((.*?)\).*?<p>(.*?)<', data.group(1), re.S)
			vals=[]
			for article in articles:
				vals.append("value="+article[1])
			data = get_media_data('/api/media/filter/service?type=movie&'+'&'.join(vals)+'&service=csfd','')
			if 'data' in data: process_movies_series(data['data'])
		except:
			pass

def get_related(cid):
	html = get_csfd_api('/film/'+str(cid))
	if html:
		data = re.search('<div class="ct-related related">(.*?)</div>', html, re.S)
		if data:
			articles = re.findall('<a href="/film/([0-9]+?)\-.*?"', data.group(1), re.S)
			vals=[]
			for article in articles:
				vals.append("value="+article)
			data = get_media_data('/api/media/filter/service?type=movie&'+'&'.join(vals)+'&service=csfd','')
			if 'data' in data: process_movies_series(data['data'])

def get_similar(cid):
	html = get_csfd_api('/film/'+str(cid))
	if html:
		data = re.search('<div class="ct-related similar">(.*?)</div>', html, re.S)
		if data:
			articles = re.findall('<a href="/film/([0-9]+?)\-.*?"', data.group(1), re.S)
			vals=[]
			for article in articles:
				vals.append("value="+article)
			data = get_media_data('/api/media/filter/service?type=movie&'+'&'.join(vals)+'&service=csfd','')
			if 'data' in data: process_movies_series(data['data'])

def get_csfd_tops(origin):
	if origin>0:
		html = get_csfd_api('/zebricky/specificky-vyber/?type=3&origin='+str(origin)+'&genre=&year_from=&year_to=&actor=&director=&ok=Zobrazit&_form_=charts&show=complete')
	else:
		html = get_csfd_api('/zebricky/nejlepsi-serialy/?show=complete')
	if html:
		data = re.search('<table class="content.*?>(.*?)</table>', html, re.S)
		if data:
			articles = re.findall('<a href="/film/([0-9]+?)\-.*?"', data.group(1), re.S)
			vals=[]
			for article in articles:
				vals.append("value="+article)
			data = get_media_data('/api/media/filter/service?type=tvshow&'+'&'.join(vals)+'&service=csfd','')
			if 'data' in data: process_movies_series(data['data'])

def get_csfd_topf(origin):
	if origin>0:
		html = get_csfd_api('/zebricky/specificky-vyber/?type=0&origin='+str(origin)+'&genre=&year_from=&year_to=&actor=&director=&ok=Zobrazit&_form_=charts&show=complete')
	else:
		html = get_csfd_api('/zebricky/nejlepsi-filmy/?show=complete')
	if html:
		data = re.search('<table class="content.*?>(.*?)</table>', html, re.S)
		if data:
			articles = re.findall('<a href="/film/([0-9]+?)\-.*?"', data.group(1), re.S)
			vals=[]
			for article in articles:
				vals.append("value="+article)
			data = get_media_data('/api/media/filter/service?type=movie&'+'&'.join(vals)+'&service=csfd','')
			if 'data' in data: process_movies_series(data['data'])


xuuid = addon.getSetting('uuid')
if xuuid == "":
	xuuid = str(uuid.uuid4())
	addon.setSetting('uuid',xuuid)

from urlparse import parse_qsl
from urllib import urlencode
nurl=params['url'][1:] if 'url' in params else urlencode(params)
nparams = dict(parse_qsl(nurl))

page=1
name=None
url=None
action=None
action_value=None
abc=False
history=1

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
try:
	history=urlparse.parse_qs(urlparse.urlparse(url).query)['history']
except:
	pass

#writeLog('NP: '+str(nparams))
#writeLog('PAGE: '+str(page))
#writeLog('URL: '+str(url))
#writeLog('NAME: '+str(name))
#writeLog('ACT: '+str(action))
#writeLog('ACTVAL: '+str(action_value))
#print params

menu = {
	'root': [
		build_item(addon.getLocalizedString(30204), 'listsearch', ''),
		build_item(addon.getLocalizedString(30200), 'folder','movies'),
		build_item(addon.getLocalizedString(30201), 'folder', 'series'),
		build_item(addon.getLocalizedString(30174), 'folder', 'concerts'),
		build_item(addon.getLocalizedString(30309), 'csfd', 'tips'),
		build_item('ČSFD.cz Top filmy', 'csfdtopf', '0'),
		build_item('ČSFD.cz Top seriály', 'csfdtops', 'tops'),
		build_item('ČSFD.cz Top filmy (Československo)', 'csfdtopf', '197'),
		build_item('ČSFD.cz Top filmy (Česko)', 'csfdtopf', '1'),
		build_item('ČSFD.cz Top filmy (Slovensko)', 'csfdtopf', '2'),
		build_item('ČSFD.cz Top seriály (Československo)', 'csfdtops', '197'),
		build_item('ČSFD.cz Top seriály (Česko)', 'csfdtops', '1'),
		build_item('ČSFD.cz Top seriály (Slovensko)', 'csfdtops', '2'),
#		build_item(addon.getLocalizedString(30254), 'seen', 'seen'),
	],
	'movies': [
		build_item(addon.getLocalizedString(30261), 'movies','trending'),
		build_item(addon.getLocalizedString(30211), 'movies','popularity'),
		build_item(addon.getLocalizedString(30262), 'movies','popular'),
		build_item(addon.getLocalizedString(30136), 'movies','aired'),
		build_item(addon.getLocalizedString(30139), 'movies','dubbed'),
		build_item(addon.getLocalizedString(30137), 'movies','dateadded'),
		build_item(addon.getLocalizedString(30210), 'a-z','movies,'),
		build_item(addon.getLocalizedString(30209), 'genres','movies'),
		build_item(addon.getLocalizedString(30257), 'countries','movies'),
		build_item(addon.getLocalizedString(30259), 'languages','movies'),
		build_item(addon.getLocalizedString(30256), 'years','movies'),
		build_item(addon.getLocalizedString(30255), 'studios','movies')
	],
	'series': [
		build_item(addon.getLocalizedString(30261), 'series','trending'),
		build_item(addon.getLocalizedString(30211), 'series','popularity'),
		build_item(addon.getLocalizedString(30262), 'series','popular'),
		build_item(addon.getLocalizedString(30136), 'series','aired'),
		build_item(addon.getLocalizedString(30139), 'series','dubbed'),
		build_item(addon.getLocalizedString(30137), 'series','dateadded'),
		build_item(addon.getLocalizedString(30210), 'a-z','series,'),
		build_item(addon.getLocalizedString(30209), 'genres','series'),
		build_item(addon.getLocalizedString(30257), 'countries','series'),
		build_item(addon.getLocalizedString(30259), 'languages','series'),
		build_item(addon.getLocalizedString(30256), 'years','series'),
		build_item(addon.getLocalizedString(30255), 'studios','series')
	],
	'concerts': [
		build_item(addon.getLocalizedString(30261), 'concerts','trending'),
		build_item(addon.getLocalizedString(30211), 'concerts','popularity'),
		build_item(addon.getLocalizedString(30262), 'concerts','popular'),
		build_item(addon.getLocalizedString(30136), 'concerts','aired'),
		build_item(addon.getLocalizedString(30137), 'concerts','dateadded'),
		build_item(addon.getLocalizedString(30210), 'a-z','concerts,'),
		build_item(addon.getLocalizedString(30209), 'genres','concerts'),
		build_item(addon.getLocalizedString(30257), 'countries','concerts'),
		build_item(addon.getLocalizedString(30259), 'languages','concerts'),
		build_item(addon.getLocalizedString(30256), 'years','concerts'),
		build_item(addon.getLocalizedString(30255), 'studios','concerts')
	]
}

if action and action[0] == 'movies': mos = 'movie'
elif action and action[0] == 'series': mos = 'tvshow'
else: mos = 'concert'

if 'action' in nparams and nparams['action'] == 'related' and 'id' in nparams:
	get_related(nparams['id'])
elif 'action' in nparams and nparams['action'] == 'similar' and 'id' in nparams:
	get_similar(nparams['id'])
elif 'action' in nparams and nparams['action'] == 'trailer' and 'id' in nparams:
	play_trailer(nparams['id'])
elif action is None:
	for c in menu['root']:
		render_item(c)
elif action[0] == 'csfd':
	get_csfd_tips()
elif action[0] == 'csfdtopf':
	get_csfd_topf(action_value[0])
elif action[0] == 'csfdtops':
	get_csfd_tops(action_value[0])
elif action[0] == 'folder':
	if action_value[0] in menu:
		for c in menu[action_value[0]]:
			render_item(c)
elif action[0] == 'movies' or action[0] == 'series' or action[0] == 'concerts':
	if action_value[0] == 'popular':
		data = get_media_data('/api/media/filter/all?sort=playCount&type=%s&order=desc&page=%s'%(mos,page),'')
	elif action_value[0] == 'popularity':
		data = get_media_data('/api/media/filter/all?sort=popularity&type=%s&order=desc&page=%s'%(mos,page),'')
	elif action_value[0] == 'trending':
		data = get_media_data('/api/media/filter/all?sort=trending&type=%s&order=desc&page=%s'%(mos,page),'')
	elif action_value[0] == 'aired':
		data = get_media_data('/api/media/filter/news?sort=dateAdded&type=%s&order=desc&days=365&page=%s'%(mos,page),'')
	elif action_value[0] == 'dateadded':
		data = get_media_data('/api/media/filter/all?sort=dateAdded&type=%s&order=desc&page=%s'%(mos,page),'')
	elif action_value[0] == 'dubbed':
		data = get_media_data('/api/media/filter/newsDubbed?lang=cs&lang=sk&sort=dateAdded&type=%s&order=desc&days=365&page=%s'%(mos,page),'')
	elif 'genre' in action_value[0]:
		(t,g) = action_value[0].split(',')
		data = get_media_data('/api/media/filter/genre?sort=year&type=%s&order=desc&value=%s&page=%s'%(mos,g,page),'')
	elif 'studio' in action_value[0]:
		(t,g) = action_value[0].split(',')
		data = get_media_data('/api/media/filter/studio?sort=year&type=%s&order=desc&value=%s&page=%s'%(mos,g,page),'')
	elif 'year' in action_value[0]:
		(t,g) = action_value[0].split(',')
		data = get_media_data('/api/media/filter/year?sort=year&type=%s&order=desc&value=%s&page=%s'%(mos,g,page),'')
	elif 'country' in action_value[0]:
		(t,g) = action_value[0].split(',')
		data = get_media_data('/api/media/filter/country?sort=year&type=%s&order=desc&value=%s&page=%s'%(mos,g,page),'')
	elif 'language' in action_value[0]:
		(t,g) = action_value[0].split(',')
		data = get_media_data('/api/media/filter/language?sort=year&type=%s&order=desc&value=%s&page=%s'%(mos,g,page),'')
	elif 'a-z' in action_value[0]:
		(m,v) = action_value[0].split(',')
		data = get_media_data('/api/media/filter/startsWithSimple?type=%s&value=%s'%(mos,v),'')
		abc = True
	else:
		data = get_media_data('/api/media/filter/startsWithSimple?type=%s&value=%s&page=%s'%(mos,action_value[0],page),'')
		abc = True
	if 'data' in data: process_movies_series(data['data'])
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
	media = get_media_data('/api/media/filter/all/count/genres?type='+mos,'')
	if 'data' in media: process_genres(media['data'])
elif action[0] == 'studios':
	media = get_media_data('/api/media/filter/all/count/studios?type='+mos,'')
	if 'data' in media: process_studios(media['data'])
elif action[0] == 'years':
	media = get_media_data('/api/media/filter/all/count/years?type='+mos,'')
	if 'data' in media: process_years(media['data'])
elif action[0] == 'languages':
	media = get_media_data('/api/media/filter/all/count/languages?type='+mos,'')
	if 'data' in media: process_languages(media['data'])
elif action[0] == 'countries':
	media = get_media_data('/api/media/filter/all/count/countries?type='+mos,'')
	if 'data' in media: process_countries(media['data'])
elif action[0] == 'a-z':
	(m,v) = action_value[0].split(',')
	if m == 'movies': mos = 'movie'
	elif m == 'series': mos = 'tvshow'
	else: mos = 'concert'
	media = get_media_data('/api/media/filter/startsWithSimple/count/titles?type=%s&value=%s'%(mos,v),'')
	if 'data' in media: process_az(media['data'])
elif action[0] == 'listsearch':
	list_search()
elif action[0] == 'search':
	search()
elif action[0] == 'play' and action_value[0] != "" and name !="":
	play(action_value[0],name)

if len(client.GItem_lst[0]) == 0:
	render_item(build_item(None, ''))
#	client.showInfo('Nic nenalezeno')

