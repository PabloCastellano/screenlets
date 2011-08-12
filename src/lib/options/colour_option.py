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
Color options, these classes will display a text box.
"""

import gtk

from screenlets.options import _
from base import Option

class ColorOption(Option):
    """An Option for color options."""
    def on_import(self, strvalue):
        """Import (r, g, b, a) from comma-separated string."""
        # strip braces and spaces
        strvalue = strvalue.lstrip('(')
        strvalue = strvalue.rstrip(')')
        strvalue = strvalue.strip()
        # split value on commas
        tmpval = strvalue.split(',')
        outval = []
        for f in tmpval:
            # create list and again remove spaces
            outval.append(float(f.strip()))
        return outval

    def on_export(self, value):
        """Export r, g, b, a to comma-separated string."""
        l = len(value)
        outval = ''
        for i in xrange(l):
            if type(value[i]) == float:
                outval += "%0.5f" % value[i]
            else:
                outval += str(value[i])
            if i < l-1:
                outval += ','
        return outval

    def generate_widget(self, value):
        """Generate a textbox for a color options"""
        self.widget = self.get_box_from_colour( value )
        self.set_value(value)
        return self.widget

    def set_value(self, value):
        """Set the color value as required."""
        self.value = value

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.value = self.get_colour_from_box(self.widget)
        super(ColorOption, self).has_changed()

    def get_box_from_colour(self, colour):
        """Turn a colour array into a colour widget"""
        result = gtk.ColorButton(gtk.gdk.Color(
            int(colour[0]*65535), int(colour[1]*65535), int(colour[2]*65535)))
        result.set_use_alpha(True)
        result.set_alpha(int(colour[3]*65535))
        result.connect("color-set", self.has_changed)
        return result

    def get_colour_from_box(self, widget):
        """Turn a colour widget into a colour array"""
        colour = widget.get_color()
        return (
            colour.red/65535.0,
            colour.green/65535.0,
            colour.blue/65535.0,
            widget.get_alpha()/65535.0
        )


class ColorsOption(ColorOption):
    """Allow a list of colours to be created"""
    def on_import(self, value):
        """Importing multiple colours"""
        result = []
        for col in value.split(';'):
            if col:
               result.append(super(ColorsOption, self).on_import(col))
        return result

    def on_export(self, value):
        """Exporting multiple colours"""
        result = ""
        for col in value:
            result += super(ColorsOption, self).on_export(col)+';'
        return result

    def generate_widget(self, value):
        """Generate a textbox for a color options"""
        self.widget = gtk.HBox()
        if type(value[0]) in [int, float]:
            value = [value]
        for col in value:
            self.add_colour_box(self.widget, col, False)

        but = gtk.Button('Add', gtk.STOCK_ADD)
        but.show()
        but.connect("clicked", self.add_colour_box)
        self.widget.pack_end(but)

        self.set_value(value)
        return self.widget

    def del_colour_box(self, widget, event):
        """Remove a colour box from the array when right clicked"""
        if event.button == 3:
            if len(self.widget.get_children()) > 2:
                self.widget.remove(widget)
                self.has_changed(widget)

    def add_colour_box(self, widget, col=None, update=True):
        """Add a new box for colours"""
        if not col:
            col = self.value[-1]
        new_box = self.get_box_from_colour( col )
        new_box.connect("button_press_event", self.del_colour_box)
        self.widget.pack_start(new_box, padding=1)
        new_box.show()
        if update:
            self.has_changed(widget)

    def has_changed(self, widget):
        """The colour widgets have changed!"""
        self.value = []
        for c in self.widget.get_children():
            if type(c) == gtk.ColorButton:
                self.value.append(self.get_colour_from_box( c ))
        super(ColorOption, self).has_changed()

