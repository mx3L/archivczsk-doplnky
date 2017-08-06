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
import json
from base64 import b64decode, b64encode

__name__ = 'streamujtv'


def supports(url):
    return _regex(url) is not None


def resolve(url):
    m = _regex(url)
    if m:
        util.init_urllib()
        data = util.request(url)
        if data.find('Toto video neexistuje') > 0:
            util.error('Video bylo smazano ze serveru')
            return
        player = 'http://www.streamuj.tv/new-flash-player/mplugin4.swf'
        headers = {
            'User-Agent': util.UA,
            'Referer': 'http://www.streamuj.tv/mediaplayer/player.swf',
            'Cookie': ','.join("%s=%s" % (c.name, c.value) for c in util._cookie_jar)
        }
        burl = b64decode('aHR0cDovL2Z1LWNlY2gucmhjbG91ZC5jb20vcGF1dGg=')
        key = util.request(
            'http://www.streamuj.tv/_key.php?auth=3C27f5wk6qB3g7nZ5SDYf7P7k1572rFH1QxV0QQ')
        index = 0
        result = []
        qualities = re.search(r'rn\:[^\"]*\"([^\"]*)', data, re.IGNORECASE | re.DOTALL)
        langs = re.search(r'langs\:[^\"]*\"([^\"]+)', data, re.IGNORECASE | re.DOTALL)
        languages = ['']  # pretend there is at least language so we read 1st stream info
        if langs:
            languages = langs.group(1).split(',')
        for language in languages:
            streams = re.search(r'res{index}\:[^\"]*\"([^\"]+)'.format(index=index),
                                data, re.IGNORECASE | re.DOTALL)
            subs = re.search(r'sub{index}\:[^\"]*\"([^\"]+)'.format(index=index),
                             data, re.IGNORECASE | re.DOTALL)
            if subs:
                subs = re.search(r'[^>]+>([^,$]+)', subs.group(1), re.IGNORECASE | re.DOTALL)
            else:
                subs = None
            if streams and qualities:
                streams = streams.group(1).split(',')
                rn = qualities.group(1).split(',')
                qindex = 0
                for stream in streams:
                    res = json.loads(util.post_json(burl, {
                        'link': stream, 'player': player, 'key': key
                    }))
                    stream = res['link']
                    q = rn[qindex]
                    if q == 'HD':
                        q = '720p'
                    else:
                        q = 'SD'
                    item = {
                        'url': stream,
                        'quality': q,
                        'headers': headers,
                        'lang': language
                    }
                    if subs:
                        link = subs.group(1)
                        response = json.loads(util.post_json(burl, {
                            'link': link, 'player': player, 'key': key
                        }))
                        if 'link' in response:
                            item['lang'] += ' + subs'
                            item['subs'] = response[u'link']
                        else:
                            util.error("Could not fetch subtitles from '{}'".format(link))
                            util.error("Server response: {}".format(response))
                    result.append(item)
                    qindex += 1
            index += 1
        return result


def _regex(url):
    return re.search(r'streamuj\.tv/video/', url, re.IGNORECASE | re.DOTALL)
