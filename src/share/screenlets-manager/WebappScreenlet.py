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

#########WORKARROUND FOR GTKOZEMBED BUG BY WHISE################
myfile = 'WebappScreenlet.py'
mypath = sys.argv[0][:sys.argv[0].find('myfile')].strip()

if sys.argv[0].endswith(myfile): # Makes Shure its not the manager running...
		# First workarround
		a = str(commands.getoutput('whereis firefox')).replace('firefox: ','').split(' ')
		for b in a:
			if os.path.isfile(b + '/run-mozilla.sh'):
				c = b + '/run-mozilla.sh'
				workarround = c + " " + sys.argv[0] + " &"

		if c == None:
			# Second workarround
			print 'First workarround didnt work let run a second manual workarround'
			if str(sensors.sys_get_distrib_name()).lower().find('ubuntu') != -1: # Works for ubuntu 32
				workarround = "export LD_LIBRARY_PATH=/usr/lib/firefox \n export MOZILLA_FIVE_HOME=/usr/lib/firefox \n python "+ sys.argv[0] + " &"
			elif str(sensors.sys_get_distrib_name()).lower().find('debian') != -1: # Works for debian 32 with iceweasel installed
				workarround = "export LD_LIBRARY_PATH=/usr/lib/iceweasel \n export MOZILLA_FIVE_HOME=/usr/lib/iceweasel \n python " + sys.argv[0] + " &"
			elif str(sensors.sys_get_distrib_name()).lower().find('suse') != -1: # Works for suse 32 with seamonkey installed
				workarround = "export LD_LIBRARY_PATH=/usr/lib/seamonkey \n export MOZILLA_FIVE_HOME=/usr/lib/seamonkey \n python "+ sys.argv[0] + " &"
				print 'Your running suse , make shure you have seamonkey installed'
			elif str(sensors.sys_get_distrib_name()).lower().find('fedora') != -1: # Works for fedora 32 with seamonkey installed
				workarround = "export LD_LIBRARY_PATH=/usr/lib/seamonkey \n export MOZILLA_FIVE_HOME=/usr/lib/seamonkey \n python "+ sys.argv[0] + " &"
				print 'Your running fedora , make shure you have seamonkey installed'


		if os.path.isfile("/tmp/"+ myfile+"running"):
			os.system("rm -f " + "/tmp/"+ myfile+"running")
		
		else:
			
			os.system (workarround)
			fileObj = open("/tmp/"+ myfile+"running","w") #// open for for write
			fileObj.write('gtkmozembed bug workarround')
		
			fileObj.close()
			exit()


else:
	pass
try:
	import gtkmozembed
except:
	screenlets.show_error(None,"You need Gtkmozembed to run this Screenlet , please install it")
#########WORKARROUND FOR GTKOZEMBED BUG BY WHISE################



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

		if hasattr(gtkmozembed, 'set_profile_path'):
			gtkmozembed.set_profile_path(self.mypath,'mozilla')
		else:
			gtkmozembed.gtk_moz_embed_set_profile_path(self.mypath ,'mozilla')

		self.moz = gtkmozembed.MozEmbed()
		self.win = gtk.Window()

		#self.win.maximize()
		self.win.add(self.moz)

		self.moz.load_url(self.url)
		self.win.connect('destroy',self.quitall)
		self.win.connect("configure-event", self.configure)
		self.moz.connect("title",self.update)		

				
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
		
		title = self.moz.get_title()
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

