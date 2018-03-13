import sys
import os
import urllib
import urllib2
import json
import traceback
import datetime
import util

class trakt_tv(object):
    def __init__(self, client_id, client_secret, token='', refresh_token='', expire=0):
        self.API = 'https://api.trakt.tv'
        self.API_AUTH = '%s/oauth/device'%self.API
        self.API_LIST = '%s/users/me/lists'%self.API
        self.API_WATCH_LIST = '%s/users/me/watchlist/items'%self.API
        self.API_VERSION = 2
        self.TOKEN = ''
        self.REFRESH_TOKEN = ''
        self.EXPIRE = 0
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        if token!='':
            self.TOKEN = token
        if refresh_token!='':
            self.REFRESH_TOKEN = refresh_token
        if expire!=0:
            self.EXPIRE = expire
        from scinema import sclog
        self.log = sclog()

    # TODO API HANDLING
    
    def get_lists(self):
        if self.valid():
            ret = []
            ret.append("%s##%s"%('Watchlist',self.API_WATCH_LIST))
            data = json.loads(util.request(self.API_LIST, {'Content-Type':'application/json', 'Authorization':'Bearer %s'%self.TOKEN, 'trakt-api-version':self.API_VERSION, 'trakt-api-key':'%s'%self.CLIENT_ID}))
            for m in data:
                ret.append("%s##%s"%(m['name'],'%s/%s/items'%(self.API_LIST, m['ids']['slug'])))
            return ret
        raise Exception('Invalid trakt token')

    def get_watch_list_items(self):
        if self.valid():
            ret = []
            data = json.loads(util.request(self.API_WATCH_LIST, {'Content-Type':'application/json', 'Authorization':'Bearer %s'%self.TOKEN, 'trakt-api-version':self.API_VERSION, 'trakt-api-key':self.CLIENT_ID}))
            for m in data:
                tp = '%s'%m['type']
                obj = {'imdb':'%s'%m[tp]['ids']['imdb'], 'title':'%s (%s)'%(m[tp]['title'],m[tp]['year'])}
                ret.append(obj)
            return ret
        raise Exception('Invalid trakt token')
    def get_list_items(self, id):
        if self.valid():
            ret = []
            data = json.loads(util.request(self.API_LIST+'/%s/items'%id, {'Content-Type':'application/json', 'Authorization':'Bearer %s'%self.TOKEN, 'trakt-api-version':self.API_VERSION, 'trakt-api-key':self.CLIENT_ID}))
            for m in data:
                tp = '%s'%m['type']
                obj = {'imdb':'%s'%m[tp]['ids']['imdb'], 'title':'%s (%s)'%(m[tp]['title'],m[tp]['year'])}
                ret.append(obj)
            return ret
        raise Exception('Invalid trakt token')

    ################

    def valid(self):
        if self.TOKEN == '':
            return False
        # check refresh
        now = (datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds()
        if self.EXPIRE-3600 < now: #-1hour
            self.refresh_token()
        return True

    def get_device_code(self):
        self.log.logDebug('get device URL='+self.API_AUTH+'/code')
        data = json.loads(util.post_json(self.API_AUTH+'/code', data={'client_id':self.CLIENT_ID}, headers={'Content-Type':'application/json'}))
        interval = data['interval'] #seconds
        expire = data['expires_in'] #seconds
        verUrl = data['verification_url']
        devCode = data['device_code']
        userCode = data['user_code']
        tryies = expire/interval

        return devCode, verUrl, userCode, interval

    def get_token(self, code):
        try:
            data = json.loads(util.post_json(self.API_AUTH+'/token', data={'code':code,'client_id':self.CLIENT_ID, 'client_secret':self.CLIENT_SECRET}, headers={'Content-Type':'application/json'}))
            self.TOKEN = data['access_token']
            self.REFRESH_TOKEN = data['refresh_token']

            

            expire = data['expires_in'] #seconds
            created = data['created_at']

            self.EXPIRE = expire+created

            self.log.logDebug("Get token return token=%s, rtoken=%s, exp=%s"%(self.TOKEN, self.REFRESH_TOKEN, self.EXPIRE))

            #update settings
            self.writeSetting('trakt_token', '%s'%self.TOKEN)
            self.writeSetting('trakt_refresh_token', '%s'%self.REFRESH_TOKEN)
            self.writeSetting('trakt_token_expire', '%s'%self.EXPIRE)

        except urllib2.HTTPError as err:
            return None
        return self.TOKEN

    def refresh_token(self, redirect_uri='urn:ietf:wg:oauth:2.0:oob', grant_type='refresh_token'):
        data = json.loads(util.post_json(self.API+'/oauth/token', data={'refresh_token':self.REFRESH_TOKEN, 'client_id':self.CLIENT_ID, 'client_secret':self.CLIENT_ID, 'redirect_uri':redirect_uri, 'grant_type':grant_type}, headers={'Content-Type':'application/json'}))
        self.TOKEN = data['access_token']
        self.REFRESH_TOKEN = data['refresh_token']

        expire = data['expires_in'] #seconds
        created = data['created_at']

        self.EXPIRE = expire+created

        #update settings
        self.writeSetting('trakt_token', '%s'%self.TOKEN)
        self.writeSetting('trakt_refresh_token', '%s'%self.TOKEN)
        self.writeSetting('trakt_token_expire', '%s'%self.EXPIRE)

    def writeSetting(self, id, val):
        from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
        addon = ArchivCZSK.get_xbmc_addon('plugin.video.stream-cinema')
        addon.setSetting(id, val)
    #def api_request_json(self, url, hdrs={}):
    #    try:
    #        req = urllib2.Request(url, headers=hdrs)
    #        response = urllib2.urlopen(req)
    #        data = response.read()
    #        self.log.logDebug('DATA=\n%s'%data)
    #        response.close()
    #        return json.loads(data)
    #    except:
    #        self.log.logError('Load trakt data failed.\n%s'%traceback.format_exc())
    #        raise