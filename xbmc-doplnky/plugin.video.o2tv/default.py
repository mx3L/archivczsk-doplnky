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

import os
import util, xbmcprovider, xbmcutil, resolver
from provider import ResolveException
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__scriptid__   = 'plugin.video.o2tv'
__scriptname__ = 'o2tv.sk'
__addon__      = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__   = __addon__.getLocalizedString
__gets         = __addon__.getSetting
__sets         = __addon__.setSetting

sys.path.append(os.path.join (__addon__.getAddonInfo('path'), 'resources', 'lib'))
from o2tv import O2TvContentProvider, o2log
o2log.logDebugEnabled = __gets('debug_enabled') == 'true'

def getDeviceUid():
    uid = str(__gets('deviceid'))
    try:
        if len(uid)>5:
            return uid
        uid = ''
        import uuid
        mac = uuid.getnode()
        o2log.logDebug("##### UID_hex=%s"%mac)
        hx = hex((mac*7919)%(2**64))
        o2log.logDebug("##### UID_hex=%s"%hx)
        uid = str('0000000000000000'+hx[2:-1])[-16:]
        o2log.logDebug("##### UID_xx=%s"%uid)
        __sets('deviceid', uid)
        return uid
    except:
        o2log.logError('Generate UID from MAC failed, get random.')
        import random
        uid = ''.join([random.choice('0123456789abcdef') for x in range(16)])
        __sets('deviceid', uid)
        return uid
    __sets('deviceid', 'empty-uid')
    return 'empty-uid'


prov = O2TvContentProvider(username=__gets('o2tvuser'), password=__gets('o2tvpwd'))
prov.usr = __gets('o2tvuser')
prov.pwd = __gets('o2tvpwd')
prov.devId = getDeviceUid()
prov.showEpg = __gets('show_epg')=='true'
prov.session = session
settings = {'quality': __gets('quality')}
if __gets('stream_quality') == '1':
    prov.streamQuality = 'SD' # HD default
if __gets('o2lang') == '0':
    prov.o2language = 'slo'
else:
    prov.o2language = 'ces'

#o2log.logDebug("PARAMS=%s"%params)
xbmcprovider.XBMCMultiResolverContentProvider(prov,settings,__addon__, session).run(params)