# -*- coding: UTF-8 -*-
#/*
# *      Copyright (C) 2011 Libor Zoubek
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
import os, re, sys, urllib, urllib2, traceback, cookielib, time, socket
from htmlentitydefs import name2codepoint as n2cp
import simplejson as json
import threading
import Queue 
from Plugins.Extensions.archivCZSK.engine import client
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
UA = 'Mozilla/6.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.5) Gecko/2008092417 Firefox/3.0.3'
LOG = 2
sys.path.append(os.path.join(os.path.dirname(__file__), 'contentprovider'))
sys.path.append( os.path.join ( os.path.dirname(__file__),'crypto') )

_cookie_jar = None

CACHE_COOKIES = 'cookies'


class _StringCookieJar(cookielib.LWPCookieJar):
    def __init__(self, string=None, filename=None, delayload=False, policy=None):
        cookielib.LWPCookieJar.__init__(self, filename, delayload, policy)
        if string and len(string) > 0:
            self._cookies = pickle.loads(string)

    def dump(self):
        return pickle.dumps(self._cookies)

def init_urllib(cache=None):
    """
    Initializes urllib cookie handler
    """
    global _cookie_jar
    data = None
    if cache is not None:
        data = cache.get(CACHE_COOKIES)
    _cookie_jar = _StringCookieJar(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(_cookie_jar))
    urllib2.install_opener(opener)

def cache_cookies(cache):
    """
    Saves cookies to cache
    """
    global _cookie_jar
    if _cookie_jar:
        cache.set(CACHE_COOKIES, _cookie_jar.dump())

def request(url, headers={}):
    debug('request: %s' % url)
    req = urllib2.Request(url, headers=headers)
    req.add_header('User-Agent', UA)
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    debug('len(data) %s' % len(data))
    return data

def post(url, data, headers={}):
    postdata = urllib.urlencode(data)
    req = urllib2.Request(url, postdata, headers)
    req.add_header('User-Agent', UA)
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    return data

def post_json(url,data,headers={}):
    postdata = json.dumps(data)
    headers['Content-Type'] = 'application/json'
    req = urllib2.Request(url,postdata,headers)
    req.add_header('User-Agent',UA)
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    return data

def run_parallel_in_threads(target, args_list):
    result = Queue.Queue()
    # wrapper to collect return value in a Queue
    def task_wrapper(*args):
        result.put(target(*args))
    threads = [threading.Thread(target=task_wrapper, args=args) for args in args_list]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result 

def icon(name):
	return 'https://github.com/lzoubek/xbmc-doplnky/raw/dharma/icons/' + name

def substr(data, start, end):
	i1 = data.find(start)
	i2 = data.find(end, i1)
	return data[i1:i2]
    

def save_to_file(url, file):
	try:
		return save_data_to_file(request(url))
	except:
		traceback.print_exc()

def save_data_to_file(data, file):
	try:
		f = open(file, 'w')
		f.write(data)
		f.close()
		return True
	except:
		traceback.print_exc()
def read_file(file):
	if not os.path.exists(file):
		return ''
	f = open(file, 'r')
	data = f.read()
	f.close()
	return data

def _substitute_entity(match):
        ent = match.group(3)
        if match.group(1) == '#':
            # decoding by number
            if match.group(2) == '':
                # number is in decimal
                return unichr(int(ent))
            elif match.group(2) == 'x':
                # number is in hex
                return unichr(int('0x' + ent, 16))
        else:
            # they were using a name
            cp = n2cp.get(ent)
            if cp: return unichr(cp)
            else: return match.group()

def decode_html(data):
	if not type(data) == str:
		return data
	try:
		if not type(data) == unicode:
			data = unicode(data, 'utf-8', errors='ignore')
		entity_re = re.compile(r'&(#?)(x?)(\w+);')
    		return entity_re.subn(_substitute_entity, data)[0]
	except:
		traceback.print_exc()
		print [data]
		return data

def debug(text):
        text = "xbmc_doplnky: debug " + (str([text]))
        client.log.debug(text)

def info(text):
        text = "xbmc_doplnky: info " + (str([text]))
        client.log.info(text)
        
def error(text):
        text = "xbmc_doplnky: error" + (str([text]))
        client.log.error(text)


_diacritic_replace= {u'\u00f3':'o',
u'\u0213':'-',
u'\u00e1':'a',
u'\u010d':'c',
u'\u010c':'C',
u'\u010f':'d',
u'\u010e':'D',
u'\u00e9':'e',
u'\u011b':'e',
u'\u00ed':'i',
u'\u0148':'n',
u'\u0159':'r',
u'\u0161':'s',
u'\u0165':'t',
u'\u016f':'u',
u'\u00fd':'y',
u'\u017e':'z',
u'\xed':'i',
u'\xe9':'e',
u'\xe1':'a',
}

def replace_diacritic(string):
	ret = []
	for char in string:
		if char in _diacritic_replace:
			ret.append(_diacritic_replace[char])
		else:
			ret.append(char)
	return ''.join(ret)


