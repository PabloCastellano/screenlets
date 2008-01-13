#!/usr/bin/env python

# PagerScreenlet (c) 2007 RYX (aka Rico Pfaus) <ryx@ryxperience.com>
#
# INFO:
# - an experiment for creating a pager-replacement
#
# TODO:
# - options
# - only redraw the region that has changed instead of the whole area
# - remove flickering and reduce number of redraws
# - blacklist-option for excluding certain windows

import screenlets
from screenlets import DefaultMenuItem

import cairo
import gtk
import wnck


class PagerScreenlet (screenlets.Screenlet):
	"""A very basic PagerScreenlet (UNFINISHED AND BUGGY YET)."""
	
	# default meta-info for Screenlets
	__name__	= 'PagerScreenlet'
	__version__	= '0.2'
	__author__	= 'RYX (aka Rico Pfaus)'
	__desc__	= __doc__
	
	# internals
	__windows		= []		
	__handlers		= []	# needed for unregistering screen-handlers
	__screen		= None
	__relx			= 1
	__rely			= 1
	__border_size	= 10
	__viewports_h	= 3
	__viewports_v	= 3
		
	# settings
	
	# constructor
	def __init__ (self, **keyword_args):
		# call super (and don't make this a "Widget")
		screenlets.Screenlet.__init__(self, is_widget=False, is_sticky=True,
			uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"

		# get screen and active window
		self.__screen = wnck.screen_get_default()
		self.__active_win = self.__screen.get_active_window()
		# get number of horiz/vert viewports and set width/height
		self.calculate_size()
		# connect wnckscreen-signal-handlers
		self.__handlers.append(self.__screen.connect("viewports_changed", 
			self.viewports_changed))
		self.__handlers.append(self.__screen.connect("active_window_changed", 
			self.active_window_changed))
		self.__handlers.append(self.__screen.connect("window_opened", 
			self.window_opened))
		self.__handlers.append(self.__screen.connect("window_closed", 
			self.window_closed))
		# TODO: add options/groups

	# ---------------------------------------------------------------------
	# public methods
	# ---------------------------------------------------------------------
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()
	def calculate_size (self):
		"""Calculate/set size relative to screen coordinates and viewports"""
		# get number of viewports
		"""
		ws = wnck.screen_get_default().get_active_workspace()
		print "WS: "+str(ws)
		if ws:
			self.__viewports_h = ws.get_width() / self.__screen.get_width()
			self.__viewports_v = ws.get_height() / self.__screen.get_height()
			"""	
		# get relation (like 8,6 for 800x600px)
		self.__relx = self.__screen.get_width() / 100
		self.__rely = self.__screen.get_height() / 100
		# set width/height
		self.width = (self.__screen.get_width() / 10 + \
			(self.__border_size * 2)) #* self.__viewports_h
		self.height = (self.__screen.get_height() / 10 + \
			(self.__border_size * 2)) #* self.__viewports_v
	
	# Check, if a window is allowed to be displayed
	# TODO: add a "blacklist"-property
	# TODO: don't use only window names for this check
	def check_window_name (self, name):
		if name[-10:] != "Screenlets" and name[-12:] != "Screenlet.py" \
			and name[-9:] != "Screenlet" and name != "Desktop":
			return True
		# add additional checks here
		return False
	
	def add_window (self, wnckwin):
		"""Add a wnckwin to the list and connect to its events."""
		hlst = []
		hlst.append(wnckwin.connect("state_changed", 
			self.window_state_changed))
		hlst.append(wnckwin.connect("icon_changed", 
			self.window_icon_changed))
		hlst.append(wnckwin.connect("name_changed", 
			self.window_name_changed))
		hlst.append(wnckwin.connect("geometry_changed", 
			self.window_geometry_changed))
		# create window info and add it to list
		wdata = {'window':wnckwin, 'handlers':hlst}
		self.__windows.append(wdata)
		
	# Creates a modified menu for the given wnck-window with the
	# Screenlet's default menuitems as "Screenlet..."-submenu.
	# NOTE: this feature should also go into the  "pydecorator"
	def create_right_click_menu(self, wnckwin):
		menu = wnck.create_window_action_menu(wnckwin)
		sep_item = gtk.SeparatorMenuItem()
		sep_item.show()
		menu.append(sep_item)
		sl_menuitem = gtk.MenuItem("Screenlet...")
		sl_menuitem.show()
		if sl_menuitem.get_submenu() == None:
			sl_menuitem.set_submenu(self.menu)
		menu.append(sl_menuitem)
		return menu
	
	def remove_window (self, wnckwin, clear_handlers=True):
		"""Remove a wnckwindow from the list and disconnect all handlers."""
		n = -1
		for i in xrange(len(self.__windows)):
			w = self.__windows[i]
			if w['window'] == wnckwin:
				n=i
				break
		if n>-1:
			if clear_handlers:
				for h in w['handlers']:
					try:
						w['window'].disconnect(h)
					except:
						pass
			del self.__windows[n]
			return True
		return False
	
	# ---------------------------------------------------------------------
	# Event-handling methods for libwnck-events
	# ---------------------------------------------------------------------
	
	# called when the active window has changed
	def active_window_changed (self, screen=None, data=None):
		if screen==None:
			screen = wnck.screen_get_default()
		active_win = screen.get_active_window()
		# ...
		self.redraw_canvas()
	
	# caled when an application is opened (maybe useless)
	def application_opened (self, app):
		print "app_opened: "+str(app)
	
	# called when a new wnckwin is opened
	def window_opened (self, screen, wnckwin):
		#print "window_opened: "+str(window)
		if wnckwin:
			# hook into window's events (and store handler ids)
			hlst = []
			hlst.append(wnckwin.connect("state_changed", 
				self.window_state_changed))
			hlst.append(wnckwin.connect("icon_changed", 
				self.window_icon_changed))
			hlst.append(wnckwin.connect("name_changed", 
				self.window_name_changed))
			hlst.append(wnckwin.connect("geometry_changed", 
				self.window_geometry_changed))
			# create window info and add it to list
			wdata = {'window':wnckwin, 'handlers':hlst}
			self.__windows.append(wdata)
		# TODO: if window shall be displayed, update the pager
		self.redraw_canvas()
	
	# called when a wnckwin is closed
	def window_closed (self, screen, wnckwin):
		print "window_closed: "+str(wnckwin)
		# remove window from list
		self.remove_window(wnckwin, False)
		#self.__windows.remove(wnckwin)
		# TODO: if window shall be displayed, update the pager
		self.redraw_canvas()
	
	# a window's state changed
	def window_state_changed (self, wnckwin, changed, new_state):
		print "state_changed: "+str(new_state)
		# TODO: if window shall be displayed, update the pager
		#self.redraw_canvas()
	
	# a window's icon changed
	def window_icon_changed (self, wnckwin):
		print "icon_changed"
	
	# a window's name changed
	def window_name_changed (self, wnckwin):
		print "name_changed"

	# a window's geometry changed
	def window_geometry_changed (self, wnckwin):
		#print "geometry_changed: "+str(wnckwin)
		# TODO: if window shall be displayed, update the pager
		self.redraw_canvas ()

	# the screen's viewport changed
	def viewports_changed (self, wnckwin):
		print "viewports_changed"
		self.redraw_canvas()
		
	# ---------------------------------------------------------------------
	# Screenlet-handlers (Drawing methods, ...)
	# ---------------------------------------------------------------------
	
	def on_draw (self, ctx):
		# scaling-support
		ctx.scale(self.scale, self.scale)
		if self.theme:
			ctx.save()
			ctx.scale(self.width/100.0, self.height/100.0)
			self.theme['pager-bg.svg'].render_cairo(ctx)
			ctx.restore()
		else:
			# draw bg (TODO: use theme)
			ctx.set_source_rgba(1.0, 1.0, 1.0, 0.6)
			ctx.paint()
		# get list of open windows from curr. wnckscreen
		if self.__screen:
			ctx.save()
			# translate border size
			ctx.translate(self.__border_size, self.__border_size)
			# set clipping to workspace area (exclude border)
			hbs = (self.__border_size * 2)
			ctx.rectangle(0, 0, 
				self.width - hbs, self.height - hbs)
			ctx.clip()
			# get viewport position (add to window drawing)
			vp_x = 0
			vp_y = 0
			ws = self.__screen.get_active_workspace()
			if ws:
				vp_x = ws.get_viewport_x() / 10 / self.__viewports_h
				vp_y = ws.get_viewport_y() / 10 / self.__viewports_v
			# get rect of curr. viewport and draw rect
			vp_w = self.__screen.get_width() / 10 / self.__viewports_h
			vp_h = self.__screen.get_height() / 10 / self.__viewports_v
			ctx.rectangle(vp_x, vp_y, vp_w, vp_h)
			ctx.set_source_rgba(1, 1, 1, 0.4)
			ctx.fill()
			# get all windows and draw them
			# TODO: draw only windows in visible space (check position)
			wins = self.__screen.get_windows_stacked()
			for win in wins:
				if win.get_name() != "Desktop" and \
					win.is_minimized() == False and \
					win.is_skip_pager() == False:
					geom = win.get_geometry()
					if geom:
						x = (geom[0] / 10) / self.__viewports_h
						y = (geom[1] / 10) / self.__viewports_v
						w = (geom[2] / 10) / self.__viewports_h
						h = (geom[3] / 10) / self.__viewports_v
						ctx.rectangle(x+vp_x, y+vp_y, w, h)
						ctx.set_source_rgba(0.5, 0.5, 0.5, 0.9)
						#ctx.fill()
						ctx.fill_preserve()
						ctx.set_source_rgba(0, 0, 0, 1)
						ctx.stroke()
			ctx.restore()
		if self.theme:
			ctx.scale(self.width/100.0, self.height/100.0)
			self.theme['pager-glass.svg'].render_cairo(ctx)
	
	def on_draw_shape (self,ctx):
		self.on_draw(ctx)

	def on_quit (self):
		# disconnect all handlers from open windows
		#print "PagerScreenlet.on_quit: "
		for w in self.__windows:
			self.remove_window(w)
		# disconnect handlers from wnckscreen
		for h in self.__handlers:
			try:
				self.__screen.disconnect(h)
			except:
				print "failed to remove signal-handler (not critical)"
				pass
		#return True
	
	def on_realize (self):
		if self.__screen:
			self.calculate_size()
	

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(PagerScreenlet)

