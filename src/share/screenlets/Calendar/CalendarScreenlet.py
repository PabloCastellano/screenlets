#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  CalendarScreenlet (c) robgig1088 2007
#
# INFO:
# - 
#

import screenlets
import cairo
import pango
import datetime

class CalendarScreenlet (screenlets.Screenlet):
	"""A simple Calendar Screenlet."""
	
	# default meta-info for Screenlets
	__name__	= 'CalendarScreenlet'
	__version__	= '0.3'
	__author__	= 'RYX (initial version by robgig1088)'
	__desc__	= __doc__

	# constructor
	def __init__(self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, uses_theme=True, **keyword_args)
		# set some options
		self.text_shadow_offset = 0.666
		# set theme
		self.theme_name = "ryx"

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()	
		
	def get_date_info(self):
		now = datetime.datetime.now()
		#get day
		day = now.strftime("%d")
		#get the month number
		month_num = now.strftime("%m")
		# get the year
		year = now.strftime("%Y")
		 #get the month name
		month_name = now.strftime("%B")
		#make a date (1st of month)
		when = datetime.date(int(year), int(month_num), int(1))
		# get the first day of the month (mon, tues, etc..)
		first_day = when.strftime("%A")
		# find number of days in the month
		if month_num in (1, 3, 5, 7, 8, 10, 12):
			days_in_month = 31
		elif month_num <> 2:
			days_in_month = 30
		elif year%4 == 0:
			days_in_month = 29
		else:
			days_in_month = 28
		#find the first day of the month
		start_day = int(when.strftime("%u"))  
		if start_day == 7:				# and do calculations on it...
			start_day = 0   
		start_day = start_day + 1
		# return the whole stuff
		return [day, month_num, year, month_name, days_in_month, 
			first_day, start_day]
	
	def draw_year_and_month (self, ctx, pl, year, month):
		ctx.save()
		ctx.translate(5 + self.text_shadow_offset, 5 + self.text_shadow_offset)
		# draw the month
		pl.set_width((self.width) * pango.SCALE)
		pl.set_markup('<b>' + month + '</b>')
		ctx.set_source_rgba(0, 0, 0, 0.3)
		ctx.show_layout(pl)
		ctx.translate(-self.text_shadow_offset, -self.text_shadow_offset)
		ctx.set_source_rgba(1, 1, 1, 0.8)
		ctx.show_layout(pl)
		# draw the year
		ctx.translate(70 + self.text_shadow_offset, self.text_shadow_offset)
		pl.set_markup('<b>' + year + '</b>')
		ctx.set_source_rgba(0, 0, 0, 0.3)
		ctx.show_layout(pl)
		ctx.translate(-self.text_shadow_offset, -self.text_shadow_offset)
		ctx.set_source_rgba(1, 1, 1, 0.8)
		ctx.show_layout(pl)
		ctx.restore()
	
	def draw_header (self, ctx, pl):
		ctx.save()
		ctx.translate(5 + self.text_shadow_offset, 17 + self.text_shadow_offset)
		pl.set_markup('<b>' + "Su  Mo  Tu  We  Th  Fr  Sa" + '</b>')
		ctx.set_source_rgba(0, 0, 0, 0.3)
		ctx.show_layout(pl)
		ctx.translate(-self.text_shadow_offset, -self.text_shadow_offset)
		ctx.set_source_rgba(1, 1, 1, 0.8)
		ctx.show_layout(pl)
		ctx.restore()
	
	def draw_days (self, ctx, pl, date):
		#ctx.translate(-5, 0)
		row = 1
		day = int(date[6])
		tso = self.text_shadow_offset
		for x in range(date[4] + 1):
			ctx.save()
			ctx.translate(4 + (day-1) * 13 + tso, 30 + 12 * (row - 1) + tso)
			if str(int(x)+1) == str(date[0]) or \
				"0" + str(int(x)+1) == str(date[0]):
				ctx.save()
				ctx.translate(0, -1)
				self.theme.render(ctx, 'calendar-day-bg')
				ctx.restore()
			if int(x)+1 < 10:
				# draw the days
				pl.set_markup('<b>' + " 0" + str(x+1) + '</b>')
			else:
				pl.set_markup('<b>' + " " + str(x+1) + '</b>')
			ctx.set_source_rgba(0, 0, 0, 0.3)
			ctx.show_layout(pl)
			ctx.translate(-tso, -tso)
			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.show_layout(pl)
			if day == 7:
				day = 0
				row = row + 1
			day = day + 1
			ctx.restore()
	
	def on_draw (self, ctx):
		# get dates
		date = self.get_date_info()
		# set size
		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			# render bg
			self.theme.render(ctx, 'calendar-bg')
			# create layout
			p_layout = ctx.create_layout()
			p_fdesc = pango.FontDescription("Free Sans 5")
			p_layout.set_font_description(p_fdesc)
			# draw year/month
			self.draw_year_and_month(ctx, p_layout, date[2], date[3])
			# draw header
			self.draw_header(ctx, p_layout)
			# draw days
			self.draw_days(ctx, p_layout, date)
		
	def on_draw_shape(self,ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			self.theme.render(ctx, 'calendar-bg')

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(CalendarScreenlet)

