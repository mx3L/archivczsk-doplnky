# -*- coding: utf-8 -*-
import os
import sys
import traceback
import time
import resolver
import re
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

try:
    from Plugins.Extensions.archivCZSK.engine.client import add_dir, add_video, getSearch, showError, showInfo, \
        showWarning, log, getListInput, set_command
    from Plugins.Extensions.archivCZSK.engine.tools.util import toString
except ImportError:
    showError("PrimaPlay vyzaduje novsiu verziu archivCZSK")

_addon_ = ArchivCZSK.get_xbmc_addon('plugin.video.primaplay')
_scriptname_ = _addon_.getAddonInfo('name')
_version_ = _addon_.getAddonInfo('version')

sys.path.append(os.path.join(_addon_.getAddonInfo('path'), 'resources', 'lib'))
_icon_ = os.path.join(_addon_.getAddonInfo('path'), 'icon.png')

from PrimaPlay import Parser, Account, primalog

_quality = _addon_.getSetting('quality')
primalog.logDebugEnabled = _addon_.getSetting('debug') == 'true'
_hd_enabled = _addon_.getSetting('hd_enabled') == 'true'
_useCache = _addon_.getSetting('use_cache') == 'true'
_play_parser = Parser(hd_enabled=_hd_enabled, useCache=_useCache)

_play_account = None
if (_addon_.getSetting('account_enabled') == 'true'):
    _play_account = Account(_addon_.getSetting('account_email'), _addon_.getSetting('account_password'), _play_parser)
#    primalog.logDebug("ACCOUNT: "+ _addon_.getSetting('account_email') +":"+ _addon_.getSetting('account_password'))


def _exception_log(exc_type, exc_value, exc_traceback):
    primalog.logError(toString(exc_value))
    showError(toString(exc_value))


def main_menu(pageurl, list_only=False):
    page = _play_parser.get_page(pageurl + '?strana=1')
    if not list_only:
        if page.player:
            add_player(page.player)
        else:
            add_search_menu()
            add_account_menu()
        add_filters(page, pageurl)
    for video_list in page.video_lists:
        if video_list.title: add_title(video_list)
        add_item_list(video_list.item_list)
        if video_list.next_link: add_next_link(video_list.next_link)


def shows_menu(pageurl, list_only=False):
    add_dir("ŽIVĚ - Prima", {'action': 'PLAY', 'linkurl': 'https://prima.iprima.cz'}, None, video_item=True)
    add_dir("ŽIVĚ - Prima COOL", {'action': 'PLAY', 'linkurl': 'https://cool.iprima.cz'}, None, video_item=True)
    add_dir("ŽIVĚ - Prima MAX", {'action': 'PLAY', 'linkurl': 'https://max.iprima.cz'}, None, video_item=True)
    add_dir("ŽIVĚ - Prima KRIMI", {'action': 'PLAY', 'linkurl': 'https://krimi.iprima.cz'}, None, video_item=True)
    add_dir("ŽIVĚ - Prima LOVE", {'action': 'PLAY', 'linkurl': 'https://love.iprima.cz'}, None, video_item=True)
    add_dir("ŽIVĚ - Prima ZOOM", {'action': 'PLAY', 'linkurl': 'https://zoom.iprima.cz'}, None, video_item=True)
    add_dir("Velké zprávy", {'action': 'PAGE', 'linkurl': 'https://prima.iprima.cz/porady/velke-zpravy/epizody'}, None)
    add_dir("Prima ZOOM Svět", {'action': 'PAGE', 'linkurl': 'https://prima.iprima.cz/porady/prima-zoom-svet/epizody'}, None)
    add_dir("Show Jana Krause", {'action': 'PAGE', 'linkurl': 'https://prima.iprima.cz/porady/show-jana-krause/epizody'}, None)
    add_dir("Autosalon", {'action': 'PAGE', 'linkurl': 'https://cool.iprima.cz/porady/autosalon/epizody'}, None)
    add_dir("Receptář Prima nápadů", {'action': 'PAGE', 'linkurl': 'https://prima.iprima.cz/receptar-prima-napadu/epizody'}, None)
    add_dir("VŠECHNY POŘADY", {'action': 'CATEGORIES', 'linkurl': pageurl}, None)
#    add_dir("Experiment 21", {'action': 'PAGE', 'linkurl': 'https://cool.iprima.cz/experiment-21'})
#    add_dir("Elitní zabiják", {'action': 'PLAY', 'linkurl': 'https://www.iprima.cz/filmy/elitni-zabijak'}, None, video_item=True)
#    add_search_menu()
#    add_account_menu()

def show_categories(pageurl, list_only=False):
    page = _play_parser.get_shows(pageurl)
    for video_list in page.video_lists:
        if video_list.title: add_show(video_list)
        add_item_list(video_list.item_list)
        if video_list.next_link: add_next_link(video_list.next_link)


def show_navigation(pageurl, list_only=False):
    page = _play_parser.get_show_navigation(pageurl)
    for video_list in page.video_lists:
        if video_list.title: add_title(video_list)


def next_menu(nexturl):
    next_list = _play_parser.get_next_list(nexturl)
    add_item_list(next_list.list)
    if next_list.next_link: add_next_link(next_list.next_link)


def search():
    search_query = getSearch(session)
    if len(search_query) <= 1: return
    main_menu(_play_parser.get_search_url(search_query))


def account():
    if not _play_account.login():
        showWarning('[B]Chyba přihlášení![/B] Zkontrolujte e-mail a heslo.')
        return
    main_menu(_play_account.video_list_url, True)


def remove_filter(removefilterurl):
    link = _play_parser.get_redirect_from_remove_link(removefilterurl)
    main_menu(link)


def manage_filter(pageurl, filterid):
    if filterid is None:
        main_menu(pageurl)
        return

    page = _play_parser.get_page(pageurl)

    filter_list = page.filter_lists[filterid]
    add_id = getListInput(session, map(lambda x: x.title, filter_list.item_list), filter_list.title)
    if add_id < 0:
        main_menu(pageurl)
        return

    main_menu(filter_list.item_list[add_id].link)


def add_filters(page, pageurl):
    if page.current_filters:
        title = u'[B]Odstranit nastavené filtry: [/B]' + ", ".join(
            map(lambda x: x.title, page.current_filters.item_list))
        url = get_menu_link(action='FILTER-REMOVE', linkurl=page.current_filters.link)
        add_dir(title, url)
    for filterid, filter_list in enumerate(page.filter_lists):
        title = u'[B]Nastav filtr: [/B]' + filter_list.title
        url = get_menu_link(action='FILTER-MANAGE', linkurl=pageurl, filterid=filterid)
        add_dir(title, url)


def add_search_menu():
    title = u'[B]Hledej[/B]'
    url = get_menu_link(action='SEARCH')
    add_dir(title, url)


def add_account_menu():
    if _play_account is None: return
    title = u'[B]Můj PLAY[/B]'
    url = get_menu_link(action='ACCOUNT')
    add_dir(title, url)


def add_show(video_list):
    title = video_list.title
    url = None
    if video_list.link:
        url = get_menu_link(action='SHOW-NAV', linkurl=video_list.link)
    add_dir(title, url, video_list.thumbnail)


def add_title(video_list):
    title = video_list.title
    url = None
    if video_list.link:
        url = get_menu_link(action='PAGE', linkurl=video_list.link)
    add_dir(title, url)


def add_item_list(item_list):
    for item in item_list:
        if item.isFolder:
            url = get_menu_link(action='PAGE', linkurl=item.link)
            add_dir(item.title, url)
        else:
            add_dir(item.title, item.link, item.image_url, video_item=True)


def add_next_link(next_link):
    title = u'Další stránka'
    url = get_menu_link(action='PAGE-NEXT', linkurl=next_link)
    add_dir(title, url)


def add_player(player):
    url = get_menu_link(action='RESOLVE', linkurl=player.video_link)
    add_dir(u"[B]Přehraj:[/B] " + player.title, url, player.image_url, video_item=True)


def resolve_videos(link):
    product_id = _play_parser.get_productID(link)
    video = _play_parser.get_video(product_id)

    # '/playlist.m3u8'
    baseUrl = video.link[:video.link.index('playlist.m3u8')]
    manifest = _play_parser.get_manifest(video.link)
    result = []
    for m in re.finditer('#EXT-X-STREAM-INF:.*?ANDWIDTH=(?P<bandwidth>\d+),RESOLUTION=.+\s(?P<chunklist>.+$\s)',manifest, re.MULTILINE):
        itm = {}
        bandwidth = int(m.group('bandwidth'))
        itm['bandwidth'] = bandwidth
        if bandwidth  < 950000:
            itm['quality'] = "288p"
        elif bandwidth >= 950000 and bandwidth < 1150000:
            itm['quality'] = "360p"
        elif bandwidth >= 1150000 and bandwidth < 1660000:
            itm['quality'] = "480p"
        else:
            itm['quality'] = "720p"
        itm['title'] = "%s - %s" % (video.title, itm['quality'])
        itm['url'] = baseUrl + m.group('chunklist').replace('\n', '')
        itm['surl'] = video.title
        primalog.logDebug("item=%s" % itm)
        result.append(itm)

    result = sorted(result, key=lambda i: i['bandwidth'], reverse=True)
    result = resolver.filter_by_quality(result, _quality)
    if len(result) > 0:
        for videoItem in result:
            add_video(videoItem['title'],videoItem['url'])


def get_menu_link(**kwargs):
    return kwargs


action = params.get('action')
linkurl = params.get('linkurl')
filterid = params.get('filterid')

primalog.logDebug("PrimaPlay Parameters!!!")
primalog.logDebug("action: " + str(action))
primalog.logDebug("linkurl: " + str(linkurl))
primalog.logDebug("filterid: " + str(filterid))
try:
    if action == "FILTER-REMOVE":
        remove_filter(linkurl)
        set_command('updatelist')
    if action == "FILTER-MANAGE":
        manage_filter(linkurl, int(filterid))
        set_command('updatelist')
    elif action == "PAGE-NEXT":
        next_menu(linkurl)
        set_command('updatelist')
    elif action == "SEARCH":
        search()
    elif action == "ACCOUNT":
        account()
    elif action == "SHOW-NAV":
        show_navigation(linkurl)
    elif action == "CATEGORIES":
        show_categories(linkurl)
    elif action == "PAGE":
        main_menu(linkurl)
    elif action == "PLAY":
        resolve_videos(linkurl)
    else:
        shows_menu("https://prima.iprima.cz/iprima-api/ListWithFilter/Series/Content?filter=all&featured_queue_name=iprima:hp-featured-series")
except Exception as ex:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    _exception_log(exc_type, exc_value, exc_traceback)
