# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,random,decimal
from parseutils import *
from urlparse import urlparse
from util import addDir, addLink,addSearch, getSearch,showWarning
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
__baseurl__ = 'http://www.stream.cz/ajax/'
__dmdbase__ = 'http://iamm.netuje.cz/xbmc/stream/'
__cdn_url__ = 'http://cdn-dispatcher.stream.cz/?id='
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
__settings__ = ArchivCZSK.get_addon('plugin.video.dmd-czech.stream')
home = __settings__.get_info('path')
icon = os.path.join(home, 'icon.png')
nexticon = os.path.join(home, 'nextpage.png') 
page_pole_url = []
page_pole_no = []
searchurl = __baseurl__+'/?a=search&search_text='
user_name =__settings__.get_setting('user_name')

def replace_words(text, word_dic):
    rc = re.compile('|'.join(map(re.escape, word_dic)))
    def translate(match):
        return word_dic[match.group(0)]
    return rc.sub(translate, text)

word_dic = {
'\u00e1': 'á',
'\u00e9': 'é',
'\u00ed': 'í',
'\u00fd': 'ý',
'\u00f3': 'ó',
'\u00fa': 'ú',
'\u016f': 'ů',
'\u011b': 'ě',
'\u0161': 'š',
'\u0165': 'ť',
'\u010d': 'č',
'\u0159': 'ř',
'\u017e': 'ž',
'\u010f': 'ď',
'\u0148': 'ň',
'\u00C0': 'Á',
'\u00c9': 'É',
'\u00cd': 'Í',
'\u00d3': 'Ó',
'\u00da': 'Ú',
'\u016e': 'Ů',
'\u0115': 'Ě',
'\u0160': 'Š',
'\u010c': 'Č',
'\u0158': 'Ř',
'\u0164': 'Ť',
'\u017d': 'Ž',
'\u010e': 'Ď',
'\u0147': 'Ň',
'\\xc3\\xa1': 'á',
'\\xc4\\x97': 'é',
'\\xc3\\xad': 'í',
'\\xc3\\xbd': 'ý',
'\\xc5\\xaf': 'ů',
'\\xc4\\x9b': 'ě',
'\\xc5\\xa1': 'š',
'\\xc5\\xa4': 'ť',
'\\xc4\\x8d': 'č',
'\\xc5\\x99': 'ř',
'\\xc5\\xbe': 'ž',
'\\xc4\\x8f': 'ď',
'\\xc5\\x88': 'ň',
'\\xc5\\xae': 'Ů',
'\\xc4\\x94': 'Ě',
'\\xc5\\xa0': 'Š',
'\\xc4\\x8c': 'Č',
'\\xc5\\x98': 'Ř',
'\\xc5\\xa4': 'Ť',
'\\xc5\\xbd': 'Ž',
'\\xc4\\x8e': 'Ď',
'\\xc5\\x87': 'Ň',
}


def OBSAH():
    addDir('Všechny Pořady','listShows',1,icon)
    addDir('Komerční pořady','listCommercials',1,icon)
    #addDir('Partnerské pořady',__baseurl__+'/',4,icon)
    #addDir('Komerční videa',__baseurl__+'/?m=stream&a=commercial_channel',5,icon)   
    #addDir('Uživatelská videa',__baseurl__+'/kategorie/2-uzivatelska-videa',2,icon)
    #addDir('Hledat...',__baseurl__,13,icon)
    #addDir('Moje videa',__baseurl__,15,icon)
    
def INDEX(url):
    link = __baseurl__+'get_catalogue?0.'+str(gen_random_decimal(9999999999999999))
    req = urllib2.Request(link)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<ul id="'+url+'" class="shows clearfix">(.+?)</ul>', re.S).findall(httpdata)
    match2 = re.compile('<a href="/porady/(.+?)" class=".+?" data-show-id="(.+?)" data-action=".+?">(.+?)<img src="(.+?)"', re.S).findall(match[0])
    for link, id, name, thumb in match2:
            name = str.strip(name)
            link = __baseurl__+'get_series?show_url='+link+'&0.'+str(gen_random_decimal(9999999999999999))
            addDir(name,link,7,thumb)

def LIST(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    match = re.compile('<a href=".+?" data-action=".+?" data-episode-id="(.+?)">(.+?)</a>', re.S).findall(httpdata)
    for id, name in match:
            link = __baseurl__+'get_video_source?context=catalogue&id='+id+'&0.'+str(gen_random_decimal(9999999999999999))
            addDir(name,link,10,icon)

def VIDEOLINK(url,name):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    #httpdata = replace_words(httpdata, word_dic).encode('utf-8')
    name = re.compile('"episode_name": "(.+?)"', re.S).findall(httpdata)
    #items = json.loads(httpdata)[u'instances']
    stream = re.compile('\{"instances": \[\{"source": "(.+?)", "type": "video/mp4", "quality_label": ".+?", "quality": "(.+?)"}').findall(httpdata)
    name = replace_words(name[0], word_dic)
    for stream_url, quality in stream:
        print stream_url,quality
        addLink(quality+' '+name,stream_url,'',name)
            
def MY_VIDEO(url):
    if url == __baseurl__:
        if user_name == '':
            xbmc.executebuiltin("XBMC.Notification('Doplněk DMD JOJ','Zadejte uživ.jméno nebo email!',30000,"+icon+")")
            __settings__.openSettings()
        if re.search('@', user_name, re.U):
            match = re.compile('(.+?)@(.+)').findall(user_name)
            for name,email in match:
                url = __baseurl__+ '/profil/' + email + '/'+ name
        else:
            url = __baseurl__+ '/profil/' + user_name
        print url            
        doc = read_page(url)
        items = doc.find('div', 'boxVideo txtRight')
        url = __baseurl__+str(items.a['href'])
        print url
    doc = read_page(url)
    items = doc.find('div', 'vertical670Box')
    for item in items.findAll('div', 'videoList'):
            name_a = item.find('h5')
            name_a = name_a.find('a') 
            name = name_a.getText(" ").encode('utf-8')
            link = __baseurl__+str(item.a['href'])
            thumb = item.find('a', 'videoListImg')
            thumb = thumb['style']
            thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
            thumb = thumb[:(thumb.find(')') - 1)]
            #print name, thumb, url
            addDir(name,link,20,thumb)
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page) - 1
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no)-1
        url_page = int(max_page_count)-1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = item['href']
            #next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu '+str(next_page)+' z '+max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label,__baseurl__+next_url,15,nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'

def LIST_UZIVATEL(url):
    doc = read_page(url)
    items = doc.find('div', 'vertical670Box')
    for item in items.findAll('div', 'matrixThreeVideoList'):
            name_a = item.find('h5')
            name_a = name_a.find('a') 
            name = name_a.getText(" ").encode('utf-8')
            link = __baseurl__+str(item.a['href'])
            thumb = item.find('a', 'videoListImg')
            thumb = thumb['style']
            thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
            thumb = thumb[:(thumb.find(')') - 1)]
            #print name, thumb, url
            addDir(name,link,20,thumb)
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page) - 1
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no)-1
        url_page = int(max_page_count)-1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = item['href']
            #next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu '+str(next_page)+' z '+max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label,__baseurl__+next_url,6,nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'


def SEARCH():
                search = getSearch(session)
                encode = urllib.quote(search)
                link = searchurl+encode
                doc = read_page(link)
                #items = doc.find('div', 'orderTabInner orderTabInnerG')
                #for item in items.findAll('a'):
                #    name = '>> '+item.getText(" ").encode('utf-8')+' <<'
                #    url = __baseurl__+str(item['href'])
                #    if re.match('>> Vše <<', name, re.U):
                #        continue
                #   #print name, url
                #    addDir(name,url,6,icon)		
                items = doc.find('div', 'vertical540Box')
                for item in items.findAll('div', 'videoList'):
                    name_a = item.find('h5')
                    name_a = name_a.find('a') 
                    name = name_a.getText(" ").encode('utf-8')
                    url = __baseurl__+str(item.a['href'])
                    thumb = item.find('a', 'videoListImg')
                    thumb = thumb['style']
                    thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
                    thumb = thumb[:(thumb.find(')') - 1)]
                    #print name, thumb, url
                    addDir(name,url,20,thumb)
                try:
                    pager = doc.find('div', 'paging')
                    act_page_a = pager.find('strong',)
                    act_page = act_page_a.getText(" ").encode('utf-8')
                    next_page = int(act_page) + 1        
                    next_url_no = int(act_page)
                    for item in pager.findAll('a'):
                        page_url = item['href'].encode('utf-8')
                        page_no = item.getText(" ").encode('utf-8')
                        page_pole_url.append(page_url)
                        page_pole_no.append(page_no)
                        max_page_count = len(page_pole_no)-1
                        url_page = int(max_page_count)-1
                        if  re.match('další', page_pole_no[max_page_count], re.U):
                            next_url = item['href']
                            #next_url = page_pole_url[next_url_no]
                            max_page = page_pole_no[url_page]
                            next_label = '>> Přejít na stranu '+str(next_page)+' z '+max_page
                            #print next_label,__baseurl__+next_url
                            addDir(next_label,__baseurl__+next_url,14,nexticon)
                except:
                    print 'STRANKOVANI NENALEZENO!'

def SEARCH2(url):
                doc = read_page(url)
                #items = doc.find('div', 'orderTabInner orderTabInnerG')
                #for item in items.findAll('a'):
                #    name = '>> '+item.getText(" ").encode('utf-8')+' <<'
                #    url = __baseurl__+str(item['href'])
                #    if re.match('>> Vše <<', name, re.U):
                #        continue
                #   #print name, url
                #    addDir(name,url,6,icon)		
                items = doc.find('div', 'vertical540Box')
                for item in items.findAll('div', 'videoList'):
                    name_a = item.find('h5')
                    name_a = name_a.find('a') 
                    name = name_a.getText(" ").encode('utf-8')
                    url = __baseurl__+str(item.a['href'])
                    thumb = item.find('a', 'videoListImg')
                    thumb = thumb['style']
                    thumb = thumb[(thumb.find('url(') + len('url(') + 1):] 
                    thumb = thumb[:(thumb.find(')') - 1)]
                    #print name, thumb, url
                    addDir(name,url,20,thumb)
                try:
                    pager = doc.find('div', 'paging')
                    act_page_a = pager.find('strong',)
                    act_page = act_page_a.getText(" ").encode('utf-8')
                    next_page = int(act_page) + 1        
                    next_url_no = int(act_page)
                    for item in pager.findAll('a'):
                        page_url = item['href'].encode('utf-8')
                        page_no = item.getText(" ").encode('utf-8')
                        page_pole_url.append(page_url)
                        page_pole_no.append(page_no)
                        max_page_count = len(page_pole_no)-1
                        url_page = int(max_page_count)-1
                        if  re.match('další', page_pole_no[max_page_count], re.U):
                            next_url = item['href']
                            #next_url = page_pole_url[next_url_no]
                            max_page = page_pole_no[url_page]
                            next_label = '>> Přejít na stranu '+str(next_page)+' z '+max_page
                            #print next_label,__baseurl__+next_url
                            addDir(next_label,__baseurl__+next_url,14,nexticon)
                except:
                    print 'STRANKOVANI NENALEZENO!'
    
                


def PAGER(doc):
    try:
        pager = doc.find('div', 'paging')
        act_page_a = pager.find('strong',)
        act_page = act_page_a.getText(" ").encode('utf-8')
        next_page = int(act_page) + 1        
        next_url_no = int(act_page) - 1
        for item in pager.findAll('a'):
            page_url = item['href'].encode('utf-8')
            page_no = item.getText(" ").encode('utf-8')
            page_pole_url.append(page_url)
            page_pole_no.append(page_no)
        max_page_count = len(page_pole_no)-1
        url_page = int(max_page_count)-1
        if  re.match('další', page_pole_no[max_page_count], re.U):
            next_url = page_pole_url[next_url_no]
            max_page = page_pole_no[url_page]
            next_label = 'Přejít na stranu '+str(next_page)+' z '+max_page
            #print next_label,__baseurl__+next_url
            addDir(next_label,__baseurl__+next_url,5,nexticon)
    except:
        print 'STRANKOVANI NENALEZENO!'


def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param


def gen_random_decimal(d):
        return decimal.Decimal('%d' % (random.randint(0,d)))


url=None
name=None
thumb=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
        print ""
        OBSAH()
       
elif mode==1:
        print ""
        INDEX(url)

elif mode==6:
        print ""+url
        LIST_UZIVATEL(url)

elif mode==7:
        print ""+url
        LIST(url)


elif mode==13:
        print ""+url
        SEARCH()
elif mode==14:
        print ""+url
        SEARCH2(url)  

elif mode==15:
        print ""+url
        MY_VIDEO(url)       

elif mode==10:
        print ""+url
        VIDEOLINK(url,name)
