#!/bin/bash
#
# Bash completion file for the p-pgcontrol.sh script. This is just a very 
# simple completion file, does not complete anything beyond the first commands.
#
# HOWTO: Copy this script to /etc/bash_completion.d/

_have p-pgcontrol.sh &&
_show() {
	local cur opt prev
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [[ "$cur" = -* ]]; then
		COMPREPLY=( $(compgen -d -W '\
			-h --help -i --info -s --start -S --stop -r --restart \
			--status -c --createdb -I --initdb -t --test -T --testall \
			--regressiontest -l --load -p --psql --csvout --csvload \
			--comparetables --patchcreate --patchcreatetestonly \
			--patch -m --make -x --restartclean --configure --testinitdb' -- "$cur") )
		return 0
	fi
	
	_filedir
	return 0
	
} &&
complete -F _show p-pgcontrol.sh

