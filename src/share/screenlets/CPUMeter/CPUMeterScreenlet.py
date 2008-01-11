#!/usr/bin/env python

#  CPUMeterScreenlet (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - a simple CPU-Meter, meant as an example for creating a Screenlet
# 
# TODO:
# - graph is incomplete: implement themed graph (with better clipping)
# - font/color settings

import screenlets
from screenlets.sensors import CPUSensor
from screenlets.options import FloatOption, BoolOption, StringOption, IntOption
from screenlets.options import FontOption

import cairo
import pango


class CPUMeterScreenlet (screenlets.Screenlet):
	"""A simple themeable CPU-Meter Screenlet."""
	
	# default meta-info for Screenlets
	__name__	= 'CPUMeterScreenlet'
	__version__	= '0.5'
	__author__	= 'RYX (Rico Pfaus) 2007'
	__desc__	= __doc__

	# options
	update_interval = 1.0
	show_text		= True
	show_graph		= True
	font			= 'Free Sans 25'
	text_prefix 	= '<span size="xx-small" rise="10000">% </span><b>'
	text_suffix 	= '</b>'
	text_x			= 17
	text_y			= 31
	
	# constructor
	def __init__ (self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, uses_theme=True, uses_pango=True, 
			**keyword_args)
		# init CPU sensor
		self.sensor = CPUSensor()
		self.sensor.connect('sensor_updated', self.handle_sensor_updated)
		# set theme
		self.theme_name = "default"
		# add default menu items
		self.add_default_menuitems()
		# add options
		self.add_options_group('CPU-Meter', 'CPU-Meter specific options')
		self.add_option(FloatOption('CPU-Meter', 'update_interval', 
			self.update_interval, 'Update-Interval', 
			'The interval for updating the CPU-meter (in seconds) ...',
			min=0.1, max=60.0))
		self.add_option(BoolOption('CPU-Meter', 'show_text', 
			self.show_text, 'Show Text', 'Show the text on the CPU-meter ...'))
		self.add_option(BoolOption('CPU-Meter', 'show_graph', 
			self.show_graph, 'Show Graph', 
			'Show the graph on the CPU-meter ...'))
		self.add_option(StringOption('CPU-Meter', 'text_prefix', 
			self.text_prefix, 'Text Prefix', 
			'Text (or Pango-Markup) that shall be placed before the load ...'), 
			realtime=False)
		self.add_option(StringOption('CPU-Meter', 'text_suffix', 
			self.text_suffix, 'Text Suffix', 
			'Text (or Pango-Markup) that shall be placed after the load ...'),
			realtime=False)
		self.add_option(IntOption('CPU-Meter', 'text_x', self.text_x, 'Text X', 
			'The horizontal offset for drawing the text at ...',
			min=0, max=100))
		self.add_option(IntOption('CPU-Meter', 'text_y', self.text_y, 'Text Y', 
			'The vertical offset for drawing the text at ...',
			min=0, max=100))
	# attribute-"setter", handles setting of attributes
	def __setattr__ (self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# check for this Screenlet's attributes, we are interested in:
		if name == 'update_interval':
			self.sensor.set_interval(int(value * 1000))
		elif name in ('text_x', 'text_y'):
			self.redraw_canvas()
		elif name == 'width':
			if self.p_layout:
				self.p_layout.set_width((self.width) * pango.SCALE)
		elif name == 'font':
			self.p_layout.set_font_description(\
				pango.FontDescription(value))
	
	# sensor callback, called on each interval
	def handle_sensor_updated (self, sensor):
		self.redraw_canvas()
	
	def on_draw (self, ctx):
		# set size
		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		if self.theme:
			self.theme.render(ctx, 'cpumeter-bg')
			# get load
			load = self.sensor.get_load()
			# draw cpu-graph
			if self.show_graph:
				h = (float(load) / 100.0) * 70.0
				ctx.save()
				ctx.rectangle(20, 10+(70-h), 60, h)
				ctx.clip()
				ctx.new_path()
				self.theme.render(ctx, 'cpumeter-graph')
				ctx.restore()
			# draw text
			if self.show_text:
				ctx.save()
				ctx.translate(self.text_x, self.text_y)
				if len(str(load))==1:
					load = "0" + str(load)
				self.p_layout.set_markup(self.text_prefix + str(load) + \
					self.text_suffix)
				ctx.set_source_rgba(1, 1, 1, 0.8)
				ctx.show_layout(self.p_layout)
				ctx.fill()
				ctx.restore()
			# draw glass (if theme available)
			self.theme.render(ctx, 'cpumeter-glass')
		
	def on_draw_shape (self,ctx):
		if self.theme:
			# set size rel to width/height
			ctx.scale(self.scale, self.scale)
			self.theme.render(ctx, 'cpumeter-bg')

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(CPUMeterScreenlet)

