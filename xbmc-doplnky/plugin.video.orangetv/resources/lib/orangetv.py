# -*- coding: UTF-8 -*-
#/*
# *      Copyright (C) 2018 Yoda
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

import urllib
import urllib2
import cookielib
import sys
import os
import json
import traceback
import datetime
import util
import xbmcprovider,xbmcutil

from provider import ContentProvider, cached, ResolveException
from time import strftime
from cachestack import lru_cache
from Components.config import config
from Components.Language import language
from Plugins.Extensions.archivCZSK.engine import client
from Plugins.Extensions.archivCZSK.compat import eConnectCallback


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class orangelog(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False
    LOG_FILE = ""
    

    @staticmethod
    def logDebug(msg):
        if orangelog.logDebugEnabled:
            orangelog.writeLog(msg, 'DEBUG')
    @staticmethod
    def logInfo(msg):
        orangelog.writeLog(msg, 'INFO')
    @staticmethod
    def logError(msg):
        orangelog.writeLog(msg, 'ERROR')
    @staticmethod
    def writeLog(msg, type):
        try:
            if not orangelog.logEnabled:
                return
            orangelog.LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'orangetv.log')
            f = open(orangelog.LOG_FILE, 'a')
            dtn = datetime.datetime.now()
            f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] +" ["+type+"] %s\n" % msg)
            f.close()
        except:
            print "####ORANGE-TV#### write log failed!!!"
            pass
        finally:
            print "####ORANGE-TV#### ["+type+"] "+msg

class OrangeTvProvider(xbmcprovider.XBMContentProvider):
    def __init__(self, provider, settings, addon, session):
        xbmcprovider.XBMContentProvider.__init__(self, provider, settings, addon, session)
        #self.check_setting_keys(['quality'])

    def resolve(self, url):
        def select_cb(resolved):
            #resolved = resolver.filter_by_quality(resolved, self.settings['quality'] or '0')
            if len(resolved) == 1:
                return resolved[0]
            else:
                stream_list = []
                if 'resolveTitle' in resolved[0]:
                    stream_list = ['%s'%(s['resolveTitle']) for s in resolved]
                else:
                    strem_list = ['%s empty'%(s['quality']) for s in resolved]
                idx = client.getListInput(self.session, stream_list, '')
                if idx == -1:
                    return None
                return resolved[idx]

        item = self.provider.video_item()
        item.update({'url':url})
        try:
            return self.provider.resolve(item, select_cb=select_cb)
        except ResolveException, e:
            orangelog.logError("Resolve item failed.\n%s"%traceback.format_exc())
            self._handle_exc(e)

class OrangeTvContentProvider(ContentProvider):
    __metaclass__ = Singleton
    ISO_639_1_CZECH = None
    par = None

    def __init__(self, username=None, password=None, filter=None):
        try:
            ContentProvider.__init__(self, name='czsklib', base_url='/', username=username, password=password, filter=filter)
            util.init_urllib()
            self.wsuser = username
            self.wspass = password
            self.language = language.getLanguage()
            self.init_trans()
            orangelog.logDebug("init orangetv...");
            self.session = None
        except:
            orangelog.logError("init orangetv failed.\n%s"%traceback.format_exc())
            pass

    def capabilities(self):
        return ['resolve', 'categories']

    def init_trans(self):
        self.trans = {
            "1": {"sk_SK":"xxx",
                  "en_EN":"xxx",
                  "cs_CZ":"xx"},
            "2": {"sk_SK":"xxx",
                  "en_EN":"xxx", 
                  "cs_CZ":"xxx"},
            }
    
    def showMsg(self, msgId, showSec, canClose=True, isError=True):
        try:
            msgType = "error"
            if not isError:
                msgType = "info"
            client.add_operation("SHOW_MSG", {
                                                'msg': self._getName(msgId),
                                                'msgType': msgType,
                                                'msgTimeout': showSec,
                                                'canClose': canClose
                                             })
        except:
            orangelog.logError("showMsg failed (minimalna verzia archivCZSK 1.1.2).\n%s"%traceback.format_exc())
            from Plugins.Extensions.archivCZSK.gui.common import showErrorMessage
            showErrorMessage(self.session, ("ERRmsg - %s"%self._getName(msgId)), showSec)
            pass

    @lru_cache(maxsize = 500, timeout = 30*60) #30min
    def cache_request_30(self, url):
        return util.request(url)
    @lru_cache(maxsize = 500, timeout = 60*60) #1h
    def cache_request_1(self, url):
        return util.request(url)
    @lru_cache(maxsize = 500, timeout = 180*60) #3h
    def cache_request_3(self, url):
        return util.request(url)
    @lru_cache(maxsize = 250, timeout = 360*60) #6h
    def cache_request_6(self, url):
        return util.request(url)
    @lru_cache(maxsize = 100, timeout = 12*60*60) #12h
    def cache_request_12(self, url):
        return util.request(url)

    def _get_data_cached(self, url, useCache, timeout):
        if useCache:
            if timeout==1:
                return self.cache_request_1(url);
            if timeout==3:
                return self.cache_request_3(url);
            if timeout==6:
                return self.cache_request_6(url);
            if timeout==12:
                return self.cache_request_12(url);

            return self.cache_request_30(url);
        else:
            return util.request(url)

    def _json(self, url, useCache=False, cacheTimeout=30):
        try:
            jsonData = self._get_data_cached(url, useCache, cacheTimeout)
            data = json.loads(jsonData)
            return data
        except urllib2.HTTPError as err:
            raise err
        except:
            orangelog.logError("Chyba pripojenia.\n%s"%traceback.format_exc())

    def _getName(self, id):
        try:
            if self.language!="sk_SK" and self.language!="en_EN" and self.language!="cs_CZ":
                self.language="en_EN"

            if id in self.trans:
                return self.trans[id][self.language]
        except Exception:
            pass
        return id

    def categories(self):
        result = []
        item = self.video_item(url='xxx', img=None, quality='')
        item['title']= 'Not implemented (donate)'
        result.append(item)
        #result.append(self.dir_item(title='Not implemented yet', url='xxx'))
        return result


    def resolve(self, item, captcha_cb=None, select_cb=None):
        # shows list of streams
        res = []
        item = self.video_item(url='xxx', img=None, quality='720p')
        res.append(item)
        item = self.video_item(url='xxx', img=None, quality='1080p')
        res.append(item)
        if len(res) == 1:
            return res[0]
        elif len(res) > 1 and select_cb:
            return select_cb(res)
        return []

   
 