#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# SearchScreenlet by Helder Fraga
#
# INFO:
# - A screenlet that searches the most popular search engines sites


import screenlets
from screenlets.options import StringOption
import cairo
import pango
import gtk
from os import system
from urllib import quote
from screenlets import DefaultMenuItem

class SearchScreenlet(screenlets.Screenlet):
	"""A screenlet performing various numerical conversions."""
	
	# default meta-info for Screenlets
	__name__ = 'SearchScreenlet'
	__version__ = '0.1'
	__author__ = 'Helder Fraga aka whise'
	__desc__ = 'A screenlet that searches the most popular search engines'

	# a list of the converter class objects
	__engines = [
		{"name": "Delicious",	"icon": "delicious.png",	"url": "http://del.icio.us/search/?p=%s&type=all"},
		{"name": "Digg",	"icon": "digg.png",		"url": "http://www.digg.com/search?section=news&s=%s"},
		{"name": "Google",	"icon": "google.png",		"url": "http://www.google.com/search?q=%s&ie=utf-8&oe=utf-8&aq=t&client=SearchScreenlet"},
		{"name": "IMDb",	"icon": "imdb.png",		"url": "http://imdb.com/find?q=%s"},
		{"name": "Wikipedia",	"icon": "wikipedia.png",	"url": "http://wikipedia.org/wiki/%s"},
		{"name": "Yahoo!",	"icon": "yahoo.png",		"url": "http://search.yahoo.com/search?p=%s"},
		{"name": "-",	"icon": "",		"": ""},
		{"name": "Dictionary",	"icon": "dictionary.png",		"url": "http://dictionary.reference.com/browse/%s"},
		{"name": "Thesaurus",	"icon": "thesaurus.png",		"url": "http://thesaurus.reference.com/browse/%s"},
		{"name": "Reference",	"icon": "reference.png",		"url": "http://www.reference.com/search?q=%s"},
		{"name": "-",	"icon": "",		"": ""},
		{"name": "ThePirateBay",	"icon": "icon_piratebay.png",	"url": "http://thepiratebay.org/search/%s"},
		{"name": "Demonoid",	"icon": "delicious.png",	"url": "http://www.demonoid.com/files/?category=0&subcategory=All&quality=All&seeded=0&external=2&query=%s"},
		{"name": "TorrentSpy",	"icon": "icon_torrentspry.png",		"url": "http://www.torrentspy.com/search?query=%s"},
		{"name": "Isohunt",	"icon": "icon_isohunt.png",		"url": "http://isohunt.com/torrents/?ihq=%s"},
		{"name": "Mininova",	"icon": "icon_minienova.png",		"url": "http://www.mininova.org/search/?search=%s"},
	]
	__engine = __engines[2]
	__has_focus = False
	__query = ''

	# editable options
	# the name, i.e., __title__ of the active converter
	engine = 'Google'

	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=200, height=40, 
				**keyword_args)
		# set theme
		self.theme_name = "default"

		# add options
		self.add_options_group('Engine', 'Web search engine settings')
		self.add_option(StringOption('Engine', 'engine', self.engine,
			'TorrentSearch engine', 'TorrentSearch engine',
			choices = [dictitem["name"] for dictitem in self.__engines]))
		# connect additional event handlers
		# self.window.connect('key-press-event', self.key_press)
		# initialize default converter
		# self.set_converter('BaseConverter')

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'engine':
			# This condition allows us to cache the option while avoiding 
			# recursion when the converter is selected from menu
			if value != self.__engine['name']:
				self.set_engine(value)

	def set_engine(self, name):
		"""Set the active converter and related variables, either python or 
		human-readable name can be specified"""
		for engine in self.__engines:
			if engine["name"] == name:
				break
		self.__engine = engine
		# make the option be cached and show in the Options dialog
		self.engine = engine['name']
		self.redraw_canvas()

	# I don't want to call this on_key_press, I consider such a name reserved 
	# for future versions of screenlets.
	def on_key_down(self, keycode, keyvalue, event):
		"""Called when a keypress-event occured in Screenlet's window."""
		key = gtk.gdk.keyval_name(event.keyval)
		if key == "Return" or key == "Tab":
			# submit query
			system("gnome-open '" + self.__engine['url'].replace('%s', quote(self.__query)) + "'")
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
		for dictitem in self.__engines:
			self.add_menuitem('engine = ' + str(dictitem["name"]), str(dictitem["name"]))	
		self.add_default_menuitems()

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
		return False

	def on_focus(self, event):
		self.__has_focus = True
		#if self.__converter:
		#	self.__converter.replace = True
		self.redraw_canvas()

	def on_unfocus(self, event):
		self.__has_focus = False
		self.redraw_canvas()
	
	def on_draw(self, ctx):
		# if a converter or theme is not yet loaded, there's no way to continue
		# set scale relative to scale-attribute
		ctx.scale(self.scale, self.scale)
		# render background
		self.theme['background.svg'].render_cairo(ctx)
		# compute space between fields
		n = 1
		m = 10
		# draw fields
		ctx.save()
		ctx.translate(8, 6)
		ctx.scale(1.5,1.5)
		ctx.set_source_surface(self.theme[self.__engine['icon']], 0, 0)
		ctx.paint()
		ctx.restore()
		ctx.save()
		ctx.translate(50, m)
		for i in range(n):
			if self.__has_focus:
				self.theme['fieldh.svg'].render_cairo(ctx)
				# cursor: disabled - it looks weird
				ctx.rectangle(185, 3, 2, 16)
				ctx.fill()
			else:
				self.theme['field.svg'].render_cairo(ctx)
			ctx.translate(0, m + 20)
		ctx.restore()
		# render field names
		# ctx.save()
		p_layout = ctx.create_layout()
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Free Sans")
		p_fdesc.set_size(11 * pango.SCALE)
		p_layout.set_font_description(p_fdesc)
		p_layout.set_width(40 * pango.SCALE)
		# ctx.translate(10, m + 3)
		# ctx.set_source_rgba(0, 0, 0, 1)
		# for i in range(n):
		# 	p_layout.set_markup('<b>' 
		#			+ 'etst' 
		#			+ '</b>')
		#	ctx.show_layout(p_layout)
		#	ctx.translate(0, m + 20)
		#ctx.restore()
		# render field values
		ctx.save()
		ctx.translate(55, m + 3)
		p_layout.set_alignment(pango.ALIGN_RIGHT)
		p_layout.set_width(130 * pango.SCALE)
		p_layout.set_ellipsize(pango.ELLIPSIZE_START)
		for i in range(n):
			p_layout.set_markup(self.__query)
			ctx.show_layout(p_layout)
			ctx.translate(0, m + 20)
		ctx.restore()
		# ...and finally something to cover this all

	
	def on_draw_shape(self, ctx):
		if self.theme:
			ctx.scale(self.scale, self.scale)
			# the background will serve well
			self.theme['background.svg'].render_cairo(ctx)

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id == "hide_show":
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			pass
		elif id[:4] == "add:":
			# make first letter uppercase (workaround for xml-menu)
			name = id[4].upper()+id[5:][:-9]
			 #and launch screenlet (or show error)
			if not screenlets.launch_screenlet(name):
				screenlets.show_error(self, 'Failed to add %sScreenlet.' % name)
		elif id[:6] == "engine":
			# execute shell command
			engine = id[9:][:+20]
			self.set_engine(id[9:][:+20])
			self.redraw_canvas()
			print  (engine)
		#elif id[:7] == "engine7":
		#	screenlets.show_error(self, id[8:][:+10])
			#engine = 'Mininova'
		#	self.set_engine(id[6:][:+8] )
		#	self.redraw_canvas()

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(SearchScreenlet)
