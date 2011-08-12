#!/usr/bin/env python

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

