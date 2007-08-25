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

import cairo
import pango


class CPUMeterScreenlet (screenlets.Screenlet):
	"""A simple themeable CPU-Meter Screenlet."""
	
	# default meta-info for Screenlets
	__name__	= 'CPUMeterScreenlet'
	__version__	= '0.5'
	__author__	= 'RYX (Rico Pfaus) 2007'
	__desc__	= __doc__

	# internals
	__timeout = None
	
	# settings
	update_interval = 1.0
	show_text		= True
	show_graph		= True
	text_prefix 	= '<span size="xx-small" rise="10000">% </span><b>'
	text_suffix 	= '</b>'
	text_x	= 17
	text_y	= 31
	
	# constructor
	def __init__ (self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, uses_theme=True, **keyword_args)
		# init CPU sensor
		self.sensor = CPUSensor(int(self.update_interval))
		self.sensor.connect('sensor_updated', self.handle_sensor_updated)
		# set theme
		self.theme_name = "default"
		# add default menu items
		self.add_default_menuitems()
		# add options
		grp = self.create_option_group('CPU-Meter', 
			'CPU-Meter specific options.')
		grp.add_option(FloatOption('update_interval', self.update_interval, 
			'Update-Interval', 'Interval for updating the graph (in seconds).',
			min=0.1, max=60.0))
		grp.add_option(BoolOption('show_text', self.show_text, 'Show Text', 
			'Show the text on the CPU-meter ...'))
		grp.add_option(BoolOption('show_graph', self.show_graph, 'Show Graph', 
			'Show the graph on the CPU-meter ...'))
		grp.add_option(StringOption('text_prefix', self.text_prefix, 
			'Text Prefix', 'Text (or Pango-Markup) to be placed before info.', 
			realtime=False))
		grp.add_option(StringOption('text_suffix', self.text_suffix, 
			'Text Suffix', 'Text (or Pango-Markup) to be placed after info.',
			realtime=False))
		grp.add_option(IntOption('text_x', self.text_x, 'Text X', 
			'The horizontal offset for drawing the text at ...',
			min=0, max=100))
		grp.add_option(IntOption('text_y', self.text_y, 'Text Y', 
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
	
	# sensor callback, called on each interval
	def handle_sensor_updated (self, sensor):
		self.redraw_canvas()
	
	def on_draw (self, ctx):
		# set size
		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
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
				p_layout = ctx.create_layout()
				p_fdesc = pango.FontDescription("Free Sans 25")
				p_layout.set_font_description(p_fdesc)
				p_layout.set_width((self.width) * pango.SCALE)
				if len(str(load))==1:
					load = "0" + str(load)
				p_layout.set_markup(self.text_prefix + str(load) + \
					self.text_suffix)
				ctx.set_source_rgba(1, 1, 1, 0.8)
				ctx.show_layout(p_layout)
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

