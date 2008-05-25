#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# WindowlistScreenlet (c) 2007 RYX (aka Rico Pfaus) <ryx@ryxperience.com>
#
# INFO:
# - a windowlist/taskbar-replacement
# - TaskIconWidget-class for more flexible alignment of icons
# - customizable icon-shadows
# - flashing-function for icons
#
# TODO:
# - customizable direction (currently right/bottom)
# - option: only show windows on curr. workspace or viewport
# - option: organize by viewport or workspace
# - don't get focus when Windowlist's window is activated
# - support for window groups
# - ?startup-notification (blinking icon)
# - make splash-windows' icon flashing (untested but implemented)
# - drag/drop of icons in the list (should be easy with widgets)

import screenlets
from screenlets import DefaultMenuItem
from screenlets.options import  BoolOption
import cairo
import gtk
import wnck
import gobject


class WindowlistScreenlet (screenlets.Screenlet):
	"""A window list, showing icons of open windows. Could become a 
	replacement for common window lists and tasklists but is still very
	experimental and "hackish"."""
	
	# default meta-info for Screenlets
	__name__		= 'WindowlistScreenlet'
	__version__		= '0.1'
	__author__		= 'RYX (Rico Pfaus) 2007 modified by Whise'
	__desc__		= __doc__
	
	# list with open windows/tasks as tuples (WnckWindow, TaskIconWidget)
	__open_tasks	= []
	__tooltips		= None		# tooltips object
	__box 			= None		# content gtk.Box (HBox/Vbox)
	vertical = False
	left = False
	# TODO: make user-definable settings of these
	#direction = 1		# 1=right, 2=bottom (TODO)
	icon_size 		= 32
	icon_spacing	= 15
	#shadow_offset = 3
	#shadow_alpha = 0.3
	#bg_color = (1, 1, 1)
	#bg_alpha = 0.5
	activate_on_rightclick = False
	#show_background = False		# bugs with show_background
	
	# constructor
	def __init__ (self, text="", **keyword_args):
		#call super (and don't make this a "Widget")
		screenlets.Screenlet.__init__(self, width=40, height=40, 
			is_widget=False, is_sticky=True, **keyword_args)
		# add HBox for children (TODO: optional: vbox)

		# create tooltips
		self.__tooltips = gtk.Tooltips()
		# try to set wnck's client type to pager so that we correctly flag
		# that we are a tasklist - only available in libwnck-python >= 2.22
		try:
			wnck.set_client_type(wnck.CLIENT_TYPE_PAGER)
		except AttributeError:
			print "Error: Failed to set libwnck client type, window " \
				"activation may not work"
		
		self.add_options_group('Options', 'Options ...')
		self.add_option(BoolOption('Options','vertical', 
			self.vertical, 'Expand Verticaly (restart req) ', 
			'Expand window list verticaly'))
		self.add_option(BoolOption('Options','left', 
			self.left, 'Expand left (restart req)', 
			'Expand window list left'))
		# connect screen-signal handlers
		screen = wnck.screen_get_default()
		self.__active_win = screen.get_active_window()
		screen.connect("active_window_changed", self.active_window_changed)
		#screen.connect("viewports_changed", self.viewports_changed)
		screen.connect("window_opened", self.window_opened)
		screen.connect("window_closed", self.window_closed)
		#screen.connect("application_opened", self.test_event)
		# screen.connect("window_stacking_changed", 
		#	self.window_stacking_changed)
		# TEST: place in lower left (TODO: make this an option)
		#self.__dict__['x'] = 20
		#self.y = screen.get_height() - 50
		# disable width/height/scale (dynamic)
		#self.disable_option('width')
		#self.disable_option('height')
		self.disable_option('scale')

	# ---------------------------------------------------------------------
	# public methods
	# ---------------------------------------------------------------------
	
	# Check, if a window is allowed to be displayed
	# TODO: add a "blacklist"-property
	# TODO: don't use only window names for this check
	def on_init (self):
		print "Screenlet has been initialized."
		if self.vertical == False:
			self.__box = gtk.HBox()
		else:
			self.__box = gtk.VBox()
		self.__box.show()
		self.__box.spacing = self.icon_spacing	# doesn't work!
		self.window.add(self.__box)
		self.add_default_menuitems(
			DefaultMenuItem.WINDOW_MENU | 
			DefaultMenuItem.PROPERTIES | 
			DefaultMenuItem.DELETE | DefaultMenuItem.QUIT | DefaultMenuItem.QUIT_ALL)

	def check_window_name (self, name):
		if name[-10:] != "Screenlets" and name[-12:] != "Screenlet.py" \
			and name[-9:] != "Screenlet" and name != "Desktop":
			return True
		# add additional checks here
		return False
	
	# Creates a modified menu for the given wnck-window with the
	# Screenlet's default menuitems as "Screenlet..."-submenu.
	# NOTE: this feature should also go into the  "pydecorator"
	def create_right_click_menu (self, wnckwin):
		try:
			menu = wnck.create_window_action_menu(wnckwin)
		except:
			return None
		if menu:
			sep_item = gtk.SeparatorMenuItem()
			sep_item.show()
			menu.append(sep_item)
			sl_menuitem = gtk.MenuItem("Screenlet...")
			sl_menuitem.show()
			if sl_menuitem.get_submenu() == None:
				sl_menuitem.set_submenu(self.menu)
			menu.append(sl_menuitem)
			return menu
		return None
	
	# add a new task - adds TaskIconWidget
	def add_task (self, wnckwin):
		# create new taskiconwidget and add it as child
		# NOTE: adding spacing to icon size here is a workaround
		iw = TaskIconWidget(self.icon_size + self.icon_spacing, 
			self.icon_size + 4, wnckwin)
		self.__box.pack_start(iw, expand=False, fill=False)
		iw.show()
		iw.connect("icon_left_clicked", self.icon_left_clicked)
		iw.connect("icon_right_clicked",self.icon_right_clicked)
		# if window is a splash-screen, start flashing
		if wnckwin.get_window_type()==wnck.WINDOW_SPLASHSCREEN:
			print "SPLASH WINDOW"
			iw.start_flashing()
		# hook into window's events
		wnckwin.connect("state_changed", self.window_state_changed)
		wnckwin.connect("icon_changed", self.window_icon_changed)
		wnckwin.connect("name_changed", self.window_name_changed)
		# add window's name as tooltip
		self.__tooltips.set_tip(iw, wnckwin.get_name())
		# add wnckwin/taskicon to open apps list
		self.__open_tasks.append((wnckwin, iw ))
	
	# remove a task - removes TaskIconWidget
	def remove_task (self, wnckwin):
		tsk = None
		for t in self.__open_tasks:
			if t[0] == wnckwin:
				t[1].destroy()
				tsk = t
				break
		if tsk:
			self.__open_tasks.remove(t)
			return True
		return False
	
	# returns the TaskIconWidget for the given WnckWindow (or NOne)
	def get_taskicon_for_wnckwindow (self, wnckwin):
		for t in self.__open_tasks:
			if t[0] == wnckwin:
				return t[1]
		return None
	
	# deactivate all icons
	def disable_all_taskicons (self):
		for t in self.__open_tasks:
			if t[1].active:
				t[1].active = False
	
	# ---------------------------------------------------------------------
	# Event-handling methods
	# ---------------------------------------------------------------------
	
	# called when the active window has changed
	def active_window_changed (self, screen=None, data=None):
		if screen==None:
			screen = wnck.screen_get_default()
		active_win = screen.get_active_window()
		# disable all items
		self.disable_all_taskicons()
		# if window is set
		if active_win:
			# get taskiconwidget associated with this window
			taskicon = self.get_taskicon_for_wnckwindow(active_win)
			if taskicon:
				taskicon.active = True
	
	# taskicon has been left-clicked
	def icon_left_clicked (self, object, taskicon, time):
		# get wnckwin from icon
		win = taskicon.get_wnck_window()
		# get active wnckwin
		active_win = win.get_screen().get_active_window()
		# active window gets minimized and unset
		if  win and win == active_win:
			win.minimize()
			taskicon.active = False
		# minimized window gets unminimized/activated
		elif win and win.is_minimized():
			win.unminimize(time)
		# inactive window gets activated
		elif win != None:
			win.activate(time)
			taskicon.active = True
			taskicon.stop_flashing()
		else:
			pass
	
	# taskicon has been right-clicked
	def icon_right_clicked (self, object, taskicon, time):
		#taskicon.start_flashing()
		win = taskicon.get_wnck_window()
		if win:
			menu = self.create_right_click_menu(win)
			if menu:
				menu.popup(None, None, None, 3, time)
		else:
			self.menu.popup(None, None, None, 3, time)
	
	# caled when an application is opened (maybe useless)
	def application_opened (self, app):
		print "app_opened: "+str(app)
	
	# called when a new wnckwin is opened
	def window_opened (self, screen, wnckwin):
		#print "window_opened: "+str(window)
		if wnckwin and wnckwin.is_skip_tasklist()==False \
		and self.check_window_name(wnckwin.get_name()):
			# add new taskicon for the window
			self.add_task(wnckwin)
			# set size to correctly draw shape mask
			if self.vertical:
				self.height = len(self.__open_tasks) * (self.icon_size + 
					self.icon_spacing)
				self.width = 40
				if self.left :
					self.y = self.y - (self.icon_size + 
					self.icon_spacing)
			else:
				self.width = len(self.__open_tasks) * (self.icon_size + 
					self.icon_spacing)
				self.height = 40
				if self.left and self.has_started and self.window.window.is_visible():
					self.x = self.x - (self.icon_size + 
					self.icon_spacing)
			self.update_shape()
	
	# called when a wnckwin is closed
	def window_closed (self, screen, wnckwin):
		#print "window_closed: "+str(window)
		if self.remove_task(wnckwin):
			# set size to correctly draw shape mask
			if self.vertical:
				self.height = len(self.__open_tasks) * (self.icon_size + 
					self.icon_spacing)
				self.width = 40
				if self.left and self.has_started and self.window.window.is_visible():
					self.y = self.y + (self.icon_size + 
					self.icon_spacing)
			else:
				self.width = len(self.__open_tasks) * (self.icon_size + 
					self.icon_spacing)
				self.height = 40
				if self.left and self.has_started and self.window.window.is_visible():
					self.x = self.x + (self.icon_size + 
					self.icon_spacing)
			self.update_shape()
	def on_quit(self):
		if self.left:
			if not self.vertical : self.x = self.x + self.width
			else:self.y = self.y + self.height 
		print 'quiting'
	# a window's state changed
	def window_state_changed (self, wnckwin, changed, new_state):
		#print "state_changed: "+str(new_state)
		# if window demands attention, start flashing
		if new_state & wnck.WINDOW_STATE_DEMANDS_ATTENTION:
			taskicon = self.get_taskicon_for_wnckwindow(wnckwin)
			if taskicon:
				taskicon.start_flashing()
	
	# a window's icon changed
	def window_icon_changed (self, wnckwin):
		#print "icon_changed: "+str(wnckwin)
		taskicon = self.get_taskicon_for_wnckwindow(wnckwin)
		if taskicon:
			taskicon.update_icon()
			taskicon.queue_draw()
	
	# a window's name changed
	def window_name_changed (self, wnckwin):
		#print "name_changed: "+str(wnckwin)
		# update tooltip
		taskicon = self.get_taskicon_for_wnckwindow(wnckwin)
		if taskicon:
			self.__tooltips.set_tip(taskicon, wnckwin.get_name())
	
	# ---------------------------------------------------------------------
	# Drawing methods
	# ---------------------------------------------------------------------
	
	def on_draw_shape (self,ctx):
		#if self.theme:
		#	self.theme['windowlist-bg.svg'].render_cairo(ctx)
		# render bg shape according to window size
		size = self.window.size_request()
		ctx.rectangle(0, 0, size[0], size[1])
		ctx.set_source_rgba(1, 1, 1, 1)
		ctx.fill()


	def __setattr__ (self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'vertical' or name == 'left':
			self.redraw_canvas()
	
class TaskIconWidget (screenlets.ShapedWidget):
	"""The TaskIconWidget is a button, displaying an icon with alpha-shadow.
	  It is associated with a WnckWindow and displays the window's icon.
	  TODO: the TaskIconWidget shouldn't contain the wnckwindow-reference"""
	
	# privates
	__icon = None
	__shadow = None
	__wnck_window = None
	__flashtimeout = None
	
	# attributes/properties
	icon_size =32		# size of icon to be drawn (not widget size)
	shadow_offset = 3
	shadow_alpha = 0.4
	active = False
	hover_color = (1, 1, 1)		# hover/flashing color
	hover_alpha = 0.5			# hover/flashing alpha
	
	# for custom signals
	__gsignals__ = dict(
		icon_left_clicked=(gobject.SIGNAL_RUN_FIRST,
			gobject.TYPE_NONE, (gobject.TYPE_OBJECT,
			gobject.TYPE_INT)),
		icon_right_clicked=(gobject.SIGNAL_RUN_FIRST,
			gobject.TYPE_NONE, (gobject.TYPE_OBJECT,
			gobject.TYPE_INT)))
	
	# constructor
	def __init__ (self, width, height, wnckwin):
		# call super
		super(TaskIconWidget, self).__init__(width, height)
		# get icon and initially update it
		self.__wnck_window  = wnckwin
		self.update_icon()
		# set size of widget
		self.set_size_request(width, height)
	
	# attribute-"setter"
	def __setattr__ (self, name, value):
		# reraw when "active"-state changes
		if name=="active":
			self.queue_draw()
		# set the value in object (ESSENTIAL)
		try:
			object.__setattr__(self, name, value)
		except TypeError:
			self.__dict__[name] = value
		
	# return the private WnckWindow for this TaskIcon
	def get_wnck_window (self):
		return self.__wnck_window
	
	# start flashing
	def start_flashing (self):
		if self.__flashtimeout==None:
			self.__flashtimeout = gobject.timeout_add(
				100, self.flashing_callback)
	
	# stop flashing
	def stop_flashing (self):
		if self.__flashtimeout:
			gobject.source_remove(self.__flashtimeout)
			self.__flashtimeout = None
	
	# update icon and synchronize with the one in wnckwin
	def update_icon (self):
		self.__icon = self.__wnck_window .get_icon()
		self.__shadow = self.__icon.copy()
		if self.__icon and self.__shadow:
			self.__icon.saturate_and_pixelate(self.__shadow, 0.0, False)
	
	# handle button-press on this taskiconwidget
	def button_press (self, widget, e):
		if e.button==1:
			# emit "state_changed"-signal
			self.active = not self.active
			self.emit("icon_left_clicked", self, e.time)
			return True
		else:
			self.emit("icon_right_clicked", self, e.time)
			return True
	
	# timeout-callback for flashing
	def flashing_callback (self):
		# redraw
		if self.hover_alpha > 0.1:
			self.hover_alpha -= 0.1
		else:
			self.hover_alpha = 0.5
		self.queue_draw()
		return True
	
	# draw highlight/flashing effect over a hovered item
	def draw_highlight (self, ctx):
		ctx.save()
		ctx.rectangle(0, 0, 
			self.icon_size + self.shadow_offset, 
			self.icon_size + self.shadow_offset)
		ctx.set_operator(cairo.OPERATOR_ATOP)
		c = self.hover_color
		ctx.set_source_rgba(c[0], c[1], c[2], 
			self.hover_alpha)
		ctx.fill()
		ctx.restore()
	
	# drawing-handler: draw icon
	def draw (self, ctx):
		ctx.set_operator(cairo.OPERATOR_OVER)
		# update icon
		self.update_icon()
		# draw shadow
		#print self.window
		#if self.window!=None:
		self.window.draw_pixbuf(None, self.__icon, 0, 0, 
			self.shadow_offset, self.shadow_offset)
		ctx.save()
		ctx.translate(self.shadow_offset, self.shadow_offset)
		ctx.set_operator(cairo.OPERATOR_IN)
		ctx.rectangle(0, 0, self.icon_size, self.icon_size)
		ctx.clip_preserve()
		ctx.set_source_rgba(0, 0, 0, self.shadow_alpha)
		ctx.fill()
		ctx.restore()
		# active?
		if self.active:
			self.window.draw_pixbuf(
				None, self.__icon, 0, 0, 0, 0 )
		else:
			self.window.draw_pixbuf(
				None, self.__shadow, 0, 0, 0, 0)
			# lighten when hovered (or flashing)
			if self.mouse_inside or self.__flashtimeout:
				self.draw_highlight(ctx)
			# add viewport number
			"""ctx.select_font_face ("Sans", 
				cairo.FONT_SLANT_NORMAL,
				cairo.FONT_WEIGHT_BOLD)
			ctx.set_font_size (7)
			ctx.set_source_rgba(1,1,1, 0.9)
			ctx.move_to (30, 33)
			ctx.show_text ("88")"""
		#size = self.window.window.size_request()



# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(WindowlistScreenlet)

