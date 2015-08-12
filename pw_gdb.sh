#!/bin/sh

gdb postgres `ps aux|grep postgres|grep idle|awk '{print $2}'`

exit 0
