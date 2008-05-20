#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# OutputScreenlet (c) Whise <helder.fraga@hotmail.com>
#
# INFO:
# - A screenlet that searches the most popular search engines sites


import screenlets
from screenlets.options import ColorOption, StringOption, IntOption
import cairo
import pango
import gtk
import gobject
from screenlets import DefaultMenuItem 
import commands



class OutputScreenlet(screenlets.Screenlet):
	"""A screenlet displays output from any unix command"""
	
	# default meta-info for Screenlets
	__name__ = 'OutputScreenlet'
	__version__ = '0.1'
	__author__ = 'Helder Fraga aka whise'
	__desc__ = 'A screenlet displays output from any unix command'

	# a list of the converter class objects
	__timeout = None
	update_interval = 5
	__has_focus = False
	__query = ''
	frame_color = (0, 0, 0, 0.7)
	iner_frame_color = (0,0,0,0.3)
	shadow_color = (0,0,0,0.5)
	text_color = (1,1,1, 0.7)
	# editable options
	# the name, i.e., __title__ of the active converter
	p_fdesc = None
	p_layout = None
	run = 'dmesg'
	output = ''
	ctxx = None
	w = 350
	h = 100
	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=350, height=100,ask_on_option_override = False, 
				**keyword_args)
		# set theme
		self.theme_name = "default"

		# add options
		self.add_options_group('Options', 'Options')
		self.add_option(StringOption('Options', 'run', 
			self.run, 'Command to run', 
			'Command to run'), realtime=False)

		self.add_option(IntOption('Options', 'update_interval', 
			self.update_interval, 'Update interval seconds', 
			'The interval for refreshing RSS feed (in seconds)', min=1, max=10000))

		self.add_option(IntOption('Options', 'w', 
			self.w, 'Width', 
			'width', min=10, max=10000))


		self.add_option(IntOption('Options', 'h', 
			self.h, 'Height', 
			'height', min=10, max=10000))


		self.add_option(ColorOption('Options','frame_color', 
			self.frame_color, 'Background Frame color', 
			'Frame color'))

		self.add_option(ColorOption('Options','iner_frame_color', 
			self.iner_frame_color, 'Iner Frame color', 
			'Iner Frame color'))

		self.add_option(ColorOption('Options','shadow_color', 
			self.shadow_color, 'Shadow color', 
			'Shadow color'))

		self.add_option(ColorOption('Options','text_color', 
			self.text_color, 'Text color', 
			'Text color'))

		self.__timeout = gobject.timeout_add(1000, self.update)
		self.update()

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(int(value * 1000), self.update)
			else:
				self.__dict__['update_interval'] = 1
				pass
		if name == 'w':
			self.width = value
		if name == 'h':
			self.height = value
		if name == 'run':
			self.update()


	def on_init(self):
		
		self.add_default_menuitems()




	def update(self):
		self.output = commands.getoutput(self.run).replace('&','').replace('<','').replace('@','')
		if len(self.output) > 300:
			self.output = self.output[len(self.output)-300:]
		self.redraw_canvas()
		return True
			
	def on_draw(self, ctx):
		self.ctxx = ctx
		# if a converter or theme is not yet loaded, there's no way to continue
		# set scale relative to scale-attribute
		ctx.scale(self.scale, self.scale)
		# render background
		ctx.set_source_rgba(*self.frame_color)
		self.draw_rectangle_advanced (ctx, 0, 0, self.width-12, self.height-12, rounded_angles=(5,5,5,5), fill=True, border_size=2, border_color=(self.iner_frame_color[0],self.iner_frame_color[1],self.iner_frame_color[2],self.iner_frame_color[3]), shadow_size=6, shadow_color=(self.shadow_color[0],self.shadow_color[1],self.shadow_color[2],self.shadow_color[3]))
		#self.theme['background.svg'].render_cairo(ctx)
		# compute space between fields
		ctx.set_source_rgba(*self.text_color)
		self.draw_text(ctx, str(self.output), 10,10,  'FreeSans',8, self.width-20,allignment=pango.ALIGN_LEFT,justify = True,weight = 0)

	
	def on_draw_shape(self, ctx):
		self.on_draw(ctx)



# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(OutputScreenlet)
