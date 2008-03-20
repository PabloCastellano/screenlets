#!/usr/bin/env python

# WidgetScreenlet (c) 2007 bu Helder Fraga aka Whise



import screenlets
from screenlets import DefaultMenuItem
from screenlets.options import BoolOption, StringOption, IntOption, ColorOption
import cairo
import gtk
import gobject
import commands
import sys
import os


#########WORKARROUND FOR GTKOZEMBED BUG BY WHISE################
myfile = 'WidgetScreenlet.py'
if sys.argv[0].endswith(myfile): # Makes Shure its not the manager running...
	
	if str(commands.getoutput("cat /etc/issue")).lower().find('ubuntu') != -1:
		mypath = sys.argv[0][:sys.argv[0].find(myfile)].strip()
		if os.path.isfile("/tmp/"+ myfile+"running"):
			os.system("rm -f " + "/tmp/"+ myfile+"running")
		
		else:
			os.system ("export LD_LIBRARY_PATH=/usr/lib/firefox \n export MOZILLA_FIVE_HOME=/usr/lib/firefox \n python "+ sys.argv[0] + " &")
			fileObj = open("/tmp/"+ myfile+"running","w") #// open for for write
			fileObj.write('gtkmozembed bug workarround')
		
			fileObj.close()
			exit()
	elif str(commands.getoutput("cat /etc/issue")).lower().find('suse') != -1:
		mypath = sys.argv[0][:sys.argv[0].find(myfile)].strip()
		if os.path.isfile("/tmp/"+ myfile+"running"):
			os.system("rm -f " + "/tmp/"+ myfile+"running")
		
		else:
			print 'Your running suse , make shure you have seamonkey installed'
			os.system ("export LD_LIBRARY_PATH=/usr/lib/seamonkey \n python "+ sys.argv[0] + " &")
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
#Check for internet connection required for web widgets

if sys.argv[0].endswith(myfile):# Makes Shure its not the manager running...
	#os.system('wget www.google.com -O/tmp/index.html &')
	a = commands.getoutput('wget www.google.com -O/tmp/index.html')
	if a.find('text/html') == -1:
		screenlets.show_error(None,"Internet connection is required to use this Screenlet")
		os.system('rm /tmp/index.html')
		exit()
	os.system('rm /tmp/index.html')

class WidgetScreenlet (screenlets.Screenlet):
	"""Puts any Web Widget in your desktop , just go on www.springwidgets.com or www.yourminis.com ,and copy the embedded html code into a html in the widgets directory"""
	
	# default meta-info for Screenlets
	__name__		= 'WidgetScreenlet'
	__version__		= '0.2'
	__author__		= 'Helder Fraga aka Whise'
	__desc__		= __doc__

	started = False
	box = None
	fh = None
	fh1 = None
	fh2 = None
	x_ratio = y_ratio = 1
	moz1 = None
	box = gtk.VBox(False, 0)
	mypath = sys.argv[0][:sys.argv[0].find('WidgetScreenlet.py')].strip()
	bitmap_width = 0
	bitmap_height = 0
	url = mypath + 'index.html'
	color_back = 0.3,0.3,0.3,0.7
	rgba_color = (1,1,1,0.2)
	widget  = open(url)
	widget_info = widget.read()
	widget.close()
	# widget width for scaling porpuse ( the width of the html frame)
	widget_width = widget_info[widget_info.find("width=" + chr(34)):]
	widget_width = widget_width[7:]
	border = 10
	widget_width = widget_width[:widget_width.find(chr(34)) ].strip()


	# widget height for scaling porpuse ( the height of the html frame)
	widget_height = widget_info[widget_info.find("height=" + chr(34)):]
	widget_height = widget_height[8:]
	widget_height = widget_height[:widget_height.find(chr(34)) ].strip()

	try:
		width =int(widget_width) +45
		height = int(widget_height )+ 120
	except:
		width = 325
		height = 370
	def __init__ (self, **keyword_args):
		# init stuff
		screenlets.Screenlet.__init__(self, width=int(self.width*self.scale), height=int(self.height*self.scale),uses_theme=True, 
			is_widget=False, is_sticky=True, **keyword_args)



		self.disable_option('scale')
	        self.x_ratio =  float(self.width) / 325
        	self.y_ratio =  float(self.height) / 370
		#self.disable_option('scale')
		# create container for our moz-widget
		self.theme_name = "default"
		# Rescale widget to our desired size
		self.fh = open(str(self.mypath)+ 'index.html', 'r')
		self.fh1 = self.fh.read()
		self.fh.close()
		try:
			self.fh1 = self.fh1.replace(str(self.widget_width) ,str(int(int(self.widget_width)*self.scale)))
			self.fh1 = self.fh1.replace(str(self.widget_height),str(int(int(self.widget_height)*self.scale)))
		except:
			pass
		fh2 = open(str(self.mypath)+'widget_scaled.html', 'w')
		fh2.write(self.fh1)
		fh2.close()

		self.box = gtk.VBox(False, 0)
		if self.box != None:
			
			self.box.set_border_width(int(15*self.scale))

			# create evntbox
		
			self.box.set_size_request(int(10*self.scale),int((self.height-77)*(self.scale)-(self.scale*5)))
			self.moz1 = gtkmozembed.MozEmbed()
			self.moz1.set_size_request(int(10*self.scale),int((self.height-77)*(self.scale)-(self.scale*5)))
			
			
		
		# add/show all inputs
		
	

    			self.box.pack_start(self.moz1, False, False, 0)
			self.box.set_uposition(1,0)
			self.window.add(self.box)		
			
			self.window.show_all()
			


	#def moz_button_press (self, widget, event):
		
		#print "Button press inside Mozilla Widget"

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'border':
			self.redraw_canvas()
			

#		if name == 'scale': 		self.scale_moz()
	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id[:4] == "add:":
			self.url =  mypath + 'widgets/'+ id[4:]

			self.on_scale()
		if id[:5] == "open:" :
			# TODO: use DBus-call for this
			self.url = id[5:]
			self.box.set_size_request(int(1*self.scale),int((self.height-237)*(self.scale)-(self.scale*5)))
			self.moz1.load_url(str(self.url))
	def on_focus (self, event):
		"""Called when the Screenlet's window receives focus."""
		self.redraw_canvas()

	def on_unfocus (self, event):
		"""Called when the Screenlet's window receives focus."""
		self.redraw_canvas()

	def on_draw (self, ctx):

		if self.x_ratio == 0 : self.x_ratio = 1
		ctx.scale(self.scale * self.x_ratio, self.scale * self.y_ratio)
		ctx.set_operator(cairo.OPERATOR_OVER)

		ctx.set_source_rgba(0, 0, 0, 0)
 		#ctx.rectangle(0, 0, self.width, self.height)
		#ctx.fill()
		bgcolor = self.box.get_style().bg[gtk.STATE_NORMAL]
#				ebox.set_size_request(1,1)
				#ebox.set_uposition(11111,211116)
				
#				self.update_shape()
		r = bgcolor.red/65535.0
		g = bgcolor.green/65535.0
		b = bgcolor.blue/65535.0
		ctx.set_source_rgba(r, g, b, 1)		
		if self.theme and self.window:
			ctx.set_source_rgba(self.color_back[0],self.color_back[1],self.color_back[2],self.color_back[3])
			if self.has_focus == True:self.theme.draw_rounded_rectangle(ctx,int((self.width - 64)/self.x_ratio),0,5,int(64/self.x_ratio),12)
			ctx.set_source_rgba(self.rgba_color[0], self.rgba_color[1], self.rgba_color[2], self.rgba_color[3])	
			#a = (5+self.border)*self.x_ratio
			
			self.theme.draw_rounded_rectangle(ctx,15,15,5,298,283)
	
		
			self.bgpb = gtk.gdk.pixbuf_new_from_file(self.mypath + 'icon.png').scale_simple(int(self.widget_width),int(self.widget_height),gtk.gdk.INTERP_HYPER)
			self.bgpbim, self.bgpbms = self.bgpb.render_pixmap_and_mask(alpha_threshold=128)
			
			if not self.window.is_composited():
				ctx.translate(0,10)
				self.theme.draw_image(ctx,0,0,self.mypath + 'icon.png')
			self.moz1.shape_combine_mask(self.bgpbms,8,8)	
	
 	


	def on_init(self):
		self.scale= 1
		self.add_default_menuitems(DefaultMenuItem.WINDOW_MENU | DefaultMenuItem.PROPERTIES |
			DefaultMenuItem.DELETE)
	def scale_moz(self):

		self.widget  = open(self.url,'r')
		self.widget_info = self.widget.read()
		self.fh1 = self.widget_info
		self.widget_info = self.widget_info.replace('width=' +chr(34) + '100%','')
		if len(self.widget_info[self.widget_info.find("width=" + chr(34)):]) != 0:
	# widget width for scaling porpuse ( the width of the html frame)
			self.widget_width = self.widget_info[self.widget_info.find("width=" + chr(34)):]
			self.widget_width = self.widget_width[7:]
	
			self.widget_width = self.widget_width[:self.widget_width.find(chr(34)) ].strip()
			self.widget_width = self.widget_width.replace('px','') 
		



		# widget height for scaling porpuse ( the height of the html frame)
			self.widget_height = self.widget_info[self.widget_info.find("height=" + chr(34)):]
			self.widget_height = self.widget_height[8:]
			self.widget_height = self.widget_height[:self.widget_height.find(chr(34)) ].strip()
			self.widget_height = self.widget_height.replace('px','') 
		
		else:
			if len(self.widget_info[self.widget_info.find("width="):]) != 0:
				self.widget_width = self.widget_info[self.widget_info.find("width="):]
				self.widget_width = self.widget_width[6:]
	
				self.widget_width = self.widget_width[:self.widget_width.find('&') ].strip()
				

		# widget height for scaling porpuse ( the height of the html frame)
				self.widget_height = self.widget_info[self.widget_info.find("height=" ):]
				self.widget_height = self.widget_height[7:]
				self.widget_height = self.widget_height[:self.widget_height.find('&') ].strip()

		self.fh1 = self.widget_info
		self.widget.close()
		try:
			self.fh1 = self.fh1.replace(str(self.widget_width) ,str(int(int(self.widget_width)*self.scale)))
			self.fh1 = self.fh1.replace(str(self.widget_height),str(int(int(self.widget_height)*self.scale)))
		except:
			pass
		fh2 = open(str(self.mypath)+'widget_scaled.html', 'w')
		fh2.write(self.fh1)
		fh2.close()
		self.moz1.load_url( str(self.mypath)+'widget_scaled.html')

		try:
			self.width =int(int(self.widget_width)*self.scale) + int(45*self.scale)
			self.height = int(int(self.widget_height)*self.scale)+ int(120*self.scale)
		except:
			self.width = 325
			self.height = 370
		if self.window:
			self.box.set_border_width(int(15*self.scale))
			self.box.set_uposition(int(1*self.scale),int(0*self.scale+(self.scale*5)))
			self.moz1.set_size_request(int(1*self.scale),int(self.height)-(77*self.scale)-(self.scale*5))
	        self.x_ratio =  float(self.width) / (325*self.scale)
	       	self.y_ratio =  float(self.height) / (370*self.scale)


	def on_scale(self):
		
		


		self.scale_moz()
		self.redraw_canvas()
	def on_mouse_down(self,event):
		pass
	def on_draw_shape (self, ctx):
		if self.theme:
			ctx.scale(1, 1)
			ctx.set_operator(cairo.OPERATOR_OVER)

			ctx.set_source_rgba(0, 0, 0, 1)
			a = self.window.get_size()
	 		ctx.rectangle(0, 0, a[0],a[1])
			print a[0],a[1]
			ctx.fill()
		
		
			


	

			

if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(WidgetScreenlet)

