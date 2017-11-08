# -*- coding: UTF-8 -*-
#/*
# *      Copyright (C) 2017 bbaron
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
from md5crypt import md5crypt
import xml.etree.ElementTree as ET
import hashlib
from provider import ResolveException
import random
import re
import sys
import traceback
import urllib
import urllib2
import urlparse
import util
import datetime
from time import strftime

class wsUserData(object):
    def __init__(self, isVip, vipDaysLeft, userId):
        self.isVip = isVip
        self.vipDaysLeft = vipDaysLeft
        self.userId = userId

class Webshare():

    def __init__(self,username=None,password=None,cache=None):
        self.username = username
        self.password = password
        self.base_url = 'http://webshare.cz/'
        self.token = ''
        #util.init_urllib()
        self.login()
        self.loginOk = False
        if self.token:
            self.loginOk = True
        
    def _url(self, url):
        """
        Transforms relative to absolute url based on ``base_url`` class property
        """
        if url.startswith('http'):
            return url
        return self.base_url + url.lstrip('./')

    def _create_request(self,url,base):
        args = dict(urlparse.parse_qsl(url))
        headers = {'X-Requested-With':'XMLHttpRequest','Accept':'text/xml; charset=UTF-8','Referer':self.base_url}
        req = base.copy()
        for key in req:
            if args.has_key(key):
                req[key] = args[key]
        return headers,req

    def login(self):
        if not self.username and not self.password:
            return True # fall back to free account
        elif self.username and self.password and len(self.username)>0 and len(self.password)>0:
            #util.info('Login user=%s, pass=*****' % self.username)
            #self.write("Login start...")
            # get salt
            headers,req = self._create_request('',{'username_or_email':self.username})
            data = util.post(self._url('api/salt/'),req,headers=headers)
            xml = ET.fromstring(data)
            if not xml.find('status').text == 'OK':
                #self.write("Login end salt...")
                #util.error('Server returned error status, response: %s' % data)
                return False
            salt = xml.find('salt').text
            # create hashes
            password = hashlib.sha1(md5crypt(self.password.encode('utf-8'), salt.encode('utf-8'))).hexdigest()
            digest = hashlib.md5(self.username + ':Webshare:' + self.password).hexdigest()
            # login
            headers,req = self._create_request('',{'username_or_email':self.username,'password':password,'digest':digest,'keep_logged_in':1})
            data = util.post(self._url('api/login/'),req,headers=headers)
            xml = ET.fromstring(data)
            #self.write("Login end...")
            if not xml.find('status').text == 'OK':
                #util.error('Server returned error status, response: %s' % data)
                return False
            
            self.token = xml.find('token').text
            #util.info('Login successfull')
            return True
        return False

    def userData(self):
        if self.token:
            headers,req = self._create_request('/',{'wst':self.token})
            data = util.post(self._url('api/user_data/'), req, headers=headers)
            xml = ET.fromstring(data)
            xml.find('vip').text
            isVip = xml.find('vip').text
            vipDays = xml.find('vip_days').text
            ident = xml.find('ident').text

            if isVip != '1':
                isVip = '0'
            return wsUserData(isVip, vipDays, ident)
        return wsUserData('-1', '0', '')

    def write(self, msg):
        # prerobit na HDD plus cas tam dat a tak
        f = open('/tmp/stream_cinema_info.log', 'a')
        dtn = datetime.datetime.now()
        f.write(dtn.strftime("%H:%M:%S.%f")[:-3] +" %s\n" % msg)
        #f.write(strftime("%H:%M:%S") +" %s\n" % msg)
        f.close()

    def sendStats(self, item, baseUrl, apiVer, deviceId):
        #send data to server about watching movie
        #self.write('Stats start...')
        udata = self.userData()
        urlStats = baseUrl + '/Stats?ver='+apiVer+'&uid='+deviceId
        
        dur = float(item['duration'])
        ep = ''
        se = ''
        if 'episode' in item:
            ep = str(item['episode'])
        if 'season' in item:
            se = str(item['season'])
        now = datetime.datetime.now()
        endIn = now + datetime.timedelta(seconds=int(dur))
        endStr = endIn.strftime('%H:%M:%S')

        data = { 'vip':udata.isVip, 'vd': udata.vipDaysLeft, 'est':endStr, 'scid':str(item['id']), 
                    'action':'start', 'ws':udata.userId, 'dur':dur, 
                    'ep':ep, 'se':se }
            
        #self.write('data='+str(data))

        headers = {'Content-Type':'application/json', 'X-Uid':deviceId}
        response = util.post_json(urlStats, data, headers)

        self.write('Stats('+str(item['id'])+')='+str(response))

        return udata

    def resolve(self,ident):
        try:
            headers,req = self._create_request('/',{'ident':ident,'wst':self.token})
            #util.info(headers)
            #util.info(req)
            data = util.post(self._url('api/file_link/'), req, headers=headers)
            xml = ET.fromstring(data)
            if not xml.find('status').text == 'OK':
                #util.error('Server returned error status, response: %s' % data)
                raise ResolveException(xml.find('message').text)
            return xml.find('link').text
        except:
            raise