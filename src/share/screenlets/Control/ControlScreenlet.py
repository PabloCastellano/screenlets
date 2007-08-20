#!/usr/bin/env python

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
from screenlets import DefaultMenuItem
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
		self.add_default_menuitems(DefaultMenuItem.XML)
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

	def on_mouse_down (self, event):
		"""If hide_show_on_click is active, switch hide/show state."""
		#if self.hide_show_on_click and event.button==1:
		#	#self.switch_hide_show()
		#	return True	
		pass
	
	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id == "hide_show":
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			pass
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

