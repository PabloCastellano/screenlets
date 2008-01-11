#!/usr/bin/env python

# ConvertScreenlet (c) Vasek Potocek 2007 <vasek.potocek@post.cz>
#
# INFO:
# - screenlet performing various conversions
# - and not limited to numerical...
# 
# TODO:
# - replace ellipsizing with some warning (red text or so)?
# - more conversions - ideas?

import screenlets
from screenlets.options import StringOption
import cairo
import pango
import gtk
import os

class ConvertScreenlet(screenlets.Screenlet):
	"""A screenlet performing various numerical conversions."""
	
	# default meta-info for Screenlets
	__name__ = 'ConvertScreenlet'
	__version__ = '0.4'
	__author__ = 'Vasek Potocek'
	__desc__ = 'A screenlet performing various numerical conversions.'

	# the active converter -- see *Converter.py
	__converter = None
	# a list of the converter class objects
	__conv_list = []
	# this affects whether the active field is highlighted
	__has_focus = False

	# editable options
	# the name, i.e., __title__ of the active converter
	converter = ''
		
	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=200, height=100, 
				**keyword_args)
		# set theme
		self.theme_name = "default"
		# scan the screenlet directory for converter modules
		# I don't know why, but not doing the following caused the number of 
		# choices in the Options dialog box to rise on each reload.
		self.__conv_list = []
		filelist = os.listdir(self.get_screenlet_dir())
		for filename in sorted(filelist):
			if filename[-12:] == 'Converter.py':
				classname = filename[:-3]
				mod = __import__(classname)
				classobj = getattr(mod, classname)
				self.__conv_list.append(classobj)
				# add a menu item for each
				self.add_menuitem('conv:' + classobj.__name__, 
						classobj.__title__)
		# for sure
		if len(self.__conv_list) == 0:
			# FIXME: how do I abort the initialization?
			print "ConvertScreenlet: No converters found in current directory!"
			return
		# add default menu items
		self.add_default_menuitems()
		# add options
		self.add_options_group('Converter', 'Converter specific options')
		self.add_option(StringOption('Converter', 'converter', self.converter,
			'Convert engine', 'Active convert engine',
			choices = [classobj.__title__ for classobj in self.__conv_list]))
		# connect additional event handlers
		self.window.connect('key-press-event', self.key_press)
		# initialize default converter
		self.set_converter('BaseConverter')

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'converter':
			# This condition allows us to cache the option while avoiding 
			# recursion when the converter is selected from menu
			if value != self.__converter.__title__:
				self.set_converter(value)

	def on_menuitem_select(self, id):
		if id[:5] == 'conv:':
			if id[5:] != self.__converter.__name__:
				self.set_converter(id[5:])

	def set_converter(self, name):
		"""Set the active converter and related variables, either python or 
		human-readable name can be specified"""
		for classobj in self.__conv_list:
			if classobj.__name__ == name or classobj.__title__ == name:
				break
		else:
			# raise exception?
			print "Unknown converter '" + name + "'!"
			return
		conv = classobj()
		self.__converter = conv
		# make the option be cached and show in the Options dialog
		self.converter = conv.__title__
		self.redraw_canvas()

	# I don't want to call this on_key_press, I consider such a name reserved 
	# for future versions of screenlets.
	def key_press(self, widget, event):
		"""Called when a keypress-event occured in Screenlet's window."""
		if self.__converter.on_key_press(gtk.gdk.keyval_name(event.keyval)):
			self.redraw_canvas()
		return False

	def on_mouse_down(self, event):
		# filter events
		if event.button != 1 or event.type != gtk.gdk.BUTTON_PRESS:
			return False
		# recalculate cursor position
		x = event.x / self.scale
		y = event.y / self.scale
		# compute space between fields
		n = self.__converter.num_fields
		m = (100 - 20*n) / (n + 1)
		# find if a click occured over some field...
		if x >= 50 and x <= 190:
			if y >= m and y <= 100:
				d = y - m
				if d % (20 + m) <= 20:
					# ...and compute its index.
					self.__converter.active_field = int(d / (20 + m))
					self.__converter.replace = True
					# redraw and make the window not shiver
					self.redraw_canvas()
					return True
		return False

	def on_focus(self, event):
		self.__has_focus = True
		if self.__converter:
			self.__converter.replace = True
		self.redraw_canvas()

	def on_unfocus(self, event):
		self.__has_focus = False
		self.redraw_canvas()
	
	def on_draw(self, ctx):
		# if a converter or theme is not yet loaded, there's no way to continue
		if not self.__converter or not self.theme:
			return
		# set scale relative to scale-attribute
		ctx.scale(self.scale, self.scale)
		# render background
		self.theme['convert-bg.svg'].render_cairo(ctx)
		# compute space between fields
		n = self.__converter.num_fields
		m = (100 - 20*n) / (n + 1)
		# draw fields
		ctx.save()
		ctx.translate(0, m)
		for i in range(n):
			if self.__has_focus and i == self.__converter.active_field:
				self.theme['convert-fieldhl.svg'].render_cairo(ctx)
				# cursor: disabled - it looks weird
				#ctx.rectangle(185, 3, 2, 16)
				#ctx.fill()
			else:
				self.theme['convert-field.svg'].render_cairo(ctx)
			ctx.translate(0, m + 20)
		ctx.restore()
		# render field names
		ctx.save()
		p_layout = ctx.create_layout()
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Free Sans")
		p_fdesc.set_size(11 * pango.SCALE)
		p_layout.set_font_description(p_fdesc)
		p_layout.set_width(40 * pango.SCALE)
		ctx.translate(10, m + 2)
		ctx.set_source_rgba(0, 0, 0, 1)
		for i in range(n):
			p_layout.set_markup('<b>' 
					+ self.__converter.field_names[i] 
					+ '</b>')
			ctx.show_layout(p_layout)
			ctx.translate(0, m + 20)
		ctx.restore()
		# render field values
		ctx.save()
		ctx.translate(55, m + 2)
		p_layout.set_alignment(pango.ALIGN_RIGHT)
		p_layout.set_width(130 * pango.SCALE)
		p_layout.set_ellipsize(pango.ELLIPSIZE_END)
		for i in range(n):
			p_layout.set_markup(str(self.__converter.values[i]))
			ctx.show_layout(p_layout)
			ctx.translate(0, m + 20)
		ctx.restore()
		# ...and finally something to cover this all
		self.theme['convert-glass.svg'].render_cairo(ctx)
	
	def on_draw_shape(self, ctx):
		if self.theme:
			ctx.scale(self.scale, self.scale)
			# the background will serve well
			self.theme['convert-bg.svg'].render_cairo(ctx)



# The base Converter class. Not to be used directly.
# For a commented example on how to write general converter modules, see the 
# file BaseConverter.py. But first, please, read below if a RatioConverter isn't 
# well suitable for your desired task.

class Converter:
	"""The base class for the converters. The converters look after maintaining 
	the list of currently shown values - initialising, accepting keyboard input, 
	etc.."""

	# the name of the class
	__name__ = 'Converter'
	# a short description to be used for selecting the converter
	__title__ = 'Base'

	# the number of fields shown on the display between 2 and 4
	num_fields = 0
	# field captions up to 4 chars long
	field_names = []
	# zero-based index of field having input focus
	active_field = 0
	# the list of currently shown 'values'. They should always be strings.
	values = []
	# replace: True = replace all the input by next keypress
	replace = True

	# initialize the list of values and fill it with defaults (strings!). 
	# Override this if you don't want then be '0's.
	def __init__(self):
		self.values = []
		for i in range(self.num_fields):
			self.values.append('0')
		self.active_field = 0
	
	def on_key_press(self, key):
		"""If accepted, appends the pressed key to the value in the currently 
		active field."""
		translate_dict = {'comma': '.', 'period': '.', 'Add': '+', 'plus': '+', 
				'Subtract': '-', 'minus': '-'}
		if key[:3] == 'KP_':
			key = key[3:]		# keys from numerical keypad come as digits
		if translate_dict.has_key(key):
			key = translate_dict[key]
		if key == 'BackSpace':	# try to guess :-)
			self.values[self.active_field] = self.values[self.active_field][:-1]
		elif key == 'Escape':	# clean the field
			self.values[self.active_field] = ''
		elif key == 'Down':		# move field focus
			if self.active_field < self.num_fields - 1:
				self.active_field += 1
				self.replace = True	# after a change, don't append next pressed 
				return True			# key but start over
			return False
		elif key == 'Up':
			if self.active_field > 0:
				self.active_field -= 1
				self.replace = True
				return True
			return False
		elif key == 'Tab':
			self.active_field += 1
			self.active_field %= self.num_fields
			self.replace = True
			return True
		else:		# leave other keys unchanged
			if not self.filter_key(key):
				return False
			if self.replace:
				self.values[self.active_field] = key
			# limit input length to 10 characters
			elif len(self.values[self.active_field]) < 10:
				self.values[self.active_field] = \
					self.values[self.active_field] + key
			self.replace = False
		self.neaten_input()
		self.convert()
		return True

	# You can use this function instead of str or fixed-width % - it leaves 
	# 3 digits after the decimal point for floats, and no decimal part if the 
	# number is integer.
	# Serves good if the same converter can be used for both ints ant floats,
	# so that the user doesn't get '1.000' when not necessary, also for showing
	# '0' instead of '0.000' in all cases.
	def str(self, val):
		if val == int(val):
			return str(int(val))
		else:
			return '%.3f' % val

	# Overridable functions:

	# neaten_input: see the docstring
	# Return value: none
	# If you don't want such function, override it in your converter with pass.
	# If you override it by something more complicated, be careful not to modify 
	# the current value so that it breaks the input.
	def neaten_input(self):
		"""Replaces an empty value with '0' and again removes leading '0' in 
		a non-empty string."""
		# This version is aware of the possibility of negative input values,
		# but you must allow + and - keys in filter_key and avoid an error when 
		# the input is '-'. See TemperatureConverter for an example.
		if self.values[self.active_field] == '' or \
				self.values[self.active_field][-1] == '+':
					self.values[self.active_field] = '0'
		elif self.values[self.active_field][-1] == '-':
			self.values[self.active_field] = '-'
		if len(self.values[self.active_field]) > 1 and \
				self.values[self.active_field][0] == '0':
			self.values[self.active_field] = self.values[self.active_field][1:]

	# filter_key: decides if pressed key can be appended to current value.
	# "key" is the GDK name of the key pressed by user
	# Return value: True - accept key, False - reject it.
	# There is no way to modify the value of key.
	# Be prepared for various "keys", e.g., 'apostrophe' must not match 'a'.
	def filter_key(self, key):
		"""Decides whether to accept pressed key."""
		return False

	# convert: actualizes field values to reflect input
	# Return value: none
	# Active value can be modified, but not so that it breaks the input.
	def convert(self):
		"""Recalculates field values after changes."""
		pass


# A subclass of Converter representing numerical converters whose field are 
# bound by a simple linear relation. It cares about float value input and output 
# and conversion, so the developer who wants to use it doesn't need to provide 
# any functions. Besides the __anything__, num_fields and field_names variables, 
# he must only provide a list describing desired ratios (see below).
# Not to be used directly. See LengthConverter for a commented example.

class RatioConverter(Converter):
	"""A base class of converters having linear dependances between their 
	fields."""

	__name__ = 'RatioConverter'
	__title__ = 'Base / Ratio'

	# The list of relative weights of the individual fields. The length of this 
	# list must be equal to num_fields. The ratio between two fields will be 
	# inverse to the ratio of corresponding entries in this list. For example, 
	# see LengthConverter. One may ask whether not to better use relative 
	# ratios, i.e., ratios between fields = ratio between entries, the answer is 
	# that this approach is more intuitive. You would set 1 for some unit and 
	# 1000 for the corresponding kilo-unit this way.
	# The above implies that the values in this list are relative to whichever 
	# one you would choose, e.g., [10, 5, 1] (will be converted to float) is 
	# equivalent to [2.0, 1.0, 0.2]. Actually, integer (exact) values are 
	# preferred if they reflect the logic of the conversion.
	weights = []

	def filter_key(self, key):
		# Accept digits
		if key.isdigit():
			return True
		# Also accept a decimal point if there is no one yet
		elif key == '.':
			return not ('.' in self.values[self.active_field])
		else:
			return False

	def convert(self):
		# A multiply-then-divide approach is used to help avoiding little
		# inaccuracies arising in operations like (3/10)*100.
		val = float(self.values[self.active_field]) \
				* self.weights[self.active_field]
		for i in range(self.num_fields):
			if i == self.active_field:
				continue
			self.values[i] = self.str(val / float(self.weights[i]))
	# Note: if you don't like the Converter.str() function used above which 
	# tries to always display integers as integers, you can provide your own, 
	# e.g., def str(self, val): return '%.3f' % val



# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(ConvertScreenlet)
