<?xml version="1.0" ?>
<response>
	<status>OK</status>
<update target="player-wrapper">
				<![CDATA[
<video id="viaplay-player" class="video-js vjs-viaplay-skin vjs-big-play-centered vjs-loading-permanent" controls preload="none" width="auto" height="auto">
				</video>
				<div id="fake-player" class="hidden vjs-viaplay-skin" data-product="p111226">
					<div id="fake-player-content">
<div class="bg"></div>
<div class="outer">
	<div class="inner">
		<div class="message">
			<div class="heading">
				<i class="icon-notice"></i>
				<p data-jnp="i.video.FlashRequired">Váš browser potřebuje pro přehrání videa Adobe Flash Player</p>
			</div>
			<div class="content">
</div>
		</div>
	</div>
</div>
</div>
				</div>
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
					'startBeatUrl': 'http://play.iprima.cz/prehravac/start-beat',
					'heartBeatUrl': 'http://play.iprima.cz/prehravac/heart-beat',
					'viewBeatUrl': 'http://play.iprima.cz/prehravac/view-beat',
					'heartBeatInterval': 30,
					'viewBeatInterval': 60,
					'from': undefined
				};
				var gemiusSettings = {
					identifier: 'bPnrQk9BACJez5XyBLcjH8dv.hf80LuTAJ0GXGuxEyD.p7',
					adsidentifier: 'AqHg7WsrYw__kw9WF1hoosdvLXT8UKd4Db_fJNKTwr7.T7',
					hitcollector: 'scz.hit.gemius.pl',
					playerId: 'viaplay-player',
					materialIdentifier: 'Cestování červí dírou s Morganem Freemanem II',
					treeId: [126950112],
					nazev: 'PERSONAL_COMPUTER',
					zdroj: 'play',
					cil: 'player',
					druh: 'Episode',
					series: 'Cestování červí dírou s Morganem Freemanem'
				};
			
				var playerOptions = {
					'thumbnails': {
						'url': 'http://prima-ott.service.cdn.cra.cz/vod/0001/4844/thumb.$Num$.jpg'
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
									src: 'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0001/4844/cze-ao-sd1-sd2-sd3-sd4.smil/playlist.m3u8',
									'type': 'application/x-mpegURL','profiles': ['ao', 'sd1', 'sd2', 'sd3', 'sd4']
								},
						],
						'DASH': [
{
									'lang': 'cze',
									'title': 'Čeština',
									'src': 'http://prima-vod-prep.service.cdn.cra.cz/vod_Prima/_definst_/0001/4844/cze-ao-sd1-sd2-sd3-sd4.smil/manifest.mpd',
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
									'http://go.cz.bbelements.com/please/showit/23145/1/1/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																	'http://go.cz.bbelements.com/please/showit/23145/1/11/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																	'http://go.cz.bbelements.com/please/showit/23145/1/12/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
								],
								'companion': {
									'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/1/7/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
								}
							},
							'midroll': [

									{
										'time': 600,
										'vast': [
											'http://go.cz.bbelements.com/please/showit/23145/1/5/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/13/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/14/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										],
										'companion': {
											'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/2/24/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										}
									}
,
									{
										'time': 1200,
										'vast': [
											'http://go.cz.bbelements.com/please/showit/23145/1/5/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/13/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/14/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										],
										'companion': {
											'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/2/24/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										}
									}
,
									{
										'time': 1800,
										'vast': [
											'http://go.cz.bbelements.com/please/showit/23145/1/5/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/13/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/14/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										],
										'companion': {
											'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/2/24/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										}
									}
,
									{
										'time': 2400,
										'vast': [
											'http://go.cz.bbelements.com/please/showit/23145/1/5/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/13/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
																					'http://go.cz.bbelements.com/please/showit/23145/1/14/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										],
										'companion': {
											'vast': 'http://go.cz.bbelements.com/please/showit/23145/1/2/24/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
										}
									}
							],
							'postroll': {
								'vast': [
								  'http://go.cz.bbelements.com/please/showit/23145/1/8/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
															  'http://go.cz.bbelements.com/please/showit/23145/1/15/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni',
															  'http://go.cz.bbelements.com/please/showit/23145/1/17/8/?typkodu=js&_xml=1&keywords=cestovani-cervi-dirou-s-morganem-freemanem-ii;cestovani-cervi-dirou-s-morganem-freemanem;porady;dokumentarni'
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
,
								{
									time: 2400,
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
