#!/bin/bash

function showHelp {
	echo "Command: $0 [OPTIONS]... [FILES]..."
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

OPTIND=1
VERBOSE=0
IGNORE=0

function outVerbose {
	test $VERBOSE -eq 1 && echo "$1" >&2
}

while getopts "hvi" key
do
	case $key in
		h)
			showHelp	
			exit 0
		;;
		v)
			VERBOSE=1
		;;
		i)
			IGNORE=1
			IGNORESTRING="$2"
			shift $((OPTIND-1))
		;;
		*)
			echo "'$0 -h' gives you more information."
			exit 1
		;;
	esac
done

shift $((OPTIND-1))
[ "$1" = "--" ] && shift

ERRCOUNT=0
SKIPCOUNT=0
TESTCOUNT=0

for ARG in "$@"
do
	if [[ ! "$ARG" =~ "_expected.txt" ]]; then 
		if [ -f "${ARG%.*}_expected.txt" ]; then 
            let TESTCOUNT=TESTCOUNT+1
			outVerbose "============================================================================="
			outVerbose "TESTING: $ARG"
			
			if test $IGNORE -eq 1; then
				outVerbose "Ignoring '$IGNORESTRING' while comparing..."
				diff -Bby --suppress-common-lines -I $IGNORESTRING ${ARG%.*}_expected.txt "$ARG" >&2
                PASSED=$?
			else
				diff -Bby --suppress-common-lines ${ARG%.*}_expected.txt "$ARG" >&2
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
