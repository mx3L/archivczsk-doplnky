# -*- coding: utf-8 -*-
import urllib2,urllib,re,os

__baseurl__ = 'http://tv.sme.sk'
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.client import add_dir, add_video
from Plugins.Extensions.archivCZSK.engine.client import log as ACZSKLog

def addDir(name, url, mode, image, page=None, kanal=None, infoLabels={}, menuItems={}, video_item=False):
    params = {'name':name, 'url':url, 'mode':mode, 'page':page, 'kanal':kanal}
    add_dir(name, params, image, infoLabels=infoLabels, menuItems=menuItems, video_item = video_item)

def addLink(name, url, image, *args, **kwargs):
    add_video(name, url, None, image)

import HTMLParser
from datetime import datetime,timedelta

__baseurl__ = 'http://tv.sme.sk'
__piano_d__ = '?piano_d=1'
__addon__ = ArchivCZSK.get_xbmc_addon('plugin.video.tv.sme.sk')
__cwd__ = __addon__.getAddonInfo('path')
__scriptname__ = 'plugin.video.tv.sme.sk'
icon = os.path.join(__cwd__, 'icon.png')
nexticon = os.path.join(__cwd__, 'nextpage.png') 
video_quality = int(__addon__.getSetting('quality'))

VQ_SELECT = 0
VQ_SD = 1
VQ_HD = 2


def log(msg, level='debug'):
	if type(msg).__name__=='unicode':
		msg = msg.encode('utf-8','ignore')
	if level == 'debug':
		logfnc = ACZSKLog.debug
	else:
		logfnc = ACZSKLog.error
	logfnc("[%s] %s"%(__scriptname__,msg))

def logDbg(msg):
	log(msg,level='debug')

def logErr(msg):
	log(msg,level='error')

def getDataFromUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data

def getHtmlFromUrl(url):
	return getDataFromUrl(url).decode("windows-1250")

def getXmlFromUrl(url):
	return getDataFromUrl(url).decode("utf-8")

def listCategories():
	logDbg("listCategories()")
	addDir(u'[B]Všetky videá[/B]',__baseurl__+'/hs/',3,icon,'')
	addDir(u'[B]Spravodajské[/B]',__baseurl__+'/vr/118/spravodajske/',3,icon,'')
	addDir(u'[B]Publicistické[/B]',__baseurl__+'/vr/117/publicisticke/',3,icon,'')
	addDir(u'[B]Zábavné[/B]',__baseurl__+'/vr/119/zabavne/',3,icon,'')
	addDir(u'[B]Zoznam relácií (aktívne)[/B]',__baseurl__+'/relacie/',1,icon,'')
	addDir(u'[B]Zoznam relácií (archív)[/B]',__baseurl__+'/relacie/',2,icon,'')

def listShows(url,section):
	logDbg("listShows("+section+")")
	httpdata = getHtmlFromUrl(url)
	match = re.compile(u'<h2 class="light">'+section+'</h2>(.+?)<div class="cb"></div></div>', re.DOTALL).findall(httpdata)
	if match:
		items = re.compile('img src="(.*?)" alt=.+?<h2><a href="(.+?)">(.+?)</a></h2>', re.DOTALL).findall(match[0])
		for img,link,name in items:
			link = __baseurl__+link
			addDir(name,link,3,img,'')
	else:
		logErr("List of TV shows not found!")

def listEpisodes(url):
	logDbg("listEpisodes()")
	httpdata = getHtmlFromUrl(url)
	match = re.compile('<div class="list">(.+?)<div id="otherartw" class="pages"', re.DOTALL).findall(httpdata)
	if match:
		items = re.compile('src="(.*?)" alt=.+?<h2>.*?<a href="(.+?)">(.+?)</a>.+?<div class="time">(.+?)</div>(.*?)</div>', re.DOTALL).findall(match[0])
		for img,link,name,date,desc in items:
			link = __baseurl__+link
			# remove new lines
			desc=desc.replace("\n", "")
			if len(desc):
				match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(desc)
				if match:
					desc = match[0]
					# remove optional <span>...</span> tag
					if "<span" in desc:
						match = re.compile('<span.*</span>(.*)', re.DOTALL).findall(desc)
						if match:
							desc = match[0]
							logDbg("new desc: "+desc)
			addDir('('+date+') '+name,link,5,img,desc, video_item=True)
		items = re.compile('<div class="otherart r"><h5><a href="(.+?)">(.+?)</a>', re.DOTALL).findall(httpdata)
		if items:
			link, name = items[0]
			link = __baseurl__+link
			h = HTMLParser.HTMLParser()
			addDir('[B]'+h.unescape(name)+'[/B]',link,3,nexticon,'')
	else:
		logErr("List of episodes not found!")

def getVideoUrl(url):
	logDbg("getVideoUrl()")
	logDbg("\tPage url="+url)
	httpdata = getHtmlFromUrl(url)
	match = re.compile('_fn\(t\)(.+?)</script>', re.DOTALL).findall(httpdata)
	if match:
		items = re.compile('var rev=(.+?);.+?"file", escape\("(.+?)"\+ rev \+"(.+?)"\)\);', re.DOTALL).findall(match[0])
		if items:
			rev,link1,link2 = items[0]
			link = link1+str(rev)+link2
			logDbg("\tPlaylist url="+link)
			xmldata = getXmlFromUrl(link)
			item = re.compile('<title>(.+?)</title>.+?<location>(.+?)</location>.+?<image>(.+?)</image>', re.DOTALL).findall(xmldata)
			if item:
				title, link, img = item[0]
				logDbg("\tVideo url="+link)
				return link
			else:
				logErr("Video location not found!")
		else:
			logErr("Video informations not found!")
	else:
		logErr("Player script not found!")
	return None

def playEpisode(url1):
	logDbg("playEpisode()")
	logDbg("\turl="+url1)
	logDbg("\tVideo quality: "+str(video_quality))
	url1_is_hd = False
	url2 = ''
	httpdata = getHtmlFromUrl(url1+__piano_d__)
	match = re.compile('<div class="v-podcast-box js-v-podcast-box">(.+?)<div class="(?:v-clanok|v-perex)">', re.DOTALL).findall(httpdata)
	if match:
		items = re.compile('</label><a href="(.+?)" class="hd-btn(.+?)"></a>', re.DOTALL).findall(match[0])
		if items:
			url2, hd_btn_off = items[0]
			url2 = __baseurl__ + url2
			if len(hd_btn_off) == 0:
				url1_is_hd = True
		else:
			logDbg("Alternative video quality not found.")
	else:
		logErr("podcast-box not found!")
	
	if len(url2):
		if url1_is_hd:
			url_sd=url2
			url_hd=url1
		else:
			url_sd=url1
			url_hd=url2
		logDbg("\tHD URL: "+url_hd)
		logDbg("\tSD URL: "+url_sd)
		if video_quality == VQ_SELECT:
			addLink('[HD] ' + name , getVideoUrl(url_hd + __piano_d__), None)
			addLink('[SD] ' + name , getVideoUrl(url_sd + __piano_d__), None)
		elif video_quality == VQ_SD:
			addLink('[SD] ' + name , getVideoUrl(url_sd + __piano_d__), None)
		else:
			addLink('[HD] ' + name , getVideoUrl(url_hd + __piano_d__), None)
	else:
		addLink('[HD] ' + name , getVideoUrl(url1 + __piano_d__), None)
	return
url=None
name=None
desc=None
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
try:
	desc=urllib.unquote_plus(params["desc"])
except:
	pass

logDbg("Mode: "+str(mode))
logDbg("URL: "+str(url))
#logDbg("Name: "+str(name))
logDbg("Desc: "+str(desc))

if mode==None or url==None or len(url)<1:
	listCategories()
	
elif mode==1:
	listShows(url,u'Aktívne')

elif mode==2:
	listShows(url,u'Archív')

elif mode==3:
	listEpisodes(url)

elif mode==5:
	playEpisode(url)
