#!/bin/bash
#
# Bash completion file for the pw_pgcontrol.sh script. This is just a very 
# simple completion file, does not complete anything beyond the first commands.
#
# HOWTO: Copy this script to /etc/bash_completion.d/

_have pw_pgcontrol.sh &&
_show()
{
	local cur opt
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"

    COMPREPLY=( $(compgen -d -W '\
		-h --help -i --info -s --start -S --stop -r --restart \
		--status -c --createdb -I --initdb -t --test -T --testall \
		-l --load -p --psql   --csvout --csvload --comparetables \
		--patchcreate  --patchapply -m --make' -- "$cur" | sort) )
} &&
complete -F _show pw_pgcontrol.sh

