#!/bin/bash

D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
cd ${D}/custom
${D}/custom/release.sh $1
cd ${D}/dmd-czech
${D}/dmd-czech/release.sh $1
cd ${D}/xbmc-doplnky
${D}/xbmc-doplnky/release.sh $1
