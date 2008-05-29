#!/usr/bin/env python

#  StocksScreenlet (c) Patrik Kullman 2007 <patrik@yes.nu>
#
# INFO:
# - Retrieve stock-information from finance.yahoo.com
# - Info button opens a more detailed view on finance.yahoo.com in webbrowser
#
# TODO:
# - make web browser gain focus and leave widget-mode when info-button is clicked
#
# CHANGELOG:
# v0.2:
# - added fault tolerance when not being able to retrieve data (print it in the screenlet, retry every 30 seconds until success)

import screenlets
from screenlets.options import BoolOption
from screenlets.options import IntOption
from screenlets.options import StringOption
import cairo
import gtk
import pango
from urllib2 import urlopen
from urllib2 import URLError
from os import system
import gobject

class StocksScreenlet(screenlets.Screenlet):

	# default meta-info for Screenlets
	__name__ = 'StocksScreenlet'
	__version__ = '0.2.1'
	__author__ = 'Patrik Kullman (modified by Pedro Huerta)'
	__desc__ = 'Retrieve stock-information from finance.yahoo.com'

	# internals
	__word = {"word": "Fetching stock...", "desc": "Please stand by..."}
	__stockdata = {'name': "Not updated", 'last_trade': 0.00, 'change': 0.00, 'percent_change': 0.00}
	__timeout = None
	__offline_timer = None

	# editable options and defaults
	update_interval = 3600 # every hour
	symbol = 'GOOG'
	use_percentage = False

	# constructor
	def __init__(self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, width=200, height=100, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add option groups
		self.fetch_stocks()
		self.update_interval = self.update_interval
		self.add_options_group('Stocks', 'Stocks settings')
		self.add_option(IntOption('Stocks',
			'update_interval', 						# attribute-name
			self.update_interval,						# default-value
			'Update interval (seconds)', 						# widget-label
			'Specify number of seconds between re-fetching stock data', min=60, max=86400	# description
			))
		self.add_option(BoolOption('Stocks',
			'use_percentage', 						# attribute-name
			self.use_percentage,						# default-value
			'Use % variation',						# widget-label
			'Show % variation instead of absolute change',	# description
			))
		self.add_option(StringOption('Stocks',
			'symbol', 						# attribute-name
			self.symbol,						# default-value
			'Stock symbol', 						# widget-label
			'The stock symbol of the company',	# description
			))

	def on_init (self):
		# add default menu items
		self.add_default_menuitems()

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# redraw the canvas when server-info is changed since a server host/ip addition/removal will change the size of the screenlet
		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(value * 1000, self.update)
			else:
				# TODO: raise exception!!!
				pass
		if name == "symbol":
			self.fetch_stocks()

		if name == "use_percentage":
			self.fetch_stocks()

	def update(self):
		gobject.idle_add(self.fetch_stocks)
		return True

	def on_draw(self, ctx):
		# scaling above 500% is very slow and might brake it (why?)
		if self.scale > 5:
			self.scale = 5
		# if theme is loaded
		if self.theme:
			# find out how many servers that are configured and force a update_shape() when they're changed from the last draw.
			# apparently the settings doesn't get loaded until the widget is first displayed, and no update_shape is performed at
			# that point
			# make sure that the background covers all the icons
			ctx.save()
			ctx.scale(self.scale, self.scale)
			ctx.translate(0, 0)
			self.theme.render(ctx, 'background')
			ctx.restore()

			ctx.save()
			ctx.translate(172 * self.scale, 8 * self.scale)
			ctx.scale(self.scale * 0.5, self.scale * 0.5)
			self.theme.render(ctx, 'info')
			ctx.restore()

			ctx.save()
			ctx.scale(self.scale, self.scale)
			self.draw_text(ctx, '<b>' + self.__stockdata['name'] + '</b>', 10, 10, 12)
			if self.__stockdata['change'] == "N/A":
				change_color = "white"
				icon = "level"
			else:
				stockchange = float(self.__stockdata['change'])
				if (stockchange == 0):
					change_color = "white"
					icon = "level"
				elif (stockchange < 0):
					change_color = "red"
					icon = "down"
				elif (stockchange > 0):
					change_color = "green"
					icon = "up"
			if self.use_percentage:
				self.draw_text(ctx, "Change: <span foreground='" + change_color + "'>" + str(self.__stockdata['percent_change']) + "%</span>", 10, 50, 10)
			else:
				self.draw_text(ctx, "Change: <span foreground='" + change_color + "'>" + str(self.__stockdata['change']) + "</span>", 10, 50, 10)
			self.draw_text(ctx, "Last trade: " + str(self.__stockdata['last_trade']), 10, 70, 10)
			ctx.restore()

			ctx.save()
			ctx.scale(self.scale, self.scale)
			ctx.translate(140, 40)
			ctx.scale(0.5, 0.5)
			self.theme.render(ctx, icon)
			ctx.restore()

			ctx.save()
			ctx.scale(self.scale, self.scale)
			ctx.translate(0, 0)
			self.theme.render(ctx, 'glass')
			ctx.restore()

	def on_mouse_down(self, event):
		if event.button != 1 or event.type != gtk.gdk.BUTTON_PRESS:
			return False
		# recalculate cursor position
		x = event.x / self.scale
		y = event.y / self.scale
		if x > 170 and y < 28:
			self.open_info()
		if 60 < x and x < 120 and 45 < y and y < 70:
			print x, y
			self.__setattr__('use_percentage', not self.use_percentage)
			self.redraw_canvas()

	def on_draw_shape(self, ctx):
		if self.theme:
			self.on_draw(ctx)

	def draw_text(self, ctx, value, x, y, size):
		# stolen from CalcScreenlet ;)
		ctx.save()
		ctx.translate(x, y)
		p_layout = ctx.create_layout()
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Sans")
		p_fdesc.set_size(size * pango.SCALE)
		p_layout.set_font_description(p_fdesc)
		p_layout.set_width(180 * pango.SCALE)
		p_layout.set_alignment(pango.ALIGN_LEFT)
		p_layout.set_markup(value)
		ctx.set_source_rgba(1, 1, 1, 0.8)
		ctx.show_layout(p_layout)
		p_layout.set_alignment(pango.ALIGN_CENTER)
		ctx.restore()

	def fetch_stocks(self):
		if self.__offline_timer:
			gobject.source_remove(self.__offline_timer)
		try:
			stockfd = urlopen('http://download.finance.yahoo.com/d/quotes.csv?s=' + self.symbol + '&f=nl1c1')
			stockcsv = stockfd.read().split(",")
			if stockcsv[0].strip() == "Missing Symbols List.":
				stockdata = {'name': "Wrong symbol", 'last_trade': 0.00, 'change': 0.00, 'percent_change': 0.00}
			else:
				stockdata = {}
				stockdata['name'] = stockcsv[0].split('"')[1].title()
				stockdata['last_trade'] = stockcsv[1]
				stockdata['change'] = stockcsv[2]
				change = float(stockdata['change'])/(float(stockdata['last_trade'])-float(stockdata['change']))
				if change > 0:
					stockdata['percent_change'] = '+' + str(round(100*change,2))
				if change < 0:
					stockdata['percent_change'] = '-' + str(round(100*change,2))
		except URLError:
			stockdata = {'name': "Connection Error", 'last_trade': 0.00, 'change': 0.00}
			self.__offline_timer = gobject.timeout_add(30 * 1000, self.update)
		self.__stockdata = stockdata
		stockdata = None
		self.redraw_canvas()

	def open_info(self):
		system("gnome-open 'http://finance.yahoo.com/q?s=" + self.symbol + "'")

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(StocksScreenlet)

