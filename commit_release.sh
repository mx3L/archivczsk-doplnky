#!/bin/bash
set -e
set -x

./release.sh
git commit -m 'release'
git rev-parse HEAD > commit
git add commit
git commit -m 'set commit to current release'
