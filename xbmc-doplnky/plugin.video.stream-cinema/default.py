# -*- coding: UTF-8 -*-
#/*
# *      Copyright (C) 2017 bbaron
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
sys.path.append( os.path.join ( os.path.dirname(__file__),'myprovider') )

from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
import re
import util,xbmcprovider,xbmcutil
import uuid
from scinema import StreamCinemaContentProvider
from scinema import StaticDataSC




__scriptid__   = 'plugin.video.stream-cinema'
__scriptname__ = 'stream-cinema.online'
__addon__      = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__   = __addon__.getLocalizedString
__gets         = __addon__.getSetting
__sets         = __addon__.setSetting

def generateNewDeviceid():
    try:
        tmp = str(uuid.uuid4())
        mac = str(uuid.uuid1(uuid.getnode(),0))[24:]
        idx = tmp.index('-')
        tmp = tmp[idx:]
        idx = tmp.index('-')
        tmp = tmp[idx+1:]
        return 'e2-mac-'+mac+tmp
    except:
        try:
            import random
            import string
            return 'e2-rnd-'+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))
        except:
            return 'e2-empty'
        pass
def getDeviceUid():
    uid = str(__gets('deviceid'))
    try:
        if uid.startswith('e2-mac-'):
            # recheck mac address
            iddev =str(uuid.uuid1(uuid.getnode(),0))[24:]
            setiddev = uid[6:]
            idx = setiddev.index('-')
            setiddev = setiddev[:-idx]
            if setiddev != iddev:
                uid = generateNewDeviceid()
                __sets('deviceid', uid)
            return uid
        else:
            if uid.startswith('e2-rnd-') or uid == 'e2-empty':
                return uid
            else:
                # generate new 
                uid = generateNewDeviceid()
                __sets('deviceid', uid)
                return uid
    except:
        uid = generateNewDeviceid()
        __sets('deviceid', uid)
        return uid
        pass
def fixXcursor():
    try:
        login = __gets('wsuser')
        pwd = __gets('wspass')
        if 'XcursorX' in login:
            login = str(login).replace('XcursorX','')
            __sets('wsuser', login)
        if 'XcursorX' in pwd:
            pwd = str(pwd).replace('XcursorX','')
            __sets('wspass', pwd)
    except:
        pass
def checkSetVIP(u, p):
    try:
        tmp = StaticDataSC(username=u, password=p)
        __sets('wsvipdays', tmp.vipDaysLeft)
    except:
        pass


settings = {'quality':__addon__.getSetting('quality')}

reverse_eps = __gets('order-episodes') == '0'

# fix crazy entry by virtual keyboard
fixXcursor()
# set number of days left for VIP account
checkSetVIP(__gets('wsuser'), __gets('wspass'))


scinema = StreamCinemaContentProvider(username=__gets('wsuser'),password=__gets('wspass'),reverse_eps=reverse_eps)
# must set again (reason: singleton)
scinema.wsuser = __gets('wsuser')
scinema.wspass = __gets('wspass')
# must set again (reason: singleton)
scinema.deviceUid = getDeviceUid()
scinema.itemOrderGenre = __gets('item_order_genre')
scinema.itemOrderCountry = __gets('item_order_country')
scinema.itemOrderQuality = __gets('item_order_quality')
scinema.session = session

scinema.write("PARAMS="+str(params))

print("Running stream cinema provider with params:", params)
xbmcprovider.XBMCMultiResolverContentProvider(
    scinema,
    settings,
    __addon__, 
    session
).run(params)


