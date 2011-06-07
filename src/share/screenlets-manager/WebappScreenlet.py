#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# WebappScreenlet (c) 2007 bu Helder Fraga aka Whise



import screenlets
from screenlets import DefaultMenuItem
from screenlets.options import BoolOption, IntOption, ColorOption
import cairo
import gtk
import gobject
import commands
import sys
import os
from screenlets import sensors
import webkit

class WebappScreenlet (screenlets.Screenlet):
	"""Brings Web applications to your desktop"""
	
	# default meta-info for Screenlets
	__name__		= 'WebappScreenlet'
	__version__		= '0.1'
	__author__		= 'Helder Fraga aka Whise'
	__desc__		= __doc__

	mypath = sys.argv[0][:sys.argv[0].find('WebappScreenlet.py')].strip()
	url = 'myurl'

	def __init__ (self, **keyword_args):
		# init stuff
		screenlets.Screenlet.__init__(self, width=325, height=370,uses_theme=True, 
			is_widget=False, is_sticky=True,draw_buttons=False, **keyword_args)

		self.view = webkit.WebView()
		self.win = gtk.Window()

		#self.win.maximize()
		self.win.add(self.view)

		self.view.load_uri(self.url)
		self.win.connect('destroy',self.quitall)
		self.win.connect("configure-event", self.configure)
		self.view.connect("notify::title",self.update)		

				
	def configure (self, widget, event):
		if event.x != self.x:
			self.x = event.x
			
		if event.y != self.y:
			self.y = event.y

		if event.width != self.width:
			self.width = event.width

		if event.height != self.height:
			self.height = event.height
			
	def on_init(self):
		if self.width == 325 and self.height == 370:
			self.win.set_default_size(700,500)
		else:
			self.win.set_default_size(self.width,self.height)
		self.win.move(self.x,self.y)
		self.win.show_all()

	def update(self,widget):
		
		title = self.view.get_title()
		self.win.set_title(title)
	def quitall(self,widget):
		if len(self.session.instances) > 1:
			self.session.delete_instance (self.id)
			# notify about being rmeoved (does this get send???)
			self.service.instance_removed(self.id)

		else:	
			
		
			self.session.quit_instance (self.id)
			self.service.instance_removed(self.id)
	

			

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(WebappScreenlet)

