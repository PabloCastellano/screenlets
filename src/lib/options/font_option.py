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
Font options, these classes will display a text box.
"""

import gtk

from screenlets.options import _
from base import Option

class FontOption(Option):
    """An class for font options."""
    def on_import(self, strvalue):
        """When a font is imported from the config."""
        return strvalue

    def on_export(self, value):
        """When a font is exported to the config."""
        return str(value)

    def generate_widget(self, value):
        """Generate a special widget for font options"""
        self.widget = gtk.FontButton()
        self.set_value(value)
        self.widget.connect("font-set", self.has_changed)
        return self.widget

    def set_value(self, value):
        """Set the font value as required."""
        self.widget.set_font_name(value)
        self.value = value

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.value = widget.get_font_name()
        super(FontOption, self).has_changed()
