#!/usr/bin/env python

# ScreenletsDaemon - (c) RYX (Rico Pfaus) 2007
#
# + INFO:
# This is a background daemon that keeps track of opened screenlets. The
# screenlets.session.ScreenletSession currently (ab)uses this as a workaround
# for the incomplete pyinotify-support in common distros.
#
# + TODO:
# - use a filewatch on '/tmp/screenlets/screenlets.running' instead of 
#   requring screenlets to register themselves with the daemon??
#
import gtk
import os
import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib
import gobject

import screenlets
from screenlets import utils
import gettext

gettext.textdomain('screenlets-manager')
gettext.bindtextdomain('screenlets-manager', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)

SLD_BUS		= 'org.screenlets.ScreenletsDaemon'
SLD_PATH	= '/org/screenlets/ScreenletsDaemon'
SLD_IFACE	= 'org.screenlets.ScreenletsDaemon'


class ScreenletsDaemon (dbus.service.Object):
	"""A simple backend class where screenlets register and unregister. It
	offers functions to keep track of currently opened screenlets."""
	DIR_USER = os.environ['HOME'] + '/.screenlets'
	DIR_USER1 = '/usr/share/screenlets'
	DIR_USER2 = '/usr/local/share/screenlets'	
	def __init__ (self):
		# create bus, call super
		pixbuf = gtk.gdk.pixbuf_new_from_file("/usr/share/icons/screenlets.svg")

		session_bus = dbus.SessionBus()
		bus_name = dbus.service.BusName(SLD_BUS, bus=session_bus)
		dbus.service.Object.__init__(self, bus_name, SLD_PATH)
		# init properties
		self.running_screenlets = []
		# get list of currently open screenlets from system
		running = utils.list_running_screenlets()
		if running:
			self.running_screenlets = running
		tray = gtk.StatusIcon()
		tray.set_from_pixbuf(pixbuf)
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
		print _("ScreenletsDaemon: registered %s") % name
	
	@dbus.service.method(SLD_IFACE)
	def unregister_screenlet (self, name):
		"""Unregister the screenlet with the given name from the list."""
		if self.running_screenlets.count(name):
			self.running_screenlets.remove(name)
			self.screenlet_unregistered(name)		# send signal
			print _("screenletsDaemon: unregistered %s") % name
	
	@dbus.service.signal(SLD_IFACE)
	def screenlet_registered (self, name):
		"""Send the 'register'-signal over DBus."""
		pass
	
	@dbus.service.signal(SLD_IFACE)
	def screenlet_unregistered (self, name):
		"""Send the 'unregister'-signal over DBus."""
		pass


	def show_menu(self, status_icon, button, activate_time):
		menu = gtk.Menu()
		menu1 = gtk.Menu()
		menu2 = gtk.Menu()
		menu3 = gtk.Menu()
		itemc = gtk.MenuItem("Screenlets Manager")
		itemc.connect("activate", self.openit)
		menu.append(itemc)
		sep = gtk.SeparatorMenuItem()
		menu.append(sep)
		item = gtk.MenuItem("Get more Screenlets")
		item.connect("activate", self.getit)
		menu.append(item)
		item = gtk.MenuItem("Install Screenlet")
		item.connect("activate", self.installit)
		menu.append(item)
		sep = gtk.SeparatorMenuItem()
		menu.append(sep)
		item0 = gtk.MenuItem("Launch Screenlet")


		if os.path.exists(self.DIR_USER) and os.path.isdir(self.DIR_USER): #is it a valid folder?
			a = os.listdir(self.DIR_USER)
			a.sort()
			for f in a:     
		
				item = gtk.MenuItem(str(f))
				item.connect("activate", self.launch,str(f))
		
				menu1.append(item)
		sep = gtk.SeparatorMenuItem()
		menu1.append(sep)
		if os.path.exists(self.DIR_USER1) and os.path.isdir(self.DIR_USER1): #is it a valid folder?
			a = os.listdir(self.DIR_USER1)
			a.sort()
			for f in a:       
		
				item = gtk.MenuItem(str(f))
				item.connect("activate", self.launch,str(f))
		
				menu1.append(item)
		sep = gtk.SeparatorMenuItem()
		menu1.append(sep)
		if os.path.exists(self.DIR_USER2) and os.path.isdir(self.DIR_USER2): #is it a valid folder?
			a = os.listdir(self.DIR_USER2)
			a.sort()
			for f in a:        
		
				item = gtk.MenuItem(str(f))
				item.connect("activate", self.launch,str(f))
	
				menu1.append(item)
		sep = gtk.SeparatorMenuItem()
		menu1.append(sep)
		item0.set_submenu(menu1)

		menu.append(item0)


		sep = gtk.SeparatorMenuItem()
		menu1.append(sep)
				
		itema = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
		itema.connect("activate", self.about)
		menu.append(itema)
		menu.show_all()
		menu.popup(None, None, None, button, activate_time)
	def openit(self, widget):
		try:
			os.system('screenlets-manager &')	
		except:
			pass
	
	def getit(self, widget):
		try:
			os.system('firefox http://screenlets.org/index.php/Category:UserScreenlets &')	
		except:
			pass
	def website_open(self, d, link, data):
		os.system('firefox http://screenlets.org &')

	def about(self, widget):
		
		"""Create/Show about dialog for this app."""
		dlg = gtk.AboutDialog()
		gtk.about_dialog_set_url_hook(self.website_open, None)
		# add baisc info
		dlg.set_name('Screenlets')
		dlg.set_comments(_('Screenlets Deamon system tray tool'))
		dlg.set_version('')
		dlg.set_copyright('(c) RYX (Rico Pfaus) and Whise (Helder Fraga) 2007')
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
	def launch(self, widget,screenlet):
		
		name = str(screenlet)
		if not screenlets.launch_screenlet(name):
			screenlets.show_error(self, 'Failed to add %sScreenlet.' % name)

	
	def installit (self, widget):

		self.show_install_dialog()

	

	

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
		dlg.set_title(('Install a Screenlet'))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			
			# try installing and show result dialog
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			self.install (filename)	
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
		
		


	def create_user_dir (self):
		"""Create the userdir for the screenlets."""
		if not os.path.isdir(os.environ['HOME'] + '/.screenlets'):
			os.mkdir(os.environ['HOME'] + '/.screenlets')
	def install (self, filename):
		"""Install a screenlet from a given archive-file. Extracts the
		contents of the archive to the user's screenlet dir."""
		print 'Installing %s' % filename
		result = False
		# TODO: set busy cursor
		# ...
		# get name of screenlet
		basename	= os.path.basename(filename)
		extension	= str(filename)[len(str(filename)) -3:]
#		name		= basename[:basename.find('.')]
		
		# check extension and create appropriate args for tar
		tar_opts = 'xfz'
	
		if extension == 'bz2':
			tar_opts = 'xvf'
		if extension == 'tar':
			tar_opts = 'xvf'

		# extract archive to temporary dir
		if not os.path.isdir('/tmp/screenlets/'):
			os.system('mkdir ' + '/tmp/screenlets/')
		
		tmpdir = '/tmp/screenlets' + '/install-temp/'
		os.system('mkdir %s' % tmpdir)
		
		
		os.system('tar %s %s -C %s' % (tar_opts, filename, tmpdir))
		for d in tmpdir : #for each item in folders
  			if os.path.exists(d) and os.path.isdir(d): #is it a valid folder?
				for f in os.listdir(tmpdir): 
					
					name = f
		try:
			print name
		except:
			screenlets.show_message(self,"Archive damaged or unsuported, only tar , bz2 or gz.")
		# verify contents
	
		if not os.path.isdir('%s/%s' % (tmpdir, name)):
			# dir missing
			
			screenlets.show_message(self,"Invalid archive. Archive must contain a directory with the screenlet's name.")
		elif not os.path.isfile('%s/%s/%sScreenlet.py' % (tmpdir, name, name)):
			# Screenlet.py missing
			screenlets.show_message(self,"Invalid archive. Archive does not contain a screenlet.")
		else:
			
			self.create_user_dir()
			os.system('tar %s %s -C %s' % (tar_opts, filename, os.environ['HOME'] + '/.screenlets'))
			# delete package info from target dir
			os.system('rm %s/%s/Screenlet.package' % (os.environ['HOME'] + '/.screenlets', name))
			# set msg/result
			screenlets.show_message(self,"The %sScreenlet has been succesfully installed." % name)
			result = True
		# remove temp contents
		os.system('rm -rf %s/install-temp' % '/tmp/screenlets/')
		
		self.add_default_menuitems()
		return result

if __name__ == '__main__':
	# check for running daemon
	"""import os
	proc = os.popen("ps axo \"%p,%a\" | grep \"screenlets-daemon.py\" | grep -v grep|cut -d',' -f1").read()
	procs = proc.split('\n')
	if len(procs) > 2:
		pid = int(procs[0].strip())
		os.kill(pid, 0)
	else:
		print "no daemon"
	import sys
	sys.exit(1)"""
	# create new daemon
	daemon = ScreenletsDaemon()
	print _('ScreenletsDaemon running ...')
	# and start mainloop
	try:
		# start mainloop
		loop = gobject.MainLoop()
		loop.run()
	except KeyboardInterrupt:
		# notify when daemon is closed
		#service.notify('Screenlets-backend has been shut down .... ', 5000)
		print _('ScreenletsDaemon has been shut down ...')
	except Exception, ex:
		print _("Exception in ScreenletsDaemon: %s") % ex


