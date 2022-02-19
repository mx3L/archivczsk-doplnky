# -*- coding: utf-8 -*-

from AESCipher import AESCipher
from collections import OrderedDict
from uuid import getnode as get_mac
import hashlib
import zlib
import json
import requests
import time

API_URL="http://maxim.iptv.antik.sk:180/api.php?id="
VOD_API_URL="http://88.212.11.51/api.php?id="

class Maxim:
	request_template = {}
	
	# #################################################################################################
	#
	# Init data to access Antik Maxim server
	# name - username to moj.antik.sk
	# password - password to moj.antik.sk
	# device_id - already registered device ID - can be seen on moj.antik.sk
	#
	# #################################################################################################
	
	def __init__(self, name, password, device_id ):
		self.device_id        = device_id
		self.name             = name
		self.password         = password
		
		# device_id must be already registered and is used for accessing device key (used to decrypt video stream)
		device_id_md5 = hashlib.md5( ("L:?<V[Z*Tc;gXc5p" + device_id).encode("utf-8") ).hexdigest()
		
		self.request_template["normal"]       = self.create_request_template( API_URL,     name,            password )
		self.request_template["register"]     = self.create_request_template( API_URL,     "#register",     "2408yh24h80g24hg023r" )
		self.request_template["device"]       = self.create_request_template( API_URL,     device_id,       device_id_md5 )
		self.request_template["vod_get_auth"] = self.create_request_template( VOD_API_URL, "vod_master",    "test12345" )

	# #################################################################################################
	#
	# Create device_id that can be used for registration
	#
	# #################################################################################################
	
	@staticmethod
	def create_device_id():
		mac_str = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
		return hashlib.sha1( mac_str.encode("utf-8") ).hexdigest()[24:]

	# #################################################################################################
	#
	# Create auth_id that is used in requests to Maxim server as parameter
	#
	# #################################################################################################
	
	def create_auth_id( self, name ):
		return hashlib.sha256( ("VFZN!7y5yiu#2&c0WBgU" + name + "ofOqtA4W%HO1snf+TLtw").encode("utf-8") ).hexdigest()

	# #################################################################################################
	#
	# This will create AES key that is used for communication with Maxim
	#
	# #################################################################################################
	
	def create_aes_key( self, password ):
		return hashlib.sha256( self.create_auth_id( password ).encode("utf-8") ).hexdigest()
	
	# #################################################################################################
	#
	# Create base template used later for creating requests and encryption
	#
	# #################################################################################################
	
	def create_request_template( self, url, name, password ):
		auth_id = self.create_auth_id( name )
		auth_key = self.create_aes_key( password )
		return { "url" : url, "id" : auth_id, "key" : auth_key }
	
	# #################################################################################################
	#
	# Print precalculated data that will be used for various types of communication
	#
	# #################################################################################################
	
	def print_data( self ):
		for request_type in self.request_template:
			data = self.request_template[request_type]
			print( "Request type: " + request_type )
			print( "url: " + data["url"] )
			print( "id: " + data["id"] )
			print( "key: " + data["key"] )
			print("")
	
	# #################################################################################################
	#
	# Compress with zlib a encrypt request
	# request_type is used to pick the right template for communication
	#
	# #################################################################################################
	
	def encode_request( self, request, request_type="normal" ):
		return AESCipher( self.request_template[request_type]["key"] ).encrypt( zlib.compress( request ) )

	# #################################################################################################
	#
	# Decrypt and decompress response with zlib
	# request_type is used to pick the right template for communication
	#
	# #################################################################################################
	
	def decode_response( self, response, request_type="normal" ):
		return zlib.decompress( AESCipher( self.request_template[request_type]["key"] ).decrypt( response ) )
	
	# #################################################################################################
	#
	# Returns dictionary with device info data - it is used in every request
	#
	# #################################################################################################
	
	def getDeviceInfo( self ):
		return {
			"vendor": "Raspberry",
			"model": "Android_AntikTV_VOD",
			"os_version": "10",
			"app_version": "1.1.17.7",
			"app_name": "Antik TV",
			"id": self.device_id,
			"ip": "192.168.1.2",
			"lang": "sk",
			"type": "stb",
			"os": "Android",
			"service": "OTT"
		}

	# #################################################################################################
	#
	# Sends the request to Maxim server. request_type is used for pick the right communication template.
	# If response is 200, then data in it will return decrypted data from response
	#
	# #################################################################################################
	
	def do_request( self, data, request_type="normal" ):
		headers = {
			"Content-Type": "application/x-www-form-urlencoded",
			"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Build/1.110111.020)",
			"Accept-Encoding": "gzip"
		}
		
		url = self.request_template[request_type]["url"] + self.request_template[request_type]["id"]
		data = self.encode_request( bytes( data ), request_type )
		response = requests.post( url, data = data, headers = headers )
		
		if response.status_code == 200 and len(response.content) >= 16 :
			return True, self.decode_response( response.content, request_type )
		else:
			print("Error response code: %s, response_len: %d" % (str( response.status_code ), len(response.content) ) )
			
		return False, None
	
	#
	# #################################################################################################
	# ####  Low level functions used to call Maxim API and returns True/False and json response  ######
	# #################################################################################################
	
	# #################################################################################################
	#
	# Calls MwGetSettings method
	#
	# #################################################################################################
	def call_MwGetSettings( self, request_type="normal" ):
		xml_data = {
			"function": "MwGetSettings",
			"mac_address": self.device_id,
			"ip_address": "",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), request_type )

	# #################################################################################################
	#
	# Calls MwGetMyAccountInfo method
	#
	# #################################################################################################
	
	def call_MwGetMyAccountInfo( self ):
		xml_data = {
			"function": "MwGetMyAccountInfo",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )

	# #################################################################################################
	#
	# Calls Register method
	#
	# #################################################################################################
	
	def call_Register( self ):
		xml_data = {
			"function": "Register",
			"username": self.device_id,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "register" )

	# #################################################################################################
	#
	# Calls MwUnregisterDevice method
	#
	# #################################################################################################
	
	def call_MwUnregisterDevice( self ):
		xml_data = {
			"function": "MwUnregisterDevice",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )

	# #################################################################################################
	#
	# Calls MwLogOnCustomer method
	#
	# #################################################################################################
	
	def call_MwLogOnCustomer( self ):
		xml_data = {
			"function": "MwLogOnCustomer",
			"device": self.getDeviceInfo(),
			"login": {
				"username": self.name,
				"password": self.create_auth_id( self.password ),
				"password_hash": True
			}
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "device" )

	# #################################################################################################
	#
	# Calls MwSyncCallbackPing method
	#
	# #################################################################################################
	
	def call_MwSyncCallbackPing( self, data ):
		xml_data = {
			"function": "MwSyncCallbackPing",
			"device": self.getDeviceInfo(),
			"data": data,
			"mac_address": ""
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "device" )

	# #################################################################################################
	# ####################################  Live TV calls  ############################################
	# #################################################################################################
	
	# #################################################################################################
	#
	# Calls ChannelList method to get list of available channels
	# channel_type can be tv, radio and cam
	#
	# #################################################################################################
	
	def call_ChannelList( self, channel_type="tv" ):
		xml_data = {
			"function": "ChannelList",
			"limit": 1000,
			"offset": 0,
			"type": channel_type,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )

	# #################################################################################################
	#
	# Calls GetContentKey to get key used to decrypt video stream
	# key_id should be extracted from m3u8 playlist - usualy in format "encrypted-file://KEY_xxxxxxxxx"
	#
	# #################################################################################################
	
	def call_GetContentKey( self, key_id ):
		xml_data = {
			"function": "GetContentKey",
			"id": key_id,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "device" )

	# #################################################################################################
	#
	# Calls ChannelEpg to get EPG for channel and time range
	#
	# #################################################################################################
	
	def call_ChannelEpg( self, channel, time_start, time_end ):
		xml_data = {
			"function": "ChannelEpg",
			"channel_id": channel,
			"from": time_start,
			"to": time_end,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )

	# #################################################################################################
	#
	# Calls ActualEpg to get actual EPG for entered channels
	#
	# #################################################################################################
	
	def call_ActualEpg( self, channels, add_next=0 ):
		xml_data = {
			"function": "ActualEpg",
			"channels": channels,
			"next": add_next,
			"programme_desc": "all",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )
	
	# ################################# VOD calls ############################################
	
	# #################################################################################################
	#
	# Calls VodGetUser method to get access data to VOD
	#
	# #################################################################################################
	
	def call_VodGetUser( self ):
		xml_data = {
			"function": "VodGetUser",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "vod_get_auth" )
	
	# #################################################################################################
	#
	# Calls VodGenres method to get available VOD genres
	#
	# #################################################################################################
	
	def call_VodGenres( self ):
		xml_data = {
			"function": "VodGenres",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "vod" )

	# #################################################################################################
	#
	# Calls VodTopMovies method to get TOP movies
	#
	# #################################################################################################
	
	def call_VodTopMovies( self, limit=20, offset=0 ):
		xml_data = {
			"function": "VodTopMovies",
			"limit": limit,
			"offset": offset,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "vod" )

	# #################################################################################################
	#
	# Calls VodGenreMovies method to get available movies for genre_id (received from VodGenres)
	#
	# #################################################################################################
	
	def call_VodGenreMovies( self, genre_id, limit=1000, offset=0 ):
		xml_data = {
			"function": "VodGenreMovies",
			"genre_id": genre_id,
			"type": "genre",
			"limit": limit,
			"offset": offset,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "vod" )

	# #################################################################################################
	#
	# Calls VodMovieDetail method to get info about selected movie_id
	#
	# #################################################################################################
	
	def call_VodMovieDetail( self, movie_id ):
		xml_data = {
			"function": "VodMovieDetail",
			"movie_id": movie_id,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "vod" )

	# #################################################################################################
	#
	# Calls VodPlay method to get playback info for selected movie_id + movie_key
	#
	# #################################################################################################
	
	def call_VodPlay( self, movie_id, movie_key ):
		xml_data = {
			"function": "VodPlay",
			"movie_id": movie_id,
			"key": movie_key,
			"network_mode": "ott",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "vod" )

	# #################################################################################################
	#
	# Calls VodGetKey to get key used to decrypt VOD
	# key_id should be extracted from m3u8 playlist - usualy in format "encrypted-file://vod_xxxxxxxxx"
	#
	# #################################################################################################
	
	def call_VodGetKey( self, key_id ):
		xml_data = {
			"function": "VodGetKey",
			"id": key_id,
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8"), "vod" )

	# ############################### Archive calls ##########################################

	# #################################################################################################
	#
	# Calls ArchiveBrowserGenres to get available genres in archive
	#
	# #################################################################################################
	
	def call_ArchiveBrowserGenres( self ):
		xml_data = {
			"function": "ArchiveBrowserGenres",
			"device": self.getDeviceInfo()
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )
	
	# #################################################################################################
	#
	# Calls ArchiveBrowserMain to get available titles for combination channels:genre
	#
	# #################################################################################################
	
	def call_ArchiveBrowserMain( self, channels, genre, limit=20, offset=0 ):
		xml_data = {
			"function": "ArchiveBrowserMain",
			"device": self.getDeviceInfo(),
			"limit": limit,
			"offset": offset,
			"channels": channels,
			"genre": genre
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )

	# #################################################################################################
	#
	# Calls ArchiveBrowserSeries to get available titles for combination channels:serie_id
	#
	# #################################################################################################
	
	def call_ArchiveBrowserSeries( self, channels, serie_id, limit=20, offset=0 ):
		xml_data = {
			"function": "ArchiveBrowserSeries",
			"device": self.getDeviceInfo(),
			"limit": limit,
			"offset": offset,
			"channels": channels,
			"sort": "episode_desc",
			"series": serie_id
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )

	# #################################################################################################
	#
	# Calls ArchiveBrowserSeason to get available titles for combination channels:serie_id:seasin_nr
	#
	# #################################################################################################
	
	def call_ArchiveBrowserSeason( self, channels, serie_id, season_nr, limit=20, offset=0 ):
		xml_data = {
			"function": "ArchiveBrowserSeason",
			"device": self.getDeviceInfo(),
			"limit": limit,
			"offset": offset,
			"channels": channels,
			"sort": "episode_desc",
			"series": serie_id,
			"season": season_nr
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )

	# #################################################################################################
	#
	# Calls GetContentArchive to get info about archive from channel in times
	#
	# #################################################################################################
	
	def call_GetContentArchive( self, channel_id, time_from, time_to ):
		xml_data = {
			"function": "GetContentArchive",
			"device": self.getDeviceInfo(),
			"channel_id": channel_id,
			"from": time_from,
			"to": time_to
		}
		
		return self.do_request( json.dumps( xml_data ).encode("utf-8") )
	
	#
	# #################################################################################################
	# #########   Higher level functions used to call Maxim API and some response processing  #########
	# #################################################################################################
	
	
	# #################################################################################################
	#
	# If request_type = "normal", then it checks if name/password is correct. If request_type = "device",
	# then it checks if device_id is registered. Returns True/False and login data
	#
	# #################################################################################################
	
	def check_login( self, request_type="normal" ):
		login_data = {}
		
		ok, data = self.call_MwGetSettings( request_type )
		
		if ok == True:
			data = json.loads( data )
			try:
				login_data["is_anonymous"] = data["setting"]["data"]["is_anonymous"]
				login_data["guest_id"] = data["setting"]["data"]["guest_id"]
			except:
				pass
		
		return ok, login_data


	# #################################################################################################
	#
	# Registers device_id and returns True/False and response message
	#
	# #################################################################################################
	
	def register_device_id( self, login_only=False ):
		if login_only == False:
			ok, data = self.call_Register()
			
			if ok == False:
				return False, "Neočakávaná odpoveď na príkaz register"

			data = json.loads( data )
			
			if data["status"] != "ok":
				return False, "Neočakávaný status na príkaz register: " + data["status"]
			
			time.sleep(1)

		ok, data = self.call_MwLogOnCustomer()
		
		if ok == False:
			return False, "Neočakávaná odpoveď na príkaz login"
		
		data = json.loads( data )

		if data["code"] > 400:
			if data["code"] == 401:
				return False, "Nesprávne meno alebo heslo! - code 401"
			elif data["code"] == 406:
				return False, "Chyba prihlásenia - skontrolujte aktivačný email! - code 406"
			elif data["code"] == 416:
				return False, "Príliš veľa registrovaných zariadení pre toto konto - code 416"
			else:
				return False, "Neznáma chyba prihlásenia! - code " + str( data["code"] )
		
		if data["code"] != 200:
			return False, "Neočakávaný návratový kód na príkaz login: " + str(data["code"])
		
		response_msg = data["status"]
		
		if "ping" in data:
			for i in 1,2,3,4,5:
				time.sleep(1)
				ok, data = self.call_MwSyncCallbackPing( data["ping"] )
				
				if ok == False:
					return False, "Neočakávaná odpoveď na príkaz sync"
				
				data = json.loads( data )
				
				if data["code"] != 301:
					break

			if data["code"] != 200:
				return False, "Neočakávaný návratový kód na príkaz sync: " + str(data["code"])
		
			response_msg = response_msg + "; " + data["status"]
		
		return True, response_msg

	# #################################################################################################
	#
	# Unregisters device_id and returns True/False and message
	#
	# #################################################################################################
	
	def unregister_device_id( self ):
		ok, data = self.call_MwUnregisterDevice()
		
		if ok == False:
			return False, "Neočakávaná odpoveď na príkaz unregister"

		data = json.loads( data )
		
		if data["code"] == 200:
			return True, data["status"]
		
		return False, "Neočakávaný návratový kód: %d, status: %s" % (data["code"], data["status"])

	# #################################################################################################
	#
	# Returns info about customer account
	#
	# #################################################################################################

	def get_account_info( self ):
		ok, data = self.call_MwGetMyAccountInfo()

		response = {
			"account": {
				"name": "???",
				"email": "???",
				"identifier": "???",
			},
			"packages": [],
			"devices": {
				"MOBILE" : [],
				"OTT" : []
				},
			}

		if ok == False:
			return response
		
		data = json.loads( data )

		try:
			resp = {}
			x = data["data"][0]["account_data"]
		
			resp["name"] = x["name"]
			resp["email"] = x["email"]
			resp["identifier"] = x["identifier"]
			response["account"] = resp
		except:
			pass
			
		try:
			for x in data["data"][0]["packages"]:
				if x["valid_to_timestamp"] == 0:
					valid_to = ""
				else:
					valid_to = " - " + x["valid_to"] + " " + x["valid_time_to"]

				response["packages"].append( { "name": x["channels_package"], "valid" : x["valid_from"] + " " + x["valid_time_from"] + valid_to } )
		except:
			pass
		
		try:
			for x in data["data"][0]["my_devices"]:
				resp = {}
	
				resp["id"] = x["device_id"]
				resp["hw"] = x["device_type"] + " " + x["device_vendor"] + " " + x["device_model_name"]
				resp["os"] = x["device_os"] + " " + x["device_os_version"]
				resp["app"] = x["app_version"]
				
				if x["device_service"] == "MOBILE":
					response["devices"]["MOBILE"].append( resp )
				elif x["device_service"] == "OTT":
					response["devices"]["OTT"].append( resp )
		except:
			pass
		
				
		return response

	
	# #################################################################################################
	#
	# Returns dictionary with categories and lists of channels in each category
	# channel type can be tv, radio, cam
	# filters is dictionary with keys "adult", "h265" / values "yes", "no", "only"
	#
	# #################################################################################################
	
	def get_channel_list( self, channel_type, filters=None ):
		ok, data = self.call_ChannelList( channel_type )

		if ok == False:
			return {}

		data = json.loads( data )

		channels = OrderedDict()
		
		adult = "yes"
		h265 = "yes"
		
		if filters != None:
			if "adult" in filters:
				adult = filters["adult"]

			if "h265" in filters:
				h265 = filters["h265"]
		
		for cat in [ data["channels"] ]:
			for channel in cat:
				
				if adult == "no" and channel["adult"] == True:
					continue

				if adult == "only" and channel["adult"] == False:
					continue
				
				quality=0
				url=None
				resolution=None
				stream_list = {}
				for stream in channel["stream"]:
					if "video_codec_name" in stream:
						vcodec = stream["video_codec_name"]
					else:
						vcodec = None
						
					stream_list[ stream["quality_id"] ] = { "url": stream["url"], "vcodec": vcodec, "resolution": str(stream["resolution"]) }
					
					if stream["quality_id"] > quality:
						if vcodec != None:
							if h265 == "no" and vcodec == "h265":
								continue

							if h265 == "only" and vcodec != "h265":
								continue
						
						quality = stream["quality_id"]
						url = stream["url"]
						resolution = stream["resolution"]
				
				try:
					channel_cat = channel["channel_category"][0]["category_plural"]
				except:
					try:
						channel_cat = "Ostatné".decode("utf-8")
					except:
						channel_cat = "Ostatné"
				
				if channel_cat not in channels:
					channels[channel_cat] = []
				
				if "snapshot" in channel:
					snapshot = channel["snapshot"]["url"]
				else:
					snapshot = None

				if "archive" in channel:
					archive = channel["archive"]
				else:
					archive = False
					
				channels[channel_cat].append( { "name": channel["name"], "url": url, "resolution": resolution, "logo": channel["logo"], "snapshot" : snapshot, "id_content" : channel["id_content"], "id" : channel["id"], "archive": archive, "streams": stream_list } )
		
		return channels

	# #################################################################################################
	#
	# Returns key used to decrypt video stream
	# key_id should be extracted from m3u8 playlist - usualy in format "encrypted-file://KEY_xxxxxxxx"
	#
	# #################################################################################################
	
	def get_content_key( self, key_id ):
		ok, data = self.call_GetContentKey( key_id )

		if ok == True:
			return json.loads( data )["key"]
		else:
			return ""

	# #################################################################################################
	#
	# Returns EPG for channel_id and time range
	#
	# #################################################################################################
	
	def get_channel_epg( self, channel, time_start, time_end ):
		ok, data = self.call_ChannelEpg( channel, time_start, time_end )

		if ok == True:
			data = json.loads( data )
			
			if "epg" in data:
				return data["epg"]

		return []

	# #################################################################################################
	#
	# Returns actual EPG for entered channels (array of channel's is_content properties)
	#
	# #################################################################################################
	
	def get_actual_epg( self, channels, add_next=0 ):
		ok, data = self.call_ActualEpg( channels, add_next )

		if ok == True:
			data = json.loads( data )
			
			if "epg" in data:
				return data["epg"]
		else:
			return {}
	
	# #################################################################################################
	# ########################################## VOD calls ############################################
	# #################################################################################################
	
	# #################################################################################################
	#
	# Creates request template for accessing VOD
	# If vod template is already created, then this method does nothing
	#
	# #################################################################################################
	
	def create_vod_request_template( self ):
		# check if we already have auth data for VOD - if yes, then don't continue
		if "vod" in self.request_template:
			return True

		ok, data = self.call_VodGetUser()
		
		if ok == False:
			return False
		
		response = json.loads( data )
		
		if response["status"] != "ok":
			return False
		
		self.request_template["vod"] = self.create_request_template( VOD_API_URL, response["account"], response["password"] )
		return True

	# #################################################################################################
	#
	# Returns available geners in VOD
	#
	# #################################################################################################
	
	def get_vod_genres( self ):
		self.create_vod_request_template()
		
		ok, data = self.call_VodGenres()
		
		if ok == False:
			return []
		
		response = json.loads( data )
		
		if response["status"] != "ok":
			return []
		
		return response["data"]

	# #################################################################################################
	#
	# Returns list of top movies
	#
	# #################################################################################################
	
	def get_vod_top_movies( self, limit=20, offset=0 ):
		self.create_vod_request_template()
		
		ok, data = self.call_VodTopMovies( limit, offset )

		if ok == False:
			return [], 0
		
		response = json.loads( data )
		
		if response["status"] != "ok":
			return [], 0
		
		return response["data"], response["count"]

	# #################################################################################################
	#
	# Returns Url with poster images formated for python format() function
	#
	# #################################################################################################
	
	def get_vod_img_url( self ):
		self.create_vod_request_template()
		
		ok, data = self.call_VodTopMovies(1)

		if ok == False:
			return ""
		
		response = json.loads( data )
		
		if response["status"] != "ok":
			return ""
		
		return response["img_url"].replace('%d', '{}')
	
	# #################################################################################################
	#
	# Returns list of movies in genre_id
	#
	# #################################################################################################
	
	def get_vod_movies_by_genre( self, genre_id, limit=100, offset=0 ):
		self.create_vod_request_template()
		
		ok, data = self.call_VodGenreMovies( genre_id, limit, offset )

		if ok == False:
			return [], 0
		
		response = json.loads( data )
		
		if response["status"] != "ok":
			return [], 0
		
		return response["data"], response["count"]

	# #################################################################################################
	#
	# Returns details about movie with movie_id
	#
	# #################################################################################################
	
	def get_vod_movie_detail( self, movie_id ):
		self.create_vod_request_template()
		
		ok, data = self.call_VodMovieDetail( movie_id )

		if ok == False:
			return {}
		
		response = json.loads( data )
		
		if response["status"] != "ok":
			return {}
		
		response = response["data"]

		ok, data = self.call_VodPlay( movie_id, response["key"] )

		if ok == False:
			return {}
		
		data = json.loads( data )
		
		if data["status"] != "ok":
			return {}
		
		response["url"] = data["data"]["url"]
		
		return response
		
	# #################################################################################################
	#
	# Returns key used to decrypt VOD stream
	# key_id should be extracted from m3u8 playlist - usualy in format "encrypted-file://vod_xxxxxxxx"
	#
	# #################################################################################################
	
	def get_vod_key( self, key_id ):
		self.create_vod_request_template()
		
		ok, data = self.call_VodGetKey( key_id )

		if ok == True:
			return json.loads( data )["key"]
		else:
			return ""

	# #################################################################################################
	# ################################### Archive calls ###############################################
	# #################################################################################################
	
	# #################################################################################################
	#
	# Gets available genres in archive
	# Returns array of dictionaries with information about genres
	#
	# #################################################################################################
	
	def get_archive_genres( self ):
		ok, data = self.call_ArchiveBrowserGenres()

		if ok == False:
			return []
		
		return json.loads( data )["genres"]
	
	# #################################################################################################
	#
	# Gets archive content for genre_id (returned by get_archive_genres()).
	# channels is array with channel's content_id identifiers
	#
	# #################################################################################################
	
	def get_archive_by_genre( self, channels, genre_id, limit=20, offset=0 ):
		ok, data = self.call_ArchiveBrowserMain( channels, genre_id, limit, offset )

		if ok == False:
			return [], 0
		
		data = json.loads( data )
		
		return data["items"], data["total_count"]

	# #################################################################################################
	#
	# Gets archive content for serie_id
	# channels is array with channel's content_id identifiers
	#
	# #################################################################################################
	
	def get_archive_by_serie( self, channels, serie_id, limit=20, offset=0 ):
		ok, data = self.call_ArchiveBrowserSeries( channels, serie_id, limit, offset )

		if ok == False:
			return [], 0
		
		data = json.loads( data )
		
		return data["items"], data["total_count"]

	# #################################################################################################
	#
	# Gets archive content for serie_id:seasin_nr
	# channels is array with channel's content_id identifiers
	#
	# #################################################################################################
	
	def get_archive_by_season( self, channels, serie_id, season_nr, limit=20, offset=0 ):
		ok, data = self.call_ArchiveBrowserSeason( channels, serie_id, season_nr, limit, offset )

		if ok == False:
			return [], 0
		
		data = json.loads( data )
		
		return data["items"], data["total_count"]
	
	# #################################################################################################
	#
	# Returns URL for accesing archive content
	#
	# #################################################################################################
	
	def get_archive_content_url( self, id_content, time_start, time_stop ):
		ok, data = self.call_GetContentArchive( id_content, time_start, time_stop )
		
		if ok == False:
			return ""
		
		return json.loads( data )["stream"]
	
	# #################################################################################################
	
