# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2013 Maros Ondrasek
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
sys.path.append(os.path.join (os.path.dirname(__file__), 'resources', 'lib'))
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
import gordonura
import xbmcprovider, xbmcutil
import util, resolver
from provider import ResolveException


__scriptid__ = 'plugin.video.gordon.ura.cz'
__scriptname__ = 'gordon.ura.cz'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__ = __addon__.getLocalizedString

class GordonUraXBMCContentProvider(xbmcprovider.XBMCMultiResolverContentProvider):
    
    def resolve(self, url):
        def select_cb(resolved):
            quality = self.settings['quality'] or '0'
            resolved = resolver.filter_by_quality(resolved, quality)
            # if user requested something but 'ask me' or filtered result is exactly 1
            if len(resolved) == 1 or int(quality) > 0:
                return resolved[0]
            return resolved

        item = self.provider.video_item()
        item.update({'url':url})
        try:
            return self.provider.resolve(item, select_cb=select_cb)
        except ResolveException, e:
            self._handle_exc(e)
        
    

settings = {'quality':__addon__.getSetting('quality')}
provider = gordonura.GordonUraContentProvider()

GordonUraXBMCContentProvider(provider, settings, __addon__,session).run(params)