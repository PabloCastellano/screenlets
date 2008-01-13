#!/usr/bin/env python

#  ClockScreenlet (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - python-version of MacSlow's cairo-clock (thanks, MacSlow :-) ...)
# - the themes cairo-clock, tango and funky are part of the cairo-clock
#   by MacSlow ... all credits to him :D
#
# TODO: 
# - more realistic shadow-placement for clock-hands
# - "shake"-effect for alarm-function
# - optimization of draw-handler
# - ?use third buffer for current hour/minute and (update once a minute)
# -

import screenlets
from screenlets import Screenlet
from screenlets.options import IntOption, BoolOption, TimeOption
from screenlets.options import StringOption, FontOption, ColorOption
from screenlets.services import ScreenletService

import pygtk
pygtk.require('2.0')
import gtk
import math
import cairo
import pango
from datetime import datetime
import gobject


# the service that implements the remote-actions for this screenlet
class ClockService (ScreenletService):
	"""A service for remote-controlling the ClockScreenlet. Defines custom
	actions and signals this Screenlet offers to the outer world."""
	
	# define our custom interface here
	IFACE 	= 'org.screenlets.Clock'
	
	# constructor
	def __init__ (self, clock):
		ScreenletService.__init__(self, clock, 'Clock')
	
	# defining an action (with support for multiple instances)
	@screenlets.services.action(IFACE)
	def get_time (self, id):
		"""This method returns the current time as string."""
		# get the instance with id
		sl = self.screenlet.session.get_instance_by_id(id)
		if sl:
			# and return its time
			return sl.get_time()
	
	# defining an action (with support for multiple instances)
	@screenlets.services.action(IFACE)
	def get_date (self, id):
		"""This method returns the current date as string."""
		sl = self.screenlet.session.get_instance_by_id(id)
		if sl:
			return sl.get_date()
	
	# defining a signal (can be just an empty function)
	@screenlets.services.signal(IFACE)
	def alarm_start (self, id):
		"""This signal is emitted whenever the Alarm starts."""

	# defining a signal (can be just an empty function)
	@screenlets.services.signal(IFACE)
	def alarm_stop (self, id):
		"""This signal is emitted whenever the Alarm ends."""


class ClockScreenlet (Screenlet):
	"""The Screenlet-version of MacSlow\'s cairo-clock. A themeable clock with 
	alarm-function and different timezones. The first Screenlet ever. Big thanks
	to MacSlow for showing how it works!"""
	
	# default meta-info for Screenlets
	__name__	= 'ClockScreenlet'
	__version__	= '0.6'
	__author__	= 'RYX (aka Rico Pfaus)'
	__desc__	= __doc__
	
	# internal vars
	__timeout		= None
	__buffer_back	= None
	__buffer_fore	= None
	__time = datetime.now()
	__alarm_running	= False
	__alarm_state	= 0
	__alarm_count	= 0
	
	# editable options
	time_offset		= 0
	face_text		= 'Screenlets'
	face_text_x		= 32
	face_text_y		= 59
	face_text_color	= (0.0, 0.0, 0.0, 0.3)
	face_text_font	= "Sans Medium 5"
	alarm_activated	= False
	alarm_time		= (7, 30, 0)
	alarm_length	= 500	# times to blink before auto-stop
	hour_format		= "12"
	show_date		= False
	date_format		= "%d/%m/%Y"
	show_seconds_hand = True
	alarm_command = 'firefox'
	run_command = False

	# constructor
	def __init__ (self, parent_window=None, **keyword_args):
		"""Create a new ClockScreenlet instance."""
		# call super (we define to use our own service here)
		Screenlet.__init__(self, uses_theme=True, service_class=ClockService,
			**keyword_args)
		# set default theme for this Screenlet (causes redraw)
		# TODO: check, if theme is valid??
		self.theme_name = "station"
		# set title
		#self.window.set_title('ClockScreenlet')
		#self.__time = None
		#self.time_offset = 0
		self.update()
		# update the clock once a second
		self.__timeout = gobject.timeout_add(1000, self.update)
		# create/add OptionGroups
		self.add_options_group('Clock', 'Clock-specific settings.')
		self.add_options_group('Alarm', 'Settings for the Alarm-function.')
		self.add_options_group('Face', 
			'Additional settings for the face-layout ...')
		# add editable settings to this Screenlet
		self.add_option(IntOption('Clock','time_offset', 
			0, 'Time-Offset', 'The-time offset for this Clock instance. ' + 
			'This can be used to create Clocks for different timezones ...',
			min=-12, max=12))
		self.add_option(StringOption('Clock','hour_format', 
			self.hour_format, 'Hour-Format', 
			'The hour-format (12/24) ...', choices=['12', '24']))
		self.add_option(BoolOption('Clock','show_seconds_hand', 
			self.show_seconds_hand, 'Show seconds-hand', 
			'Show/Hide the seconds-hand ...'))
		self.add_option(BoolOption('Alarm','alarm_activated', 
			self.alarm_activated, 'Activate Alarm', 
			'Activate the alarm for this clock-instance ...'))
		self.add_option(TimeOption('Alarm','alarm_time', self.alarm_time, 
 			'Alarm-Time', 'The time to run the alarm at (if active) ...'))
		self.add_option(IntOption('Alarm','alarm_length', 
			self.alarm_length, 'Alarm stops after', 
			'The times the clock shall blink before auto-stopped. ' + \
			'Divide the number by two to get the seconds ...', 
			min=0, max=5000))
		self.add_option(BoolOption('Alarm','run_command', 
			self.run_command, 'Run a command', 
			'Run a command when the alarm is activated...'))
		self.add_option(StringOption('Alarm','alarm_command', 
			self.alarm_command, 'Alarm command', 
			'The command that should be run when the alarm goes off...'))
 		self.add_option(StringOption('Face', 'face_text', 
			self.face_text, 'Face-Text', 
			'The text/Pango-Markup to be placed on the clock\'s face ...'))
		self.add_option(FontOption('Face', 'face_text_font', 
			self.face_text_font, 'Text-Font', 
			'The font of the text (when no Markup is used) ...'))
		self.add_option(ColorOption('Face', 'face_text_color', 
			self.face_text_color, 'Text-Color', 
			'The color of the text (when no Markup is used) ...'))
		self.add_option(IntOption('Face', 'face_text_x', 
			self.face_text_x, 'X-Position of Text', 
			'The X-Position of the text-rectangle\'s upper left corner ...', 
			min=0, max=100))
		self.add_option(IntOption('Face', 'face_text_y', 
			self.face_text_y, 'Y-Position of Text', 
			'The Y-Position of the text-rectangle\'s upper left corner ...', 
			min=0, max=100))
		self.add_option(BoolOption('Face', 'show_date', 
			self.show_date, 'Show today\'s date', 
			'Show date on the clock\'s face ...'))
		self.add_option(StringOption('Face', 'date_format', self.date_format, 
			'Date Format', 'Format of the date displayed by this Clock. '+\
			'Some vars are %d for day, %m for months and %Y for the year.'))
	
	
	def __setattr__ (self, name, value):
		super(ClockScreenlet, self).__setattr__(name, value)
		# check for other attribs	
		if name[:9]=="face_text" or name=='show_date' or \
			(name=='date_format' and self.show_date):
			# text-property? redraw background and redraw
			self.redraw_background()
			self.redraw_canvas()
		elif name == "alarm_activated" and value==False:
			if self.__alarm_running:
				self.stop_alarm()
		elif name == 'show_seconds_hand':
			if value == True:
				self.set_update_interval(1000)
			else:
				self.set_update_interval(20000)
			self.redraw_canvas()
	
	def get_date (self):
		"""Only needed for the service."""
		return self.__time.strftime(self.date_format)

	def get_time (self):
		"""Only needed for the service."""
		return self.__time.strftime("%h/%i/%s")
	
	def on_load_theme (self): 
		"""A Callback to do special actions when the theme gets reloaded.
		(called AFTER loading theme and BEFORE redrawing shape/canvas)"""
		self.init_buffers()
		self.redraw_foreground()
		self.redraw_background()
	
	def on_scale (self):
		"""Called when the scale-attribute changes."""
		if self.window:
			self.init_buffers()
			self.redraw_foreground()
			self.redraw_background()
	
	def init_buffers (self):
		"""(Re-)Create back-/foreground buffers"""
		self.__buffer_back = gtk.gdk.Pixmap(self.window.window, 
			int(self.width * self.scale), int(self.height * self.scale), -1)
		self.__buffer_fore = gtk.gdk.Pixmap(self.window.window, 
			int(self.width * self.scale), int(self.height * self.scale), -1)
		
	def redraw_foreground (self):
		"""Redraw the foreground-buffer (face-shadow, glass, frame)."""
		# create context from fg-buffer
		ctx_fore = self.__buffer_fore.cairo_create()
		# clear context
		self.clear_cairo_context(ctx_fore)
		# and compose foreground
		ctx_fore.scale(self.scale, self.scale)
		self.theme['clock-face-shadow.svg'].render_cairo(ctx_fore)
		self.theme['clock-glass.svg'].render_cairo(ctx_fore)
		self.theme['clock-frame.svg'].render_cairo(ctx_fore)
	
	def redraw_background (self):
		"""Redraw the background-buffer (drop-shadow, face, marks)."""
		# create context
		ctx_back = self.__buffer_back.cairo_create()
		# clear context
		self.clear_cairo_context(ctx_back)
		# compose background
		ctx_back.set_operator(cairo.OPERATOR_OVER)
		ctx_back.scale(self.scale, self.scale)
		self.theme['clock-drop-shadow.svg'].render_cairo(ctx_back)
		self.theme['clock-face.svg'].render_cairo(ctx_back)
		# override text with date?
		if self.show_date == True:
			#today = self.__time.strftime("%d/%m/%Y")
			txt = self.get_date() #self.__time.strftime("%d/%m/%Y")
		else:
			txt = self.face_text
		if self.face_text != '':
			# get pango layout for self.window
			ctx_back.save()
			ctx_back.translate(self.face_text_x, self.face_text_y)
			p_layout = ctx_back.create_layout()
			p_layout.set_width((self.width * pango.SCALE))
			om = '<span font_desc="'+self.face_text_font+'">'
			cm = '</span>'
			p_layout.set_markup(om + txt + cm)
			ctx_back.set_source_rgba(self.face_text_color[0], 
				self.face_text_color[1], self.face_text_color[2], 
				self.face_text_color[3])
			ctx_back.show_layout(p_layout)
			ctx_back.fill()
			ctx_back.restore()
			del p_layout
		self.theme['clock-marks.svg'].render_cairo(ctx_back)
	
	def start_alarm (self):
		"""Start the alarm-animation."""
		self.__alarm_running = True
		self.__alarm_count = self.alarm_length
		self.set_update_interval(500)
		if self.run_command == True and self.alarm_command != '':
			os.system(self.alarm_command)
		# send signal over service
		self.service.alarm_start(self.id)
	
	def stop_alarm (self):
		"""Stop the alarm-animation."""
		self.__alarm_running = False
		self.__alarm_count = 0
		self.set_update_interval(1000)
		# send signal over service
		self.service.alarm_stop(self.id)
	
	def set_update_interval (self, interval):
		"""Set the update-time in milliseconds."""
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(interval, self.update)
		
	def check_alarm (self):
		"""Checks current time with alarm-time and start alarm on match."""
		if self.__time.hour == self.alarm_time[0] and \
			self.__time.minute == self.alarm_time[1] and \
			self.__time.second == self.alarm_time[2]:
			self.start_alarm()
				
	def update (self):
		"""Update the time and redraw the canvas"""
		self.__time = datetime.now()
		if self.alarm_activated:
			self.check_alarm()
		if self.show_date:
			# accomodate date changes even after suspend/resume
			# (thanks to Rene Auberger :))
			if self.__time.second == 0:
				self.redraw_background()
		self.redraw_canvas()
		return True # keep running this event
	
	def on_init (self):
		print "OK - Clock has been initialized."
		# add default menuitems
		self.add_default_menuitems()
	def on_draw (self, ctx):
		# no theme? no drawing
		if self.theme==None:
			return
		# get dimensions
		x = (self.theme.width / 2.0) * self.scale
		y = (self.theme.height / 2.0) * self.scale
		radius = min(self.theme.width / 2.0, self.theme.height / 2.0) - 5
		# render background buffer to context
		if self.__buffer_back:
			ctx.set_operator(cairo.OPERATOR_OVER)
			ctx.set_source_pixmap(self.__buffer_back, 0, 0)
			ctx.paint()
		# calc. scale relative to theme proportions
		ctx_w = self.scale
		ctx_h = self.scale
		# init time-vars
		hours = self.__time.hour + self.time_offset
		minutes = self.__time.minute
		seconds = self.__time.second
		# TODO: use better shadow-placing
		shadow_offset_x = 1
		shadow_offset_y = 1
		# set hour-format specific vars
		if self.hour_format=="24":
			hf = 12.0
			hr = 720.0
		else:
			hf = 6.0
			hr = 360.0
		ctx.set_operator(cairo.OPERATOR_OVER)
		# render hour-hand-shadow
		ctx.save()
		ctx.translate (x+shadow_offset_x, y+shadow_offset_y)
		ctx.rotate(-math.pi/2.0)
		ctx.scale(ctx_w, ctx_h)
		ctx.rotate ((math.pi/hf) * hours + (math.pi/hr) * minutes)
		self.theme['clock-hour-hand-shadow.svg'].render_cairo(ctx)
		ctx.restore()
		# render hour-hand
		ctx.save()
		ctx.translate (x, y)
		ctx.rotate(-math.pi/2.0)
		ctx.scale(ctx_w, ctx_h)
		ctx.rotate ((math.pi/hf) * hours + (math.pi/hr) * minutes)
		self.theme['clock-hour-hand.svg'].render_cairo(ctx)
		ctx.restore()
		# render minutes-hand-shadow
		ctx.save()
		ctx.translate (x+shadow_offset_x, y+shadow_offset_y)
		ctx.rotate(-math.pi/2.0)
		ctx.scale(ctx_w, ctx_h)
		ctx.rotate((math.pi/30.0) * minutes)
		self.theme['clock-minute-hand-shadow.svg'].render_cairo(ctx)
		ctx.restore()
		# render minutes-hand
		ctx.save()
		ctx.translate(x, y);
		ctx.rotate(-math.pi/2.0)
		ctx.scale(ctx_w, ctx_h)
		ctx.rotate((math.pi/30.0) * minutes)
		self.theme['clock-minute-hand.svg'].render_cairo(ctx)
		ctx.restore()
		# render seconds-hand
		if self.show_seconds_hand:
			ctx.save()
			ctx.translate(x, y);
			ctx.rotate(-math.pi/2.0)
			ctx.set_source_rgba(0, 0, 0, 0.3)
			ctx.scale(ctx_w, ctx_h)
			ctx.rotate((math.pi/30.0) * seconds)
			ctx.translate(-shadow_offset_x, -shadow_offset_y)
			ctx.set_operator(cairo.OPERATOR_OVER)
			self.theme['clock-second-hand-shadow.svg'].render_cairo(ctx)
			ctx.translate(shadow_offset_x, shadow_offset_y)
			self.theme['clock-second-hand.svg'].render_cairo(ctx)
			ctx.restore()
		# render foreground-buffer to context
		if self.__buffer_fore:
			ctx.set_operator(cairo.OPERATOR_OVER)
			ctx.set_source_pixmap(self.__buffer_fore, 0, 0)
			ctx.paint()
		# alarm-function
		if self.alarm_activated:
			if self.__alarm_running:
				ctx.set_operator(cairo.OPERATOR_ATOP)
				if self.__alarm_state == 1:
					ctx.set_source_rgba(1, 1, 1, 0.5)
					self.__alarm_state = 0
				else:
					ctx.set_source_rgba(0, 0, 0, 0.1)
					self.__alarm_state = 1
				ctx.paint()
				self.__alarm_count -= 1
				if self.__alarm_count == 0:
					self.stop_alarm()
			
	def on_draw_shape (self,ctx):
		if self.__buffer_back:
			ctx.set_operator(cairo.OPERATOR_OVER)
			ctx.set_source_pixmap(self.__buffer_back, 0, 0)
			ctx.paint()
			ctx.set_source_pixmap(self.__buffer_fore, 0, 0)
			ctx.paint()

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(ClockScreenlet)

