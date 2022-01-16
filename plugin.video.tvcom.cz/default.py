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
from Plugins.Extensions.archivCZSK.engine import client
import cookielib,urllib2
import re,util,datetime,json
from provider import ContentProvider
import xbmcprovider
import util
from Components.config import config

LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'tvcom.log')

def writeLog(msg, type='INFO'):
        try:
                f = open(LOG_FILE, 'a')
                dtn = datetime.datetime.now()
                f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
                f.close()
        except:
                pass

def showInfo(mmsg):
        client.add_operation("SHOW_MSG", {'msg': mmsg, 'msgType': 'info', 'msgTimeout': 4, 'canClose': True })
#       writeLog(mmsg)

def showError(mmsg):
        client.add_operation("SHOW_MSG", {'msg': mmsg, 'msgType': 'error', 'msgTimeout': 4, 'canClose': True })
#       writeLog(mmsg,'ERROR')

class TvcomContentProvider(ContentProvider):

	def __init__(self, username=None, password=None, filter=None, tmp_dir='/tmp'):
		ContentProvider.__init__(self, 'tvcom.cz', 'https://www.tvcom.cz', username, password, filter, tmp_dir)
		self.cp = urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())
		self.init_urllib()

	def init_urllib(self):
		opener = urllib2.build_opener(self.cp)
		urllib2.install_opener(opener)

	def capabilities(self):
		return ['categories', 'resolve', 'search']

	def search(self,keyword):
		result = []
		headers = {"referer": self.base_url}
		data = util.request("https://archivczsk.eu/api/tvcom.php?search=%s" % urllib2.quote(keyword), headers=headers)
		items = json.loads(data)
		for item in items['items']:
			itm=self.video_item()
			id = re.search("\/([0-9]+)\-.*?.htm", item['url'], re.DOTALL)
			if id:
				itm['img']='https://tvcom-static.ssl.cdn.cra.cz/VideoPicture/'+str(item['date'])[0:4]+'/'+str(item['date'])[4:6]+'/'+str(item['date'])[6:8]+'/b'+id.group(1)+'.png?v=637774123360000000'
			itm['url']=item['url']
			itm['title']=str(item['date'])[6:8]+"."+str(item['date'])[4:6]+"."+str(item['date'])[0:4]+" "+str(item['date'])[8:10]+":"+str(item['date'])[10:12]+" ["+item['sport']+"] "+item['name']
			itm['plot']=itm['title']
			result.append(itm)
		return result

	def categories(self):
		result = []
		today = datetime.datetime.today()
		for day in range(0,-10,-1):
			doy = today + datetime.timedelta(days=day)
			result.append(self.dir_item(doy.strftime('%d.%m.%Y'),'https://tvcom-dynamic.ssl.cdn.cra.cz/Json/Tvcom.Cz/GetDayListCalednar/'+doy.strftime('%Y-%m-%d')+'/'))
		result.append(self.dir_item('Další','fr=-10'))
		return result

	def list(self, url):
		result = []
		if 'fr=' in url:
			today = datetime.datetime.today()
			tmp, fr = url.split("fr=")
			fr = int(fr)
			for day in range(fr,fr-10,-1):
				doy = today + datetime.timedelta(days=day)
				result.append(self.dir_item(doy.strftime('%d.%m.%Y'),'https://tvcom-dynamic.ssl.cdn.cra.cz/Json/Tvcom.Cz/GetDayListCalednar/'+doy.strftime('%Y-%m-%d')+'/'))
			result.append(self.dir_item('Další','fr=%s'%(fr-10)))
		if 'GetDayList' in url:
			headers = {"referer": self.base_url}
			httpdata = util.request(url, headers=headers)
			items = json.loads(httpdata)
			if "Data" in items:
				for item in items['Data']:
					itm=self.video_item()
					itm['url']=item['Url']
					itm['title']=item['Time']+" ["+item['Sport']+"] "+item['Name']
					itm['plot']=item['Name']
					itm['sort']=item['SortDateTime']
					id = re.search("\/([0-9]+)\-.*?.htm", itm['url'], re.DOTALL)
					if id:
						itm['img']='https://tvcom-static.ssl.cdn.cra.cz/VideoPicture/'+str(itm['sort'])[0:4]+'/'+str(itm['sort'])[4:6]+'/'+str(itm['sort'])[6:8]+'/b'+id.group(1)+'.png?v=637774123360000000'
					# itm['img']=img
					result.append(itm)
			result = sorted(result, key=lambda x:int(x['sort']))
			return result
		return result

	def resolve(self, item, captcha_cb=None, select_cb=None):
		item = item.copy()
		result = []
		headers = {"referer": self.base_url}
		httpdata = util.request(self.base_url+item['url'], headers=headers)
		items = re.compile("programDuration: (.*?),.*?programName: '(.*?)'.*?hls.*?src: '(.*?)\.m3u8'", re.DOTALL).findall(httpdata)
		for dur,name,link in items:
			item = self.video_item()
			item['surl'] = name
			item['title'] = name
			# item['quality'] = res
			# item['headers'] = {"referer": self.base_url}
			item['url'] = link+".m3u8"
			result.append(item)
		# result = sorted(result, key=lambda x:int(x['quality']), reverse=True)
		if len(result) > 0 and select_cb:
			return select_cb(result)
		return result

__scriptid__ = 'plugin.video.tvcom.cz'
__scriptname__ = 'tvcom.cz'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__ = __addon__.getLocalizedString

settings = {'quality':__addon__.getSetting('quality')}

provider = TvcomContentProvider()

#print("PARAMS: %s"%params)

xbmcprovider.XBMCMultiResolverContentProvider(provider, settings, __addon__, session).run(params)
