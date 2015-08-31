#!/bin/bash
SCRIPTNAME=${0##*/}

# Fetch environment information about the PostgreSQL installation
. .pw_pgcontrol.ini

# Binary dir default setting, if not set inside the INI-file...
test -z $BINDIR && BINDIR="./server/bin"

function showError {
    echo "$SCRIPTNAME: $1"
	echo "$SCRIPTNAME --help gives more information."
}

function showConfig {
	echo "  Port: $PORT"
	echo "  Log : $LOGFILE"
	echo "  Data: $DATADIR"
    echo "  Bin : $BINDIR"
}

function showHelp {
	echo "USAGE: $SCRIPTNAME [OPTIONS]"
	echo "Script to control a PostgreSQL instance with the following configuration:"
    showConfig
	echo "  > Note: Change configurations in $INIFILE inside your PostgreSQL directory."
	echo
	echo "OPTIONS:"
	echo "  help, -h, --help      Show this help message"
    echo "  info                  Show configuration for current directory"
	echo "  start                 Start the PostgreSQL Server"
	echo "  stop                  Stop the PostgreSQL Server"
	echo "  restart               Restart the PostgreSQL Server"
	echo "  status                Show the status of the PostgreSQL Server"
	echo "  createdb <DBNAME>     Create a database with name <DBNAME>"
	echo "  initdb                Create a new PostgreSQL database cluster in <DATADIR>"
	echo "                        Change <DATADIR> in the ini-file"
	echo "  test <DBNAME> <FILE>  Test <FILE> with database <DBNAME> (batch mode; single transaction; stop on error)"
	echo "  testall <DBNAME> <FILE>"
	echo "                        Test <FILE> with database <DBNAME> (batch mode; multiple transactions; do not stop on error)"
	echo "  load <DBNAME> <FILE>  Load <FILE> with SQL data into the database <DBNAME>"
    echo "  psql <DBNAME>         Start psql for database <DBNAME>  with current configuration"
    echo "  csvout <DBNAME> <FILE>"
    echo "                        Same as 'load', but writes results as CSV to stdout"
    echo "  csvload <DBNAME> <TABLENAME> <FILE>"
    echo "                        Load a csv-file and store contents in table <TABLENAME>"
    echo "  comparetables <DBNAME> <TABLENAME> <FILE>"
    echo "                        Execute the query in <FILE>, and compare results with <TABLENAME>"
    echo "  patchcreate <ORIGPATH> <NEWPATH> <PATCHFILE>"
    echo "                        Create a patch by comparing two Postgres directories with diff"
    echo "                        See man diff for further details."
    echo "  patchapply <P-LEVEL> <PATCHFILE>"
    echo "                        Apply a patch to a Postgres source code directory"
    echo "                        See man patch for further details."
}

function checkArguments {
	if test $1 -lt $2; then
        showError "$3"
		exit 1
	fi
}

case $1 in
	help|-h|--help)
		showHelp	
	;;
    info)
        showConfig        
    ;;
	start|restart|status|stop)
        checkArguments $# 1 "$1: pg_ctl: additional parameters given, but ignored" 
        if test -z $LOGFILE; then
		    $BINDIR/pg_ctl $1 -D $DATADIR -o "-p $PORT"
        else 
		    $BINDIR/pg_ctl $1 -D $DATADIR -l $LOGFILE -o "-p $PORT"
        fi
	;;
	createdb)
		checkArguments $# 2 "$1: no database name specified!"
		$BINDIR/createdb -p $PORT -h localhost $2
	;;
	load)
		checkArguments $# 3 "$1: no database name and/or data-file specified!"
		$BINDIR/psql -p $PORT -h localhost -d $2 -f $3 		
	;;
	test)
		# Resource: http://petereisentraut.blogspot.it/2010/03/running-sql-scripts-with-psql.html
		
		checkArguments $# 3 "$1: no database name and/or test-file specified!"
		# echo "Test '$3' starts now..." >&2
		# echo "NB: We stop on first error and use a single transaction mode" >&2
		# echo >&2
		PGOPTIONS='--client-min-messages=warning' $BINDIR/psql -p $PORT -h localhost -X -a -q -1 -v ON_ERROR_STOP=1 --pset pager=off -d $2 -f $3 		
	;;
	testall)
		checkArguments $# 3 "$1: no database name and/or test-file specified!"
		PGOPTIONS='--client-min-messages=warning' $BINDIR/psql -p $PORT -h localhost -X -a -q -v ON_ERROR_STOP=0 --pset pager=off -d $2 -f $3 		
	;;
    debug)
        $BINDIR/psql -a -e -p $PORT -h localhost -d $2 -f $3 		
    ;;
    psql)
    	# TODO Build a better checkArguments here... pass additional parameters if any.
        checkArguments $# 2 "$1: database name missing or too many arguments given." 
        $BINDIR/psql -p $PORT -h localhost -d $2
    ;;
    csvout)
    	query=$(sed 's/;//' $3 | grep -v ^SET ) 
    	$BINDIR/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV HEADER DELIMITER ';'"
    ;;
    csvout2)
    	query=$(sed 's/;//' $3 | grep -v ^SET ) 
    	$BINDIR/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV DELIMITER ','"
    ;;
    csvload)
    	# To fetch the absolute path with filename
    	file=$(readlink -m $4)
    	$BINDIR/psql -p $PORT -h localhost -d $2 -c "COPY $3 FROM '$file' DELIMITER ';' CSV HEADER"
    ;;
    comparetables)
    	# http://stackoverflow.com/questions/4602083/sql-compare-data-from-two-tables
    	query=$(sed 's/;//' $4 | grep -v ^SET ) 
    	$BINDIR/psql -p $PORT -h localhost -d $2 -c "SELECT * FROM $3 UNION SELECT * FROM ($query) XXXXX EXCEPT ALL SELECT * FROM $3 INTERSECT SELECT * FROM ($query) YYYYY"
    ;;
    initdb)
    	$BINDIR/initdb -D $DATADIR
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
    ;;
    patchapply)
    	checkArguments $# 3 "$1: Provide a p-level and a patch-file to apply a patch to a postgres directory."
    	patch -p$2 < $3
    ;;
	*)
        showError "OPTION '$1' does not exist." 
        exit 1
	;;
esac

exit $?
