# -*- coding: utf-8 -*-

import unittest
import os, sys
import PrimaPlay
import urllib, urllib2, urlparse

os.chdir(os.path.dirname(sys.argv[0]))

class UrlCmp(object):
    def __init__(self, url):
        parts = urlparse.urlparse(url)
        _query = frozenset(urlparse.parse_qsl(parts.query))
        parts = parts._replace(query=_query)
        self.parts = parts
        self.url = url

    def __eq__(self, other):
        return self.parts == other.parts

    def __hash__(self):
        return hash(self.parts)

    def __str__(self):
        return self.url

    def __repr__(self):
        return self.url

class CacheUserAgent(PrimaPlay.UserAgent):
    def __init__(self, cache_dir = None):
        super(CacheUserAgent, self).__init__()
        self._init_cache_dir(cache_dir)

    def get(self, url):
        content = super(CacheUserAgent, self).get(url)
        if self.cache_dir: self._save_content(url, content)
        return content

    def post(self, url, params):
        content = super(CacheUserAgent, self).post(url, params)
        if self.cache_dir: self._save_content(url, content)
        return content

    def _init_cache_dir(self, cache_dir):
        self.cache_dir = cache_dir
        if not self.cache_dir: return
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _save_content(self, url, content):
        filename = self._generate_filename(url)
        fl = open(filename, 'w')
        fl.write(content)
        fl.close()

    def _generate_filename(self, url):
        return self.cache_dir + '/' + urllib.quote_plus(url)

class PrimaPlayIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.play_parser = PrimaPlay.Parser(CacheUserAgent())
        self.account_user = os.environ.get('PRIMA_USER')
        self.account_password = os.environ.get('PRIMA_PASSWORD')

    def test_homepage(self):
        page = self.play_parser.get_page('http://play.iprima.cz')
        self.assertEqual(page.player, None)
        self.assertTrue(len(page.video_lists))
        self.assertEqual(page.video_lists[0].title, u'Doporučujeme')
        self.assertTrue(len(page.video_lists[0].item_list))
        self.assertEqual(len(page.filter_lists), 3)
        self.assertEqual(page.filter_lists[0].title, u'Žánr')
        self.assertTrue(len(page.filter_lists[0].item_list))
        page.filter_lists[0].item_list.sort(key=lambda elem: elem.title)
        self.assertEqual(page.filter_lists[0].item_list[0].title, u'Akční')
        self.assertEqual(page.filter_lists[0].item_list[0].link,
            'http://play.iprima.cz?genres[]=p14198')

    def test_prostreno(self):
        page = self.play_parser.get_page('http://play.iprima.cz/prostreno')
        self.assertEqual(page.player, None)
        self.assertEqual(len(page.video_lists), 3)
        self.assertRegexpMatches(page.video_lists[0].title, u'^Všechny epizody')
        self.assertEqual(len(page.video_lists[0].item_list), 20)

    def test_prostreno_epizodes(self):
        page = self.play_parser.get_page('http://play.iprima.cz/prostreno')
        epizodes_page = self.play_parser.get_page(page.video_lists[0].link)
        self.assertEqual(epizodes_page.player, None)
        self.assertEqual(len(epizodes_page.video_lists), 1)
        self.assertEqual(len(epizodes_page.video_lists[0].item_list), 18)
        self.assertEqual(UrlCmp(epizodes_page.video_lists[0].next_link),
            UrlCmp('https://play.iprima.cz/tdi/dalsi/prostreno?cat[]=EPISODE&src=p14877&sort[]=latest&sort[]=Rord&offset=18'))

    def test_prostreno_video(self):
        page = self.play_parser.get_page('http://play.iprima.cz/prostreno')
        video_page = self.play_parser.get_page(page.video_lists[0].item_list[0].link)

        self.assertRegexpMatches(video_page.player.title, u'Prostřeno!')
        self.assertRegexpMatches(video_page.player.video_link, '-sd3-sd4.*\.m3u8')
        self.assertRegexpMatches(video_page.player.image_url, '/l_xhdpi')
        self.assertRegexpMatches(video_page.player.description, 'Prostřeno!')
        self.assertRegexpMatches(video_page.player.broadcast_date, '^\d+\.\d+\.\d+$')

    def test_prostreno_epizodes_next_page(self):
        page = self.play_parser.get_page('http://play.iprima.cz/prostreno')
        epizodes_page = self.play_parser.get_page(page.video_lists[0].link)
        next_page = self.play_parser.get_next_list(epizodes_page.video_lists[0].next_link)
        self.assertEqual(UrlCmp(next_page.next_link),
            UrlCmp('https://play.iprima.cz/tdi/dalsi/prostreno?cat[]=EPISODE&src=p14877&sort[]=Rord&sort[]=latest&offset=36'))

    def test_account(self):
        if not self.account_user: return self.skipTest("Account credentials must be defined in environment (PRIMA_USER, PRIMA_PASSWORD) for account testing")
        account = PrimaPlay.Account(self.account_user, self.account_password, self.play_parser)
        try:
            self.assertTrue(account.login())
        except urllib2.HTTPError, e:
            print "URL: " + e.url
            raise
        self.assertTrue(self.play_parser.get_page(account.video_list_url))



if __name__ == '__main__':
    unittest.main()

