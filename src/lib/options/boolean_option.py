# 
# Copyright (C) 2009 Martin Owens (DoctorMO) <doctormo@gmail.com>
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
Boolean options, these classes will display a boolean
Checkbox as required and control the formating of data.
"""

import gtk

from screenlets.options import _
from base import Option

class BoolOption(Option):
    """An Option for boolean values."""
    def on_import(self, strvalue):
        """When a boolean is imported from the config."""
        return strvalue.lower() == "true"

    def on_export(self, value):
        """When a boolean is exported to the config."""
        return str(value)

    def generate_widget(self, value):
        """Generate a checkbox for a boolean option."""
        if not self.widget:
            self.widget = gtk.CheckButton()
            self.set_value(value)
            self.widget.connect("toggled", self.has_changed)
        return self.widget

    def set_value(self, value):
        """Set the true/false value to the checkbox widget"""
        self.value = value
        self.widget.set_active(self.value)

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.set_value( self.widget.get_active() )
        super(BoolOption, self).has_changed()
