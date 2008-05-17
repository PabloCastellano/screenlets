#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  SysmonitorScreenlet (c) Whise <helder.fraga@hotmail.com>


import screenlets
from screenlets.options import StringOption , BoolOption , IntOption, ColorOption, FontOption, ImageOption
from screenlets import DefaultMenuItem
from screenlets import sensors
import pango
import gobject
import gtk
import os

class SysmonitorScreenlet (screenlets.Screenlet):
	"""A simple system monitor Screenlet based in conky"""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'SysmonitorScreenlet'
	__version__	= '0.1'
	__author__	= 'Whise'
	__desc__	= __doc__	# set description to docstring of class
	
	# editable options (options that are editable through the UI)

	fontsize = 10
	expand = True
	color_text =(1.0, 1.0, 1.0, 0.7)
	color_background =(0.0, 0.0, 0.0, 0.7)
	color_graph =(1.0, 1.0, 1.0, 0.2)
	font= "FreeSans"
	username = ''
	hostname = ''
	date = ''
	time = ''
	kernel = ''
	distro = ''
	avg_load = ''
	cpu_nb = 0
	old_cpu = [0,0,0,0]
	new_cpu = [0,0,0,0]
	cpu_load = [0,0,0,0]
	distroshort = ''
	cpu_name= ''
	mem_used = 0
	swap_used = 0
	up = 0
	down = 0
	old_up = 0
	old_down = 0
	upload = 0
	download =0
	ip = ''
	disks = []
	disk = []
	bat_list= []
	bat_data=[]
	bat_load = 0
	wire_list = []
	wire_data = []
	newheight = gtk.gdk.screen_height()
	show_logo = True
	show_frame = True
	starty = 0
	number = 0
	_update_interval = 2
	font1 = 'FreeSans'
	image_filename = ''
	use_bg_image = False

	#Sensors to display
	show_time = True
	show_date = True
	show_username = True
	show_distro = True
	show_kernel = True
	show_cpuname = True
	show_cpus = True
	show_load = True
	show_mem = True
	show_swap = True
	show_ip = True
	show_updown = True
	show_disks = True
	show_bat_wir = True
	show_processes = True
	show_uptime = True



	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=180, height=self.newheight, 
			uses_theme=True,ask_on_option_override=False, **keyword_args)
		# set theme
		self.get_constants()
		self.theme_name = "default"
		# add option group
		self.add_options_group('Sysmonitor', 'Options ...')
		# add editable option to the groupSysmonitor

		self.add_option(BoolOption('Sysmonitor','expand', 
			self.expand, 'Expand height', 
			'Expand height to screen height'))

		self.add_option(BoolOption('Sysmonitor','show_logo', 
			self.show_logo, 'Show distro logo if available', 
			'Show distro logo if available'))

		self.add_option(BoolOption('Sysmonitor','show_frame', 
			self.show_frame, 'Show frame', 
			'Show frame window'))

		self.add_option(IntOption('Sysmonitor', 'update_interval',self.update_interval, 'Update Interval','',min=1, max=60))

		self.add_option(IntOption('Sysmonitor', 'starty',self.starty, 'Y position to start the text','',min=0, max=500))

		self.add_option(FontOption('Sysmonitor','font', 
			self.font, 'Text Font', 
			'Text font'))

		self.add_option(ColorOption('Sysmonitor','color_text', 
			self.color_text, 'Text color', ''))

		self.add_option(ColorOption('Sysmonitor','color_background', 
			self.color_background, 'Background Color', 
			''))
		self.add_option(ColorOption('Sysmonitor','color_graph', 
			self.color_graph, 'Graphs Color', 
			''))
		self.add_options_group('Backgound', 'Options ...')
		self.add_option(BoolOption('Backgound','use_bg_image', 
			self.use_bg_image, 'Use Background image', 
			'use_bg_image'))
		self.add_option(ImageOption('Backgound', 'image_filename', 
			self.image_filename, 'Background image',
			'Background image')) 

		self.add_options_group('Sensors', 'Options ...')

		self.add_option(BoolOption('Sensors','show_time', 
			self.show_time, 'Show time', 
			'Show Sensor'))

		self.add_option(BoolOption('Sensors','show_date', 
			self.show_date, 'Show date', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_username', 
			self.show_username, 'Show username', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_distro', 
			self.show_distro, 'Show distro', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_kernel', 
			self.show_kernel, 'Show kernel', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_cpuname', 
			self.show_cpuname, 'Show Cpu name', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_cpus', 
			self.show_cpus, 'Show Cpus', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_load', 
			self.show_load, 'Show Load', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_mem', 
			self.show_mem, 'Show Memory', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_swap', 
			self.show_swap, 'Show Swap', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_ip', 
			self.show_ip, 'Show Ip', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_updown', 
			self.show_updown, 'Show Upload Download', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_disks', 
			self.show_disks, 'Show Disks', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_bat_wir', 
			self.show_bat_wir, 'Show battery and wifi', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_processes', 
			self.show_processes, 'Show Processes', 
			'Show Sensor'))
		self.add_option(BoolOption('Sensors','show_uptime', 
			self.show_uptime, 'Show Uptime', 
			'Show Sensor'))
		# ADD a 1 second (1000) TIMER
		self.timer = None

		#Also add options from xml file for example porpuse

	# getter and setter methods to be used by the update_interval property
	def get_update_interval(self):
		return self._update_interval

	def set_update_interval(self, new_interval):
		if new_interval < 1: new_interval = 1
		if new_interval != self._update_interval:
			if self.timer:
				gobject.source_remove(self.timer)
			self.timer = gobject.timeout_add(int(new_interval * 1000), self.update)
			self._update_interval = new_interval

	# create an update_interval property that controls restarting the update timer
	update_interval = property(get_update_interval, set_update_interval)

	def get_constants(self):
		self.username = sensors.sys_get_username()
		self.hostname = sensors.sys_get_hostname ()
		self.kernel = sensors.sys_get_kernel_version()
		self.distro = sensors.sys_get_distrib_name()
		self.distroshort = sensors.sys_get_distroshort()
		self.cpu_nb = sensors.cpu_get_nb_cpu()
		self.cpu_name = sensors.cpu_get_cpu_name()

	def get_variables(self):
		if self.show_time: self.time = sensors.cal_get_local_time()
		if self.show_date: self.date = sensors.cal_get_day_name() + ' '+  sensors.cal_get_local_date()
		if self.show_load: self.avg_load = sensors.sys_get_average_load()
		if self.show_cpus:
			for i in range (0,self.cpu_nb+1):

			#	if not self.cpu_load[i]: self.cpu_load.append(0)
				self.new_cpu[i]=sensors.cpu_get_load(i)

				self.cpu_load[i] = (self.new_cpu[i]-self.old_cpu[i])/self.update_interval
				
				self.old_cpu[i] = self.new_cpu[i]
				try:
					if self.cpu_load[i] > 99: self.cpu_load[i] = 99
					elif self.cpu_load[i] < 0: self.cpu_load[i]=0
				except : pass
		if self.show_mem: self.mem_used = sensors.mem_get_usage()
		if self.show_swap: self.swap_used = sensors.mem_get_usedswap()
		if self.show_ip: self.ip = sensors.net_get_ip()
		if self.show_updown: 
			self.up = sensors.net_get_updown()[0]
			self.down = sensors.net_get_updown()[1]
			self.upload = (self.up - self.old_up)/self.update_interval
			self.download = (self.down - self.old_down)/self.update_interval
			self.old_up = self.up
			self.old_down = self.down
		if self.show_disks:self.disks = sensors.disk_get_disk_list()
		if self.show_bat_wir:
			self.bat_list = sensors.bat_get_battery_list()
			if self.bat_list:
				self.bat_data = sensors.bat_get_data(self.bat_list[0])
				try:
					self.bat_load = (self.bat_data[1]*100)/self.bat_data[2]
				except: self.bat_load = 0
			self.wire_list = sensors.wir_get_interfaces()
			if self.wire_list:
				self.wire_data = sensors.wir_get_stats(self.wire_list[0])
			

	def update (self):
		self.get_variables()
		self.redraw_canvas()
		return True # keep running this event	

	def on_map(self):
		if not self.timer:
			self.timer = gobject.timeout_add( self.update_interval*1000, self.update)
		self.update()

	def on_unmap(self):
		if self.timer:
			gobject.source_remove(self.timer)
			self.timer = None

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
		print 'i just got started'
		# add  menu items from xml file

		print self.date
		#self.add_default_menuitems(DefaultMenuItem.XML)
		# add menu item
		#self.add_menuitem("at_runtime", "A")
		# add default menu items
		self.add_default_menuitems()
		
		self.height = self.newheight

	def on_key_down (self, keycode, keyvalue, event=None):
		"""Called when a key is pressed within the screenlet's window."""
		pass
	
	def on_load_theme (self):
		"""Called when the theme is reloaded (after loading, before redraw)."""
		pass
	
	def on_menuitem_select (self, id):
		"""Called when a menuitem is selected."""
		pass
	
	def on_mouse_down (self, event):
		"""Called when a buttonpress-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		return False
	
	def on_mouse_enter (self, event):
		"""Called when the mouse enters the Screenlet's window."""
	        #self.theme.show_tooltip("this is a tooltip , it is set to shows on mouse hover",self.x+self.mousex,self.y+self.mousey)

		
	def on_mouse_leave (self, event):
		"""Called when the mouse leaves the Screenlet's window."""
	        #self.theme.hide_tooltip()


	def on_mouse_move(self, event):
		"""Called when the mouse moves in the Screenlet's window."""

		pass

	def on_mouse_up (self, event):
		"""Called when a buttonrelease-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		return False
	
	def on_quit (self):
		"""Callback for handling destroy-event. Perform your cleanup here!"""

		return True
		
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
		# if theme is loaded
		#self.font =  self.font.strip(' ')
		if self.font.find(' ') != -1:
			self.font1 =  self.font.strip().split(' ')[0]
			try : self.fontsize = int(self.font.strip().split(' ')[2])
			except:
				try: self.fontsize = int(self.font.strip().split(' ')[1])
				except : self.fontsize = 10
		if self.theme:
			# set scale rel. to scale-attribute
			ctx.scale(self.scale, self.scale)
			if self.show_logo:
				if os.path.exists (self.get_screenlet_dir() + '/themes/'+ self.theme_name + '/' + self.distroshort.lower() + '.svg') or os.path.exists (self.get_screenlet_dir() + '/themes/'+ self.theme_name + '/' +self.distroshort.lower() + '.png'):
					ctx.translate(0,20)
					try:
						self.theme.render(ctx,self.distroshort.lower())
					except:pass
					ctx.translate(0,-20)
			#DRAW BACKGROUND ALLWAYS
			if self.show_frame:
				ctx.set_source_rgba(0, 0, 0,0.7)	
				self.draw_rectangle(ctx,0,0,self.width,self.height,False)
				ctx.set_source_rgba(89/255, 89/255, 89/255,0.43)	
				ctx.translate (1,1)
				self.draw_rectangle(ctx,0,0,self.width-2,self.height-2,False)

				ctx.set_source_rgba(229/255, 229/255, 229/255,76/255)	
				ctx.translate (1,1)
				self.draw_rectangle(ctx,0,0,self.width-2,self.height-2)
				ctx.translate (-2,-2)
			
			#DRAW BACKGROUND USER SELECTED
			if self.image_filename != '' and self.use_bg_image:self.draw_scaled_image(ctx,0,0,self.image_filename,self.width,self.height)

			ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],self.color_background[3])	
			self.draw_rectangle(ctx,0,0,self.width,self.height)
			ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
			#DRAW TEXT
			m = self.starty
			m = m + 5
			if self.show_time:
				self.draw_text(ctx, ' ' + self.time, 0, m, self.font1, self.fontsize + 8,  self.width,pango.ALIGN_CENTER)
				m = m + 25
			if self.show_date:
				self.draw_text(ctx, self.date, 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				m = m + 40
			if self.show_username:

				self.draw_text(ctx, self.username + '@' + self.hostname, 0, m, self.font1, self.fontsize + 1,  self.width,pango.ALIGN_CENTER)
				m = m + 20
			if self.show_distro:
				self.draw_text(ctx, self.distro, 0, m, self.font1, self.fontsize + 1,  self.width,pango.ALIGN_CENTER)
				m = m + 20
			if self.show_kernel:
				self.draw_text(ctx, 'kernel: ' + self.kernel, 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				m = m + 40
			if self.show_cpuname:
				self.draw_text(ctx, self.cpu_name, 0, m, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
				m = m + 30
			if self.show_cpus:			
				ctx.save()
			#d = 1
				if self.cpu_nb == 1:
					ctx.save()
					ctx.translate(65,m)
					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
					a = (40* self.cpu_load[0])/100
					self.draw_rounded_rectangle(ctx,0,0,10,50,50)
					ctx.translate(5,5)
					ctx.translate (0,40-a)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])	
					self.draw_rectangle(ctx,0,0,40,a)
					ctx.translate(75,-5-(40-a))
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.draw_text(ctx, 'CPU' , -75-70, 0, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
					self.draw_text(ctx,str(self.cpu_load[0])+ '%', -75-70, 30, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)

					ctx.restore()
					m = m + 40
				if self.cpu_nb >= 2:
					ctx.translate(25,m)
					a = (40* self.cpu_load[1])/100
					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
					ctx.save()
					self.draw_rounded_rectangle(ctx,0,0,10,50,50)
					ctx.translate(5,5)
					ctx.translate (0,40-a)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])	
					self.draw_rectangle(ctx,0,0,40,a)
					ctx.translate(75,-5-(40-a))
					ctx.restore()
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.draw_text(ctx, 'CPU 1' , -65, 0, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
					self.draw_text(ctx,str(self.cpu_load[1])+ '%', -65, 30, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
					ctx.translate(75,0)


					a = (40* self.cpu_load[2])/100
					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
					ctx.save()
					self.draw_rounded_rectangle(ctx,0,0,10,50,50)
					ctx.translate(5,5)
					ctx.translate (0,40-a)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
					self.draw_rectangle(ctx,0,0,40,a)
					ctx.restore()
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.draw_text(ctx, 'CPU 2' , -65, 0, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
					self.draw_text(ctx,str(self.cpu_load[2])+ '%' , -65, 30, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
					#ctx.restore()
					m = m + 40
					d = 4
					if self.cpu_nb == 4:#self.cpu_nb
						ctx.save()
						m = m +60
						ctx.translate (25,m)
						a = (40* self.cpu_load[3])/100
						ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
						ctx.save()
						self.draw_rounded_rectangle(ctx,0,0,10,50,50)
						ctx.translate(5,5)
						ctx.translate (0,40-a)
						ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])	
						self.draw_rectangle(ctx,0,0,40,a)
						ctx.translate(75,-5-(40-a))
						ctx.restore()
						ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
						self.draw_text(ctx, 'CPU 3' , -65, 0, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
						self.draw_text(ctx,str(self.cpu_load[3])+ '%', -65, 30, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
						ctx.translate(75,0)


						a = (40* self.cpu_load[4])/100
						ctx.save()
						ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)

						ctx.translate(5,5)
						ctx.translate (0,40-a)
						ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
						self.draw_rectangle(ctx,0,0,40,a)
						ctx.restore()
						ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
						self.draw_text(ctx, 'CPU 4' , -65, 0, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
						self.draw_text(ctx,str(self.cpu_load[4])+ '%' , -65, 30, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
						self.draw_rounded_rectangle(ctx,0,0,10,50,50)
						ctx.restore()
						m = m + 40
				ctx.restore()
				m = m +20
			else: m= m +10
			if self.show_load:
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.draw_text(ctx, 'Load : ' + self.avg_load, 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				m = m +20
			if self.show_mem:
				ctx.save()
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.draw_text(ctx, 'Ram ' + str(self.mem_used) + '%', 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				ctx.translate(0,m)
				ctx.translate(20,15)
				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
				self.draw_rectangle(ctx,0,0,140,5)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
				self.draw_rectangle(ctx,0,0,(self.mem_used*100)/140,5)
				ctx.translate(-20,-15)
				ctx.restore()
				m = m +20
			if self.show_swap:
				ctx.save()
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.draw_text(ctx,'Swap ' + str(self.swap_used)+ "%", 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				ctx.translate(0,m)
				ctx.translate(20,15)
				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
				self.draw_rectangle(ctx,0,0,140,5)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
				self.draw_rectangle(ctx,0,0,(self.swap_used*100)/140,5)
				ctx.translate(-20,-15)
				ctx.restore()
				m = m +30
			if self.show_ip:
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.draw_text(ctx, 'IP : ' + self.ip, 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				m = m +25
			if self.show_updown:
				self.draw_text(ctx, 'Upload - ' + str(self.upload)[:3] + ' KB/sec', 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				m = m +20

				self.draw_text(ctx, 'Download - ' + str(self.download)[:3] + ' KB/sec', 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
				m = m +40

			if self.show_disks:
				ctx.save()
				for i in self.disks:
					a = sensors.disk_get_usage(i)
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.draw_text(ctx,a[0]+  ' ' + a[4], 0, m, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)
					ctx.translate(0,m)
					ctx.translate(20,15)
					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
					self.draw_rectangle(ctx,0,0,140,5)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])

					self.draw_rectangle(ctx,0,0,(int(a[4].replace('%',''))*140)/100,5)
					ctx.translate(-20,-15)
					m = m +30
					ctx.restore()
					ctx.save()
				m = m + 10
				ctx.restore()

			if self.show_bat_wir:
				
				if self.bat_list and self.bat_data !=[] and self.wire_list:
					ctx.save()
					ctx.translate(25,m)
					a = (40*self.bat_load)/100
	
					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
					ctx.save()
					self.draw_rounded_rectangle(ctx,0,0,10,50,50)

					ctx.translate(5,5)
					ctx.translate (0,40-a)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])		
					self.draw_rectangle(ctx,0,0,40,a)
					ctx.translate(75,-5-(40-a))
					ctx.restore()
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.draw_text(ctx, self.bat_list[0] , -65, 0, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)

					self.draw_text(ctx,str(self.bat_load) + '%', -65, 30, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)

					ctx.translate(75,0)



					a = (40* int(self.wire_data['percentage']))/100

					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
					ctx.save()
					self.draw_rounded_rectangle(ctx,0,0,10,50,50)

					ctx.translate(5,5)
					ctx.translate (0,40-a)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
					self.draw_rectangle(ctx,0,0,40,a)
					ctx.restore()
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.draw_text(ctx, self.wire_list[0] , -65, 0, self.font1, self.fontsize,  self.width,pango.ALIGN_CENTER)

					self.draw_text(ctx,str( int(self.wire_data['percentage']))+ '%' , -65, 30, self.font1, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
					ctx.restore()
				m = m + 60
			if self.show_processes:
				self.draw_text(ctx,str( sensors.process_get_top().replace(' ','-')) , 0, m, self.font1, self.fontsize - 3,  self.width -10,pango.ALIGN_CENTER)
				m = m + 110
			if self.show_uptime:
				self.draw_text(ctx,'Uptime: ' + str( sensors.sys_get_uptime()) , 0, m, self.font1, self.fontsize +3,  self.width -10,pango.ALIGN_CENTER)
			m = m +40
			if self.height != m and self.expand == False:
				self.height = m
#							ctx.translate(-20,-15)self.draw_text(ctx, self.theme_name, 0, 50, self.font1, self.fontsize,  self.width,pango.ALIGN_LEFT)

#			self.draw_text(ctx, 'mouse x ' + str(self.mousex ) + ' \n mouse y ' + str(self.mousey ) , 0, 170, self.font1, self.fontsize,  self.width,pango.ALIGN_LEFT)


			# render svg-file

			# render png-file
			#ctx.set_source_surface(self.theme['example-test.png'], 0, 0)
			#ctx.paint()
	
	def on_draw_shape (self, ctx):
		if self.theme:
			ctx.set_source_rgba(0, 0, 0,1)	
			self.draw_rectangle(ctx,0,0,self.width,self.height)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(SysmonitorScreenlet)

