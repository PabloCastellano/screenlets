#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#RingSensorScreenlet (c) Whise <helder.fraga@hotmail.com>

import screenlets
from screenlets import sensors
from screenlets.options import FloatOption, BoolOption, StringOption, IntOption, ColorOption
import cairo
import pango
import sys
import gobject
import math

class RingSensorsScreenlet(screenlets.Screenlet):
	"""Circle Sensors Screenlet."""

	# default meta-info for Screenlets
	__name__ = 'RingSensorsScreenlet'
	__version__ = '0.2'
	__author__ = 'Helder Fraga aka Whise based on RingClock by Paul Ashton'
	__desc__ = 'Ring Sensors Screenlet.'

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
	hourMiddle = False
	color_back = (1,1,1,0.6)
	color_front =(1, 1, 1, 0.9)
	color_text = (1, 1, 1, 1)
	graph_type = 'Graph'
	thickness = 24.0
	ringSpacing = 26.0
	sensor_list = []
	sensor = 'CPU0'
	blockSpacing = 1.0
	load = 0
	size = 100
	old_cpu = 0
	new_cpu = 0
	wire_list = []
	wire_data = []
	big_bars = True
	# constructor
	def __init__(self,**keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=200, 
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
					#print i.split(':')[0]
			self.wire_list = sensors.wir_get_interfaces()
			if self.wire_list !=[]:
				self.sensor_list.append('Wifi '+ self.wire_list[0])		

		self.theme_name = "default"
		# add default menu items
		# add settings
		self.add_options_group('Sensors', 'CPU-Graph specific options')

		self.add_option(BoolOption('Sensors', 'show_text',
			self.show_text, 'Show Text', 'Show the text on the CPU-Graph ...'))



		self.add_option(StringOption('Sensors', 'sensor',
			self.sensor, 'Sensor to Display',
			'',choices=self.sensor_list))

		self.add_option(ColorOption('Sensors','color_back', 
			self.color_back, 'background color', ''))

		self.add_option(ColorOption('Sensors','color_front', 
			self.color_front, 'Front color', 
			''))
		self.add_option(ColorOption('Sensors','color_text', 
			self.color_text, 'Text color', 
			''))
		self.add_option(FloatOption('Sensors', 'thickness', self.thickness, 'Ring Thickness', '',min=0.0, max=500.0, increment=0.1))
		self.add_option(FloatOption('Sensors', 'blockSpacing', self.blockSpacing, 'Block Spacing', '',min=0.0, max=6.0, increment=0.1))
		self.add_option(BoolOption('Sensors', 'big_bars',
			self.big_bars, 'Use Big bars', ''))
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

			self.load = int(self.new_cpu-self.old_cpu)
			
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

			self.sensor = str(self.sensor.split(':')[0]) + ':' + str(sensors.sensors_get_sensor_value(self.sensor.split(':')[0]))
			self.load = 0
		elif self.sensor.endswith('RPM'):
			self.sensor = str(self.sensor.split(':')[0]) + ':' +str(sensors.sensors_get_sensor_value(self.sensor.split(':')[0]))
			self.load = 0
		elif self.sensor.endswith('V'):
			self.sensor = str(self.sensor.split(':')[0]) + ':' +str(sensors.sensors_get_sensor_value(self.sensor.split(':')[0]))
			self.load = 0
		elif self.sensor.endswith('Custom Sensors'):
			pass			
		elif self.sensor.startswith('Wifi'):
			if self.wire_list != []:
				self.wire_data = sensors.wir_get_stats(self.wire_list[0])
				print self.wire_data
				a = str(self.wire_data['essid']).find('off/any')
				if a != -1:
					self.sensor = 'Wifi ' + str(self.wire_list[0])
				else:
					self.sensor = 'Wifi '  + str(self.wire_data['essid'])
				self.load = int(str(self.wire_data['percentage']).replace('%',''))
		else:

			if self.sensor != None:
				self.load = int(sensors.disk_get_usage(self.sensor)[4].replace('%',''))
		


		if self.load > 100:
			self.load = 100
		elif self.load < 0:
			self.load=0

		self.redraw_canvas()
		return True


	def on_draw(self, ctx):

		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
		
		b = (int(self.load)*80)/100
		a = (int(b)*450)/100
		startrad = self.size-(self.thickness/2.0)		
		a = float(self.load*12)/100
				
		
		ctx.set_line_width( self.thickness )	
		if self.big_bars:
			for i in range(12):
				if i == a or (i<=a ): col = self.color_front
				else: col = self.color_back
				if self.hourMiddle: radius = startrad-(self.ringSpacing*2.0)
				else: radius = startrad
				pos = -105+(self.blockSpacing/2.0)+(i*30)
				
				ctx.arc( 100, 100, radius, math.radians(pos), math.radians(pos+30-self.blockSpacing) )
				ctx.set_source_rgba(col[0],col[1],col[2],col[3])
				ctx.stroke()
		else:
			a = float(self.load*60)/100
			for i in range(60):
				if i == a or (i<=a ): col = self.color_front
				else: col = self.color_back
				if self.hourMiddle: radius = startrad-(self.ringSpacing*2.0)
				else: radius = startrad
				pos = -93+(self.blockSpacing/2.0)+(i*6)
				
				ctx.arc( 100, 100, radius, math.radians(pos), math.radians(pos+6-self.blockSpacing) )
				ctx.set_source_rgba(col[0],col[1],col[2],col[3])
				ctx.stroke()
		if len(str(self.load))==1:
			self.load = "0" + str(self.load)
		ctx.set_source_rgba(self.color_text[0],self.color_text[1],self.color_text[2],self.color_text[3])
		if self.sensor.endswith('RPM') or self.sensor.endswith('C') or self.sensor.endswith('V'):
			text = '<small><small><small><small>' +str(self.sensor.split(':')[0]) +'</small></small></small></small>\n'+str(self.sensor.split(':')[1])	
		else:
			text = '<small><small><small><small>' +self.sensor +'</small></small></small></small>\n'+self.text_prefix + str(self.load) + self.text_suffix
		if self.theme:self.theme.draw_text(ctx,text, 0, 70, 'Free Sans', 25,  self.width,pango.ALIGN_CENTER)
			
			
	

	def on_draw_shape(self,ctx):
		self.on_draw(ctx)


# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(RingSensorsScreenlet)
