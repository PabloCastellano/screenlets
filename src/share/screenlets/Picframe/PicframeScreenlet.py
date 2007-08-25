#!/usr/bin/env python

#  PicframeScreenlet (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - a picture frame screenlet
# 
# TODO:
# - rotate-function for vertical images
# - implement "drag-out" functionality for dragging images out of the screenlet
# - support more image types (use gtk.Image or gtk.Pixmap??)
# - add history-list and maybe keys to switch fore/back
# - ??use four corners and four edges instead of one frame-image to have
#   a dynamically sizeable border (this one would be much nicer in html :) ..)
# - ...

import screenlets
from screenlets.options import ImageOption, IntOption, FloatOption

import cairo


class PicframeScreenlet (screenlets.Screenlet):
	"""A Screenlet that displays an image within a themeable frame. Currently
	this only displays PNG-images. You can add new images by drag&amp;drop them
	into the screenlet's window area."""
	
	# --------------------------------------------------------------------------
	# meta-info, options
	# --------------------------------------------------------------------------
	
	__name__		= 'PicframeScreenlet'
	__version__		= '0.5'
	__author__		= 'RYX (Rico Pfaus) 2007'
	__desc__		= __doc__
	
	# attributes
	__image = None
	
	# editable options
	image_filename 	= ''
	image_scale		= 0.18
	image_offset_x	= 16
	image_offset_y	= 24
	
	# --------------------------------------------------------------------------
	# constructor and internals
	# --------------------------------------------------------------------------
	
	def __init__ (self, **keyword_args):
		# call super (and enable drag/drop)
		screenlets.Screenlet.__init__(self, width=100, height=100,
			uses_theme=True, drag_drop=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# initially apply default image (for newly created instances)
		#self.image_filename = screenlets.PATH + '/Picframe/dali.png'
		# add default menuitems (all the standard ones)
		self.add_default_menuitems()
		# add option group to properties-dialog
		group = self.create_option_group('Picframe', 'Picframe settings.')
		# add editable options
		group.add_option(ImageOption('image_filename', self.image_filename, 
			'Image', 'Image to be shown in this Picframe ...')) 
		group.add_option(FloatOption('image_scale', self.image_scale, 
			'Image Scale', 'Scale of image within this Picframe ...', 
			min=0.01, max=10.0, digits=2, increment=0.01))
		group.add_option(IntOption('image_offset_x', self.image_offset_x, 
			'Image Offset X', 'X-offset of upper left corner of the image '+\
			'within this Picframe ...', min=0, max=self.width))
		group.add_option(IntOption('image_offset_y', self.image_offset_y, 
			'Image Offset Y', 'Y-offset of upper left corner of the image ' +\
			'within this Picframe ...', min=0, max=self.height))
		
	def __setattr__ (self, name, value):
		if name == "image_filename":
			#print "SET IMAGEFILENAME"
			# set self.__image to new image, if value is set and != current
			ret = True
			if value != '' and value != self.image_filename:	# ok?
				ret = self.set_image(value)
			# call super (if image has been successfully applied)
			if ret != False:
				screenlets.Screenlet.__setattr__(self, name, value)
			# update view
			self.redraw_canvas()
			#self.update_shape()
		elif name in ('image_scale', 'image_offset_x', 'image_offset_y'):
			# update view
			screenlets.Screenlet.__setattr__(self, name, value)
			self.redraw_canvas()
		else:
			# else, just call super
			screenlets.Screenlet.__setattr__(self, name, value)
		
	def set_image(self, filename):
		"""Set new image for this pictureframe (does NOT call redraw).
		TODO: support for more image-types (currently only png supported)"""
		# delete old image first
		print "Setting new image for PicframeScreenlet: %s" % filename
		if self.__image:
			self.__image.finish()
			del self.__image
		# and recreate image
		try:
			img = cairo.ImageSurface.create_from_png(filename)
			if img:
				self.__image = img
			#self.redraw_canvas()
			return True
		except Exception, ex:
			screenlets.show_error(self, 
				'Failed to load image "%s": %s (only PNG images supported yet)' % (filename, ex))
		return False
		
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
		# get text-elements in selection data
		txt = sel_data.get_text()
		if txt:
			if txt[-1] == '\n':
				txt = txt[:-1]
			txt.replace('\n', '\\n')
			# if it is a filename, use it
			if txt.startswith('file://'):
				filename = txt[7:]
			else:
				screenlets.show_error(self, 'Invalid string: %s.' % txt)
		else:
			# else get uri-part of selection
			uris = sel_data.get_uris()
			if uris and len(uris)>0:
				#print "URIS: "+str(uris	)
				filename = uris[0][7:]
		if filename != '':
			#self.set_image(filename)
			self.image_filename = filename
	
	def on_draw (self, ctx):
		ctx.set_operator(cairo.OPERATOR_OVER)
		ctx.scale(self.scale, self.scale)
		if self.theme:
			# if something is dragged over, lighten up the whole thing
			if self.dragging_over:
				ctx.set_operator(cairo.OPERATOR_XOR)
			# render bg
			#self.theme['picframe-bg.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'picframe-bg')
			# render image if set
			if self.__image != None:
				ctx.save()
				ctx.translate(self.image_offset_x, self.image_offset_y)
				ctx.scale(self.image_scale, self.image_scale)
				ctx.set_source_surface(self.__image, 0, 0)
				ctx.paint()
				ctx.restore()
			# render frame
			#self.theme['picframe-frame.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'picframe-frame')
			# render glass
			#self.theme['picframe-glass.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'picframe-glass')
	
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)

	
# If the program is run directly or passed as an argument to the python
# interpreter then launch as new application
if __name__ == "__main__":
	# create session object here, the rest is done automagically
	import screenlets.session
	screenlets.session.create_session(PicframeScreenlet)

