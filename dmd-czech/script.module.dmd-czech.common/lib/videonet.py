# -*- coding: utf-8 -*-
#
# Modify: 2011-09-17, Ivo Brhel
#
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

def geturl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', user_agent)
        req.add_header('Referer','http://www.24video.net/')
        response = urllib2.urlopen(req)
        link=response.read()
        return link


def latin2text(word):
    dict_hex = {'&#xe1;' : 'á',
                '&#x10d;': 'č',
                '&#x10f;': 'ď',
                '&#xe9;' : 'é',
                '&#x11b;': 'ě',
                '&#xed;' : 'í',
                '&#xf1;' : 'ñ',
                '&#xf3;' : 'ó',
                '&#x159;': 'ř',
                '&#x161;': 'š',
                '&#x165;': 'ť',
                '&#xfa;' : 'ú',
                '&#xfc;' : 'ü',
                '&#xfd;' : 'ý',
                '&#x17e;': 'ž',
                }
    for key in dict_hex.keys():
        word = word.replace(key,dict_hex[key])
    return word


def getURL( page_url ):
    print("[videonet.py] getURL(page_url='%s')" % page_url)

    data = latin2text(geturl(page_url))
    match=re.compile("<videos><video url=\'(.+?)[^ ] rating").findall(data)
   
    return match[0]