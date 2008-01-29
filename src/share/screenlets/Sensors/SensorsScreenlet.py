#!/usr/bin/env python



import screenlets
from screenlets import sensors
from screenlets.options import FloatOption, BoolOption, StringOption, IntOption, ColorOption
import cairo
import pango
import sys
import gobject

class SensorsScreenlet(screenlets.Screenlet):
	"""Sensors Screenlet."""

	# default meta-info for Screenlets
	__name__ = 'SensorsScreenlet'
	__version__ = '0.1'
	__author__ = 'Helder Fraga aka Whise'
	__desc__ = 'Sensors Screenlet.'

	# internals
	__timeout = None

	# settings
	update_interval = 1
	nb_points=50
	show_text = True
	show_graph = True
	text_prefix = '<span size="xx-small" rise="10000">% </span><b>'
	text_suffix = '</b>'
	loads=[]
	old_idle=0
	linear = ''
	color_high = (1,0,0,1)
	color_medium =(0, 0, 1, 1)
	color_low = (0, 1, 0, 1)
	graph_type = 'Graph'
	sensor_list = []
	sensor = 'CPU0'
	load = 0
	old_cpu = 0
	new_cpu = 0
	# constructor
	def __init__(self,**keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=100, 
			uses_theme=True, **keyword_args)
		self.loads=[]
		#self.old_somme=0
		self.old_idle=0
		for i in range(self.nb_points):
			self.loads.append(0)




		#call super (and not show window yet)
		#screenlets.Screenlet.__init__(self, uses_theme=True, **keyword_args)
		# set theme
		if self.sensor_list ==[]:
			for i in range (0,sensors.cpu_get_nb_cpu()+1): 
	
				self.sensor_list.append('CPU' + str(i))

			self.sensor_list.append('RAM')
			self.sensor_list.append('SWAP')
			if sensors.bat_get_battery_list():
				self.sensor_list.append(str(sensors.bat_get_battery_list()[0]))
			for i in sensors.disk_get_disk_list():
				self.sensor_list.append(str(i))
			print sensors.sensors_get_sensors_list()
			if sensors.sensors_get_sensors_list():
				for i in sensors.sensors_get_sensors_list():
					self.sensor_list.append(str(i))	
		
		self.theme_name = "default"
		# add default menu items
		# add settings
		self.add_options_group('Sensors', 'CPU-Graph specific options')

		self.add_option(BoolOption('Sensors', 'show_text',
			self.show_text, 'Show Text', 'Show the text on the CPU-Graph ...'))


		self.add_option(StringOption('Sensors', 'graph_type',
			self.graph_type, 'Graph type',
			'Chart or bar',choices = ['Graph','Bar']))

		self.add_option(StringOption('Sensors', 'sensor',
			self.sensor, 'Sensor to Display',
			'',choices=self.sensor_list))

		self.add_option(ColorOption('Sensors','color_high', 
			self.color_high, 'High color', ''))

		self.add_option(ColorOption('Sensors','color_medium', 
			self.color_medium, 'Medium Color', 
			''))
		self.add_option(ColorOption('Sensors','color_low', 
			self.color_low, 'Low Color', 
			''))

		# init the timeout function
		self.update_interval = self.update_interval


	def on_init(self):
		self.add_default_menuitems()

	# attribute-"setter", handles setting of attributes
	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# check for this Screenlet's attributes, we are interested in:
		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(int(value * 1000), self.update)
			else:
				# TODO: raise exception!!!
				self.__dict__['update_interval'] = 1
				pass
		elif name == "nb_points":
			if value > 1:
				if len(self.loads)> value:
					self.loads=self.loads[len(self.loads)-value:]
				elif len(self.loads)< value:
					for i in range(value-len(self.loads)):
						self.loads.insert(0,0)
				self.__dict__['nb_points'] = value
				
			else:
				# TODO: raise exception!!!
				self.__dict__['nb_points'] = 2
				pass

	# calculate cpu-usage by values from /proc/stat

	# timeout-function
	def update(self):
		if self.sensor.startswith('CPU'):
			self.new_cpu=sensors.cpu_get_load(int(self.sensor[3]))

			self.load = self.new_cpu-self.old_cpu
			
			self.old_cpu = self.new_cpu
		elif self.sensor.startswith('RAM'):
			self.load = sensors.mem_get_usage()

		elif self.sensor.startswith('SWAP'):
			self.load = sensors.mem_get_usedswap()

		elif self.sensor.startswith('BAT'):
			bat_data = sensors.bat_get_data(self.sensor)
			try:
				self.load = (bat_data[1]*100)/bat_data[2]
			except: self.load = 0
		elif self.sensor.endswith('C'):
			self.load = 0
		elif self.sensor.endswith('RPM'):
			self.load = 0
		elif self.sensor.endswith('V'):
			self.load = 0				
		elif self.sensor.endswith('Custom Sensors'):
			pass			


		else:
			self.load = int(sensors.disk_get_usage(self.sensor)[4].replace('%',''))
		


		if self.load > 100:
			self.load = 100
		elif self.load < 0:
			self.load=0

		self.redraw_canvas()
		return True


	def on_draw(self, ctx):
		# get load
		#print self.loads
		del(self.loads[0])
		self.loads.append(self.load)
		# set size
		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			self.theme['cpumeter-bg.svg'].render_cairo(ctx)
		# draw cpu-graph
			if self.graph_type == 'Graph':
				ctx.save()
				ctx.move_to(10,80)
				i=0
				for l in self.loads:
					ctx.line_to(i*(180./(self.nb_points-1))+10,80-l*.65)
					i+=1
				ctx.line_to(self.width-10,self.height-20)
				ctx.close_path()
				ctx.stroke_preserve()
				self.linear = cairo.LinearGradient(0, 100,0, 0)
				self.linear.add_color_stop_rgba(0.22, self.color_low[0],self.color_low[1],self.color_low[2],self.color_low[3])
				self.linear.add_color_stop_rgba(0.44, self.color_medium[0],self.color_medium[1],self.color_medium[2],self.color_medium[3])
				self.linear.add_color_stop_rgba(0.66, self.color_high[0],self.color_high[1],self.color_high[2],self.color_high[3])
				ctx.set_source(self.linear)
				ctx.fill()
		
				ctx.restore()
			elif self.graph_type == 'Bar':
				if self.load <= 33:
					ctx.set_source_rgba(self.color_low[0],self.color_low[1],self.color_low[2],self.color_low[3])
				elif self.load > 33 and self.load <=  66:
					ctx.set_source_rgba(self.color_medium[0],self.color_medium[1],self.color_medium[2],self.color_medium[3])
				elif self.load > 66:
					ctx.set_source_rgba(self.color_high[0],self.color_high[1],self.color_high[2],self.color_high[3])

				self.theme.draw_rectangle(ctx,10,15,(self.load*180)/100,65)
		# draw text
			if len(str(self.load))==1:
				self.load = "0" + str(self.load)
			ctx.set_source_rgba(1, 1, 1, 0.9)
			if self.sensor.endswith('RPM') or self.sensor.endswith('C') or self.sensor.endswith('V'):
				text = '<small><small><small><small>' +self.sensor +'</small></small></small></small>\n'	
			else:
				text = '<small><small><small><small>' +self.sensor +'</small></small></small></small>\n'+self.text_prefix + str(self.load) + self.text_suffix
			self.theme.draw_text(ctx,text, 15, 20, 'Free Sans', 25,  self.width,pango.ALIGN_LEFT)
			
			
		# draw glass (if theme available)
	
			self.theme['cpumeter-glass.svg'].render_cairo(ctx)

	def on_draw_shape(self,ctx):
		if self.theme:
			ctx.scale(self.scale, self.scale)
			self.theme['cpumeter-bg.svg'].render_cairo(ctx)


# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(SensorsScreenlet)
