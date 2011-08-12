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

po "screenlets"
po "screenlets-manager"


