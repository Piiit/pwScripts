#!/bin/bash
set -euo pipefail
SCRIPTNAME=${0##*/}

wget https://dl.pstmn.io/download/latest/linux64 -O /tmp/postman-linux64.tar.gz

sudo mkdir -p /opt/postman
cd /opt/postman

tar xfvz /tmp/postman-linux64.tar.gz --strip 1

echo "DONE."

exit 0
