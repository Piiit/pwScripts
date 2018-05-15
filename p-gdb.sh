#!/bin/bash

SCRIPTNAME=${0##*/}

if [ $# < 1 ] ; then 
	echo "$SCRIPTNAME: Database name missing." >&2
	exit 1
fi

gdb postgres `ps aux|grep postgres|grep idle|grep 'pemoser '$1 | awk '{print $2}'|sort|head -n1`

exit 0
