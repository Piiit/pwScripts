#!/bin/sh

LOG=/tmp/postgresql-temporal3-serverlog

rm $LOG
make && make install && pw_pgcontrol.sh restart 

# Wait until log file exists, i.e. server started...
while [ ! -f $LOG ]
do
	echo -n .
done

clear
tail -f $LOG
