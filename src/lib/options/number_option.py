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
Integer and Float options, these classes will display a spin box.
"""

import gtk, sys

from screenlets.options import _
from base import Option

class IntOption(Option):
    """An Option for integer options."""
    min = -100000
    max = 100000
    increment = 1

    def on_import(self, strvalue):
        """When a integer is imported from the config."""
        try:
            if strvalue[0]=='-':
                return int(float(strvalue[1:])) * -1
            return int(float(strvalue))
        except:
            sys.stderr.write(_("Error during on_import - option: %s.\n") % self.name)
            return 0

        return int(strvalue)

    def on_export(self, value):
        """When a string is exported to the config."""
        return str(value)

    def generate_widget(self, value):
        """Generate a spin button for integer options"""
        self.widget = gtk.SpinButton()
        self.widget.set_increments(self.increment, int(self.max / self.increment))
        if self.min != None and self.max != None:
            self.widget.set_range(self.min, self.max)
        self.set_value(value)
	if self.realtime:
            self.widget.connect("value-changed", self.has_changed)
        return self.widget

    def set_value(self, value):
        """Set the int value, including the value of the widget."""
        self.value = value
        self.widget.set_value(value)

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.value = int(self.widget.get_value())
        super(IntOption, self).has_changed()


class FloatOption(IntOption):
    """An option for float numbers."""
    digits = 0

    def on_import (self, strvalue):
        """Called when FloatOption gets imported. Converts str to float."""
        if strvalue[0]=='-':
            return float(strvalue[1:]) * -1.0
        return float(strvalue)

    def generate_widget(self, value):
        """Do the same as int but add the number of ditgits"""
        super(FloatOption, self).generate_widget(value)
        self.widget.set_digits(self.digits)
        return self.widget

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.value = float(self.widget.get_value())
        super(IntOption, self).has_changed()

