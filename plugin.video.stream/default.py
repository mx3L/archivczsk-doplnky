# -*- coding: utf-8 -*-
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine import client

addon = ArchivCZSK.get_addon('plugin.video.stream')
home = addon.get_info('path')
icon = os.path.join( home, 'icon.png' ) 

client.add_operation("SHOW_MSG", {'msg': 'Vyvoj tohoto doplnku byl ukoncen z duvodu ukonceni webu www.stream.cz. Pouzijte jiz novy doplnek Televize Seznam, kde jsou take vsechny porady ze Stream TV!', 'msgType': 'info', 'msgTimeout': 30, 'canClose': True })
