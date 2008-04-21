#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  ClearCalendarScreenlet (c) Whise aka Helder Fraga


import screenlets
from screenlets.options import StringOption, BoolOption
import cairo
import pango
import gtk
import gobject
import datetime
import locale
from iCal import ICalReader
import sys


class ClearCalendarScreenlet(screenlets.Screenlet):
	"""A simple multilingual iCalendar Screenlet with month preview, you can scroll through other months too and view monthly events."""
	
	# default meta-info for Screenlets
	__name__ = 'ClearCalendarScreenlet'
	__version__ = '0.4'
	__author__ = 'Helder Fraga aka Whise based on calendar Screenlet by robgig1088'
	__desc__ = 'A simple multilingual iCalendar Screenlet with month preview, you can scroll through other months too and view monthly events.'

	# internals
	__timeout = None
	__first_day = 0
	__day_names = []


	__buttons_pixmap = None
	__buttons_alpha = 0
	__buttons_timeout = None
	__button_pressed = 0
	__month_shift = 0

	# settings
	update_interval = 10
	first_weekday = ''
	enable_buttons = True
	reader = ICalReader()
	event1 = ''


	showevents = True
	today=datetime.datetime.now().strftime("%F")
	mypath = sys.argv[0][:sys.argv[0].find('ClearCalendarScreenlet.py')].strip()
	icalpath = mypath + 'calendar.ics'
	# constructor
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=int(102*2), height=int(105*2),uses_theme=True, **keyword_args) 
		# get localized day names
		locale.setlocale(locale.LC_ALL, '');
		# we convert to unicode here for the first letter extraction to work well
		self.__day_names = [locale.nl_langinfo(locale.DAY_1 + i).decode() for i in range(7)] 
		self.first_weekday = self.__day_names[self.__first_day]
		# call super (and not show window yet)
		# set theme
		self.add_menuitem("icspath", "Ics file path")	
		self.add_menuitem("events", "View events")
		self.add_menuitem("mini", "Toggle view events")
		self.add_menuitem("update", "Update events")	
		self.theme_name = "default"
		# add settings
		self.add_options_group('iCalendar', 'Calendar specific options')
		self.add_option(StringOption('iCalendar', 'first_weekday', self.first_weekday,
			'First Weekday', 'The day to be shown in the leftmost column',
			choices = self.__day_names))
		self.add_option(BoolOption('iCalendar', 'enable_buttons', self.enable_buttons, 
			'Enable month shifting', 'Enable buttons selecting another months'))
		self.add_option(StringOption('iCalendar', 'icalpath', self.icalpath, 'iCalendar ics file path', 'The full path where the .ics file is located , local or url) ...'), realtime=False)
		self.add_option(BoolOption('iCalendar', 'showevents',bool(self.showevents), 'Show iCalendar events','Show iCalendar events'),realtime=False)
		# init the timeout functions
		self.update_interval = self.update_interval
		self.enable_buttons = self.enable_buttons
		self.reader.readURL(self.icalpath)
		self.showevents = self.showevents
	# attribute-"setter", handles setting of attributes
	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# check for this Screenlet's attributes, we are interested in:
		if name == ('icalpath'):
			self.reader = ICalReader()
			self.reader.readURL(self.icalpath)
			if self.window:
				self.redraw_canvas()
		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(value 
						* 1000, self.update)
			else:
				# TODO: raise exception!!!
				pass
		elif name == 'first_weekday':
			self.__first_day\
				= self.__day_names.index(self.first_weekday)
			self.update()
		elif name == 'enable_buttons':
			self.__dict__['enable_buttons'] = value
			if value == True and not self.__buttons_timeout:
				self.__buttons_timeout = gobject.timeout_add(100, 
						self.update_buttons)
			elif value == False and self.__buttons_timeout:
				gobject.source_remove(self.__buttons_timeout)
				self.__buttons_timeout = None
				self.__buttons_alpha = 0
				self.update()
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()	
	
	def get_date_info(self):
		today = datetime.datetime.now()
		day = today.day
		month = today.month
		year = today.year
		# apply month shift
		if self.__month_shift:
			month += self.__month_shift
			if month > 12:
				year += int((month - 1) / 12)
				month -= (year - today.year) * 12
			elif month <= 0:
				year -= int((12 - month) / 12)
				month += (today.year - year) * 12
		# get first day of the updated month
		month_num = datetime.datetime.now().strftime("%m")
		first_day = datetime.date(year, month, 1)
		# get the month name
		month_name = first_day.strftime("%B")
		month_num = first_day.strftime("%m")
		# get the day count
		when = datetime.date(int(year), int(month), int(1))
		# get the first day of the month (mon, tues, etc..)
		first_day = when.strftime("%A")
		# find number of days in the month
		if month in (1, 3, 5, 7, 8, 10, 12):
			days_in_month = 31
		elif month <> 2:
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
	
		# return as array
		return [day, year, month_name, days_in_month, start_day,month_num]

	def on_map(self):
		if not self.__timeout:
			self.__timeout = gobject.timeout_add(self.__dict__['update_interval']
						* 1000, self.update)
		if self.__dict__['enable_buttons'] == True and not self.__buttons_timeout:
			self.__buttons_timeout = gobject.timeout_add(100, 
					self.update_buttons)
 
	def on_unmap(self):
		if self.__timeout:
			gobject.source_remove(self.__timeout)
			self.__timeout = None
		if self.__buttons_timeout:
			gobject.source_remove(self.__buttons_timeout)
			self.__buttons_timeout = None

	# timeout-functions
	def update(self):
		self.icalpath = self.icalpath
		self.redraw_canvas()
		return True

	def update_buttons(self):
		x, y = self.window.get_pointer()
		x /= (2*self.scale)
		y /= (2*self.scale)
		al_last = self.__buttons_alpha
		if x >= 0 and x < 100 and y >= 0 and y <= 15:	# top line
			self.__buttons_alpha = min(self.__buttons_alpha + 0.2, 1.0)
		else:
			self.__buttons_alpha = max(self.__buttons_alpha - 0.2, 0.0)
		if self.__buttons_alpha != al_last:
			self.redraw_canvas()
		return True

	def on_load_theme(self):
		self.init_buttons()

	def on_scale(self):

		if self.window:
			self.init_buttons()

	# redraw button buffer. FIXME: the pixmap is used to enable alpha-rendering of the SVGs.
	def init_buttons(self):
		if self.__buttons_pixmap:
			del self.__buttons_pixmap
		self.__buttons_pixmap = gtk.gdk.Pixmap(self.window.window, int(self.width 
			* (2*self.scale)), int(self.height * (2*self.scale)), -1)
		ctx = self.__buttons_pixmap.cairo_create()
		self.clear_cairo_context(ctx)
		ctx.scale(2 *self.scale, 2* self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)
		self.theme['buttons-dim.svg'].render_cairo(ctx)
		ctx.translate(0, 50)	# bottom half
		self.theme['buttons-press.svg'].render_cairo(ctx)
		del ctx

	def on_mouse_down(self, event):
		if self.enable_buttons and event.button == 1:
			if event.type == gtk.gdk.BUTTON_PRESS:
				return self.detect_button(event.x, event.y)
			else:
				return True
		return False

	def on_mouse_up(self, event):
		# do the active button's action
		if self.__button_pressed:
			if self.__button_pressed == 1:
				self.__month_shift -= 1
			elif self.__button_pressed == 2:
				self.__month_shift = 0
			elif self.__button_pressed == 3:
				self.__month_shift += 1
			self.__button_pressed = 0
			self.redraw_canvas()
		return False

	def detect_button(self, x, y):
		x /= (2*self.scale)
		y /= (2*self.scale)

		button_det = 0
		if y >= 5.5 and y <= 12.5:
			if x >= 8.5 and x <= 15.5:
				button_det = 1
			elif x >= 18.5 and x <= 25.5:
				button_det = 2
			elif x >= 28.5 and x <= 35.5:
				button_det = 3
		self.__button_pressed = button_det
		if button_det:
			self.redraw_canvas()
			return True	# we must return boolean for Screenlet.button_press
		else:
			return False

	def menuitem_callback(self, widget, id):
		screenlets.Screenlet.menuitem_callback(self, widget, id)

		if id == "events":
			screenlets.show_message(self,self.event1)
			self.redraw_canvas()
		if id=="icspath":
			self.show_edit_dialog()
			


		if id == "mini":
			self.showevents = not self.showevents
			self.redraw_canvas()
	
		if id=="update":
			
			self.update()
	
	def on_draw(self, ctx):
		# get data
		date = self.get_date_info() # [day, year, month_name, days_in_month, start_day]
		# set size
		ctx.scale(2*self.scale, 2*self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			self.theme['date-bg.svg'].render_cairo(ctx)
			#self.theme['date-border.svg'].render_cairo(ctx)
		# draw buttons and optionally the pressed one
		if self.__buttons_pixmap:
			ctx.save()
			ctx.rectangle(0, 0, 100, 15)
			ctx.clip()
			ctx.identity_matrix()
			ctx.set_source_pixmap(self.__buttons_pixmap, 0, 0)
			ctx.paint_with_alpha(self.__buttons_alpha)
			ctx.restore()
			if self.__button_pressed:
				ctx.save()
				ctx.rectangle(26.5 + self.__button_pressed * 10, 0, 10, 15)
				ctx.clip()
				ctx.identity_matrix()
				# use bottom half of the pixmap
				ctx.set_source_pixmap(self.__buttons_pixmap, 0, -50 * 2* self.scale)
				ctx.paint()
				ctx.restore()
				
		# draw the calendar foreground
		if self.theme:
			ctx.save()
			ctx.translate(5,5)
			p_layout = ctx.create_layout()
			p_fdesc = pango.FontDescription()
			p_fdesc.set_family_static("Tahoma")
			p_fdesc.set_size(5 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)      ### draw the month
			p_layout.set_width((self.width - 10) * pango.SCALE)
			p_layout.set_markup('<b>' + date[2] + '</b>')
			ctx.set_source_rgba(1, 1, 1, 0.8)
			
			
			#ctx.show_layout(p_layout)
		
			ctx.translate(-100,0)
			p_layout.set_width((self.width - 10) * pango.SCALE)
			p_layout.set_alignment(pango.ALIGN_RIGHT)
			p_layout.set_markup("<b>" + date[2]+' '+ str(date[1])+ '  </b>') ### draw the year
			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.show_layout(p_layout)

			ctx.restore()
			ctx.save()

			ctx.translate(0, 15)
			#self.theme['header-bg.svg'].render_cairo(ctx)  #draw the header background
			ctx.translate(6, 0)
			p_fdesc.set_size(4 * pango.SCALE)
			p_layout.set_font_description(p_fdesc) 
			#Draw header
			p_layout.set_alignment(pango.ALIGN_CENTER);
			p_layout.set_width(10*pango.SCALE);
			self.event1 = ''
			for i in range(7):
				dayname = self.__day_names[(i \
					+ self.__first_day) % 7]
				p_layout.set_markup("<b><span font_desc='Monospace'>" + dayname[:3] + '</span></b>') # use first letter
				ctx.set_source_rgba(1, 1, 1, 0.8)
				ctx.show_layout(p_layout)
				ctx.translate(13, 0)	# 6 + 6*13 + 6 = 100
			p_fdesc.set_size(6 * pango.SCALE)
			p_fdesc.set_family_static("Free Sans")

			p_layout.set_font_description(p_fdesc) 
			# Draw the day labels
			ctx.restore()
			row = 1

			day = (int(date[4]) + 7 - self.__first_day)%7
			if day == 0 :
				day = 7
			for x in range(date[3]):
				ctx.save()

				if row == 6:
					row = 1
				ctx.translate(6 + (day - 1)*13, 25 + 12*(row - 1))
				#print str(6 + (day - 1)*13)
				#print str( 25 + 12*(row - 1))
				if self.__month_shift == 0 and int(x)+1 == int(date[0]):
					self.theme['day-bg1.svg'].render_cairo(ctx)
				if self.showevents == True:
					for event in self.reader.events:
						
						myevent = str(event.startDate)
						myevent  = myevent[:myevent.find(' ')].strip()
	
						a = str(x +1)
						if len(a) == 1:
							a = '0' + a
					
						if myevent == str(date[1]) + '-' + str(date[5])+ '-' + str(a) :
							self.theme['day-bg.svg'].render_cairo(ctx)
							if int(date[1]) >= int(self.today[:4]) or int(date[1]) >= int(self.today[:4]) and int(date[5]) >= int(self.today[5:7]) :
								
								self.event1 = self.event1 + '\n'+ str(date[1]) + '-' + str(date[5])+ '-' + str(a)+ ' - ' +str(event)
						if myevent == datetime.datetime.now().strftime("%F") and self.__month_shift == 0 and int(x)+1 == int(date[0]) :
							self.theme['day-bg2.svg'].render_cairo(ctx)
							self.event1 = self.event1 + '\n Today - '+ str(event)
				p_layout.set_markup( str(x+1) )
	
				ctx.set_source_rgba(1, 1, 1, 1)
				ctx.show_layout(p_layout)
				if day == 7:
					day = 0
					row = row + 1
				day = day + 1
				ctx.restore()

	def show_edit_dialog(self):
		# create dialog
		dialog = gtk.Dialog("iCalendar ics path", self.window)
		dialog.resize(300, 100)
		dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, 
			gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		entrybox = gtk.Entry()
		entrybox.set_text(str(self.icalpath))
		dialog.vbox.add(entrybox)
		entrybox.show()	
		# run dialog
		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			self.icalpath = entrybox.get_text()
			self.updated_recently = 1
		dialog.hide()
		self.update()

	def on_draw_shape(self,ctx):
		if self.theme:
			# set size rel to width/height
			ctx.scale(2*self.scale, 2*self.scale)
			self.theme['date-bg.svg'].render_cairo(ctx)
	

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(ClearCalendarScreenlet)
