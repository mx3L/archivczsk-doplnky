#!/bin/bash

D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
cd ${D}/custom
./release.sh
cd ${D}/dmd-czech
./release.sh
cd ${D}/xbmc-doplnky
./release.sh
cd ${D}
if [ "$1" != "force" ]; 
then
	git reset HEAD ${D}/custom/repo
	git reset HEAD ${D}/dmd-czech/repo
	git reset HEAD ${D}/xbmc-doplnky/repo
	git checkout -- ${D}/custom/repo
	git checkout -- ${D}/dmd-czech/repo
	git checkout -- ${D}/xbmc-doplnky/repo
	git add ${D}/custom/repo
	git add ${D}/custom/addons.xml
	git add ${D}/custom/addons.xml.md5
	git add ${D}/xbmc-doplnky/repo
	git add ${D}/xbmc-doplnky/addons.xml
	git add ${D}/xbmc-doplnky/addons.xml.md5
	git add ${D}/dmd-czech/repo
	git add ${D}/dmd-czech/addons.xml
	git add ${D}/dmd-czech/addons.xml.md5
fi
exit 0


