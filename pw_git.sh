#!/bin/bash
SCRIPTNAME=${0##*/}

# showHelp
#   Show usage text.
function showHelp {
	echo "USAGE:" 
	echo " $SCRIPTNAME [OPTIONS]"
	echo " This is a script to handle all kinds of git magic."
	echo
	echo "OPTIONS:"
	echo " -h, --help            Show this help message"
	echo " -0, --lastcommithash  Get last abbreviated commit hash from origin/master"
	echo " -1, --lastcommit      Get last commit information from origin/master"
	exit 0
}

# showError
#   Put error text to the standard output stream, and add usage text.
#
#   $1 - Error description.
function showError {
	echo "$SCRIPTNAME: ERROR: $1" >&2
	echo >&2
	showHelp >&2
}

# MAIN #########################################################################

# Handling of script arguments...
# Each short option character in shortopts may be followed by one colon to
# indicate it has a required argument, and by two colons to indicate it has
# an optional argument. For example, "hx:" if "h" has no argument, whereas "x"
# has one. Long options are separated by a comma.
ARGS=$(
	getopt -q -o "h10" \
	-l "help,lastcommit,lastcommithash" \
	-n $SCRIPTNAME -- "$@"
)

if [ $? != 0 ] ; then
	showError "Wrong argument given: $@"
	exit 1
fi

eval set -- "$ARGS"

CMD=
while true; do
	case "$1" in
		-h | --help)
			showHelp	
		;;
		-0 | --lastcommithash)
			git log --pretty=format:"%h" -1 origin/master
			exit 0
		;;
		-1 | --lastcommit)
			git log --pretty=format:"%h%d: %cn - %s" -1 origin/master
			exit 0
		;;
		-- ) 
			shift
			break 
		;;
		*)
		    showError "OPTION '$1' does not exist." 
		    exit 1
		;;
	esac
done



# We should never reach this line!
showError "No parameter specified."
exit 1
