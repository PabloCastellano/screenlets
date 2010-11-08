#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# ScreenletsDaemon - (c) RYX (Rico Pfaus) 2007 and Whise Helder Fraga
# <helder.fraga@hotmail.com>
# + INFO:
# This is a background daemon that keeps track of opened screenlets. The
# screenlets.session.ScreenletSession currently (ab)uses this as a workaround
# for the incomplete pyinotify-support in common distros.
#
# + TODO:
# - use a filewatch on '/tmp/screenlets/screenlets.running' instead of 
#   requring screenlets to register themselves with the daemon??
#

import os
import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	if getattr(dbus, 'version', (0,0,0)) <= (0,80,0):
		
		import dbus.glib
	else:
		
		from dbus.mainloop.glib import DBusGMainLoop
		DBusGMainLoop(set_as_default=True)
import gobject
import screenlets
from screenlets.menu import add_menuitem, add_image_menuitem
import gtk
from screenlets import utils, install
import gettext

gettext.textdomain('screenlets-manager')
gettext.bindtextdomain('screenlets-manager', screenlets.INSTALL_PREFIX +  '/share/locale')


def _(s):
	return gettext.gettext(s)

SLD_BUS		= 'org.screenlets.ScreenletsDaemon'
SLD_PATH	= '/org/screenlets/ScreenletsDaemon'
SLD_IFACE	= 'org.screenlets.ScreenletsDaemon'
DIR_USER	= os.environ['HOME'] + '/.screenlets'
DIR_TMP		= '/tmp/screenlets/'

class ScreenletsDaemon (dbus.service.Object):
	"""A simple backend class where screenlets register and unregister. It
	offers functions to keep track of currently opened screenlets."""
	DIR_USER = os.environ['HOME'] + '/.screenlets'
	DIR_USER1 = '/usr/share/screenlets'
	DIR_USER2 = '/usr/local/share/screenlets'	
	show_in_tray = 'True'
	def __init__ (self):
		# create bus, call super

		pixbuf = gtk.gdk.pixbuf_new_from_file("/usr/share/icons/screenlets.svg")

		session_bus = dbus.SessionBus()
		bus_name = dbus.service.BusName(SLD_BUS, bus=session_bus)
		dbus.service.Object.__init__(self, bus_name, SLD_PATH)
		# init properties
		self.running_screenlets = []
		self.menu = None
		# get list of currently open screenlets from system
		running = utils.list_running_screenlets()
		if running:
			self.running_screenlets = running
		try:
			ini = utils.IniReader()
			if ini.load(DIR_USER + '/config.ini'):
				self.show_in_tray = ini.get_option('show_in_tray', section='Options')
		except:
			self.show_in_tray = 'True'
		if self.show_in_tray == 'True':
			tray = gtk.StatusIcon()
			tray.set_from_pixbuf(pixbuf)
			tray.connect("activate", self.openit)
			tray.connect("popup-menu", self.show_menu)
			tray.set_tooltip("Screenlets daemon")
			tray.set_visible(True)		
			gtk.main()
	
	@dbus.service.method(SLD_IFACE)
	def get_running_screenlets (self):
		"""Get a list of all currently running screenlets."""
		return self.running_screenlets
	
	@dbus.service.method(SLD_IFACE)
	def register_screenlet (self, name):
		"""Register the screenlet with the given name as running."""
		self.running_screenlets.append(name)
		self.screenlet_registered(name)		# send signal
		print "ScreenletsDaemon: registered %s" % name
	
	@dbus.service.method(SLD_IFACE)
	def unregister_screenlet (self, name):
		"""Unregister the screenlet with the given name from the list."""
		if self.running_screenlets.count(name):
			self.running_screenlets.remove(name)
			self.screenlet_unregistered(name)		# send signal
			print "screenletsDaemon: unregistered %s" % name
	
	@dbus.service.signal(SLD_IFACE)
	def screenlet_registered (self, name):
		"""Send the 'register'-signal over DBus."""
		pass
	
	@dbus.service.signal(SLD_IFACE)
	def screenlet_unregistered (self, name):
		"""Send the 'unregister'-signal over DBus."""
		pass


	def show_menu(self, status_icon, button, activate_time):
		"""Create the menu and show it."""
		if self.menu is None:
			self.menu = gtk.Menu()
			
			# create top menuitems
			add_image_menuitem(self.menu, gtk.STOCK_PREFERENCES, _("Screenlets Manager"), self.openit)
			add_menuitem(self.menu, "-")
			add_image_menuitem(self.menu, gtk.STOCK_ADD, _("Install Screenlet"), self.installit)
			add_image_menuitem(self.menu, gtk.STOCK_NETWORK, _("Get more Screenlets"), self.getit)
			add_menuitem(self.menu, "-")
			
			# create the
			#launch menu 
			launch_menu = gtk.Menu()
			item = add_image_menuitem(self.menu, gtk.STOCK_EXECUTE, _("Launch Screenlet"))
			item.set_submenu(launch_menu)
			
			def set_item_image (self, item, name):
				img = utils.get_screenlet_icon(name,16,16)
				item.set_image_from_pixbuf(img)
				return False
			
			# populate the launch menu
			for path in screenlets.SCREENLETS_PATH:
				if os.path.exists(path) and os.path.isdir(path): #is it a valid folder?
					a = os.listdir(path)
					a.sort()
					for f in a:
						item = add_image_menuitem(launch_menu, gtk.STOCK_MISSING_IMAGE, f, self.launch, str(f))
						gobject.idle_add(set_item_image, self, item, f)
					add_menuitem(launch_menu, "-")
			
			# create the bottom menuitems
			add_image_menuitem(self.menu, gtk.STOCK_QUIT, _("Close all Screenlets"), self.closeit)
			add_image_menuitem(self.menu, gtk.STOCK_REFRESH, _("Restart all Screenlets"), self.restartit)
			add_image_menuitem(self.menu, gtk.STOCK_ABOUT, None, self.about)
			
			self.menu.show_all()
		
		# show the menu
		self.menu.popup(None, None, None, button, activate_time)

	def quit_screenlet_by_name (self, name):
		"""Quit all instances of the given screenlet type."""
		# get service for instance and call quit method
		service = screenlets.services.get_service_by_name(name)
		if service:
			service.quit()

	def restartit(self, widget):
		utils.restart_all_screenlets()

	def closeit(self, widget):
		utils.quit_all_screenlets()
				
	def installit(self, widget):
		self.show_install_dialog()



	def openit(self, widget):

		os.system('screenlets-manager &')
			

	
	def getit(self, widget):
		utils.xdg_open('http://screenlets.org/index.php/Category:UserScreenlets')

	def website_open(self, d, link, data):
		utils.xdg_open('http://screenlets.org')


	def about(self, widget):
		
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
		logo = gtk.gdk.pixbuf_new_from_file('/usr/share/icons/screenlets.svg')
		if logo:
			dlg.set_logo(logo)
		# run/destroy
		dlg.run()
		dlg.destroy()

	def launch(self, widget,screenlet):
		utils.launch_screenlet(screenlet)


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
		dlg.set_title((_('Install a Screenlet')))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			
			# try installing and show result dialog
			self.install (filename)	
			
		
		


	def create_user_dir (self):
		"""Create the userdir for the screenlets."""
		if not os.path.isdir(os.environ['HOME'] + '/.screenlets'):
			os.mkdir(os.environ['HOME'] + '/.screenlets')

	def install (self, filename):
		"""Install a screenlet from a given archive-file. Extracts the
		contents of the archive to the user's screenlet dir."""
		installer = install.ScreenletInstaller()
		result = installer.install(filename)
		if result:
			# reload screenlets to add new screenlet to iconview and show result
			screenlets.show_message(None, installer.get_result_message())
		else:
			screenlets.show_error(None, installer.get_result_message())

if __name__ == '__main__':
	# check for running daemon
	import os
	proc = os.popen("""ps axo "%p,%a" | grep "screenlets-daemon.py" | grep -v grep|cut -d',' -f1""").read()
	procs = proc.split('\n')
	if len(procs) > 2:
		print "daemon already started"
		import sys
		sys.exit(1)
	else:
		print "no daemon yet"


	
	# create new daemon
	daemon = ScreenletsDaemon()
	print 'ScreenletsDaemon running ...'
	# and start mainloop
	try:
		# start mainloop
		loop = gobject.MainLoop()
		loop.run()
	except KeyboardInterrupt:
		# notify when daemon is closed
		#service.notify('Screenlets-backend has been shut down .... ', 5000)
		print 'ScreenletsDaemon has been shut down ...'
	except Exception, ex:
		print "Exception in ScreenletsDaemon: %s" % ex


