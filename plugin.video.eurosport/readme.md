For fully working plugin you need to obtain the "st" cookie value from your browser.

Open Google Chrome browser:
- Log into www.eurosportplayer.com and start play any video
- Press F12 to access developer tools
- Select Application tab
- On the left hand side of the popup select Cookies in the Storage section.
- Locate the 'st' cookie Name under https://www.eurosportplayer.com and copy it's Value.

Open Enigma box (log into box by telnet):
- Stop Enigma2 (by running command: init 4)
- Open /etc/enigma2/settings file by any editor (vi)
- Insert copied value at new line started with config.plugins.archivCZSK.archives.plugin_video_eurosport.eurosporttoken=
- Save settings file and close editor
- Start Enigma2 (by running command: init 3)
