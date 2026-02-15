#!/usr/bin/env bash
set -euo pipefail


OSMOSIS_VERSION="0.49.2"
OSMOSIS_URL="https://github.com/openstreetmap/osmosis/releases/download/${OSMOSIS_VERSION}/osmosis-${OSMOSIS_VERSION}.tar"

echo "Installing osmosis ${OSMOSIS_VERSION} from ${OSMOSIS_URL}"


# Download in /tmp to keep /osm clean.
cd /tmp
wget -O osmosis.tar "${OSMOSIS_URL}"

# Install osmosis into /osm (matches existing project paths).
# Some releases unpack as ./bin, others as ./osmosis-<ver>/bin.
rm -rf /tmp/osmosis-extract
mkdir -p /tmp/osmosis-extract
tar -xf osmosis.tar -C /tmp/osmosis-extract

if [ -x "/tmp/osmosis-extract/bin/osmosis" ]; then
  OSMOSIS_SRC="/tmp/osmosis-extract"
elif [ -x "/tmp/osmosis-extract/osmosis-${OSMOSIS_VERSION}/bin/osmosis" ]; then
  OSMOSIS_SRC="/tmp/osmosis-extract/osmosis-${OSMOSIS_VERSION}"
else
  echo "Could not locate osmosis bin after extracting ${OSMOSIS_URL}" >&2
  find /tmp/osmosis-extract -maxdepth 3 -type f | sed -n '1,80p' >&2
  exit 1
fi

cp -a "${OSMOSIS_SRC}/." /osm/
chmod a+x /osm/bin/osmosis /osm/bin/osmosis.bat

# Optional convenience path for direct invocation by name.
ln -sf /osm/bin/osmosis /usr/local/bin/osmosis

rm -f /tmp/osmosis.tar
rm -rf /tmp/osmosis-extract
