# -*- coding: UTF-8 -*-
# /*
# *  Copyright (C) 2020 Michal Novotny https://github.com/misanov
# *
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
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.tools.util import toString
from Plugins.Extensions.archivCZSK.engine import client

import cookielib,urllib2,urlparse,re,rfc822,time,util,resolver,json,datetime
from provider import ContentProvider
from provider import ResolveException
import xbmcprovider
import util

ytinfo = "https://www.youtube.com/get_video_info?video_id="

def writeLog(msg, type='INFO'):
	try:
		from Components.config import config
		f = open(os.path.join(config.plugins.archivCZSK.logPath.getValue(),'yt.log'), 'a')
		dtn = datetime.datetime.now()
		f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
		f.close()
	except:
		pass

class YTContentProvider(ContentProvider):

	def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
		ContentProvider.__init__(self, 'YouTube', 'https://youtube.com/', username, password, filter, tmp_dir)
		self.cp = urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())
		self.init_urllib()

	def init_urllib(self):
		opener = urllib2.build_opener(self.cp)
		urllib2.install_opener(opener)

	def capabilities(self):
		return ['categories', 'resolve', 'search']

	def search(self, keyword):
		return self.list(self.base_url+'results?search_query='+urllib2.quote(keyword))

	def categories(self):
		result = self.load_channels()
		return result

	def save_channel(self,name,url):
		max_history = __addon__.getSetting("channels") or 10
		cnt = 0
		history = []
		filename = addon_userdata_dir + "channels.txt"
		try:
			with open(filename, "r") as file:
				for line in file:
					item = line[:-1]
					history.append(item)
		except IOError:
			history = []
		history.insert(0,name+";"+url)
		with open(filename, "w") as file:
			for item in history:
				cnt = cnt + 1
				if cnt <= max_history:
					file.write('%s\n' % item)
		client.refresh_screen()

	def load_channels(self):
		history = []
		filename = addon_userdata_dir + "channels.txt"
		try:
			with open(filename, "r") as file:
				for line in file:
					item = line[:-1].split(";")
					history.append(self.dir_item(item[0], self.base_url+'channel/'+item[1]+'/videos?sort=dd'))
		except IOError:
			history = []
		return history

	def list(self, url):
		# ulozit kanal
		if 'save;' in url:
			item = url.split(";")
			self.save_channel(item[1],item[2])
			return []

		# kanal
		if '/channel/' in url:
			headers = {"cookie": "CONSENT=YES+CZ.cs+V10+BX; GPS=1" }
			httpdata = util.request(url,headers=headers)
			return self.parseChannel(httpdata)

		# kanal dalsi
		if 'browse_ajax?ctoken=' in url:
			headers = {"cookie": "CONSENT=YES+CZ.cs+V10+BX; GPS=1", "referer": "https://www.youtube.com", "x-youtube-client-name": "1", "x-youtube-client-version": "2.20201110.02.00"}
			httpdata = util.request(url, headers=headers)
			return self.parseChannelNext(httpdata)

		# hledat v kanalu
		#https://www.youtube.com/channel/{kanal_url}/search?query=

		# vyhledat
		if '?search' in url:
			headers = {"cookie": "CONSENT=YES+CZ.cs+V10+BX; GPS=1" }
			httpdata = util.request(url,headers=headers)
			return self.parseSearch(httpdata)
			
		return []

	def parseChannelNext(self, httpdata):
		result = []
		data = json.loads(httpdata)
		videos = data[1]["response"]["continuationContents"]["gridContinuation"]["items"]
		for video in videos:
			if "gridVideoRenderer" in video.keys():
				video_data = video.get("gridVideoRenderer", {})
				if video_data["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["style"] == "UPCOMING": continue
				item = self.video_item()
				item['title'] = video_data.get("title", {}).get("runs", [[{}]])[0].get("text", None)
				item['url'] = self.base_url+'watch?v='+video_data.get("videoId", None)
				item['img'] = 'https://i.ytimg.com/vi/'+video_data.get("videoId", 0)+'/0.jpg'
				item['plot'] = video_data.get("title", {}).get("accessibility",{}).get("accessibilityData",{}).get("label","")
				result.append(item)
		try:
			ctoken=data[1]["response"]["continuationContents"]["gridContinuation"]["continuations"][0]["nextContinuationData"]["continuation"]
			result.append(self.dir_item('Dalsi', 'https://www.youtube.com/browse_ajax?ctoken='+ctoken))
		except:
			pass
		return result

	def parseChannel(self, httpdata):
		result = []
		try:
			start = (httpdata.index('window["ytInitialData"]') + 26)
		except:
			start = (httpdata.index('var ytInitialData = ') + 20)
		end = httpdata.index("};", start) + 1
		json_str = httpdata[start:end]
		data = json.loads(json_str)
		try:
			videos = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["gridRenderer"]["items"]
		except:
			from Screens.MessageBox import MessageBox
			session.open(MessageBox, 'Kanal nenalezen', MessageBox.TYPE_INFO, timeout=8)
			return []
		for video in videos:
			if "gridVideoRenderer" in video.keys():
				video_data = video.get("gridVideoRenderer", {})
				if video_data["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["style"] == "UPCOMING": continue
				item = self.video_item()
				item['title'] = video_data.get("title", {}).get("runs", [[{}]])[0].get("text", None)
				item['url'] = self.base_url+'watch?v='+video_data.get("videoId", None)
				item['img'] = 'https://i.ytimg.com/vi/'+video_data.get("videoId", 0)+'/0.jpg'
				item['plot'] = video_data.get("title", {}).get("accessibility",{}).get("accessibilityData",{}).get("label","")
				result.append(item)
		try:
			ctoken=data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["gridRenderer"]["continuations"][0]["nextContinuationData"]["continuation"]
			result.append(self.dir_item('Dalsi', 'https://www.youtube.com/browse_ajax?ctoken='+ctoken))
		except:
			pass
		return result

	def parseSearch(self, httpdata):
		result = []
		start = (httpdata.index("ytInitialData") + len("ytInitialData") + 3)
		end = httpdata.index("};", start) + 1
		json_str = httpdata[start:end]
		data = json.loads(json_str)
		videos = []
		for section in data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]:
			try:
				for item in section["itemSectionRenderer"]["contents"]:
					if "videoRenderer" in item:
						videos = section["itemSectionRenderer"]["contents"]
						break
			except:
				pass
		for video in videos:
			if "videoRenderer" in video.keys():
				video_data = video.get("videoRenderer", {})
				item = self.video_item()
				item['title'] = video_data.get("title", {}).get("runs", [[{}]])[0].get("text", None)
				channel = video_data.get("longBylineText", {}).get("runs", [[{}]])[0].get("text", "")
				channelUrl = video_data.get("longBylineText", {}).get("runs", [[{}]])[0].get("navigationEndpoint", {}).get("browseEndpoint", {}).get("browseId","")
				item['url'] = self.base_url+'watch?v='+video_data.get("videoId", None)
				item['img'] = 'https://i.ytimg.com/vi/'+video_data.get("videoId", 0)+'/0.jpg'
				descr = ""
				try:
					for desc in video_data.get("descriptionSnippet", {}).get("runs", [{}]):
						descr+=desc["text"]
				except:
					pass
				duration = video_data.get("lengthText", {}).get("simpleText", 0)
				views = video_data.get("viewCountText", {}).get("simpleText", 0)
				item['plot'] = "[" + str(duration) + "] - " + str(channel) + " : " + str(views) + " - " + descr
				item['menu'] = {}
				item['menu']['Videa kanalu: '+channel] = {'list': self.base_url+'channel/'+channelUrl+'/videos?sort=dd', 'action-type':'list'}
				item['menu']['Ulozit kanal: '+channel] = {'list': 'save;'+channel+';'+channelUrl, 'action-type':'list'}
				result.append(item)
		return result

	def resolve(self, item, captcha_cb=None, select_cb=None):
		item = item.copy()
		result = []
		import youtube_dl
		from enigma import getDesktop
		ydl_opts = {}
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			meta = ydl.extract_info(self._url(item['url']), download=False)
		if not meta: return []
		full_ids = ["18","22","35","37","38","91","92","94","300"]
		audio_url = ""
		audio_size = 0
		for format in meta.get("formats",[]):
			if 'DASH' in format.get("format",""): continue	# dash neumime
			url = ""
			split = "p"
			filesize = ""
			if format.get("format_id","0") == "140" and format.get("url",""):
				audio_url = format.get("url")
				audio_size = format.get("filesize",0)
				continue
			if format.get("format_id","0") in full_ids and format.get("url",""):
				url = format.get("url","")
				if format.get("filesize",0): filesize = str(round(format.get("filesize",0)/1048576)) + "MB"
			elif format.get("height","") > 300 and format.get("url","") and audio_url:  # nezobrazovat zbytecne mensi nez 300p
				url = format.get("url")+"&suburi="+audio_url
				if format.get("filesize",0): filesize = str(round((format.get("filesize",0)+audio_size)/1048576)) + "MB"
				split = "s"
			if not url: continue
			if format.get("height",0) > getDesktop(0).size().height(): continue  # nezobrazovat vetsi rozliseni nez je obrazovka
			item = self.video_item()
			item['url'] = url
			item['quality'] = str(format.get("height",0)) + split
			fsplit = format.get("format","").split(' - ')
			fsearch = re.search("\((.*?)\)", fsplit[1], re.S)
			if fsearch: title = fsearch.group(1)
			else: title = fsplit[1]
			item['title'] = "[" + title + " " + format.get("vcodec","") + " " + filesize + "]"  # zobrazime i ruzne kodeky at si kazdy vybere
			result.append(item)
		return list(reversed(result))

__scriptid__ = 'plugin.video.yt'
__scriptname__ = 'YouTube'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__ = __addon__.getLocalizedString
addon_userdata_dir = __addon__.getAddonInfo('profile')+'/'
settings = {'quality':__addon__.getSetting('quality')}
provider = YTContentProvider(tmp_dir='/tmp')
xbmcprovider.XBMCMultiResolverContentProvider(provider, settings, __addon__, session).run(params)
