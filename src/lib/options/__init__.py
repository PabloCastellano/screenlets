#
# Options-system (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
# Heavily Refactored by Martin Owens (c) 2009
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
# INFO:
# - a dynamic Options-system that allows very easy creation of
#   objects with embedded configuration-system.
#   NOTE: The Dialog is not very nice yet - it is not good OOP-practice
#   because too big functions and bad class-layout ... but it works
#   for now ... :)
#
# TODO:
# - option-widgets for all option-types (e.g. ListOptionWidget, ColorOptionWidget)
# - OptionGroup-class instead of (or behind) add_options_group
# - TimeOption, DateOption
# - FileOption needs filter/limit-attribute
# - allow options to disable/enable other options
# - support for EditableOptions-subclasses as options
# - separate OptionEditorWidget from Editor-Dialog
# - place ui-code into screenlets.options.ui-module
# - create own widgets for each Option-subclass
#

import screenlets

import os
import gtk, gobject

# translation stuff
import gettext
gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', screenlets.INSTALL_PREFIX +  '/share/locale')

def _(s):
    return gettext.gettext(s)

from boolean_option import BoolOption
from string_option import StringOption
from number_option import IntOption, FloatOption
from list_option import ListOption
from account_option import AccountOption
from font_option import FontOption
from file_option import FileOption, DirectoryOption, ImageOption
from colour_option import ColorOption, ColorsOption
from time_option import TimeOption
from base import EditableOptions, OptionsDialog, create_option_from_node

# ------ ONLY FOR TESTING ------------------:
if __name__ == "__main__":

    import os

    # this is only for testing - should be a Screenlet
    class TestObject (EditableOptions):

        testlist = ['test1', 'test2', 3, 5, 'Noch ein Test']
        pop3_account = ('Username', '')

        # TEST
        pin_x        = 100
        pin_y        = 6
        text_x        = 19
        text_y        = 35
        font_name    = 'Sans 12'
        rgba_color    = (0.0, 0.0, 1.0, 1.0)
        text_prefix    = '<b>'
        text_suffix    = '</b>'
        note_text    = ""    # hidden option because val has its own editing-dialog
        random_pin_pos    = True
        opt1 = 'testval 1'
        opt2 = 'testval 2'
        filename2    = ''
        filename    = ''
        dirname        = ''
        font = 'Sans 12'
        color = (0.1, 0.5, 0.9, 0.9)
        name = 'a name'
        name2 = 'another name'
        combo_test = 'el2'
        flt = 0.5
        x = 10
        y = 25
        width = 30
        height = 50
        is_sticky = False
        is_widget = False
        time    = (12, 32, 49)        # a time-value (tuple with ints)

        def __init__ (self):
            EditableOptions.__init__(self)
            # Add group
            self.add_options_group('General',
                'The general options for this Object ...')
            self.add_options_group('Window',
                'The Window-related options for this Object ...')
            self.add_options_group('Test', 'A Test-group ...')
            # Add editable options
            self.add_option(ListOption('Test', 'testlist', default=self.testlist,
                label='ListOption-Test', desc='Testing a ListOption-type ...'))
            self.add_option(StringOption('Window', 'name', default='TESTNAME',
                label='Testname', desc='The name/id of this Screenlet-instance ...'),
                realtime=False)
            self.add_option(AccountOption('Test', 'pop3_account',
                default=self.pop3_account, label='Username/Password',
                desc='Enter username/password here ...'))
            self.add_option(StringOption('Window', 'name2', default='TESTNAME2',
                label='String2', desc='Another string-test ...'))
            self.add_option(StringOption('Test', 'combo_test', default="el1",
                label='Combo', desc='A StringOption for a drop-down-list.',
                choices=['el1', 'el2', 'element 3']))
            self.add_option(FloatOption('General', 'flt', default=30.4,
                label='A Float', desc='Testing a FLOAT-type ...',
                min=0, max=gtk.gdk.screen_width(), increment=0.01, digits=4))
            self.add_option(IntOption('General', 'x', default=30,
                label='X-Position', desc='The X-position of this Screenlet ...',
                min=0, max=gtk.gdk.screen_width()))
            self.add_option(IntOption('General', 'y', default=30,
                label='Y-Position', desc='The Y-position of this Screenlet ...',
                min=0, max=gtk.gdk.screen_height()))
            self.add_option(IntOption('Test', 'width', default=300,
                label='Width', desc='The width of this Screenlet ...',
                min=100, max=1000, increment=12))
            self.add_option(IntOption('Test', 'height', default=150,
                label='Height', desc='The height of this Screenlet ...',
                min=100, max=1000))
            self.add_option(BoolOption('General', 'is_sticky', default=True,
                label='Stick to Desktop', desc='Show this Screenlet always ...'))
            self.add_option(BoolOption('General', 'is_widget', default=False,
                label='Treat as Widget', desc='Treat this Screenlet as a "Widget" ...'))
            self.add_option(FontOption('Test', 'font', default='Sans 14',
                label='Font', desc='The font for whatever ...'))
            self.add_option(ColorOption('Test', 'color', default=(1, 0.35, 0.35, 0.7),
                label='Color', desc='The color for whatever ...'))
            self.add_option(ColorsOption('Test', 'rainbows', default=[(1, 0.35, 0.35, 0.7), (0.1, 0.8, 0.2, 0.2), (1, 0.35, 0.6, 0.7)],
                label='Multi-Colours', desc='The colors for whatever ...'))
            self.add_option(ColorsOption('Test', 'rainbow2', default=(1, 0.35, 0.35, 0.7),
                label='Colours-Up', desc='The colors for whatever ...'))
            self.add_option(FileOption('Test', 'filename', default=os.environ['HOME'],
                label='Filename-Test', desc='Testing a FileOption-type ...',
                patterns=[ ( 'Python Files', ['*.py', '*.pyc'] ) ]))
            self.add_option(ImageOption('Test', 'filename2', default=os.environ['HOME'],
                label='Image-Test', desc='Testing the ImageOption-type ...'))
            self.add_option(DirectoryOption('Test', 'dirname', default=os.environ['HOME'],
                label='Directory-Test', desc='Testing a FileOption-type ...'))
            self.add_option(TimeOption('Test','time', default=self.time,
                label='TimeOption-Test', desc='Testing a TimeOption-type ...'))
            # TEST
            self.disable_option('width')
            self.disable_option('height')
            # TEST: load options from file
            #self.add_options_from_file('/home/ryx/Desktop/python/screenlets/screenlets-0.0.9/src/share/screenlets/Notes/options.xml')

        def __setattr__(self, name, value):
            self.__dict__[name] = value
            print name + "=" + str(value)

        def get_short_name(self):
            return self.__class__.__name__[:-6]


    # this is only for testing - should be a Screenlet
    class TestChildObject (TestObject):

        uses_theme = True
        theme_name = 'test'

        def __init__ (self):
            TestObject.__init__(self)
            self.add_option(StringOption('Test', 'anothertest', default='ksjhsjgd',
                label='Another Test', desc='An attribute in the subclass  ...'))
            self.add_option(StringOption('Test', 'theme_name', default=self.theme_name,
                label='Theme', desc='The theme for this Screenelt  ...',
                choices=['test1', 'test2', 'mytheme', 'blue', 'test']))

    # TEST: load/save
    # TEST: option-editing
    to = TestChildObject()
    #print to.export_options_as_list()
    se = OptionsDialog(500, 380)#, treeview=True)
    #img = gtk.image_new_from_stock(gtk.STOCK_ABOUT, 5)
    img = gtk.Image()
    img.set_from_file('../share/screenlets/Notes/icon.svg')
    se.set_info('TestOptions',
        'A test for an extended options-dialog with embedded about-info.' +
        ' Can be used for the Screenlets to have all in one ...\nNOTE:' +
        '<span color="red"> ONLY A TEST!</span>',
        '(c) RYX 2007', version='v0.0.1', icon=img)
    se.show_options_for_object(to)
    resp = se.run()
    if resp == gtk.RESPONSE_OK:
        print "OK"
    else:
        print "Cancelled."
    se.destroy()
    print to.export_options_as_list()

