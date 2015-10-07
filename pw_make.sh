#!/bin/bash

INI=.pw_pgcontrol.ini

test -f $INI && . $INI || { 
		showError "No evironment INI file found. Have you specified PostgreSQL configs in $INI?"
		exit 1
	}
	
rm $LOGFILE
make && make install && pw_pgcontrol.sh --restart 

if test $? -ne 0; then
	exit $?
fi

# Wait until log file exists, i.e. server started...
while [ ! -f $LOGFILE ]
do
	echo -n -e "\rWaiting for log file..."
done

clear
tail -f $LOGFILE

exit 0
