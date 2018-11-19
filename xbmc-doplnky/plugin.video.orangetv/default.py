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

__scriptid__   = 'plugin.video.orangetv'
__scriptname__ = 'orangetv.sk'
__addon__      = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__   = __addon__.getLocalizedString
__gets         = __addon__.getSetting
__sets         = __addon__.setSetting

sys.path.append(os.path.join (__addon__.getAddonInfo('path'), 'resources', 'lib'))
from orangetv import OrangeTvContentProvider, OrangeTvProvider, orangelog

prov = OrangeTvContentProvider(username=__gets('orangetvuser'),password=__gets('orangetvpwd'),)
prov.wsuser = __gets('orangetvuser')
prov.wspass = __gets('orangetvpwd')
prov.session = session
settings = {'quality':__addon__.getSetting('quality')}

orangelog.logDebug("PARAMS=%s"%params)
OrangeTvProvider(prov,settings,__addon__, session).run(params)