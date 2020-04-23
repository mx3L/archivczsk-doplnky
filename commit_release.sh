#!/bin/bash
set -e
set -x

./release.sh
git rev-parse HEAD > commit
git add commit
git commit -m 'release'
