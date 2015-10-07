#!/bin/bash
SCRIPTNAME=${0##*/}
INI=.pw_pgcontrol.ini

function showError {
    echo "$SCRIPTNAME: ERROR: $1"
	echo "$SCRIPTNAME -h gives more information."
}

# Fetch environment information about the PostgreSQL installation
function checkINI {
	test -f $INI && . $INI || { 
		showError "No evironment INI file found. Have you specified PostgreSQL configs in $INI?"
		exit 1
	}
}

function showConfig {
	checkINI
	echo "  Port: $PORT"
	echo "  Log : $LOGFILE"
	echo "  Data: $DATADIR"
    echo "  Bin : $BINDIR"
}

function showHelp {
	echo "USAGE:" 
	echo " $SCRIPTNAME [OPTIONS]"
	echo " This is a script to control a PostgreSQL instance."
	echo
	echo "OPTIONS:"
	echo " -h, --help            |Show this help message"
    echo " -i, --info            |Show configuration for current directory"
	echo " -s, --start           |Start the PostgreSQL Server"
	echo " -t, --stop            |Stop the PostgreSQL Server"
	echo " -r, --restart         |Restart the PostgreSQL Server"
	echo "     --status          |Show the status of the PostgreSQL Server"
	echo " -c, --createdb DB     |Create a database with name DB"
	echo "     --initdb          |Create a new PostgreSQL database cluster in \$DATADIR"
	echo "                       |Change \$DATADIR in the ini-file"
	echo "     --test DB FILE    |Test FILE with database DB (batch mode; single transaction; stop on error)"
	echo "     --testall DB FILE |Test FILE with database DB (batch mode; multiple transactions; do not stop on error)"
	echo "     --load DB FILE    |Load FILE with SQL data into the database DB"
    echo " -p, --psql DB         |Start psql for database DB  with current configuration"
    echo "     --csvout DB FILE  |Same as 'load', but writes results as CSV to stdout"
    echo "     --csvload DB TABLE FILE"
    echo "                       |Load a csv-file and store contents in table TABLE"
    echo "     --comparetables DB TABLE FILE"
    echo "                       |Execute the query in FILE, and compare results with TABLE"
    echo "     --patchcreate ORIGPATH NEWPATH PATCHFILE"
    echo "                       |Create a patch by comparing two Postgres directories with diff"
    echo "                       |See man diff for further details."
    echo "     --patchapply PLEVEL PATCHFILE"
    echo "                       |Apply a patch to a Postgres source code directory"
    echo "                       |See man patch for further details."
	echo
	echo "CONFIG:"
    showConfig
	echo "  > Note: Change configurations in '$INI' inside your PostgreSQL directory."

    exit 0
}

function checkArguments {
	if test $1 -lt $2; then
        showError "$3"
		exit 1
	fi
}

##
## MAIN
## 


# Binary dir default setting, if not set inside the INI-file...
test -z $BINDIR && BINDIR="./server/bin"

# Each short option character in shortopts may be followed by one colon to indicate it has a required 
# argument, and by two colons to indicate it has an optional argument.
TEMP=$(getopt -o hisrtc:p: -l help,info,start,stop,restart,status,initdb,createdb:,test:,testall:,load:,psql:,csvout:,csvload:,comparetables:,patchcreate:,patchapply: -n $SCRIPTNAME -- "$@")

if [ $? != 0 ] ; then echo "$SCRIPTNAME: Parameter parsing failed (getopt). Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"

CMD=
while true; do
	case "$1" in
		-h | --help)
			showHelp	
		;;
		-i | --info)
		    showConfig       
		    exit 0 
		;;
		-s | --start)
			CMD=start
			break
		;;
		-r | --restart)
			CMD=restart
			break
		;; 
		--status)
			CMD=status
			break
		;;
		-t | --stop)
			CMD=stop
			break
		;;
		createdb)
			checkArguments $# 2 "$1: no database name specified!"
			$BINDIR/createdb -p $PORT -h localhost $2
		    shift 2
		;;
		load)
			checkArguments $# 3 "$1: no database name and/or data-file specified!"
			$BINDIR/psql -p $PORT -h localhost -d $2 -f $3 		
			shift 2
		;;
		test)
			# Resource: http://petereisentraut.blogspot.it/2010/03/running-sql-scripts-with-psql.html
		
			checkArguments $# 3 "$1: no database name and/or test-file specified!"
			# echo "Test '$3' starts now..." >&2
			# echo "NB: We stop on first error and use a single transaction mode" >&2
			# echo >&2
			PGOPTIONS='--client-min-messages=warning' $BINDIR/psql -p $PORT -h localhost -X -a -q -1 -v ON_ERROR_STOP=1 --pset pager=off -d $2 -f $3 	
			exit $?
		;;
		testall)
			checkArguments $# 3 "$1: no database name and/or test-file specified!"
			PGOPTIONS='--client-min-messages=warning' $BINDIR/psql -p $PORT -h localhost -X -a -q -v ON_ERROR_STOP=0 --pset pager=off -d $2 -f $3 2>&1		
			exit $?
		;;
		debug)
		    $BINDIR/psql -a -e -p $PORT -h localhost -d $2 -f $3 
		    exit $?		
		;;
		psql)
			# TODO Build a better checkArguments here... pass additional parameters if any.
		    checkArguments $# 2 "$1: database name missing or too many arguments given." 
		    $BINDIR/psql -p $PORT -h localhost -d $2
		    exit $?
		;;
		csvout)
			query=$(sed 's/;//' $3 | grep -v ^SET ) 
			$BINDIR/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV HEADER DELIMITER ';'"
			exit $?
		;;
		csvout2)
			query=$(sed 's/;//' $3 | grep -v ^SET ) 
			$BINDIR/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV DELIMITER ','"
			exit $?
		;;
		csvload)
			# To fetch the absolute path with filename
			file=$(readlink -m $4)
			$BINDIR/psql -p $PORT -h localhost -d $2 -c "COPY $3 FROM '$file' DELIMITER ';' CSV HEADER"
			exit $?
		;;
		comparetables)
			# http://stackoverflow.com/questions/4602083/sql-compare-data-from-two-tables
			query=$(sed 's/;//' $4 | grep -v ^SET ) 
			$BINDIR/psql -p $PORT -h localhost -d $2 -c "SELECT * FROM $3 UNION SELECT * FROM ($query) XXXXX EXCEPT ALL SELECT * FROM $3 INTERSECT SELECT * FROM ($query) YYYYY"
			exit $?
		;;
		initdb)
			$BINDIR/initdb -D $DATADIR
			exit $?
		;;
		testinitdb)
			TMPDIR="/tmp/$SCRIPTNAME-initdb-test.$$"
	 		$BINDIR/initdb -D $TMPDIR
	 		RES=$?
	 		rm -rf $TMPDIR
	 		exit $RES
		;;
		patchcreate)
			checkArguments $# 4 "$1: diff requires <origpath> <newpath>, and <patch-file> to create a patch with name <patch-file>."
			# -x excludes some file types that are not required for patches.
			#    add more here, if they show up in the future.
			diff -x '*.o' \
			     -x '*.global' \
			     -x '.*' \
			     -x '*.log' \
			     -x '*.stat' \
			     -x '*.status' \
			     -x '*.patch' -rupN $2 $3 > $4
			exit $?
		;;
		patchapply)
			checkArguments $# 3 "$1: Provide a p-level and a patch-file to apply a patch to a postgres directory."
			patch -p$2 < $3
			exit $?
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

if test $CMD; then
	checkArguments $# 1 "$1: pg_ctl: additional parameters given, but ignored" 
	if test -z $LOGFILE; then
		$BINDIR/pg_ctl $CMD -D $DATADIR -o "-p $PORT"
		exit $?
	fi
	
	$BINDIR/pg_ctl $CMD -D $DATADIR -l $LOGFILE -o "-p $PORT"
	exit $?
fi

# We should not reach this line!
showError "No parameter specified"
echo
showHelp

exit 1
