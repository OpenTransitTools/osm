#!/usr/bin/env bash
set -euo pipefail

wget -O osmosis-latest.tgz https://github.com/openstreetmap/osmosis/releases/download/0.48.3/osmosis-0.48.3.tgz
tar xvfz osmosis-latest.tgz
chmod a+x bin/osmosis
chmod a+x bin/osmosis.bat
