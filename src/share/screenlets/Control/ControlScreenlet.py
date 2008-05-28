#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#  ControlScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - a simple "control" for adding Screenlets and a possible replacement
#   for the system-menu
#
# TODO:
# - fix menu
# - drag&drop of .desktop-files (i.e. icons) should add them to the menu
# - re-ordering of the menu by drag&drop
# - editable menu-structure (would require nested ListOption)
# 

import screenlets
from screenlets import DefaultMenuItem,utils
from screenlets.options import BoolOption

import cairo
import os


class ControlScreenlet (screenlets.Screenlet):
	"""A simple control-button for adding Screenlets and launching other 
	applications. Offers a user-configurable menu on right-click."""
	
	# default meta-info for Screenlets
	__name__ 	= 'ControlScreenlet'
	__version__ = '0.5'
	__author__ 	= 'RYX (Rico Pfaus) 2007'
	__desc__ 	= __doc__
		
	# menuitems
	menuitem_add = None
	#menuitem_hideshow = None
	
	_hidden = False
	
	# editable settings
	add_screenlet_as_widget = False
	#hide_show_on_click = False
	
	# constructor
	def __init__ (self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, is_widget=False, 
			is_sticky=True, uses_theme=True, **keyword_args)
		# set theme and redraw
		self.theme_name = "default"
		# create menu

		# quit gtk when this window is closed
		self.quit_on_close = True
		# add editable settings
		self.add_options_group('Control', 
			'Additional settings for the ControlScreenlet.')
		# add editable settings to this Screenlet
		self.add_option(BoolOption('Control', 'add_screenlet_as_widget', 
			self.add_screenlet_as_widget, 'Add as "Widget"', 
			'If active, adds new Screenlets as "Widgets" (NOTE: When this ' + 
			'is active, you will not immediately see newly added Screenlets ' +
			'if you are not in "Widget"-mode (which depends on your ' +
			'Windowmanager and is only fully supported by compiz yet))'))
		"""self.add_option(BoolOption('Control', 'hide_show_on_click', 
			self.hide_show_on_click, 'Hide/Show on click', 
			'Hide/Show all open Screenlets (added by this Control) when '+
			'the Control is left-clicked.'))"""
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems(DefaultMenuItem.XML)
	def on_mouse_down (self, event):
		"""If hide_show_on_click is active, switch hide/show state."""
		#self.menu.popup(None, None, None, event.button, event.time)
		pass
		
	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id == "to_widget":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'is_widget',True)
		if id == "to_normal":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'is_widget',False)
		if id == "above":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'keep_above',True)
		if id == "normal":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'keep_above',False)
							set(f,'keep_below',False)
		if id == "below":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'keep_above',True)
		if id == "sticky":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'is_sticky',True)
		if id == "unsticky":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'is_sticky',False)
		if id == "lock":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'lock_position',True)
		if id == "unlock":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'lock_position',False)
		if id == "show_but":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'draw_buttons',True)
		if id == "hide_but":
			running = utils.list_running_screenlets()
			for name in running:
				name = name[:-9]
				if name != 'Control':
					service = screenlets.services.get_service_by_name(name)
					set = service.set
					if service != None and service:
						for f in service.list_instances():
							set(f,'draw_buttons',False)
		elif id[:4] == "add:":
			# make first letter uppercase (workaround for xml-menu)
			name = id[4].upper()+id[5:][:-9]
			 #and launch screenlet (or show error)
			if not screenlets.launch_screenlet(name):
				screenlets.show_error(self, 'Failed to add %sScreenlet.' % name)
		elif id[:5] == "exec:":
			# execute shell command
			os.system(id[5:] + " &")
	
	def on_draw (self, ctx):
		# set scale
		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)
		# render bg
		if self.theme:
			if self._hidden:
				#self.theme['control-bg-hidden.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'control-bg-hidden')
			else:
				#self.theme['control-bg.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'control-bg')
	
	def on_draw_shape (self, ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			#self.theme['control-bg.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'control-bg')

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(ControlScreenlet)

