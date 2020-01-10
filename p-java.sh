#!/bin/bash

set -xeuo pipefail

SCRIPTNAME=${0##*/}


__DOC__="
================================================================================
                         $SCRIPTNAME  MANUAL
================================================================================

This script helps to get java related programming tasks done fast.
"

# All output should be in English
export LC_ALL=C

function showHelp {
    echo "
USAGE:
  $SCRIPTNAME [OPTIONS]
  This is a script that helps to get java related programming tasks done fast.

OPTIONS:
  -h, --help             Show this help message
      --manual           Show the manual of this command
  -m, --mvngenerate      Generate a new maven project
"

    exit 0
}

function showError {
    echo "$SCRIPTNAME $1" >&2
    exit 1
}

function checkArguments {
    if test $1 -lt $2; then
        showError "$3"
    fi
}


# callPgCtl
#   Call the PostgreSQL control program pg_ctl, either with or without log file
#   output.
#
#   $1 - pg_ctl command (ex., status, start, stop)
#   $2 - data dir of the PostgreSQL cluster
#   $3 - server port
#   $4 - log file
function mvnGenerate {
    mvn -B archetype:generate \
        -DarchetypeGroupId=org.apache.maven.archetypes \
        -DgroupId="$1" \
        -DartifactId="$2"
    return $?
}


################################################################################
## MAIN
################################################################################

# Handling of script arguments...
# Each short option character in shortopts may be followed by one colon to
# indicate it has a required argument, and by two colons to indicate it has
# an optional argument.
ARGS=$(
    getopt -o "hm" \
    -l "help,manual,mvngenerate" \
    -n $SCRIPTNAME -- "$@"
)

if [ $? != 0 ] ; then
    showError "Wrong argument given: $@"
fi

eval set -- "$ARGS"

test $# == 1 || test "$1" == "-h" || test "$1" == "--help" && {
    showHelp
    exit 0
}

test "$1" == "--manual" && {
    echo "$__DOC__"
    echo
    showHelp
    exit 0
}

CMD=
while true; do
    case "$1" in
        -m | --mvngenerate)
            checkArguments $# 3 "$1: ERROR: Specify a groupId and an artifactId. Ex.: com.example.mylibrary fancy-app"
            mvnGenerate $3 $4
            exit $?
        ;;
        -- )
            shift
            break
        ;;
    esac
done

# We should not reach this line!
showError "No parameter specified"

