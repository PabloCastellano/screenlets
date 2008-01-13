#!/usr/bin/env python

#  LauncherScreenlet (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - a Screenlet that launches an application when double-clicked
# 
# TODO:
# - add dragover_color-option (and maybe rollover_color)
# - add (optional) confirmation-dialog when updating via drag&drop
# - fully configure by drag&drop (image/filename)
# - scale window to icon-size (100/icon_size) when new icon is set
# - if Label set there should be an optional label-text
# - use startup-notify
# - ...

import screenlets
from screenlets import DefaultMenuItem
from screenlets.options import StringOption, ImageOption

import cairo
import rsvg
import gtk
import os


class LauncherScreenlet (screenlets.Screenlet):
	"""A Screenlet that executes any kind of application or shell-command when 
	clicked (e.g. it also offers the ability to "dbus-send"). You can think of
	it as a desktop-icon in form of a window/screenlet. You can simply 
	drag&amp;drop an icon from your mainmenu or panel on the Launcher's window 
	to initialize a new Launcher for the given app."""
	
	# default meta-info for Screenlets
	__name__	= 'LauncherScreenlet'
	__version__ = '0.7'
	__author__	= 'RYX (aka Rico Pfaus)'
	__desc__	= __doc__
	
	# internals
	__icon_svg			= None
	__icon_pixbuf		= None
	__mouse_inside		= False
	__left_mouse_down	= False
	__icon_width		= 32
	__icon_height		= 32
	
	# editable options
	#action = "dbus-send --type=method_call --dest=org.freedesktop.compiz " + \
	#		"/org/freedesktop/compiz/rotate/allscreens/rotate_right " + \
	#		"org.freedesktop.compiz.activate string:'root' int32:0"
	#action	= 'xterm -fg green -bg black -cr black -fn 8x12'
	action	= ''
	icon	= ''
	label	= ''
	
	# constructor/internals
	
	def __init__ (self, **keyword_args):
		# call super (and enable drag/drop)
		screenlets.Screenlet.__init__(self, drag_drop=True, **keyword_args)
		# add default menu items

		# set default icon and action
		self.icon = self.get_screenlet_dir() + '/default-icon.svg'
		# add editable settings
		self.add_options_group('Starter', 
			'Some options related to the Launcher-Screenlet.')
		self.add_option(StringOption('Starter', 'label', self.label, 
			'Tooltip/Label', 'A string that will be displayed as tooltip ...'))
		self.add_option(StringOption('Starter', 'action', 
			self.action, 'Command', 
			'Shell-command to be executed when icon is clicked ...'))
		self.add_option(ImageOption('Starter', 'icon', self.icon, 
			'Icon-Filename', 'The image to display on this Launcher ...'))
		
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems(DefaultMenuItem.SIZE |
			DefaultMenuItem.WINDOW_MENU | DefaultMenuItem.PROPERTIES |
			DefaultMenuItem.DELETE)
		
	def __setattr__ (self, name, value):
		screenlets.Screenlet.__setattr__(self, name, value)
		if name=="icon" and value != None and value != '':
			try:
				if value[-4:].lower() == '.svg':
					# is it an svg? then load it as such
					self.__icon_svg = rsvg.Handle(value)
					if self.__icon_svg:
						icon_size = self.__icon_svg.get_dimension_data()
						self.__icon_width	= icon_size[0]
						self.__icon_height	= icon_size[1]
						if self.__icon_pixbuf != None:
							self.__icon_pixbuf = None
				else:
					# else we use the gdk.pixbuf for loading the file
					self.__icon_pixbuf = gtk.gdk.pixbuf_new_from_file(value)
					if self.__icon_pixbuf:
						self.__icon_width	= self.__icon_pixbuf.get_width()
						self.__icon_height	= self.__icon_pixbuf.get_height()
						if self.__icon_svg != None:
							self.__icon_svg = None
				# update window to match new icon dimensions
				self.width = int(self.__icon_width * self.scale)
				self.height = int(self.__icon_height * self.scale)
			except Exception, ex:
				screenlets.show_message(self, 'Error - ' + 
					'failed to load icon "' + str(self.icon) + '"')
				print "Exception in Launcher '%s'" % ex
				# set default icon or exit with fatal error
				di = self.get_screenlet_dir() + '/default-icon.svg'
				if value != di:
					self.icon = di
				else:
					import sys
					print "Unable to load default icon '%s'! Fatal error." % di
					sys.exit(15)
			# and reshape/update
			if self.window:
				self.update_shape()
				self.redraw_canvas()
		elif name == "label":
			tt = gtk.Tooltips()
			tt.set_tip(self.window, value)

	# custom functions for launcher
	
	def configure_from_desktop_file (self, filename):
		"""Configure this launcher from a .desktop-file. The Exec-action
		becomes the command and the Icon is used as icon (if available, else
		the current icon is unchanged).
		TODO: check/use startup-notify"""
		print "Parsing .desktop-file: %s" % filename
		ret = False
		if filename.startswith('file://'):
			filename = filename[7:]
		try:
			f = open(filename, 'r')
			for l in f.readlines():
				# get line from file and split/convert it
				data = l[:-1].replace('/n', '//n').split('=', 1)
				# if there are two elements
				if len(data) > 1:
					data[0].strip()
					data[1].lstrip()
					print data[0] + '=' + data[1]
					var = data[0]
					val = data[1] 
					if var=='Exec':
						self.action = val
					elif var=='Icon':
						if val[0]=='/':
							self.icon = val
						else:
							icn = self.get_icon_file_from_gtk(val)
							if icn:
								self.icon = icn
					elif var=='Name':
						self.label = val
					ret = True
			f.close()
		except Exception,ex:
			print "Failed to parse desktop-file: %s" % ex
		return ret
	
	def get_icon_file_from_gtk (self, name):
		"""Get the specified icon's filename from the current gtk-theme or
		/usr/share/icons or /usr/share/pixmaps."""
		# try to get icon from theme
		if self.window:
			theme = gtk.icon_theme_get_for_screen(self.window.get_screen())
			print theme
			#if theme.has_icon(name):
			iconinfo = theme.lookup_icon(name, 48, 0)
			if iconinfo:
				fn = iconinfo.get_filename()
				iconinfo.free()
				return fn
			else:
				# try to load icon from default locations
				print "NAME: '%s'" % ('/usr/share/pixmaps/' + name)
				return '/usr/share/pixmaps/' + name
		return None
	
	def launch_action (self):
		"""Execute the action/command for this LauncherScreenlet."""
		if self.action:
			os.system(self.action + "&")
		else:
			screenlets.show_message(self, "You have first to define a " +
				"command to be launched for this LauncherScreenlet (see " + 
				"Options/Starter/Command in this Screenlet's right-click " +
				"menu).")
	
	# Screenlet event-handlers
	
	def on_drag_enter (self, drag_context, x, y, timestamp):
		"""Something has been dragged into of the Screenlet's area."""
		self.redraw_canvas()
	
	def on_drag_leave (self, drag_context, timestamp):
		"""Something has been dragged out of the Screenlet's area."""
		self.redraw_canvas()
	
	def on_drop (self, x, y, sel_data, timestamp):
		"""Something has been dropped ontp the Screenlet."""
		print "Data dropped ..."
		filename = ''
		# we prefer URIs
		uris = sel_data.get_uris()
		if uris:
			print "URIs: " + str(uris)
			if uris[0].endswith('.desktop'):
				self.configure_from_desktop_file(uris[0])
		else:
			# yes, we also take texts :)
			txt = sel_data.get_text()
			if txt:
				print "TXT: " + str(txt)
				# trim EOLs at end and strip EOLs within text
				#if txt[-1] == '\n': txt = txt[:-1]
				txt = txt.replace('\n', '')
				# if it is a file-location,
				if txt.startswith('file://'):
					filename = txt[7:]
					# check type of file
					if filename.endswith('.desktop'):
						# desktop-file? take special care on this one
						self.configure_from_desktop_file(filename)
					elif filename[-4:] in ('png', 'svg', 'jpg', 'gif', 'xpm') \
						or filename.endswith('.jpeg'):
						# image?
						print "TODO: set new icon: %s" % filename
					else:
						# unkown type - assume it is intended to be set as the
						# new application to get launched by this Launcher
						print "TODO: set new command: %s" % filename
						# TODO: check for directory and launch it in special app
				else:
					screenlets.show_error(self, 'Invalid string: %s.' % txt)
			else:
				# nothing of interest within the dragged data
				pass
	
	def on_mouse_enter (self, event):
		"""Mouse entered the Screenlet."""
		self.__mouse_inside = True
		self.redraw_canvas()
	
	def on_mouse_leave (self, event):
		"""Mouse left the Screenlet."""
		self.__mouse_inside = False
		self.__left_mouse_down = False
		self.redraw_canvas()
	
	def on_mouse_down (self, event):
		"""Mouse pressed on the Screenlet."""
		if event.button == 1:
			self.__left_mouse_down = True
			self.redraw_canvas()
			self.launch_action()
			return True
	
	def on_mouse_up (self, event):
		"""Mouse released on the Screenlet."""
		if event.button == 1:
			self.__left_mouse_down = False
			self.redraw_canvas()
			
	def on_draw (self, ctx):
		"""Draw the Screenlet's graphics."""
		#ctx.scale(self.width/self.__icon_width, self.height/self.__icon_height)
		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)
		# if we have a pixbuf-icon, render it as such
		if self.__icon_pixbuf:
			ctx.set_source_pixbuf(self.__icon_pixbuf, 0, 0)
			ctx.paint()
		# else we use SVG to render it scalable
		elif self.__icon_svg:
			self.__icon_svg.render_cairo(ctx)
		# set shade color (not very elegant, I know :D ...)
		shade = None
		if self.dragging_over:
			ctx.set_source_rgba(1, 1, 0, 0.3)		# TEMP!!! make option
			shade = True
		elif self.__mouse_inside:
			if self.__left_mouse_down:
				ctx.set_source_rgba(0, 0, 0, 0.3)
			else:
				ctx.set_source_rgba(1, 1, 1, 0.3)
			shade = True
		if shade:
			ctx.set_operator(cairo.OPERATOR_ATOP)
			ctx.rectangle(0, 0, self.width, self.height)
			ctx.fill()
		
	def on_draw_shape (self, ctx):
		"""Draw the Screenlet's input shape."""
		if self.__icon_pixbuf or self.__icon_svg:
			self.on_draw(ctx)

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(LauncherScreenlet)

