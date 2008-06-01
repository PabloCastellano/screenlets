#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  SlideshowScreenlet (c) Whise <helder.fraga@hotmail.com>


import screenlets
from screenlets.options import FileOption, IntOption, FloatOption, StringOption, BoolOption
from screenlets import DefaultMenuItem , utils
import cairo
import gtk
import pango
import gobject
import os
import commands
import random
from screenlets import Plugins
Flickr = Plugins.importAPI('Flickr')


class SlideshowScreenlet (screenlets.Screenlet):
	"""A Screenlet that displays a slideshow from your folder or from the Flickr.com website.You can add new images by drag drop them into the screenlet's window area.You need a package called Python imaging"""
	
	# --------------------------------------------------------------------------
	# meta-info, options
	# --------------------------------------------------------------------------
	
	__name__		= 'SlideshowScreenlet'
	__version__		= '1.1'
	__author__		= 'Helder Fraga aka Whise'
	__desc__		= __doc__
	
	# attributes
	__image = None
	__timeout = None
	# editable options
	update_interval = 60
	image_filename 	= ''
	image_scale		= 0.865
	image_offset_x	= 13
	image_offset_y	= 13
	url = ''
	slide = True
	home = commands.getoutput("echo $HOME")
	folders = home
	use_types = ['.jpg', '.gif', '.png','.bmp', '.svg', '.jpeg', '.tif', '.tiff']
	engine = ''
	engine1 = 'directory'
	engine_sel = ['directory', 'Flickr']
	frame = 'normal'
	frame_sel = ['normal', 'wide']
	paint_menu = False
	showbuttons = True
	img_name = ''
	factor = 1
	preserve_aspect = 0
	recursive = False
	flickrurl = 'http://www.flickr.com/explore/interesting/7days/'
	# --------------------------------------------------------------------------
	# constructor and internals
	# --------------------------------------------------------------------------
	
	def __init__ (self, **keyword_args):
		# call super (and enable drag/drop)
		screenlets.Screenlet.__init__(self, width=200, height=200,
			uses_theme=True, drag_drop=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# initially apply default image (for newly created instances)
		#self.image_filename = screenlets.PATH + '/Picframe/dali.png'
		# add default menuitems (all the standard ones)
		self.add_default_menuitems(DefaultMenuItem.XML)

		
		# add option group to properties-dialog
		self.add_options_group('SlideShow', 'Slideshow-related settings ...')
		# add editable options
		#self.add_option(FileOption('Slideshow', 'image_filename', 
		#	self.image_filename, 'Filename',

		self.add_option(IntOption('SlideShow', 'update_interval', 
			self.update_interval, 'Update interval', 
			'The interval for updating info (in seconds ,3660 = 1 day, 25620 = 1 week)', min=1, max=25620))
		self.add_option(StringOption('SlideShow', 'engine', self.engine,'Select Engine', '',choices = self.engine_sel),realtime=False)
		self.add_option(StringOption('SlideShow', 'flickrurl', self.flickrurl,'Flickr Url', 'flickr url'))
		self.add_option(StringOption('SlideShow', 'folders', self.folders,'Select Folders', 'The folder where pictures are',))
		self.add_option(BoolOption('SlideShow', 'recursive',bool(self.recursive), 'Recursive folders','Show images on sub folders'))
		self.add_option(BoolOption('SlideShow', 'showbuttons',bool(self.showbuttons), 'Show Buttons on focus','Show Buttons on focus'))
		self.add_option(StringOption('SlideShow', 'frame', self.frame,'Select frame type', 'Select frame type',choices = self.frame_sel),)
		#	'Filename of image to be shown in this Slideshow ...')) 
		self.add_option(FloatOption('SlideShow', 'image_scale', self.image_scale, 
			'Image Scale', 'Scale of image within this Picframe ...', 
			min=0.01, max=10.0, digits=2, increment=0.01,hidden=True))
		self.add_option(IntOption('SlideShow', 'image_offset_x', 
			self.image_offset_x, 'Image Offset X', 'X-offset of upper left '+\
			'corner of the image within this Picframe ...', 
			min=0, max=self.width,hidden=True))
		self.add_option(IntOption('SlideShow', 'image_offset_y', 
			self.image_offset_y, 'Image Offset Y', 'Y-offset of upper left '+\
			'corner of the image within this Picframe ...', 
			min=0, max=self.height,hidden=True))
		self.add_option(BoolOption('SlideShow', 'preserve_aspect', bool(self.preserve_aspect),'Preserve aspect ratio', 'Preserve the aspect ratio when resizing images ,thanks to Mike Peters'))
		self.update_interval = self.update_interval
		self.engine = self.engine
		self.folders = self.folders

	def __setattr__ (self, name, value):

		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'showbuttons':
			self.redraw_canvas()
		if name == 'engine':
			if value == 'directory' :
				self.engine1 = 'directory'
				self.update()
			if value == '' :
				self.engine1 = 'directory'
				self.update()
			if value == 'Flickr':
				self.engine1 = value
				self.update()
		if name == 'folders' and self.engine == 'directory':
				self.engine1 = 'directory'
				self.update()
		if name == 'frame':
			if value == 'wide':

				self.factor = 0.8
			else:
				self.factor = 1


		if name == "image_filename":
			screenlets.Screenlet.__setattr__(self, name, value)
			# update view
			self.redraw_canvas()
			#self.update_shape()



		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(int(value * 1000), self.update)
			else:
				self.__dict__['update_interval'] = 1
				pass
	def on_init(self):
		self.height = int(200 * self.factor)
		self.update()
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()


	def set_image(self, filename):
		
		self.image_filename = filename

	

	def fetch_image(self):
		
	 #if self.slide == True:	
	 if self.engine1 == 'Flickr':
		imgs = []
		a = Flickr.Flickr()
		try:
			imgs = a.get_image_list(self.flickrurl)
		except:return ''
		choice = random.choice(imgs) 
		self.url = a.url_list[str(choice)]
		self.img_name =  self.home + "/slide.jpg"
		random.choice(imgs) 
		saveto = self.home + "/slide.jpg"
		a.save_image(choice,saveto)

		self.img_name =  self.home + "/slide.jpg"	
		forecast = self.img_name
	 elif self.engine1 == 'directory':
		imgs = []
		
		if self.recursive:
			for root, dirs, files in os.walk(self.folders): 
				for file in files:
					try:
						if os.path.splitext(file)[1].lower() in self.use_types:
							imgs.append(os.path.join(root,file))
				   	except: pass
		else:
			if os.path.exists(self.folders) and os.path.isdir(self.folders): 
				for f in os.listdir(self.folders):                
					
			      		try:  #splitext[1] may fail
						if os.path.splitext(f)[1].lower() in self.use_types: 
				                 	imgs.append(self.folders + os.sep + f)         #if so, add it to our list
							#print f
				   	except: pass

		try:
			forecast = random.choice(imgs)  #get a random entry from our list
			self.img_name = forecast
			
		except:
			              		pass

	 try:return forecast	
	 except:
			              		pass

	# --------------------------------------------------------------------------
	# Screenlet handlers
	# --------------------------------------------------------------------------
	def update(self):
		#screenlets.show_error(self, 
		#		'Failed to load image "%s": %s (only PNG images supported yet)' )# % (filename, ex))
		if self.slide == True:	
			self.set_image (self.fetch_image())
			self.redraw_canvas()
		return True

	def on_drag_enter (self, drag_context, x, y, timestamp):
		self.redraw_canvas()
	
	def on_drag_leave (self, drag_context, timestamp):
		self.redraw_canvas()
	
	def on_drop (self, x, y, sel_data, timestamp):
		print "Data dropped ..."
		filename = ''
		filename = utils.get_filename_on_drop(sel_data)[0]
		print filename
		if filename != '':
			#self.set_image(filename)
			self.image_filename = filename.replace(chr(34),'')

	def show_install_dialog (self):
		"""Craete/Show the install-dialog."""
		# create filter
		flt = gtk.FileFilter()
		flt.add_pattern('*.')

		# create dialog
		dlg = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,buttons=(gtk.STOCK_CANCEL, 
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dlg.set_current_folder(os.environ['home'])
		dlg.set_title(('Select a folder'))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			
			# try installing and show result dialog
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			self.folders = filename 

			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	

	def on_draw (self, ctx):
		ctx.set_operator(cairo.OPERATOR_OVER)
		ctx.scale(self.scale, self.factor*self.scale)

		if self.theme:
			# if something is dragged over, lighten up the whole thing
			if self.dragging_over:
				ctx.set_operator(cairo.OPERATOR_XOR)
			# render bg
			#self.theme['Slideshow-bg.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'frame')
			if self.preserve_aspect == 1:
        			w, h = self.get_image_size(self.image_filename)
	      			h_offset = 0
			        w_offset = 0
			        if w >= h:
					ratio = float(200) / w
					h = int(h * ratio)
					w = 200
					h_offset = int((200-h)/2)
				else:
					ratio = float(200) / h
					w = int(w * ratio)
					h = 200
					w_offset = int((200-w)/2)
			else:
				w, h = (200, 200)
			# render image if set
			
			ctx.save()
			ctx.translate(self.image_offset_x, self.image_offset_y)
			ctx.scale(0.875,self.image_scale)
			try:
				self.draw_scaled_image(ctx,0,0,self.image_filename,w,h)
			except:pass
			ctx.restore()
			ctx.translate(60,158)
			if self.paint_menu == True and  self.showbuttons == True: self.theme.render(ctx, 'menu')				

	
	def on_focus(self, event):
	
		self.paint_menu = True
		self.redraw_canvas()
		
	def on_unfocus(self, event):
		self.paint_menu = False
		self.redraw_canvas()


	def on_mouse_down(self,event):
			x, y = self.window.get_pointer()
			x /= (self.scale)
			y /= (self.scale*self.factor)
			if y >= 158 and y <=180:
				if x >= 60 and x <= 86 :
					self.slide = False
					self.update()
				elif x >= 87 and x <= 109 :
					self.slide = True
					self.update()
				elif x >= 110 and x <= 136 :
					self.set_image (self.fetch_image())
					self.redraw_canvas()
	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id == "next":
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			
			self.set_image (self.fetch_image())
			self.redraw_canvas()

		if id == "visit":
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			if self.engine1 == 'Flickr':
				os.system('firefox ' + self.url + " &")
			elif self.engine1 == 'directory':
				os.system('gnome-open ' + chr(34) + self.img_name + chr(34) + " &")

		if id == "wall":
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			if self.engine1 == 'directory':
				os.system("gconftool-2 -t string -s /desktop/gnome/background/picture_filename " + chr(34) + self.img_name + chr(34))
				os.system("gconftool-2 -t bool -s /desktop/gnome/background/draw_background False")
				os.system("gconftool-2 -t bool -s /desktop/gnome/background/draw_background True")
			elif self.engine1 == 'Flickr':
				screenlets.show_message(self,'Can only set wallpaper to local images')

		if id == "start":
			self.slide = True
			self.update()
		if id == "stop":
			self.slide = False

		if id[:7] == "Install":
			# TODO: use DBus-call for this
			self.show_install_dialog()
			self.update()

	def on_draw_shape (self, ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			#self.theme['control-bg.svg'].render_cairo(ctx)
			ctx.set_source_rgba(1, 1, 1, 1)
			ctx.rectangle (0,0,self.width,self.height)
			ctx.fill()

	
# If the program is run directly or passed as an argument to the python
# interpreter then launch as new application
if __name__ == "__main__":
	# create session object here, the rest is done automagically
	import screenlets.session
	screenlets.session.create_session(SlideshowScreenlet)

