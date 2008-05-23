#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  SidebarScreenlet (c) Helder Fraga (Whise) 2008

import screenlets
from screenlets import DefaultMenuItem, utils, session
from screenlets.options import BoolOption, StringOption, IntOption, ColorOption
import gtk
import cairo
import os
import math
from sys import argv
import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	if getattr(dbus, 'version', (0,0,0)) <= (0,80,0):
		
		import dbus.glib
	else:
		
		from dbus.mainloop.glib import DBusGMainLoop
		DBusGMainLoop(set_as_default=True)
	screenlets.Screenlet.docking = True
else:
	screenlets.Screenlet.docking = False
	print 'Auto docking will not be available. Upgrade your python dbus libraries'
import time
import wnck

action = dbus.service.method


class SidebarScreenlet (screenlets.Screenlet):
	"""A themeable Sidebar that sits in any edge of the screen and allows you to dock and control all other screenlets , it also allows you to install new screenlets with drag and drop support. It can also act like a gnome menu."""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__ = 'SidebarScreenlet'
	__version__ = '3'
	__author__ = 'Helder Fraga aka Whise'

	__desc__	= __doc__	# set description to docstring of class
	
	# editable options (options that are editable through the UI)
	size = 150



	ebox = None

	BUS 	= 'org.screenlets' #'org.freedesktop.Screenlets'
	PATH	= '/org/screenlets/' #'/org/freedesktop/Screenlets/'
	IFACE 	= 'org.screenlets.ScreenletService' #'org.freedesktop.ScreenletService'

	bg_style = 'Theme'
	bg_style_sel = ['Theme','Custom','System']	
	started = False
	rgba_color = (0, 0, 0, 1)

	# editable settings
	add_screenlet_as_widget = False
	DIR_USER = os.environ['HOME'] + '/.screenlets'
	alignment = 'Right'
	alignment_sel = ['Right','Right_Reserved','Left','Left_Reserved','Top','Top_Reserved','Bottom','Bottom_Reserved']	
	mypath = argv[0][:argv[0].find('SidebarScreenlet.py')].strip()
	killall = False
	dock = True
	x_old = 0
	y_old = 0
	width_old = 0
	height_old = 0
	old_alignment = 'Right'

	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self,is_widget=False, width=160, height=1024,is_sticky=True, drag_drop=True, uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# create menu
		self.add_options_group('Sidebar', 'Options')
	#	self.add_option(BoolOption('Sidebar', 'autosize',bool(self.autosize), 'Autosize To fit Screen','Autosize To fit Screen'))
		self.add_option(StringOption('Sidebar', 'alignment', self.alignment,'Select Alignment', 'Select sidebar alignment options',choices = self.alignment_sel))
        	self.add_option(IntOption('Sidebar', 'size', self.size, 'Size of the Sidebar',  'The width or the height of the sidebar', min=50, max=250))

		self.add_option(BoolOption('Sidebar', 'killall',bool(self.killall), 'killall screenlets on exit','kill all screenlets when you quit the sidebar'))
		self.add_option(StringOption('Sidebar', 'bg_style', self.bg_style,'Backgound Style', 'Select sidebar backgound style scheme',choices = self.bg_style_sel))
		self.add_option(ColorOption('Sidebar', 'rgba_color', self.rgba_color, 'Background Color', 'The background color of the sidebar if custom style is selected) ...'))
		self.add_option(BoolOption('Sidebar', 'dock',bool(self.dock), 'Dock other Screenlets','Dock other Screenlets to the sidebar(experimental)'))

		self.ebox =  gtk.EventBox()
		self.quit_on_close = True
		# add editable settings
		self.window.add(self.ebox)		
		self.free_screen_space()
		self.keep_below = True
		self.lock_position = True
		self.keep_above = False
		self.lock_position = True
        	self.x_ratio =  self.width / 160.0
        	self.y_ratio =  self.height / 1024.0	
		self.disable_option('scale')
		self.disable_option('y')
		self.disable_option('x')
		self.disable_option('keep_above')
		self.disable_option('keep_below')
		self.disable_option('scale')
		self.disable_option('lock_position')
		#try:
		#	self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
		#except:
		#	pass
		self.__screen = wnck.screen_get_default()
		self.__screen.connect("window_opened", 	self.window_opened)
		self.__screen.connect("window_closed",  self.window_closed)
		#self.timer = gobject.timeout_add( 5000, self.update)
		while gtk.events_pending():
			gtk.main_iteration()
		wins = self.__screen.get_windows_stacked()
		for win in wins:
			name = win.get_name()[:-3]
			if name.endswith("Screenlet") and name != 'SidebarScreenlet':		
				win.connect("geometry_changed", self.update_win)
		if self.session:
			if self.session.instances == []:
		  		if os.path.exists(self.mypath + 'startup') and os.path.isdir(self.mypath + 'startup'): #is it a valid folder?
					for f in os.listdir(self.mypath + 'startup'):     
						print 'launching' + f
						try:
							if f != ('Sidebar'):
								screenlets.launch_screenlet(f)
						except:
							pass


	def on_quit(self):
		if self.killall:
			for s in utils.list_running_screenlets():
				if s != 'SidebarScreenlet':
					if s.endswith('Screenlet'):
						s = s[:-9]
					try:
						self.quit_screenlet_by_name(s)
					except:
						pass
			for s in utils.list_running_screenlets():
				if s != 'SidebarScreenlet' :
					if s.endswith('Screenlet'):
						s = s[:-9]
					try:
						self.quit_screenlet_by_name(s)
					except:
						pass
			exit()
	def align_all_screenlets(self,name):
	
		service = screenlets.services.get_service_by_name(name)
		
		if service != None and service and self.dock and self.alignment != self.old_alignment:
			

			for f in service.list_instances():
				
				slw= int(service.get(f,'width'))				
				slh= int(service.get(f,'height'))
				slx= int(service.get(f,'x'))
				sly= int(service.get(f,'y'))
				slsc=service.get(f,'scale')
				slww = slw/2
				slhh = slh/2
				posx = slww + slx
				posy = slhh + sly
				set = service.set
				if self.old_alignment.startswith('Left') or self.old_alignment.startswith('Right'):
 					
					if self.alignment.startswith('Right') or self.alignment.startswith('Left'):
						set(f,'x',self.x +4)

						#x1 = int(self.x_old+self.width) - int(slx+(slw*slsc))
						#after_x =self.x+ x1

						#x1 = int(slx) - int(self.x_old)
						#after_x =  (self.x + self.width ) - (x1+int(slw*slsc))
					#	self.free_screen_space()
					#	set(f,'x',self.x +4)

					elif self.alignment.startswith('Bottom') or self.alignment.startswith('Top'):
						
						after_x =sly - self.y_old
						set(f,'y',self.y+4)	
						set(f,'x',after_x)					

				elif self.old_alignment.startswith('Top') or self.old_alignment.startswith('Bottom'):	
		
					if self.alignment.startswith('Right') or self.alignment.startswith('Left'):
						after_y =slx - self.x_old
						set(f,'x',self.x+4)
						set(f,'y',after_y)	



					elif self.alignment.startswith('Bottom') or self.alignment.startswith('Top'):
						
						
						set(f,'y',self.y+4)	
						
				

				

	@action(IFACE)
	def set (self, id, attrib, value):
		"""Ask the assigned Screenlet to set the given attribute to 'value'. The 
		instance with the given id will be accessed. """
		sl = screenlets.session.ScreenletSession.get_instance_by_id(id)

		if sl == None:
			sl = screenlets.screenlet
		if sl.get_option_by_name(attrib) == None:
			raise Exception('Trying to access invalid option "%s".' % attrib)
		else:
			o = sl.get_option_by_name(attrib)
			if not o.protected:
				setattr(sl, attrib, value)
			else:
				print "Cannot get/set protected options through service."

	def quit_screenlet_by_name (self, name):
		"""Quit all instances of the given screenlet type."""
		# get service for instance and call quit method
		service = screenlets.services.get_service_by_name(name)

		if service:
			
			service.quit() 
	def on_mouse_down(self,event):

		self.window.set_keep_below(1)
		
	def dock_screenlet(self,win,x,y):

					
		name = win.get_name()[:-3]
		
		
		service = screenlets.services.get_service_by_name(name[:-9])
		
		if service != None and service and self.dock:
			set = service.set

			for f in service.list_instances():
				sizable=service.get(f,'is_sizable')
				if sizable == True or sizable == None:
					if self.alignment.startswith('Left') or self.alignment.startswith('Right'):	
						slx=float(service.get(f,'x'))
						if int(x) == int(slx) :
							slsc=float(service.get(f,'scale'))
							slw= int(service.get(f,'width'))
							after_scale = self.calculate_width_to_dock(slw,slsc)
							after_x = int(self.x + 4)
							#sldragged= service.get(f,'is_dragged')
							#if sldragged == 0:
					
							if int((slw*slsc)+8)!= int(self.width) :
								set(f,'scale',after_scale)
								set(f,'x',after_x)
								
							elif int(slx) == int(after_x-4):
								pass	
							elif int(slx) != int(after_x):
								set(f,'x',after_x)	
				
					elif self.alignment.startswith('Top') or self.alignment.startswith('Bottom'):	
	
						sly=float(service.get(f,'y'))
						if int(y) == int(sly):
							slsc=float(service.get(f,'scale'))
							slh= int(service.get(f,'height'))
							after_scale = self.calculate_height_to_dock(slh,slsc)
							after_y = int(self.y + 4)
							#sldragged= service.get(f,'is_dragged')
							#if sldragged == 0:
						
							if int((slh*slsc)+8)!= int(self.height) :
								set(f,'scale',after_scale)
								set(f,'y',after_y)
							elif int(sly) == int(after_y-4):
								pass	
							elif int(sly) != int(after_y):
								set(f,'y',after_y)
	
					
	def calculate_width_to_dock(self,w,s):
	

		sw = float(s)*float(w) +8
		newscale = (float(self.width)*float(s))/float(sw)

		return newscale

	def calculate_height_to_dock(self,h,s):
	

		sh = (float(s)*float(h)) +8
		newscale = (float(self.height)*float(s))/float(sh)

		return newscale

	def window_opened (self, screen, win):
		#print "window_opened: "+str(window)
		
		name = win.get_name()[:-3]
		
		if name.endswith("Screenlet") and name != 'SidebarScreenlet':		
			win.connect("geometry_changed", self.update_win)
			
	# called when a wnckwin is closed
	def window_closed (self, screen, win):
		pass

	def update(self):
		for win in self.__screen.get_windows_stacked():
			name = win.get_name()[:-3]
			if name.endswith("Screenlet") and name != 'SidebarScreenlet':	
				self.update_win(win)

	def update_win (self, win):

		

		if self.docking == False:
			return False
		geom = win.get_geometry()
		slx = geom[0]
		sly = geom[1]
		slw = geom[2]
		slh = geom[3]
			
		slww = slw/2
		slhh = slh/2		
		posx = slww + slx
		posy = slhh + sly
			
		
		if posx >=  self.x and posx < (self.x + (self.width*self.scale)) and  posy >=  self.y and posy < (self.y + (self.height*self.scale)) :
			if self.alignment.startswith('Left') or self.alignment.startswith('Right'):	
				if int(slx) != int(self.x +4) or int(slw) != int((self.width*self.scale)-8):	
					print 'Docking to right or left'	
					self.dock_screenlet(win,slx,sly)	
			elif self.alignment.startswith('Top'):	
				if int(sly) != int(self.y +4) or int(slh) != int((self.height*self.scale)-8):	
					print 'Docking to top'
					self.dock_screenlet(win,slx,sly)	
			elif self.alignment.startswith('Bottom'):	
				if int(sly) != int(self.y +4) or int(slh) != int((self.height*self.scale)-8):	
					print 'Docking to bottom'
					self.dock_screenlet(win,slx,sly)		

	def __setattr__(self, name, value):
		if name == 'alignment':
			self.__dict__['old_alignment'] = self.alignment
			self.__dict__['x_old'] = self.x
			self.__dict__['y_old'] = self.y
			self.__dict__['width_old'] = self.width
			self.__dict__['height_old'] = self.height
		if name == 'keep_above':
			value = False
			if self.window:
				self.window.set_keep_above(0)
				self.is_widget = not self.is_widget
				self.is_widget = not self.is_widget
 		if name == 'keep_below':
			value = True
			if self.window:
			
				self.window.set_keep_below(1)

 		if name == 'lock_position':
			value = True


		screenlets.Screenlet.__setattr__(self, name, value)

		if name == ('alignment'):
			self.free_screen_space()

			if value == 'Right' or value == 'Right_Reserved':
				self.x = gtk.gdk.screen_width() - int((self.size *self.scale))
				self.window.move(gtk.gdk.screen_width() - int((self.size *self.scale)),0)
         			self.width = self.size
           			self.height = gtk.gdk.screen_height()
			elif value == 'Left' or value == 'Left_Reserved':
				self.x = 0
				self.window.move(0,0)
         			self.width = self.size
           			self.height = gtk.gdk.screen_height()
			elif value == 'Top' or value == 'Top_Reserved':
				self.x = 0
				self.window.move(0,0)	
				#self.sidebar_height = gtk.gdk.screen_width()
         			self.width = gtk.gdk.screen_width()
           			self.height = self.size
			elif value == 'Bottom' or value == 'Bottom_Reserved':
				self.x = 0
				#self.window.move(0,0)	
				#self.sidebar_height = gtk.gdk.screen_width()
         			self.width = gtk.gdk.screen_width()
           			self.height = self.size
				self.y = gtk.gdk.screen_height() - self.height
			self.redraw_canvas()
					

			if self.started == True:
				#for s in utils.list_running_screenlets():
				#	if s != 'SidebarScreenlet':
				#		if s.endswith('Screenlet'):
				#			s = s[:-9]
				#			self.align_all_screenlets(s)	

				for win in self.__screen.get_windows_stacked():
					name = win.get_name()[:-3]
					if name.endswith("Screenlet") and name != 'SidebarScreenlet':	
						geom = win.get_geometry()
						slx = geom[0]
						sly = geom[1]
						slw = geom[2]
						slh = geom[3]

						slww = slw/2
						slhh = slh/2		
						posx = slww + slx
						posy = slhh + sly
						
		
						if posx >=  self.x_old and posx < (self.x_old + (self.width_old*self.scale)) and  posy >=  self.y_old and posy < (self.y_old + (self.height_old*self.scale)) and self.docking == True:
													
							self.align_all_screenlets(name[:-9])

				self.reserve_screen_space()

		if name == ('size'):
			if self.alignment.startswith('Left') or self.alignment.startswith('Right'):

         			self.width = value
			elif self.alignment.startswith('Top') or self.alignment.startswith('Bottom'):
        	   		self.height = value
        	#	self.x_ratio =  self.width / 160.0
        	#	self.y_ratio =  self.height / 1024.0
			self.alignment = self.alignment
		if name == 'bg_style' or 'rgba_color':
			if self.started == True:

				self.redraw_canvas()

	def free_screen_space(self):
		self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
		time.sleep(0.1)

	def reserve_screen_space(self):
		self.free_screen_space()
		if self.alignment == 'Right':
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
				
		elif self.alignment == 'Left':
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
		elif self.alignment == 'Top':
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
		elif self.alignment == 'Bottom':
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
				
		elif self.alignment == 'Right_Reserved':
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [0, int((self.width *self.scale)), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

		elif self.alignment == 'Left_Reserved' :
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [ int((self.width *self.scale)), 0, 0, 0, 0, int((self.width *self.scale)), 0, 0, 0, 0, 0, 0])

		elif self.alignment == 'Top_Reserved':
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [0, 0, int((self.height *self.scale)), 0, 0, 0, 0, 0, 0, 0, 0, 0])

		elif self.alignment == 'Bottom_Reserved' :
			self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [ 0, 0, 0, int((self.height *self.scale)), 0,0, 0, 0, 0, 0, 0, 0])

	def show_install_dialog (self):
		"""Craete/Show the install-dialog."""
		# create filter
		flt = gtk.FileFilter()
		flt.add_pattern('*.tar.bz2')
		flt.add_pattern('*.tar.gz')
		flt.add_pattern('*.tar')
		flt.add_pattern('*.zip')

		# create dialog
		dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dlg.set_current_folder(os.environ['HOME'])
		dlg.set_title(('Install a Screenlet'))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			
			# try installing and show result dialog
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			self.install (filename)	
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
		
		

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id[:7] == "Install":
			# TODO: use DBus-call for this
			self.show_install_dialog()
		if id[:4] == "add:":
			# make first letter uppercase (workaround for xml-menu)
			name = id[4].upper()+id[5:][:-9]
			 #and launch screenlet (or show error)
			if not screenlets.launch_screenlet(name):
				screenlets.show_error(self, 'Failed to add %sScreenlet.' % name)
		elif id[:5] == "exec:":
			# execute shell command
			os.system(id[5:] + " &")
		elif id[:6] == "align:":
			# execute shell command
			self.alignment = str(id[6:])
		elif id[:3] == "bg:":
			# execute shell command
			self.bg_style = str(id[3:])
		elif id[:8] == "shortcut":
			# execute shell command
			desktop = os.environ['HOME'] + '/Desktop/'
			shortcut = open( desktop + "Sidebar.Desktop" ,"w") #// open for for write
			towrite = '\n' + '[Desktop Entry]' + '\n' + 'Encoding=UTF-8' + '\n' + 'Version=1.0' + '\n' + 'Type=Application' + '\n' + 'Terminal=false' + '\n' + 'Icon=' + self.mypath + 'icon.svg' + '\n' + 'Exec=python ' + self.mypath + 'SidebarScreenlet.py' + '\n' + 'Name=Sidebar' + '\n'
			shortcut.write(towrite)
			shortcut.close()
			os.system('chmod +x ' + desktop + "Sidebar.Desktop")
		elif id[:4] == 'kill':
			for s in utils.list_running_screenlets():
				if s != 'SidebarScreenlet':
					if s.endswith('Screenlet'):
						s = s[:-9]
					try:
						self.quit_screenlet_by_name(s)
					except:
						pass
			for s in utils.list_running_screenlets():
				if s != 'SidebarScreenlet':
					if s.endswith('Screenlet'):
						s = s[:-9]
					try:
						self.quit_screenlet_by_name(s)
					except:
						pass
		if id[:14] == "startupremove:":
			# make first letter uppercase (workaround for xml-menu)
			name = id[14].upper()+id[15:][:-9]
			if not os.path.isdir(self.mypath + "startup"):
				os.mkdir(self.mypath + "startup")
			try:
				os.system('rm -rf ' + self.mypath + "startup/" + name)
			except:
				screenlets.show_message(self,'Error - please remove this file manually ' + self.mypath + "startup/" + name)
		if id[:11] == "startupadd:":
			name = id[11].upper()+id[12:][:-9]
			if not os.path.isdir(self.mypath + "startup"):
				os.mkdir(self.mypath + "startup")
			try:
				os.system('rm -rf ' + self.mypath + "startup/" + name)
			except:
				screenlets.show_message(self,'Error - unknown error')
			fileObj = open( self.mypath + "startup/" + name ,"w") #// open for for write
			fileObj.close()	


		#self.add_default_menuitems(DefaultMenuItem.XML)
		#self.add_default_menuitems(DefaultMenuItem.THEMES | DefaultMenuItem.PROPERTIES |
		#	DefaultMenuItem.DELETE)

	def on_init(self):
		self.started = True
		time.sleep(1)

		self.alignment = self.alignment
		self.add_default_menuitems(DefaultMenuItem.XML)
		#self.add_default_menuitems(DefaultMenuItem.THEMES | DefaultMenuItem.PROPERTIES |
		#	DefaultMenuItem.DELETE)
		self.update()



	def install (self, filename):
		"""Install a screenlet from a given archive-file. Extracts the
		contents of the archive to the user's screenlet dir."""
		print 'Installing %s' % filename
		result = False
		# TODO: set busy cursor
		# ...
		# get name of screenlet
		basename	= os.path.basename(filename)
		extension	= str(filename)[len(str(filename)) -3:]
#		name		= basename[:basename.find('.')]
		
		# check extension and create appropriate args for tar
		tar_opts = 'xfz'
		if extension == 'bz2':
			tar_opts = 'xfj'

		# extract archive to temporary dir
		if not os.path.isdir('/tmp/screenlets/'):
			os.system('mkdir ' + '/tmp/screenlets/')
		
		tmpdir = '/tmp/screenlets' + '/install-temp/'
		os.system('mkdir %s' % tmpdir)
		
		
		os.system('tar %s %s -C %s' % (tar_opts, filename, tmpdir))
		for d in tmpdir : #for each item in folders
  			if os.path.exists(d) and os.path.isdir(d): #is it a valid folder?
				for f in os.listdir(tmpdir): 
					
					name = f
		try:
			print name
		except:
			screenlets.show_message(self,"Archive damaged or unsuported, only tar , bz2 or gz.")
		# verify contents
	
		if not os.path.isdir('%s/%s' % (tmpdir, name)):
			# dir missing
			
			screenlets.show_message(self,"Invalid archive. Archive must contain a directory with the screenlet's name.")
		elif not os.path.isfile('%s/%s/%sScreenlet.py' % (tmpdir, name, name)):
			# Screenlet.py missing
			screenlets.show_message(self,"Invalid archive. Archive does not contain a screenlet.")
		else:
			
			utils.create_user_dir()
			os.system('tar %s %s -C %s' % (tar_opts, filename, os.environ['HOME'] + '/.screenlets'))
			# delete package info from target dir
			os.system('rm %s/%s/Screenlet.package' % (os.environ['HOME'] + '/.screenlets', name))
			# set msg/result
			screenlets.show_message(self,"The %sScreenlet has been succesfully installed." % name)
			result = True
		# remove temp contents
		os.system('rm -rf %s/install-temp' % '/tmp/screenlets/')
		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_default_menuitems()
		return result

	def on_drop (self, x, y, sel_data, timestamp):
		print "Data dropped ..."
		filename = utils.get_filename_on_drop(sel_data)[0]
		self.install (filename)

	def on_draw (self, ctx):

		# set scale
		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)

		if self.theme:
			if self.alignment == 'Left' or self.alignment == 'Left_Reserved':	
				ctx.rotate(math.pi)
				ctx.translate(-int(self.width)-(self.size-self.width),-int(gtk.gdk.screen_height()))
			elif self.alignment == 'Top' or self.alignment == 'Top_Reserved':	
				ctx.translate(0, self.size)				
				ctx.rotate(1.5*math.pi)
			elif self.alignment == 'Bottom' or self.alignment == 'Bottom_Reserved':	
				ctx.translate(gtk.gdk.screen_width(), 0)				
				ctx.rotate(0.5*math.pi)
										

			if self.bg_style == 'System':
				self.window.realize()
				self.window.show_all()
				self.ebox.set_uposition(999999,999999)
				bgcolor = self.ebox.get_style().bg[gtk.STATE_NORMAL]
				r = bgcolor.red/65535.0
				g = bgcolor.green/65535.0
				b = bgcolor.blue/65535.0
				ctx.set_source_rgba(r, g, b, 0.9)

				if self.alignment.startswith('Left') or self.alignment.startswith('Right'):	
					ctx.rectangle (0,0,self.size,gtk.gdk.screen_height())
					ctx.fill()
					self.draw_scaled_image(ctx,0,0,self.mypath + 'themes/Transparent/sidebar.png',self.size,gtk.gdk.screen_height())

				elif self.alignment.startswith('Top') or self.alignment.startswith('Bottom'):	
					ctx.rectangle (0,0,self.size,gtk.gdk.screen_width())			
					ctx.fill()
					self.draw_scaled_image(ctx,0,0,self.mypath + 'themes/Transparent/sidebar.png',self.size,gtk.gdk.screen_width())	

			elif self.bg_style == 'Custom':
				
				self.ebox.set_uposition(999999,999999)
				ctx.set_source_rgba(self.rgba_color[0], self.rgba_color[1], self.rgba_color[2], self.rgba_color[3])
				ctx.save()

				if self.alignment.startswith('Left') or self.alignment.startswith('Right'):	
					ctx.rectangle (0,0,self.size,gtk.gdk.screen_height())
					ctx.fill()
					self.draw_scaled_image(ctx,0,0,self.mypath + 'themes/Transparent/sidebar.png',self.size,gtk.gdk.screen_height())

				elif self.alignment.startswith('Top') or self.alignment.startswith('Bottom'):	
					ctx.rectangle (0,0,self.size,gtk.gdk.screen_width())		
					ctx.fill()	
					self.draw_scaled_image(ctx,0,0,self.mypath + 'themes/Transparent/sidebar.png',self.size,gtk.gdk.screen_width())	

			elif self.bg_style == 'Theme':
				self.ebox.set_uposition(999999,999999)
			
				if self.alignment.startswith('Left') or self.alignment.startswith('Right'):	
					self.draw_scaled_image(ctx,0,0,self.theme.path + '/sidebar.png',self.size,gtk.gdk.screen_height())
				elif self.alignment.startswith('Top') or self.alignment.startswith('Bottom'):	
					self.draw_scaled_image(ctx,0,0,self.theme.path + '/sidebar.png',self.size,gtk.gdk.screen_width())
						

				
	def on_draw_shape (self, ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			#self.theme['control-bg.svg'].render_cairo(ctx)
			ctx.set_source_rgba(1, 1, 1, 1)
			ctx.rectangle (0,0,self.width,self.height)
			ctx.fill()


# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(SidebarScreenlet)
    
    

