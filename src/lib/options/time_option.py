# 
# Copyright (C) 2009 Martin Owens (DoctorMO) <doctormo@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# 
"""
Time options, these classes will display a text box.
"""

import gtk

from screenlets.options import _
from colour_option import ColorOption

class TimeOption(ColorOption):
    """An class for time options."""

    def generate_widget(self, value):
        """Generate a textbox for a time options"""
        self.widget = gtk.HBox()
        input_hour = gtk.SpinButton()
        input_minute = gtk.SpinButton()
        input_second = gtk.SpinButton()
        input_hour.set_range(0, 23)
        input_hour.set_max_length(2)
        input_hour.set_increments(1, 1)
        input_hour.set_numeric(True)
        input_hour.set_value(value[0])
        input_minute.set_range(0, 59)
        input_minute.set_max_length(2)
        input_minute.set_increments(1, 1)
        input_minute.set_numeric(True)
        input_minute.set_value(value[1])
        input_second.set_range(0, 59)
        input_second.set_max_length(2)
        input_second.set_increments(1, 1)
        input_second.set_numeric(True)
        input_second.set_value(value[2])
        input_hour.connect('value-changed', self.has_changed)
        input_minute.connect('value-changed', self.has_changed)
        input_second.connect('value-changed', self.has_changed)
        input_hour.set_tooltip_text(self.desc)
        input_minute.set_tooltip_text(self.desc)
        input_second.set_tooltip_text(self.desc)
        self.widget.add(input_hour)
        self.widget.add(gtk.Label(':'))
        self.widget.add(input_minute)
        self.widget.add(gtk.Label(':'))
        self.widget.add(input_second)
        self.widget.add(gtk.Label('h'))
        self.widget.show_all()
        return self.widget

    def set_value(self, value):
        """Set the time value as required."""
        self.value = value

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        box = widget.get_parent()
        inputs = box.get_children()
        self.value = (
            int(inputs[0].get_value()),
            int(inputs[2].get_value()),
            int(inputs[4].get_value()),
        )
        super(ColorOption, self).has_changed()

