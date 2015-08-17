#!/bin/bash

SCRIPTNAME=${0##*/}

function showHelp {
	echo "Command: $SCRIPTNAME [OPTIONS]... [FILES]..."
	echo "Runs test-cases of given [FILES], compares the output of a method with an expected-output file."
	echo "Returns SUCCEEDED for outputs that are equal to the expected file content."
	echo "Needed: A input file (<something>.txt) and an expected output file (<something>_expected.txt),"
	echo "        where <something> must be the same string."
	echo
	echo "OPTIONS:"
	echo "  -h, --help          	Show this help message"
	echo "  -v, --verbose       	Prints additional information, if a test fails"
	echo "  -i, --ignore <pattern>	Ignore lines with a certain <pattern>"
}

# NOTE: This requires GNU getopt.  On Mac OS X and FreeBSD, you have to install this
# separately; see below.
TEMP=$(getopt -o hvic: --long help,verbose,ignore,command:,debugfile: -n $SCRIPTNAME -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"

VERBOSE=false
IGNORE=false
DEBUGFILE=
CMD=

while true; do
  case "$1" in
    -h | --help ) 
    	showHelp
    	exit 0 
    ;;
    -v | --verbose ) 
    	VERBOSE=true
    	shift 
    ;;
    -i | --ignore ) 
    	IGNORE=true
		IGNORESTRING="$2" 
		shift 2 
	;;
	-c | --command )
		CMD="$2"
		shift 2
	;;
    --debugfile ) 
    	DEBUGFILE="$2"
    	shift 2 
    ;;
    -- ) 
    	shift
    	break 
    ;;
    * ) 
    	echo "'$SCRIPTNAME -h' gives you more information."
		exit 1
	;;
  esac
done

function outVerbose {
	$VERBOSE && echo "$1" >&2
}

ERRCOUNT=0
SKIPCOUNT=0
TESTCOUNT=0

function diffCmd {

	DIFFCMD="diff -Bbc --suppress-common-lines "
	if $IGNORE; then
		DIFFCMD=$DIFFCMD"-I $IGNORESTRING "
	fi
	
	if test -n "$CMD"; then
		$CMD $2 | $DIFFCMD $1 -
		return $?
	fi
	
	$DIFFCMD $1 $2
	return $?
}

for ARG in "$@"
do
	if [[ ! "$ARG" =~ "_expected.txt" ]]; then 
		if [ -f "${ARG%.*}_expected.txt" ]; then 
            let TESTCOUNT=TESTCOUNT+1
			outVerbose "============================================================================="
			outVerbose "TESTING: $ARG"
			
			if $IGNORE; then
				outVerbose "Ignoring '$IGNORESTRING' while comparing..."
				diff -Bby --suppress-common-lines -I $IGNORESTRING ${ARG%.*}_expected.txt "$ARG" >&2
                PASSED=$?
			else
				diffCmd ${ARG%.*}_expected.txt "$ARG"  >&2
                PASSED=$?
			fi
			
			if [ $PASSED -eq 0 ]; then
				echo "TEST SUCCEEDED: $ARG"
			else
				echo "TEST FAILED   : $ARG"
				let ERRCOUNT=ERRCOUNT+1
			fi
			outVerbose "============================================================================="
		else
			let SKIPCOUNT=SKIPCOUNT+1
			outVerbose "TEST SKIPPED: '$ARG' (no EXPECTED RESULT file)"
		fi
	fi
done

if test $TESTCOUNT -eq 0; then
  echo "Error: No test files given."
  showHelp
  exit 0
fi

echo ">>> DONE: $TESTCOUNT tests, $ERRCOUNT failures, $SKIPCOUNT skipped."
test $ERRCOUNT -eq 0 && echo ">>> RESULT: ALL TESTS PASSED!" || echo ">>> RESULT: ERRORS REPORTED!"

exit 0
