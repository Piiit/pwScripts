#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

SCRIPTNAME=${0##*/}


__DOC__="
================================================================================
                         $SCRIPTNAME  MANUAL
================================================================================

This script controls PostgreSQL servers, clients, and build processes.

Some information have been taken from:
http://petereisentraut.blogspot.it/2010/03/running-sql-scripts-with-psql.html

Example setup for this script:

export PW_PGC_PORT=5112
export PW_PGC_LOG=/tmp/postgresql-temporal-serverlog
export PW_PGC_DATA=\$PWD/projects/tpg-source/data
export PW_PGC_BUILD=\$PWD/projects/tpg-source/server
"

# All output should be in English
export LC_ALL=C

function showConfig {
	loadINI
	echo "  Port  : $PORT"
	echo "  Log   : $LOG"
	echo "  Data  : $DATA"
	echo "  Build : $BUILD"
}

function showHelp {
	echo "USAGE:"
	echo " $SCRIPTNAME [OPTIONS]"
	echo " This is a script to control a PostgreSQL instance."
	echo
	echo "OPTIONS:"
	echo " -h, --help            |Show this help message"
	echo "     --manual          |Show the manual of this command"
	echo " -i, --info            |Show configuration for current directory"
	echo " -s, --start           |Start the PostgreSQL Server"
	echo " -S, --stop            |Stop the PostgreSQL Server"
	echo " -r, --restart         |Restart the PostgreSQL Server"
	echo "     --status          |Show the status of the PostgreSQL Server"
	echo " -c, --createdb DB     |Create a database with name DB"
	echo "     --dropdb DB		 |Drop a database with name DB"
	echo " -I, --initdb          |Create a new PostgreSQL database cluster in \$DATA"
	echo "                       |Change \$DATA in the ini-file"
	echo " -t, --test DB FILE    |Test FILE with database DB (batch mode; single transaction; stop on error)"
	echo " -T, --testall DB FILE |Test FILE with database DB (batch mode; multiple transactions; do not stop on error)"
	echo "     --regressiontest DB FILE"
	echo "                       |Run FILE with database DB to create a regression test file for PG test/regress/expected"
	echo " -l, --load DB FILE    |Load FILE with SQL data into the database DB"
	echo " -p, --psql DB         |Start psql for database DB  with current configuration"
	echo "     --execute DB COMMAND"
	echo "                       |Execute COMMAND on database DB"
	echo "     --csvout DB FILE  |Same as 'load', but writes results as CSV to stdout"
	echo "     --csvload DB TABLE FILE"
	echo "                       |Load a csv-file and store contents in table TABLE"
	echo "     --comparetables DB QUERY1 QUERY2"
	echo "                       |Run both queries and compare results"
	echo "     --patchcreate PATCHFILE"
	echo "                       |Create a patch against PostgreSQL origin/master without src/test"
	echo "     --patchcreatetestonly PATCHFILE"
	echo "                       |Create a patch against PostgreSQL origin/master, but src/test only!"
	echo "     --patch PATCHFILE |Apply a patch to a Postgres source code directory"
	echo "                       |See man patch for further details."
	echo " -m, --make            |Compiles the source of PostgreSQL, restarts the server, and"
	echo "                       |displays server's log file"
	echo " -x, --restartclean    |Remove logfile, restart server and output log constantly"
	echo "     --configure       |Run configure with default parameters"
	echo "     --testinitdb      |Tests to initialize a temporary database"
	echo
	echo " Note: Change environmental variables if you want to have a different"
	echo " configuration. See \"$SCRIPTNAME --manual\" for details."
	echo
	echo "CONFIG:"
	showConfig


	exit 0
}

function showError {
	echo "$SCRIPTNAME: ERROR: $1" >&2
	exit 1
}

# Fetch environment information about the PostgreSQL installation
function loadINI {
	PORT=$(printf "%s\n" "${PW_PGC_PORT:?You must set PW_PGC_PORT}")
	DATA=$(printf "%s\n" "${PW_PGC_DATA:?You must set PW_PGC_DATA}")
	LOG=$(printf "%s\n" "${PW_PGC_LOG:?You must set PW_PGC_LOG}")
	BUILD=$(printf "%s\n" "${PW_PGC_BUILD:?You must set PW_PGC_BUILD}")
	return 0
}

function checkArguments {
	if test $1 -lt $2; then
        showError "$3"
	fi
}


# callPgCtl
# 	Call the PostgreSQL control program pg_ctl, either with or without log file
#   output.
#
#   $1 - pg_ctl command (ex., status, start, stop)
#   $2 - data dir of the PostgreSQL cluster
#   $3 - server port
#   $4 - log file
function callPgCtl {
	L=""
	test -n $4 && L="-l $4"
	$BUILD/bin/pg_ctl $1 -D $2 $L -o "-p $3"
	return $?
}


# callPsql
# 	Call the PostgreSQL client program psql for the server on localhost with a
#   given port, data cluster directory, and file that should be executed.
#
#   $1 - server port
#   $2 - data dir of the PostgreSQL cluster
#   $3 - SQL file that must be executed
#   $4 - Additional parameters
function callPsql {
	$BUILD/bin/psql -p $1 -h localhost -d $2 -f $3 $4
	return $?
}

##
## MAIN
##

# Handling of script arguments...
# Each short option character in shortopts may be followed by one colon to
# indicate it has a required argument, and by two colons to indicate it has
# an optional argument.
ARGS=$(
	getopt -o "hisrt:T:SIc:l:p:mx" \
	-l "help,info,start,stop,restart,status,initdb,createdb:,dropdb:,test:,
	testall:,load:,psql:,csvout:,csvload:,comparetables:,patchcreate:,patch:,
	make,restartclean,regressiontest:,configure,patchcreatetestonly:,execute:,
	testinitdb,manual" \
	-n $SCRIPTNAME -- "$@"
)
#2>/tmp/pw_pgcontrol.sh_getopt$$
if [ $? != 0 ] ; then
	showError "Wrong argument given: $@"
fi

eval set -- "$ARGS"

test "$1" == "-h" || test "$1" == "--help" && {
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
		-i | --info)
		    showConfig
		    exit 0
		;;
		-s | --start)
			callPgCtl start $DATA $PORT $LOG
			exit $?
		;;
		-r | --restart)
			callPgCtl restart $DATA $PORT $LOG
			exit $?
		;;
		--status)
			callPgCtl status $DATA $PORT $LOG
			exit $?
		;;
		-S | --stop)
			callPgCtl stop $DATA $PORT $LOG
			exit $?
		;;
		-c | --createdb)
			checkArguments $# 2 "$1: no database name specified!"
			$BUILD/bin/createdb -p $PORT -h localhost $2
		    exit $?
		;;
		--dropdb)
			checkArguments $# 2 "$1: no database name specified!"
			$BUILD/bin/dropdb -p $PORT -h localhost $2
		    exit $?
		;;
		-l | --load)
			checkArguments $# 3 "$1: no database name and/or data-file specified!"
			callPsql $PORT $2 $4
			exit $?
		;;
		-t | --test)
			checkArguments $# 4 "--test DB FILE: no database name or test-file specified!"
			PGOPTIONS='--client-min-messages=warning' $BUILD/bin/psql -p $PORT \
				-h localhost -X -a -q -1 -v ON_ERROR_STOP=1 --pset pager=off \
				-d $2 -f $4
			exit $?
		;;
		--regressiontest)
			# The -f parameter produces error messages with filename and line of
			# code numbers, where the error occurred. Therefore, we use
			# "< filename" instead of "-f filename"
			checkArguments $# 4 "--regressiontest DB FILE: no database name or test-file specified!"
			PGOPTIONS='--client-min-messages=warning' $BUILD/bin/psql -p $PORT \
				-h localhost -X -a -q -v ON_ERROR_STOP=0 --pset pager=off \
				-d $2 < $4 2>&1
			exit $?
		;;
		-T | --testall)
			checkArguments $# 4 "--testall DB FILE: no database name or test-file specified!"
			PGOPTIONS='--client-min-messages=warning' $BUILD/bin/psql -p $PORT \
				-h localhost -X -a -q -v ON_ERROR_STOP=0 --pset pager=off \
				-d $2 -f $4 2>&1
			exit $?
		;;
		--debug)
		    $BUILD/bin/psql -a -e -p $PORT -h localhost -d $2 -f $3
		    exit $?
		;;
		-p | --psql)
			# TODO Build a better checkArguments here... pass additional parameters if any.
		    checkArguments $# 2 "$1: database name missing or too many arguments given."
		    $BUILD/bin/psql -p $PORT -h localhost -d $2
		    exit $?
		;;
		--csvout)
			query=$(sed 's/;//' $3 | grep -v ^SET )
			$BUILD/bin/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV HEADER DELIMITER ';'"
			exit $?
		;;
		--csvout2)
			query=$(sed 's/;//' $3 | grep -v ^SET )
			$BUILD/bin/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV DELIMITER ','"
			exit $?
		;;
		--csvload)
			# To fetch the absolute path with filename
			file=$(readlink -m $4)
			$BUILD/bin/psql -p $PORT -h localhost -d $2 -c "COPY $3 FROM '$file' DELIMITER ';' CSV HEADER"
			exit $?
		;;
		--comparetables)
			$BUILD/bin/psql -p $PORT -h localhost -d $2 -c "WITH test AS ($4), test2 AS ($5) SELECT * FROM ((TABLE test EXCEPT ALL TABLE test2) UNION (TABLE test2 EXCEPT ALL TABLE test)) d;"
			exit $?
		;;
		--execute)
			$BUILD/bin/psql -p $PORT -h localhost -d $2 -c "$4"
			exit $?
		;;
		-I | --initdb)
			$BUILD/bin/initdb -D $DATA
			exit $?
		;;
		--testinitdb)
			TMPDIR="/tmp/$SCRIPTNAME-initdb-test.$$"
	 		$BUILD/bin/initdb -D $TMPDIR
	 		RES=$?
	 		rm -rf $TMPDIR
	 		exit $RES
		;;
		--patchcreate)
			checkArguments $# 2 "$1: No <patch-file> given."

			git diff --no-prefix origin/master -- src/ \
				| filterdiff -p 0 -x "src/test/*" \
				| sed '/diff --git src\/test/,/^index/{d}' - > $2

			exit $?
		;;
		--patchcreatetestonly)
			checkArguments $# 2 "$1: No <patch-file> given."

			git diff --no-prefix origin/master -- src/test/ > $2

			exit $?
		;;
		--patch)
			checkArguments $# 2 "$1: Provide a patch-file to apply a patch to a postgres directory."
			patch -p0 < $3
			exit $?
		;;
		-x | --restartclean | -m | --make )

			# Remove logfile, restart server and show log constantly...
			test -z $LOG && {
				showError "LOG not set in INI file $INI."
			}

			rm -f $LOG || {
				showError "Can not remove LOG file $LOG."
			}

			test "$1" = "-m" || test "$1" == "--make" && {
				make && make install || {
					showError "make or make install failed with error-code $?"
				}
			}

			# Server restart
			callPgCtl restart $DATA $PORT $LOG || {
				exit $?
			}

			# Wait until log file exists, i.e. server has been started...
			while [ ! -f $LOG ]
			do
				echo -n -e "\rWaiting for PostgreSQL server to start up..."
			done

			clear
			tail -f $LOG

			exit 0
		;;
		--configure )

			# Disable all compile optimization techniques. Step-by-step
			# debugging works better without.
			export CFLAGS="-O0"

		    ./configure \
				--prefix="$(readlink -f $BUILD)" \
				--enable-debug \
				--enable-depend \
				--enable-cassert

			exit $?
		;;
		-- )
			shift
			break
		;;
		*)
		    showError "OPTION '$1' does not exist."
		;;
	esac
done



# We should not reach this line!
showError "No parameter specified"
