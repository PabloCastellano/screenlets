#!/usr/bin/env python

# Screenlets Manager - (c) RYX (Rico Pfaus) 2007
#
# + INFO:
# This is a graphical manager application that simplifies managing and
# starting screenlets. It also allows simple install and uninstall of
# per-user Screenlets.
#
# + TODO:
# - support for using sessions (via commandline), (NOTE: if a session is selected
#   all autostart-files need to be removed and created new)
# - if daemon can't be found, try again in periodic intervals
# - Help-button
# - menu
#    - function to reset all screenlets and clear the default session
#    - function to easily package a screenlet from within the gui (?)
#    - different View-modes (icons/details)
#

import os
import gtk, gobject
import screenlets
from screenlets import utils
import dbus

# stub for gettext - we not translate yet, but we will :D
def _(s):
	return s


# name/version of this app
APP_NAME	= _('Screenlets Manager')
APP_VERSION	= '0.1'

# some constants
DIR_USER		= os.environ['HOME'] + '/.screenlets'
DIR_AUTOSTART	= os.environ['HOME'] + '/.config/autostart'
DIR_TMP			= '/tmp/screenlets/'
DEBUG_MODE		= True


# classes

class ScreenletInfo:
	"""A container with info about a screenlet."""
	
	def __init__ (self, name, lname, info, author, version, icon):
		self.name		= name
		self.lname		= lname
		self.info		= info.replace("\n", '').replace('\t', ' ')
		self.author		= author
		self.version	= version
		self.icon		= icon
		self.active		= False
		self.system		= not os.path.isfile('%s/%s/%sScreenlet.py' % (DIR_USER, name, name))
		self.autostart	= os.path.isfile(DIR_AUTOSTART + '/' + name + 'Screenlet.desktop')


class ScreenletInstaller:
	"""A simple utility to install screenlets into the user's screenlets-
	directory in $HOME/.screenlets/."""
	
	def __init__ (self):
		self._message = ''
	
	def get_result_message (self):
		"""Return a human-readble result message about the last operation."""
		return self._message
	
	def create_user_dir (self):
		"""Create the userdir for the screenlets."""
		if not os.path.isdir(DIR_USER):
			os.mkdir(DIR_USER)
	
	def install (self, filename):
		"""Install a screenlet from a given archive-file. Extracts the
		contents of the archive to the user's screenlet dir."""
		print 'Installing %s' % filename
		result = False
		# get name of screenlet
		basename	= os.path.basename(filename)
		extension	= os.path.splitext(filename)
		name		= basename[:basename.find('.')]
		print name
		# check extension and create appropriate args for tar
		tar_opts = 'xfz'
		if extension == 'bz2':
			tar_opts = 'xfj'
		# extract archive to temporary dir
		if not os.path.isdir(DIR_TMP):
			os.system('mkdir ' + DIR_TMP)
		tmpdir = DIR_TMP + '/install-temp'
		os.system('mkdir %s' % tmpdir)
		os.system('tar %s %s -C %s' % (tar_opts, filename, tmpdir))
		# verify contents
		if not os.path.isdir('%s/%s' % (tmpdir, name)):
			# dir missing
			self._message = _("Invalid archive. Archive must contain a directory with the screenlet's name.")
		elif not os.path.isfile('%s/%s/%sScreenlet.py' % (tmpdir, name, name)):
			# Screenlet.py missing
			self._message = _("Invalid archive. Archive does not contain a screenlet.")
		else:
			# check for package-info
			if not os.path.isfile('%s/%s/Screenlet.package' % (tmpdir, name)):
				self._message = _("Invalid archive. Archive does not contain a package info, screenlet seems to be outdated.")
			else:
				# copy archive to user dir (and create if not exists)
				self.create_user_dir()
				os.system('tar %s %s -C %s' % (tar_opts, filename, DIR_USER))
				# delete package info from target dir
				os.system('rm %s/%s/Screenlet.package' % (DIR_USER, name))
				# set msg/result
				self._message = _("The %sScreenlet has been succesfully installed." % name)
				result = True
		# remove temp contents
		os.system('rm -rf %s/install-temp' % DIR_TMP)
		# ready
		return result
	

class ScreenletsManager:
	"""The main application class."""
	
	def __init__ (self):
		# inti props
		self.tips = gtk.Tooltips()
		# create ui and populate it
		self.create_ui()
		# populate UI
		self.load_screenlets()
		# connect dameon
		self.connect_daemon()		
	
	# screenlets stuff
	
	def connect_daemon (self):
		"""Connect to org.screenlets.ScreenletsDaemon and connect to
		the register/unregister signals."""
		self.daemon_iface = None
		bus = dbus.SessionBus()
		if bus:
			try:
				bus_name	= 'org.screenlets.ScreenletsDaemon'
				path		= '/org/screenlets/ScreenletsDaemon'
				iface		= 'org.screenlets.ScreenletsDaemon'
				proxy_obj = bus.get_object(bus_name, path)
				if proxy_obj:
					self.daemon_iface = dbus.Interface(proxy_obj, iface)
			except Exception, ex:
				print "Error in ScreenletsManager.connect_daemon: %s" % ex
		# if daemon is not available, 
		if not self.daemon_iface:
			# if daemon is unavailable, try to launch it 
			print "Trying to launching screenlets-daemon ..."
			os.system(screenlets.INSTALL_PREFIX + \
				'/share/screenlets-manager/screenlets-daemon.py &')
			os.system('sleep 2')
		# running now?
		if self.daemon_iface:
			print "DAEMON FOUND!"
			# connect to signals
			self.daemon_iface.connect_to_signal('screenlet_registered', 
				self.handle_screenlet_registered)
			self.daemon_iface.connect_to_signal('screenlet_unregistered', 
				self.handle_screenlet_unregistered)
			# ok
			return True
		else:
			#print "Error: Unable to connect/launch daemon."
			screenlets.show_error(None, _("Unable to connect or launch daemon. Some values may be displayed incorrectly."), _('Error'))
		return False
	
	def create_autostarter (self, name):
		"""Create a .desktop-file for the screenlet with the given name in 
		$HOME/.config/autostart."""
		if name.endswith('Screenlet'):
			name = name[:-9]
		starter = '%s/%sScreenlet.desktop' % (DIR_AUTOSTART, name)
		if not os.path.isfile(starter):
			path = utils.find_first_screenlet_path(name)
			if path:
				print "Create autostarter for: %s/%sScreenlet.py" % (path, name)
				code = ['[Desktop Entry]']
				code.append('Name=%sScreenlet' % name)
				code.append('Encoding=UTF-8')
				code.append('Version=1.0')
				code.append('Exec=%s/%sScreenlet.py > /dev/null' % (path, name))
				code.append('X-GNOME-Autostart-enabled=true')
				#print code
				f = open(starter, 'w')
				if f:
					for l in code:
						f.write(l + '\n')
					f.close()
					return True
				print 'Failed to create autostarter for %s.' % name
				return False
		else:
			print "Starter already exists."
	
	def delete_autostarter (self, name):
		"""Delete the autostart for the given screenlet."""
		if name.endswith('Screenlet'):
			name = name[:-9]
		print 'Delete autostarter for %s.' % name
		os.system('rm %s/%sScreenlet.desktop' % (DIR_AUTOSTART, name))
	
	def delete_selected_screenlet (self):
		"""Delete the selected screenlet from the user's screenlet dir."""
		sel = self.view.get_selected_items()
		if sel and len(sel) > 0 and len(sel[0]) > 0:
			it = self.model.get_iter(sel[0][0])
			if it:
				info = self.model.get_value(it, 2)
				if info and not info.system:
					# delete the file
					if screenlets.show_question(None, _('Do you really want to permanently uninstall/delete the %sScreenlet from your system?' % info.name), _('Delete Screenlet')):
						# delete screenlet's directory from userdir
						os.system('rm -rf %s/%s' % (DIR_USER, info.name))
						# remove entry from model
						self.model.remove(it)
				else:
					screenlets.show_error(None, 'Can\'t delete system-wide screenlets.')
		return False
	
	def load_screenlets (self):
		"""Load all available screenlets, create ScreenletInfo-objects for
		them and add them to the iconview-model."""
		# fallback icon
		noimg = gtk.gdk.pixbuf_new_from_file_at_size(\
			screenlets.INSTALL_PREFIX + '/share/screenlets-manager/noimage.svg', 
			48, 48)
		# get list of available/running screenlets
		lst_a = utils.list_available_screenlets()
		lst_r = utils.list_running_screenlets()
		if not lst_r:
			lst_r = []
		for s in lst_a:
			path = screenlets.SCREENLETS_PATH[0] + '/' + s + '/icon.svg'
			#print path
			try:
				if os.path.isfile(path):
					img = gtk.gdk.pixbuf_new_from_file_at_size(path, 48, 48)
				else:
					path = screenlets.SCREENLETS_PATH[1] + '/' + s + '/icon.svg'
					if os.path.isfile(path):
						img = gtk.gdk.pixbuf_new_from_file_at_size(path, 48, 48)
					else:
						#print "Unable to load icon for %s, using default" % s
						img = noimg
			except Exception, ex:
				#print "Exception while loading icon '%s': %s" % (path, ex)
				img = noimg
			# get metadata and create ScreenletInfo-object from it
			meta = utils.get_screenlet_metadata(s)
			info = ScreenletInfo(s, meta['name'], meta['info'], meta['author'], 
				meta['version'], img)
			# check if already running
			if lst_r.count(s + 'Screenlet'):
				info.active = True
			# check if system-wide
			#if path.startswith(screenlets.INSTALL_PREFIX):
			#	print "SYSTEM: %s" % s
			#	info.system = True
			# add to model
			self.model.append(['<span size="9000">%s</span>' % s, img, info])
	
	def quit_screenlet_by_name (self, name):
		"""Quit all instances of the given screenlet type."""
		# get service for instance and call quit method
		service = screenlets.services.get_service_by_name(name)
		if service:
			service.quit()
		
	# general handling
	
	def get_screenletinfo_by_name (self, name):
		"""Returns a ScreenletInfo-object for the screenlet with given name."""
		for row in self.model:
			if row[2] and row[2].name == name:
				return row[2]
		return None
	
	def get_selection (self):
		"""Returns a ScreenletInfo-object for the currently selected entry
		int the IconView."""
		sel = self.view.get_selected_items()
		if sel and len(sel)>0 and len(sel[0])>0:
			it = self.model.get_iter(sel[0][0])
			if it:
				return self.model.get_value(it, 2)
		return None
	
	def set_info (self, info_obj):
		"""Set the values in the infobox according to the given data in the
		ScreenletInfo-object (and recreate infobox first)."""
		# reset infobox
		self.recreate_infobox(info_obj)
	
	def set_screenlet_active (self, name, active):
		"""Set the screenlet's active-state to active (True/False)."""
		for row in self.model:
			if row[2].name == name[:-9]:
				row[2].active = active
				# if selected, also toggle checkbox
				sel = self.get_selection()
				if sel and sel.name == name[:-9]:
					self.recreate_infobox(sel)
				break
	
	# ui creation
	
	def create_ui (self):
		"""Create UI."""
		# window
		self.window = w = gtk.Window()
		w.set_title(APP_NAME)
		w.set_skip_taskbar_hint(False)
		w.set_skip_pager_hint(False)
		#w.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
		w.set_position(gtk.WIN_POS_CENTER)
		w.set_icon_from_file('/usr/share/icons/screenlets.svg')
		w.connect('delete-event', self.delete_event)
		#w.set_has_separator(False)
		# create outer vbox in window
		vbox = gtk.VBox()
		w.add(vbox)
		# create hbox for upper part
		hbox = gtk.HBox()
		vbox.pack_start(hbox, True, True)
		hbox.show()
		# iconview
		self.model= gtk.ListStore(object)
		self.view = iv = gtk.IconView()
		self.model = gtk.ListStore(str, gtk.gdk.Pixbuf, object)
		iv.set_model(self.model)
		iv.set_markup_column(0)
		iv.set_pixbuf_column(1)
		iv.connect('selection-changed', self.selection_changed)
		iv.connect('item-activated', self.item_activated)
		# wrap iconview in scrollwin
		sw = gtk.ScrolledWindow()
		sw.set_size_request(560, 300)
		sw.set_shadow_type(gtk.SHADOW_IN)
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		sw.add(iv)
		sw.show()
		# infobox at bottom (empty yet, filled later)
		# wrap scrollwin and infobox in a paned
		self.paned = paned = gtk.VPaned()
		paned.pack1(sw, True, True)
		# add paned to hbox
		hbox.pack_start(paned, True, True)
		w.set_border_width(10)
		# add HBox to dialog's vbox
		#w.vbox.add(hbox)
		#vbox.add(hbox)
		# create right area with buttons
		butbox = gtk.VBox()
		self.button_add = but1 = gtk.Button(_('Launch/Add ...'))
		but1.set_image(gtk.image_new_from_stock(gtk.STOCK_EXECUTE, 
			gtk.ICON_SIZE_BUTTON))
		but1.set_sensitive(False)
		but2 = gtk.Button(_('Install Screenlet ...'))
		but2.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, 
			gtk.ICON_SIZE_BUTTON))
		self.button_delete = but3 = gtk.Button(_('Uninstall Screenlet ...'))
		but3.set_sensitive(False)
		but3.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, 
			gtk.ICON_SIZE_BUTTON))
		but1.connect('clicked', self.button_clicked, 'add')
		but2.connect('clicked', self.button_clicked, 'install')
		but3.connect('clicked', self.button_clicked, 'uninstall')
		self.tips.set_tip(but1, _('Launch/add a new instance of the selected Screenlet ...'))
		self.tips.set_tip(but2, _('Install a new Screenlet from a zipped archive (tar.gz, tar.bz2 or zip) ...'))
		self.tips.set_tip(but3, _('Permanently uninstall/delete the currently selected Screenlet ...'))
		butbox.pack_start(but1, False)
		butbox.pack_start(but2, False)
		butbox.pack_start(but3, False)
		butbox.show_all()
		hbox.pack_end(butbox, False, False, 10)
		# create lower buttonbox
		action_area = gtk.HButtonBox()
		vbox.pack_start(action_area, False, False)
		# add about/close buttons to window
		but_about = gtk.Button(stock=gtk.STOCK_ABOUT)
		but_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		but_about.connect('clicked', self.button_clicked, 'about')
		but_close.connect('clicked', self.button_clicked, 'close')
		self.tips.set_tip(but_about, _('Show info about this dialog ...'))
		self.tips.set_tip(but_close, _('Close this dialog ...'))
		action_area.set_layout(gtk.BUTTONBOX_EDGE)
		action_area.pack_start(but_about, False, False)
		action_area.pack_end(but_close, False, False)
		vbox.show_all()
		# initially create lower infobox
		self.vbox_info = None
		self.recreate_infobox(None)
		# show window
		w.show_all()
	
	def recreate_infobox (self, info_obj):
		"""Recerate the infobox at the bottom and fill data accoring to the
		given info_obj."""
		# delete old infobox
		if self.vbox_info:
			self.vbox_info.destroy()
			del self.vbox_info
		# create new infobox
		self.vbox_info = ibox = gtk.VBox()
		ibox.set_size_request(-1, 70)
		#vbox_info.set_spacing(20)
		self.label_info = itxt = gtk.Label('')
		itxt.set_alignment(0, 0)
		itxt.set_line_wrap(True)
		#itxt.set_padding(3, 3)
		itxt.show()
		# create checkboxes
		self.cb_enable_disable = cb = gtk.CheckButton(_('Enable/Disable'))
		self.cb_autostart = cb2 = gtk.CheckButton(_('Automatically start on login'))
		if info_obj:
			cb.set_sensitive(True)
			cb2.set_sensitive(True)
			cb.set_active(info_obj.active)
			cb2.set_active(info_obj.autostart)
			itxt.set_markup('<big><b>' + info_obj.name + '</b></big>\n' + \
			info_obj.info)
		else:
			cb.set_active(False)
			cb2.set_active(False)
			cb.set_sensitive(False)
			cb2.set_sensitive(False)
		cb.connect('toggled', self.toggle_enabled)
		cb2.connect('toggled', self.toggle_autostart)
		#cb.show()
		ibox.pack_start(cb, False, False)
		ibox.pack_start(cb2, False, False, 3)
		#ibox.pack_start(itxt, True, True)
		ibox.show_all()
		# add infbox to lower paned area
		self.paned.pack2(ibox, False, True)
	
	def show_about_dialog (self):
		"""Create/Show about dialog for this app."""
		dlg = gtk.AboutDialog()
		# add baisc info
		dlg.set_name(APP_NAME)
		dlg.set_comments(_('A graphical manager application that simplifies managing, starting and (un-)installing Screenlets.'))
		dlg.set_version(APP_VERSION)
		dlg.set_copyright('(c) RYX (Rico Pfaus) 2007')
		dlg.set_website('http://www.screenlets.org')
		dlg.set_website_label('http://www.screenlets.org')
		dlg.set_license(_('This application is released under the GNU General Public License v3 (or, at your option, any later version). You can find the full text of the license under http://www.gnu.org/licenses/gpl.txt. By using, editing and/or distributing this software you agree to the terms and conditions of this license. Thank you for using free software!'))
		dlg.set_wrap_license(True)
		# add logo
		logo = gtk.gdk.pixbuf_new_from_file('/usr/share/icons/screenlets.svg')
		if logo:
			dlg.set_logo(logo)
		# run/destroy
		dlg.run()
		dlg.destroy()
	
	def show_install_dialog (self):
		"""Craete/Show the install-dialog."""
		# create filter
		flt = gtk.FileFilter()
		flt.add_pattern('*.tar.bz2')
		flt.add_pattern('*.tar.gz')
		flt.add_pattern('*.zip')
		# create dialog
		dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dlg.set_current_folder(os.environ['HOME'])
		dlg.set_title(_('Install a Screenlet'))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			installer = ScreenletInstaller()
			# try installing and show result dialog
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			result = installer.install(filename)
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
			if result:
				# reload screenlets to add new screenlet to iconview and show result
				self.model.clear()
				self.load_screenlets()
				screenlets.show_message(None, installer.get_result_message())
			else:
				screenlets.show_error(None, installer.get_result_message())
		
	# event-callbacks
	
	def button_clicked (self, widget, id):
		"""Called when one of the buttons is clicked."""
		if id == 'close':
			self.delete_event(self.window, None)
		elif id == 'about':
			self.show_about_dialog()
		elif id == 'add':
			info = self.get_selection()
			if info:
				screenlets.launch_screenlet(info.name, debug=DEBUG_MODE)
		elif id == 'install':
			self.show_install_dialog()
		elif id == 'uninstall':
			self.delete_selected_screenlet()
		elif id == 'website':
			print "TODO: open website"
	
	def handle_screenlet_registered (self, name):
		"""Callback for dbus-signal, called when a new screenlet gets 
		registered within the daemon."""
		print "REGISTER screenlet: " + name
		self.set_screenlet_active(name, True)
		
	def handle_screenlet_unregistered (self, name):
		"""Callback for dbus-signal, called when a screenlet gets 
		unregistered within the daemon."""
		print "UNREGISTER screenlet: " + name
		self.set_screenlet_active(name, False)
		
	def selection_changed (self, iconview):
		"""Callback for handling selection changes in the IconView."""
		info = self.get_selection()
		if info:
			print info.name
			self.set_info(info)
			self.button_add.set_sensitive(True)
			if not info.system:
				self.button_delete.set_sensitive(True)
			else:
				self.button_delete.set_sensitive(False)
		else:
			# nothing selected? 
			self.cb_enable_disable.set_sensitive(False)
			self.cb_autostart.set_sensitive(False)
			self.button_add.set_sensitive(False)
			self.button_delete.set_sensitive(False)
			self.label_info.set_text('')
	
	def item_activated (self, iconview, item):
		"""Callback for handling doubleclick/ENTER in the IconView."""
		info = self.get_selection()
		if info:
			# launch/add screenlet
			screenlets.launch_screenlet(info.name)
	
	def toggle_enabled (self, widget):
		"""Callback for handling changes to the Enable/Disable CheckButton."""
		info = self.get_selection()
		if info:
			info.active = not info.active
			if info.active:
				# launch screenlet
				print "Launch %s" % info.name
				screenlets.launch_screenlet(info.name, debug=DEBUG_MODE)
			else:
				# quit screenlet
				self.quit_screenlet_by_name(info.name)
				print "Quit %s" % info.name
	
	def toggle_autostart (self, widget):
		"""Callback for handling changes to the Autostart-CheckButton."""
		info = self.get_selection()
		if info:
			info.autostart = not info.autostart
			if info.autostart:
				self.create_autostarter(info.name)
			else:
				self.delete_autostarter(info.name)
			
	def delete_event (self, widget, event):
		gtk.main_quit()
		print "Quit!"
	
	# start the app
	
	def start (self):
		gtk.main()
		

app = ScreenletsManager()
app.start()
