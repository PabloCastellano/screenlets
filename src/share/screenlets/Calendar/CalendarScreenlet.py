#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  CalendarScreenlet (c)  Whise 2008 original by RYX
#
# INFO:
# - 
#

import screenlets
import cairo
import pango
import datetime
import locale
from screenlets.options import ColorOption

import commands

class CalendarScreenlet (screenlets.Screenlet):
	"""A simple Calendar Screenlet."""
	
	# default meta-info for Screenlets
	__name__	= 'CalendarScreenlet'
	__version__	= '0.3'
	__author__	= ' Whise aka helder Fraga original version by RYX'
	__desc__	= __doc__

	p_layout1 = None
	font_color = (1,1,1, 0.8)
	today_color = (0.5,0.5,0.5, 0.8)
	__day_names = None
	f = "FreeSans 9"
	# constructor
	def __init__(self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, uses_theme=True,width=130,height=141, **keyword_args)
		# set some options
		self.text_shadow_offset = 0.666
		# set theme
		locale.setlocale(locale.LC_ALL, '');
		# we convert to unicode here for the first letter extraction to work well
		self.__day_names = [locale.nl_langinfo(locale.DAY_1 + i).decode() for i in range(7)] 

		self.theme_name = "ryx"
		self.add_options_group('Calendar', 'Calendar specific options')
		self.add_option(ColorOption('Calendar','font_color', 
			self.font_color, 'Text color', 'font_color'))
		self.add_option(ColorOption('Calendar','today_color', 
			self.today_color, 'Today color', 'today_color'))


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
		ctx.translate(5 + self.text_shadow_offset, 7 + self.text_shadow_offset)
		# draw the month
		pl.set_width((self.width) * pango.SCALE)
		pl.set_markup('<b>' + month + '</b>')
		ctx.set_source_rgba(0, 0, 0, 0.3)
		ctx.show_layout(pl)
		ctx.translate(-self.text_shadow_offset, -self.text_shadow_offset)
		ctx.set_source_rgba(*self.font_color)
		ctx.show_layout(pl)
		# draw the year
		ctx.translate(91 + self.text_shadow_offset, self.text_shadow_offset)
		pl.set_markup('<b>' + year + '</b>')
		ctx.set_source_rgba(0, 0, 0, 0.3)
		ctx.show_layout(pl)
		ctx.translate(-self.text_shadow_offset, -self.text_shadow_offset)
		ctx.set_source_rgba(*self.font_color)
		ctx.show_layout(pl)
		ctx.restore()
	
	def draw_header (self, ctx, pl):
		ctx.save()
		tso = self.text_shadow_offset
		ctx.translate(5,24)
		for i in range(7):

			ctx.set_source_rgba(0, 0, 0, 0.3)
			ctx.translate(tso, tso)
			self.draw_text(ctx, self.__day_names[i][:2] , 0, 0, 'FreeSans',9, self.width , pango.ALIGN_LEFT)
			ctx.translate(-tso, -tso)
			ctx.set_source_rgba(*self.font_color)
			self.draw_text(ctx, self.__day_names[i][:2] , 0, 0, 'FreeSans',9, self.width , pango.ALIGN_LEFT)
			ctx.translate(17.5,0)
		ctx.restore()

	
	def draw_days (self, ctx, pl, date):
		#ctx.translate(-5, 0)
		row = 1
		day = int(date[6])
		tso = self.text_shadow_offset
		for x in range(date[4] + 1):
			ctx.save()
			ctx.translate(2 + (day-1) * 17.5 + tso, 36 + 16.5 * (row - 1) + tso)
			if str(int(x)+1) == str(date[0]) or \
				"0" + str(int(x)+1) == str(date[0]):
				ctx.save()
				ctx.translate(0, -1)
				ctx.set_source_rgba(*self.today_color)
				self.draw_rounded_rectangle(ctx,2,0,2,15,12)
				#self.theme.render(ctx, 'calendar-day-bg')
				ctx.restore()
			if int(x)+1 < 10:
				# draw the days
				pl.set_markup('<b>' + " 0" + str(x+1) + '</b>')
			else:
				pl.set_markup('<b>' + " " + str(x+1) + '</b>')
			ctx.set_source_rgba(0, 0, 0, 0.3)
			ctx.show_layout(pl)
			ctx.translate(-tso, -tso)
			ctx.set_source_rgba(*self.font_color)
			ctx.show_layout(pl)
			if day == 7:
				day = 0
				row = row + 1
			day = day + 1
			ctx.restore()

	def on_mouse_enter(self,event):
		self.redraw_canvas()

	def on_mouse_leave(self,event):
		self.redraw_canvas()

	def on_draw (self, ctx):
		# get dates
		tso = self.text_shadow_offset
		date = self.get_date_info()
		# set size
		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.p_layout1 == None :
	
			self.p_layout1 = ctx.create_layout()
		else:
		
			ctx.update_layout(self.p_layout1)
		if self.theme:
			# render bg

			self.theme.render(ctx, 'calendar-bg')
			# create layout
			if self.mouse_is_over:
				ctx.save()

				ctx.translate(0,7)

				self.p_layout1 = ctx.create_layout()
				p_fdesc = pango.FontDescription("FreeSans 9")
				self.p_layout1.set_font_description(p_fdesc)

				# draw year/month
				self.draw_year_and_month(ctx, self.p_layout1, date[2], date[3])
				# draw header
				self.draw_header(ctx, self.p_layout1)
				# draw days
				self.draw_days(ctx, self.p_layout1, date)
				ctx.restore()
				ctx.scale(self.scale, self.scale)
			else:


				ctx.set_source_rgba(0, 0, 0, 0.3)
				ctx.translate(tso, tso)
				self.draw_text(ctx, date[0] , 0, 38, 'FreeSans', 60, self.width , pango.ALIGN_CENTER)
				ctx.translate(-tso, -tso)
				ctx.set_source_rgba(*self.font_color)
				self.draw_text(ctx, date[0] , 0, 38, 'FreeSans', 60, self.width , pango.ALIGN_CENTER)

				ctx.set_source_rgba(0, 0, 0, 0.3)
				ctx.translate(tso, tso)
				self.draw_text(ctx, str(date[3])+ ' ' + str(date[2]) , 0, 20, 'FreeSans', 10, self.width , pango.ALIGN_CENTER)
				ctx.translate(-tso, -tso)
				ctx.set_source_rgba(*self.font_color)
				self.draw_text(ctx, str(date[3])+ ' ' + str(date[2]) , 0, 20, 'FreeSans', 10, self.width , pango.ALIGN_CENTER)

				ctx.set_source_rgba(0, 0, 0, 0.3)
				o = commands.getoutput('date +%A')
				ctx.translate(tso, tso)
				self.draw_text(ctx, o, 0, 118, 'FreeSans', 10, self.width , pango.ALIGN_CENTER)
				ctx.translate(-tso, -tso)
				ctx.set_source_rgba(*self.font_color)

				self.draw_text(ctx, o, 0, 118, 'FreeSans', 10, self.width , pango.ALIGN_CENTER)
		
	def on_draw_shape(self,ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			self.theme.render(ctx, 'calendar-bg')

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(CalendarScreenlet)

