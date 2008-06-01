#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# SpeechScreenlet (c) Whise <helder.fraga@hotmail.com>
#
# INFO:
# - A screenlet that searches the most popular search engines sites


import screenlets
from screenlets.options import ColorOption
import cairo
import pango
import gtk
from os import system
from urllib import quote
from screenlets import DefaultMenuItem , utils
import sys

is_manager = utils.is_manager_running_me()
try:
	from orca import speech,orca_i18n
	from orca.orca_i18n import _           # for gettext support
	from orca.orca_i18n import Q_          # to provide qualified translatable strings
except:
	if not is_manager:
		screenlets.show_message(None,'Orca is required to use this Screenlet')
		sys.exit()
	else:
		print 'Orca is required to use this Screenlet'



class SpeechScreenlet(screenlets.Screenlet):
	"""A screenlet that speaks what you type , uses orca tts api"""
	
	# default meta-info for Screenlets
	__name__ = 'SpeechScreenlet'
	__version__ = '0.1'
	__author__ = 'Helder Fraga aka whise'
	__desc__ = 'A screenlet that speaks what you type , uses orca tts api'

	# a list of the converter class objects

	__has_focus = False
	__query = ''
	frame_color = (0, 0, 0, 0.7)
	# editable options
	# the name, i.e., __title__ of the active converter
	p_fdesc = None
	p_layout = None
	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=201, height=50, 
				**keyword_args)
		# set theme
		self.theme_name = "default"

		# add options
		self.add_options_group('Options', 'Options')

		self.add_option(ColorOption('Options','frame_color', 
			self.frame_color, 'Frame color', 
			'Frame color'))

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)




	def on_key_down(self, keycode, keyvalue, event):
		"""Called when a keypress-event occured in Screenlet's window."""
		key = gtk.gdk.keyval_name(event.keyval)
		if key == "Return" or key == "Tab":
			# submit query
			if self.__query != '':speech.speak(_(self.__query))
			
			self.__query = ''
			self.redraw_canvas()
		elif key == "BackSpace":
			self.__query = self.__query[:-1]
			self.redraw_canvas()
		elif key == "space":
			self.__query += " "
			self.redraw_canvas()
		else:
			self.__query += keyvalue
			self.redraw_canvas()

	def on_init(self):
		
		self.add_default_menuitems()
		speech.init()


	def on_mouse_down(self, event):
		# filter events
		if event.button != 1 or event.type != gtk.gdk.BUTTON_PRESS:
			return False
		# recalculate cursor position
		x = event.x / self.scale
		y = event.y / self.scale
		# compute space between fields
		n = 1
		m = 10
		# find if a click occured over some field...
		if x >= 50 and x <= 190:
			if y >= m and y <= 100:
				d = y - m
				if d % (20 + m) <= 20:
					self.redraw_canvas()
					return True
		if x >= 4 and x<= 46:

			if self.__query != '': speech.speak(_(self.__query))
		return False

	def on_focus(self, event):
		self.__has_focus = True
		#if self.__converter:

		self.redraw_canvas()

	def on_unfocus(self, event):
		self.__has_focus = False
		self.redraw_canvas()
	
	def on_draw(self, ctx):
		# if a converter or theme is not yet loaded, there's no way to continue
		# set scale relative to scale-attribute
		ctx.scale(self.scale, self.scale)
		n = 1
		m = 10
		ctx.save()
		if self.theme:	
			ctx.set_source_rgba(*self.frame_color)
			if self.theme_name == 'default':self.draw_rounded_rectangle(ctx,0,0,6.5,200,40)
			self.theme.render(ctx,'background')

		ctx.translate(6, 8)
		if self.theme:	
			self.theme.render(ctx,'icon')
		ctx.translate(-6, -8)
		ctx.translate(50, m)
		if self.theme:
			for i in range(n):
				if self.__has_focus:
					self.theme.render(ctx,'fieldh')
					# cursor: disabled - it looks weird
				#	ctx.rectangle(185, 3, 2, 16)
				#	ctx.fill()
				else:
					self.theme.render(ctx,'field')
				ctx.translate(0, m + 20)
		ctx.restore()
		# render field names
		# ctx.save()
		ctx.set_source_rgba(0,0,0,1)
		if self.p_layout == None :
	
			self.p_layout = ctx.create_layout()
		else:
		
			ctx.update_layout(self.p_layout)
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Free Sans")
		p_fdesc.set_size(11 * pango.SCALE)
		self.p_layout.set_font_description(p_fdesc)
		self.p_layout.set_width(40 * pango.SCALE)
		ctx.save()
		ctx.translate(55, m + 3)
		self.p_layout.set_alignment(pango.ALIGN_RIGHT)
		self.p_layout.set_width(130 * pango.SCALE)
		self.p_layout.set_ellipsize(pango.ELLIPSIZE_START)
		for i in range(n):
			if self.has_focus:
				self.p_layout.set_markup(self.__query + '_')
			else:
				self.p_layout.set_markup(self.__query)
			ctx.show_layout(self.p_layout)
			ctx.translate(0, m + 20)
		ctx.restore()

	
	def on_draw_shape(self, ctx):
		self.on_draw(ctx)



# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(SpeechScreenlet)
