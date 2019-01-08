#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import cookielib
import time
import re
import sys
import ssl
import os
import datetime
from Components.config import config

__author__ = "Ladislav Dokulil"
__license__ = "GPL 2"
__version__ = "1.0.0"
__email__ = "alladdin@zemres.cz"


class primalog(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = True
    LOG_FILE = ""

    @staticmethod
    def logDebug(msg):
        if primalog.logDebugEnabled:
            primalog.writeLog(msg, 'DEBUG')

    @staticmethod
    def logInfo(msg):
        primalog.writeLog(msg, 'INFO')

    @staticmethod
    def logError(msg):
        primalog.writeLog(msg, 'ERROR')

    @staticmethod
    def writeLog(msg, type):
        try:
            if not primalog.logEnabled:
                return
            # if log.LOG_FILE=="":
            primalog.LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(), 'prima.log')
            f = open(primalog.LOG_FILE, 'a')
            dtn = datetime.datetime.now()
            f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
            f.close()
        except:
            print "####PRIMA#### write log failed!!!"
            pass
        finally:
            print "####PRIMA#### [" + type + "] " + msg

class UserAgent(object):
    def __init__(self, session_id = None, agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'):
        self.agent = agent
        self.play_url = 'https://prima.iprima.cz'
        self.cookie_domain = 'prima.iprima.cz'
        self.cookie_port = '80'
        self.cookie_jar = cookielib.CookieJar()
        self.cookie_jar.set_cookie(self.cookie('ott_cookies_confirmed', '1'))
        if session_id: self.cookie_jar.set_cookie(self.cookie('PLAY_SESSION', session_id))

        if hasattr(ssl, 'create_default_context'):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self.opener = urllib2.build_opener(urllib2.HTTPSHandler(context = ctx), urllib2.HTTPCookieProcessor(self.cookie_jar))
        else:
            self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))

    def get(self, url):
        req = self.request(url)
        res = self.opener.open(req)
        output = res.read()
        res.close()
        return output

    def post(self, url, params):
        req = self.request(url)
        req.add_data(urllib.urlencode(params))
        res = self.opener.open(req)
        output = res.read()
        res.close()
        return output

    def cookie(self, name, value):
        return cookielib.Cookie(None, name, value, self.cookie_port, True, self.cookie_domain, 
            True, False, '/', True, False, int(time.time()) + 3600, False, '', None, None, False)

    def request(self, url):
        req = urllib2.Request(self.sanitize_url(url))
        req.add_header('User-Agent', self.agent)
        return req

    def sanitize_url(self, url):
        abs_url_re = re.compile('^/')
        if (abs_url_re.match(url)):
            return self.play_url + url
        return url

class Parser:
    def __init__(self, ua = UserAgent(), time_obj = time, hd_enabled = True):
        self.ua = ua
        self.player_init_url = 'http://api.play-backend.iprima.cz/prehravac/init?'
        self.search_url = 'http://play.iprima.cz/vysledky-hledani-vse?'
        self.time = time_obj
        self.hd_enabled = hd_enabled

    def get_player_init_url(self, productID):
        return self.player_init_url + urllib.urlencode({
            '_infuse': '1',
            '_ts': int(self.time.time()),
            'productId': productID
        })
        #http://api.play-backend.iprima.cz/prehravac/init?_infuse=1&_ts=1450864235286&productId=p135603

    def get_search_url(self, query):
        return self.search_url + urllib.urlencode({
            'query': query
        })

    def get_productID(self, episode_link):
        content = self.ua.get(episode_link)

        product_id_re = re.compile('src="https://api.play-backend.iprima.cz/prehravac/embedded\?id=(.*?)"', re.S)
        product_id_result = product_id_re.search(content)

        if product_id_result is None:
            return None

        product_id = product_id_result.group(1)

        return product_id

    def get_video(self, productID):
        content = self.ua.get(self.get_player_init_url(productID))

        link_re = re.compile("'?src'?\s*:\s+'(https?://[^']+\\.m3u8.*)'")
        title_re = re.compile("programName: '(.*?)',")
        thumb_re = re.compile("thumbnails: {[\s\n]*url: '(.*?)\$")

        link = None
        sd_link = link_re.search(content)
        if sd_link:link = sd_link.group(1)

        hd_link = None
        if self.hd_enabled: hd_link = self.try_get_hd_link(sd_link.group(1))
        if hd_link: link = hd_link

        title = title_re.search(content).group(1)

        thumb = None
        thumb_result = thumb_re.search(content)
        if thumb_result:
            thumb = thumb_result.group(1) + '010.jpg'

        return Item(title, link, thumb)

    def try_get_hd_link(self, sd_link):
        hd_link = re.sub(".smil/", "-hd1-hd2.smil/", sd_link)
        try:
            self.ua.get(hd_link)
        except urllib2.HTTPError, e:
            if (e.code == 404) or (e.code == 403):
                return None
            else:
                raise

        return hd_link

    def get_next_list(self, link):
        content = self.ua.get(link)
        next_link = self.get_next_list_link(content)
        list = self.get_next_list_items(content)
        return NextList(next_link, list)

    def get_next_list_items(self, content):
        cdata_re = re.compile('<!\[CDATA\[(.*)\]\]>', re.S)
        cdata_match = cdata_re.search(content)
        return self.get_items_from_wrapper(cdata_match.group(1), '')

    def get_next_list_link(self, content):
        next_link_re = re.compile('<section class="molecule--button--load-more-button">.*?<a href="(.*?)"', re.S)
        result = next_link_re.search(content)
        if result: return result.group(1)
        return None

    def get_page(self, link):
        content = self.ua.get(link)
        return Page(None, self.get_video_lists(content, link))

    def get_shows(self, src_link):
        list = []
        content = self.ua.get(src_link)
        content_unescaped = eval('u"""' + content.replace('"', r'\"') + '-"""').replace('\\', '')

        wrapper_items = re.split('<div class="component--scope--cinematography ', content_unescaped)

        title_re = re.compile('<div class="component--scope--cinematography--details--title">(.*?)</div>', re.S)
        link_re = re.compile('<a href="([^\s"]*)', re.S)
        thumb_re = re.compile('<picture.*?data-srcset="(.*?)\?', re.S)

        for wrapper_item in wrapper_items:
            title_result = title_re.search(wrapper_item)
            if title_result is None: continue
            title = self.strip_tags(title_result.group(1).strip())

            link_result = link_re.search(wrapper_item)
            link = None
            if link_result: link = link_result.group(1)

            thumb_result = thumb_re.search(wrapper_item)
            thumb = None
            if thumb_result: thumb = thumb_result.group(1)

            items = self.get_items_from_wrapper(wrapper_item, src_link)
            list.append(PageVideoList(title, link, None, items, thumb))

        return Page(None, list)

    def get_show_navigation(self, link):
        list = []
        valid_items = ['Epizody', 'Bonusy', 'Sestřihy']
        content = self.ua.get(link)

        wrapper_re = re.compile('<nav.*?id="program-navigation-menu"(.*?)</nav>', re.S)
        item_re = re.compile('<a href="//(.*?)".*?>(.*?)</a>', re.S)

        wrapper_result = wrapper_re.search(content).group(1)
        item_result = item_re.findall(wrapper_result)

        for (link, txt) in item_result:
            if txt in valid_items:
                list.append(PageVideoList(txt, 'https://' + link))

        return Page(None, list)

    def get_redirect_from_remove_link(self, link):
        content = self.ua.get(link)
        redirect_re = re.compile('<redirect href="([^"]+)"')
        redirect_result = redirect_re.search(content)
        if redirect_result is None: return None
        return self.make_full_link(redirect_result.group(1), link)
    """
    def get_page_player(self, content):
        title_re = re.compile('<meta property="og:title" content="([^"]+)"/>', re.S)
        description_re = re.compile('<meta property="og:description" content="([^"]+)"/>', re.S)
        additional_info_re = re.compile('<span data-jnp="i.BroadcastDate">[^<]*</span>:([^\|]*)\|([^\|]*)\|([^<]*)</p>', re.S)
        fake_player_re = re.compile('<div id="fake-player" class="[^"]+" data-product="([^"]+)">[^<]*(?:<img src="([^"]+)")?', re.S)
        fake_player_result = fake_player_re.search(content)
        if fake_player_result is None:
            return None
        title_result = title_re.search(content)
        description_result = description_re.search(content)
        additional_info_result = additional_info_re.search(content)
        product_id = fake_player_result.group(1)
        image_url = fake_player_result.group(2)
        title = title_result.group(1).strip().decode('utf-8')
        description = None
        broadcast_date = None
        duration = None
        year = None
        if description_result:
            description = description_result.group(1)
        if additional_info_result:
            broadcast_date = additional_info_result.group(1).strip()
            duration = additional_info_result.group(2).strip()
            year = additional_info_result.group(3).strip()
        video_link = self.get_video_link(product_id)
        return Player(title, video_link, image_url, description, broadcast_date, duration, year)
    """
    def get_video_lists(self, content, src_link):
        list = []

        next_link_re = re.compile('<section class="molecule--button--load-more-button">[\s\n]*?<a.*?href="(.*?)"', re.S)
        next_link_result = next_link_re.search(content)
        next_link = None
        if next_link_result:
            next_link = next_link_result.group(1)

        seasons = self.get_seasons(content, src_link)
        items = self.get_items_from_wrapper(content, src_link)
        if seasons: list.append(PageVideoList(None, None, self.make_full_link(next_link, src_link), seasons))
        list.append(PageVideoList(None, None, self.make_full_link(next_link, src_link), items))

        return list

    def get_seasons(self, content, src_link):
        list = []

        seasons_re = re.compile('<div class="section--view--program-videos-section--seasons">(.*?)</a>[\s\n]*?</div>',
                                re.S)
        seasons_result = seasons_re.search(content)
        if seasons_result is None: return None

        seasons_items = re.findall(
            '<a class="season.*?href="//(.*?)">[\s\n]*?<div class="title">(.*?)</div>[\s\n]*?<div class="description">(.*?)</div>',
            seasons_result.group(0), re.S)

        for item in seasons_items:
            link = 'https://' + item[0]
            title = item[1]
            description = item[2]

            list.append(Item('[B]' + title + '[/B]', link, None, description, isFolder=True))

        return list

    def get_items_from_wrapper(self, content, src_link):
        list = []

        html_items = re.findall('class="compoment--scope--video-type.*?">(.*?)</a>', content, re.S)

        item_link_re = re.compile('<a class="compoment--scope--video-type--link" href="(.*?)"', re.S)
        item_img_re = re.compile('<div class="compoment--scope--video-type--picture.*?<source data-srcset.*?<source data-srcset="(.*?)\?'
                                 ,
                                 re.S)
        item_title_re = re.compile('<div class="compoment--scope--video-type--details--title">(.*?)</div>', re.S)
        item_description_re = re.compile('<div class="compoment--scope--video-type--details--description">(.*?)</div>',
                                         re.S)

        for html_item in html_items:
            item_content = html_item
            link_result = item_link_re.search(item_content)
            img_result = item_img_re.search(item_content,re.DOTALL)
            title_result = item_title_re.search(item_content)
            description_result = item_description_re.search(item_content)

            if title_result is None: continue
            title = self.strip_tags(title_result.group(1))

            if link_result is None: continue
            link = link_result.group(1)
            link = {'action': 'PLAY', 'linkurl': 'https:' + link}

            image_url = None
            description = ''

            if img_result: image_url = img_result.group(1)

            if description_result:
                description = description_result.group(1).strip()
                title = title + ' | ' + description


            list.append(Item(title, link, image_url, description))

        return list

    def get_filter_lists(self, content, src_link):
        list = []
        before_wrapper_re = re.compile('^(.*)<div class="loading-wrapper">', re.S)
        before_wrapper_result = before_wrapper_re.search(content)
        if before_wrapper_result is None: return list
        before_content = before_wrapper_result.group(1)

        filter_wrappers = re.split('<li class="hamburger-parent[^"]*">', before_content)

        title_re = re.compile('<span data-jnp="[^"]+" class="hamburger-toggler">([^<]+)</span>')
        for filter_wrapper in filter_wrappers:
            title_result = title_re.search(filter_wrapper)
            if title_result is None: continue
            title = title_result.group(1)
            items = self.get_filter_items(filter_wrapper, src_link)
            if (len(items) <= 0): continue 
            list.append(PageVideoList(title.decode('utf-8'), None, None, items))
        return list

    def get_filter_items(self, content, src_link):
        link_list_re = re.compile('<div class="sub-menu" id="js-tdi-items-filter[^"]*">[^<]*<ul>', re.S)
        if link_list_re.search(content):
            return self.get_filter_items_link(content, src_link)
        checkbox_list_re = re.compile('<div class="sub-menu" id="js-tdi-items-filter[^"]*">[^<]*<ul class="checkbox-columns[^"]*">', re.S)
        if checkbox_list_re.search(content):
            return self.get_filter_items_checkbox(content, src_link)
        return []

    def get_filter_items_link(self, content, src_link):
        list = []
        filter_item_re = re.compile('<li>[^<]*<a class="tdi" href="([^"]+)"[^>]*>([^<]+)</a>[^<]*</li>', re.S)
        for raw_link, raw_title in filter_item_re.findall(content):
            link = self.make_full_link(raw_link, src_link)
            title = self.strip_tags(raw_title)
            list.append(Item(title.decode('utf-8'), link))
        return list

    def get_filter_items_checkbox(self, content, src_link):
        list = []
        prefix_char = '?'
        if src_link.find('?') >= 0: prefix_char = '&'
        filter_item_re = re.compile('<li>[^<]*<div class="checkbox">[^<]*<input type="checkbox" id="[^"]*" name="([^"]+)" value="([^"]+)">[^<]*<label[^>]*>([^<]+)</label>[^<]*</div>[^<]*</li>', re.S)
        for name, value, raw_title in filter_item_re.findall(content):
            link = src_link + prefix_char + name + "=" + value
            title = self.strip_tags(raw_title)
            list.append(Item(title.decode('utf-8'), link))
        return list

    def get_current_filters(self, content, src_link):
        filter_wrapper_re = re.compile('<div class="current-filter">(.*)<div class="loading-wrapper">', re.S)
        filter_wrapper_result = filter_wrapper_re.search(content)
        if filter_wrapper_result is None: return None
        filter_content = filter_wrapper_result.group(1)

        reset_filter_re = re.compile('<li>[^<]*<a class="tdi" data-jnp="i.ResetFilter" href="([^"]+)">([^<]+)</a></li>')
        reset_filter_result = reset_filter_re.search(filter_content)
        if reset_filter_result is None: return None
        
        reset_filter_link = self.make_full_link(reset_filter_result.group(1), src_link)

        current_filters = []
        filter_item_re = re.compile('<li>[^<]*<a href="([^"]+)"[^>]*>([^<]+)<span[^>]+></span></a>[^<]*</li>', re.S)
        for raw_link, raw_title in filter_item_re.findall(filter_content):
            link = self.make_full_link(raw_link, src_link)
            title = self.strip_tags(raw_title)
            current_filters.append(Item(title.decode('utf-8'), link))

        return PageVideoList(None, reset_filter_link, None, current_filters)

    def make_full_link(self, target_link, src_link):
        if target_link is None:
            return None
        target_link = target_link.replace('&amp;','&')
        full_link_re = re.compile('^https?://')
        if full_link_re.match(target_link):
            return target_link
        abs_link_re = re.compile('^/')
        if abs_link_re.match(target_link):
            dom_re = re.compile('^(https?://[^/]+)')
            dom = dom_re.match(src_link).group(1)
            return dom + target_link
        link_re = re.compile('^(https?://[^\?]+)')
        link = link_re.match(src_link).group(1)
        return link + target_link

    def strip_tags(self, string):
        result = re.sub('<[^>]+>', '', string)
        result = result.replace("\n",' ')
        result = result.replace("\t",' ')
        result = result.replace("\r",' ')
        result = re.sub('\s+', ' ', result)
        return result.strip()

class Account:
    def __init__(self, email, password, parser):
        self.page_for_login = 'http://play.iprima.cz/'
        self.auth_params = {
            'nav_remember': 'true',
            'nav_email': email,
            'nav_password': password,
            'nav_redirectUri': self.page_for_login
        }
        self.parser = parser
        self.login_url_re = re.compile('action="(https://[^/]+(?:/tdi)?/login/(?:nav/)?form(?:ular)?[^"]+)"', re.S)
        self.video_list_url = 'http://play.iprima.cz/moje-play'

    def login(self):
        login_url = self.get_login_url()

        content = self.parser.ua.post(login_url, self.auth_params)
        if self.login_url_re.search(content): return False
        return True

    def get_login_url(self):
        content = self.parser.ua.get(self.page_for_login)
        return self.login_url_re.search(content).group(1)
        # https://play.iprima.cz/login/formular?csrfToken=142090b66b24c01af02aa7c23a98d890b667b0cd-1453127273565-b29a993b2a09570ee2da1151
        # https://play.iprima.cz/tdi/login/nav/form?csrfToken=e925f6428ac151c8675ea15fc4cf0b9d09b1613f-1478592531500-e2236dd1ce0b6b725c253abe

class Page:
    def __init__(self, player = None, video_lists = [], filter_lists = [], current_filters = None):
        self.video_lists = video_lists
        self.current_filters  = current_filters
        self.filter_lists = filter_lists
        self.player = player

class PageVideoList:
    def __init__(self, title=None, link=None, next_link=None, item_list=[], thumbnail=None):
        self.title = title
        self.link = link
        self.next_link = next_link
        self.item_list = item_list
        self.thumbnail = thumbnail

class Player:
    def __init__(self, title, video_link, image_url, description, broadcast_date = None, duration = None, year = None):
        self.title = title
        self.video_link = video_link
        self.image_url = image_url
        self.description = description
        self.broadcast_date = broadcast_date
        self.year = year
        self.duration = duration

class NextList:
    def __init__(self, next_link, list):
        self.next_link = next_link
        self.list = list

class Item:
    def __init__(self, title, link, image_url=None, description=None, broadcast_date=None, duration=None, year=None, isFolder=False):
        self.title = title
        self.link = link
        self.image_url = image_url
        self.description = description
        self.broadcast_date = broadcast_date
        self.year = year
        self.duration = duration
        self.isFolder = isFolder
