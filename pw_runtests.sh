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
	echo "  -h, --help              Show this help message"
	echo "  -v, --verbose           Prints additional information, if a test fails"
	echo "  -i, --ignore <pattern>  Ignore lines with a certain <pattern>"
	echo "  -c, --command <command> Executes a command and compares its result with a given expected result file"
	echo "  -s, --silent            Prints only minimal info, i.e., pass or fail"
	echo "  -k, --keepinfo			Keep all results, and accumulate them (not implemented yet)"
}

# Each short option character in shortopts may be followed by one colon to indicate it has a required 
# argument, and by two colons to indicate it has an optional argument.
TEMP=$(getopt -o hvsi:c: --long help,verbose,silent,ignore:,command: -n $SCRIPTNAME -- "$@")

if [ $? != 0 ] ; then echo "$SCRIPTNAME: Parameter parsing failed (getopt). Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"

SILENT=false
VERBOSE=false
DEBUGFILE=
CMD=

while true; do
  case "$1" in
    -h | --help ) 
    	showHelp
    	exit 0 
    ;;
    -v | --verbose ) 
    	$SILENT && { echo "$SCRIPTNAME: Verbose and silent can not be given at the same time! Terminating..." >&2; exit 1; }
    	VERBOSE=true
    	shift 
    ;;
    -i | --ignore ) 
		IGNORESTRING="$2"
		shift 2
	;;
	-c | --command )
		CMD="$2"
		shift 2
	;;
	-s | --silent )
		$VERBOSE && { echo "$SCRIPTNAME: Verbose and silent can not be given at the same time! Terminating..." >&2; exit 1; }
		SILENT=true
		shift
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
TESTCOUNT=0

TMPFILE1="/tmp/$SCRIPTNAME-stdout.$$.tmp"
TMPFILE2="/tmp/$SCRIPTNAME-stderr.$$.tmp"

function diffCmd {

echo $IGNORESTRING

	DIFFCMD="diff -Bbc --suppress-common-lines "
	if test -n "$IGNORESTRING"; then
		outVerbose "Ignoring '$IGNORESTRING' while comparing..."
		DIFFCMD=$DIFFCMD" -I"$IGNORESTRING
	fi
	
	DIFFOUT=$($SILENT && echo /dev/null || echo /dev/stdout)
	
	if test -n "$CMD"; then
		$CMD $2 > $TMPFILE1 2> $TMPFILE2
		OUT=$?
		if test $OUT -ne 0; then
			echo "ERROR: UNABLE TO EXECUTE TESTS..."
			printf "\tCommand '$CMD' failed with error-code '$OUT' and stderr output:\n"
			cat $TMPFILE2
			exit 1
		fi
		
		cat $TMPFILE1 | $DIFFCMD $1 - > $DIFFOUT
		return $?
	fi
	
	$DIFFCMD $1 $2 > $DIFFOUT
	return $?
}

$SILENT || {
	echo "Starting tests..."
	echo
}

for ARG in "$@"
do
	if [[ ! "$ARG" =~ "_expected.txt" ]]; then 
		outVerbose "-----------------------------------------------------------------------------"
		if [ -f "${ARG%.*}_expected.txt" ]; then 
            let TESTCOUNT+=1
			
			outVerbose "TESTING: $ARG"
			
			diffCmd ${ARG%.*}_expected.txt "$ARG"  >&2
            PASSED=$?
			
			if [ $PASSED -eq 0 ]; then
				echo "TEST SUCCEEDED: $ARG"
			else
				echo "TEST FAILED   : $ARG"
				let ERRCOUNT+=1
			fi
		else
			outVerbose "TEST SKIPPED: '$ARG' (no EXPECTED RESULT file)"
		fi
	fi
done

if test $TESTCOUNT -eq 0; then
  echo "Error: No test files given."
  showHelp
  exit 0
fi

outVerbose "-----------------------------------------------------------------------------"

$SILENT || {
	echo
	echo "...done!"
	echo
	test $ERRCOUNT -eq 0 && printf "ALL TESTS PASSED!\n\n" || printf "ERRORS REPORTED!\n\n"
	echo "Details:"
	printf "  $TESTCOUNT tests executed\n"
	printf "  $ERRCOUNT tests failed\n"
	printf "  $[TESTCOUNT-ERRCOUNT] tests passed\n"
	echo
}

exit 0
