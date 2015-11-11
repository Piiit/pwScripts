#!/bin/bash
SCRIPTNAME=${0##*/}
INI=.pw_pgcontrol.ini

function showConfig {
	echo "  Port: $PORT"
	echo "  Log : $LOG"
	echo "  Data: $DATA"
	echo "  Bin : $BIN"
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
	echo " -S, --stop            |Stop the PostgreSQL Server"
	echo " -r, --restart         |Restart the PostgreSQL Server"
	echo "     --status          |Show the status of the PostgreSQL Server"
	echo " -c, --createdb DB     |Create a database with name DB"
	echo " -I, --initdb          |Create a new PostgreSQL database cluster in \$DATA"
	echo "                       |Change \$DATA in the ini-file"
	echo " -t, --test DB FILE    |Test FILE with database DB (batch mode; single transaction; stop on error)"
	echo " -T, --testall DB FILE |Test FILE with database DB (batch mode; multiple transactions; do not stop on error)"
	echo " -l, --load DB FILE    |Load FILE with SQL data into the database DB"
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
	echo " -m, --make            |Compiles the source of PostgreSQL, restarts the server, and"
	echo "                       |displays server's log file"
	echo
	echo "CONFIG:"
	showConfig
	echo "  > Note: Change configurations in '$INI' inside your PostgreSQL directory."

	exit 0
}

function showError {
	echo "$SCRIPTNAME: ERROR: $1" >&2
	echo >&2
	showHelp >&2
}

# Fetch environment information about the PostgreSQL installation
function loadINI {
	test -f $INI && . $INI || { 
		showError "No evironment INI file found. Have you specified PostgreSQL configs in $INI?"
		return 1
	}
	
	# Binary dir default setting, if not set inside the INI-file...
	test -z $BIN && BIN="./server/bin"
	
	return 0
}

function checkArguments {
	if test $1 -lt $2; then
        showError "$3"
		exit 1
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
	$BIN/pg_ctl $1 -D $2 $L -o "-p $3"
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
	$BIN/psql -p $1 -h localhost -d $2 -f $3 $4
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
	getopt -q -o "hisrtTSIc:l:p:m" \
	-l "help,info,start,stop,restart,status,initdb,createdb:,test:,testall:,
	load:,psql:,csvout:,csvload:,comparetables:,patchcreate:,patchapply:make" \
	-n $SCRIPTNAME -- "$@"
)

if [ $? != 0 ] ; then
	showError "Wrong argument given: $@"
	echo
	showHelp
	exit 1
fi

eval set -- "$ARGS"

loadINI || showHelp

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
			$BIN/createdb -p $PORT -h localhost $2
		    exit $?
		;;
		-l | --load)
			checkArguments $# 3 "$1: no database name and/or data-file specified!"
			callPsql $PORT $2 $4 		
			exit $?
		;;
		-t | --test)
			# Resource: http://petereisentraut.blogspot.it/2010/03/running-sql-scripts-with-psql.html
			checkArguments $# 4 "--test DB FILE: no database name or test-file specified!"
			PGOPTIONS='--client-min-messages=warning' $BIN/psql -p $PORT -h localhost -X -a -q -1 -v ON_ERROR_STOP=1 --pset pager=off -d $2 -f $4 2>&1
			exit $?
		;;
		-T | --testall)
			checkArguments $# 4 "--testall DB FILE: no database name or test-file specified!"
			PGOPTIONS='--client-min-messages=warning' $BIN/psql -p $PORT -h localhost -X -a -q -v ON_ERROR_STOP=0 --pset pager=off -d $2 -f $4 2>&1		
			exit $?
		;;
		--debug)
		    $BIN/psql -a -e -p $PORT -h localhost -d $2 -f $3 
		    exit $?		
		;;
		-p | --psql)
			# TODO Build a better checkArguments here... pass additional parameters if any.
		    checkArguments $# 2 "$1: database name missing or too many arguments given." 
		    $BIN/psql -p $PORT -h localhost -d $2
		    exit $?
		;;
		--csvout)
			query=$(sed 's/;//' $3 | grep -v ^SET ) 
			$BIN/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV HEADER DELIMITER ';'"
			exit $?
		;;
		--csvout2)
			query=$(sed 's/;//' $3 | grep -v ^SET ) 
			$BIN/psql -p $PORT -h localhost -d $2 -c "COPY ( $query ) TO STDOUT WITH CSV DELIMITER ','"
			exit $?
		;;
		--csvload)
			# To fetch the absolute path with filename
			file=$(readlink -m $4)
			$BIN/psql -p $PORT -h localhost -d $2 -c "COPY $3 FROM '$file' DELIMITER ';' CSV HEADER"
			exit $?
		;;
		--comparetables)
			# http://stackoverflow.com/questions/4602083/sql-compare-data-from-two-tables
			query=$(sed 's/;//' $4 | grep -v ^SET ) 
			$BIN/psql -p $PORT -h localhost -d $2 -c "SELECT * FROM $3 UNION SELECT * FROM ($query) XXXXX EXCEPT ALL SELECT * FROM $3 INTERSECT SELECT * FROM ($query) YYYYY"
			exit $?
		;;
		-I | --initdb)
			$BIN/initdb -D $DATA
			exit $?
		;;
		--testinitdb)
			TMPDIR="/tmp/$SCRIPTNAME-initdb-test.$$"
	 		$BIN/initdb -D $TMPDIR
	 		RES=$?
	 		rm -rf $TMPDIR
	 		exit $RES
		;;
		--patchcreate)
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
		--patchapply)
			checkArguments $# 3 "$1: Provide a p-level and a patch-file to apply a patch to a postgres directory."
			patch -p$2 < $3
			exit $?
		;;
		-m | --make )
			test -z $LOG && {
				showError "LOG not set in INI file $INI."
				exit 1
			}

			rm -f $LOG || {
				showError "Can not remove LOG file $LOG."
				exit 1
			}

			make && make install && callPgCtl restart $DATA $PORT $LOG

			if test $? -ne 0; then
				exit $?
			fi

			# Wait until log file exists, i.e. server has been started...
			while [ ! -f $LOG ]
			do
				echo -n -e "\rWaiting for PostgreSQL server to start up..."
			done

			clear
			tail -f $LOG

			exit 0
		;;
		-- ) 
			shift
			break 
		;;
		*)
		    showError "OPTION '$1' does not exist." 
		    echo
		    showHelp
		    exit 1
		;;
	esac
done



# We should not reach this line!
showError "No parameter specified"
echo
showHelp

exit 1
