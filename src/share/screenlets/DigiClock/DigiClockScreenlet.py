#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  DigiClockScreenlet (c) Whise 2007 

import screenlets
from screenlets.options import ColorOption , BoolOption, FontOption
from screenlets import DefaultMenuItem , sensors
import pango
import gobject
import random
import gtk
import cairo
import gconf

class DigiClockScreenlet (screenlets.Screenlet):
	"""A Screenlet that allows to instantly change metacity composite state"""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'DigiClockScreenlet'
	__version__	= '0.1'
	__author__	= 'Helder Fraga aka Whise'
	__desc__	= __doc__	# set description to docstring of class
	
	# editable options (options that are editable through the UI)
	frame_color = (1, 1, 1, 1)
	color_text = (0, 0, 0, 0.6)
	use_gradient = True
	composite_enabled = True
	time = ''
	date = ''
	font= "FreeSans"
	use_ampm = False
	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=150, height=70, 
			uses_theme=True,ask_on_option_override=False, **keyword_args)
		# set theme
		
		#self.theme_name = "default"
		# add option group
		self.add_options_group('Options', 'Options')

		self.add_option(ColorOption('Options','frame_color', 
			self.frame_color, 'Frame color', 
			'Frame color'))



		self.add_option(BoolOption('Options', 'use_ampm',bool(self.use_ampm), 'Use am/pm','Use am/pm'))		# ADD a 1 second (1000) TIMER

		self.add_option(FontOption('Options','font', 
			self.font, 'Text Font', 
			'Text font'))
		self.add_option(ColorOption('Options','color_text', 
			self.color_text, 'Text color', ''))

		self.timer = gobject.timeout_add( 1000, self.update)
		self.update()

	def update (self):
		if self.use_ampm:
			self.time = str(sensors.cal_get_hour12()) + ':' + str(sensors.cal_get_minute()) + ':' + str(sensors.cal_get_second())
		else:
			self.time = str(sensors.cal_get_hour24()) + ':' + str(sensors.cal_get_minute()) + ':' + str(sensors.cal_get_second())
		self.date = str(sensors.cal_get_local_date())

		self.redraw_canvas()
		return True # keep running this event	
	
	# ONLY FOR TESTING!!!!!!!!!
	def init_options_from_metadata (self):
		"""Try to load metadata-file with options. The file has to be named
		like the Screenlet, with the extension ".xml" and needs to be placed
		in the Screenlet's personal directory. 
		NOTE: This function always uses the metadata-file relative to the 
			  Screenlet's location, not the ones in SCREENLETS_PATH!!!"""
		print __file__
		p = __file__.rfind('/')
		mypath = __file__[:p]
		print mypath
		self.add_options_from_file( mypath + '/' + \
			self.__class__.__name__ + '.xml')	


	def on_after_set_atribute(self,name, value):
		"""Called after setting screenlet atributes"""
		
		pass

	def on_before_set_atribute(self,name, value):
		"""Called before setting screenlet atributes"""
		
		pass


	def on_create_drag_icon (self):
		"""Called when the screenlet's drag-icon is created. You can supply
		your own icon and mask by returning them as a 2-tuple."""
		return (None, None)

	def on_composite_changed(self):
		"""Called when composite state has changed"""
		pass

	def on_drag_begin (self, drag_context):
		"""Called when the Screenlet gets dragged."""
		pass
	
	def on_drag_enter (self, drag_context, x, y, timestamp):
		"""Called when something gets dragged into the Screenlets area."""
		pass
	
	def on_drag_leave (self, drag_context, timestamp):
		"""Called when something gets dragged out of the Screenlets area."""
		pass

	def on_drop (self, x, y, sel_data, timestamp):
		"""Called when a selection is dropped on this Screenlet."""
		return False
		
	def on_focus (self, event):
		"""Called when the Screenlet's window receives focus."""
		pass
	
	def on_hide (self):
		"""Called when the Screenlet gets hidden."""
		pass
	
	def on_init (self):
		"""Called when the Screenlet's options have been applied and the 
		screenlet finished its initialization. If you want to have your
		Screenlet do things on startup you should use this handler."""
		
		# add default menu items
		self.add_default_menuitems()


	def on_key_down(self, keycode, keyvalue, event):
		"""Called when a keypress-event occured in Screenlet's window."""

		
		pass
	
	def on_load_theme (self):
		"""Called when the theme is reloaded (after loading, before redraw)."""
		pass
	
	def on_menuitem_select (self, id):
		"""Called when a menuitem is selected."""
		
		pass
	



	def on_mouse_move(self, event):
		"""Called when the mouse moves in the Screenlet's window."""

		pass

	def on_mouse_up (self, event):
		"""Called when a buttonrelease-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		return False
	

		
	def on_realize (self):
		""""Callback for handling the realize-event."""
	
	def on_scale (self):
		"""Called when Screenlet.scale is changed."""
		pass
	
	def on_scroll_up (self):
		"""Called when mousewheel is scrolled up (button4)."""
		pass

	def on_scroll_down (self):
		"""Called when mousewheel is scrolled down (button5)."""
		pass
	
	def on_show (self):
		"""Called when the Screenlet gets shown after being hidden."""
		pass
	
	def on_switch_widget_state (self, state):
		"""Called when the Screenlet enters/leaves "Widget"-state."""
		pass
	
	def on_unfocus (self, event):
		"""Called when the Screenlet's window loses focus."""
		pass
	
	def on_draw (self, ctx):
		"""In here we draw"""
		ctx.scale(self.scale,self.scale)
		if self.use_gradient:
			gradient = cairo.LinearGradient(0, self.height*2,0, 0)
			gradient.add_color_stop_rgba(1,*self.frame_color)
			gradient.add_color_stop_rgba(0.7,self.frame_color[0],self.frame_color[1],self.frame_color[2],1-self.frame_color[3]+0.5)

			ctx.set_source(gradient)
		else:
			ctx.set_source(self.frame_color)
		self.draw_rectangle_advanced (ctx, 0, 0, self.width-12, self.height-12, rounded_angles=(5,5,5,5), fill=True, border_size=2, border_color=(0,0,0,0.5), shadow_size=6, shadow_color=(0,0,0,0.5))
		ctx.set_source_rgba(self.color_text[0],self.color_text[0],self.color_text[0],0.05)
		self.draw_text(ctx,'88:88:88', 0, 20, self.font.split(' ')[0], 21, self.width, pango.ALIGN_CENTER)
		ctx.set_source_rgba(*self.color_text)

		if not self.use_ampm:
			self.draw_text(ctx, self.time, 0, 20, self.font.split(' ')[0], 21, self.width, pango.ALIGN_CENTER)

		else:

			b = sensors.cal_get_ampm()
			if b == '':
				h = sensors.cal_get_hour ()
				if int(h)>12: 
					b = 'PM'
				else:
					b = 'AM'
				
			else: 
				self.am=True
				self.pm=False
			self.draw_text(ctx, self.time, 0, 20, self.font.split(' ')[0], 21, self.width, pango.ALIGN_CENTER)
			self.draw_text(ctx, b, -8, 36, self.font.split(' ')[0], 6, self.width, pango.ALIGN_RIGHT)
		ctx.set_source_rgba(self.color_text[0],self.color_text[0],self.color_text[0],0.05)
		self.draw_text(ctx, '88:88:88', 0, 46, self.font.split(' ')[0], 9, self.width, pango.ALIGN_CENTER)
		ctx.set_source_rgba(*self.color_text)
		self.draw_text(ctx, self.date, 0, 46, self.font.split(' ')[0], 9, self.width, pango.ALIGN_CENTER)		

	def on_draw_shape (self, ctx):
		self.on_draw(ctx)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(DigiClockScreenlet)

