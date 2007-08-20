#!/usr/bin/env python

#  CalendarScreenlet (c) robgig1088 2007
#
# INFO:
# - 
#

import screenlets
import cairo
import pango
import time
import datetime

class CalendarScreenlet (screenlets.Screenlet):
	"""A simple Calendar Screenlet."""
	
	# default meta-info for Screenlets
	__name__	= 'CalendarScreenlet'
	__version__	= '0.2'
	__author__	= 'RYX (initial version by robgig1088)'
	__website__	= 'http://www.screenlets.org/screenlets'
	__desc__	= __doc__

	# constructor
	def __init__(self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, width=200, height=200, 
			uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "ryx"
		# add default menu items
		self.add_default_menuitems()
		
	# attribute-"setter", handles setting of attributes
	#def __setattr__(self, name, value):
	#	# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
	#	screenlets.Screenlet.__setattr__(self, name, value)

	def get_date_info(self, old_cuse = [0]):
		#get day
		day = datetime.datetime.now().strftime("%d")
		#get the month number
		month_num = datetime.datetime.now().strftime("%m")
		# get the year
		year = datetime.datetime.now().strftime("%Y")
		 #get the month name
		month_name = datetime.datetime.now().strftime("%B")
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
		return [day, month_num, year, month_name, 
			days_in_month, first_day, start_day]
	
	def on_draw(self, ctx):
		# get dates
		date = self.get_date_info()
		# set size
		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			# render bg
			self.theme.render(ctx, 'date-bg')
			#self.theme.render(ctx, 'date-border')
			ctx.save()
			ctx.translate(5,5)
			p_layout = ctx.create_layout()
			p_fdesc = pango.FontDescription("Free Sans 5")
			p_layout.set_font_description(p_fdesc)
			# draw the month
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup('<b>' + date[3] + '</b>')
			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.show_layout(p_layout)
			# draw the year
			ctx.translate(70, 0)
			p_layout.set_markup('<b>' + date[2] + '</b>')
			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.show_layout(p_layout)
			ctx.restore()
			ctx.save()
			ctx.translate(0,15)
			#draw the header background
			self.theme.render(ctx, 'header-bg')
			ctx.translate(8, 1)
			p_layout.set_markup('<b>' + "S    M    T    W    T    F    S" + \
				'</b>')
			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.show_layout(p_layout)
			ctx.restore()
			row = 1
			day = int(date[6])
			#print str(date[0])
			for x in range(date[4] + 1):
				ctx.save()
				ctx.translate(5 + (day-1)*13, 29 + 12*(row - 1))
				if str(int(x)+1) == str(date[0]) or \
					"0"+str(int(x)+1) == str(date[0]):
					self.theme.render(ctx, 'day-bg')
				if int(x)+1 < 10:
					# draw the days
					p_layout.set_markup('<b>' + " 0"+str(x+1) + '</b>')
				else:
					p_layout.set_markup('<b>' + " "+str(x+1) + '</b>')
				ctx.set_source_rgba(1, 1, 1, 0.8)
				ctx.show_layout(p_layout)
				if day == 7:
					day = 0
					row = row + 1
				day = day + 1
				ctx.restore()
		
	def on_draw_shape(self,ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			self.theme.render(ctx, 'date-bg')

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(CalendarScreenlet)

