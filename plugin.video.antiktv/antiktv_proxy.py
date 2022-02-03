import sys,os
sys.path.append( os.path.dirname(__file__)  )

import threading
try:
	from SocketServer import ThreadingMixIn
	from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
	is_py3 = False
except:
	from socketserver import ThreadingMixIn
	from http.server import HTTPServer, BaseHTTPRequestHandler
	is_py3 = True

import base64
import requests
import binascii
from Maxim import Maxim

maxim = None
key_cache={}

# #################################################################################################

def init_maxim():
	username = None
	password = None
	device_id = None
	global maxim
	
	if maxim != None:
		return
	
	with open( "/etc/enigma2/settings", "r" ) as f:
		for line in f.readlines():
			if line.startswith("config.plugins.archivCZSK.archives.plugin_video_antiktv.") == True:
				line = line[56:].strip()
				
				if line.startswith("device_id=") == True:
					device_id = line[10:]
				elif line.startswith("username=") == True:
					username = line[9:]
				elif line.startswith("password=") == True:
					password = line[9:]

	if device_id != None and username != None and password != None and len(device_id) > 0 and len(username) > 0 and len( password ) > 0:
		maxim = Maxim( username, password, device_id )
	
# #################################################################################################

def getm3u8( base64_url ):
	getkey_uri = "/getkey/"
	if base64_url.startswith("vod_") == True:
		getkey_uri = "/getkey_vod/"
		base64_url = base64_url[4:]
		
	url = base64.b64decode(base64_url).decode("utf-8")
	base_url = url[:url.rindex("/") + 1]
	
	headers = {
		"User-Agent": "AntikTVExoPlayer/1.1.6 (Linux;Android 10) ExoPlayerLib/2.11.4",
		"Accept-Encoding": "gzip"
	}
	
	try:
		response = requests.get( url, headers = headers )
	except:
		return None

	ret = response.text.replace("encrypted-file://", this_proxy_url + getkey_uri )
	
	ret2=""
	for line in iter( ret.splitlines() ):
		if line[:1] != "#" and line.startswith("http://") == False:
			ret2 += base_url
		
		ret2 += (line + "\n")
	
	return ret2

# #################################################################################################

def getkey( key_name, is_vod=False ):
	init_maxim()
	global maxim, key_cache
	
	if maxim == None:
		return None
		
	try:
		return key_cache[key_name]
	except:
		pass
	
	if is_vod == True:
		key = maxim.get_vod_key( "encrypted-file://" + key_name )
	else:
		key = maxim.get_content_key( "encrypted-file://" + key_name )
	
	try:
		key = binascii.a2b_hex(key)
		key_cache[key_name] = key
	except:
		return None
	
	return key

# #################################################################################################

class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		response = None
		if self.path == "/info":
			response = "antiktv_proxy"
		elif self.path == "/reloadconfig":
			global maxim, key_cache
			maxim = None
			key_cache = {}
			response = ""
		elif self.path.startswith("/getm3u8/" ) == True:
			response = getm3u8( self.path[9:] )
		elif self.path.startswith("/getkey/" ) == True:
			response = getkey( self.path[8:] )
		elif self.path.startswith("/getkey_vod/" ) == True:
			response = getkey( self.path[12:], True )

		if response == None:
			self.send_error( 404 )
			return

		if is_py3 == True and type( response ) == str:
			response = response.encode("utf-8")
		
		self.send_response(200)
		self.end_headers()
		self.wfile.write(response)
		return
	
	def log_message(self, format, *args):
		return

# #################################################################################################

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

pidfile="/tmp/antiktv_proxy.pid"

if __name__ == '__main__':
	address = "127.0.0.1"
	port = 18080
	
	this_proxy_url = "http://%s:%d" % (address, port)
	
	server = ThreadedHTTPServer(( address, port ), Handler)
	
	with open( pidfile,"w" ) as f:
		f.write( "%d" % os.getpid() )
		
	try:
		server.serve_forever(3)
	except:
		pass

	try:
		os.remove( pidfile )
	except:
		pass
