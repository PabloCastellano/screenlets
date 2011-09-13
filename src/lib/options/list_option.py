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
List options, these classes will display all sorts of crazy shit.
"""

import gtk

from screenlets.options import _
from base import Option

class ListOption(Option):
    """An Option for string options."""
    def on_import(self, strvalue):
        """When a list is imported from the config."""
        return eval(strvalue)

    def on_export(self, value):
        """When a list is exported to the config."""
        return str(value)

    def generate_widget(self, value):
        """Generate some widgets for a list."""
        self._entry = gtk.Entry()
        self._entry.set_editable(False)
        self.set_value(value)
        self._entry.show()
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_EDIT, 1)
        but = gtk.Button()
        but.set_image(img)
        but.show()
        but.connect("clicked", self.open_listeditor)
        but.set_tooltip_text(_('Open List-Editor ...'))
        self._entry.set_tooltip_text(self.desc)
        self.widget = gtk.HBox()
        self.widget.add(self._entry)
        self.widget.add(but)
        return self.widget

    def open_listeditor(self, event):
        # open dialog
        dlg = ListOptionDialog()
        # read string from entry and import it through option-class
        # (this is needed to always have an up-to-date value)
        dlg.set_list(self.on_import(self._entry.get_text()))
        resp = dlg.run()
        if resp == gtk.RESPONSE_OK:
            # set text in entry
            self._entry.set_text(str(dlg.get_list()))
            # manually call the options-callback
	    if self.realtime:
                self.has_changed(dlg)
        dlg.destroy()

    def set_value(self, value):
        """Set the list string value as required."""
        self._entry.set_text(str(value))
        self.value = value

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        self.value = widget.get_list()
        super(ListOption, self).has_changed()


class ListOptionDialog(gtk.Dialog):
    """An editing dialog used for editing options of the ListOption-type."""
    model = None
    tree = None
    buttonbox = None

    # call gtk.Dialog.__init__
    def __init__ (self):
        super(ListOptionDialog, self).__init__(
            "Edit List",
            flags=gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK, gtk.RESPONSE_OK)
        )
        # set size
        self.resize(300, 370)
        self.set_keep_above(True)
        # init vars
        self.model = gtk.ListStore(str)
        # create UI
        self.create_ui()

    def create_ui (self):
        """Create the user-interface for this dialog."""
        # create outer hbox (tree|buttons)
        hbox = gtk.HBox()
        hbox.set_border_width(10)
        hbox.set_spacing(10)
        # create tree
        self.tree = gtk.TreeView(model=self.model)
        self.tree.set_headers_visible(False)
        self.tree.set_reorderable(True)
        #self.tree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
        col = gtk.TreeViewColumn('')
        cell = gtk.CellRendererText()
        #cell.set_property('cell-background', 'cyan')
        cell.set_property('foreground', 'black')
        col.pack_start(cell, False)
        col.set_attributes(cell, text=0)
        self.tree.append_column(col)
        self.tree.show()
        hbox.pack_start(self.tree, True, True)
        #sep = gtk.VSeparator()
        #sep.show()
        #hbox.add(sep)
        # create  buttons
        self.buttonbox = bb = gtk.VButtonBox()
        self.buttonbox.set_layout(gtk.BUTTONBOX_START)
        b1 = gtk.Button(stock=gtk.STOCK_ADD)
        b2 = gtk.Button(stock=gtk.STOCK_EDIT)
        b3 = gtk.Button(stock=gtk.STOCK_REMOVE)
        b1.connect('clicked', self.button_callback, 'add')
        b2.connect('clicked', self.button_callback, 'edit')
        b3.connect('clicked', self.button_callback, 'remove')
        bb.add(b1)
        bb.add(b2)
        bb.add(b3)
        self.buttonbox.show_all()
        #hbox.add(self.buttonbox)
        hbox.pack_end(self.buttonbox, False)
        # add everything to outer hbox and show it
        hbox.show()
        self.vbox.add(hbox)

    def set_list (self, lst):
        """Set the list to be edited in this editor."""
        for el in lst:
            self.model.append([el])

    def get_list (self):
        """Return the list that is currently being edited in this editor."""
        lst = []
        for i in self.model:
            lst.append(i[0])
        return lst

    def remove_selected_item (self):
        """Remove the currently selected item."""
        sel = self.tree.get_selection()
        if sel:
            it = sel.get_selected()[1]
            if it:
                print self.model.get_value(it, 0)
                self.model.remove(it)

    def entry_dialog (self, default = ''):
        """Show entry-dialog and return string."""
        entry = gtk.Entry()
        entry.set_text(default)
        entry.show()
        dlg = gtk.Dialog("Add/Edit Item", flags=gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK,
            gtk.RESPONSE_OK))
        dlg.set_keep_above(True)
        dlg.vbox.add(entry)
        resp = dlg.run()
        ret = None
        if resp == gtk.RESPONSE_OK:
            ret = entry.get_text()
        dlg.destroy()
        return ret

    def button_callback (self, widget, id):
        print "PRESS: %s" % id
        if id == 'remove':
            self.remove_selected_item()
        if id == 'add':
            new = self.entry_dialog()
            if new != None:
                self.model.append([new])
        if id == 'edit':
            sel = self.tree.get_selection()
            if sel:
                it = sel.get_selected()[1]
                if it:
                    new = self.entry_dialog(self.model.get_value(it, 0))
                    if new != None:
                        #self.model.append([new])
                        self.model.set_value(it, 0, new)

# TEST>-
"""dlg = ListOptionDialog()
dlg.set_list(['test1', 'afarew34s', 'fhjh23faj', 'yxcdfs58df', 'hsdf7jsdfh'])
dlg.run()
print "RESULT: " + str(dlg.get_list())
dlg.destroy()
import sys
sys.exit(1)"""
# /TEST

