#!/usr/bin/env python

#  SysmonitorScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - a simple example for creating a Screenlet
# 
# TODO:
# - make a nice Screenlet from this example ;) ....

import screenlets
from screenlets.options import StringOption , BoolOption , IntOption, ColorOption, FontOption
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
	font= "Sans"
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
	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=180, height=self.newheight, 
			uses_theme=True, **keyword_args)
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


		# ADD a 1 second (1000) TIMER
		self.timer = gobject.timeout_add( 1000, self.update)

		#Also add options from xml file for example porpuse



	def get_constants(self):
		self.username = sensors.sys_get_username()
		self.hostname = sensors.sys_get_hostname ()
		self.kernel = sensors.sys_get_kernel_version()
		self.distro = sensors.sys_get_distrib_name()
		self.distroshort = sensors.sys_get_distroshort()
		self.cpu_nb = sensors.cpu_get_nb_cpu()
		self.cpu_name = sensors.cpu_get_cpu_name()
		self.ip = sensors.net_get_ip()
		self.disks = sensors.disk_get_disk_list()
		self.wire_list = sensors.wir_get_interfaces()

	def get_variables(self):
		self.time = sensors.cal_get_local_time()
		self.date = sensors.cal_get_day_name() + ' '+  sensors.cal_get_local_date()
		self.avg_load = sensors.sys_get_average_load()
		for i in range (0,self.cpu_nb+1):

		#	if not self.cpu_load[i]: self.cpu_load.append(0)
			self.new_cpu[i]=sensors.cpu_get_load(i)

			self.cpu_load[i] = self.new_cpu[i]-self.old_cpu[i]
			
			self.old_cpu[i] = self.new_cpu[i]
			try:
				if self.cpu_load[i] > 99: self.cpu_load[i] = 99
				elif self.cpu_load[i] < 0: self.cpu_load[i]=0
			except : pass
		self.top = sensors.top_process_get_list()
		self.mem_used = sensors.mem_get_usage()
		self.swap_used = sensors.mem_get_usedswap()
		self.up = sensors.net_get_updown()[0]
		self.down = sensors.net_get_updown()[1]
		self.upload = self.up - self.old_up
		self.download = self.down - self.old_down
		self.old_up = self.up
		self.old_down = self.down
		self.bat_list = sensors.bat_get_battery_list()
		if self.bat_list:
			self.bat_data = sensors.bat_get_data(self.bat_list[0])
			try:
				self.bat_load = (self.bat_data[1]*100)/self.bat_data[2]
			except: self.bat_load = 0
		if self.wire_list:
			self.wire_data = sensors.wir_get_stats(self.wire_list[0])
			

	def update (self):
		self.get_variables()
		if self.number <= 10000:
			self.number = self.number+1
			self.get_constants()
		else:
			self.number = 0
		self.redraw_canvas()
		return True # keep running this event	


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
		self.redraw_canvas()
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

		try : self.fontsize = int(self.font.strip().split(' ')[2])
		except:
			try: self.fontsize = int(self.font.strip().split(' ')[1])
			except : pass
		self.font =  self.font.strip().split(' ')[0]
		if self.theme:
			# set scale rel. to scale-attribute
			ctx.scale(self.scale, self.scale)
			if self.show_logo:
				if os.path.exists (self.get_screenlet_dir() + '/themes/'+ self.theme_name + '/' + self.distroshort.lower() + '.svg') or os.path.exists (self.get_screenlet_dir() + '/themes/'+ self.theme_name + '/' +self.distroshort.lower() + '.png'):
					ctx.translate(0,20)
					self.theme.render(ctx,self.distroshort.lower())
					ctx.translate(0,-20)
			#DRAW BACKGROUND ALLWAYS
			if self.show_frame:
				ctx.set_source_rgba(0, 0, 0,0.7)	
				self.theme.draw_rectangle(ctx,self.width,self.height,False)
				ctx.set_source_rgba(89/255, 89/255, 89/255,0.43)	
				ctx.translate (1,1)
				self.theme.draw_rectangle(ctx,self.width-2,self.height-2,False)

				ctx.set_source_rgba(229/255, 229/255, 229/255,76/255)	
				ctx.translate (1,1)
				self.theme.draw_rectangle(ctx,self.width-2,self.height-2)
				ctx.translate (-2,-2)
			
			#DRAW BACKGROUND USER SELECTED
			ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],self.color_background[3])	
			self.theme.draw_rectangle(ctx,self.width,self.height)
			ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
			#DRAW TEXT
			m = self.starty + 5
			self.theme.draw_text(ctx, ' ' + self.time, 0, m, self.font, self.fontsize + 8,  self.width,pango.ALIGN_CENTER)
			m = m + 25
			self.theme.draw_text(ctx, self.date, 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
			m = m + 40
			self.theme.draw_text(ctx, self.username + '@' + self.hostname, 0, m, self.font, self.fontsize + 1,  self.width,pango.ALIGN_CENTER)
			m = m + 20
			self.theme.draw_text(ctx, self.distro, 0, m, self.font, self.fontsize + 1,  self.width,pango.ALIGN_CENTER)
			m = m + 20
			self.theme.draw_text(ctx, 'kernel: ' + self.kernel, 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
			m = m + 40
			self.theme.draw_text(ctx, self.cpu_name, 0, m, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
			
			m = m + 30
			ctx.save()
			#d = 1
			if self.cpu_nb == 1:
				ctx.save()
				ctx.translate(65,m)
				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
				a = (40* self.cpu_load[0])/100
				self.theme.draw_rounded_rectangle(ctx,10,50,50)
				ctx.translate(5,5)
				ctx.translate (0,40-a)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])	
				self.theme.draw_rectangle(ctx,40,a)
				ctx.translate(75,-5-(40-a))
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.theme.draw_text(ctx, 'CPU' , -75-70, 0, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
				self.theme.draw_text(ctx,str( a)+ '%', -75-70, 30, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)

				ctx.restore()
			if self.cpu_nb >= 2:
				ctx.translate(25,m)
				a = (40* self.cpu_load[1])/100
				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
				ctx.save()
				self.theme.draw_rounded_rectangle(ctx,10,50,50)
				ctx.translate(5,5)
				ctx.translate (0,40-a)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])	
				self.theme.draw_rectangle(ctx,40,a)
				ctx.translate(75,-5-(40-a))
				ctx.restore()
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.theme.draw_text(ctx, 'CPU 1' , -65, 0, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
				self.theme.draw_text(ctx,str( a)+ '%', -65, 30, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
				ctx.translate(75,0)


				a = (40* self.cpu_load[2])/100
				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
				ctx.save()
				self.theme.draw_rounded_rectangle(ctx,10,50,50)
				ctx.translate(5,5)
				ctx.translate (0,40-a)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
				self.theme.draw_rectangle(ctx,40,a)
				ctx.restore()
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.theme.draw_text(ctx, 'CPU 2' , -65, 0, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
				self.theme.draw_text(ctx,str( a)+ '%' , -65, 30, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
				ctx.restore()
		
				d = 4
				if self.cpu_nb == 4:#self.cpu_nb
					ctx.save()
					m = m +60
					ctx.translate (25,m)
					a = (40* self.cpu_load[3])/100
					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
					ctx.save()
					self.theme.draw_rounded_rectangle(ctx,10,50,50)
					ctx.translate(5,5)
					ctx.translate (0,40-a)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])	
					self.theme.draw_rectangle(ctx,40,a)
					ctx.translate(75,-5-(40-a))
					ctx.restore()
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.theme.draw_text(ctx, 'CPU 3' , -65, 0, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
					self.theme.draw_text(ctx,str( a)+ '%', -65, 30, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
					ctx.translate(75,0)


					a = (40* self.cpu_load[4])/100
					ctx.save()
					ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)

					ctx.translate(5,5)
					ctx.translate (0,40-a)
					ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
					self.theme.draw_rectangle(ctx,40,a)
					ctx.restore()
					ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
					self.theme.draw_text(ctx, 'CPU 4' , -65, 0, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
					self.theme.draw_text(ctx,str( a)+ '%' , -65, 30, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)
					self.theme.draw_rounded_rectangle(ctx,10,50,50)
					ctx.restore()
			m = m +60
			ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
			self.theme.draw_text(ctx, 'Load : ' + self.avg_load, 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)

			m = m +20
			ctx.save()
			ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
			self.theme.draw_text(ctx, 'Ram ' + str(self.mem_used) + '%', 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
			ctx.translate(0,m)
			ctx.translate(20,15)
			ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
			self.theme.draw_rectangle(ctx,140,5)
			ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
			self.theme.draw_rectangle(ctx,(self.mem_used*100)/140,5)
			ctx.translate(-20,-15)
			m = m +20
			ctx.restore()
			ctx.save()
			ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
			self.theme.draw_text(ctx,'Swap ' + str(self.swap_used)+ "%", 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
			ctx.translate(0,m)
			ctx.translate(20,15)
			ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
			self.theme.draw_rectangle(ctx,140,5)
			ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
			self.theme.draw_rectangle(ctx,(self.swap_used*100)/140,5)
			ctx.translate(-20,-15)
			ctx.restore()
			ctx.save()
			m = m +30
			ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
			self.theme.draw_text(ctx, 'IP : ' + self.ip, 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
			m = m +25
			self.theme.draw_text(ctx, 'Upload - ' + str(self.upload)[:3] + ' KB/sec', 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
			m = m +20

			self.theme.draw_text(ctx, 'Download - ' + str(self.download)[:3] + ' KB/sec', 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
			m = m +40
			ctx.restore()
			ctx.save()
			for i in self.disks:
				a = sensors.disk_get_usage(i)
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.theme.draw_text(ctx,a[0]+  ' ' + a[4], 0, m, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)
				ctx.translate(0,m)
				ctx.translate(20,15)
				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
				self.theme.draw_rectangle(ctx,140,5)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])

				self.theme.draw_rectangle(ctx,(int(a[4].replace('%',''))*140)/100,5)
				ctx.translate(-20,-15)
				ctx.restore()
				ctx.save()
				m = m +30
		





			if self.bat_list and self.bat_data !=[] and self.wire_list:
				ctx.translate(25,m)
				a = (40*self.bat_load)/100
	
				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)	
				ctx.save()
				self.theme.draw_rounded_rectangle(ctx,10,50,50)

				ctx.translate(5,5)
				ctx.translate (0,40-a)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])		
				self.theme.draw_rectangle(ctx,40,a)
				ctx.translate(75,-5-(40-a))
				ctx.restore()
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.theme.draw_text(ctx, self.bat_list[0] , -65, 0, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)

				self.theme.draw_text(ctx,str(self.bat_load) + '%', -65, 30, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)

				ctx.translate(75,0)



				a = (40* int(self.wire_data['percentage']))/100

				ctx.set_source_rgba(self.color_background[0], self.color_background[1], self.color_background[2],0.2)
				ctx.save()
				self.theme.draw_rounded_rectangle(ctx,10,50,50)

				ctx.translate(5,5)
				ctx.translate (0,40-a)
				ctx.set_source_rgba(self.color_graph[0], self.color_graph[1], self.color_graph[2],self.color_graph[3])
				self.theme.draw_rectangle(ctx,40,a)
				ctx.restore()
				ctx.set_source_rgba(self.color_text[0], self.color_text[1], self.color_text[2],self.color_text[3])
				self.theme.draw_text(ctx, self.wire_list[0] , -65, 0, self.font, self.fontsize,  self.width,pango.ALIGN_CENTER)

				self.theme.draw_text(ctx,str( int(self.wire_data['percentage']))+ '%' , -65, 30, self.font, self.fontsize - 2,  self.width,pango.ALIGN_CENTER)

			m = m +60
			if self.height != m and self.expand == False:
				self.height = m
#							ctx.translate(-20,-15)self.theme.draw_text(ctx, self.theme_name, 0, 50, self.font, self.fontsize,  self.width,pango.ALIGN_LEFT)

#			self.theme.draw_text(ctx, 'mouse x ' + str(self.mousex ) + ' \n mouse y ' + str(self.mousey ) , 0, 170, self.font, self.fontsize,  self.width,pango.ALIGN_LEFT)


			# render svg-file

			# render png-file
			#ctx.set_source_surface(self.theme['example-test.png'], 0, 0)
			#ctx.paint()
	
	def on_draw_shape (self, ctx):
		if self.theme:
			ctx.set_source_rgba(0, 0, 0,1)	
			self.theme.draw_rectangle(ctx,self.width,self.height)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(SysmonitorScreenlet)

