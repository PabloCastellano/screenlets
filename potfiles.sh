#!/bin/bash

VERSION=$(cat VERSION)

function po()
{
	xgettext --add-comments --from-code=utf-8 --files-from=$1.in --output=$1/$1.pot --package-name=screenlets --package-version=$VERSION
	cd $1
	pwd
	for x in $(ls *.po)
	do
		echo -n "$x: "
		msgmerge -v --update $x $1.pot
	done
	cd ..
	echo "-------------------------------------------------"
}

po "screenlets"
po "screenlets-manager"


