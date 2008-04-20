#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  KarambaScreenlet (c) Helder Fraga aka whise <helder.fraga@hotmail.com>

import screenlets
from screenlets.options import StringOption , BoolOption , IntOption , FileOption , DirectoryOption , ListOption , AccountOption , TimeOption , FontOption, ColorOption , ImageOption
from screenlets.options import create_option_from_node
from screenlets import DefaultMenuItem , sensors
import pango
import gobject
import gtk
import cairo
import os
from sys import path
import commands

class KarambaScreenlet (screenlets.Screenlet):
	"""A Screenlet that loads simple karamba themes, still beta"""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'KarambaScreenlet'
	__version__	= '0.32'
	__author__	= 'Whise'
	__desc__	= __doc__	# set description to docstring of class
	
	# editable options (options that are editable through the UI)

	hover = False
	number = 0
	karambafile = ''
	update_karamba = False
	karamba_data = []
	karamba_mouse_data = []
	has_karamba_theme = False
	font = 'Sans'
	font_backup = 'Sans'
	mypath =path[0] + '/'
	font_size = 7
	font_size_backup = 7
	font_color = (0,0,0,1)
	font_color_backup = (0,0,0,1)
	align = pango.ALIGN_LEFT
	karamba_height = 100
	karamba_width = 100
	karambafile_choice = []
	oldcpu = [0,0,0,0,0,0]
	newcpu = [0,0,0,0,0,0]
	cpu = [0,0,0,0,0,0]
	loads = []
	value = 1
	nb_points = 60
	groupx = 0
	groupy = 0
	load = {}
	ram = 0
	swap = 0
	used_ram = 0
	free_ram = 0
	used_swap = 0
	free_swap = 0
	disk = []
	diskp ={}
	upload = {}
	download = {}
	newnet_down = {}
	newnet_up = {}
	oldnet_down = {}
	oldnet_up = {}
	rot = True
	rotstart ={}
	rotate = {}
	has_updated = False
	__timeout = None
	dd = 0
	for a in os.listdir(mypath):
		
		if os.path.isfile(mypath  + a ) and a.lower().endswith('theme'):
			karambafile_choice.append(mypath + a)
	karambafile_choice.sort()
	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=127, height=127, 
			uses_theme=True, **keyword_args)
		# set theme
		for i in range(self.nb_points):
			self.loads.append(0)
		self.theme_name = "default"
		# add option group
		self.add_options_group('Karamba', 'This is an example of ' +\
			' editable options within an OptionGroup ...')
		# add editable option to the group
		self.add_option(StringOption('Karamba','karambafile',			# attribute-name
			self.karambafile,						# default-value
			'Karamba Theme', 						# widget-label
			'Karamba Theme ...'	# description
			,self.karambafile_choice))



		# ADD a 1 second (1000) TIMER
		#self.update()
		#self.set_update_interval(1000)
		#self.4 = gobject.timeout_add(500, self.update)

	def set_update_interval (self, interval):
		"""Set the update-time in milliseconds."""
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(interval, self.update)

	def update (self):

		if self.has_updated == False :
			self.has_updated = True
			self.redraw_canvas()
		
		return True # keep running this event	
	
	# ONLY FOR TESTING!!!!!!!!!



	def on_after_set_atribute(self,name, value):
		"""Called after setting screenlet atributes"""

		if name == 'karambafile': 
			if value.startswith('/'):
				try:self.loadkaramba(self.karambafile )
				except:pass
			else:
				try:self.loadkaramba(self.mypath  + self.karambafile)
				except:pass

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


		if self.karambafile == '' :self.find_first_karamba_theme()
		# add default menu items
		self.add_default_menuitems()
		gobject.threads_init()
		self.set_update_interval(1000)
		
	def on_key_down(self, keycode, keyvalue, event):
		"""Called when a keypress-event occured in Screenlet's window."""
		key = gtk.gdk.keyval_name(event.keyval)
		
		if key == "Return" or key == "Tab":
			screenlets.show_message(self, 'This is the ' + self.__name__ +'\n' + 'It is installed in ' + self.__path__)
	
	def on_load_theme (self):
		"""Called when the theme is reloaded (after loading, before redraw)."""
		pass
	
	def on_menuitem_select (self, id):
		"""Called when a menuitem is selected."""
		if id == "at_runtime":
			screenlets.show_message(self, 'This is an example on a menu created at runtime')
		if id == "at_xml":
			screenlets.show_message(self, 'This is an example on a menu created in the menu.xml')
		if id[:11] == "changetheme":
			# make first letter uppercase (workaround for xml-menu)

			self.karambafile = self.get_screenlet_dir() +id[11:]
			
			self.loadkaramba(self.karambafile)
	def find_first_karamba_theme(self):
		themename = ''
		for findtheme in os.listdir(self.mypath):
			if str(findtheme).lower().endswith('.theme'):
				if themename == '':
					if not os.path.isfile(self.mypath + themename[:-6] + '.py'):
						themename = findtheme
					else: 
						screenlets.show_message(self,'Compatibility for this karamba theme is not yet implemented')
						return False
			if themename != '':
				self.loadkaramba(self.mypath + themename)
	def loadkaramba(self,filename):
		if os.path.isfile(filename[:-6] +'.py'):
			screenlets.show_message(self,'This karamba theme will not work because its not supported yet')
			return False
		self.font = 'Sans'
		self.font_backup = 'Sans'
		self.font_size = 7
		self.font_size_backup = 7
		self.font_color_backup = (1,1,1,1)
		k_data = []
		k_mouse_data =[]
		f = open (filename,'r')
		tmp = f.readlines(2500)
		f.close()
		for line in tmp:
			line = line.replace('       ',' ')
			line = line.replace('      ',' ')	
			line = line.replace('     ',' ')
			line = line.replace('    ',' ')
			line = line.replace('	',' ')
			line = line.replace('  ',' ')
			line = line.replace("  x",' x')
			line = line.replace("  X",' X')
			line = line.replace("  y",' y')
			line = line.replace("  Y",' Y')	


			line = line.replace("  h",' h')
			line = line.replace("  H",' H')
			line = line.replace("  w",' w')
			line = line.replace("  W",' W')	
			line = line.replace("kwrite",'gedit')		
			line = line.replace("~/.superkaramba/",self.mypath )		
						
			
			
			#########################
			#karamba general settings
			#########################
			if line.lower().startswith("x") or line.lower().startswith('<group>') or line.lower().startswith('</group>') or  line.lower().startswith("clickarea"):
				
				k_mouse_data.append(line)
			if not line.lower().startswith("clickarea"):
				if not len(line) < 1 or not line.startswith('#'):
					k_data.append(line)
					
			if line.lower().startswith("karamba"):
				general = line.split(' ')
				for a in general:
					
					#if a.lower().startswith("x"): # X
					#	self.x = int(a[2:])
					#elif a.lower().startswith("y"): # Y
					#	self.y = int(a[2:])
					a.replace(' ','')
					if a.lower().startswith("w="): #WIDTH
						self.karamba_width = int(a[2:])
					elif a.lower().startswith("h="): #HEIGHT
						self.karamba_height = int(a[2:])
						
					#elif a.lower().startswith("locked="): #locked
						
					#	self.lock_position = self.strtobool(a[7:])

		self.karamba_data = k_data
		self.karamba_mouse_data = k_mouse_data
		self.height = self.karamba_height
		self.width = int(self.karamba_width)
	
		self.has_karamba_theme = True
		self.redraw_canvas()
		self.update_shape()			


#		ctx = self.window.window.cairo_create()
#		ctx.set_antialias (cairo.ANTIALIAS_SUBPIXEL)    # ?
		# set a clip region for the expose event
	def strtobool(self,text):

		if text.lower().startswith('false'): return False
		elif text.lower().startswith('true'): return True




	def output_filter(self,output):
		
		if str(output).find(': not found') != -1: output =""
		if str(output).lower().startswith('intel') or str(output).lower().startswith('amd'): output = output.split('\n')[0]
		if str(output).startswith('No sensors found!'): output =''
		elif str(output).startswith('cat'): output =''
		elif str(output).startswith('sh'): output =output[4:]
		elif str(output).startswith('(Not all processes could be identified, non-owned process info'): output = ''
		#if str(output).endswith('%'): output =  int(str(output)[:-1])
		#output = output.split('\n')[0]
		
		return output
	def on_mouse_down (self, event):
		"""Called when a buttonpress-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		
		try:
			if event.button ==1:
				x1 = 0
				y1 = 0
				for line in self.karamba_mouse_data:
					if line.lower().startswith('<group>'):
						a = line.split(' ')
								
						x1 = int(a[1][2:]) 
						y1 = int(a[2][2:])
	
					elif line.lower().startswith('</group>'):
						
								
						x1 = 0
						y1 = 0
					
					elif line.lower().startswith("clickarea"):
						a = line.split(' ')
						
	
						x = x1 + int(a[1][2:])	
						y = y1 + int(a[2][2:])
						w = int(a[3][2:])
						h = int(a[4][2:])
						a[5] = line[line.lower().find('sensor=program'):]
					

						a[6] = line[line.lower().find('onclick='):]
						try:a[7] = line[line.lower().find('program='):]
						except:pass
					
						if a[5].lower().startswith('sensor=program') or a[6].lower().startswith('onclick='):
						
							if self.mousex >= x and self.mousex <= (x + w) and self.mousey >= y and self.mousey <= (y+h):
								
								b =  a[6][9:][:a[6][9:].find(chr(34))]
								if b.startswith('kdialog'):
									screenlets.show_message(self,commands.getoutput(a[7][9:][:a[7][9:].find(chr(34))]))
								else:
									os.system(a[6][9:][:a[6][9:].find(chr(34))])
	
		except: pass
		return False
	
	def on_mouse_enter (self, event):
		"""Called when the mouse enters the Screenlet's window."""
	        pass
		
	def on_mouse_leave (self, event):
		"""Called when the mouse leaves the Screenlet's window."""
		pass

	def on_mouse_move(self, event):
		"""Called when the mouse moves in the Screenlet's window."""
		
		pass

	def on_mouse_up (self, event):
		"""Called when a buttonrelease-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		return False
	
	def on_quit (self):
		"""Callback for handling destroy-event. Perform your cleanup here!"""
		pass
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
		if self.theme:
			# set scale rel. to scale-attribute
			ctx.scale(self.scale, self.scale)
			ctx.set_operator(cairo.OPERATOR_OVER)
			#ctx.set_source_rgba(self.color_example[2], self.color_example[1], self.color_example[0],0.6)	
			#if self.hover:
			#self.theme.draw_rounded_rectangle(ctx,0,0,20,self.width,self.height)



			if self.has_karamba_theme is True :
				config = ['x','y','h','w','font','fontsize','color','path','format','program','value','sensor','align','cpu','mountpoint','device','full','rotation','increment']
				for line in self.karamba_data:
					value = {}

					for atrib in config:
						
						n =  line.lower().find(' ' + str(atrib) + '=')
					
						if n != -1:

							if atrib in ('format','program','device','mountpoint','path','value','font'):
								
								value[atrib] = line[n +len(' ' + str(atrib)+ '='+chr(34)):]
								value[atrib] = value[atrib][:value[atrib].lower().find(chr(34))].strip()




#							elif atrib == ('program'):
#								value[atrib] = line[n +len(' ' + str(atrib)+ '='+chr(34)):]
#								value[atrib] = value[atrib][:value[atrib].lower().find(chr(34))].strip()
					

#							elif atrib == ('device'):
#								value[atrib] = line[n +len(' ' + str(atrib)+ '='+chr(34)):]
#								value[atrib] = value[atrib][:value[atrib].lower().find(chr(34))].strip()
							

#							elif atrib == ('mountpoint'):
#								value[atrib] = line[n +len(' ' + str(atrib)+ '='+chr(34)):]
#								value[atrib] = value[atrib][:value[atrib].lower().find(chr(34))].strip()
						

							
#							elif atrib == ('path'):
#								value[atrib] = line[n +len(' ' + str(atrib)+ '='+chr(34)):]
#								value[atrib] = value[atrib][:value[atrib].lower().find(chr(34))].strip()
							
#							elif atrib == ('value'):
#								value[atrib] = line[n +len(' ' + str(atrib)+ '='+chr(34)):]
#								value[atrib] = value[atrib][:value[atrib].lower().find(chr(34))].strip()
								
#							elif atrib == ('font'):
#								value[atrib] = line[n +len(' ' + str(atrib)+ '='+chr(34)):]
#								value[atrib] = value[atrib][:value[atrib].lower().find(chr(34))].strip()
							

							else:
								value[atrib] = line[n+len(' ' + str(atrib)+ '='):]
								value[atrib] = value[atrib][:value[atrib].lower().find(' ')].strip()
								if atrib is 'align':
									if value[atrib].lower().find(chr(34)) != -1:
										value[atrib] = value[atrib][:-1]
								
							if atrib is 'sensor':
								value[atrib] = value[atrib].lower()
							
							
			
					try:
						if value['x'].find(",") != -1: value['x'] = value['x'].replace(",",'.')
					except:pass
					try:
						if value['y'].find(",") != -1: value['y'] = value['y'].replace(",",'.')
					except:pass
					try:
						if value['w'].find(",") != -1: value['w'] = value['w'].replace(",",'.')
					except:pass
					try:
						if value['h'].find(",") != -1: value['h'] = value['h'].replace(",",'.')
					except:pass
	
					#########################
					#Image settings
					#########################
					#self.update_karamba = True
					ctx.set_source_rgba(self.font_color[0],self.font_color[1],self.font_color[2],self.font_color[3])
					if line.lower().startswith('<group>'):
								
						self.groupx = value['x']
						self.groupy = value['y']
						ctx.translate(int(value['x']), int(value['y']))
									
					elif line.lower().startswith('</group>'):
						ctx.translate(-int(self.groupx), -int(self.groupy))	
						
					elif line.lower().startswith("image"):
						
					
					
						try: a = self.rotate[str(value['path']) + str(self.id)]
						except : self.rotate[str(value['path']) + str(self.id)] = 0
						if 'rotation' in value:
							if str(value['rotation']).lower() == 'program':
							
								self.rotate[str(value['path'])+str(self.id)] = float(commands.getoutput(value['program']))

							else:
								if self.rotate[str(value['path'])+str(self.id)] == 0:self.rotate[str(value['path'])+str(self.id)] = float(value['rotation'])
							if 'increment' in value and value['increment'] != 0:
								
								self.rotate[str(value['path']) + str(self.id)] = self.rotate[str(value['path'])+str(self.id)] + float(value['increment'])

							if 'full' in value:
							
								ro = self.rotate[str(value['path'])+str(self.id)] *(3.14/(float(value['full'])/2))
							else: ro = self.rotate[str(value['path'])+str(self.id)]*(3.14/(360/2))


						if 'path' in value:
							ctx.save()
							ctx.translate(int(value['x']), int(value['y']))	
							ctx.translate(self.width / 2.0, self.height / 2.0)
							if 'rotation' in value:
								
									#except:self.rotate[str(value['path']) + str(self.id)] = 0
								ctx.rotate(ro)
								
							ctx.translate(-(self.width / 2.0), -(self.height / 2.0))
							try:
								png = cairo.ImageSurface.create_from_png(self.get_screenlet_dir()  +self.karambafile[:self.karambafile.find('/')]+'/'+ value['path'])
							
								ctx.set_source_surface(png, 0, 0)
								ctx.paint()
							except: pass								

							ctx.restore()
							png = None
	
					elif line.lower().startswith("defaultfont"):
						ctx.save()
						
						
						#ctx.set_antialias (cairo.ANTIALIAS_SUBPIXEL)    # ?
						if 'font' in value: # Y
							self.font = value['font']
							self.font_backup = value['font']
						if 'fontsize' in value: # Y
							self.font_size = int(int(value['fontsize'])*0.7)
							self.font_size_backup  = self.font_size
						if 'color' in value: # Y
							
							b = value['color'].split(',')
							self.font_color=(float(int(b[0]))/255, float(int(b[1]))/255,float(int(b[2]))/255, 1)
							self.font_color_backup = self.font_color
							ctx.set_source_rgba(self.font_color[0],self.font_color[1],self.font_color[2],self.font_color[3])
								
																
								

						ctx.restore()




					elif line.lower().startswith("text"):
						ctx.save()
						output = ''
					
						align1 = 'LEFT'
						if 'font' in value:
							self.font = value['font']

						else: self.font = self.font_backup
						if 'fontsize' in value:
							self.font_size = int(int(value['fontsize']) *0.68)
						else: self.font_size = self.font_size_backup
						if 'color' in value:								
							c = value['color'].split(',')	
							
							self.font_color=(float(int(c[0]))/255, float(int(c[1]))/255,float(int(c[2]))/255, 1)
						
							ctx.set_source_rgba(self.font_color[0],self.font_color[1],self.font_color[2],self.font_color[3])
						else: 
							self.font_color = self.font_color_backup
							ctx.set_source_rgba(self.font_color[0],self.font_color[1],self.font_color[2],self.font_color[3])
						if 'align' in value:
							align1 = value['align'].upper()
						
						if align1 == 'RIGHT' or align1.startswith(chr(34)+ 'RIGHT'):
							self.align = pango.ALIGN_RIGHT
							xxx = int(value['x'])-self.width
							yyy =  int(value['y'])#-((self.width-30)/2-int(value['x'])/2)
						elif align1 == 'LEFT' or align1.startswith(chr(34)+ 'LEFT'): 
							self.align = pango.ALIGN_LEFT
							xxx = int(value['x'])
							yyy = int(value['y'])
							
						elif align1 == 'CENTER' or align1.startswith(chr(34)+ 'CENTER'):
							self.align = pango.ALIGN_CENTER
							xxx = float(value['x'])-(self.width/2)
							yyy = int(value['y']) # -((self.width-float(value['x']))/2)

						if 'value' in value:
							self.theme.draw_text(ctx, value['value'], xxx, yyy, self.font , self.font_size,self.width,self.align)

						elif 'sensor' in value:
						
						
							if value['sensor'] == 'program':

								if line.find("wget") == -1: 
									
									output = commands.getoutput(value['program'])


							else:		
								
								
								if value['sensor'] == 'cpu':
						
									if 'cpu' in value :option = value['cpu']
									else : option = 0

								elif value['sensor'] == 'network':
									if 'device' in value:option = value['device']
									else:option = 'eth1'
									self.download[option] = 0
									
									self.upload[option] = 0
								elif value['sensor'] == 'disk':
									if 'mountpoint' in value :option = value['mountpoint']
								elif value['sensor'] == 'sensor' : option = ''
								else:
									option = 0

								output = self.get_sensors(value['sensor'],option,value['format'])
							
							if output is not None:
								output = self.output_filter(output)

							self.theme.draw_text(ctx, str(output), xxx, yyy, self.font , self.font_size,self.width,self.align)
			#			if 'align' in atribute and atribute['align'] != '':
			#					align1 = value['align'].upper()
			#			
			#			if align1 == 'RIGHT' or align1.startswith(chr(34)+ 'RIGHT'):
			#				self.align = pango.ALIGN_RIGHT
			#				ctx.translate(-(int(value['x'])-self.width),- int(value['y'])) #-((self.width-30)/2-int(value['x'])/2)
			#			elif align1 == 'LEFT' or align1.startswith(chr(34)+ 'LEFT'): 
			#				self.align = pango.ALIGN_LEFT
			#				ctx.translate(-int(value['x']), -int(value['y'])) 
							
			#			elif align1 == 'CENTER' or align1.startswith(chr(34)+ 'CENTER'):
			#				self.align = pango.ALIGN_CENTER
			#				ctx.translate(-(float(value['x'])-(self.width/2)), -int(value['y']))
						ctx.restore()
			

					elif line.lower().startswith("bar"):
						ctx.save()

						
							
						if 'sensor' in value:
						
						
							if value['sensor'] == 'program':

								if line.find("wget") == -1: 
									
									output = commands.getoutput(value['program'])


							else:		
								
								
								if value['sensor'] == 'cpu':
						
									if 'cpu' in value :option = value['cpu']
									else: option= 0

								elif value['sensor'] == 'network':
									if 'device' in value:option = value['device']
									else:option = 'eth1'
									self.download[option] = 0
									
									self.upload[option] = 0

								elif value['sensor'] == 'disk':

									if 'mountpoint' in value :option = value['mountpoint']
								else:
									option = 0 																			
							
								if value['sensor'] == 'cpu': output = self.cpu[int(option)]	
								elif value['sensor'] == 'memory' :
									if 'format' in value :
										if value['format'] == '%umb' or value['format'] == '%um' or value['format'] == '': 
											output = self.ram	

										if value['format'] == '%usb' or value['format'] == '%us': 
											output = self.swap
									else: output = self.ram
								elif value['sensor'] == 'disk' :
										try:output = self.diskp[option]
										except: output = 0
								elif value['sensor'] == 'network' :
									if value['format'] == '%in': 
										try:output = self.download[option]
										except:output = 0
									if value['format'] == '%out': 
										try:output = self.upload[option]
										except:output = 0
								elif value['sensor'] == 'sensor' : pass
								else: 	output = self.get_sensors(value['sensor'],option,value['format'])
								
						if output is not None:
							output = self.output_filter(output)
						else: output  = ''
						
												
						
						

						if 'path' in value: # Y
							
							png2 = cairo.ImageSurface.create_from_png(self.get_screenlet_dir() +self.karambafile[:self.karambafile.find('/')]+'/' + value['path'])
							ctx.translate(int(value['x']), int(value['y'])) 
							ctx.set_source_rgba(1, 1, 1, 1)

							if output != '':
								try:ctx.rectangle (0,0,(int(output)*int(png2.get_width()))/100,self.height)
								except:pass
							ctx.set_source_surface(png2, 0, 0)
							#ctx.paint()
							ctx.fill()
							
								
						ctx.restore()
					
					elif line.lower().startswith("graph"):
						ctx.save()
						
						if 'sensor' in value:
						
						
							if value['sensor'] == 'program':

								text = value['program']

								if line.find("wget") == -1: 
									
									output = commands.getoutput(text)


							else:		
								
								if value['sensor'] == 'cpu':
						
									if 'cpu' in value :option = value['cpu']
									else: option= 0

								elif value['sensor'] == 'network':
									if 'device' in value:option = value['device']
									else:option = 'eth1'
									self.download[option] = 0
									
									self.upload[option] = 0
								elif value['sensor'] == 'disk':
									if 'mountpoint' in value :option = value['mountpoint']
								else:
									option = 0



																		
							
								if value['sensor'] == 'cpu': output = self.cpu[int(option)]	
								elif value['sensor'] == 'memory' :
									if not 'format' in value : value['format'] = '%umb'
									if value['format'] == '%umb' or value['format'] == '%um' or value['format'] == '': 
										output = self.ram	
									if value['format'] == '%usb' or value['format'] == '%us': 
										output = self.swap
								elif value['sensor'] == 'disk' :
										try:output = self.diskp[option]
										except: output = 0
								elif value['sensor'] == 'network' :
									if value['format'] == '%in': 
										output = self.download[str(option)]
										
									if value['format'] == '%out': 
										if not option in value:
											output = 0
										else:output = self.upload[option]

								elif value['sensor'] == 'sensor' : pass
								else: 
									try:output = self.get_sensors(value['sensor'],option,value['format'])
									except:	output = self.get_sensors(value['sensor'],option,'')						
					
						#self.load[str(value['sensor']) + str(option )] = self.loads
						if output is not None:
							output = self.output_filter(output)
						else: output  = ''
							
						if not output is '':
							del(self.loads[0])
							if 'color' in value:								
								c = value['color'].split(',')
								ctx.set_source_rgba(float(int(c[0]))/255, float(int(c[1]))/255,float(int(c[2]))/255, 1)
							self.loads.append(str(value['sensor']) + str(option) + str(output))

							
							
							ctx.translate(float(value['x']), float(value['y'])) 
							ctx.move_to(0,int(value['h']))
							i=0
							for l in self.loads:
								if l != 0:
									a = str(l)
									
									a= a[len(str(value['sensor']) + str(option)):]
									
									if a == '': a = '0'
								else: a = l
								if str(l).startswith(str(value['sensor']) + str(option)) or l == 0:
									try:ctx.line_to(i*((int(value['w']))/(self.nb_points-1)),( int(value['h']))-float(a)*(float(value['h'])/100))
									except:pass
									i+=1
						
							ctx.line_to(int(value['w']),int(value['h']))
							#ctx.close_path()
							ctx.stroke()
							ctx.translate(-float(value['x']), -float(value['y'])) 
							ctx.fill()
							ctx.restore






			if not self.has_karamba_theme : self.theme.render(ctx, 'karamba')
			self.has_updated = False

	

	def get_sensors(self,sensor,option,format):
		if sensor.lower() == 'memory':

			self.used_ram = sensors.mem_get_usedmem()
			self.total_ram = sensors.mem_get_total()
			self.free_ram = self.total_ram - self.used_ram
			self.ram = (float(self.used_ram)/float(self.total_ram))*100
			self.used_swap = sensors.mem_get_usedswap()
			self.total_swap = sensors.mem_get_totalswap()
			self.free_swap = self.total_swap - self.used_swap
			self.swap = (float(self.used_swap)/float(self.total_swap))*100
			if format is '' : format = '%um'
			#if len(format) == 0 : format == ('%umb')
			if format.find('%umb') != -1:format = format.replace('%umb',str(self.used_ram))
			if format.find('%fmb') != -1:format = format.replace('%fmb',str(self.free_ram))		
			if format.find('%um') != -1:format = format.replace('%um',str(self.used_ram))
			if format.find('%fm') != -1:format = format.replace('%fm',str(self.free_ram))
			if format.find('%tm') != -1:format = format.replace('%tm',str(self.total_ram))

			if format.find('%fs') != -1:format = format.replace('%fs',str(self.free_swap))
			if format.find('%us') != -1:format = format.replace('%us',str(self.used_swap))
			if format.find('%ts') != -1:format = format.replace('%ts',str(self.total_swap))


			return format 
		elif sensor.lower() == 'uptime':
			self.uptime = sensors.sys_get_uptime()
			format = self.uptime

			return format 
		elif sensor.lower() == 'cpu':
			
			if format is '' : format = '%v'
			try:self.newcpu[int(option)] = sensors.cpu_get_load(int(option))
			except : 
				option = 0
				self.newcpu[int(option)] = sensors.cpu_get_load(int(option))
			self.cpu[int(option)] = self.newcpu[int(option)] - self.oldcpu[int(option)]
			self.oldcpu[int(option)] = self.newcpu[int(option)]
			if self.cpu[int(option)] > 99 :self.cpu[int(option)] = 99
			elif self.cpu[int(option)] < 0 :self.cpu[int(option)] = 0
			if format.find('%v') != -1:format = format.replace('%v',str(int(self.cpu[int(option)])))
			elif format.find('%load') != -1:format = format.replace('%load',str(int(self.cpu[int(option)])))			
			elif format.find('%user') != -1:format = format.replace('%user',str(int(self.cpu[int(option)])))	


			return format 

		elif sensor.lower() == 'network':
			try:p = sensors.net_get_activity(str(option))
			except:return 0
			self.newnet_down[option] = p[0]
			self.newnet_up[option] = p[1]				
			
			try:
				self.download[option] = (self.newnet_down[option] - self.oldnet_down[option])/ 1024
				self.upload[option] = (self.newnet_up[option] - self.oldnet_up[option])/1024
			except:
				self.download[option] = 0
				self.upload[option] = 0
			
			self.oldnet_down[option] = self.newnet_down[option]
			self.oldnet_up[option] = self.newnet_up[option]
			self.download[option] = str(self.download[option])[:str(self.download[option]).find('.')]
			self.upload[option] = str(self.upload[option])[:str(self.upload[option]).find('.')]
			if format.find('%in') != -1:format = format.replace('%in',self.download[option])
			if format.find('%out') != -1:format = format.replace('%out',self.upload[option])
			return format
		elif sensor.lower() == 'disk':
			try:
				self.disk = sensors.disk_get_drive_info(option)	
				if format.find('%up') != -1:format = format.replace('%up', self.disk['quota'].replace('%',''))
				if format.find('%ug') != -1:format = format.replace('%ug', self.disk['used'].replace('G',''))
				if format.find('%fg') != -1:format = format.replace('%fg', self.disk['free'].replace('G',''))
				if format.find('%f') != -1:format = format.replace('%f', self.disk['free'].replace('G',''))
				if format.find('%tg') != -1:format = format.replace('%tg', self.disk['size'].replace('G',''))
				if format.find('%u') != -1:format = format.replace('%u', str(int(self.disk['used'].replace('G',''))*1024))
				if format.find('%t') != -1:format = format.replace('%t', str(int(self.disk['size'].replace('G',''))*1024))
				self.diskp[option] = self.disk['quota'].replace('%','')
					
				return format 			
			except:
				pass
		elif sensor.lower() == 'time':
			if format.find('ss') != -1:format = format.replace('ss',str(sensors.cal_get_second()))
			if format.find('dddd') != -1:format = format.replace('dddd',str(sensors.cal_get_day_name()))
			elif format.find('ddd') != -1:format = format.replace('ddd',str(sensors.cal_get_day_name()))
			if format.find('dd') != -1:format = format.replace('dd',str(sensors.cal_get_day()))
			elif format.find('d ') != -1:format = format.replace('d ',str(sensors.cal_get_day())+' ')
			if format.find('MMMM') != -1:format = format.replace('MMMM',str(sensors.cal_get_month_name()))
			elif format.find('MMM') != -1:format = format.replace('MMM',str(sensors.cal_get_month_name()))
			if format.find('MM') != -1:format = format.replace('MM',str(sensors.cal_get_month()))
			elif format.find('M') != -1:format = format.replace('M',str(sensors.cal_get_month()))
			if format.find('ap') != -1:format = format.replace('ap',str(sensors.cal_get_ampm()))		
			if format.find('hh:mm') != -1:format = format.replace('hh:mm',str(sensors.cal_get_hour())+':'+str(sensors.cal_get_minute()))
			elif format.find('h:mm') != -1:format = format.replace('h:mm',str(sensors.cal_get_hour())+':'+str(sensors.cal_get_minute()))	
			if format.find('hh') != -1:format = format.replace('hh',str(sensors.cal_get_hour()))
			if format.find('mm') != -1:format = format.replace('mm',str(sensors.cal_get_minute()))		
			if format.find('yyyy') != -1:format = format.replace('yyyy',str(sensors.cal_get_year()))
			elif format.find('yy') != -1:format = format.replace('yy',str(sensors.cal_get_year()[2:]))
			return format 
	def on_draw_shape (self, ctx):
		ctx.rectangle (0,0,self.width,self.height)
		ctx.fill()

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(KarambaScreenlet)

