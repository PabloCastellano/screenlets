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
Account options, these classes will display a text box.
"""

import gtk
try:
	import gnomekeyring
except ImportError: print 'No GNOME keyring, there will be problems with account options'

from screenlets.options import _
from base import Option

class AccountOption(Option):
    """
    An Option-type for username/password combos. Stores the password in
    the gnome-keyring (if available) and only saves username and auth_token
    through the screenlets-backend.
    TODO:
    - not create new token for any change (use "set" instead of "create" if
      the given item already exists)
    - use usual storage if no keyring is available but output warning
    - on_delete-function for removing the data from keyring when the
      Screenlet holding the option gets deleted
    """
    protected = True

    def __init__(self, group, name, *attr, **args):
        super(AccountOption, self).__init__ (group, name, *attr, **args)
        # check for availability of keyring
        if not gnomekeyring.is_available():
            raise Exception('GnomeKeyring is not available!!')
        # THIS IS A WORKAROUND FOR A BUG IN KEYRING (usually we would use
        # gnomekeyring.get_default_keyring_sync() here):
        # find first available keyring
        self.keyring_list = gnomekeyring.list_keyring_names_sync()
        if len(self.keyring_list) == 0:
            raise Exception('No keyrings found. Please create one first!')
        else:
            # we prefer the default keyring
            try:
                self.keyring = gnomekeyring.get_default_keyring_sync()
            except:
                if "session" in self.keyring_list:
                    print "Warning: No default keyring found, using session keyring. Storage is not permanent!"
                    self.keyring = "session"
                else:
                    print "Warning: Neither default nor session keyring found, assuming keyring %s!" % self.keyring_list[0]
                    self.keyring = self.keyring_list[0]


    def on_import(self, strvalue):
        """Import account info from a string (like 'username:auth_token'),.
        retrieve the password from the storage and return a tuple containing
        username and password."""
        # split string into username/auth_token
        #data = strvalue.split(':', 1)
        (name, auth_token) = strvalue.split(':', 1)
        if name and auth_token:
            # read pass from storage
            try:
                pw = gnomekeyring.item_get_info_sync(self.keyring, 
                    int(auth_token)).get_secret()
            except Exception, ex:
                print "ERROR: Unable to read password from keyring: %s" % ex
                pw = ''
            # return
            return (name, pw)
        else:
            raise Exception('Illegal value in AccountOption.on_import.')

    def on_export(self, value):
        """Export the given tuple/list containing a username and a password. The
        function stores the password in the gnomekeyring and returns a
        string in form 'username:auth_token'."""
        # store password in storage
        attribs = dict(name=value[0])
        auth_token = gnomekeyring.item_create_sync(self.keyring, 
            gnomekeyring.ITEM_GENERIC_SECRET, value[0], attribs, value[1], True)
        # build value from username and auth_token
        return value[0] + ':' + str(auth_token)

    def generate_widget(self, value):
        """Generate a textbox for a account options"""
        self.widget = gtk.HBox()
        vb = gtk.VBox()
        input_name = gtk.Entry()
        input_name.set_text(value[0])
        input_name.show()
        input_pass = gtk.Entry()
        input_pass.set_visibility(False)    # password
        input_pass.set_text(value[1])
        input_pass.show()
        vb.add(input_name)
        vb.add(input_pass)
        vb.show()
        but.set_tooltip_text(_('Apply username/password ...'))
        input_name.set_tooltip_text(_('Enter username here ...'))
        input_pass.set_tooltip_text(_('Enter password here ...'))
        self.widget.add(vb)
        return self.widget

    def set_value(self, value):
        """Set the account value as required."""
        self.value = value

    def has_changed(self, widget):
        """Executed when the widget event kicks off."""
        # the widget is a HBox containing a VBox containing two Entries
        # (ideally we should have a custom widget for the AccountOption)
        for c in self.widget.get_children():
            if c.__class__ == gtk.VBox:
               c2 = c.get_children()
               self.value = (c2[0].get_text(), c2[1].get_text())
        super(AccountOption, self).has_changed()

"""#TEST:
o = AccountOption('None', 'pop3_account', ('',''), 'Username/Password', 'Enter username/password here ...')
# save option to keyring
exported_account = o.on_export(('RYX', 'mysecretpassword'))
print exported_account
# and read option back from keyring
print o.on_import(exported_account)
"""

