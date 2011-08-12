# 
# Copyright (C) 2009 Martin Owens (DoctorMO) <doctormo@gmail.com>
# Changed by Guido Tabbernuk 2011
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
# 
"""
String options, these classes will display a text box.
"""

import gtk

from screenlets.options import _
from base import Option

class StringOption(Option):
    """An Option for string options."""
    choices = None
    password = False

    def on_import(self, strvalue):
        """When a string is imported from the config."""
        return strvalue.replace("\\n", "\n")

    def on_export(self, value):
        """When a string is exported to the config."""
        return str(value).replace("\n", "\\n")

    def generate_widget(self, value):
        """Generate a textbox for a string options"""
        if self.choices:
            # if a list of values is defined, show combobox
            self.widget = gtk.combo_box_new_text()
            p = -1
            i = 0
            for s in self.choices:
                self.widget.append_text(s)
                if s==value:
                    p = i
                i+=1
            self.widget.set_active(p)
        else:
            self.widget = gtk.Entry()
            # if it is a password, set text to be invisible
            if self.password:
                self.widget.set_visibility(False)

        self.set_value(value)
        self.widget.connect("changed", self.has_changed)
        #self.widget.set_size_request(180, 28)
        return self.widget

    def set_value(self, value):
        """Set the string value as required."""
        self.value = value
        if self.choices:
            # TODO self.widget.set_active(p)
            pass
        else:
            self.widget.set_text(value)

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        if self.choices:
            self.set_value( widget.get_active_text() )
        else:
            self.set_value( widget.get_text() )
        super(StringOption, self).has_changed()
