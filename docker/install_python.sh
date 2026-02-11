#!/usr/bin/env bash
set -euo pipefail

PYTHON_VERSION="${1:-3.12.8}"
PYTHON_MM="${PYTHON_VERSION%.*}"

cd /tmp
curl -fsSLO "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"
tar -xf "Python-${PYTHON_VERSION}.tar.xz"
cd "Python-${PYTHON_VERSION}"
./configure --with-ensurepip=install
make -j"$(nproc)"
make altinstall

cd /
rm -rf "/tmp/Python-${PYTHON_VERSION}" "/tmp/Python-${PYTHON_VERSION}.tar.xz"

ln -sf "/usr/local/bin/python${PYTHON_MM}" /usr/local/bin/python3
ln -sf "/usr/local/bin/python${PYTHON_MM}" /usr/local/bin/python
ln -sf "/usr/local/bin/pip${PYTHON_MM}" /usr/local/bin/pip3
ln -sf "/usr/local/bin/pip${PYTHON_MM}" /usr/local/bin/pip
