# -*- coding: utf-8 -*-
"""
Created by mx3L

TA3 video addon for archivCZSK
easily portable to XBMC

Rewritten from C# to Python
C# source is from mponlinevideos2 project
added HLS links

Big thx to original author
"""


import urllib, urllib2
import re
from util import addDir, addLink

baseUrl = "http://www.ta3.com/archiv.html"
baseLiveUrl = "http://www.ta3.com/live.html"

dynamicCategoryStart = '<div class="archive">'
dynamicCategoryEnd = r'<div class="inside archive-filter">'
categoryStartRegex = r'<a href="(?P<categoryUrl>[^<]*)">(?P<categoryTitle>[^<]*)</a>'
showsStart = r'<ul class="items">'
showsEnd = r"</ul>"
showBlockStartRegex = r"<li"
showUrlAndTitleRegex = r'<a href="(?P<showUrl>[^"]*)"><span class="vicon"></span>(?P<showTitle>[^<]*)</a>'
showEpisodeNextPageStart = r'<li class="next">'
showEpisodeNextPageRegex = r'<a href="(?P<url>[^"]*)">'

videoIdStart = r"arrTa3VideoPlayer.push"
videoIdEnd = r"));"
videoIdAndTypeRegex = r'(?P<videoId>[0-9A-Z]{8}\-[0-9A-Z]{4}\-[0-9A-Z]{4}\-[0-9A-Z]{4}\-[0-9A-Z]{12})"\,[\s]*"(?P<videoType>[0-9]*)'
playerOfflineUrl = r"http://embed.livebox.cz/ta3/player-offline.js"
playerOnlineUrl = r"http://embed.livebox.cz/ta3/player-live.js"
videoTypeArray = [ r"Videoteka/mp4:", r"VideotekaEncoder/mp4:"]
videoUrlPrefixRegex = r"prefix:[\s]*'(?P<prefix>[^']+)"
videoUrlPostfixRegex = r"postfix:[\s]*'(?P<postfix>[^']+)"
videoIdLiveRegex = r"videoID0:[\s]*'(?P<videoId>[^']+)"
videoLowIdLiveRegex = r"videoID1:[\s]*'(?P<videoLowId>[^']+)"
videoMediumIdLiveRegex = r"videoID2:[\s]*'(?P<videoMediumId>[^']+)"
videoHighIdLiveRegex = r"videoID3:[\s]*'(?P<videoHighId>[^']+)"


currentStartIndex = 0
hasNextPage = False

def request(url, headers={}):
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    return data


def DiscoverDynamicCategories():
    dynamicCategoriesCount = 0;
    baseWebData = request(baseUrl)
    startIndex = baseWebData.find(dynamicCategoryStart)
    print startIndex
    if startIndex > 0:
        endIndex = baseWebData.find(dynamicCategoryEnd, startIndex)
        baseWebData = baseWebData[startIndex:] if endIndex == -1 else baseWebData[startIndex:endIndex]
        #print baseWebData
        #match = re.match(categoryStartRegex,baseWebData)
        for match in re.finditer(categoryStartRegex, baseWebData):
            categoryUrl = match.group("categoryUrl")
            categoryTitle = match.group("categoryTitle")
            #print match.start()
            #print match.end() - match.start()
            #print match.length
            addDir(categoryTitle, categoryUrl, 1, None)
            dynamicCategoriesCount += 1
            categoriesDiscovered = True
        #addDir("Live", baseLiveUrl, 1, None)
        return dynamicCategoriesCount;                

    
#DiscoverDynamicCategories()

def GetPageVideos(pageUrl):
    if pageUrl is not None:
        nextPageUrl = None
        if pageUrl == baseLiveUrl:
            nextPageUrl = None
            addDir("Live", pageUrl, 2, None)
        else:
            baseWebData = request(pageUrl)
            shows = None
            index = baseWebData.find(showsStart)
            if (index > 0):
                endIndex = baseWebData.find(showsEnd, index);
                shows = baseWebData[index:] if endIndex == -1 else baseWebData[index:endIndex]
                #showEpisodeBlockStart= re.search(showBlockStartRegex, shows)
                while True:
                #for showEpisodeBlockStart in re.finditer(showBlockStartRegex, shows):
                    #print shows
                    showEpisodeBlockStart = re.search(showBlockStartRegex, shows)
                    if showEpisodeBlockStart is not None:
                        shows = shows[showEpisodeBlockStart.end():]
                        showTitle = None
                        showThumbUrl = None
                        showUrl = None
                        showLength = None
                        showDescription = None
                        showEpisodeUrlAndTitle = re.search(showUrlAndTitleRegex, shows)
                        if showEpisodeUrlAndTitle:
                            showUrl = showEpisodeUrlAndTitle.group("showUrl")
                            showTitle = showEpisodeUrlAndTitle.group("showTitle")
                            shows = shows[showEpisodeUrlAndTitle.end():]
                            #print shows
                        else:
                            break
                        addDir(showTitle, showUrl, 2, image=showThumbUrl, infoLabels={'Title':showTitle, 'Length':showLength, 'Plot':showDescription})
                    else:
                        break

            index = baseWebData.find(showEpisodeNextPageStart)
            if (index > 0):
                baseWebData = baseWebData[index:]
                nextPageMatch = re.search(showEpisodeNextPageRegex, baseWebData)
                nextPageUrl = nextPageMatch.group("url") if nextPageMatch else None
            else:
                nextPageUrl = None
            if nextPageUrl:
                addDir('Ďaľšia strana', nextPageUrl, 1, None)
                

def GetVideoLink(videoUrl):
    baseWebData = request(videoUrl);
    showUrl = None
    if (videoUrl != baseLiveUrl):
        headers = {'Referer': videoUrl, 'User-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1'}
        playerOfflineWebData = request(playerOfflineUrl, headers);
        startIndex = baseWebData.find(videoIdStart);
        if (startIndex >= 0):
            endIndex = baseWebData.find(videoIdEnd, startIndex);
            if (endIndex >= 0):
                videoId = ''
                videoType = 0
                prefix = ''
                postfix = ''
                videoIdAndType = baseWebData[startIndex:endIndex]
                match = re.search(videoIdAndTypeRegex, videoIdAndType)
                if match is not None:
                    videoId = match.group("videoId")
                    videoType = match.group("videoType")
                    if videoType is not None and videoType != '':
                        videoType = int(videoType)
                match = re.search(videoUrlPrefixRegex, playerOfflineWebData);
                if match is not None:
                    prefix = match.group("prefix")
                match = re.search(videoUrlPostfixRegex, playerOfflineWebData);
                if match is not None:
                    postfix = match.group("postfix")
                    
                showUrl_lq = prefix + videoTypeArray[videoType] + videoId + '_ta3d.mp4' + postfix + '&' + urllib.urlencode({"HttpReferer":"http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639"})
                showUrl_hq = prefix + videoTypeArray[videoType] + videoId + '_ta2d.mp4' + postfix + '&' + urllib.urlencode({"HttpReferer":"http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639"})
                showUrl_hd = prefix + videoTypeArray[videoType] + videoId + '_ta1d.mp4' + postfix + '&' + urllib.urlencode({"HttpReferer":"http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639"})
                showUrl_lq = showUrl_lq.replace('.f4m', '.m3u8')
                showUrl_hq = showUrl_hq.replace('.f4m', '.m3u8')
                #showUrl_hd = showUrl_hd.replace('.f4m', '.m3u8')
                #addLink('574p Video', showUrl_hd, None)
                addLink('404p Video', showUrl_hq, None)
                addLink('288p Video', showUrl_lq, None)
                #url="media_b125000_w1074750885_qSHR0cFJlZmVyZXI9aHR0cCUzQSUyRiUyRmVtYmVkLmxpdmVib3guY3olMkZ0YTMlMkZwbGF5ZXIuc3dmJTNGbm9jYWNoZSUzRDEzNDM2NzE0NTg2MzkmYXV0aD1fYW55XyU3QzEzNDM4MTczNTQlN0NhMGJjMzE2Y2FjMWI3NzA3ZGNhODMxNmI5MWMxOWVhZTY1NmQyYTNk.abst/">
            ##
                # showUrl = new OnlineVideos.MPUrlSourceFilter.HttpUrl(String.Format("{0}{1}{2}_ta3d.mp4{3}", prefix, TA3Util.videoType[videoType], videoId, postfix)) { Referer = "http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639" }.ToString();

    else:
        headers = {'Referer':videoUrl}
        playerOnlineWebData = request(playerOnlineUrl, headers)
        videoId = ''
        prefix = ''
        postfix = ''
        match_lq = re.search(videoLowIdLiveRegex, playerOnlineWebData)
        match_hq = re.search(videoMediumIdLiveRegex, playerOnlineWebData)
        match_hd = re.search(videoHighIdLiveRegex, playerOnlineWebData)
        videoId_lq = None
        videoId_hq = None
        videoId_hd = None
        if match_lq is not None:
            videoId_lq = match_lq.group("videoLowId")
        if match_hq is not None:
            videoId_hq = match_hq.group("videoMediumId")
        if match_hd is not None:
            videoId_hd = match_hd.group("videoHighId")

        match = re.search(videoUrlPrefixRegex, playerOnlineWebData)
        if match is not None:
            prefix = match.group("prefix")
        match = re.search(videoUrlPostfixRegex, playerOnlineWebData)
        if match is not None:
            postfix = match.group("postfix")
        if videoId_hd:
            showUrl = prefix + videoId_hd + postfix + '&' + urllib.urlencode({"HttpReferer":"http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639"})
            showUrl = showUrl.replace('.f4m', '.m3u8')
            addLink('574p Video', urllib.unquote(showUrl), None)
        if videoId_hq:
            showUrl = prefix + videoId_hq + postfix + '&' + urllib.urlencode({"HttpReferer":"http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639"})
            showUrl = showUrl.replace('.f4m', '.m3u8')
            addLink('404p Video', urllib.unquote(showUrl), None)
        if videoId_lq:
            showUrl = prefix + videoId_lq + postfix + '&' + urllib.urlencode({"HttpReferer":"http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639"})
            showUrl = showUrl.replace('.f4m', '.m3u8')
            addLink('288p Video', urllib.unquote(showUrl), None)
        #showUrl = String.Format("{0}{1}{2}", prefix, videoId, postfix)) { Referer = "http://embed.livebox.cz/ta3/player.swf?nocache=1343671458639" }.ToString();
                
    
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
        DiscoverDynamicCategories()
       
elif mode == 1:
        print ""
        GetPageVideos(url)

elif mode == 2:
        print "" + url
        GetVideoLink(url)
