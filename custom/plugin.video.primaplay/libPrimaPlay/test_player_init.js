<?xml version="1.0" ?>
<response>
	<status>OK</status>
<update target="player-wrapper">
			<![CDATA[
<video id="viaplay-player" class="video-js vjs-viaplay-skin vjs-big-play-centered vjs-loading-permanent" controls preload="none" width="auto" height="auto">
			</video>
			]]>
		</update>
		<script>
			<![CDATA[

			var userDevice = {
				os: 'WINDOWS',
				userAgent: 'FIREFOX',
				browser: 'Firefox',
				browserVersion: '43',
				isMobileDevice: false
			};

			var heartBeatSettings = {
				'name': 'player-beat',
				'startBeatUrl': 'http://play.iprima.cz/prehravac/start-beat?csrfToken=cf04fdfd75768e1fcd29212a6833677b88bc30da-1450865206797-55fbc39b6ea5a369d8723b76',
				'heartBeatUrl': 'http://play.iprima.cz/prehravac/heart-beat?csrfToken=cf04fdfd75768e1fcd29212a6833677b88bc30da-1450865206797-55fbc39b6ea5a369d8723b76',
				'viewBeatUrl': 'http://play.iprima.cz/prehravac/view-beat?csrfToken=cf04fdfd75768e1fcd29212a6833677b88bc30da-1450865206797-55fbc39b6ea5a369d8723b76',
				'heartBeatInterval': 30,
				'viewBeatInterval': 60,
				'from': undefined
			};
			var gemiusSettings = {
				identifier: 'bPnrQk9BACJez5XyBLcjH8dv.hf80LuTAJ0GXGuxEyD.p7',
				adsidentifier: 'AqHg7WsrYw__kw9WF1hoosdvLXT8UKd4Db_fJNKTwr7.T7',
				hitcollector: 'scz.hit.gemius.pl',
				playerId: 'viaplay-player',
				materialIdentifier: 'Brno a okolí',
				treeId: [14885112],
				nazev: 'PERSONAL_COMPUTER',
				zdroj: 'play',
				cil: 'player',
				druh: 'Episode',
				series: 'Prostřeno!'
			};
			
			var playerOptions = {
				'thumbnails': {
					'url': 'http://prima-ott.service.cdn.cra.cz/vod/0000/5314/thumb.$Num$.jpg'
				},

				'language': 'cs',
				'autoplay': true,
				'plugins': {
					'tagsOnTimeline': {},
					'videojsAds': {},
					'settingsControl': {},
					'persistsettings': {}
					,
					'sharingScreen': {}
				},
				'tracks': {
					'HLS': [
{
								'lang': 'cze',
								'title': 'Čeština',
								'src': 'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4.smil/playlist.m3u8',
								'type': 'application/x-mpegURL','profiles': ['ao', 'sd1', 'sd2', 'sd3', 'sd4']
							},
					],
					'DASH': [
{
								'lang': 'cze',
								'title': 'Čeština',
								'src': 'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0000/5314/cze-ao-sd1-sd2-sd3-sd4.smil/manifest.mpd',
								'type': 'application/dash+xml','profiles': ['ao', 'sd1', 'sd2', 'sd3', 'sd4']
							},
					]
				},
				'subtitles': [
				],
				'mediafile': {
					'meta': {
						'title': 'Name of the video'
					}
				},
				children: {
					controlBar: {
						children: {
							captionsButton: false,
							"volumeControl": {
								"children": {
									"volumeBar": {
										"children": {
											"volumeHandle": false
										}
									}
								}
							}
						}
					}
				},
				'ads': {
					'active': true,
					'skip': true,
					'skipDelay': 2,
					'preferedFormate': 'video/mp4',
					'inventory': {
						'preroll': {
							'vast': [
								'http://go.cz.bbelements.com/please/showit/23145/1/1/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
															'http://go.cz.bbelements.com/please/showit/23145/1/11/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
															'http://go.cz.bbelements.com/please/showit/23145/1/12/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
							],
							'companion': {
								'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/1/7/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
							}
						},
						'midroll': [

								{
									'time': 600,
									'vast': [
										'http://go.cz.bbelements.com/please/showit/23145/1/5/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
																			'http://go.cz.bbelements.com/please/showit/23145/1/13/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
																			'http://go.cz.bbelements.com/please/showit/23145/1/14/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
									],
									'companion': {
										'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/2/24/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
									}
								}
,
								{
									'time': 1200,
									'vast': [
										'http://go.cz.bbelements.com/please/showit/23145/1/5/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
																			'http://go.cz.bbelements.com/please/showit/23145/1/13/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
																			'http://go.cz.bbelements.com/please/showit/23145/1/14/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
									],
									'companion': {
										'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/2/24/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
									}
								}
,
								{
									'time': 1800,
									'vast': [
										'http://go.cz.bbelements.com/please/showit/23145/1/5/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
																			'http://go.cz.bbelements.com/please/showit/23145/1/13/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
																			'http://go.cz.bbelements.com/please/showit/23145/1/14/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
									],
									'companion': {
										'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/2/24/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
									}
								}
						],
						'postroll': {
							'vast': [
							  'http://go.cz.bbelements.com/please/showit/23145/1/8/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
													  'http://go.cz.bbelements.com/please/showit/23145/1/15/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family',
													  'http://go.cz.bbelements.com/please/showit/23145/1/17/8/?typkodu=js&_xml=1&keywords=brno-a-okoli;prostreno-;porady;dokumentarni;reality;game-show;prostreno;family'
						]
						}
					}
				},
				'markers': [


							{
								time: 600,
								class: "vjs-marker-ad"
							}
,
							{
								time: 1200,
								class: "vjs-marker-ad"
							}
,
							{
								time: 1800,
								class: "vjs-marker-ad"
							}
				]
			};
			]]>
		</script>
<script>
		var statusCode = 'OK';
	</script>
</response>