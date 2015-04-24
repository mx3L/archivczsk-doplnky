# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2011 Lubomir Kucera
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
import re
import util

__author__ = 'Lubomir Kucera'
__name__ = 'exashare'


def supports(url):
    return re.search(r'exashare\.com/embed\-[^\.]+\.html', url) is not None


def resolve(url):
    playlist = re.search(r'playlist:\s*\[.+?file:\s*\"([^\"]+)\"', util.request(url), flags=re.S)
    if playlist:
        return [{'url': playlist.group(1), 'quality': '???'}]
    return None
