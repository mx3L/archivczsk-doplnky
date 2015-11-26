# -*- coding: UTF-8 -*-
#/*
# *      Copyright (C) 2015 Josef Weiss
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

import re,os,urllib,urllib2,cookielib
import util

import xml.etree.ElementTree as ET
from provider import ContentProvider

class SlowTVContentProvider(ContentProvider):

    def __init__(self,username=None,password=None,filter=None):
        ContentProvider.__init__(self,'playtvak.cz','http://generix.idnes.cz/generatory/playtvak/slowtvxml.aspx',username,password,filter)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['resolve','categories']

    def categories(self):

        def media_tag(tag):
            return str( ET.QName('http://search.yahoo.com/mrss/', tag) )

        result = []

        xml = ET.fromstring(util.request(self.base_url))
        for i in xml.find('channel').findall('item'):
            item = self.video_item()
            item['title'] = i.find('title').text
            item['img'] = i.find('img').text
            item['url'] = i.find('url').text
            result.append(item)

        return result

    def resolve(self,item,captcha_cb=None,select_cb=None):
        return self.video_item(url=item['url'])
