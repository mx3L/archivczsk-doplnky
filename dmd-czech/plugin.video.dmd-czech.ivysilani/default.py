# -*- coding: utf-8 -*-
import urllib2, urllib, re, os, time, datetime
from parseutils import *
from urlparse import urlparse
from util import addDir, addLink, addSearch, getSearch
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
#import json
import simplejson as json



__baseurl__ = 'http://www.ceskatelevize.cz/ivysilani'
#__dmdbase__ = 'http://iamm.netuje.cz/xbmc/stream/'
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
#swfurl = 'http://img8.ceskatelevize.cz/libraries/player/flashPlayer.swf?version=1.43'
swfurl = 'http://img.ceskatelevize.cz/libraries/player/flashPlayer.swf?version=1.45.5'
__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.ivysilani')
home = __settings__.get_info('path')
icon = os.path.join(home, 'icon.png')
search = os.path.join( home, 'search.png' )
nexticon = os.path.join(home, 'nextpage.png')
page_pole_url = []
page_pole_no = []
bonus_video = __settings__.get_setting('bonus-video')

DATE_FORMAT = '%d.%m.%Y'
DAY_NAME = (u'Po', u'Út', u'St', u'Čt', u'Pá', u'So', u'Ne')

RE_DATE   = re.compile('(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})')


def OBSAH():
    addDir('Nejnovější pořady',__baseurl__+'/?nejnovejsi=vsechny-porady',12,icon)
    addDir('Nejsledovanější videa týdne',__baseurl__+'/?nejsledovanejsi=tyden',11,icon)
    addDir('Podle data',__baseurl__+'/podle-data-vysilani/',5,icon)
    addDir('Podle abecedy',__baseurl__+'/podle-abecedy/',2,icon)
    addDir('Podle kategorie',__baseurl__,1,icon)
    addDir('Vyhledat...(beta)','0',13,search)
    addDir('Živé iVysílání',__baseurl__+'/ajax/liveBox.php?time=',4,icon)

def KATEGORIE():
    addDir('Filmy',__baseurl__+'/filmy/',3,icon)
    addDir('Seriály',__baseurl__+'/serialy/',3,icon)
    addDir('Dokumenty',__baseurl__+'/dokumenty/',3,icon)  
    addDir('Sport',__baseurl__+'/sportovni/',3,icon)  
    addDir('Hudba',__baseurl__+'/hudebni/',3,icon)  
    addDir('Zábava',__baseurl__+'/zabavne/',3,icon)  
    addDir('Děti a mládež',__baseurl__+'/deti/',3,icon)  
    addDir('Vzdělání',__baseurl__+'/vzdelavaci/',3,icon)  
    addDir('Zpravodajství',__baseurl__+'/zpravodajske/',3,icon)  
    addDir('Publicistika',__baseurl__+'/publicisticke/',3,icon)  
    addDir('Magazíny',__baseurl__+'/magaziny/',3,icon)  
    addDir('Náboženské',__baseurl__+'/nabozenske/',3,icon)  
    addDir('Všechny',__baseurl__+'/zanr-vse/',3,icon)  

def LIVE_OBSAH(url):
    url = url+str(time.time())
    program=[r'ČT1 - ', r'ČT2 - ', r'ČT24 - ', r'ČT4 - ', r'ČTD/ART - ']
    i = 0
    request = urllib2.Request(url)
    request.add_header("Referer",__baseurl__)    
    request.add_header("Origin","http://www.ceskatelevize.cz")
    request.add_header("Accept","*/*")
    request.add_header("X-Requested-With","XMLHttpRequest")
    request.add_header("x-addr","127.0.0.1")
    request.add_header("User-Agent",_UserAgent_)
    request.add_header("Content-Type","application/x-www-form-urlencoded")
    con = urllib2.urlopen(request)
    # Read lisk XML page
    data = con.read()
    con.close()
    doc = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)

    items = doc.find('div', 'clearfix')
    for item in items.findAll('div', 'channel'):
            prehrano = item.find('div','progressBar')
            prehrano = prehrano['style']
            prehrano = prehrano[(prehrano.find('width:') + len('width:') + 1):]
            #name_a = item.find('p')
            try:
                name_a = item.find('a')
                name = program[i]+name_a.getText(" ").encode('utf-8')+'- Přehráno: '+prehrano.encode('utf-8')
                url = 'http://www.ceskatelevize.cz'+str(item.a['href'])
                thumb = str(item.img['src'])
            except:
                name = program[i]+'Právě teď běží pořad, který nemůžeme vysílat po internetu.'
                thumb = 'http://img7.ceskatelevize.cz/ivysilani/gfx/empty/noLive.png'
            #print name, thumb, url
            addDir(name,url,14,thumb)
            i=i+1
def ABC(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<a class="pageLoadAjaxAlphabet" href="(.+?)" rel="letter=.+?"><span>(.+?)</span></a>').findall(httpdata)
    for link,name in match:
        #print name,__baseurl__+link
        addDir(name,'http://www.ceskatelevize.cz'+link,3,icon)

def CAT_LIST(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    
    cat_iter_regex = '<li>.+?a class=\"toolTip\"(.+?)href=\"(?P<url>.+?)\".*?title=\"(?P<desc>.*?)\".*?>(?P<title>[^<]+)(.*?)</li>'
    httpdata = httpdata[httpdata.find('clearfix programmesList'):]
    for m in re.finditer(cat_iter_regex, httpdata, re.DOTALL):
        link = m.group('url')
        desc = m.group('desc')
        name = m.group('title')
        if m.group('url').find('labelBonus') != -1:
            name = name + ' (pouze bonusy)'
            if not bonus_video:
                continue 
        infoLabels = {'title':name, 'plot':desc}
        #print name,link
        addDir(name, 'http://www.ceskatelevize.cz' + link, 6, icon, infoLabels=infoLabels)


# =============================================

# vypis CT1,CT2,CT24,CT4
def DAY_LIST(url):
    doc = read_page(url)
    data = doc.find("ul", {"id": "channels"})  
    items = data.findAll("li")
    kanaly=[]
    for ite in items:
        rows = ite.findAll("span", attrs={'class' : 'logo'})
        for it in rows:
                item = it.find('img')
                icons= item['src']
                name = item['alt'].encode('utf-8').strip()
                addDir(name,url,9,icons)


def DAY_PROGRAM_LIST( url, chnum ):
    doc = read_page(url)
    data = doc.find('div', {"id": "programme"})
    items = data.findAll('ul')
    nazvy=['ČT1', 'ČT2', 'ČT24', 'ČT sport', 'ČT :D', 'ČT Art']
    count=-1
    for it1 in items:
        count += 1    
        if count != nazvy.index(chnum):
                continue
        it2 = it1.findAll('div',{'class': 'overlay'})
        for it3 in it2:
                name = it3.find('a', {'class':'title'})
                if name == None:
                        name = it3.find('strong', {'class':'title'})
                name = name.getText(" ").encode('utf-8')
               
                cas  = it3.find("span", {"class": "time"})
                cas  = cas.getText(" ").encode('utf-8')
                #icons = it3.find("img")
                #icons = icon['src']

                link = it3.find("a")
                if link != None:
                        link = str(link['href'])
                        addDir(cas+' '+name,'http://www.ceskatelevize.cz'+link,10,icon)
                else:
                        name = name +' - pořad se ještě nevysílá.'
                        thumb = 'http://img7.ceskatelevize.cz/ivysilani/gfx/empty/noLive.png'
                        addDir(cas+' '+name, url, 10, thumb)


def date2label(date):
     dayname = DAY_NAME[date.weekday()]
     return "%s %s.%s.%s" % (dayname, date.day, date.month, date.year)


def DATE_LIST(url):
     pole_url = url.split("/")
     date = pole_url[len(pole_url) - 1]
     if date:
         date = datetime.date(*time.strptime(date, DATE_FORMAT)[:3])
     else:
         date = datetime.date.today()
     # Add link to previous month virtual folder
     pdate = date - datetime.timedelta(days=30)
     addDir('Předchozí měsíc (%s)' % date2label(pdate).encode('utf-8'), __baseurl__ + '/' + pdate.strftime(DATE_FORMAT), 5, icon)
     for i in range(0, 30):
           pdate = date - datetime.timedelta(i)
           addDir(date2label(pdate).encode('utf-8'), __baseurl__ + '/' + pdate.strftime(DATE_FORMAT), 8, icon)


# vypis nejsledovanejsi za tyden
def MOSTVISITED(url):
    doc = read_page(url)
    #items = doc.find('ul', 'clearfix content','mostWatchedBox')    
    items = doc.find(id="mostWatchedBox")    
    for item in items.findAll('a'):
            name = item.getText(" ").encode('utf-8')
            link = str(item['href'])
            item = item.find('img')
            icons = item['src']
            #print "LINK: "+link
            addDir(name, 'http://www.ceskatelevize.cz' + link, 10, icons)

# vypis nejnovejsich poradu
def NEWEST(url):
    doc = read_page(url)
    items = doc.find(id="newestBox")    
    for item in items.findAll('a'):
            name = item.getText(" ").encode('utf-8')
            link = str(item['href'])
            item = item.find('img')
            icons = item['src']
            #print "LINK: "+link
            addDir(name, 'http://www.ceskatelevize.cz' + link, 10, icons)


# =============================================


def VIDEO_LIST(url, video_listing= -1):
    program_single_start = '<div id="programmeInfoDetlail">'
    program_single_end = '<div id="programmePlayer">'
    program_multi_start = '<div id="programmeMoreBox" class="clearfix">'
    program_multi_end = '<div id="programmeRelated">'
    single_regex = '<a href=\"(?P<url>[^"]+).*?<h2>(?P<title>[^<]+)<\/h2>.*?<p>(?P<desc>[^<]+)<\/p>'
    iter_regex = '<li class=\"itemBlock (clearfix|clearfix active).*?<a class=\"itemImage\".*?src=\"(?P<img>[^"]+).*?<a class=\"itemSetPaging\".*?href=\"(?P<url>[^"]*).+?>(?P<title>[^<]+).*?<\/li>'
    paging_regex = '<div class=\"pagingContent clearfix\">.*?<td class=\"center\">(?P<page>[^<]+)</td>.*<td class=\"right\".*?<a.*?href=\"(?P<nexturl>[^"]+).*?<\/a>'
    
    link = url
    if not re.search('dalsi-casti', url):
        link = url + 'dalsi-casti/'
        
    req = urllib2.Request(link)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    #doc = read_page(link)
    if re.search('Bonusy', str(httpdata), re.U) and video_listing == -1:
        bonuslink = url + 'bonusy/'
        if re.search('dalsi-casti', url):
            bonusurl = re.compile('(.+?)dalsi-casti/?').findall(url)
            bonuslink = bonusurl[0] + 'bonusy/'
        addDir('Bonusy', bonuslink, 7, nexticon)
        print 'Bonusy = True - ' + url + 'bonusy/'
    #items = doc.find('ul', 'clearfix content')
    if re.search('Ouha', httpdata, re.U):
        bonuslink = url + 'bonusy/'
        BONUSY(bonuslink)
        
        
    item_single = True
    
    multidata = httpdata[httpdata.find(program_multi_start):httpdata.find(program_multi_end)]
    items = re.compile(iter_regex, re.DOTALL).finditer(multidata)
    
    for item in items:
        item_single = False
        thumb = item.group('img')
        name = item.group('title').strip()
        url = 'http://www.ceskatelevize.cz' + item.group('url')
        url = re.sub('porady', 'ivysilani', url)
        print item.group('url'), item.group('title').strip()
        addDir(name, url, 10, thumb)
    
    if item_single:
        program_single_start = '<div id="programmeInfoDetail">'
        program_single_end = 'div id="programmePlayer">'
        singledata = httpdata[httpdata.find(program_single_start):httpdata.find(program_single_end)]
        #print singledata
        item = re.search(single_regex, singledata, re.DOTALL)
        print item.group('url'), item.group('title').strip(), item.group('desc')
        
        name = item.group('title').strip()
        popis = item.group('desc')
        url = 'http://www.ceskatelevize.cz' + item.group('url')
        url = re.sub('porady', 'ivysilani', url)
        infoLabels = {'title':name, 'plot':popis}
        addDir(name, url, 10, None, infoLabels=infoLabels)
               
    try:
        pager = re.search(paging_regex, multidata, re.DOTALL)
        act_page = pager.group('page').split()
        #print act_page,next_page_i
        next_url = pager.group('nexturl')
        next_label = 'Další strana (Zobrazena videa ' + act_page[0] + '-' + act_page[2] + ' ze ' + act_page[4] + ')'
        #print next_label,next_url
        
        video_listing_setting = int(__settings__.get_setting('video-listing'))
        if video_listing_setting > 0:
                next_label = 'Další strana (celkem ' + act_page[4] + ' videí)'
        if (video_listing_setting > 0 and video_listing == -1):
                if video_listing_setting == 3:
                        video_listing = 99999
                elif video_listing_setting == 2:
                        video_listing = 3
                else:
                        video_listing = video_listing_setting
        if (video_listing_setting > 0 and video_listing > 0):
                VIDEO_LIST('http://ceskatelevize.cz' + next_url, video_listing - 1)
        else:
                print next_label, 'http://www.ceskatelevize.cz' + next_url
                addDir(next_label, 'http://www.ceskatelevize.cz' + next_url, 6, nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'

def BONUSY(link):
    doc = read_page(link)
    items = doc.find('ul', 'clearfix content')
    if re.search('Ouha', str(items), re.U):
        link = url + 'bonusy/'
        BONUSY(link)
    for item in items.findAll('li', 'itemBlock clearfix'):
        name_a = item.find('h3')
        name_a = name_a.find('a')
        name = name_a.getText(" ").encode('utf-8')
        if len(name) < 2:
            name = 'Titul bez názvu'
        url = 'http://www.ceskatelevize.cz' + str(item.a['href'])
        url = re.sub('porady', 'ivysilani', url)
        thumb = str(item.img['src'])
        #print name, thumb, url
        addDir(name, url, 10, thumb)
    try:
        pager = doc.find('div', 'pagingContent')
        act_page_a = pager.find('td', 'center')
        act_page = act_page_a.getText(" ").encode('utf-8')
        act_page = act_page.split()
        next_page_i = pager.find('td', 'right')
        #print act_page,next_page_i
        next_url = next_page_i.a['href']
        next_label = 'Další strana (Zobrazena videa ' + act_page[0] + '-' + act_page[2] + ' ze ' + act_page[4] + ')'
        #print next_label,next_url
        addDir(next_label, 'http://www.ceskatelevize.cz' + next_url, 7, nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'
       
       
def HLEDAT(url):
    #https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=20&hl=cs&prettyPrint=false&source=gcsc&gss=.cz&sig=981037b0e11ff304c7b2bfd67d56a506&cx=000499866030418304096:fg4vt0wcjv0&q=vypravej+tv&googlehost=www.google.com&callback=google.search.Search.apiary6680&nocache=1360011801862
    #https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=20&start=20&hl=cs&prettyPrint=false&source=gcsc&gss=.cz&sig=981037b0e11ff304c7b2bfd67d56a506&cx=000499866030418304096:fg4vt0wcjv0&q=vypravej+tv&googlehost=www.google.com&callback=google.search.Search.apiary6680&nocache=1360011801862
    if url == '0':
            what = getSearch(session)
            if not what == '':
                what = re.sub(' ', '+', what)
                url2 = 'https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=20&hl=cs&prettyPrint=false&source=gcsc&gss=.cz&sig=981037b0e11ff304c7b2bfd67d56a506&cx=000499866030418304096:fg4vt0wcjv0&q=' + what + '&googlehost=www.google.com&callback=google.search.Search.apiary6680&nocache=1360011801862'
    else:
        match_page = re.compile('start=([0-9]+)').findall(url)
        match2 = re.compile('q=(.+?)&googlehost').findall(url)
        next_page = int(match_page[0]) + 20
        url2 = url
    req = urllib2.Request(url2)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('google.search.Search.apiary6680\((.*)\)').findall(httpdata)
    items = json.loads(match[0])[u'results']
    for item in items:
        print item
        name = item[u'titleNoFormatting']
        name = name.encode('utf-8')
        url2 = item[u'url']
        try:
            image = item[u'richSnippet'][u'cseImage'][u'src']
            image = image.encode('utf-8')
        except:
            image = icon
        if re.search('diskuse', url2, re.U):
            continue
        #if not re.search('([0-9]{15}-)', url, re.U):
        #continue
        addDir(name, url2, 10, image)
    if url == '0':
        next_url = 'https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=20&start=20&hl=cs&prettyPrint=false&source=gcsc&gss=.cz&sig=981037b0e11ff304c7b2bfd67d56a506&cx=000499866030418304096:fg4vt0wcjv0&q=' + what + '&googlehost=www.google.com&callback=google.search.Search.apiary6680&nocache=1360011801862'
        next_title = '>> Další strana (výsledky 0 - 20)'
        addDir(next_title, next_url, 13, nexticon)
    else:
        next_url = 'https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=20&start=' + str(next_page) + '&hl=cs&prettyPrint=false&source=gcsc&gss=.cz&sig=981037b0e11ff304c7b2bfd67d56a506&cx=000499866030418304096:fg4vt0wcjv0&q=' + match2[0] + '&googlehost=www.google.com&callback=google.search.Search.apiary6680&nocache=1360011801862'
        next_title = '>> Další strana (výsledky ' + str(match_page[0]) + ' - ' + str(next_page) + ')'
        addDir(next_title, next_url, 13, nexticon)



def VIDEOLINK(url, name, live):
    if name.find('pořad se ještě nevysílá')!=-1:
        return
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    #match = re.compile('callSOAP\((.+?)\)').findall(httpdata)
    match = re.compile('callSOAP\((.*)\)').findall(httpdata)
    print "VIDEO-LINK URL: " + url
    print match[0]
    info = re.compile('<meta name="description" content="(.+?)"').findall(httpdata)
    if len(info) < 1:
            info = re.compile('<title>(.+?)&mdash').findall(httpdata)
    #RE_PLAYLIST_URL = re.compile('callSOAP\((.+?)\)')
    # Converting text to dictionary
    query = json.loads(match[0])
    # Converting dictionary to text arrays    options[UserIP]=xxxx&options[playlistItems][0][..]....
    strquery = http_build_query(query)
    # Ask a link page XML
    request = urllib2.Request('http://www.ceskatelevize.cz/ajax/playlistURL.php')
    request.add_data(strquery)
    request.add_header("Referer", url)    
    request.add_header("Origin", "http://www.ceskatelevize.cz")
    request.add_header("Accept", "*/*")
    request.add_header("X-Requested-With", "XMLHttpRequest")
    request.add_header("x-addr", "127.0.0.1")
    request.add_header("User-Agent", _UserAgent_)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    con = urllib2.urlopen(request)
    # Read lisk XML page
    data = con.read()
    con.close()
    doc = read_page(urllib.unquote(data))
    items = doc.find('body')
    for item in items.findAll('switchitem'):
        match = re.compile('<switchitem id="(.+?)" base="(.+?)"').findall(str(item))
        for id, base in match:
            base = re.sub('&amp;', '&', base)
            if re.search('AD', id, re.U):
                continue
            video = re.compile('<video src="(.+?)" system-bitrate=".+?" label="(.+?)" enabled=".+?"').findall(str(item))
            for cesta, kvalita in video:
                if live:
                    rtmp_url = base+'/'+cesta
                else:
                    app = base[base.find('/', base.find('://') + 3) + 1:]
                    rtmp_url = base + ' app=' + app + ' playpath=' + cesta
                addLink(kvalita + ' ' + name, rtmp_url, icon, info[0])
                #print rtmp_url,kvalita+info[0] #vystupni parametry RTMP


def http_build_query(params, topkey=''):
    from urllib import quote_plus
   
    if len(params) == 0:
       return ""
 
    result = ""

    # is a dictionary?
    if type (params) is dict:
       for key in params.keys():
           newkey = quote_plus (key)
           
           if topkey != '':
              newkey = topkey + quote_plus('[' + key + ']')
           
           if type(params[key]) is dict:
              result += http_build_query (params[key], newkey)

           elif type(params[key]) is list:
                i = 0
                for val in params[key]:
                    if type(val) is dict:
                       result += http_build_query (val, newkey + '[' + str(i) + ']')

                    else:
                       result += newkey + quote_plus('[' + str(i) + ']') + "=" + quote_plus(str(val)) + "&"

                    i = i + 1              

           # boolean should have special treatment as well
           elif type(params[key]) is bool:
                result += newkey + "=" + quote_plus(str(int(params[key]))) + "&"

           # assume string (integers and floats work well)
           else:
                try:
                  result += newkey + "=" + quote_plus(str(params[key])) + "&"       # OPRAVIT ... POKUD JDOU U params[key] ZNAKY > 128, JE ERROR, ALE FUNGUJE TO I TAK
                except:
                  result += newkey + "=" + quote_plus("") + "&"  

    # remove the last '&'
    if (result) and (topkey == '') and (result[-1] == '&'):
       result = result[:-1]      
 
    return result


url = None
name = None
thumb = None
mode = None

try:
        url = urllib.unquote_plus(params["url"])
except:
        pass
try:
        name = urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode = int(params["mode"])
except:
        pass


print "Mode: " + str(mode)
print "URL: " + str(url)
print "Name: " + str(name)


if mode == None or url == None or len(url) < 1:
        print ""
        OBSAH()
       
elif mode == 1:
        print ""
        KATEGORIE()

elif mode == 2:
        print "" + url
        ABC(url)

elif mode == 3:
        print "" + url
        CAT_LIST(url)

elif mode == 4:
        print "" + url
        LIVE_OBSAH(url)

elif mode == 5:
        print "" + url
        DATE_LIST(url)

elif mode == 6:
        print "" + url
        VIDEO_LIST(url)

elif mode == 7:
        print "" + url
        BONUSY(url)

elif mode == 8:
        print "" + url
        DAY_LIST(url)

elif mode == 9:
        print "" + url
        DAY_PROGRAM_LIST(url, name)

elif mode == 10:
        print "" + url
        VIDEOLINK(url, name, False)

elif mode == 11:
        print "" + url
        MOSTVISITED(url)

elif mode == 12:
        print "" + url
        NEWEST(url)
       
elif mode == 13:
        print "" + url
        HLEDAT(url)
        
elif mode == 14:
        print "" + url
        VIDEOLINK(url, name, True)
