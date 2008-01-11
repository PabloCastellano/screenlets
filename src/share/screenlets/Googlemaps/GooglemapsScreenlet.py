#!/usr/bin/env python

# GooglemapsScreenlet  (c) 2007 bu Helder Fraga aka Whise
#


import screenlets
from screenlets import DefaultMenuItem
from screenlets.options import BoolOption
import cairo
import gtk
import wnck
import gobject
import commands
import sys
import os


#########WORKARROUND FOR GTKOZEMBED BUG################

if sys.argv[0].endswith('GooglemapsScreenlet.py'):

	if commands.getoutput("lsb_release -is") == 'Ubuntu':
		mypath = sys.argv[0][:sys.argv[0].find('GooglemapsScreenlet.py')].strip()
		if os.path.isfile(mypath + "running"):
			os.system("rm -f " + mypath + "running")
		
		else:
			os.system ("export LD_LIBRARY_PATH=/usr/lib/firefox \n export MOZILLA_FIVE_HOME=/usr/lib/firefox \n python "+ sys.argv[0] + " &")
			fileObj = open(mypath + "running","w") #// open for for write
			fileObj.write('gtkmozembed bug workarround')
		
			fileObj.close()
			exit()
else:
	pass
try:
	import gtkmozembed
except:
	print 'You dont have gtkmozembed , please install python gnome extras'

class GooglemapsScreenlet (screenlets.Screenlet):
	"""A Google Maps Screenlet, If you use this screenlet to make other html screenlets please give me some credits"""
	
	# default meta-info for Screenlets
	__name__		= 'GooglemapsScreenlet'
	__version__		= '0.6'
	__author__		= 'Helder Fraga aka Whise'
	__desc__		= __doc__
	width =425
	height = 470
	box = None
	fh = None
	fh1 = None
	fh2 = None
	gameswf = 'arkanoid.swf'
	moz = None
	box = gtk.VBox(False, 0)
	mypath = sys.argv[0][:sys.argv[0].find('GooglemapsScreenlet.py')].strip()

	url = str(mypath)+'geomap.html'

	def __init__ (self, **keyword_args):
		# init stuff
		screenlets.Screenlet.__init__(self, width=int(self.width*self.scale), height=int(self.height*self.scale),uses_theme=True, 
			is_widget=False, is_sticky=True, **keyword_args)
		#self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_default_menuitems()
	
		#self.disable_option('scale')
		# create container for our moz-widget
		self.theme_name = "default"
		self.fh = open(str(self.mypath)+'geomap.html', 'r')
		self.fh1 = self.fh.read()
		self.fh.close()
		self.fh1 = self.fh1.replace('380',str(int(int(380)*self.scale)))
		self.fh1 = self.fh1.replace('370',str(int(int(370)*self.scale)))
		fh2 = open(str(self.mypath)+'gtoload.html', 'w')
		fh2.write(self.fh1)
		fh2.close()
		self.url = str(self.mypath)+'gtoload.html'
		if self.box != None:
			
			self.box.set_border_width(int(15*self.scale))

			# create evntbox
		
			self.box.set_size_request(int(1*self.scale),int((self.height-77)*(self.scale)-(self.scale*5)))
			self.moz = gtkmozembed.MozEmbed()
			self.moz.set_size_request(int(1*self.scale),int((self.height-77)*(self.scale)-(self.scale*5)))
		
			self.moz.load_url(str(self.url))
		
		# add/show all inputs
		
	

    			self.box.pack_start(self.moz, False, False, 0)
			self.box.set_uposition(1,46)
			self.window.add(self.box)		
		
			self.window.show_all()
	#def moz_button_press (self, widget, event):
		
		#print "Button press inside Mozilla Widget"

	def on_draw (self, ctx):
		ctx.scale(self.scale, self.scale)
		ctx.set_source_rgba(0, 0, 0, 0)
 		ctx.rectangle(0, 0, self.width*self.scale, self.height*self.scale)
		ctx.fill()
		
		
			#self.box = None
		if self.theme:
			self.theme['bg.svg'].render_cairo(ctx)
		
 	def on_mouse_down(self,event):
		x = event.x / self.scale
		y = event.y / self.scale

		
		if y >= 48 and y <= 60 and x >= 71 and x <= 247:
			self.moz.load_url(str(self.url))


		self.redraw_canvas()


	def on_scale(self):
		print 'scaling'

		if self.window:
			self.box.set_border_width(int(15*self.scale))
			self.box.set_uposition(int(1*self.scale),int(46*self.scale+(self.scale*5)))
			self.moz.set_size_request(int(1*self.scale),int((self.height-77)*(self.scale)-(self.scale*5)))
		self.fh = open(str(self.mypath)+'geomap.html', 'r')
		self.fh1 = self.fh.read()
		self.fh.close()
		self.fh1 = self.fh1.replace('380',str(int(int(380)*self.scale)))
		self.fh1 = self.fh1.replace('370',str(int(int(370)*self.scale)))
		fh2 = open(str(self.mypath)+'gtoload.html', 'w')
		fh2.write(self.fh1)
		fh2.close()
		self.url = str(self.mypath)+'gtoload.html'
		self.moz.load_url(str(self.url))
	def on_draw_shape (self, ctx):
		ctx.scale(self.scale, self.scale)
		ctx.set_source_rgba(0, 0, 0, 1)
 		ctx.rectangle(0, 0, self.width*self.scale, self.height*self.scale)
		ctx.fill()
		if self.theme:
			self.theme['bg.svg'].render_cairo(ctx)
	

			

if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(GooglemapsScreenlet)

