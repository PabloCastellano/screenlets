#!/usr/bin/env python
#-*- coding: utf-8 -*-


# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# MainMenuScreenlet Copyright (c) 2007 Helder Fraga






import screenlets
from screenlets import DefaultMenuItem
from screenlets import sensors
from screenlets.options import StringOption, IntOption, BoolOption, ColorOption ,FontOption
import cairo
import gtk
import pango
import gobject
import commands
import sys
import os
import pygtk
from gtk import gdk

import menus
import string
import pathfinder
import keyboard

class MainMenuScreenlet (screenlets.Screenlet):
	"""A main menu screenlet"""
	
	# default meta-info for Screenlets
	__name__		= 'MainMenuScreenlet'
	__version__		= '0.1'
	__author__		= 'Helder Fraga aka Whise'
	__desc__		= __doc__

	width =410
	height = 800
	bgcolor = 0
	red = 0
	green = 0
	blue = 0
	has_focus = True
	is_hover = False
	icon = None
	transx = 0
	transy = 0
	orientation = 'top_left'
	icon_size = 32
	use_theme = False
	home = os.environ['HOME']
	theme1 = None
	distro = ''
	user = ''
	host = ''
	font_title = 'FreeSans'
	curve = 10
	transp = 90
	draw_shadow = True
	draw_border = True
	frame_color=(0,0,0,0.7)
	border_color=(0,0,0,0.5)
	shadow_color=(0,0,0,0.5)
	use_gtk = True
	draw_border = True
	draw_shadow = True
	
	gnome_panel = False

	
	def __init__ (self, **keyword_args):   

		screenlets.Screenlet.__init__(self, width=400, height=self.height,uses_theme=True, 
			is_widget=False, is_sticky=True,is_sizable = False,ask_on_option_override = False, **keyword_args)
	
		self.theme_name = "gnome"
	        screen_hieght = gtk.gdk.screen_height()
	        if screen_hieght >= 901:
			self.screen_hieght = int(screen_hieght * 0.4)
		if screen_hieght <= 900:
			self.screen_hieght = int(screen_hieght * 0.5)
		if screen_hieght <= 700:
			self.screen_hieght = int(screen_hieght * 0.55)
		#theme = gtk.IconTheme()
		self.height = self.screen_hieght +80
		self.distro = sensors.sys_get_distrib_name()
		self.user = sensors.sys_get_username()
		self.host = sensors.sys_get_hostname()
		print self.height
		print self.width
	        location =  __file__
		print __file__
	        self.location = location.replace('MainMenuScreenlet.py','')
	        self.location_icon = self.location + 'icon.svg'    
		self.add_options_group('Main Menu Options', 'Main menu options')
		self.add_option(StringOption('Main Menu Options','orientation',			# attribute-name
			self.orientation,						# default-value
			'Position of the button relativly to the menu', 						# widget-label
			'Position of the button relativly to the menu',choices = ['top_left','top_center','top_right','middle_right','middle_center','middle_left','bottom_right','bottom_center','bottom_left']	))

		self.add_option(IntOption('Main Menu Options','icon_size', 
			self.icon_size, 'Main menu icon size', 
			'icon_size', 	min=0, max=128))

		self.add_option(FontOption('Main Menu Options','font_title', 
			self.font_title, 'Title Font', 
			''))

		self.add_option(BoolOption('Main Menu Options','use_theme', 
			self.use_theme, 'Use costume icon theme', 'Use costume icon theme'))

		self.add_option(BoolOption('Main Menu Options','use_gtk', 
			self.use_gtk, 'Use gtk theme color for frame', 'Use gtk theme color in the frame'))

		self.add_option(IntOption('Main Menu Options','transp', 
			self.transp, 'Gtk theme transparency', 
			'', min=0, max=100))

		self.add_option(ColorOption('Main Menu Options','frame_color', 
			self.frame_color, 'Frame color', 
			'Frame color, only when gtk theme is off'))

		self.add_option(BoolOption('Main Menu Options','draw_border', 
			self.draw_border, 'Draw border arround menu', 'draw_shadow'))

		self.add_option(ColorOption('Main Menu Options','border_color', 
			self.border_color, 'Border color', 
			'Frame color'))

		self.add_option(BoolOption('Main Menu Options','draw_shadow', 
			self.draw_shadow, 'Draw shadow arround menu', 'draw_shadow'))

		self.add_option(ColorOption('Main Menu Options','shadow_color', 
			self.shadow_color, 'Shadow color', 
			'Frame color'))


		self.add_option(IntOption('Main Menu Options','curve', 
			self.curve, 'Rounded corners angule', 
			'curve', min=0, max=45))

		self.add_options_group('Gnome panel integration', 'Gnome panel integration')

		self.add_option(BoolOption('Gnome panel integration','gnome_panel', 
			self.gnome_panel, 'Integrate with gnome-panel', 'Always show menu'))

	        self.theme1 = gtk.icon_theme_get_default()
		try:self.icon = self.theme1.load_icon ("gnome-main-menu", self.icon_size, 0)
		except: 
			try: self.icon = gdk.pixbuf_new_from_file (self.location + 'themes/' +self.theme_name + '/icon.svg')
			except: self.icon = gdk.pixbuf_new_from_file (self.location + 'themes/' +self.theme_name + '/icon.png')

	        render = gtk.CellRendererPixbuf()
	        cell1 = gtk.CellRendererText()
	        cell2 = gtk.CellRendererText()
	        cell2.set_property('xalign', 1.0)
	        column1 = gtk.TreeViewColumn("==1==", render)
	        column1.add_attribute(render, 'pixbuf', 0)
	        column2 = gtk.TreeViewColumn("==2==", cell1,text=1)
	        tree1 = gtk.TreeView()
	        tree1.set_size_request(160, -1)
	        tree1.set_headers_visible (0)
	        tree1.append_column(column1)
	        tree1.append_column(column2)
	        lst1,self.objlist1 = menus.get_menus(menus.data.MENUROOT,
                                             root2=menus.data.SYSTEMMENUROOT)
	        model = menus.set_model(tree1,lst1,self.theme1,self.location_icon)
	        tree1.connect('cursor_changed', self.treeclick,
	                      tree1,self.objlist1,False)
	        tree1.set_model(model)
        
	        render = gtk.CellRendererPixbuf()
	        cell1 = gtk.CellRendererText()
	        cell2 = gtk.CellRendererText()
	        cell2.set_property('xalign', 1.0)
	        column1 = gtk.TreeViewColumn("==1==", render)
	        column1.add_attribute(render, 'pixbuf', 0)
	        column2 = gtk.TreeViewColumn("==2==", cell1,text=1)
        	tree2 = gtk.TreeView()
        	tree2.set_size_request(150, -1)
        	tree2.set_headers_visible (0)
        	tree2.append_column(column1)
        	tree2.append_column(column2)
        	lst2,self.objlist2 = menus.get_menus(menus.data.MENUROOT)
        	model,self.objlist3 = menus.get_places(self.theme1)
        	tree2.set_model(model)
        	tree2.connect("button-press-event", keyboard.tree2faux,
                      self.treeclick,tree2,self.objlist2)
        #

        	#entry.set_size_request(-1,20)
        	search_button = gtk.Button("")
		search_button.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND, 
			gtk.ICON_SIZE_BUTTON))
		hbox3 = gtk.HBox()
        	entry = gtk.Entry()
		
        	self.hbox = gtk.HBox()
        	hbox2 = gtk.HBox()
        	vbox = gtk.VBox()
        	swindow = gtk.ScrolledWindow()
        	swindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        	swindow.set_size_request(-1, self.screen_hieght)
        	hbox2.pack_start(entry, padding=0)
        	hbox2.pack_end(search_button,expand=False, fill=False, padding=0)
        	swindow2 = gtk.ScrolledWindow()
        	swindow2.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        	swindow2.set_size_request(-1, self.screen_hieght)
        	swindow2.add(tree1)
        	vbox.pack_start(swindow2,expand=True, fill=True)
        	vbox.pack_end(hbox2,expand=False, fill=True, padding=0)
        	quit_button = gtk.Button("")
		quit_button.set_image(gtk.image_new_from_stock(gtk.STOCK_QUIT, 
			gtk.ICON_SIZE_BUTTON))
        	edit_button = gtk.Button("")
		edit_button.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, 
			gtk.ICON_SIZE_BUTTON))
        	help_button = gtk.Button("")
		help_button.set_image(gtk.image_new_from_stock(gtk.STOCK_HELP, 
			gtk.ICON_SIZE_BUTTON))
        	control_button = gtk.Button("")
		control_button.set_image(gtk.image_new_from_stock(gtk.STOCK_PREFERENCES, 
			gtk.ICON_SIZE_BUTTON))
        	swindow.add(tree2)
        	vbox3 = gtk.VBox()
        	hbox3 = gtk.HBox()
        	hbox3.pack_end(quit_button,expand=False, fill=False, padding=0)
        	hbox3.pack_end(edit_button,expand=False, fill=False, padding=0)
        	hbox3.pack_end(help_button,expand=False, fill=False, padding=0)
        	hbox3.pack_end(control_button,expand=False, fill=False, padding=0)
		vbox3.pack_start(swindow,expand=True, fill=True)
		vbox3.pack_start(hbox3,expand=False, fill=False)

        	self.hbox.pack_start(vbox)
        	self.hbox.add(vbox3)

		self.vbox2 = gtk.VBox()
        	self.vbox2.pack_start(self.hbox,expand=False, fill=False, padding=0)
        	self.vbox2.show_all()
        	self.window.add(self.vbox2)
		self.hbox.set_size_request(1,self.height - 100)
		self.bgcolor = self.vbox2.get_style().bg[gtk.STATE_NORMAL]
		self.tips = gtk.Tooltips()
		self.tips.set_tip(control_button, ('Launch gnome control center...'))
		self.tips.set_tip(quit_button, ('Quit , shutdown or restart dialog ...'))
		self.tips.set_tip(help_button, ('Get help ...'))
		self.tips.set_tip(edit_button, ('Edit this menu ...'))
	        entry.connect("activate",self.search)
        	search_button.connect("clicked",self.search)
        	quit_button.connect("clicked",self.but,'quit')
        	help_button.connect("clicked",self.but,'help')
        	edit_button.connect("clicked",self.but,'edit')
        	control_button.connect("clicked",self.but,'control')
        	tree1.connect("key-press-event",keyboard.navigate,tree2,1)
        	tree2.connect("key-press-event",keyboard.navigate,tree1,2)
        	tree2.connect("row-activated",keyboard.tree2activated,
        	              self.treeclick,tree2,self.objlist2)
        	tree2.set_hover_selection(True)
        	self.entry = entry
        	self.tree1 = tree1
        	self.tree2 = tree2

        	self.tree1.set_cursor((self.objlist1.__len__()-1,0),None,False)
		self.hbox.set_border_width(7)
        	self.hbox.set_uposition(0,80)
        	if "placesmodel" in self.__dict__:pass
        	else:self.placesmodel,self.objlist3 = menus.get_places(self.theme1)
        	self.tree2.set_model(self.placesmodel)
     #   self.tree1.grab_focus()
    #    self.window.show_all()


	def but(self,widget,id):
        	if id == 'quit':
			os.system('gnome-session-save --kill --gui &')
        	if id == 'edit':
			os.system('alacarte &')
        	if id == 'control':
			os.system('gnome-control-center &')
        	if id == 'help':
			os.system('yelp &')

	def search(self,widget):
        	test = pathfinder.exists(self.entry.get_text())
        	if test[0] == True and test[1] != None:
        		os.system(test[1]+' &')
  		else:gobject.spawn_async(["tracker-search-tool", self.entry.get_text()], 
                                 flags=gobject.SPAWN_SEARCH_PATH)   


	def on_after_set_atribute(self,name, value):
		"""Called after setting screenlet atributes"""
		if name == 'orientation' or name == 'use_theme' or name == 'icon_size' or name == 'curve':
			self.redraw_canvas()
			self.update_shape()


	def on_mouse_enter (self, event):
		"""Called when the mouse enters the Screenlet's window."""
	

		
	def on_mouse_leave (self, event):
		"""Called when the mouse leaves the Screenlet's window."""

		self.is_hover = False


	def on_mouse_down (self, event):
		"""Called when a buttonpress-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
	        self.tree1.set_cursor((self.objlist1.__len__()-1,0),None,False)
	        #self.window.show_all()
	        #self.title.hide(self)
	        if "placesmodel" in self.__dict__:pass
	        else:self.placesmodel,self.objlist3 = menus.get_places(self.theme1)
	        self.tree2.set_model(self.placesmodel)

		self.is_hover = True
		return False

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_menuitem("Menuapplet", "How to gnome panel")
		self.add_default_menuitems(DefaultMenuItem.WINDOW_MENU | DefaultMenuItem.THEMES | DefaultMenuItem.PROPERTIES |
			DefaultMenuItem.DELETE | DefaultMenuItem.QUIT | DefaultMenuItem.QUIT_ALL)
		self.is_visible = True

	def menuitem_callback(self, widget, id):
		screenlets.Screenlet.menuitem_callback(self, widget, id)
		if id=="Menuapplet":
			screenlets.show_message(self,'1 - Create a launcher in the gnome main menu\n2 - Link the launcher to the gnomeApplet.py in the like this: python -u ' + self.get_screenlet_dir() + '/gnomeApplet.py\n3 - Select the integrate with gnome-panel in the screenlet options')

	def treeclick(self,widget,tree,obj,toggle,t2act=False):
		"""
	        this method is activated when tree1 is clicked. 
	        It fills tree2 with a model from the selected tree1 row
	        """
	        selection = tree.get_selection()
	        selection.set_mode('single')
	        if t2act == True:
		        selection.select_path(1)
			selection.select_path(0)
       		model, iter = selection.get_selected()
       		try:name = model.get_value(iter,1)
	        except:name=None        
	        if name != None:
	            try:
	                if toggle == True:obj = self.objlist2
	                if obj[name][0] == 1:
	                    command = obj[name][1]
	                    if '%' in command:command = command[:command.index('%')]
	                    os.system(command+' &')
	
	                if obj[name][0] == 2:
	                    lst,self.objlist2 = menus.get_menus(obj[name][1])
	                    model = menus.set_model(self.tree1,lst,self.theme1,
	                                            self.location_icon)
	                    self.tree2.set_cursor_on_cell((0,0), focus_column=None,
	                                                  focus_cell=None, 
	                                                  start_editing=False)
	                    self.tree2.set_model(model)
	                    self.tree2.set_cursor_on_cell((0,0), focus_column=None,
	                                                  focus_cell=None, 
	                                                  start_editing=False)
	            except KeyError:
	                if self.objlist3[name][0] == 0:
	                    gobject.spawn_async(["nautilus", self.objlist3[name][1]], 
	                                        flags=gobject.SPAWN_SEARCH_PATH)
	  
	            try:
	                if obj[name][0] == 4:
	                    if "placesmodel" in self.__dict__:pass
	                    else:self.placesmodel,self.objlist3 = \
	                                                    menus.get_places(self.theme1)
	                    self.tree2.set_model(self.placesmodel)
	            except:pass

	def get_icon_file_from_gtk (self, name):
		"""Get the specified icon's filename from the current gtk-theme or
		/usr/share/icons or /usr/share/pixmaps."""
		# try to get icon from theme
		if self.window:
			theme = gtk.icon_theme_get_for_screen(self.window.get_screen())
			print theme
			if iconinfo:
				fn = iconinfo.get_filename()
				iconinfo.free()
				return fn
			else:
				# try to load icon from default locations
				print "NAME: '%s'" % ('/usr/share/pixmaps/' + name)
				return '/usr/share/pixmaps/' + name
		return None

	def on_focus (self, event):
		"""Called when the Screenlet's window receives focus."""
		#if self.gnome_panel:self.is_visible = True
		self.has_focus = True
		self.redraw_canvas()
		self.update_shape()

	def on_unfocus (self, event):
		"""Called when the Screenlet's window loses focus."""
		if self.gnome_panel and self.has_started and self.window:
			self.is_visible = False
		self.has_focus = False
		if not self.gnome_panel:
			self.redraw_canvas()
			self.update_shape()

	def on_draw (self, ctx):
		
		ctx.scale(self.scale, self.scale)
		if self.has_focus is False and not self.gnome_panel:
			try:self.vbox2.hide()
			except : pass


			if self.theme:
				#try:ico = self.get_icon_file_from_gtk("gnome-main-menu")
				#except: ico = self.location_icon
				if not self.use_theme:	
					
						try:self.icon = self.theme1.load_icon ("gnome-main-menu", self.icon_size, 0)
						except: 
							try: self.icon = gdk.pixbuf_new_from_file (self.location + 'themes/' +self.theme_name + '/icon.svg')
							except: self.icon = gdk.pixbuf_new_from_file (self.location + 'themes/' +self.theme_name + '/icon.png')
							print ' no icon'
						if self.orientation.startswith('top'):
							self.transy = 0
						elif self.orientation.startswith('middle'):
							self.transy = (self.height /2) - self.icon.get_height()
						elif self.orientation.startswith('bottom'):
							self.transy = self.height - self.icon.get_height()

	
						if self.orientation.endswith('right'):
							self.transx = self.width - self.icon.get_width()
						elif self.orientation.endswith('center'):
							self.transx = (self.width/2) - self.icon.get_width()
						elif self.orientation.endswith('left'):
							self.transx = 0

						ctx.save()
						ctx.translate(self.transx,self.transy)
						ctx.set_source_pixbuf(self.icon, 0, 0)
						ctx.paint()
						ctx.restore()
				else:

						try: self.icon = gdk.pixbuf_new_from_file (self.location + 'themes/' +self.theme_name + '/icon.svg')
						except: self.icon = gdk.pixbuf_new_from_file (self.location + 'themes/' +self.theme_name + '/icon.png')
						ctx.save()
						new_width = (self.scale *self.icon_size)/self.icon.get_width()
						new_height = (self.scale *self.icon_size)/self.icon.get_height()
						ctx.scale(new_width,new_height )
						
						if self.orientation.startswith('top'):
							self.transy = 0
						elif self.orientation.startswith('middle'):
							self.transy = (self.height /2) - (new_height * self.icon.get_height())
						elif self.orientation.startswith('bottom'):
							self.transy = self.height - (new_height * self.icon.get_height())
	
	
						if self.orientation.endswith('right'):
							self.transx = self.width - (new_width *self.icon.get_width())
						elif self.orientation.endswith('center'):
							self.transx = (self.width/2) - (new_width *self.icon.get_width())
						elif self.orientation.endswith('left'):
							self.transx = 0
						ctx.restore()
						ctx.save()
						ctx.scale(1,1 )					
						ctx.translate(self.transx,self.transy)
						ctx.scale(new_width,new_height )
						ctx.set_source_pixbuf(self.icon, 0, 0)
						ctx.paint()
						ctx.restore()

		elif self.has_focus or self.gnome_panel:
			if self.theme:		
				ctx.save()
				if self.window.is_composited == False : a = 1
				else : a = 0.4	
				ctx.set_source_rgba(0.5, 0.5, 0.5, a)	
				self.theme.draw_rounded_rectangle(ctx,0,0,self.curve +5,self.width*self.scale,self.height*self.scale)	#self.box = None
				co = float(self.transp) /100
				if not self.window.is_composited and co<=69: co = 70
				try:
					self.bgcolor = self.vbox2.get_style().bg[gtk.STATE_NORMAL]
			        	r = self.bgcolor.red/65535.0
					g = self.bgcolor.green/65535.0
					b = self.bgcolor.blue/65535.0
					ctx.set_source_rgba(r, g, b, co)
					font_color = (1 - r, 1 - g,1-  b, 0.9)
					
			
				except: 		ctx.set_source_rgba(0, 0, 0, co)
				if self.draw_shadow:
					shadow = 6
				else:
					shadow = 0
				if self.draw_border:
					border = 2
				else:
					border = 0
				adjust =  (6 - shadow)
				if not self.use_gtk:
					font_color = (1 - self.frame_color[0], 1 - self.frame_color[1],1-  self.frame_color[2], 0.9)
					ctx.set_source_rgba(*self.frame_color)
				self.draw_rectangle_advanced (ctx, 0+adjust, 0+adjust, self.width-12, self.height-12, rounded_angles=(self.curve,self.curve,self.curve,self.curve), fill=True,border_size=border, border_color=(self.border_color[0],self.border_color[1],self.border_color[2],self.border_color[3]), shadow_size=shadow, shadow_color=(self.shadow_color[0],self.shadow_color[1],self.shadow_color[2],self.shadow_color[3]))	
				ctx.restore()
				#try:self.user_icon = gdk.pixbuf_new_from_file (self.home + 'themes/' +self.theme_name + '/icon.png')	
				if (self.theme1 != None):

					self.user_icon = self.theme1.load_icon ("computer", 64, 0)
					ctx.translate(15,15)
					ctx.save()

					ctx.set_source_pixbuf(self.user_icon, 0, 0)
					ctx.paint()
					ctx.set_source_rgba(*font_color)
					self.theme.draw_text(ctx, self.distro, 70, 10, self.font_title.split(' ')[0] , 15,self.width - 74 ,pango.ALIGN_LEFT)
					self.theme.draw_text(ctx, self.user +'@' + self.host, 70, 30, self.font_title.split(' ')[0] , 10,self.width - 74 ,pango.ALIGN_LEFT)
					ctx.restore()
				
				try:self.vbox2.show()
				except : pass

	def on_draw_shape (self, ctx):
		if self.theme:
			if self.has_focus is False and not self.gnome_panel:
				ctx.translate(self.transx,self.transy)
				self.theme.draw_rounded_rectangle(ctx,5,5,self.curve,self.icon_size,self.icon_size)
			elif self.has_focus or self.gnome_panel:
														

				self.theme.draw_rounded_rectangle(ctx,5,5,self.curve,self.width,self.height)
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(MainMenuScreenlet)
