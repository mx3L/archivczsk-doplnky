# -*- coding: utf-8 -*-

import requests
import lookups
import auth
import json
import sys
from string import Template

from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine import client
addon = ArchivCZSK.get_xbmc_addon('plugin.video.iprima')

def getResourceUrl(resource, replacements):
	url = lookups.resources[resource]['path']
	if len(replacements) > 0:
		url = url.format(**replacements)
	return url

def getResourceMethod(resource):
	return lookups.resources[resource]['method']

def getResourceContentPath(resource):
	return lookups.resources[resource]['content_path']

def getResourcePostData(resource, options):
	template = Template(lookups.resources[resource]['post_data'])
	return template.substitute(**options)

def getJSONPath(data, keys):
	return getJSONPath(data[keys[0]], keys[1:]) if keys else data

def isPlayable(itemType):
	return lookups.item_types[itemType]['playable']

def performCredentialCheck():
	username = addon.getSetting('username')
	password = addon.getSetting('password')
	if not username or not password:
		client.showInfo('Pro přehrávání pořadů je potřeba účet na iPrima.cz\n\nPokud účet nemáte, zaregistrujte se na auth.iprima.cz/user/register a pak zde Menu -> Nastavení vyplňte přihlašovací údaje.')
		return False
	return True

def getAccessToken(refresh=False):
	access_token = addon.getSetting('accessToken')
	if not access_token or refresh:
#		print('Getting new access token')
		username = addon.getSetting('username')
		password = addon.getSetting('password')
		access_token = auth.login(username, password)
		addon.setSetting('accessToken', access_token)
	return access_token

def requestResource(resource, count=0, page=0, replace={}, postOptions={}, retrying=False):
	url = getResourceUrl(resource, replace)
	method = getResourceMethod(resource)
	options = {
		'count': str(count or lookups.shared['pagination']),
		'offset': str(page * lookups.shared['pagination'])
	}
	options.update(postOptions)
	token = getAccessToken(refresh=retrying)
	common_headers = {
		'Authorization': 'Bearer ' + token,
		'x-prima-access-token': token,
		'X-OTT-Access-Token': token
	}
	if method == 'POST':
		data = getResourcePostData(resource, options).encode('utf-8')
		contentPath = getResourceContentPath(resource)
		request = postUrl(url, data, common_headers)
	else:
		request = getUrl(url, common_headers)
	if request.ok:
		return getJSONPath(request.json(), contentPath) if method == 'POST' else request.json()
	elif request.status_code in {401, 403}:
		if retrying: 
			client.showError('Chyba autorizace')
			sys.exit(1)
		return requestResource(resource, count, page, replace, postOptions, retrying=True)
	client.showError('Server neodpovídá správně')
	sys.exit(1)

def getUrl(url, headers):
#	print('Requesting: ' + url)
	request = requests.get(
		url,
		timeout=20,
		headers=headers
	)
	return request

def postUrl(url, data, headers):
#	print('Requesting: %s; with data: %s' % (url, data))
	request = requests.post(
		url,
		data=data,
		timeout=20,
		headers=headers
	)
	return request
