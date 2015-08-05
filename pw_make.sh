#!/bin/sh

rm /tmp/postgresql-temporal2-serverlog
make && make install && pw_pgcontrol.sh restart && sleep 3 && clear && tail -f /tmp/postgresql-temporal3-serverlog
