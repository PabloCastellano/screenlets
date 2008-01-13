#!/usr/bin/env python

#  TestScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - a testing-screenlet for experimental usage
# 
# TODO:
# - 

import screenlets
from screenlets.options import StringOption, AccountOption
import cairo
import gtk

class TestScreenlet (screenlets.Screenlet):
	"""A testing Screenlet"""
	
	# default meta-info for Screenlets
	__name__	= 'TestScreenlet'
	__version__	= '0.2'
	__author__	= 'RYX'
	__desc__	= 'A testbed for experimenting - only useful for developers.'

	# drag/drop constants
	DRAGDATA_TYPE_TEXT = 1
	DRAGDATA_TYPE_PIXMAP = 2
	DRAGDATA_TYPE_SCREENLET = 3
		
	# editable options
	test_text = ''
	pop3_account = ('user', 'pass')
	
	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=200, height=200, 
			drag_drop=True, **keyword_args)
		# set theme
		self.theme_name = "default"

		# add option group
		self.add_options_group('Example', 'This is an example of editable' +\
			' options within an options-group ...')
		# add editable option
		self.add_option(StringOption('Example', # group name
			'test_text', 						# attribute-name
			self.test_text,						# default-value
			'Test-Text', 						# widget-label
			'The Test-Text option for this Screenlet ...'	# description
			)) 
		# test of new account-option
		self.add_option(AccountOption('Example', 'pop3_account', 
			self.pop3_account, 'Username/Password', 
			'Enter username/password here ...'))
		# drag-test
		self.window.connect("drag-data-get", self.drag_data_get)
		self.window.drag_source_set(gtk.gdk.BUTTON1_MASK, [],
			#[("text/plain", 0, self.DRAGDATA_TYPE_TEXT ),
			#[("image/x-xpixmap", 0, self.DRAGDATA_TYPE_PIXMAP ),
			#("screenlet/test", 0, self.DRAGDATA_TYPE_SCREENLET)], 		# TEST
			gtk.gdk.ACTION_COPY)
		# set as text-source
		self.window.drag_source_add_text_targets()
		#self.window.drag_source_add_image_targets()
		#self.add_drag_type("text/plain", self.DRAGDATA_TYPE_TEXT)
		#self.add_drag_type("image/x-xpixmap", self.DRAGDATA_TYPE_PIXMAP)

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()


	def on_draw (self, ctx):
		# if theme is loaded
		if self.theme:
			# set scale rel. to scale-attribute
			ctx.scale(self.scale, self.scale)
			# render svg-file
			self.theme['example-bg.svg'].render_cairo(ctx)
			# render png-file
			#ctx.set_source_surface(self.theme['example-test.png'], 0, 0)
			#ctx.paint()
	
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)
	
	def on_realize (self):
		#self.create_drag_icon()
		pass
	
	def button_press (self, widget, event):
		if event.button == 1:
			print "PRESS"
		else:
			screenlets.Screenlet.button_press(self, widget, event)
	
	def on_create_drag_icon (self):
		"""Called when the drag-icon needs to be recreated. Should return
		a pixmap or None."""
		return None
	
	def on_drag (self, drag_context):
		"""Called when the screenlet starts getting dragged."""
		print "Screenlet.on_drag"
	
	def on_drag_end (self, drag_context):
		"""Called when the screenlet ends getting dragged."""
		print "Screenlet.on_drag_end"
	
	# info contains the id assigned to the target the data is requested for
	def on_drag_data_get (self, info, timestamp):
		"""Called when the drag-operation requests data."""
		print "Screenlet.on_drag_data_get"
		# return a string
		return "This is some DRAG-DATA ..."
		
	# --------------------- goes into Screenlet-class?
	
	__drag_icon = None
	__drag_icon_mask = None
	def create_drag_icon (self):
		"""Create drag_icon and drag_mask for drag-operation."""
		w = self.width
		h = self.height
		icon = self.on_create_drag_icon()
		if icon == None:
			# create icon
			self.__drag_icon = gtk.gdk.Pixmap(self.window.window, w, h)
			ctx = self.__drag_icon.cairo_create()
			self.clear_cairo_context(ctx)
			self.on_draw(ctx)
			# create mask
			self.__drag_icon_mask = gtk.gdk.Pixmap(self.window.window, w, h)
			ctx = self.__drag_icon_mask.cairo_create()
			self.clear_cairo_context(ctx)
			self.on_draw_shape(ctx)
		
	def drag_data_get (self, widget, drag_context, selection_data, info, 
		timestamp):
		# call user-defined callback to get data
		data = self.on_drag_data_get(info, timestamp)
		# TODO: decide between image and text
		selection_data.set_text(data)
		# test
		if info == self.DRAGDATA_TYPE_PIXMAP:
			print "IMAGE DATA."
			#selection_data.set_pixbuf(self.get_window_pixbuf())
		elif info == self.DRAGDATA_TYPE_TEXT:
			print "TEXT DATA."
			selection_data.set_text('TestScreenlet exported data ...')
		else:
			pass
	
	def drag_end(self, widget, drag_context):
		# call user-defined handler
		self.on_drag_end(drag_context)
	
	def drag_begin(self, widget, drag_context):
		# call user-defined handler
		self.on_drag(drag_context)
		# create icon
		self.create_drag_icon()
		print self.__drag_icon.get_depth()
		if self.__drag_icon and self.__drag_icon_mask:
			# WAY1: use the usual gtk.Widget-method (no hot_x, hot_y)
			self.window.drag_source_set_icon(self.window.get_colormap(), 
				self.__drag_icon, None)
			# WAY2: set pixbuf directly in context (no mask)
			"""w=self.width
			h=self.height
			pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h)
			pb.add_alpha(True, chr(0), chr(0), chr(0))
			pb.get_from_drawable(self.window.window,
				self.window.get_colormap(), 0, 0, 0, 0, w, h)
			drag_context.set_icon_pixbuf(pb, w/2, h/2)"""
			# WAY3: directly set pixmap in context (causes X-crash)
			"""drag_context.set_icon_pixmap(self.window.get_colormap(), 
				self.__drag_icon, self.__drag_icon_mask, self.width / 2, 
				self.height / 2)"""
			# WAY4: set the window iself as icon (destroys window after drag)
			"""drag_context.set_icon_widget(self.window, self.width / 2, 
				self.height / 2)"""
	
	# -------------------------------- maybe into screenlets.utils?
	
	def get_window_pixbuf(self, gtkwin, w, h):
		"""No alpha channel yet!!!"""
		pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h)
		#pb.add_alpha(True, chr(0), chr(0), chr(0))
		pb.get_from_drawable(gtkwin, gtkwin.get_colormap(), 
			0, 0, 0, 0, w, h)
		return pb
	
		
	
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(TestScreenlet)

