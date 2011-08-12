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

# WidgetScreenlet (c) 2007 bu Helder Fraga aka Whise



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

myfile = 'WidgetScreenlet.py'

try:
	import webkit
except:
	if sys.argv[0].endswith(myfile):screenlets.show_error(None,"You need WebKit to run this Screenlet , please install it")
	else: print "You need WebKit to run this Screenlet , please install it"

#Check for internet connection required for web widgets

if sys.argv[0].endswith(myfile):# Makes Shure its not the manager running...
	#os.system('wget www.google.com -O/tmp/index.html &')
	a = commands.getoutput('wget www.google.com -O/tmp/index.html')
	if a.find('text/html') == -1:
		screenlets.show_error(None,"Internet connection is required to use this Screenlet")
		os.system('rm /tmp/index.html')
		sys.exit()
	os.system('rm /tmp/index.html')

class WidgetScreenlet (screenlets.Screenlet):
	"""Converted widgets to screenlets engine"""
	
	# default meta-info for Screenlets
	__name__		= 'WidgetScreenlet'
	__version__		= '0.3'
	__author__		= 'Helder Fraga aka Whise'
	__desc__		= __doc__

	started = False
	view = None
	box = None
	mypath = sys.argv[0][:sys.argv[0].find('WidgetScreenlet.py')].strip()
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
	set_width = 0
	set_height = 0
	def __init__ (self, **keyword_args):
		# init stuff
		screenlets.Screenlet.__init__(self, width=325, height=370,uses_theme=True, 
			is_widget=False, is_sticky=True,is_sizable=False, **keyword_args)


		self.add_options_group('Options', 'CPU-Graph specific options')
		self.add_option(BoolOption('Options', 'show_frame',
			self.show_frame, 'Show frame border', 'Show frame border arround the widget ...'))	
		self.add_option(ColorOption('Options','rgba_color', 
			self.rgba_color , 'Frame color', 'The color of the frame border'))
        	self.add_option(IntOption('Options', 'set_width', self.set_width, 'Width',  'Custom width', min=10, max=gtk.gdk.screen_width()))
        	self.add_option(IntOption('Options', 'set_height', self.set_height, 'Height', 'Custom height', min=10, max=gtk.gdk.screen_height()))
        	#self.add_option(IntOption('Options', 'border_width', self.border_width, 'Frame border width', 'The width of the frame border', min=1, max=8))
		self.disable_option('scale')
		self.theme_name = 'default'
		self.box = gtk.VBox(False, 0)
		self.view = webkit.WebView()
    		self.box.pack_start(self.view, False, False, 0)

		self.window.add(self.box)		
			
		self.window.show_all()
			


	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'border_width' or name == 'rgba_color' or name == 'show_frame':
			self.redraw_canvas()
		if name == 'set_width' and value  != self.widget_width:
			self.widget_width = value
			self.width = int(value)+30
			self.redraw_canvas()
		if name == 'set_height' and value != self.widget_height:
			self.widget_height = value
			self.height = int(value)+30	
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
					self.draw_rounded_rectangle(ctx,int((self.width - 64)),0,5,64,12)
			ctx.set_source_rgba(self.rgba_color[0], self.rgba_color[1], self.rgba_color[2], self.rgba_color[3])	
		
			
			if self.show_frame:
				self.draw_rounded_rectangle(ctx,0,0,5,self.width,self.height)
				ctx.set_source_rgba(1-self.rgba_color[0], 1-self.rgba_color[1], 1- self.rgba_color[2], 0.15)
				self.draw_rounded_rectangle(ctx,0,0,5,self.width,self.height,fill=False)
	
			if self.engine == 'google':		
				self.bgpb = gtk.gdk.pixbuf_new_from_file(self.mypath + 'icon.png').scale_simple(int(self.width),int(self.widget_height),gtk.gdk.INTERP_HYPER)
				self.bgpbim, self.bgpbms = self.bgpb.render_pixmap_and_mask(alpha_threshold=128)
			
				if not self.window.is_composited():
					#ctx.translate(0,10)
					self.draw_scaled_image(ctx,0,0,self.width,self.height,self.mypath + 'icon.png')

				self.view.shape_combine_mask(self.bgpbms,0,0)	
			else:
				self.bgpb = gtk.gdk.pixbuf_new_from_file(self.mypath + 'icon.png').scale_simple(int(self.widget_width),int(self.widget_height),gtk.gdk.INTERP_HYPER)
				self.bgpbim, self.bgpbms = self.bgpb.render_pixmap_and_mask(alpha_threshold=128)
			
				if not self.window.is_composited():
					ctx.translate(0,10)
					self.draw_image(ctx,0,0,self.mypath + 'icon.png')

				self.view.shape_combine_mask(self.bgpbms,8,8)	
 	


	def on_init(self):
		self.load_widget()
		self.add_default_menuitems(DefaultMenuItem.WINDOW_MENU | DefaultMenuItem.PROPERTIES |
			DefaultMenuItem.DELETE | DefaultMenuItem.QUIT | DefaultMenuItem.QUIT_ALL)
		if self.set_width == 0: self.set_width = int(self.widget_width)
		else:
			self.width = self.set_width + 30
			self.redraw_canvas()
			
		if self.set_height == 0: self.set_height = int(self.widget_height)
		else:
			self.height = self.set_height + 30
			self.redraw_canvas()
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
		self.view.load_uri(self.url)
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
		
			self.view.set_size_request(-1,int(self.widget_height))
		else:
			self.view.set_size_request(-1,int(self.height))
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
	screenlets.session.create_session(WidgetScreenlet)

