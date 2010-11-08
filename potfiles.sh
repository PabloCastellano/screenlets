#!/bin/bash

function po()
{
	xgettext --add-comments --from-code=utf-8 --files-from=$1.in --output=$1/$1.pot
	cd $1
	pwd
	for x in $(ls *.po)
	do
		echo -n "$x: "
		msgmerge -v --update $x $1.pot
	done
	cd ..
}

po "screenlets"
po "screenlets-manager"


