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
File options, these classes will display a file select widget.
"""

import gtk
import os

from screenlets.options import _, TOOLTIPS
from base import Option

class FileOption(Option):
    """
    An Option-subclass for string-values that contain filenames. Adds
    a patterns-attribute that can contain a list of patterns to be shown
    in the assigned file selection dialog. The show_pixmaps-attribute
    can be set to True to make the filedialog show all image-types.
    supported by gtk.Pixmap. If the directory-attributue is true, the
    dialog will ony allow directories.

    XXX - Some of this doen't yet work, unknown reason.
    """
    patterns = [ ( 'All Files', ['*'] ) ]
    image = False
    _gtk_file_mode = gtk.FILE_CHOOSER_ACTION_OPEN
    _opener_title = _("Choose File")

    def on_import(self, strvalue):
        """When a file is imported from the config."""
        return strvalue

    def on_export(self, value):
        """When a file is exported to the config."""
        return str(value)

    def generate_widget(self, value):
        """Generate a special widget for file options"""
        dlg = self.generate_file_opener()
        self.widget = gtk.FileChooserButton(dlg)
        self.widget.set_title(self._opener_title)
        self.widget.set_size_request(180, 28)
        self.set_value(value)
        self.widget.connect("selection-changed", self.has_changed)
        return self.widget

    def generate_file_opener(self):
        """Generate a file opener widget"""
        dlg = gtk.FileChooserDialog(action=self._gtk_file_mode,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN, gtk.RESPONSE_OK),
        )
        dlg.set_keep_above(True)
        self.set_filters(dlg)
        return dlg

    def set_filters(self, dlg):
        """Add file filters to the dialog widget"""
        if self.patterns:
            for filter in self.patterns:
                fil = gtk.FileFilter()
                fil.set_name("%s (%s)" % (filter[0], ','.join(filter[1])))
                for pattern in filter[1]:
                    fil.add_pattern(pattern)
                dlg.add_filter(fil)

    def set_value(self, value):
        """Set the file value as required."""
        self.widget.set_filename(value)
        self.value = value

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.value = self.widget.get_filename()
        super(FileOption, self).has_changed()


class DirectoryOption(FileOption):
    """Directory is based on file widgets"""
    _gtk_file_mode = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
    _opener_title = _("Choose Directory")


class ImageOption(FileOption):
    """Image is based on file widgets"""
    _opener_title = _("Choose Image")

    def set_filters(self, dlg):
        """Add the standard pixbug formats"""
        flt = gtk.FileFilter()
        flt.add_pixbuf_formats()
        dlg.set_filter(flt)

    def generate_widget(self, value):
        """Crazy image opener widget generation."""
        # create entry and button (entry is hidden)
        self._entry = gtk.Entry()
        self._entry.set_text(value)
        self._entry.set_editable(False)
        but = gtk.Button('')
        # load preview image
        but.set_image(self.create_preview(value))
        but.connect('clicked', self.but_callback)
        # create widget
        self.widget = gtk.HBox()
        self.widget.add(self._entry)
        self.widget.add(but)
        but.show()
        self.widget.show()
        # add tooltips
        TOOLTIPS.set_tip(but, 'Select Image ...')
        TOOLTIPS.set_tip(but, self.desc)
        return self.widget

    def create_preview(self, filename):
        """Utililty method to reload preview image"""
        if filename and os.path.isfile(filename):
            pb = gtk.gdk.pixbuf_new_from_file_at_size(filename, 64, -1)
            if pb:
                img = gtk.Image()
                img.set_from_pixbuf(pb)
                return img
        img = gtk.image_new_from_stock(gtk.STOCK_MISSING_IMAGE,
            gtk.ICON_SIZE_LARGE_TOOLBAR)
        img.set_size_request(64, 64)
        return img

    def but_callback(self, widget):
        """Create button"""
        dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dlg.set_keep_above(True)
        dlg.set_filename(self._entry.get_text())
        prev = gtk.Image()
        box = gtk.VBox()
        box.set_size_request(150, -1)
        box.add(prev)
        prev.show()
        dlg.set_preview_widget_active(True)
        dlg.connect('selection-changed', self.preview_callback, dlg, prev)
        dlg.set_preview_widget(box)
        response = dlg.run()
        if response == gtk.RESPONSE_OK:
            self._entry.set_text(dlg.get_filename())
            widget.set_image(self.create_preview(dlg.get_filename()))
            self.has_changed(self.widget)
        dlg.destroy()

    def preview_callback(self, widget, dlg, prev):
        """add preview widget to filechooser"""
        fname = dlg.get_preview_filename()
        if fname and os.path.isfile(fname):
            pb = gtk.gdk.pixbuf_new_from_file_at_size(fname, 150, -1)
            if pb:
                prev.set_from_pixbuf(pb)
                dlg.set_preview_widget_active(True)
            else:
                dlg.set_preview_widget_active(False)

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.value = self._entry.get_text()
        super(FileOption, self).has_changed()

