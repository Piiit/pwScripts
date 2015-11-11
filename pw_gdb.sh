#!/bin/sh

gdb postgres `ps aux|grep postgres|grep idle|grep pemoser|awk '{print $2}'|sort|head -n1`

exit 0
