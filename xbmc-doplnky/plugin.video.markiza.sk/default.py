# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2014 Maros Ondrasek
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

__scriptid__ = 'plugin.video.markiza.sk'
__scriptname__ = 'markiza.sk'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)

__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting

sys.path.append(os.path.join (__addon__.getAddonInfo('path'), 'resources', 'lib'))
from markiza import markizalog, MarkizaContentProvider
settings = {'quality':__addon__.getSetting('quality')}
markizalog.logDebugEnabled = __addon__.getSetting('debug')=='true'


class MarkizaXBMCContentProvider(xbmcprovider.XBMCMultiResolverContentProvider):
    def render_video(self, item):
        date = item.get('date')
        if date:
            item['title'] = '%s - %s' %(item['title'], date)
        super(MarkizaXBMCContentProvider, self).render_video(item)
    #def play(self, params):
        # @TODO tu by trebalo pretazit a pridat tam playlist aby to hralo v jednej kvalite samozrejme
        # a tak ci tak neviem ci to na VTi 11 nepadne

markizalog.logDebug("PARAMS=%s"%params)
cp = MarkizaContentProvider(quality=settings['quality'])
cp.useCache = __addon__.getSetting('use_cache')=='true'
MarkizaXBMCContentProvider(cp, settings, __addon__, session).run(params)
