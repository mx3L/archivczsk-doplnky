import os
import util, xbmcprovider, xbmcutil, resolver
from provider import ResolveException
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK

__scriptid__ = 'plugin.video.dvtv.cz'
__scriptname__ = 'dvtv.cz'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)

__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting

sys.path.append(os.path.join (__addon__.getAddonInfo('path'), 'resources', 'lib'))
import dvtv
settings = {'quality':__addon__.getSetting('quality')}


class DVTVXBMCContentProvider(xbmcprovider.XBMCMultiResolverContentProvider):

    def play(self, params):
        stream = self.resolve(params['play'])
        print type(stream)
        if type(stream) == type([]):
            sdict={}
            for s in stream:
                if s['surl'] not in sdict:
                    sdict[s['surl']] = s
                if len(sdict) > 1:
                    break
            else:
                return xbmcprovider.XBMCMultiResolverContentProvider.play(self,params)

            # resolved to mutliple files, we'll feed playlist and play the first one
            playlist = []
            i = 0
            for video in stream:
                i += 1
                if 'headers' in video.keys():
                    playlist.append(xbmcutil.create_play_it(params['title'] + " [" + str(i) + "]", "", video['quality'], video['url'], subs=video['subs'], filename=params['title'], headers=video['headers']))
                else:
                    playlist.append(xbmcutil.create_play_it(params['title'] + " [" + str(i) + "]", "", video['quality'], video['url'], subs=video['subs'], filename=params['title']))
            xbmcutil.add_playlist(params['title'], playlist)
        elif stream:
            if 'headers' in stream.keys():
                xbmcutil.add_play(params['title'], "", stream['quality'], stream['url'], subs=stream['subs'], filename=params['title'], headers=stream['headers'])
            else:
                xbmcutil.add_play(params['title'], "", stream['quality'], stream['url'], subs=stream['subs'], filename=params['title'])

    def resolve(self, url):
        def select_cb(resolved):
            stream_parts = []
            stream_parts_dict = {}

            for stream in resolved:
                if stream['surl'] not in stream_parts_dict:
                    stream_parts_dict[stream['surl']] = []
                    stream_parts.append(stream['surl'])
                stream_parts_dict[stream['surl']].append(stream)

            if len(stream_parts) == 1:
                quality = self.settings['quality'] or '0'
                resolved = resolver.filter_by_quality(stream_parts_dict[stream_parts[0]], quality)
                # if user requested something but 'ask me' or filtered result is exactly 1
                if len(resolved) == 1 or int(quality) > 0:
                    return resolved[0]
                return resolved
            # requested to play all streams in given order - so return them all
            return [stream_parts_dict[p][0] for p in stream_parts]

        item = self.provider.video_item()
        item.update({'url':url})
        try:
            return self.provider.resolve(item, select_cb=select_cb)
        except ResolveException, e:
            self._handle_exc(e)

DVTVXBMCContentProvider(dvtv.DVTVContentProvider(),settings, __addon__,session).run(params)