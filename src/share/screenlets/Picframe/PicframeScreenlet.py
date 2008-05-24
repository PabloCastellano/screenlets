#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  PicframeScreenlet (c) Whise aka Helder Fraga


import screenlets
from screenlets.options import ImageOption, IntOption, FloatOption, ColorOption,BoolOption
from screenlets import utils
import gtk
import cairo
import math
import urllib

class PicframeScreenlet (screenlets.Screenlet):
	"""A Screenlet that displays an image within a themeable frame. You can add new images by drag&amp;drop them
	into the screenlet's window area."""
	
	# --------------------------------------------------------------------------
	# meta-info, options
	# --------------------------------------------------------------------------
	
	__name__		= 'PicframeScreenlet'
	__version__		= '0.1'
	__author__		= 'Whise aka Helder Fraga'
	__desc__		= __doc__
	
	# attributes
	__image = None
	
	# editable options
	image_filename 	= ''
	image_scale		= 0.18
	image_offset_x	= 16
	image_offset_y	= 24
	curve = 15
	show_frame = False
	screen_width = gtk.gdk.screen_width() /10
	screen_height = gtk.gdk.screen_height()/10
	rotate = 0
	s_width = 300
	s_height = 200
	color_back = (0.5,0.5,0.5,0.7)
	# --------------------------------------------------------------------------
	# constructor and internals
	# --------------------------------------------------------------------------
	
	def __init__ (self, **keyword_args):
		# call super (and enable drag/drop)
		screenlets.Screenlet.__init__(self, width=500, height=400,
			uses_theme=True, drag_drop=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# initially apply default image (for newly created instances)
		#self.image_filename = screenlets.PATH + '/Picframe/dali.png'
		# add option group to properties-dialog
		self.add_options_group('Picframe', 'Picframe-related settings ...')
		# add editable options
		self.add_option(ImageOption('Picframe', 'image_filename', 
			self.image_filename, 'Filename',
			'Filename of image to be shown in this Picframe ...')) 
		#self.add_option(ColorOption('Picframe','color_back', 
		#	self.color_back, 'Frame color', ''))
		self.add_option(IntOption('Picframe','s_width', self.s_width,'Width','',min=20, max=2000,increment=10))
		self.add_option(IntOption('Picframe','s_height', self.s_height,'Height','',min=20, max=2000,increment=10)) 
		self.add_option(IntOption('Picframe','curve', 
			self.curve, 'Rounded corners angle', 
			'curve', min=0, max=45))
		self.add_option(BoolOption('Picframe','show_frame', 
			self.show_frame, 'Show Theme Frame ', 
			''))
		
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()
		self.width = self.s_width
		self.height = self.s_height
	def __setattr__ (self, name, value):
		if name == "image_filename":
			#print "SET IMAGEFILENAME"
			# set self.__image to new image, if value is set and != current
			ret = True
			if value != '' and value != self.image_filename:	# ok?
	
				screenlets.Screenlet.__setattr__(self, name, value)
			# update view

				self.redraw_canvas()


		elif name == 's_width':
			screenlets.Screenlet.__setattr__(self, name, value)
			self.width = value 
		elif name == 's_height':
			screenlets.Screenlet.__setattr__(self, name, value)
			self.height = value 
		else:
			# else, just call super
			screenlets.Screenlet.__setattr__(self, name, value)
		
	def set_image(self, filename):
		"""Set new image for this pictureframe (does NOT call redraw).
		TODO: support for more image-types (currently only png supported)"""
		# delete old image first
		
		self.image_filename = urllib.unquote(filename)
			
			#self.redraw_canvas()
		return True
		
		
	# --------------------------------------------------------------------------
	# Screenlet handlers
	# --------------------------------------------------------------------------
	
	def on_drag_enter (self, drag_context, x, y, timestamp):
		self.redraw_canvas()
	
	def on_drag_leave (self, drag_context, timestamp):
		self.redraw_canvas()
	
	def on_drop (self, x, y, sel_data, timestamp):
		print "Data dropped ..."
		filename = ''
		filename = utils.get_filename_on_drop(sel_data)[0]
		print filename
		if filename != '':
			#self.set_image(filename)
			self.image_filename = filename.replace(chr(34),'')
	
	def on_draw (self, ctx):
		ctx.set_operator(cairo.OPERATOR_OVER)
		ctx.scale(self.scale, self.scale)
		if self.theme:
			# if something is dragged over, lighten up the whole thing
			if self.dragging_over:
				ctx.set_operator(cairo.OPERATOR_XOR)

			ctx.set_source_rgba(0,0,0,0.2)
			self.draw_rounded_rectangle(ctx,0,0,self.curve,self.s_width,self.s_height)	
			ctx.translate(1,1)
			ctx.set_source_rgba(0,0,0,0.8)
			self.draw_rounded_rectangle(ctx,1,1,self.curve,self.s_width-4,self.s_height-4)
			ctx.translate(2,2)
			padding=0 # Padding from the edges of the window
	        	rounded=self.curve # How round to make the edges 20 is ok
	        	w = self.s_width-6
			h = self.s_height-6

	        	# Move to top corner
	        	ctx.move_to(0+padding+rounded, 0+padding)
	        	
	        	# Top right corner and round the edge
	        	ctx.line_to(w-padding-rounded, 0+padding)
	        	ctx.arc(w-padding-rounded, 0+padding+rounded, rounded, math.pi/2, 0)
	
	        	# Bottom right corner and round the edge
	        	ctx.line_to(w-padding, h-padding-rounded)
	        	ctx.arc(w-padding-rounded, h-padding-rounded, rounded, 0, math.pi/2)
	       	
	        	# Bottom left corner and round the edge.
	        	ctx.line_to(0+padding+rounded, h-padding)
	        	ctx.arc(0+padding+rounded, h-padding-rounded, rounded, math.pi+math.pi/2, math.pi)
		
	        	# Top left corner and round the edge
	        	ctx.line_to(0+padding, 0+padding+rounded)
	        	ctx.arc(0+padding+rounded, 0+padding+rounded, rounded, math.pi/2, 0)
        		
				#self.draw_scaled_image(ctx,self.image_filename,self.width,self.height)
			if self.image_filename != '': 
				
				self.image_filename = urllib.unquote(self.image_filename)
				try:
					pixbuf = gtk.gdk.pixbuf_new_from_file(self.image_filename).scale_simple(w,h,gtk.gdk.INTERP_HYPER)
				except:pass
				format = cairo.FORMAT_RGB24
				if pixbuf.get_has_alpha():
					format = cairo.FORMAT_ARGB32

				iw = pixbuf.get_width()
				ih = pixbuf.get_height()
				image = cairo.ImageSurface(format, iw, ih)

				

				#iw = float(image.get_width()) 
				#ih = float(image.get_height()) 

				matrix = cairo.Matrix(xx=iw/w, yy=ih/h)
				image = ctx.set_source_pixbuf(pixbuf, 0, 0)
				if image != None :image.set_matrix(matrix)
				
				#ctx.scale( min(((self.width-8)/iw),, ((self.height-8)/ih))
				
				#image = ctx.set_source_pixbuf(pixbuf, 0, 0)
			#except:pass
	        	# Fill in the shape.
			

			ctx.fill()
			#ctx.paint()

			image = None
			puxbuf = None
			if self.show_frame:
				ctx.translate(-2,-2)
				s = self.get_screenlet_dir() +  '/themes/' + self.theme_name + '/' + 'picframe-frame.svg'

			
				a = self.get_image_size(s)
				ctx.scale(float(self.width)/float(a[0]),float(self.height)/float(a[1]))
				self.theme.render(ctx, 'picframe-frame')
			# render glass
			#self.theme['picframe-glass.svg'].render_cairo(ctx)
			#self.theme.render(ctx, 'picframe-glass')

	def draw_scaled_image(self,ctx, pix, w, h):
		"""Draws a png or svg from specified path with a certain width and height"""

		ctx.save()
		
		if pix.lower().endswith('svg'):
			image = rsvg.Handle(pix)
			size=image.get_dimension_data()
			try:ctx.scale( w/size[0], h/size[1])
			except:pass
			image.render_cairo(ctx)
		elif pix.lower().endswith('png'):

			image = cairo.ImageSurface.create_from_png(pix)
			iw = float(image.get_width())
			ih = float(image.get_height())
			ctx.scale( w/iw, h/ih)
			ctx.set_source_surface(image, 0, 0)
			
		image = None
		ctx.restore()
	
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)

	
# If the program is run directly or passed as an argument to the python
# interpreter then launch as new application
if __name__ == "__main__":
	# create session object here, the rest is done automagically
	import screenlets.session
	screenlets.session.create_session(PicframeScreenlet)

