#!/bin/bash

D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
cd ${D}/custom
${D}/custom/release.sh
cd ${D}/dmd-czech
${D}/dmd-czech/release.sh
cd ${D}/xbmc-doplnky
${D}/xbmc-doplnky/release.sh
