#!/usr/bin/env python

#  CopyStackScreenlet (c) RYX 2007 <ryx [at] ryxperience [dot] com>
#
# INFO:
# - a graphical Clipboard tool
# 
# TODO:
# - only increase window size on certain steps (not on each add_element) 
# - ImageElement, DirectoryElement, ...
# - fix spacing- and positioning-bugs
# - maximum length of list ("height" of stack)
# - drag from the Screenlets area
# - two different modes: cut-mode and copy-mode (when dragging things off
#   the screenlet), switch using mouseweel and/or key-combo
# - random variation of element placement
# - rollover-images for ImageElement
# - save elements somewhere (needs more complex storage-type, maybe XMLOption)
# - more checks on data to verify different types (maybe check for mimetype?)
# - if topmost element is deleted, the next element should be copied onto
#   the current gtk.Clipboard (so it can be inserted using Ctrl+C)
#

import screenlets
from screenlets.options import IntOption

import gtk, gobject
import cairo, pango


class CopyStackScreenlet (screenlets.Screenlet):
	"""A Screenlet that serves as Clipboard-manager and displays a stack with 
	a history of your copy/paste actions."""
	
	__name__	= 'CopyStackScreenlet'
	__version__	= '0.1'
	__author__	= 'RYX (Rico Pfaus)'
	__desc__	= __doc__
	
	theme_height		= 30	# TODO: auto-set from theme whenever it changes
	selected_element	= None	# the selected element
	selected_index		= -1	# index of the selected element (or -1)
	tooltip				= None
	mouse_inside		= False
	
	# editable options
	element_spacing	= 8
	
	# constructor
	def __init__ (self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=100, height=30, 
			uses_theme=True, drag_drop=True, **keyword_args)
		# init props
		self.elements		= []
		# set attributes
		self.theme_name	= "default"
		# add menuitems
		self.add_menuitem('element_delete', 'Delete Element')
		# and append efault items
		self.add_default_menuitems()
		# add options
		#group_cs = OptionsGroup('CopyStack', 'CopyStack-related settings ...')
		#self.add_options_group(group_cs)
		self.add_options_group('CopyStack', 'CopyStack-related settings ...')
		self.add_option(IntOption('CopyStack', 'element_spacing', 
			self.element_spacing, 'Element Spacing', 
			'The vertical space between element-symbols on the stack ...',
			min=5, max=30))
		#self.add_option(ListOption('CopyStack', 'elements', self.elements,
		#	'Element-List', 'A list with elements on the stack ...'))
		#self.window.connect('motion-notify-event', self.on_mouse_move)
		gobject.timeout_add(50, self.engine)
		# init our self-made tooltip window
		self.tooltip = Tooltip(250, 30)
		# init clipboard
		self.clipboard	= gtk.Clipboard()
		self.clipboard.connect('owner-change', self.clipboard_owner_change)
	
	def __setattr__ (self, name, value):
		if name == 'elements':
			self.__dict__[name] = value
			# calculate height difference and set new height
			#diff = self.height - (len(value)* self.element_spacing)
			self.height = len(value) * self.element_spacing +\
				self.theme_height
			print value
			# add offset to y-position
			#self.y -= diff * self.element_spacing
			screenlets.Screenlet.__setattr__(self, name, value)
		else:
			screenlets.Screenlet.__setattr__(self, name, value)
			if name == 'element_spacing':
				self.redraw_canvas()
				self.update_shape()	
		
	# "public" functions
	
	def add_element (self, element):
		"""Add a new element to this stack (if different from topmost)."""
		if not self.topmost_element() or \
			self.topmost_element().data != element.data:
			self.elements.append(element)
			self.elements = self.elements		# causes save/redraw
			self.y -= int(self.element_spacing * self.scale)
			return True
		return False
	
	def add_element_from_clipboard (self, clipboard):
		"""Tries to add the current clipboard contents as new data."""
		# currently we only check for text and images
		if clipboard.wait_is_text_available():
			self.add_element_from_data(clipboard.wait_for_text())
		elif clipboard.wait_is_image_available():
			self.add_element_from_data(clipboard.wait_for_image())
	
	def add_element_from_data (self, data):
		"""Add an element from a string/unicode/list/tuple/object with data."""
		obj = None
		if isinstance(data, (str, unicode)):
			#data = data.replace('<', '&lt;')
			#data = data.replace('>', '&gt;')
			data = data.replace('&', '&amp;')
			# url?
			if data.startswith('http://'):
				obj = UrlElement(data, data)
			# file?
			elif data.startswith('file://'):
				# TODO: check if file or dir!!!
				obj = FileElement(data, data)
			else:
				# at least its text!
				obj = TextElement(data[:50] + ' ...', data)
		if obj:
			self.add_element(obj)
			return True
		return False
	
	def delete_selected_element (self):
		"""Deletes the currently selected (hovered) element."""
		if self.selected_element != None:
			del self.elements[self.selected_index-1]
			self.selected_index		= -1
			self.selected_element	= None
			self.elements			= self.elements	# redraw	
			return True
		return False
	
	def get_element_at_pixel (self, x, y):
		"""Return the element at the given x/y-position (or None if no elements
		are available)."""
		id = self.get_index_at_pixel(x, y)
		if len(self.elements) == 0:
			return None
		else:
			return self.elements[id-1]
	
	def get_element_by_index (self, id):
		""""Return an element by its index."""
		self.elements[id-1]
	
	def get_index_at_pixel (self, x, y):
		"""Return the index of the element at the given x/y-position."""
		if len(self.elements) == 0:
			return 0
		else:
			elnum = len(self.elements)
			eh = (self.height - self.theme_height) / elnum
			id = elnum - int((y - self.theme_height + eh) / eh)
			if id < elnum:
				return id
			else:
				return elnum
	
	def show_tooltip (self):
		"""Show tooltip window at current element's position. Does nothing
		if no element is selected ..."""
		if self.selected_element:
			self.tooltip.text	= self.selected_element.desc
			self.tooltip.y		= self.y + (self.element_spacing * \
					(len(self.elements) - self.selected_index)) + \
					self.tooltip.height / 2 + self.element_spacing / 2
			self.tooltip.x		= self.x + self.width
			self.tooltip.show_delayed(300)
	
	def topmost_element (self):
		"""Return reference to topmost element (or None if stack is empty)."""
		if len(self.elements) == 0:
			return None
		else:
			return self.elements[-1]
	
	# gtk signal-handlers and drawing engine
	
	def clipboard_owner_change (self, clipboard, event):
		self.add_element_from_clipboard(clipboard)
	
	def engine (self):
		if self.mouse_inside:
			p = self.window.get_pointer()
			id = self.get_index_at_pixel(p[0], p[1])
			if id > 0:
				el = self.elements[id-1]
				if el != self.selected_element:
					self.selected_element = el
					self.selected_index = id
					self.redraw_canvas()
					# show tooltip
					self.show_tooltip()
		return True
	
	# screenlet event-handlers
	
	def on_init (self):
		# add element if something is in the current clipboard
		self.add_element_from_clipboard(gtk.clipboard_get())
	
	def on_menuitem_select (self, id):
		if id == 'element_delete':
			self.delete_selected_element()
	
	def on_mouse_down (self, event):
		self.tooltip.hide()
		if event.button == 1:
			print self.get_element_at_pixel(event.x, event.y)
			return True
		else:
			return screenlets.Screenlet.on_mouse_down(self, event)
	
	def on_mouse_enter (self, event):
		self.mouse_inside = True
		self.redraw_canvas()
		self.show_tooltip()
		
	def on_mouse_leave (self, event):
		self.mouse_inside = False
		self.tooltip.hide()
		self.redraw_canvas()
	
	def on_drag_enter (self, drag_context, x, y, timestamp):
		self.redraw_canvas()
	
	def on_drag_leave (self, drag_context, timestamp):
		self.redraw_canvas()
	
	def on_drop (self, x, y, sel_data, timestamp):
		print "Data dropped ..."
		txt = sel_data.get_text()
		if txt:
			print "TEXT: "+txt
			if txt[-1] == '\n':
				txt = txt[:-1]
				txt.replace('\n', '\\n')
			#self.texts.append(txt)		# DOES NOT CALL __SETATTR__ !!!
			#self.texts = self.texts		# so we need to call it manually
			self.add_element_from_data(txt)
		uris = sel_data.get_uris()
		if uris:
			#self.uris.append(uris)
			#self.uris = self.uris	
			print uris
			#self.add_element(uris)
			self.add_element_from_data(uris)
	
	def on_draw (self, ctx):
		if self.theme:
			ctx.scale(self.scale, self.scale)
			# drag-highlight
			if self.dragging_over:
				ctx.set_operator(cairo.OPERATOR_ADD)
			# render
			ctx.translate(0, self.height - self.theme_height)
			self.theme.render(ctx, 'copystack-base')
			for el in self.elements:
				ctx.translate(0, -self.element_spacing)
				#ctx.rotate(1.2)
				if self.mouse_inside and el == self.selected_element:
					ctx.set_operator(cairo.OPERATOR_ADD)
				if isinstance(el, UrlElement):
					self.theme.render(ctx, 'copystack-element-url')
				elif isinstance(el, FileElement):
					self.theme.render(ctx, 'copystack-element-file')
				else:
					# unknown element
					self.theme.render(ctx, 'copystack-element')
				if self.mouse_inside and not self.dragging_over and \
					el == self.selected_element:
					ctx.set_operator(cairo.OPERATOR_OVER)
			# draw marker
			"""if self.mouse_inside and not self.dragging_over:
				y = (self.element_spacing * \
					(len(self.elements) - self.selected_index)) + \
					self.tooltip.height / 2 + self.element_spacing / 2
				ctx.set_source_rgba(0, 0, 0, 0.7)
				ctx.rectangle(0, y+5, self.width, 1)
				ctx.fill()"""
				
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)


# TODO: put in screenlets.ui
class Tooltip ():
	"""A window that displays a text and serves as Tooltip (very basic yet)."""
	
	# internals
	__timeout	= None
	
	# attribs
	text		= ''
	font_name	= 'Free Sans 8'
	width		= 100
	height		= 20
	x 			= 0
	y 			= 0
	
	def __init__ (self, width, height):
		object.__init__(self)
		# init
		self.__dict__['width']	= width
		self.__dict__['height']	= height
		self.window = gtk.Window()
		self.window.set_app_paintable(True)
		self.window.set_size_request(width, height)
		self.window.set_decorated(False)
		self.window.set_skip_pager_hint(True)
		self.window.set_skip_taskbar_hint(True)
		self.window.set_keep_above(True)
		self.screen_changed(self.window)
		self.window.connect("expose_event", self.expose)
		self.window.connect("screen-changed", self.screen_changed)
		#self.window.show()
		self.p_context = self.window.get_pango_context()
		self.p_layout = pango.Layout(self.p_context)
		self.p_layout.set_font_description(\
			pango.FontDescription(self.font_name))
		self.p_layout.set_width(-1)
	
	def __setattr__ (self, name, value):
		self.__dict__[name] = value
		if name in ('width', 'height', 'text'):
			if name== 'width':
				self.p_layout.set_width(width)
			elif name == 'text':
				self.p_layout.set_markup(value)
			self.window.queue_draw()
		elif name == 'x':
			self.window.move(value, self.y)
		elif name == 'y':
			self.window.move(self.x, value)
	
	def show (self):
		"""Show the Tooltip window."""
		self.cancel_show()
		self.window.show()
	
	def show_delayed (self, delay):
		"""Show the Tooltip window after a given delay."""
		self.cancel_show()
		self.__timeout = gobject.timeout_add(delay, self.__show_timeout)
	
	def hide (self):
		"""Hide the Tooltip window."""
		self.cancel_show()
		self.window.hide()
	
	def cancel_show (self):
		"""Cancel showing of the Tooltip."""
		if self.__timeout:
			gobject.source_remove(self.__timeout)
	
	def __show_timeout (self):
		self.show()
	
	def screen_changed (self, window, screen=None):
		if screen == None:
			screen = window.get_screen()
		map = screen.get_rgba_colormap()
		if not map:
			map = screen.get_rgb_colormap()
		window.set_colormap(map)
	
	def expose (self, widget, event):
		ctx = self.window.window.cairo_create()
		# set a clip region for the expose event
		ctx.rectangle(event.area.x, event.area.y,
			event.area.width, event.area.height)
		ctx.clip()
		# clear context
		ctx.set_source_rgba(1, 1, 1, 0)
		ctx.set_operator (cairo.OPERATOR_SOURCE)
		ctx.paint()
		# draw rectangle
		ctx.set_source_rgba(1, 1, 1, 0.7)
		ctx.rectangle(0, 0, self.width, self.height)
		ctx.fill()
		# draw text
		ctx.save()
		ctx.translate(3, 3)
		ctx.set_source_rgba(0, 0, 0, 1) 
		ctx.show_layout(self.p_layout)
		ctx.fill()
		ctx.restore()
		ctx.rectangle(0, 0, self.width, self.height)
		ctx.set_source_rgba(0, 0, 0, 0.7)
		ctx.stroke()


class Element:
	"""Abstract superclass for an element on the stack."""
	
	def __init__ (self, desc, data):
		self.desc	= desc		# info/tooltip
		self.data	= data


class TextElement (Element):
	"""A stack-element containing text."""
	
	def __init__ (self, desc, text):
		Element.__init__(self, desc, text)


class FileElement (Element):
	"""A stack-element containing a link to a file."""
	
	def __init__ (self, desc, text):
		Element.__init__(self, desc, text)


class UrlElement (Element):
	"""A stack-element containing an URL."""
	
	def __init__ (self, desc, url):
		Element.__init__(self, desc, url)



# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(CopyStackScreenlet)

