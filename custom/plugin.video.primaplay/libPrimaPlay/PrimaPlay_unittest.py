# -*- coding: utf-8 -*-

import unittest
import os, sys
import PrimaPlay
import urllib2

os.chdir(os.path.dirname(sys.argv[0]))

user = 'text@example.com';
password = 'password';

class mockTime:
    def time(self):
        return 1450875766

class mockUserAgent:
    def __init__(self, url_map = {}):
        self.ua = PrimaPlay.UserAgent()
        self.url_map = {
            'http://api.play-backend.iprima.cz/prehravac/init?_ts=1450875766&_infuse=1&productId=p135603': lambda url: 'test_player_init.js',
            'http://play.iprima.cz/': lambda url: 'test_homepage.html',
            'http://play.iprima.cz': lambda url: 'test_homepage.html',
            'http://play.iprima.cz/prostreno': lambda url: 'test_filters.html',
            'http://play.iprima.cz/vysledky-hledani-vse?query=prostreno': lambda url: 'test_search_page.html',
            'http://play.iprima.cz/prostreno-IX-9': lambda url: 'test_video_page.html',
            'http://play.iprima.cz/moje-play': lambda url: 'test_moje_play.html',
            'https://play.iprima.cz/tdi/login/nav/form?csrfToken=868668da5dd5d622ddee5738cf226523ccc6b708-1451918185394-55fbc39b6ea5a369d8723b76': lambda url: 'test_homepage_logged.html',
            'http://play.iprima.cz/prostreno?cat[]=EPISODE&src=p14877&sort[]=Rord&sort[]=latest': lambda url: 'test_prostreno_epizody.html',
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4-hd1-hd2.smil/playlist.m3u8': lambda url: self.raise_not_found(url),
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0001/4844/cze-ao-sd1-sd2-sd3-sd4-hd1-hd2.smil/playlist.m3u8': lambda url: 'test_homepage.html',
            'http://api.play-backend.iprima.cz/prehravac/init?_ts=1450875766&_infuse=1&productId=p148175': lambda url: 'test_player_init-2.js',
            'http://play.iprima.cz/cestovani-cervi-dirou-s-morganem-freemanem-ii-9': lambda url: 'test_video_page-2.html',
            'http://play.iprima.cz/prostreno?season=p14894&action=remove': lambda url: 'test_remove_all_filters.html',
            'https://play.iprima.cz/tdi/dalsi?filter=allShows&sort[]=title&offset=54': lambda url: 'test_ajax_response.data',
            'https://play.iprima.cz/tdi/dalsi/prostreno?season=p14877&sort[]=Rord&sort[]=latest&offset=18': lambda url: 'test_ajax_response_p.data'
        }
        self.url_map.update(url_map)

    def get(self, url):
        filename = self._get_filename_from_map(url)
        return self._get_cache(filename)

    def post(self, url, params):
        filename = self._get_filename_from_map(url)
        return self._get_cache(filename)

    def _get_filename_from_map(self, url):
        if not self.url_map.has_key(url):
            print "ERROR! not found in url map: " + url
            raise urllib2.HTTPError(url, 500, 'Internal server error', None, None)
            return
        get_url = self.url_map[url]
        return get_url(url)

    def _get_cache(self, filename):
        fl = open(filename, 'r')
        content = fl.read()
        return content

    def raise_not_found(self, url):
        raise urllib2.HTTPError(url, 404, 'Not found', None, None)

class PrimaPlayUnitTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_player_init_link(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())

        self.assertEqual(prima_play.get_player_init_url('p135603'),
            'http://api.play-backend.iprima.cz/prehravac/init?_ts=1450875766&_infuse=1&productId=p135603')

    def test_get_video_link__sd(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())

        self.assertEqual(prima_play.get_video_link('p135603'),
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4.smil/playlist.m3u8')

    def test_get_video_link__hd(self):
        prima_play = PrimaPlay.Parser(mockUserAgent({
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4-hd1-hd2.smil/playlist.m3u8': lambda url: 'test_homepage.html',
        }), mockTime())

        self.assertEqual(prima_play.get_video_link('p135603'),
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4-hd1-hd2.smil/playlist.m3u8')

    def test_get_video_link__force_sd(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime(), False)

        self.assertEqual(prima_play.get_video_link('p135603'),
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4.smil/playlist.m3u8')

    def test_get_next_list(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())

        next_list = prima_play.get_next_list('https://play.iprima.cz/tdi/dalsi?filter=allShows&sort[]=title&offset=54')
        self.assertEqual(next_list.next_link,
            'https://play.iprima.cz/tdi/dalsi?filter=allShows&sort[]=title&offset=72')

        self.assertEqual(len(next_list.list), 18)
        self.assertEqual(next_list.list[0].title, u'Největší esa mafie 1 Epizoda')
        self.assertEqual(next_list.list[0].link, 'http://play.iprima.cz/nejvetsi-esa-mafie-1')

    def test_get_next_list_series(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())

        next_list = prima_play.get_next_list('https://play.iprima.cz/tdi/dalsi/prostreno?season=p14877&sort[]=Rord&sort[]=latest&offset=18')
        self.assertEqual(next_list.next_link,
            'https://play.iprima.cz/tdi/dalsi/prostreno?season=p14877&sort[]=Rord&sort[]=latest&offset=36')

    def test_get_page__player_page(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        page = prima_play.get_page('http://play.iprima.cz/prostreno-IX-9')

        self.assertEqual(page.player.title, u'Prostřeno!')
        self.assertEqual(page.player.video_link,
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4.smil/playlist.m3u8')
        self.assertEqual(page.player.image_url,
            'http://static.play-backend.iprima.cz/cdn/img/splash169/p135609-p183945/l_xhdpi')
        self.assertEqual(page.player.description,
            'Zábavná porce vašeho oblíbeného pořadu Prostřeno!')
        self.assertEqual(page.player.broadcast_date, '16.12.2015')
        self.assertEqual(page.player.duration, '42 min')
        self.assertEqual(page.player.year, '2015')
        self.assertEqual(len(page.video_lists), 2)
        self.assertEqual(page.video_lists[0].title, u'Další epizody')
        self.assertEqual(page.video_lists[0].link,
            'http://play.iprima.cz/prostreno-IX-9?season=p135603&sort[]=ord&sort[]=Rlatest')
        self.assertEqual(len(page.video_lists[0].item_list), 20)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'Prostřeno! Sezóna 12: Epizoda 9')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/prostreno/videa/prostreno-xii-9')

    def test_get_page__player_page_2(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        page = prima_play.get_page('http://play.iprima.cz/cestovani-cervi-dirou-s-morganem-freemanem-ii-9')

        self.assertEqual(page.player.title, u'Cestování červí dírou s Morganem Freemanem II (7)')
        self.assertEqual(page.player.video_link,
            'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0001/4844/cze-ao-sd1-sd2-sd3-sd4-hd1-hd2.smil/playlist.m3u8')
        self.assertEqual(page.player.image_url, None)

    def test_get_page__homepage(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        page = prima_play.get_page('http://play.iprima.cz')

        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 8)
        self.assertEqual(page.video_lists[1].title, u'Pořady a Seriály')
        self.assertEqual(page.video_lists[1].link, None)
        self.assertEqual(len(page.video_lists[1].item_list), 19)
        self.assertEqual(page.video_lists[1].item_list[0].title,
            u'Ohnivý kuře 32 Epizod')
        self.assertEqual(page.video_lists[1].item_list[0].link,
            'http://play.iprima.cz/ohnivy-kure')
        self.assertTrue(page.video_lists[1].item_list[0].description);
        self.assertEqual(len(page.filter_lists), 3)
        self.assertEqual(page.filter_lists[0].title, u'Žánr')
        self.assertEqual(len(page.filter_lists[0].item_list), 30)
        self.assertEqual(page.filter_lists[0].item_list[0].title, u'Akční')
        self.assertEqual(page.filter_lists[0].item_list[0].link,
            'http://play.iprima.cz?genres[]=p14198')

    def test_get_page__episodes(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        page = prima_play.get_page('http://play.iprima.cz/prostreno?cat[]=EPISODE&src=p14877&sort[]=Rord&sort[]=latest')

        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 1)
        self.assertEqual(page.video_lists[0].title, None)
        self.assertEqual(page.video_lists[0].link, None)
        self.assertEqual(page.video_lists[0].next_link,
            'https://play.iprima.cz/tdi/dalsi/prostreno?season=p14877&sort[]=Rord&sort[]=latest&offset=18')
        self.assertEqual(len(page.video_lists[0].item_list), 18)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'Praha Sezóna 3: Epizoda 10')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/prostreno-ix-10')

        self.assertEqual(len(page.filter_lists), 3)
        self.assertEqual(page.filter_lists[0].title, u'Řada')

        self.assertEqual(len(page.filter_lists[0].item_list), 11)
        self.assertEqual(page.filter_lists[0].item_list[0].title, u'Sezóna 1')
        self.assertEqual(page.filter_lists[0].item_list[0].link,
            'http://play.iprima.cz/prostreno?season=p14883&sort[]=Rord&sort[]=latest')

    def test_get_page__search(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        page = prima_play.get_page('http://play.iprima.cz/vysledky-hledani-vse?query=prostreno')

        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 3)
        self.assertEqual(page.video_lists[0].title, u'Mezi seriály')
        self.assertEqual(page.video_lists[0].link,
            'http://play.iprima.cz/vysledky-hledani?query=prostreno&searchGroup=SERIES')
        self.assertEqual(len(page.video_lists[0].item_list), 2)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'VIP PROSTŘENO! 3 Řady , 32 Epizod')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/vip-prostreno')

    def test_get_page__current_filters(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        page = prima_play.get_page('http://play.iprima.cz/prostreno')

        self.assertEqual(page.current_filters.link,
            'https://play.iprima.cz/tdi/filtr/zrusit/prostreno?availability=new&season=p14894')
        self.assertEqual(len(page.current_filters.item_list), 2)
        self.assertEqual(page.current_filters.item_list[0].title, u'Novinky')
        self.assertEqual(page.current_filters.item_list[0].link,
            'http://play.iprima.cz/prostreno?season=p14894&action=remove')

    def test_get_redirect_from_remove_link(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        self.assertEqual(prima_play.get_redirect_from_remove_link("http://play.iprima.cz/prostreno?season=p14894&action=remove"),
            'http://play.iprima.cz/prostreno')

    def test_Account_login(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        parser_account = PrimaPlay.Account( user, password, prima_play )
        self.assertEqual(parser_account.login(), True)

    def test_get_page__moje_play(self):
        prima_play = PrimaPlay.Parser(mockUserAgent(), mockTime())
        page = prima_play.get_page('http://play.iprima.cz/moje-play')

        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 1)
        self.assertEqual(page.video_lists[0].title, u'Moje oblíbené Spravovat oblíbené')
        self.assertEqual(page.video_lists[0].link, None)
        self.assertEqual(len(page.video_lists[0].item_list), 1)
        self.assertEqual(page.video_lists[0].item_list[0].title,
            u'Prostřeno! 13 Řad , 1023 Epizod')
        self.assertEqual(page.video_lists[0].item_list[0].link,
            'http://play.iprima.cz/prostreno')
        self.assertEqual(len(page.filter_lists), 0)

if __name__ == '__main__':
    unittest.main()
