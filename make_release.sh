#!/bin/bash

D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)

git reset HEAD ${D}/repo
git checkout -- ${D}/repo
git add ${D}/repo
git add ${D}/addons.xml
git add ${D}/addons.xml.md5

git rev-parse HEAD > commit
git add commit
git commit -m 'release'
