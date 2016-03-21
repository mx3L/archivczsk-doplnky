# -*- coding: utf-8 -*-
import os
import sys
import traceback
import m3u8

from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
try:
    from Plugins.Extensions.archivCZSK.engine.client import add_dir, add_video, getSearch, showError, showInfo, showWarning, log, getListInput, set_command
    from Plugins.Extensions.archivCZSK.resources.libraries import m3u8
except ImportError:
    showError("PrimaPlay vyzaduje novsiu verziu archivCZSK")

sys.path.append(os.path.join (os.path.dirname(__file__), 'libPrimaPlay'))

import PrimaPlay

_addon_ = ArchivCZSK.get_xbmc_addon('plugin.video.primaplay')
_scriptname_ = _addon_.getAddonInfo('name')
_version_ = _addon_.getAddonInfo('version')

###############################################################################
def _log(msg, level=0):
    if type(msg).__name__ == 'unicode':
        msg = msg.encode('utf-8')
    if level == 0:
        log.debug("[%s] %s" % (_scriptname_, msg.__str__()))
    else:
        log.error("[%s] %s" % (_scriptname_, msg.__str__()))

def logDbg(msg):
    _log(msg, level=0)

def logErr(msg):
    _log(msg, level=1)

def _exception_log(exc_type, exc_value, exc_traceback):
    logErr(traceback.format_exception(exc_type, exc_value, exc_traceback))
    showError(_toString(exc_value))
    
def _toString(text):
    if type(text).__name__ == 'unicode':
        output = text.encode('utf-8')
    else:
        output = str(text)
    return output

_icon_ = os.path.join(_addon_.getAddonInfo('path'), 'icon.png')
_hd_enabled = False;
if (_addon_.getSetting('hd_enabled') == 'true'): _hd_enabled = True
_play_parser = PrimaPlay.Parser(hd_enabled=_hd_enabled)
_play_account = None
if (_addon_.getSetting('account_enabled') == 'true'):
    _play_account = PrimaPlay.Account( _addon_.getSetting('account_email'), _addon_.getSetting('account_password'), _play_parser )

def main_menu(pageurl, list_only = False):
    page = _play_parser.get_page(pageurl)
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
        title = u'[B]Odstranit nastavené filtry: [/B]' + ", ".join(map(lambda x: x.title, page.current_filters.item_list))
        url = get_menu_link( action = 'FILTER-REMOVE', linkurl = page.current_filters.link )
        add_dir(title, url)
    for filterid, filter_list in enumerate(page.filter_lists):
        title = u'[B]Nastav filtr: [/B]' + filter_list.title
        url = get_menu_link( action = 'FILTER-MANAGE', linkurl = pageurl, filterid = filterid )
        add_dir(title, url)

def add_search_menu():
    title = u'[B]Hledej[/B]'
    url = get_menu_link( action = 'SEARCH' )
    add_dir(title, url)

def add_account_menu():
    if _play_account is None: return
    title = u'[B]Můj PLAY[/B]'
    url = get_menu_link( action = 'ACCOUNT' )
    add_dir(title, url)

def add_title(video_list):
    title = '[B]'+video_list.title+'[/B]'
    url = None
    if video_list.link:
        url = get_menu_link( action = 'PAGE', linkurl = video_list.link )
    add_dir(title, url)

def add_item_list(item_list):
    for item in item_list:
        url = get_menu_link( action = 'PAGE', linkurl = item.link )
        add_dir(item.title, url, item.image_url, {'label':item.title, 'plot':item.description})

def add_next_link(next_link):
    title = u'Další stránka'
    url = get_menu_link( action = 'PAGE-NEXT', linkurl = next_link )
    add_dir(title, url)

def add_player(player):
    url = get_menu_link( action = 'RESOLVE', linkurl = player.video_link )
    add_dir(u"[B]Přehraj:[/B] " + player.title, url, player.image_url, video_item=True)

def resolve_videos(link):
    m3u8_obj = m3u8.load(link)
    if m3u8_obj.is_variant:
        streams = []
        for i in m3u8_obj.playlists:
            streams.append((i.uri, i.stream_info.resolution, i.stream_info.bandwidth))
        streams.sort(key=lambda x:x[2], reverse=True)
        streams.sort(key=lambda x:x[1], reverse=True)
        for idx, (url, resolution, bandwidth) in enumerate(streams):
            if resolution and bandwidth:
                title = "%sx%s - %dKB/s" % (resolution[0], resolution[1], bandwidth/1024/8)
            elif resolution:
                title = "%sx%s" % (resolution[0], resolution[1])
            elif bandwidth:
                title = "%dKB/s" % (bandwidth/1024/8)
            else:
                title = str(idx)
            add_video(title, link[:link.rfind('/') + 1] + url)
    else:
        add_video("video", link)


def get_menu_link(**kwargs):
    return kwargs

action = params.get('action')
linkurl = params.get('linkurl')
filterid = params.get('filterid')

logDbg("PrimaPlay Parameters!!!")
logDbg("action: "+str(action))
logDbg("linkurl: "+str(linkurl))
logDbg("filterid: "+str(filterid))
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
    elif action == "PAGE":
        main_menu(linkurl)
    elif action == "RESOLVE":
        resolve_videos(linkurl)
    else:
        main_menu("http://play.iprima.cz")
except Exception as ex:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    _exception_log(exc_type, exc_value, exc_traceback)

