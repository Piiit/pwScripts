#!/bin/bash

function showHelp {
	echo "USAGE: $0 [OPTIONS] <start> <end> <file>"
	echo "Extracts the last occurrence of a paragraph in a <file> which starts"
	echo "   with <start>, and ends with <end>. Where <start> and <end> are"
	echo "   strings, and <file> is a file name."
	echo
	echo "OPTIONS:"
	echo "  help, -h, --help      Show this help message"
}

function showError {
    echo "$0: $1"
	echo "$0 --help gives more information."
}

function checkArguments {
	if test $1 -ne $2; then
        showError "$3"
		exit 1
	fi
}

case $1 in
	help|-h|--help)
		showHelp	
		exit 0
	;;
esac

checkArguments $# 3 "$1: Wrong parameter count." 

cat "$3" | sed -n "/$1/,/$2/p" | grep -v "$1" | grep -v "$2" | awk -v RS="" ' { str=$0 } END { print str } '

exit 0
