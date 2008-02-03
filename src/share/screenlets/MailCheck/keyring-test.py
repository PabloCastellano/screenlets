# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  keyring-test.py(c) RYX 2007 <ryx [at] ryxperience [dot] com>

import gtk


try: 
	import gnomekeyring 
except ImportError: 
	HAVE_GNOMEKEYRING = False 
else: 
	HAVE_GNOMEKEYRING = True 

# TEST:
#import gobject
#gtk.set_application_name("keyring-test")
if HAVE_GNOMEKEYRING:
	# check availability
	if not gnomekeyring.is_available():
		print "Keyring not available."
	# list names of keyrings and use the first one we can find
	keyring_list = gnomekeyring.list_keyring_names_sync()
	if len(keyring_list) == 0:
		print "No keyrings available."
		import sys
		sys.exit(1)
	else:
		print "We have %i keyrings" % len(keyring_list)
		print "KEYRING: %s" % keyring_list[0]
	# name/password to store
	name		= 'myname'
	password	= 'mysecret'
	# get default keyring
	keyring = gnomekeyring.get_default_keyring_sync() 	# crashes if no default exists
	# create attributes
	attribs = dict(name=name, magic='something')
	
	# create keyring item with password
	auth_token = gnomekeyring.item_create_sync(keyring, 
		gnomekeyring.ITEM_GENERIC_SECRET, name, attribs, password, True) 
	print auth_token
	print "save: token for account %s: %i" % (name, auth_token) 
	token = "gnomekeyring:%i" % (auth_token,) 
	print token
	
	# now read it back from the keyring
	print "Password read from keyring is:"
	print gnomekeyring.item_get_info_sync(keyring, auth_token).get_secret()

