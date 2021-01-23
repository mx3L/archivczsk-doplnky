# -*- coding: utf-8 -*-

import re
import requests
import helpers
import sys

try:
	from urlparse import urlparse, parse_qs
except ImportError:
	from urllib.parse import urlparse, parse_qs

from Plugins.Extensions.archivCZSK.engine import client

def login(email, password):
	s = requests.Session()

	# Get login page
	login_page = s.get('https://auth.iprima.cz/oauth2/login')
	login_page_content = login_page.text

	# Acquire CSRF token
	r_csrf = re.search('name="_csrf_token".*value="(.*)"', login_page_content)
	csrf_token = ''
	if r_csrf:
		csrf_token = r_csrf.group(1)
	else:
		client.showError('Nepodařilo se získat CSRF token')
		sys.exit(1)

	# Log in
	do_login = s.post('https://auth.iprima.cz/oauth2/login', {
		'_email': email,
		'_password': password,
		'_csrf_token': csrf_token
	})

	# Acquire authorization code from login result
	parsed_auth_url = urlparse(do_login.url)
	try:
		auth_code = parse_qs(parsed_auth_url.query)['code'][0]
	except KeyError:
		client.showError('Nepodařilo se získat autorizační kód, zkontrolujte přihlašovací údaje', 'ERROR')
		sys.exit(1)

	# Get access token
	get_token = s.post('https://auth.iprima.cz/oauth2/token', {
		'scope': 'openid+email+profile+phone+address+offline_access',
		'client_id': 'prima_sso',
		'grant_type': 'authorization_code',
		'code': auth_code,
		'redirect_uri': 'https://auth.iprima.cz/sso/auth_check.html'
	})
	if get_token.ok:
		responseJson = get_token.json()
		return responseJson['access_token']
	else:
		client.showError('Nepodařilo se získat access token', 'ERROR')
		sys.exit(1)
