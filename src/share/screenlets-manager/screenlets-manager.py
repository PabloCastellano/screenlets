#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Screenlets Manager - (c) RYX (Rico Pfaus) 2007  / Whise (Helder Fraga) <helder.fraga@hotmail.com>
#
# + INFO:
# This is a graphical manager application that simplifies managing and
# starting screenlets. It also allows simple install and uninstall of
# per-user Screenlets.
#
# + TODO:
# - support for using sessions (via commandline), (NOTE: if a session is selected
#   all autostart-files need to be removed and created new)
# - Help-button
# - menu
#    - different View-modes (icons/details)
#

import pygtk
pygtk.require('2.0')
import os, sys
import screenlets
from screenlets import utils,install
import gtk, gobject
import dbus
import gettext
import subprocess
import urllib


gettext.textdomain('screenlets-manager')
gettext.bindtextdomain('screenlets-manager', screenlets.INSTALL_PREFIX +  '/share/locale')


# stub for gettext
def _(s):
	#return s
	return gettext.gettext(s)


# name/version of this app
APP_NAME	= _('Screenlets Manager')
APP_VERSION	= '0.1'


# get executing user (root or normal) and set user-dependant constants
if os.geteuid()==0:
	# we run as root, install system-wide
	USER = 0
	DIR_USER		= screenlets.DIR_USER_ROOT
	DIR_AUTOSTART	= '/etc/xdg/autostart'			# TODO: use pyxdg here
else:
	# we run as normal user, install into $HOME
	USER = 1
	DIR_USER		= screenlets.DIR_USER
	DIR_AUTOSTART = utils.get_autostart_dir()





# classes


# TEST:	
#inst = ScreenletInstaller()
#print inst.get_info_from_package_name('ClockScreenlet-0.3.2.tar.bz2')
#print inst.get_info_from_package_name('/home/ryx/tmp/ExampleScreenlet-0.3.zip')
#print inst.get_info_from_package_name('/somewhere/MyScreenlet-0.1.tar.gz')
#sys.exit(1)
# /TEST


class ScreenletsManager(object):
	"""The main application class."""
	
	daemon_iface = None
	
	def __init__ (self):
		# inti props

		if not os.path.isdir(screenlets.DIR_CONFIG):
			if os.path.isdir(screenlets.OLD_DIR_CONFIG): # workaround for XDG compliance update, see https://bugs.launchpad.net/screenlets/+bug/827369
				os.rename(OLD_DIR_CONFIG, DIR_CONFIG)
			else:
				os.system('mkdir %s' % screenlets.DIR_CONFIG)
		if not os.path.isdir(DIR_USER):
			os.system('mkdir %s' % DIR_USER)	
		# create ui and populate it
		self.create_ui()
		# populate UI
		self.load_screenlets()
		# if we are running as root, show error
		if USER == 0:
			screenlets.show_error(None, _("""Important! You are running this application as root user, almost all functionality is disabled. You can use this to install screenlets into the system-wide path."""), 
				_('Warning!'))
		else:
			# lookup, connect dameon
			utils.lookup_daemon_autostart()
			self.lookup_daemon()
			self.connect_daemon()	
		
	# screenlets stuff


	

	
	def lookup_daemon (self):
		"""Find the screenlets-daemon or try to launch it. Initializes 
		self.daemon_iface if daemon is found."""
		self.daemon_iface = utils.get_daemon_iface()
		# if daemon is not available, 
		if self.daemon_iface == None:
			# try to launch it 
			print "Trying to launching screenlets-daemon ..."
			os.system(screenlets.INSTALL_PREFIX + \
				'/share/screenlets-manager/screenlets-daemon.py &')
			def daemon_check ():
				print "checking for running daemon again ..."
				self.daemon_iface = utils.get_daemon_iface()
				if self.daemon_iface:
					print "DAEMON FOUND - Ending timeout"
					self.connect_daemon()
				else:
					print "Error: Unable to connect/launch daemon."
					screenlets.show_error(None, _("Unable to connect or launch daemon. Some values may be displayed incorrectly."), _('Error'))
			import gobject
			gobject.timeout_add(2000, daemon_check)
			return False
		else:
			return True
	
	def connect_daemon (self):
		"""Connect to org.screenlets.ScreenletsDaemon and connect to
		the register/unregister signals."""
		if self.daemon_iface:
			print "DAEMON FOUND!"
			# connect to signals
			self.daemon_iface.connect_to_signal('screenlet_registered', 
				self.handle_screenlet_registered)
			self.daemon_iface.connect_to_signal('screenlet_unregistered', 
				self.handle_screenlet_unregistered)
	

	def delete_selected_screenlet (self):
		"""Delete the selected screenlet from the user's screenlet dir."""
		sel = self.view.get_selected_items()
		if sel and len(sel) > 0 and len(sel[0]) > 0:
			it = self.model.get_iter(sel[0][0])
			if it:
				info = self.model.get_value(it, 2)
				if info and not info.system:
					# delete the file
					if screenlets.show_question(None, _('Do you really want to permanently uninstall and delete the %sScreenlet from your system?') % info.name, _('Delete Screenlet')):
						# delete screenlet's directory from userdir
						os.system('rm -rf %s/%s' % (DIR_USER, info.name))
						# remove entry from model
						self.model.remove(it)
						if screenlets.show_question(None, _('Do you also want to remove the Screenlet configuration files?')):
							os.system('rm -rf %s/%s' % (screenlets.DIR_CONFIG, info.name))
							os.system('rm -rf %s/%sScreenlet.log' % (screenlets.DIR_CONFIG, info.name))
				else:
					screenlets.show_error(None, _('Can\'t delete system-wide screenlets.'))
		return False
	
	def load_screenlets (self):
		"""Load all available screenlets, create ScreenletInfo-objects for
		them and add them to the iconview-model."""
		# fallback icon
		noimg = gtk.gdk.pixbuf_new_from_file_at_size(\
			screenlets.INSTALL_PREFIX + '/share/screenlets-manager/noimage.svg', 
			56, 56)
		# get list of available/running screenlets
		lst_a = utils.list_available_screenlets()
		lst_r = utils.list_running_screenlets()

		if not lst_r:
			lst_r = []
		lst_a.sort()
		lst_filtered = []
		filter_input = str(self.txtsearch.get_text()).lower()
		combo_sel = self.combo.get_active()
		if filter_input != '':
			for s in lst_a:
				filter_slname = str(s).lower()
				filter_find = filter_slname.find(filter_input)
				if filter_input == None or filter_find != -1:
					lst_filtered.append(s)
		if lst_filtered == [] and filter_input == '': lst_filtered = lst_a
		for s in lst_filtered:
			try:
				img = utils.get_screenlet_icon(s, 56, 56)
			except Exception, ex:
				#print "Exception while loading icon '%s': %s" % (path, ex)
				img = noimg
			# get metadata and create ScreenletInfo-object from it
			meta = utils.get_screenlet_metadata(s)
			if meta:
				# get meta values
				def setfield(name, default):
					if meta.has_key(name):
						if meta[name] != None:
							return meta[name]
						else:
							return default
					else:
						return default
				name	= setfield('name', '')
				info	= setfield('info', '')
				author	= setfield('author', '')
				version	= setfield('version', '')
				# get info
				slinfo = utils.ScreenletInfo(s, name, info, author, version, img)
				# check if already running
				if lst_r.count(s + 'Screenlet'):
					slinfo.active = True
				# check if system-wide
				#if path.startswith(screenlets.INSTALL_PREFIX):
				#	print "SYSTEM: %s" % s
				#	info.system = True
			else:
				print 'Error while loading screenlets metadata for "%s".' % s
				slinfo = utils.ScreenletInfo(s, '', '', '', '', img)
			# add to model


			if combo_sel == 0:
				self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])	
			elif combo_sel == 1:
				if slinfo.active :self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])	
			elif combo_sel == 2:
				if slinfo.autostart == True :self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])	
			elif combo_sel == 3:
				if slinfo.system == True :self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])	
			elif combo_sel == 4:
				if slinfo.system == False:self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])				


	
	def get_Info_by_name (self, name):
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
	
	def reset_selected_screenlet(self):
		sel = self.view.get_selected_items()
		if sel and len(sel) > 0 and len(sel[0]) > 0:
			it = self.model.get_iter(sel[0][0])
			if it:
				info = self.model.get_value(it, 2)
				if screenlets.show_question(None, _('Do you really want to reset the %sScreenlet configuration?') % info.name, _('Reset Screenlet')):
					# delete screenlet's config directory 
					os.system('rm -rf %s/%s' % (screenlets.DIR_CONFIG, info.name))
					# remove entry from model
					
				
	def set_info (self, info_obj):
		"""Set the values in the infobox according to the given data in the ScreenletInfo-object (and recreate infobox first)."""
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
  		if USER == 0:	# add note about "root-mode"
			w.set_title(APP_NAME + ' (root mode)')
		else:
			w.set_title(APP_NAME)
		w.set_skip_taskbar_hint(False)
		w.set_skip_pager_hint(False)
		#w.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
		w.set_position(gtk.WIN_POS_CENTER)

		icontheme = gtk.icon_theme_get_default()
		w.set_icon_list(icontheme.load_icon("screenlets", 24, 0))

		w.connect('delete-event', self.delete_event)
		w.connect('notify::is-active', self.on_active_changed)

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
		# disable UI for root user
		if USER == 0:
			iv.set_sensitive(False)
		iv.connect('selection-changed', self.selection_changed)
		iv.connect('item-activated', self.item_activated)
		iv.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
				gtk.DEST_DEFAULT_DROP, #gtk.DEST_DEFAULT_ALL, 
				[("text/plain", 0, 0), 
				("image", 0, 1),
				("text/uri-list", 0, 2)], 
				gtk.gdk.ACTION_COPY)
		iv.connect("drag_data_received", self.drag_data_received)
		# wrap iconview in scrollwin
		sw = self.slwindow = gtk.ScrolledWindow()
		sw.set_size_request(560, 350)
		sw.set_shadow_type(gtk.SHADOW_IN)
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		sw.add(iv)
		sw.show()
		# infobox at bottom (empty yet, filled later)
		# wrap scrollwin and infobox in a paned
		self.paned = paned = gtk.VPaned()
		paned.pack1(sw, True, True)
		# add paned to hbox
		hbox.pack_end(paned, True, True)
		w.set_border_width(5)
		# add HBox to dialog's vbox
		#w.vbox.add(hbox)
		#vbox.add(hbox)
		# create right area with buttons
		butbox = self.bbox = gtk.VBox()
		self.button_add = but1 = gtk.Button(_('Launch/Add'))
		#but1.set_image(gtk.image_new_from_stock(gtk.STOCK_EXECUTE, 
		#	gtk.ICON_SIZE_BUTTON))
		but1.set_sensitive(False)
		but2 = gtk.Button(_('Install'))
		#but2.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, 
		#	gtk.ICON_SIZE_BUTTON))
		self.button_delete = but3 = gtk.Button(_('Uninstall'))
		but3.set_sensitive(False)
		#but3.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, 
		#	gtk.ICON_SIZE_BUTTON))
		self.button_reset = but4 = gtk.Button(_('Reset Screenlet Config'))
		but4.set_sensitive(False)
		#but4.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, 
		#	gtk.ICON_SIZE_BUTTON))
		self.button_theme = but5 = gtk.Button(_('Install New Theme'))
		but5.set_sensitive(False)
		#but5.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, 
		#	gtk.ICON_SIZE_BUTTON))
		self.button_restartall = but6 = gtk.Button(_('Re-Start All'))
		but6.set_sensitive(True)		
		#but6.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH, 
		#	gtk.ICON_SIZE_BUTTON))
		self.button_closeall = but7 = gtk.Button(_('Close All'))
		but7.set_sensitive(True)
		#but7.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, 
		#	gtk.ICON_SIZE_BUTTON))
		self.button_prop = but8 = gtk.Button(_('Options'))
		but8.set_sensitive(True)
		self.button_shortcut = but9 = gtk.Button(_('Create Desktop Shortcut'))
		but9.set_sensitive(False)
		#but8.set_image(gtk.image_new_from_stock(gtk.STOCK_PROPERTIES, 
		#	gtk.ICON_SIZE_BUTTON))
		#self.sep = gtk.Separator()	
		but1.connect('clicked', self.button_clicked, 'add')
		but2.connect('clicked', self.button_clicked, 'install')
		but3.connect('clicked', self.button_clicked, 'uninstall')
		but4.connect('clicked', self.button_clicked, 'reset')
		but5.connect('clicked', self.button_clicked, 'theme')
		but6.connect('clicked', self.button_clicked, 'restartall')
		but7.connect('clicked', self.button_clicked, 'closeall')
		but8.connect('clicked', self.button_clicked, 'prop')
		but9.connect('clicked', self.button_clicked, 'desktop_shortcut')
		but1.set_relief(gtk.RELIEF_NONE)
		but2.set_relief(gtk.RELIEF_NONE)
		but3.set_relief(gtk.RELIEF_NONE)
		but4.set_relief(gtk.RELIEF_NONE)
		but5.set_relief(gtk.RELIEF_NONE)
		but6.set_relief(gtk.RELIEF_NONE)
		but7.set_relief(gtk.RELIEF_NONE)
		but8.set_relief(gtk.RELIEF_NONE)
		but9.set_relief(gtk.RELIEF_NONE)
		but1.set_alignment(0,0.5)
		but2.set_alignment(0,0.5)
		but3.set_alignment(0,0.5)
		but4.set_alignment(0,0.5)
		but5.set_alignment(0,0.5)
		but6.set_alignment(0,0.5)
		but7.set_alignment(0,0.5)
		but8.set_alignment(0,0.5)
		but9.set_alignment(0,0.5)
		but1.set_tooltip_text(_("Launch/add a new instance of the selected Screenlet ..."))
		but2.set_tooltip_text(_("Install a new Screenlet, SuperKaramba or Web Widget or Web Application  ..."))
		but3.set_tooltip_text(_("Permanently uninstall/delete the currently selected Screenlet ..."))
		but4.set_tooltip_text(_("Reset this Screenlet configuration (will only work if Screenlet isn't running)"))
		but5.set_tooltip_text(_("Install new theme for this screenlet"))
		but6.set_tooltip_text(_("Restart all Screenlets that have auto start at login"))
		but7.set_tooltip_text(_("Close all Screenlets running"))
		but8.set_tooltip_text(_("New Screenlets Options/Properties"))
		but9.set_tooltip_text(_("Create a Desktop shortcut for this Screenlet"))
		self.label = gtk.Label('')
		self.label.set_line_wrap(1)
		self.label.set_width_chars(70)
		self.label.set_alignment(0, 0)
		self.label.set_size_request(-1, 65)
    		self.btnsearch = gtk.Button()
    		self.searchbox = gtk.HBox()
    		self.txtsearch = gtk.Entry()
		self.btnsearch.set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE, 
			gtk.ICON_SIZE_BUTTON))
    		self.btnsearch.connect("clicked",self.redraw_screenlets, 'clean')
    		self.txtsearch.connect("changed",self.redraw_screenlets, 'enter')
    		self.txtsearch.connect("backspace",self.redraw_screenlets, 'backspace')

    		self.searchbox.pack_start(self.txtsearch, 1)
    		self.searchbox.pack_start(self.btnsearch, False)
		butbox.pack_start(self.searchbox, False,0,3)
		self.combo = gtk.combo_box_new_text()
		self.combo.append_text(_('All Screenlets'))
		self.combo.append_text(_('Running Screenlets'))
		self.combo.append_text(_('Autostart Screenlets'))
		self.combo.append_text(_('Only native Screenlets'))
		self.combo.append_text(_('Only third party'))
		self.combo.set_active(0)
    		self.combo.connect("changed",self.redraw_screenlets, 'enter')
		self.combo.show()
		butbox.pack_start(but1, False)
		butbox.pack_start(but2, False)
		butbox.pack_start(but3, False)
		butbox.pack_start(but4, False)
		butbox.pack_start(but5, False)
		butbox.pack_start(but6, False)
		butbox.pack_start(but7, False)
		butbox.pack_start(but9, False)
		#sep2 =   gtk.HSeparator()
		#butbox.pack_start(sep2, False,False,5)
		butbox.pack_start(but8, False)
		butbox.pack_start(self.combo, False)
		#butbox.pack_start(self.label, False)
		butbox.show_all()
		hbox.pack_start(butbox, False, False, 10)

		# create lower buttonbox
		action_area = gtk.HButtonBox()
		vbox.pack_start(action_area, False, False)
		# add about/close buttons to window
		but_about = gtk.Button(stock=gtk.STOCK_ABOUT)
		but_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		but_download = gtk.Button(_('Get more screenlets'))
		but_download.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_DOWN, 
			gtk.ICON_SIZE_BUTTON))
		but_about.connect('clicked', self.button_clicked, 'about')
		but_close.connect('clicked', self.button_clicked, 'close')
		but_download.connect('clicked', self.button_clicked, 'download')
		but_about.set_tooltip_text(_("Show info about this dialog ..."))
		but_download.set_tooltip_text(_("Download more screenlets ..."))
		but_close.set_tooltip_text(_("Close this dialog ..."))
		action_area.set_layout(gtk.BUTTONBOX_EDGE)
		action_area.pack_start(but_about, False, False)
		action_area.pack_start(but_download, False, False)
		action_area.pack_end(but_close, False, False)
		vbox.show_all()
		# initially create lower infobox
		self.vbox_info = None
		self.recreate_infobox(None)
		# show window
		#self.gtk_screen = w.get_screen()
  		#colormap = self.gtk_screen.get_rgba_colormap()
  		#if colormap:
      		#	self.window.set_colormap(colormap)
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
		self.cb_enable_disable = cb = gtk.CheckButton(_('Start/Stop'))
		self.cb_autostart = cb2 = gtk.CheckButton(_('Auto start on login'))
		self.cb_tray = cb3 = gtk.CheckButton(_('Show daemon in tray'))
		ini = utils.IniReader()
		
		if ini.load (DIR_USER + '/config.ini'):
		
			print ini.get_option('show_in_tray')
		if not os.path.isfile(DIR_USER + '/config.ini'):
			f = open(DIR_USER + '/config.ini', 'w')
			f.write("[Options]\n")
			f.write("show_in_tray=True\n")
			f.write("Keep_above=False\n")
			f.write("Keep_below=True\n")
			f.close()
		try:
			if ini.load(DIR_USER + '/config.ini'):
				show_in_tray = ini.get_option('show_in_tray', section='Options')
				if show_in_tray == 'True': #doesnt work with the bool variable directly..dont know why
					cb3.set_active(True)
				else:
					cb3.set_active(False)
			
		except:
			f = open(DIR_USER + '/config.ini', 'w')
			f.write("[Options]\n")
			f.write("show_in_tray=True\n")
			f.write("Keep_above=False\n")
			f.write("Keep_below=True\n")
			f.close()
			if ini.load(DIR_USER + '/config.ini'):
				show_in_tray = ini.get_option('show_in_tray', section='Options')
				if show_in_tray == 'True':
					cb3.set_active(True)
				else:
					cb3.set_active(False)
			
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
		cb3.connect('toggled', self.toggle_tray)
		#cb.show()
		sep2 =   gtk.HSeparator()
		ibox.pack_start(cb, False, False)
		ibox.pack_start(cb2, False,False, 3)
		ibox.pack_start(sep2, False,False,3)
		ibox.pack_start(cb3, False,False)
		#ibox.pack_start(itxt, True, True)
		ibox.show_all()
		# add infbox to lower paned area
		self.paned.pack2(self.label,False,False)
		#self.bbox.set_spacing(2)
		sep1 =   gtk.HSeparator()
		#self.bbox.pack_start(sep1, False,False,5)
		self.bbox.pack_start(ibox, False,False)

	def redraw_screenlets(self,widget,id):
		if id == 'backspace':
			if len(self.txtsearch.get_text()) == 1:
				self.txtsearch.set_text('')
		elif id == 'clean':
			self.txtsearch.set_text('')
		else:
			self.model.clear()
			self.load_screenlets()

	def show_about_dialog (self):
		"""Create/Show about dialog for this app."""
		dlg = gtk.AboutDialog()
		gtk.about_dialog_set_url_hook(self.website_open, None)
		# add baisc info
		dlg.set_name(screenlets.APP_NAME)
		dlg.set_comments(_(screenlets.COMMENTS))
		dlg.set_version(screenlets.VERSION)
		dlg.set_copyright(screenlets.COPYRIGHT)
		dlg.set_authors(screenlets.AUTHORS)
		dlg.set_website(screenlets.WEBSITE)
		dlg.set_website_label(screenlets.WEBSITE)
		dlg.set_license(_('This application is released under the GNU General Public License v3 (or, at your option, any later version). You can find the full text of the license under http://www.gnu.org/licenses/gpl.txt. By using, editing and/or distributing this software you agree to the terms and conditions of this license. Thank you for using free software!'))
		dlg.set_wrap_license(True)
		dlg.set_documenters(screenlets.DOCUMENTERS)
		dlg.set_artists(screenlets.ARTISTS)
		dlg.set_translator_credits(screenlets.TRANSLATORS)
		# add logo
		icontheme = gtk.icon_theme_get_default()
		logo = icontheme.load_icon("screenlets", 128, 0)
		if logo:
			dlg.set_logo(logo)
		# run/destroy
		dlg.run()
		dlg.destroy()
		
	def website_open(self, d, link, data):
		subprocess.Popen(["xdg-open", "http://www.screenlets.org"])

	# could be used to reload screenlets on every activation (but it's a bit too much)
	def on_active_changed(self, window, param):
		if window.is_active():
			# this makes the right one started/used at least if not displayed
			utils.refresh_available_screenlet_paths()
			# this seems too much (but if saved the active selection in view, maybe it could work)
#			self.model.clear()
#			self.load_screenlets()

	def drag_data_received (self, widget, dc, x, y, sel_data, info, timestamp):
			
		print "Data dropped ..."
		filename = ''
		# get text-elements in selection data
		try:
			txt = unicode.encode(sel_data.get_text(), 'utf-8')

		except:
			txt = sel_data.get_text()
		txt = urllib.unquote(txt)
		if txt:
			if txt[-1] == '\n':
				txt = txt[:-1]
			txt.replace('\n', '\\n')
			# if it is a filename, use it
			if txt.startswith('file://'):
				filename = txt[7:]
			else:
				screenlets.show_error(self, _('Invalid string: %s.') % txt)
		else:
			# else get uri-part of selection
			uris = sel_data.get_uris()
			if uris and len(uris)>0:
				#print "URIS: "+str(uris	)
				filename = uris[0][7:]
		if filename != '':
			#self.set_image(filename)
			installer = install.ScreenletInstaller()
			if not utils.containsAny(filename,'%'):
				result = installer.install(filename)
				if result:
				# reload screenlets to add new screenlet to iconview and show result
					self.model.clear()
					self.load_screenlets()
					screenlets.show_message(None, installer.get_result_message())
				else:
					screenlets.show_error(None, installer.get_result_message())
			else:
				self.show_install_dialog()
				print 'Please install screenlets from folders without strange characters'

	def show_install_dialog (self):
		"""Craete/Show the install-dialog."""
		# create filter
		flt = gtk.FileFilter()
		flt.add_pattern('*.tar.bz2')
		flt.add_pattern('*.skz')
		flt.add_pattern('*.tar.gz')
		flt.add_pattern('*.zip')
		# create dialog
		dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dlg.set_current_folder(os.environ['HOME'])
		dlg.set_title(_('Install a Screenlet or SuperKaramba theme'))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			installer = install.ScreenletInstaller()
			# TEST
			#print installer.get_info_from_package_name (filename)
			#return
			# /TEST
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

	def show_install_theme_dialog (self):
		"""Craete/Show the install-dialog."""
		# create filter
		flt = gtk.FileFilter()
		flt.add_pattern('*.tar.bz2')
		flt.add_pattern('*.tar.gz')
		flt.add_pattern('*.zip')
		try: os.system('rm -rf /tmp/screenlets/install-temp')
		except:pass
		# create dialog
		dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dlg.set_current_folder(os.environ['HOME'])
		dlg.set_title((_('Install a new theme for the selected Screenlet')))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			
			# try installing and show result dialog
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			print 'Installing %s' % filename
			result = False
			info = self.get_selection()
			basename	= os.path.basename(filename)
			ext	= str(filename)[len(str(filename)) -3:]
	
			tar_opts = 'xfz'
			if ext == 'bz2':
				tar_opts = 'xfj'
			x = 0
			y = 0
			
#			if not info.system:
			install_dir = DIR_USER + '/' 
			themes_dir = DIR_USER + '/' + info.name + '/themes/'
			install_prefix = ''
#			else:
#				if not screenlets.show_question(None, _("You are about to install a theme in root mode. Continue only if you have gksudo installed, do you wish to continue?")):
#					self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
#					result = False
#				themes_dir = screenlets.INSTALL_PREFIX + '/share/screenlets' + '/'  + info.name + '/themes/'
#				install_dir = screenlets.INSTALL_PREFIX + '/share/screenlets' + '/' 
#				install_prefix = 'gksudo '

			if not os.path.isdir('/tmp/screenlets/'):
				os.system('mkdir ' + '/tmp/screenlets/')
		
			tmpdir = '/tmp/screenlets' + '/install-temp/'
			os.system('mkdir %s' % tmpdir)
		
			os.system('tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), tmpdir))
			try:
				print os.listdir(tmpdir)[0]
			except:				
				screenlets.show_message(None, _("Error Found"))				
				self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
				result = False #is it a valid folder?
				
			if not os.path.exists(tmpdir + os.listdir(tmpdir)[0]):	
				screenlets.show_message(None, _("Theme install error 1 found - Theme not installed , maybe a package error "))				
				self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
				result = False #is it a valid folder?

			if os.listdir(tmpdir)[0] == 'themes': 
				install_dir = install_dir + info.name
				print "list contains themes folder"
			elif os.listdir(tmpdir)[0] == info.name:
				print "list contains the screenlet name folder"
				install_dir = install_dir
				if os.path.exists(tmpdir + os.listdir(tmpdir)[0] + '/'+ info.name + 'Screenlet.py') and os.path.isfile(tmpdir + os.listdir(tmpdir)[0] + '/'+ info.name + 'Screenlet.py'):
					screenlets.show_message(None, _("This package seams to contain a full Screenlet and not just a theme, please use the screenlet install instead"))
					self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))			
					return False
			else:
				z =0 
				for f in os.listdir(tmpdir + os.listdir(tmpdir)[0]):
					f = str(f).lower()
					
					if f.endswith('png') or f.endswith('svg'):
						if not f.startswith('icon'):
							z=z+1
				if z == 0:
					screenlets.show_message(None, _("This package doesnt seem to contain a theme"))
					self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
					return False
				install_dir = install_dir + info.name + '/themes/'
				print "only contains the themes folders"
						
			os.system('rm -rf %s/install-temp' % screenlets.DIR_TMP)

			os.system('mkdir -p ' + themes_dir)

			for f in os.listdir(themes_dir):
				x= x +1
			if install_prefix != '':
				os.system(install_prefix +chr(34) +'tar '+tar_opts+' '+ chr(39)+ filename + chr(39)+ ' -C ' + chr(39) + install_dir + chr(39)+chr(34))
			else:
				os.system('tar '+tar_opts+' '+ chr(39)+ filename + chr(39)+ ' -C ' + chr(39) + install_dir + chr(39))

 #% (tar_opts, chr(39)+ filename + chr(39), chr(39) + screenlets.INSTALL_PREFIX + '/share/screenlets' + '/' + info.name + '/themes/'+ chr(39)))
			for f in os.listdir(themes_dir):
				y= y +1

			if y > x:
				
				screenlets.show_message(None, _("Theme installed , please restart %s") % info.name )
				self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
				result = True

			else:
				screenlets.show_message(None, _("Theme install error 2 found - Theme not installed or already installed"))
				self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
				result = False
		else:
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
			result = False
	# event-callbacks
	
	def button_clicked (self, widget, id):
		"""Called when one of the buttons is clicked."""
		if id == 'close':
			self.delete_event(self.window, None)
		elif id == 'widgetsite':
			a = self.combo1.get_active()
			if a == 0:
				os.system("xdg-open http://www.google.com/ig/directory?synd=open &")
			elif a == 1:
				os.system("xdg-open http://www.yourminis.com/minis &")
			elif a == 2:
				os.system("xdg-open http://www.springwidgets.com/widgets/ &")
			elif a == 3:
				os.system("xdg-open http://www.widgetbox.com/galleryhome/ &")

		elif id == 'about':
			self.show_about_dialog()
		elif id == 'add':
			info = self.get_selection()
			if info:
				screenlets.launch_screenlet(info.name, debug=screenlets.DEBUG_MODE)
				
		elif id == 'install':
			self.show_install_chose_ui()
		elif id == 'uninstall':
			self.delete_selected_screenlet()
		elif id == 'reset':
			self.reset_selected_screenlet()
		elif id == 'theme':
			self.show_install_theme_dialog()
		elif id == 'prop':
			self.show_options_ui()
		elif id == 'desktop_shortcut':
			info = self.get_selection()
			name = info.name
			path = utils.find_first_screenlet_path(name)
			desk = utils.get_desktop_dir()
			if name.endswith('Screenlet'):
				name = name[:-9]
			starter = '%s/%sScreenlet.desktop' % (desk, name)
			if path:
				print "Create desktop shortcut for: %s/%sScreenlet.py" % (path, name)
				code = ['[Desktop Entry]']
				code.append('Name=%sScreenlet' % name)
				code.append('Encoding=UTF-8')
				code.append('Version=1.0')
				if os.path.exists('%s/icon.svg' % path):
					code.append('Icon=%s/icon.svg' % path)
				elif os.path.exists('%s/icon.png' % path):
					code.append('Icon=%s/icon.png' % path)
				code.append('Type=Application')
				code.append('Exec= python -u %s/%sScreenlet.py > /dev/null' % (path, name))
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
		elif id == 'restartall':
			utils.quit_all_screenlets()
			for s in os.listdir(DIR_AUTOSTART):
		
				if s.lower().endswith('screenlet.desktop'):
					#s = s[:-17]
					os.system('sh '+ DIR_AUTOSTART + s + ' &')	
		elif id == 'closeall':
			utils.quit_all_screenlets()

		elif id == 'download':
			if screenlets.UBUNTU:
				utils.get_more_screenlets_ubuntu()
			else:
				subprocess.Popen(["xdg-open", screenlets.THIRD_PARTY_DOWNLOAD])
			
	def show_install_chose_ui(self):
		install_combo = gtk.combo_box_new_text()
		install_combo.append_text(_('Install Screenlet'))
		install_combo.append_text(_('Install SuperKaramba Theme'))
		install_combo.append_text(_('Convert Web Widget'))
		install_combo.append_text(_('Install Web Application'))
		install_combo.set_active(0)
       		dialog = gtk.Dialog(_("Install"),self.window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		install_combo.show()
		dialog.vbox.add(install_combo)
		resp = dialog.run()
		ret = None
		if resp == gtk.RESPONSE_ACCEPT:
			if install_combo.get_active() == 0 or install_combo.get_active() == 1:
				self.show_install_dialog()
			elif install_combo.get_active() == 2:
				self.show_widget_converter()
			elif install_combo.get_active() == 3:
				self.show_webapp()						
		dialog.destroy()

	def show_options_ui(self):
		label = gtk.Label(_('New screenlets atributes..'))
		cb1 = gtk.CheckButton(_('Lock'))
		cb2 = gtk.CheckButton(_('Sticky'))
		cb3 = gtk.CheckButton(_('Widget'))
		cb4 = gtk.CheckButton(_('Keep above'))
		cb4.set_active(True)
		cb5 = gtk.CheckButton(_('Keep below'))
		cb6 = gtk.CheckButton(_('Show buttons'))
		ini = utils.IniReader()
		if ini.load (DIR_USER + '/config.ini'):
				
			if ini.get_option('Lock', section='Options') == 'True':
				cb1.set_active(True)
			elif ini.get_option('Lock', section='Options') == 'False':
				cb1.set_active(False)
			if ini.get_option('Sticky', section='Options') == 'True':
				cb2.set_active(True)
			elif ini.get_option('Sticky', section='Options') == 'False':
				cb2.set_active(False)
			if ini.get_option('Widget', section='Options') == 'True':
				cb3.set_active(True)
			elif ini.get_option('Widget', section='Options') == 'False':
				cb3.set_active(False)
			if ini.get_option('Keep_above', section='Options') == 'True':
				cb4.set_active(True)
			elif ini.get_option('Keep_above', section='Options') == 'False':
				cb4.set_active(False)
			else:
				cb4.set_active(True)
			if ini.get_option('Keep_below', section='Options') == 'True':
				cb5.set_active(True)
			elif ini.get_option('Keep_below', section='Options') == 'False':
				cb5.set_active(False)
			if ini.get_option('draw_buttons', section='Options') == 'True':
				cb6.set_active(True)
			elif ini.get_option('draw_buttons', section='Options') == 'False':
				cb6.set_active(False)
			else:
				cb6.set_active(True)					
		dialog = gtk.Dialog(_("New Screenlets atributes"),
                    self.window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		label.show()
		cb1.show()
		cb2.show()
		cb3.show()
		cb4.show()
		cb5.show()
		cb6.show()
		dialog.vbox.add(label)
		dialog.vbox.add(cb1)
		dialog.vbox.add(cb2)
		dialog.vbox.add(cb3)
		dialog.vbox.add(cb4)
		dialog.vbox.add(cb5)
		dialog.vbox.add(cb6)				
		
		resp = dialog.run()
		ret = None
		if resp == gtk.RESPONSE_ACCEPT:
			
			ret = 'show_in_tray=' + str(self.cb_tray.get_active()) + '\n'
			ret = ret + 'Lock=' + str(cb1.get_active()) + '\n'
			ret = ret + 'Sticky=' + str(cb2.get_active()) + '\n'
			ret = ret + 'Widget=' + str(cb3.get_active()) + '\n'
			ret = ret + 'Keep_above=' + str(cb4.get_active()) + '\n'
			ret = ret + 'Keep_below=' + str(cb5.get_active()) + '\n'
			ret = ret + 'draw_buttons=' + str(cb6.get_active()) + '\n'	
			f = open(DIR_USER + '/config.ini', 'w')
			f.write("[Options]\n")
			f.write(ret)
			f.close()
		dialog.destroy()

	def show_webapp(self):
		label1 = gtk.Label(_('Web Application Url'))
		label2 = gtk.Label(_('Web Application Name'))
		code = gtk.Entry()
		name = gtk.Entry()
		h = gtk.HBox()
		h1 = gtk.HBox()	
		h.pack_start(label1,False,False)
		h.pack_start(code,True,True)
		h1.pack_start(label2,False,False)
		h1.pack_start(name,True,True)
      		dialog = gtk.Dialog(_("Install Web Application"),self.window,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    		label1.show()
    		label2.show()
		code.show()
		name.show()
		h.show()
		h1.show()
		dialog.vbox.pack_start(h,False,False,5)
		dialog.vbox.pack_start(h1,False,False,5)
				
			
		resp = dialog.run()
		ret = None
		if resp == gtk.RESPONSE_ACCEPT:
			if code.get_text() != '':
				if name.get_text() != '':
					try:
						a = name.get_text()
						a = a.replace(' ','')
						if os.path.isdir(DIR_USER + '/' + a):#found_path != None:
							if screenlets.show_question(None,(_("There is already a screenlet with that name installed\nDo you wish to continue?") )):
								pass
							else: 
								return False
						os.system('mkdir ' +DIR_USER + '/' + a)
						os.system('mkdir ' +DIR_USER + '/' + a + '/themes')
						os.system('mkdir ' +DIR_USER + '/' + a + '/themes/default')
						os.system('mkdir ' +DIR_USER + '/' + a + '/mozilla')
						os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/WebappScreenlet.py ' +DIR_USER + '/' + a + '/' + a + 'Screenlet.py')
						os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/webapp.png ' +DIR_USER + '/' + a + '/icon.png')				
						os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/webapp.png ' +DIR_USER + '/' + a + '/themes/default')
		
						enginecopy = open(DIR_USER + '/' + a + '/' + a + 'Screenlet.py','r')
						enginesave = enginecopy.read()
						enginesave = enginesave.replace('WebappScreenlet',a + 'Screenlet')
						enginesave = enginesave.replace("url = 'myurl'","url = " + chr(34) + code.get_text() + chr(34))
						enginecopy.close()
						enginecopy = open(DIR_USER + '/' + a + '/' + a + 'Screenlet.py','w')
						enginecopy.write(enginesave)
						enginecopy.close()
						screenlets.show_message (None,_("Web Application was successfully installed"))
						self.model.clear()
						self.load_screenlets()			
					except:	screenlets.show_error(None,_("Error installing!!!"))
				else:	screenlets.show_error(None,_("Please specify a name for the widget"))
			else:	screenlets.show_error(None,_("No HTML code found"))
		dialog.destroy()

	def show_widget_converter(self):
		label1 = gtk.Label(_('Convert any webpage widget into a Screenlet.'))
		label2 = gtk.Label(_('Step 1 : Find the widget you want to convert'))
		label3 = gtk.Label(_('Step 2 : Copy and Paste the HTML from the widget in the box below'))
		label4 = gtk.Label(_('Step 3 : Give it a name in the box below and click on Ok to convert'))
		label5 = gtk.Label(_('The name of the widget'))
		code = gtk.Entry()
		name = gtk.Entry()
		h = gtk.HBox()
		h1 = gtk.HBox()
		self.combo1 = combo = gtk.combo_box_new_text()
		combo.append_text('Google Gadgets')
		combo.append_text('Yourminis Widgets')
		combo.append_text('SpringWidgets')
		combo.append_text('Widgetbox')
		combo.set_active(0)
		web = gtk.Button('Go to web page')
		web.connect('clicked', self.button_clicked, 'widgetsite')
    		label1.show()
    		label2.show()
    		label3.show()
    		label4.show()
    		label5.show()
		combo.show()
		name.show()
		web.show()
		h.show()
		h1.show()
		code.show()
		dialog = gtk.Dialog(_("Widget converter"),
                    self.window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		#dialog.set_size_request(300, 500)
		dialog.vbox.pack_start(label1,False,False,20)
		dialog.vbox.pack_start(label2,True,False,5)
		h.pack_start(combo,True,True,5)
		h.pack_start(web,False,False,5)
		dialog.vbox.pack_start(h,False,False,5)
		dialog.vbox.pack_start(label3,False,False,10)
		dialog.vbox.pack_start(code,False,False,5)
		dialog.vbox.pack_start(label4,False,False,5)
		h1.pack_start(label5,False,False,5)			
		h1.pack_start(name,True,True,5)
		dialog.vbox.pack_start(h1,False,False,5)
		resp = dialog.run()
		ret = None
		if resp == gtk.RESPONSE_ACCEPT:
			if code.get_text() != '':
				if name.get_text() != '':
					try:
						a = name.get_text()
						a = a.replace(' ','')
						if os.path.isdir(DIR_USER + '/' + a):#found_path != None:
							if screenlets.show_question(None,(_("There is already a screenlet with that name installed\nDo you wish to continue?") )):
								pass
							else: 
								return False
						os.system('mkdir ' +DIR_USER + '/' + a)
						os.system('mkdir ' +DIR_USER + '/' + a + '/themes')
						os.system('mkdir ' +DIR_USER + '/' + a + '/themes/default')
						os.system('mkdir ' +DIR_USER + '/' + a + '/mozilla')
						f = open(DIR_USER + '/' + a  + '/' + 'index.html' , 'w')
						f.write(code.get_text())
						f.close()
						os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/WidgetScreenlet.py ' +DIR_USER + '/' + a + '/' + a + 'Screenlet.py')
						os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/widget.png ' +DIR_USER + '/' + a + '/icon.png')				
						os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/widget.png ' +DIR_USER + '/' + a + '/themes/default')
						enginecopy = open(DIR_USER + '/' + a + '/' + a + 'Screenlet.py','r')
						enginesave = enginecopy.read()
						enginesave = enginesave.replace('WidgetScreenlet',a + 'Screenlet')
						enginecopy.close()
						enginecopy = open(DIR_USER + '/' + a + '/' + a + 'Screenlet.py','w')
						enginecopy.write(enginesave)
						enginecopy.close()
						screenlets.show_message (None,_("Widget was successfully converted"))
						self.model.clear()
						self.load_screenlets()			
					except:	screenlets.show_error(None,_("Error converting!!!"))
				else:	screenlets.show_error(None,_("Please specify a name for the widget"))		
			else:	screenlets.show_error(None,_("No HTML code found"))			
		dialog.destroy()

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
		self.slwindow.set_size_request(560, 300)
		info = self.get_selection()
		if info:
			
			self.set_info(info)
			self.label.set_line_wrap(1)
			a = info.name + ' ' + info.version+' by ' + info.author + '\n' + info.info
			a = a[:200]
			self.label.set_label(a + '...')

			self.button_add.set_sensitive(True)
			self.button_reset.set_sensitive(True)
			self.button_theme.set_sensitive(True)
#			self.button_restartall.set_sensitive(True)
#			self.button_closeall.set_sensitive(True)
			if not info.system:
				self.button_delete.set_sensitive(True)
			else:
				self.button_delete.set_sensitive(False)
			self.button_shortcut.set_sensitive(True)
		else:
			# nothing selected? 
			self.label.set_label('')
			self.cb_enable_disable.set_sensitive(False)
			self.cb_autostart.set_sensitive(False)
			self.button_add.set_sensitive(False)
			self.button_delete.set_sensitive(False)
			self.button_reset.set_sensitive(False)
			self.button_theme.set_sensitive(False)	
			self.button_shortcut.set_sensitive(False)
#			self.button_restartall.set_sensitive(False)
#			self.button_closeall.set_sensitive(False)
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
				screenlets.launch_screenlet(info.name, debug=screenlets.DEBUG_MODE)
				
			else:
				# quit screenlet
				utils.quit_screenlet_by_name(info.name)
				print "Quit %s" % info.name
				self.model.clear()
				self.load_screenlets()

	def toggle_autostart (self, widget):
		"""Callback for handling changes to the Autostart-CheckButton."""
		info = self.get_selection()
		if info:
			info.autostart = not info.autostart
			if info.autostart:
				if not utils.create_autostarter(info.name):
					widget.set_active(False)
					widget.set_sensitive(False)
			else:
				utils.delete_autostarter(info.name)

	def toggle_tray (self, widget):
		"""Callback for handling changes to the tray-CheckButton."""
		ini = utils.IniReader()
		if ini.load (DIR_USER + '/config.ini'):
			r = ''
			if ini.get_option('Lock', section='Options') != None:
				r = r +  'Lock=' + str(ini.get_option('Lock', section='Options')) + '\n'
				
			if ini.get_option('Sticky', section='Options') != None:
				r = r +  'Sticky=' + str(ini.get_option('Sticky', section='Options')) + '\n'
				
			if ini.get_option('Widget', section='Options') != None:
				r = r +  'Sticky=' + str(ini.get_option('Sticky', section='Options')) + '\n'
				
			if ini.get_option('Keep_above', section='Options') != None:
				r = r +  'Keep_above=' + str(ini.get_option('Keep_above', section='Options')) + '\n'
		
			if ini.get_option('Keep_below', section='Options') != None:
				r = r +  'Keep_below=' + str(ini.get_option('Keep_below', section='Options')) + '\n'

			if ini.get_option('draw_buttons', section='Options') != None:
				r = r +  'draw_buttons=' + str(ini.get_option('draw_buttons', section='Options')) + '\n'

		f = open(DIR_USER + '/config.ini', 'w')
		DIR_USER + '/config.ini'
		f.write("[Options]\n")
		f.write("show_in_tray="+str(widget.get_active())+"\n")
		f.write(r)
		f.close()
		os.system('pkill -f screenlets-daemon.py') #restart the daemon
		os.system(screenlets.INSTALL_PREFIX + \
				'/share/screenlets-manager/screenlets-daemon.py &')
		screenlets.show_message(None, _('Screenlets-Manager must now be restarted'))
		try:
			os.system('screenlets-manager &')	
		except:
			pass
		self.delete_event(self.window, None)		
				
	def delete_event (self, widget, event):

		gtk.widget_pop_colormap()
		gtk.main_quit()
		print "Quit!"
	
	# start the app
	
	def start (self):
		gtk.main()
		
import os
proc = os.popen("""ps axo "%p,%a" | grep "python.*screenlets-manager.py" | grep -v grep|cut -d',' -f1""").read()
procs = proc.split('\n')
import sys
import wnck
try:
	wnck.set_client_type(wnck.CLIENT_TYPE_PAGER)
except AttributeError:
	print "Error: Failed to set libwnck client type, window " \
				"activation may not work"
if len(procs) > 2:
	print "Manager already started"
	screen = wnck.screen_get_default()
	while gtk.events_pending():
		gtk.main_iteration()
	wins = screen.get_windows_stacked()
	
	for win in wins:
		name = win.get_name()
		if name == gettext.gettext('Screenlets Manager'):

			if win and win.is_active():
				sys.exit(1)
			elif win and win.is_minimized():
				win.unminimize(1)
			elif win and win.is_active() == False:
				win.activate(1)


	sys.exit(1)


app = ScreenletsManager()
app.start()
