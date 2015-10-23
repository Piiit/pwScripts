#!/bin/bash
SCRIPTNAME=${0##*/}
INI=.pw_pgcontrol.ini

function showError {
    echo "$SCRIPTNAME: ERROR: $1"
	echo
}

test -f $INI && . $INI || { 
	showError "No evironment INI file found. Have you specified PostgreSQL configs in $INI?"
	exit 1
}

echo $LOG

test -z $LOG && {
	showError "LOG not set in INI file $INI."
	exit 1
}

rm -f $LOG || {
	showError "Can not remove LOG file $LOG."
	exit 1
}

make && make install && pw_pgcontrol.sh --restart 

if test $? -ne 0; then
	exit $?
fi

# Wait until log file exists, i.e. server started...
while [ ! -f $LOG ]
do
	echo -n -e "\rWaiting for log file..."
done

clear
tail -f $LOG

exit 0
