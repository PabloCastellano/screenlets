#!/bin/bash
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

VERSION=$(cat VERSION)
INDIV_ROOT=../indiv-screenlets/
function po()
{
	tmpname="/tmp/$(uuidgen).pot"
	xgettext --add-comments --from-code=utf-8 --files-from="$1.in" --output="$tmpname" --package-name=screenlets --package-version=$VERSION
	if [ -e "$tmpname" ]; then
		# check if pot has changed at all
		strip1="/tmp/$(uuidgen).pot"
		strip2="/tmp/$(uuidgen).pot"
		grep -v "\"POT-Creation-Date:.*[[:digit:]].*\"" "$tmpname" > "$strip1"
		grep -v "\"POT-Creation-Date:.*[[:digit:]].*\"" "$1/$1.pot" > "$strip2"
		res=`diff $strip1 $strip2`
		
		if [ "$res" != "" ]; then
			# more than just a date has changed
			echo "*** $1.pot"
			cp "$tmpname" "$1/$1.pot"
		else
			notprinted=true
		fi
		
		cd $1
#		pwd
		for x in $(ls *.po 2>/dev/null)
		do
			# check if po has changed and not just the position of Language field
			cp "$x" "$strip1"
			cp "$x" "$strip2"
			# to indicate which screenlet is being processed if pot is not created
			if $notprinted; then
				echo "--- $filename"
				notprinted=false
			fi
			echo -n "$x: "
			msgmerge -v --update "$strip2" "$1.pot"
			potemp="/tmp/$(uuidgen)"
			cp "$strip2" "$potemp"
			str="\"Language:.*[[:alpha:]].*\""
			linenr=$(grep -m 1 -n "$str" "$strip1" | sed -r -e "s/([[:digit:]]*)(:.*)/\1/")
			sed -r -i -e "$linenr d" "$strip1"
			linenr=$(grep -m 1 -n "$str" "$strip2" | sed -r -e "s/([[:digit:]]*)(:.*)/\1/")
			sed -r -i -e "$linenr d" "$strip2"
			res=`diff -q $strip1 $strip2`
			if [ "$res" != "" ]; then
				# more than just a date has positon of Language field has changed
				mv "$potemp" "$x"
			fi
		done
		cd ..
		echo "-------------------------------------------------"
	fi
}

function po_categories() {
	SAVEIFS=$IFS
	IFS=$(echo -en "\n\b")
	CAT_LIST=`cat $INDIV_ROOT/src/*/*.py | grep __category__ | awk -F\' '{print tolower($(NF-1))}'  | sort -r |uniq -c| awk '{for(i=2;i<=NF;i++)
printf "%s ",$i;print "" }'`
	echo -e "\n#Extracted categories from indiv-screenlets\n" >> $1/$1.pot
	for i in $CAT_LIST 
	do
		i=`echo $i | sed 's/ *$//g'`
		l=`echo ${i:0:1} | tr "[:lower:]" "[:upper:]"`
		echo -e "msgid \"$l${i:1}\"\nmsgstr \"\"\n" >> $1/$1.pot
	done
	IFS=$SAVEIFS
}

po "screenlets"
po "screenlets-manager"
po_categories "screenlets-manager"


