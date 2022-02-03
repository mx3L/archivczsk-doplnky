# -*- coding: utf-8 -*-

from __future__ import print_function
import sys, os
sys.path.append( os.path.dirname(__file__)  )
from Maxim import Maxim
import base64

try:
	from urllib.parse import quote_plus
except:
	from urllib import quote_plus

from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.tools.util import toString
from Plugins.Extensions.archivCZSK.engine import client

import util
from provider import ContentProvider
import xbmcprovider
from datetime import datetime
from datetime import timedelta
import requests
import time
import json
from lameDB import lameDB

######### contentprovider ##########

proxy_url = "http://127.0.0.1:18080"

# #################################################################################################

def install_antiktv_proxy():
	try:
		response = requests.get( proxy_url + '/info', timeout=2 )
		
		if response.text.startswith("antiktv_proxy"):
			return True
	except:
		pass
	
	src_file = os.path.dirname(__file__) + '/antiktv_proxy.sh'
	os.chmod( src_file, 0o755 )
	try:
		os.symlink( src_file, '/etc/init.d/antiktv_proxy.sh' )
	except:
		pass
	
	try:
		os.system('update-rc.d antiktv_proxy.sh defaults')
		os.system('/etc/init.d/antiktv_proxy.sh start')
		time.sleep(1)
	except:
		pass

	for i in range(5):
		try:
			response = requests.get( proxy_url + '/info', timeout=1 )
		except:
			response = None
			time.sleep(1)
			pass
		
		if response != None and response.text.startswith("antiktv_proxy"):
			return True
			
	
	return False

# #################################################################################################

def build_service_ref( service, player_id ):
	return player_id + ":0:{:X}:{:X}:{:X}:{:X}:{:X}:0:0:0:".format( service.ServiceType, service.ServiceID, service.Transponder.TransportStreamID, service.Transponder.OriginalNetworkID, service.Transponder.DVBNameSpace )

# #################################################################################################

def service_ref_get( lamedb, channel_name, player_id ):

	skylink_freq = [ 11739, 11778, 11856, 11876, 11934, 11954, 11973, 12012, 12032, 12070, 12090, 12110, 12129, 12168, 12344, 12363 ]
	antik_freq = [ 11055, 11094, 11231, 11283, 11324, 11471, 11554, 11595, 11637, 12605 ]
	
	def cmp_freq( f, f_list ):
		f = int(f/1000)
		
		for f2 in f_list:
			if abs( f - f2) < 5:
				return True
	
		return False

	try:
		services = lamedb.Services[ lamedb.name_normalise( channel_name ) ]
		
		# try position 23.5E first
		for s in services:
			if s.Transponder.Data.OrbitalPosition == 235 and cmp_freq( s.Transponder.Data.Frequency, skylink_freq ):
				return build_service_ref(s, player_id)

		# then 16E
		for s in services:
			if s.Transponder.Data.OrbitalPosition == 160 and cmp_freq( s.Transponder.Data.Frequency, antik_freq ):
				return build_service_ref(s, player_id)

		for s in services:
			if s.Transponder.Data.OrbitalPosition == 235:
				return build_service_ref(s, player_id)

		# then 16E
		for s in services:
			if s.Transponder.Data.OrbitalPosition == 160:
				return build_service_ref(s, player_id)

		# then 0,8W
		for s in services:
			if s.Transponder.Data.OrbitalPosition == -8:
				return build_service_ref(s, player_id)

		# then 192
		for s in services:
			if s.Transponder.Data.OrbitalPosition == 192:
				return build_service_ref(s, player_id)

		# take the first one
		for s in services:
			return build_service_ref(s, player_id)

	except:
		pass
	
	return player_id + ":0:0:0:0:0:0:0:0:0:"


# #################################################################################################
		
class antiktvContentProvider(ContentProvider):
	maxim = None
	
	# #################################################################################################
	
	def __init__(self, username=None, password=None, device_id=None, filter=None, tmp_dir='/tmp'):
		ContentProvider.__init__(self, 'antiktv', '/', username, password, filter, tmp_dir)
		
		self.username = username
		self.password = password
		self.device_id = device_id
		
		if len( username ) > 0 and len( password ) > 0 and len( device_id ) > 0:
			self.maxim = Maxim( username, password, device_id )

		self.channels_archive_ids = None
		self.channels = { "tv": None, "radio": None, "cam": None }
	
	# #################################################################################################

	def capabilities(self):
		return ['login', 'categories', 'resolve', '!download']
	
	# #################################################################################################
	
	def encode_url( self, url, prefix="" ):
		if url.startswith("http"):
			return proxy_url + "/getm3u8/" + prefix + base64.b64encode( bytes( url.encode("utf-8") ) ).decode("utf-8")
		else:
			return url

	# #################################################################################################

	def login(self):
		if self.maxim == None:
			device_id = __addon__.getSetting( 'device_id' )
			
			if len( self.username ) == 0 or len( self.password ) == 0:
				client.showInfo("Nie su zadané prihlasovacie údaje!\nTeraz sa vrátite do zoznamu pluginov. V ňom nechajte vybraný plugin Antik TV, stlačte tlačidlo MENU a vyberte NASTAVENIA. V nich budete mať možnosť zadať potrebné prihlasovacie údaje.")
				return False
			
			if len( self.device_id ) == 0:
				self.device_id = Maxim.create_device_id()
				__addon__.setSetting( 'device_id', self.device_id )
			
			self.maxim = Maxim( self.username, self.password, self.device_id )

		ret, data2 = self.maxim.check_login("device")

		if ret == False:
			ret, msg = self.maxim.register_device_id()
			
			if ret == False:
				client.showInfo("Registrácia zariadenia zlyhala:\n" + msg )
				return False
			else:
				client.add_operation('SHOW_MSG', { 'msg': "Zariadenie zaregistrované:\n" + msg, 'msgType': 'info', 'msgTimeout': 0, 'canClose': True, })
		else:
			if data2["is_anonymous"] == True:
				ret, msg = self.maxim.register_device_id(True)

				if ret == False:
					client.showInfo("Priradenie zariadenia k aktuálnemu účtu zlyhalo:\n" + msg )
					return False
				else:
					client.add_operation('SHOW_MSG', { 'msg': "Zariadenie pridelené k aktuálnemu účtu:\n" + msg, 'msgType': 'info', 'msgTimeout': 0, 'canClose': True, })

		# we have login, password and device_id - check login credentials
		ret, data1 = self.maxim.check_login()
		
		if ret == False:
			client.showInfo("Nesprávne prihlasovacie meno alebo heslo!\nTeraz sa vrátite do zoznamu pluginov. V ňom nechajte vybraný plugin Antik TV, stlačte tlačidlo MENU a vyberte NASTAVENIA. V nich budete mať možnosť opraviť prihlasovacie údaje.")
			return False

		if install_antiktv_proxy() == False:
			client.showInfo("Nepodarilo sa spustiť AntikTV HTTP proxy!\nBez spustenia tejto služby nefunguje prehrávanie programov. Reštartujte prijímač a skúste znovu spustiť plugin.")
			return False
		
		return True
	
	# #################################################################################################
	
	def unregister_device( self ):
		answer = client.getYesNoInput(session, "Naozaj odregistrovať toto zariadenie z používateľského účtu?")
		
		if answer == False:
			return "Operácia zrušená používateľom"

		ret, msg = self.maxim.unregister_device_id()
		
		if ret == False:
			return "Odhlásanie zlyhalo: " + msg
		
		try:
			response = requests.get( proxy_url + '/reloadconfig' )
		except:
			pass
		
		self.maxim = None
		__addon__.setSetting( 'device_id', "" )
		client.showInfo("Zariadenie odregistrované: " + msg)

	# #################################################################################################
	
	def categories(self):
		result = []
		result.append(self.dir_item("TV Stanice", "#tv" ))
		result.append(self.dir_item("Rádiá", "#radio" ))
		result.append(self.dir_item("Kamery", "#cam" ))
		result.append(self.dir_item("Filmy", "#vod" ))
		result.append(self.dir_item("Archív", "#archive" ))
		
		if __addon__.getSetting('enable_extra') == "true":
			result.append(self.dir_item("Špeciálna sekcia", "#extra" ))
			
		return result

	# #################################################################################################

	def list(self, url):
		self.info("list %s" % url)
		
		if url == '#tv':
			return self.show_tv()
		elif url == '#radio':
			return self.show_radiocam( "radio" )
		elif url == '#cam':
			return self.show_radiocam( "cam" )
		elif url == '#vod':
			return self.show_vod()
		elif url == '#archive':
			result = []
			if self.maxim != None:
				result.append(self.dir_item("Podľa staníc", "#archive_channels" ))
				result.append(self.dir_item("Podľa žánru", "#archive_genres" ))
				
			return result
		elif url == '#extra':
			return self.show_extra_menu()
		elif url == '#archive_channels':
			return self.show_archive_channels()
		elif url == '#archive_genres':
			return self.show_archive_genres()
		elif url.startswith( '#archive_channel_dates#'):
			return self.show_archive_channel_dates( url[23:] )
		elif url.startswith( '#archive_epg#'):
			return self.show_archive_epg( url[13:] )
		elif url.startswith( '#archive_genre#'):
			return self.show_archive_genre( url[15:] )
		elif url.startswith( '#archive_serie#'):
			return self.show_archive_serie( url[15:] )
		elif url.startswith( '#archive_season#'):
			return self.show_archive_season( url[16:] )
		elif url.startswith( '#tv_cat#'):
			return self.show_tv_cat( url[8:] )
		elif url.startswith( '#vod_genre#'):
			return self.show_vod_genre( url[11:] )
		
		return []

	# #################################################################################################

	def get_extra_info( self, section ):
		data = self.maxim.get_account_info()

		result = ""

		if section == 1:
			x = data["account"]
			result += "Zákazník:\n"
			result += "Name: " + x["name"] + "\n"
			result += "E-mail: " + x["email"] + "\n"
			result += "Identifier: " + x["identifier"] + "\n"
			result += "\n"
		
		if section == 2:
			result += "Zaplatené balíky:\n"
			for x in data["packages"]:
				result += "Balík: " + x["name"] + "\nPlatnosť: " + x["valid"] + "\n\n"

		if section == 3:
			result += "Registrované zariadenia:\n"
			for service_type in data["devices"]:
				result += "Služba typu: " + service_type + "\n"
				for x in data["devices"][service_type]:
					result += "Device ID: " + x["id"] + ", HW: " + x["hw"] + ", OS: " + x["os"] + ", App info: " + x["app"] + "\n\n"

		return result

	# #################################################################################################

	def generate_bouquet( self, channel_type="tv" ):
		self.load_channel_list( channel_type )
		
		lamedb = lameDB("/etc/enigma2/lamedb")
		
		player_name = __addon__.getSetting('player_name')
		
		gst_blacklist = []
		
		if player_name == "3":
			player_id = "5001"
			gst_blacklist = [ "HBO", "HBO 2", "HBO 3", "Cinemax", "Cinemax 2" ]
		elif player_name == "1":
			player_id = "5001"
		elif player_name == "2":
			player_id = "5002"
		else:
			player_id = "4097"

		file_name = "userbouquet.antiktv_" + channel_type + ".tv"
		
		with open( "/etc/enigma2/" + file_name, "w" ) as f:
			f.write( "#NAME Antik " + channel_type + "\n")
			for cat in self.channels[channel_type]:
				f.write( "#SERVICE 1:64:0:0:0:0:0:0:0:0::" + cat + "\n")
				f.write( "#DESCRIPTION " + cat + "\n")

				for channel in self.channels[channel_type][cat]:
					if channel["url"] == None:
						continue
					
					url = self.encode_url( channel["url"] )
					url = quote_plus( url )
					
					if channel["name"] in gst_blacklist:
						service_ref = service_ref_get( lamedb, channel["name"], "5002" )
					else:
						service_ref = service_ref_get( lamedb, channel["name"], player_id )
						
					f.write( "#SERVICE " + service_ref + url + ":" + channel["name"] + "\n")
					f.write( "#DESCRIPTION " + channel["name"] + "\n")
		
		first_export = True
		with open( "/etc/enigma2/bouquets.tv", "r" ) as f:
			for line in f.readlines():
				if file_name in line:
					first_export = False
					break
		
		if first_export:
			with open( "/etc/enigma2/bouquets.tv", "a" ) as f:
				f.write( '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + file_name + '" ORDER BY bouquet' + "\n" )

		try:
			requests.get("http://127.0.0.1/web/servicelistreload?mode=2")
		except:
			pass
		
		return "userbouquet pre typ " + channel_type + " vygenerovaný"
			
	# #################################################################################################
	
	def show_extra_menu( self, section=None ):
		if self.maxim == None:
			return "Neregistrované zariadenie!"
		
		if section == None:
			# Main menu
			result = []
			
			item = self.video_item( "#extra#account" )
			item['title'] = "Používateľské konto"
			result.append( item )

			item = self.video_item( "#extra#packages" )
			item['title'] = "Predplatené balíky"
			result.append( item )

			item = self.video_item( "#extra#devices" )
			item['title'] = "Registrované zariadenia"
			result.append( item )

			item = self.video_item( "#extra#logout" )
			item['title'] = "Odregistrovať/odhlásiť toto zariadenie"
			result.append( item )

			item = self.video_item( "#" )
			item['title'] = "------------------------"
			result.append( item )

			item = self.video_item( "#extra#bouquet_tv" )
			item['title'] = "Vygenerovať userbouquet pre TV"
			result.append( item )

			item = self.video_item( "#extra#bouquet_radio" )
			item['title'] = "Vygenerovať userbouquet pre rádia"
			result.append( item )

			item = self.video_item( "#extra#bouquet_cam" )
			item['title'] = "Vygenerovať userbouquet pre kamery"
			result.append( item )
			
			return result
		elif section == '#account':
			return self.get_extra_info(1)
		elif section == '#packages':
			return self.get_extra_info(2)
		elif section == '#devices':
			return self.get_extra_info(3)
		elif section == '#bouquet_tv':
			return self.generate_bouquet()
		elif section == '#bouquet_radio':
			return self.generate_bouquet('radio')
		elif section == '#bouquet_cam':
			return self.generate_bouquet('cam')
		elif section == '#logout':
			return self.unregister_device()
		
	# #################################################################################################

	def show_archive_channels( self ):
		self.load_channel_list()
		result = []
		
		channels = self.channels["tv"]
		for cat in channels:
			for channel in channels[ cat ]:
				if channel["archive"] == True:
					item = self.dir_item( channel["name"], "#archive_channel_dates#" + channel["id_content"] )
					result.append(item)
		
		return result

	# #################################################################################################
	
	def show_archive_epg( self, id_content ):
		x = id_content.split('#')
		id_content = x[0]
		date_from = x[1]
		date_to = (datetime.strptime( date_from[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(days=1)).isoformat() + "+0100"

		epg_list = self.maxim.get_channel_epg( id_content, date_from, date_to )

		result = []
		for epg in epg_list:
			if "archived" in epg and epg["archived"] == True:
				# pridaj video
				item = self.video_item( "#archive_url#" + id_content + "#" + epg["start"] + "#" + epg["stop"] )
				
				epg_start = datetime.strptime( epg["start"][:19], "%Y-%m-%dT%H:%M:%S" )
				epg_stop = datetime.strptime( epg["stop"][:19], "%Y-%m-%dT%H:%M:%S" )
				title = "{:02}:{:02} - {:02d}:{:02d}".format(epg_start.hour, epg_start.minute, epg_stop.hour, epg_stop.minute)
				
				try:
					title = title + " - [I]" + str( epg["title"] ) + "[/I]"
				except:
					pass

				item["title"] = title
			
				try:
					item["img"] = epg["image"]
					item["plot"] = epg["description"]
				except:
					pass
				
				result.append( item )
		
		return result
			
		
	# #################################################################################################

	def show_archive_channel_dates( self, id_content ):
		d = datetime.now().replace( hour=0, minute=0, second=0, microsecond=0 )
		
		result = []
		
		for i in range(20):
			dx = d - timedelta(days=i)
			name = self.convert_date( dx.isoformat(), False )
			item = self.dir_item( name, "#archive_epg#" + id_content + "#" + dx.isoformat() + "+0100" )
			result.append(item)
		
		return result
			
		
	# #################################################################################################

	def show_archive_genres( self ):
		result = []
		
		genres = self.maxim.get_archive_genres()
		
		for genre in genres:
			self.info( "Genre: {}, id: {}".format( genre["title"], genre["id"] ) )
			result.append(self.dir_item( genre["title"], "#archive_genre#" + str( genre["id"] ) ) )
		
		return result

	# #################################################################################################

	def show_archive_genre( self, genre_id ):
		offset = 0
		x = genre_id.split('#')
		if len(x) > 1:
			offset = int(x[1])
		
		genre_id = x[0]

		result = []
		
		self.load_channel_list()
		
		archives, count = self.maxim.get_archive_by_genre( self.channels_archive_ids, genre_id, 20, offset )
		return self.parse_archives( archives, count, offset, "#archive_genre#" + str(genre_id), True )
	
	# #################################################################################################
	
	def show_archive_serie( self, serie_id ):
		offset = 0
		x = serie_id.split('#')
		if len(x) > 1:
			offset = int(x[1])
		
		serie_id = int(x[0])

		result = []
		
		self.load_channel_list()
			
		archives, count = self.maxim.get_archive_by_serie( self.channels_archive_ids, serie_id, 20, offset )
		return self.parse_archives( archives, count, offset, "#archive_serie#" + str(serie_id))

	# #################################################################################################

	def show_archive_season( self, serie_id ):
		offset = 0
		x = serie_id.split('#')
		if len(x) > 2:
			offset = int(x[2])
		
		serie_id = int(x[0])
		season_nr = int(x[1])

		result = []
		
		self.load_channel_list()
			
		archives, count = self.maxim.get_archive_by_season( self.channels_archive_ids, serie_id, season_nr, 20, offset )
		return self.parse_archives( archives, count, offset, "#archive_season#" + str(serie_id) + "#" + str(season_nr) )
		
	# #################################################################################################
	
	def convert_date( self, date_str, add_time=True ):
		day_names = [ "Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok", "Sobota", "Nedeľa" ]
		
		d = datetime.strptime( date_str[:19], "%Y-%m-%dT%H:%M:%S")
		day_name = day_names[ d.weekday() ]

		response = "{:02d}.{:02d} ({})".format( d.day, d.month, day_name )
		
		if add_time == True:
			response = "{} {:02d}:{:02d}".format( response, d.hour, d.minute )
			
		return response
	
	# #################################################################################################
	
	def convert_time( self, date_str, date2_str = None ):
		d = datetime.strptime( date_str[:19], "%Y-%m-%dT%H:%M:%S")
		response = "{:02d}:{:02d}".format( d.hour, d.minute )
		
		if date2_str != None:
			d = datetime.strptime( date2_str[:19], "%Y-%m-%dT%H:%M:%S")
			response += " - {:02d}:{:02d}".format( d.hour, d.minute )
			
		return response
	
	# #################################################################################################

	def parse_archives( self, archives, count, offset, next_tag, simple_title=False ):
		result = []
		
		for archive in archives:
			if "type_series" in archive:
				item = self.dir_item( str(archive["title"]), "#archive_serie#" + str( archive["type_series"]["id"] ) )
			elif "type_season" in archive:
				name = "Séria " + str( archive["type_season"]["season_number"] )
				try:
					name = name + ": " + archive["title"]
				except:
					pass
				
				serie_id = next_tag.split('#')[2]
				item = self.dir_item( name, "#archive_season#" + serie_id + "#" + str( archive["type_season"]["season_number"] ) )
			else:
				# pridaj video
				item = self.video_item( "#archive_url#" + archive["channel_id_content"] + "#" + archive["start"] + "#" + archive["stop"] )
				
				if simple_title == True:
					try:
						title = archive["title"]
					except:
						title = self.convert_date( archive["start"] )
				else:
					if next_tag.startswith( "#archive_genre#" ):
						title = self.convert_date( archive["start"] )

					try:
						title = title + " - [I]" + str(archive["title"]) + "[/I]"
					except:
						title = self.convert_date( archive["start"] )

					try:
						title = title + " [" + str(archive["channel"]) + "]"
					except:
						pass
					
				item["title"] = title
			
			try:
				item["img"] = archive["icon"]
				item["rating"] = archive["score"]
				
				if "type_series" in archive or "type_season" in archive:
					item["plot"] = archive["description"]
				else:
					item["plot"] = self.convert_date( archive["start"] ) + " [" + str( archive["channel"] ) + "]\n" + archive["description"]
					
			except:
				pass
			
			result.append( item )
		
		if count > offset + len( archives ):
			item = self.dir_item( "Ďalšie", next_tag + "#" + str( offset + len( archives ))  )
			item["type"] = 'next'
			result.append( item )

		return result
		
	# #################################################################################################
	
	def load_channel_list( self, channel_type="tv" ):
		if self.maxim == None:
			self.channels[channel_type] = {}
			return
		
		if self.channels[channel_type] != None:
			return
		
		filters = {}
		if __addon__.getSetting('enable_h265') == "false":
			filters["h265"] = "no"
			
		if __addon__.getSetting('enable_adult') == "false":
			filters["adult"] = "no"
		
		channels = self.maxim.get_channel_list( channel_type, filters )
		self.channels[channel_type] = channels
		
		if channel_type == "tv":
			result = []
			for cat in channels:
				for channel in channels[cat]:
					if channel["archive"] == True:
						result.append( channel["id_content"] )
		
			self.channels_archive_ids = result

	# #################################################################################################
	
	def show_tv( self ):
		self.load_channel_list()
		result = []

		for cat in self.channels["tv"]:
			result.append(self.dir_item( cat, "#tv_cat#" + cat ) )
				 
		return result

	# #################################################################################################

	def show_tv_cat( self, cat ):
		self.load_channel_list()
		result = []
		
		channels = self.channels["tv"]
		cat = cat.decode("utf-8")

		epg_list = []
		for channel in channels[ cat ]:
			epg_list.append( channel["id_content"] )
		
		epg_list = self.maxim.get_actual_epg( epg_list )
		
		for channel in channels[ cat ]:
			if channel["url"] == None:
				continue
			
			try:
				epg = epg_list[ channel["id_content"] ]["epg"][0]
				
				if "subtitle" in epg:
					epg_str = "  [I]" + epg["title"] + " - " + epg["subtitle"] + "[/I]"
				else:
					epg_str = "  [I]" + epg["title"] + "[/I]"
			except:
				epg = { "title": "", "desc": "" }
				epg_str = ""
		
			item = self.video_item( self.encode_url( channel["url"] ) )
			item["title"] = channel["name"] + epg_str
			item["quality"] = str(channel["resolution"]) + "p"
			try:
				item["plot"] = self.convert_time( epg["start"], epg["stop" ] ) + "\n"
				item["plot"] += epg["desc"]
			except:
				pass
			
			if "snapshot" in channel:
				item['img'] = channel["snapshot"]
			else:
				item['img'] = channel["logo"]
			result.append(item)

		return result

	# #################################################################################################

	def show_radiocam( self, channel_type ):
		self.load_channel_list( channel_type )
		result = []

		channels = self.channels[channel_type]
		for cat in channels:
			for channel in channels[ cat ]:
				if channel["url"] == None:
					continue
				
				item = self.video_item( self.encode_url( channel["url"] ) )
				item["title"] = channel["name"]
				
				if "snapshot" in channel:
					item['img'] = channel["snapshot"]
				else:
					item['img'] = channel["logo"]
					
				result.append(item)

		return result

	# #################################################################################################

	def show_vod( self ):
		result = []
		
		if self.maxim != None:
			genres = self.maxim.get_vod_genres()
			for genre in genres:
				result.append(self.dir_item( genre["name"], "#vod_genre#" + str(genre["id"]) ) )

		return result
	
	# #################################################################################################
	
	def show_vod_genre( self, genre_id ):
		offset = 0
		x = genre_id.split('_')
		if len(x) > 1:
			offset = int(x[1])
		
		genre_id = int(x[0])
		
		movies, count = self.maxim.get_vod_movies_by_genre( genre_id, 200, offset )
		img_url = self.maxim.get_vod_img_url()
		
		result = []
		
		for movie in movies:
			item = self.video_item(  "#vod_movie#" + str( movie["id"] ) )
			item["title"] = movie["title"]
			item["img"] = img_url.format(movie["id"])
			try:
				item["rating"] = movie["imdb_rating"]
			except:
				pass
				
			result.append(item)

		if count > offset + len( movies ):
			item = self.dir_item( "Ďalšie", "#vod_genre#" + str(genre_id) + "_" + str( offset + len( movies ))  )
			item["type"] = 'next'
			result.append( item )
			
		return result

	# #################################################################################################

	def resolve(self, item, captcha_cb=None, select_cb=None):
		if self.maxim == None:
			return None
		
#		self.info("resolve %s" % item["url"])

		url = item["url"]

		if url == '#':
			return None
		
		if url.startswith('#extra'):
			client.add_operation('SHOW_MSG', { 'msg': self.show_extra_menu(url[6:]), 'msgType': 'info', 'msgTimeout': 0, 'canClose': True, })
			return None

		if url.startswith("#vod_movie#"):
			movie = self.maxim.get_vod_movie_detail( int(url[11:]) )
			item["url"] = self.encode_url( movie["url"], "vod_" )

		if url.startswith("#archive_url#"):
			a = url[13:].split("#")
			x = self.maxim.get_archive_content_url( a[0], a[1], a[2] )
			item["url"] =  self.encode_url( x )
		
		self.info("result URL for player %s" % item["url"])
		if select_cb:
			return select_cb(item)

		return item

# #################################################################################################

__scriptid__ = 'plugin.video.antiktv'
__scriptname__ = 'antiktv'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__ = __addon__.getLocalizedString

#settings = {'quality':__addon__.getSetting('quality')}
settings = {}

provider = antiktvContentProvider( username=__addon__.getSetting('username'), password=__addon__.getSetting('password'), device_id=__addon__.getSetting( 'device_id' ) )

xbmcprovider.XBMCLoginRequiredContentProvider(provider, settings, __addon__, session).run(params)
