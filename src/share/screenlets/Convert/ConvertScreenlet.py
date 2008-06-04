#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

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
from screenlets.options import StringOption, ColorOption
from screenlets import Plugins
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
	background_color = (0,0,0, 0.8)
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
		filelist = os.listdir(Plugins.PATH)

		for filename in sorted(filelist):
			
			if filename[-12:] == 'Converter.py':

				classname = filename[:-3]
				mod = Plugins.importAPI(classname)
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


		# add options
		self.add_options_group('Converter', 'Converter specific options')
		self.add_option(StringOption('Converter', 'converter', self.converter,
			'Convert engine', 'Active convert engine',
			choices = [classobj.__title__ for classobj in self.__conv_list]))
		self.add_option(ColorOption('Converter','background_color', 
			self.background_color, 'Back color(only with default theme)', 'only works with default theme'))
	
		# connect additional event handlers
		# initialize default converter
		self.set_converter('BaseConverter')

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()

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
		ctx.set_source_rgba(*self.background_color)
		if self.theme_name == 'default':self.draw_rounded_rectangle(ctx,0,0,10,200,100)
		self.theme.render(ctx,'convert-bg')
		ctx.set_source_rgba(0, 0, 0, 1)
		# compute space between fields
		n = self.__converter.num_fields
		m = (100 - 20*n) / (n + 1)
		# draw fields
		ctx.save()
		ctx.translate(0, m)
		for i in range(n):
			if self.__has_focus and i == self.__converter.active_field:
				self.theme.render(ctx,'convert-fieldhl')
				# cursor: disabled - it looks weird
				#ctx.rectangle(185, 3, 2, 16)
				#ctx.fill()
			else:
				self.theme.render(ctx,'convert-field')
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
		self.theme.render(ctx,'convert-glass')
	
	def on_draw_shape(self, ctx):
		if self.theme:
			ctx.scale(self.scale, self.scale)
			# the background will serve well
			self.theme.render(ctx,'convert-bg')







# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(ConvertScreenlet)
