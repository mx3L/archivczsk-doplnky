# -*- coding: UTF-8 -*-
#/*
# *      Copyright (C) 2013 Libor Zoubek + jondas
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

sys.path.append( os.path.join ( os.path.dirname(__file__),'resources','lib') )
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
import re
import util,xbmcprovider,xbmcutil
from sosac import SosacContentProvider

__scriptid__   = 'plugin.video.sosac.ph'
__scriptname__ = 'sosac.ph'
__addon__      = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__   = __addon__.getLocalizedString
__set          = __addon__.getSetting


settings = {'quality':__addon__.getSetting('quality'), 'subs':__set('subs') == 'true'}

reverse_eps = __set('order-episodes') == '0'

print("Running sosac provider with params:", params)
xbmcprovider.XBMCMultiResolverContentProvider(SosacContentProvider(reverse_eps=reverse_eps),settings,__addon__, session).run(params)


