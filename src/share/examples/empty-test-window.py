#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# (c) 2007 RYX (aka Rico Pfaus) <ryx@ryxperience.com>

import gtk


#from gobject import GObject

# A simple testbed
#


# testing app class
class TestApp(object):

	def __init__ (self):
		self.win = gtk.Window()
		self.win.show()
		self.win.connect('delete-event', self.handle_delete)
		
	def start (self):
		gtk.main()
	
	def handle_delete (self, window, event):
		print "Bye!"
		gtk.main_quit()

# TEST
app = TestApp()
app.start()

