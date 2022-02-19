import sys,os
sys.path.append( os.path.dirname(__file__)  )

import threading
try:
	from SocketServer import ThreadingMixIn
	from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
	import cPickle as pickle
	is_py3 = False
except:
	from socketserver import ThreadingMixIn
	from http.server import HTTPServer, BaseHTTPRequestHandler
	import pickle
	is_py3 = True

import base64
import requests
import binascii
from time import time
from datetime import datetime, timedelta
from xml.sax.saxutils import escape
from Maxim import Maxim

from Crypto.Hash import MD5

maxim = None
data_mtime = 0
key_cache={}

XMLEPG_DATA_FILE = 'antiktv.data.xml'
XMLEPG_CHANNELS_FILE = 'antiktv.channels.xml'
XMLEPG_SOURCES_FILE = '/etc/epgimport/antiktv.sources.xml'
EPGIMPORT_SETTINGS_FILE = '/etc/enigma2/epgimport.conf'

XMLEPG_SOURCES_CONTENT ='''<?xml version="1.0" encoding="utf-8"?>
<sources>
  <mappings>
      <channel name="antiktv.channels.xml">
        <url>%s</url>
      </channel>
  </mappings>
  <sourcecat sourcecatname="AntikTV">
    <source type="gen_xmltv" channels="antiktv.channels.xml">
      <description>AntikTV</description>
      <url>%s</url>
    </source>
  </sourcecat>
</sources>
'''

# #################################################################################################

def load_settings():
	settings = {
		'username': '',
		'password': '',
		'device_id': '',
		'enable_xmlepg': False,
		'xmlepg_dir': '/media/hdd',
		'xmlepg_days': 5
	}
	
	with open( "/etc/enigma2/settings", "r" ) as f:
		for line in f.readlines():
			if line.startswith("config.plugins.archivCZSK.archives.plugin_video_antiktv.") == True:
				line = line[56:].strip()
				
				if line.startswith("device_id=") == True:
					settings['device_id'] = line[10:]
				elif line.startswith("username=") == True:
					settings['username'] = line[9:]
				elif line.startswith("password=") == True:
					settings['password'] = line[9:]
				elif line.startswith("enable_xmlepg=") == True:
					settings['enable_xmlepg'] = True if line[14:].lower() == 'true' else False
				elif line.startswith("xmlepg_dir=") == True:
					d = line[11:]
					if len(d) > 0:
						settings['xmlepg_dir'] = d
				elif line.startswith("xmlepg_days=") == True:
					try:
						d = int(line[12:])+1
						if d >= 1 and d <= 7:
							settings['xmlepg_days'] = d
					except:
						pass
					
	return settings

# #################################################################################################

def init_maxim( settings = None ):
	global maxim
	
	if maxim != None:
		return

	if settings == None:
		settings = load_settings()

	if len(settings['device_id']) > 0 and len(settings['username']) > 0 and len( settings['password'] ) > 0:
		maxim = Maxim( settings['username'], settings['password'], settings['device_id'] )
	
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

# #################################################################################################

def create_xmlepg( data_file, channels_file, days ):
	global maxim
	
	act_date = datetime.now()
	date_from = act_date.isoformat() + "+0100"
	date_to = (act_date + timedelta(days=days)).isoformat() + "+0100"

	with open( channels_file, "w" ) as fc:
		with open( data_file, "w" ) as f:
			fc.write('<?xml version="1.0" encoding="UTF-8"?>\n')
			fc.write('<channels>\n')
			
			f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
			f.write('<tv generator-info-name="plugin.video.antiktv" generator-info-url="https://antiktv.sk" generator-info-partner="none">\n')
	
			channel_type_id = -1
			for channel_type in ('tv', 'radio'):
				channels = maxim.get_channel_list( channel_type )
				channel_type_id += 1
	
				for cat in channels:
					for channel in channels[cat]:
						id_content = 'AntikTV_' + channel["id_content"]
						fc.write( ' <channel id="%s">1:0:1:%X:%X:0:E010000:0:0:0:http%%3a//</channel>\n' % (id_content, channel["id"], channel_type_id))
		
				for cat in channels:
					for channel in channels[cat]:
#						print("Processing channel: %s (%s)" % (channel['name'], channel["id_content"]))
						
						id_epg = channel["id_content"]
						id_content = 'AntikTV_' + id_epg
						
						epg = maxim.get_channel_epg( id_epg, date_from, date_to )
						
						for event in epg:
							xml_data = {
								'start': event['start'].replace("-", '').replace("T", '').replace(':','').replace('+',' '),
								'stop': event['stop'].replace("-", '').replace("T", '').replace(':','').replace('+',' '),
								'title': escape(str(event['title'])),
								'desc': escape(event['description']) if event['description'] != None else None
							}
							
							f.write( ' <programme start="%s" stop="%s" channel="%s">\n' % (xml_data['start'], xml_data['stop'], id_content ) )
							f.write( '  <title lang="cs">%s</title>\n' % xml_data['title'])
							f.write( '  <desc lang="cs">%s</desc>\n' % xml_data['desc'] )
							f.write( ' </programme>\n')
						
			fc.write('</channels>\n')
			f.write('</tv>\n')
			
# #################################################################################################

def generate_xmlepg_if_needed():
	settings = load_settings()
	
	if settings['enable_xmlepg'] == False:
		print("[XMLEPG] generator is disabled")
		return
	
	init_maxim( settings )
	global maxim, data_mtime
	
	if maxim == None:
		print("[XMLEPG] No antik login credentials provided or they are wrong")
		return
	
	# check if epgimport plugin exists
	epgimport_check_file = '/usr/lib/enigma2/python/Plugins/Extensions/EPGImport/__init__.py'
	if not os.path.exists( epgimport_check_file ) and not os.path.exists( epgimport_check_file + 'o' ) and not os.path.exists( epgimport_check_file + 'c' ):
		print("[XMLEPG] epgimport plugin not detected")
		return
	
	# create paths to export files
	data_file = os.path.join(settings['xmlepg_dir'], XMLEPG_DATA_FILE)
	channels_file = os.path.join(settings['xmlepg_dir'], XMLEPG_CHANNELS_FILE)
	
	# check modification time of last exported file
	try:
		if data_mtime == 0:
			# data_mtime is global to prevent rotary disc to start by every check
			data_mtime = os.path.getmtime( data_file )
			
		if (data_mtime + 86400) > time():
			# we have generated data file less then 1 day ago
			return
	except:
		pass
	
	# time to generate new XML EPG file
	try:
		gen_time_start = time()
		create_xmlepg(data_file, channels_file, settings['xmlepg_days'])
		data_mtime = time()
		print("[XMLEPG] Epg generated in %d seconds" % int(data_mtime - gen_time_start))
	except:
		print("[XMLEPG] something's failed by generating epg")

	# generate proper sources file for epgimport
	if not os.path.exists('/etc/epgimport'):
		os.mkdir( '/etc/epgimport')
	
	xmlepg_source_content = XMLEPG_SOURCES_CONTENT % (channels_file, data_file)
	xmlepg_source_content_md5 = MD5.new( xmlepg_source_content ).hexdigest()
	
	# check for correct content of sources file and update is if needed
	if not os.path.exists( XMLEPG_SOURCES_FILE ) or MD5.new( open( XMLEPG_SOURCES_FILE, 'r' ).read() ).hexdigest() != xmlepg_source_content_md5:
		print("[XMLEPG] Writing new sources file to " + XMLEPG_SOURCES_FILE )
		with open( XMLEPG_SOURCES_FILE, 'w' ) as f:
			f.write( xmlepg_source_content )

	# check if antik source is enabled in epgimport settings and enable if needed
	if os.path.exists( EPGIMPORT_SETTINGS_FILE ):
		epgimport_settings = pickle.load(open(EPGIMPORT_SETTINGS_FILE, 'rb'))
	else:
		epgimport_settings = { 'sources': [] }

	if 'AntikTV' not in epgimport_settings['sources']:
		print("[XMLEPG] Enabling AntikTV in epgimport config" )
		epgimport_settings['sources'].append('AntikTV')
		pickle.dump(epgimport_settings, open(EPGIMPORT_SETTINGS_FILE, 'wb'), pickle.HIGHEST_PROTOCOL)
	
# #################################################################################################

class EpgThread(threading.Thread):
	def __init__(self, event):
		threading.Thread.__init__(self)
		self.stopped = event

	def run(self):
		# after boot system time can be inacurate and this causes problems with modification times
		# so wait 5m before first try
		wait_time = 300
		
		while not self.stopped.wait(wait_time):
			generate_xmlepg_if_needed()
			
			# let's repeat this check every hour
			wait_time = 3600
		
		print("EPG thread stopped")
            
# #################################################################################################

pidfile="/tmp/antiktv_proxy.pid"

if __name__ == '__main__':
	address = "127.0.0.1"
	port = 18080
	
	this_proxy_url = "http://%s:%d" % (address, port)
	
	server = ThreadedHTTPServer(( address, port ), Handler)
	
	with open( pidfile,"w" ) as f:
		f.write( "%d" % os.getpid() )
		
	# start EPG update thread
	epg_stop_flag = threading.Event()
	epg_thread = EpgThread(epg_stop_flag)
	epg_thread.start()

	try:
		server.serve_forever(3)
	except:
		pass

	epg_stop_flag.set()
	print("Waiting for EPG thread to stop")
	epg_thread.join()
	
	try:
		os.remove( pidfile )
	except:
		pass
