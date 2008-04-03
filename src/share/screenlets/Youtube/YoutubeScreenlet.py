#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# YoutubeScreenlet (c) 2007 bu Helder Fraga aka Whise



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
myfile = 'YoutubeScreenlet.py'
mypath = sys.argv[0][:sys.argv[0].find(myfile)].strip()

if sys.argv[0].endswith(myfile): # Makes Shure its not the manager running...
		# First workarround
		c = None
		workarround =  sys.argv[0] + " &"
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
			if workarround == sys.argv[0] + " &":
				print 'No workarround will be applied to your sistem , this screenlet will probably not work properly'
			os.system (workarround)
			fileObj = open("/tmp/"+ myfile+"running","w") #// open for for write
			fileObj.write('gtkmozembed bug workarround')
		
			fileObj.close()
			sys.exit()


else:
	pass
try:
	import gtkmozembed
except:
	screenlets.show_error(None,"You need Gtkmozembed to run this Screenlet , please install it")
#########WORKARROUND FOR GTKOZEMBED BUG BY WHISE################
#Check for internet connection required for web widgets

if sys.argv[0].endswith(myfile):# Makes Shure its not the manager running...
	#os.system('wget www.google.com -O/tmp/index.html &')
	a = commands.getoutput('wget www.google.com -O/tmp/index.html')
	if a.find('text/html') == -1:
		screenlets.show_error(None,"Internet connection is required to use this Screenlet")
		os.system('rm /tmp/index.html')
		sys.exit()
	os.system('rm /tmp/index.html')

class YoutubeScreenlet (screenlets.Screenlet):
	"""Converted widgets to screenlets engine"""
	
	# default meta-info for Screenlets
	__name__		= 'YoutubeScreenlet'
	__version__		= '0.3'
	__author__		= 'Helder Fraga aka Whise'
	__desc__		= __doc__

	started = False
	moz = None
	box = None
	mypath = sys.argv[0][:sys.argv[0].find('YoutubeScreenlet.py')].strip()
	url = mypath + 'index.html'
	color_back = 0.3,0.3,0.3,0.7
	rgba_color = (1,1,1,0.2)
	border_width = 8
	show_frame = True
	widget_width = 300
	widget_height = 330
	engine = ''

	width = 325
	height = 370
	def __init__ (self, **keyword_args):
		# init stuff
		screenlets.Screenlet.__init__(self, width=325, height=370,uses_theme=True, 
			is_widget=False, is_sticky=True, **keyword_args)


		self.add_options_group('Options', 'CPU-Graph specific options')
		self.add_option(BoolOption('Options', 'show_frame',
			self.show_frame, 'Show frame border', 'Show frame border arround the widget ...'))	
		self.add_option(ColorOption('Options','rgba_color', 
			self.rgba_color , 'Frame color', 'The color of the frame border'))
        	#self.add_option(IntOption('Options', 'border_width', self.border_width, 'Frame border width', 'The width of the frame border', min=1, max=8))
		self.disable_option('scale')
		self.theme_name = 'default'
		self.box = gtk.VBox(False, 0)
		if hasattr(gtkmozembed, 'set_profile_path'):
			gtkmozembed.set_profile_path(self.mypath,'mozilla')
		else:
			gtkmozembed.gtk_moz_embed_set_profile_path(self.mypath ,'mozilla')
		self.moz = gtkmozembed.MozEmbed()
    		self.box.pack_start(self.moz, False, False, 0)

		self.window.add(self.box)		
			
		self.window.show_all()
			


	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'border_width' or name == 'rgba_color' or name == 'show_frame':
			self.redraw_canvas()
			



	def on_focus (self, event):
		"""Called when the Screenlet's window receives focus."""
		self.redraw_canvas()

	def on_unfocus (self, event):
		"""Called when the Screenlet's window receives focus."""
		self.redraw_canvas()

	def on_draw (self, ctx):


		ctx.scale(self.scale , self.scale )
		ctx.set_operator(cairo.OPERATOR_OVER)

		ctx.set_source_rgba(0, 0, 0, 0)
 		
		bgcolor = self.box.get_style().bg[gtk.STATE_NORMAL]

		r = bgcolor.red/65535.0
		g = bgcolor.green/65535.0
		b = bgcolor.blue/65535.0
		ctx.set_source_rgba(r, g, b, 1)	
	
		if self.theme and self.window:
			ctx.set_source_rgba(self.color_back[0],self.color_back[1],self.color_back[2],self.color_back[3])
			if self.has_focus == True:
				if not self.show_frame:
					self.theme.draw_rounded_rectangle(ctx,int((self.width - 64)),0,5,64,12)
			ctx.set_source_rgba(self.rgba_color[0], self.rgba_color[1], self.rgba_color[2], self.rgba_color[3])	
		
			
			if self.show_frame:
				self.theme.draw_rounded_rectangle(ctx,0,0,5,self.width,self.height)
				ctx.set_source_rgba(1-self.rgba_color[0], 1-self.rgba_color[1], 1- self.rgba_color[2], 0.15)
				self.theme.draw_rounded_rectangle(ctx,0,0,5,self.width,self.height,fill=False)
	
			if self.engine == 'google':		
				self.bgpb = gtk.gdk.pixbuf_new_from_file(self.mypath + 'icon.png').scale_simple(int(self.width),int(self.widget_height),gtk.gdk.INTERP_HYPER)
				self.bgpbim, self.bgpbms = self.bgpb.render_pixmap_and_mask(alpha_threshold=128)
			
				if not self.window.is_composited():
					#ctx.translate(0,10)
					self.theme.draw_scaled_image(ctx,0,0,self.width,self.height,self.mypath + 'icon.png')

				self.moz.shape_combine_mask(self.bgpbms,0,0)	
			else:
				self.bgpb = gtk.gdk.pixbuf_new_from_file(self.mypath + 'icon.png').scale_simple(int(self.widget_width),int(self.widget_height),gtk.gdk.INTERP_HYPER)
				self.bgpbim, self.bgpbms = self.bgpb.render_pixmap_and_mask(alpha_threshold=128)
			
				if not self.window.is_composited():
					ctx.translate(0,10)
					self.theme.draw_image(ctx,0,0,self.mypath + 'icon.png')

				self.moz.shape_combine_mask(self.bgpbms,8,8)	
 	


	def on_init(self):
		self.load_widget()
		self.add_default_menuitems(DefaultMenuItem.WINDOW_MENU | DefaultMenuItem.PROPERTIES |
			DefaultMenuItem.DELETE)

	def load_widget(self):

		self.widget  = open(self.url,'r')
		self.widget_info = self.widget.read()
		self.widget_info = self.widget_info.replace('width=' +chr(34) + '100%','')


		if self.widget_info.find("width=" + chr(34)) != -1:
		# Search for width="
			self.widget_width = self.widget_info[self.widget_info.find("width=" + chr(34)):]
			self.widget_width = self.widget_width[7:]
			self.widget_width = self.widget_width[:self.widget_width.find(chr(34)) ].strip()
			self.widget_height = self.widget_info[self.widget_info.find("height=" + chr(34)):]
			self.widget_height = self.widget_height[8:]
			self.widget_height = self.widget_height[:self.widget_height.find(chr(34)) ].strip()

		
		elif self.widget_info.find("width=") != -1:
		# Search for width=
			self.widget_width = self.widget_info[self.widget_info.find("width="):]
			self.widget_width = self.widget_width[6:]
	
			self.widget_width = self.widget_width[:self.widget_width.find('&') ].strip()
				

			# widget height for scaling porpuse ( the height of the html frame)
			self.widget_height = self.widget_info[self.widget_info.find("height=" ):]
			self.widget_height = self.widget_height[7:]
			self.widget_height = self.widget_height[:self.widget_height.find('&') ].strip()
		elif self.widget_info.find("w=") != -1:
		# Search for w=
			self.widget_width = self.widget_info[self.widget_info.find("w="):]
			self.widget_width = self.widget_width[2:]
			self.widget_width = self.widget_width[:self.widget_width.find('&') ].strip()
			self.widget_height = self.widget_info[self.widget_info.find("h=" ):]
			self.widget_height = self.widget_height[2:]
			self.widget_height = self.widget_height[:self.widget_height.find('&') ].strip()
		
		self.widget_width = str(self.widget_width).replace('px','') 
		self.widget_height = str(self.widget_height).replace('px','') 

		self.widget.close()


		if self.widget_info.startswith('<script src='):
			self.url = self.widget_info[13:][:(len(self.widget_info)-24)]
			
			self.engine = 'google'
		self.moz.load_url(self.url)
		print 'loading ' + self.url
		
		self.width = int(self.widget_width)+30
		self.height = int(self.widget_height)+30
		#print self.width,self.height
		#print self.widget_width, self.widget_height
		#	self.width = 325
		#	self.height = 370
		self.box.set_border_width(7)
		if self.engine == 'google':
			#self.box.set_border_width(10)

			self.box.set_uposition(-1,7)
		
			self.moz.set_size_request(-1,int(self.widget_height))
		else:
			self.moz.set_size_request(-1,int(self.height))
		self.redraw_canvas()

	def on_mouse_down(self,event):
		pass
	def on_draw_shape (self, ctx):
		if self.theme:
			ctx.scale(1, 1)
			ctx.set_operator(cairo.OPERATOR_OVER)

			ctx.set_source_rgba(0, 0, 0, 1)
			#a = self.window.get_size()
	 		
	 		ctx.rectangle(0, 0, self.width,self.height)
			
			ctx.fill()
		
		
			


	

			

if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(YoutubeScreenlet)

