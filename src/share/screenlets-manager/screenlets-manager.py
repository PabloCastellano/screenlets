#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

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
from screenlets import utils
import gtk, gobject
from screenlets import utils
import dbus
import gettext
import subprocess
import commands
#a = commands.getoutput("ps -ef | grep 'screenlets-manager.py'" )
#b = a.find('/usr/share/screenlets-manager/screenlets-manager.py')
#if b != -1:
#	print b
#	exit()

gettext.textdomain('screenlets-manager')
gettext.bindtextdomain('screenlets-manager', '/usr/share/locale')


# stub for gettext
def _(s):
	#return s
	return gettext.gettext(s)


# name/version of this app
APP_NAME	= _('Screenlets Manager')
APP_VERSION	= '0.1'

# some constants
DIR_TMP			= '/tmp/screenlets/'
DEBUG_MODE		= True

# get executing user (root or normal) and set user-dependant constants
if os.geteuid()==0:
	# we run as root, install system-wide
	USER = 0
	DIR_USER		= screenlets.INSTALL_PREFIX + '/share/screenlets'
	DIR_AUTOSTART	= '/etc/xdg/autostart'			# TODO: use pyxdg here
else:
	# we run as normal user, install into $HOME
	USER = 1
	DIR_USER		= os.environ['HOME'] + '/.screenlets'
	


        desktop_environment = 'gnome'

        if os.environ.get('KDE_FULL_SESSION') == 'true':
            desktop_environment = 'kde'
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            desktop_environment = 'gnome'
        else:
            try:
		import commands
                info = commands.getoutput('xprop -root _DT_SAVE_MODE')
                if ' = "xfce4"' in info:
                    desktop_environment = 'xfce'
            except (OSError, RuntimeError):
                pass

        print _('It looks like you are running %s') % desktop_environment

	if desktop_environment == 'kde':
		DIR_AUTOSTART	= os.environ['HOME'] + '/.kde/Autostart/'
	elif desktop_environment == 'gnome':
		DIR_AUTOSTART	= os.environ['HOME'] + '/.config/autostart/'
	elif desktop_environment == 'xfce':
		DIR_AUTOSTART	= os.environ['HOME'] + '/.config/autostart/'

DIR_CONFIG = os.environ['HOME'] + '/.config/Screenlets'

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
	"""A simple utility to install screenlets into the current user's directory 
	(so either into $HOME/.screenlets/ for normal users or, if run as root, 
	into screenlets.INSTALL_PREFIX/share/screenlets/)."""
	
	def __init__ (self):
		self._message = ''
	
	def create_user_dir (self):
		"""Create the userdir for the screenlets."""
		if not os.path.isdir(DIR_USER):
			os.mkdir(DIR_USER)
	
	def get_info_from_package_name (self, filename):
		"""Return all info we can get from the package-name or return None
		if something went wrong. If nothing failed, the returned value is
		a 4-tuple of the form: (name, version, basename, extension)."""
		base	= os.path.basename(filename)
		ext		= str(filename)[len(str(filename)) -3:]
		# prepend "tar." if we have a bz2 or gz archive
		tar_opts = 'xfz'
		if ext == 'bz2':
			tar_opts = 'xfj'
		if ext == 'skz': 
			screenlets.show_error(None,_('This type of karamba theme is not supported yet\n Only older versions can be used'))
			return False
		# extract archive to temporary dir

		if not os.path.isdir('/tmp/screenlets/'):
			os.system('mkdir ' + '/tmp/screenlets/')
		try: os.system('rm -rf /tmp/screenlets/install-temp')
		except: pass		
		tmpdir = '/tmp/screenlets' + '/install-temp/'
		os.system('mkdir %s' % tmpdir)
		
		

		os.system('tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), tmpdir))
		for dd in os.listdir(tmpdir):
			if str(dd).endswith('.theme'):
				os.system('mv ' + tmpdir + ' ' + '/tmp/screenlets/' + dd[:-6])
				os.system('mkdir %s' % tmpdir)
				os.system('mv ' + '/tmp/screenlets/' + dd[:-6] + ' '+ tmpdir)
				name = dd[:-6]
				return (name, ext)

		for d in tmpdir : #for each item in folders
  			if os.path.exists(d) and os.path.isdir(d): #is it a valid folder?
				for f in os.listdir(tmpdir): 
					
					name = f
		try:
			print name
		except:
			screenlets.show_message(None, _("Archive is damaged or unsupported, use only tar, bz2 or gz."))
		return (name, ext)
	
	def get_result_message (self):
		"""Return a human-readable result message about the last operation."""
		return self._message
	
	def is_installed (self, name):
		"""Checks if the given screenlet with the name defined by 'name' 
		(without trailing 'Screenlet') is already installed in the current
		install target location."""
		return os.path.isdir(DIR_USER + '/' + name)
			
	def install (self, filename):
		"""Install a screenlet from a given archive-file. Extracts the
		contents of the archive to the user's screenlet dir."""
		print _('Installing %s') % filename
		result = False
		# get name of screenlet
		#basename	= os.path.basename(filename)
		#extension	= os.path.splitext(filename)
		#name		= basename[:basename.find('.')]
		#print name
		info = self.get_info_from_package_name(filename)
		name	= info[0]
		ext		= info[1]
		
		tar_opts = 'xfz'
		if ext == 'bz2':
			tar_opts = 'xfj'
			
			

		# check if screenlet is already installed
		#found_path = screenlets.utils.find_first_screenlet_path(name)
		if self.is_installed(name):#found_path != None:
			if screenlets.show_question(None,(_("The %sScreenlet is already installed in '%s'.\nDo you wish to continue?") % (name, DIR_USER)),(_('Install %s') % (name))):
				pass
			else:
				self._message= _('%sScreenlet is already installed') % (name)
				return False
		# check extension and create appropriate args for tar
		tmpdir = DIR_TMP + '/install-temp'
		# verify contents
		if not os.path.isdir('%s/%s' % (tmpdir, name)):
			# dir missing
			self._message = _("Invalid archive. Archive must contain a directory with the screenlet's name.")
		elif not os.path.isfile('%s/%s/%sScreenlet.py' % (tmpdir, name, name)):
			# Not a screenlet , lets check for karamba theme
			themename = ''
			for findtheme in os.listdir('%s/%s/' % (tmpdir, name)):
				if str(findtheme).lower().endswith('.theme'):
					print findtheme
					if themename == '':
						print tmpdir + '/'+ name + '/' + themename[:-6] + '.py'
						if not os.path.isfile(tmpdir + '/'+ name + '/' + findtheme[:-6] + '.py'):
							themename = findtheme[:-6]
						else:
							self._message = _("Compatibility for this karamba theme is not yet implemented")
							return False
			if themename != '':
				name1 = name.replace(' ','')
				name1 = name1.replace('-','')
				name1 = name1.replace('.','')
				name1 = name1.replace('_','')
				print name1
				#os.system('tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), DIR_USER))
				#os.system('mkdir %s/%s' % (DIR_USER,name1))
				if self.is_installed(name1):os.system('rm -rf %s/%s' % (DIR_USER, name1))
				
				os.system('mv %s/%s %s/%s ' % (chr(34) + tmpdir, name + chr(34),DIR_USER,name1))#tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), DIR_USER))
				os.system('mkdir %s/%s/themes' % (DIR_USER,name1))
				os.system('mkdir %s/%s/themes/default' % (DIR_USER,name1))
				os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/karamba.png ' + DIR_USER + '/' + name1 + '/themes/default/')
				if os.path.isfile(DIR_USER + '/' + name1 + '/icon.png') == False or os.path.isfile(DIR_USER + '/' + name1 + '/icon.svg') == False:
					os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/karamba.png ' + DIR_USER + '/' + name1 + '/icon.png')
				widgetengine = open(screenlets.INSTALL_PREFIX + '/share/screenlets-manager/KarambaScreenlet.py', 'r')
				enginecopy = widgetengine.read()
				widgetengine.close()
				widgetengine = None
				enginecopy = enginecopy.replace('KarambaScreenlet',name1 + 'Screenlet')

				enginesave = open(DIR_USER + '/' + name1 + '/' + name1 + 'Screenlet.py','w')
				enginesave.write(enginecopy)
				enginesave.close()
				self._message = _("Karamba theme was successfully installed")
				result = True	
			else:self._message = _("Invalid archive. Archive does not contain a screenlet or a valid karamba theme.")


			







		else:
			# check for package-info

			if not os.path.isfile('%s/%s/Screenlet.package' % (tmpdir, name)):
				if screenlets.show_question(None,(_("%s was not packaged with the screenlet packager. Do you wish to continue and try to install it?") % (name)),(_('Install %s') % (name))):
					pass
				else:
					self._message = _("This package was not packaged with the screenlet packager.")
					return False	
			
			# copy archive to user dir (and create if not exists)
			self.create_user_dir()
			os.system('tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), DIR_USER))
			# delete package info from target dir
			os.system('rm %s/%s/Screenlet.package' % (DIR_USER, name))
			# set msg/result
			self._message = _("The %sScreenlet has been succesfully installed.") % name
			result = True
		# remove temp contents
		os.system('rm -rf %s/install-temp' % DIR_TMP)
		# ready
		return result

# TEST:	
#inst = ScreenletInstaller()
#print inst.get_info_from_package_name('ClockScreenlet-0.3.2.tar.bz2')
#print inst.get_info_from_package_name('/home/ryx/tmp/ExampleScreenlet-0.3.zip')
#print inst.get_info_from_package_name('/somewhere/MyScreenlet-0.1.tar.gz')
#sys.exit(1)
# /TEST


class ScreenletsManager:
	"""The main application class."""
	
	daemon_iface = None
	
	def __init__ (self):
		# inti props

		if not os.path.isdir(DIR_CONFIG):
			os.system('mkdir %s' % DIR_CONFIG)
		if not os.path.isdir(DIR_USER):
			os.system('mkdir %s' % DIR_USER)	
		self.tips = gtk.Tooltips()
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
			self.lookup_daemon_autostart()
			self.lookup_daemon()
			self.connect_daemon()	
		
	# screenlets stuff

	def lookup_daemon_autostart (self):
		"""Adds Screenlets-daemon to autostart if not already"""
		if not os.path.isdir(DIR_AUTOSTART):
		# create autostart directory, if not existent
			if screenlets.show_question(None, _("There is no existing autostart directory for your user account yet. Do you want me to automatically create it for you?"), _('Error')):
				print _("Auto-create autostart dir ...")
				os.system('mkdir %s' % DIR_AUTOSTART)
				if not os.path.isdir(DIR_AUTOSTART):
					screenlets.show_error(None, _("Automatic creation failed. Please manually create the directory:\n%s") % DIR_AUTOSTART, _('Error'))
					return False
			else:
				screenlets.show_message(None, _("Please manually create the directory:\n%s") % DIR_AUTOSTART)
				return False
		starter = '%sScreenlets Daemon.desktop' % (DIR_AUTOSTART)

		if not os.path.isfile(starter) and os.path.isfile('%sscreenlets-daemon.desktop' % (DIR_AUTOSTART)) == False:
			print _("Create autostarter for: Screenlets Daemon")
			code = ['[Desktop Entry]']
			code.append('Encoding=UTF-8')
			code.append('Version=1.0')
			code.append('Name=Screenlets Daemon')
			code.append('Type=Application')
			code.append('Exec=%s/share/screenlets-manager/screenlets-daemon.py' % (screenlets.INSTALL_PREFIX))
			code.append('X-GNOME-Autostart-enabled=true')
			f = open(starter, 'w')
			if f:
				for l in code:
					f.write(l + '\n')
				f.close()
				return True
			print _('Failed to create autostarter for %s.') % name
			return False
		else:
			print _("Starter already exists.")
			return True
	

	
	def lookup_daemon (self):
		"""Find the screenlets-daemon or try to launch it. Initializes 
		self.daemon_iface if daemon is found."""
		self.daemon_iface = self.get_daemon_iface()
		# if daemon is not available, 
		if self.daemon_iface == None:
			# try to launch it 
			print _("Trying to launching screenlets-daemon ...")
			os.system(screenlets.INSTALL_PREFIX + \
				'/share/screenlets-manager/screenlets-daemon.py &')
			def daemon_check ():
				print _("checking for running daemon again ...")
				self.daemon_iface = self.get_daemon_iface()
				if self.daemon_iface:
					print _("DAEMON FOUND - Ending timeout")
					self.connect_daemon()
				else:
					print _("Error: Unable to connect/launch daemon.")
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
	
	def get_daemon_iface (self):
		"""Check if the daemon is already running and return its interface."""
		bus = dbus.SessionBus()
		if bus:
			try:
				bus_name	= 'org.screenlets.ScreenletsDaemon'
				path		= '/org/screenlets/ScreenletsDaemon'
				iface		= 'org.screenlets.ScreenletsDaemon'
				proxy_obj = bus.get_object(bus_name, path)
				if proxy_obj:
					return dbus.Interface(proxy_obj, iface)
			except Exception, ex:
				print _("Error in ScreenletsManager.connect_daemon: %s") % ex
		return None

	def __get_user_dir(self, key, default):
		"""http://www.freedesktop.org/wiki/Software/xdg-user-dirs"""

		user_dirs_dirs = os.path.expanduser("~/.config/user-dirs.dirs")
		if os.path.exists(user_dirs_dirs):
			f = open(user_dirs_dirs, "r")
			for line in f.readlines():
				if line.startswith(key):
					return os.path.expandvars(line[len(key)+2:-2])
 		return default	

	def get_desktop_dir(self):
		"""Returns desktop dir"""
		self.__desktop_dir =  self.__get_user_dir("XDG_DESKTOP_DIR", os.path.expanduser("~/Desktop"))
		return self.__desktop_dir

	def create_autostarter (self, name):
		"""Create a .desktop-file for the screenlet with the given name in 
		$HOME/.config/autostart."""
		if not os.path.isdir(DIR_AUTOSTART):
			# create autostart directory, if not existent
			if screenlets.show_question(None, 
				_("There is no existing autostart directory for your user account yet. Do you want me to automatically create it for you?"), 
				_('Error')):
				print _("Auto-create autostart dir ...")
				os.system('mkdir %s' % DIR_AUTOSTART)
				if not os.path.isdir(DIR_AUTOSTART):
					screenlets.show_error(None, _("Automatic creation failed. Please manually create the directory:\n%s") % DIR_AUTOSTART, _('Error'))
					return False
			else:
				screenlets.show_message(None, _("Please manually create the directory:\n%s") % DIR_AUTOSTART)
				return False
		if name.endswith('Screenlet'):
			name = name[:-9]
		starter = '%s%sScreenlet.desktop' % (DIR_AUTOSTART, name)

		for f in os.listdir(DIR_AUTOSTART):
			a = f.find(name + 'Screenlet')
			if a != -1:
				print str(f) + ' duplicate entry'
				os.system('rm %s%s' % (chr(34)+DIR_AUTOSTART,f+chr(34)))
				print _('Removed duplicate entry')
		if not os.path.isfile(starter) and not os.path.exists(os.environ['HOME'] + '/.config/autostart/CalendarScreenlet'):
			path = utils.find_first_screenlet_path(name)
			if path:
				print _("Create autostarter for: %s/%sScreenlet.py") % (path, name)
				code = ['[Desktop Entry]']
				code.append('Name=%sScreenlet' % name)
				code.append('Encoding=UTF-8')
				code.append('Version=1.0')
				code.append('Type=Application')
				code.append('Exec= python -u %s/%sScreenlet.py' % (path, name))
				code.append('X-GNOME-Autostart-enabled=true')
				#print code
				f = open(starter, 'w')
				if f:
					for l in code:
						f.write(l + '\n')
					f.close()
					return True
				print _('Failed to create autostarter for %s.') % name
				return False
		else:
			print _("Starter already exists.")
			return True
	
	def delete_autostarter (self, name):
		"""Delete the autostart for the given screenlet."""
		if name.endswith('Screenlet'):
			name = name[:-9]
		print _('Delete autostarter for %s.') % name
		os.system('rm %s%sScreenlet.desktop' % (DIR_AUTOSTART, name))
		for f in os.listdir(DIR_AUTOSTART):
			a = f.find(name + 'Screenlet')
			if a != -1:
				print str(f) + ' duplicate entry'
				os.system('rm %s%s' % (chr(34)+DIR_AUTOSTART,f+chr(34)))
				print _('Removed duplicate entry')
	
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
						if screenlets.show_question(None, _('Do you also want to remove the Screenlet configuration files?')):
							os.system('rm -rf %s/%s' % (DIR_CONFIG, info.name))
							os.system('rm -rf %s/%sScreenlet.log' % (DIR_CONFIG, info.name))
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
		for s in lst_a:
			#path = screenlets.SCREENLETS_PATH[0] + '/' + s + '/icon.svg'
			#print path
			# not really beautiful, but it works .. (maybe make a function)
			p = screenlets.SCREENLETS_PATH
			icon_svg = '/' + s + '/icon.svg'
			icon_png = '/' + s + '/icon.png'
			if os.path.isfile(p[0] + icon_svg):
				path = p[0] + icon_svg
			elif os.path.isfile(p[0] + icon_png):
				path = p[0] + icon_png
			elif os.path.isfile(p[1] + icon_svg):
				path = p[1] + icon_svg
			elif os.path.isfile(p[1] +icon_png):
				path = p[1] + icon_png
			else:
				img = noimg	
			try:
				img = gtk.gdk.pixbuf_new_from_file_at_size(path, 56, 56)
				path = ''
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
				slinfo = ScreenletInfo(s, name, info, author, version, img)
				# check if already running
				if lst_r.count(s + 'Screenlet'):
					slinfo.active = True
				# check if system-wide
				#if path.startswith(screenlets.INSTALL_PREFIX):
				#	print "SYSTEM: %s" % s
				#	info.system = True
			else:
				print _('Error while loading screenlets metadata for "%s".' % s)
				slinfo = ScreenletInfo(s, '', '', '', '', img)
			# add to model
			ccc = self.combo.get_active()
			if ccc == 0:
				
				sss = str(self.txtsearch.get_text()).lower()
				slname = str(s).lower()
				a = slname.find(sss)
				if sss == None or a != -1:
					self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])	
					#self.txtsearch.get_text('')
			elif ccc == 1:
				
				sss = str(self.txtsearch.get_text()).lower()
				slname = str(s).lower()
				a = slname.find(sss)
				

				if sss == None or a != -1:
					a = utils.list_running_screenlets()
					b = s + 'Screenlet'

					if b in a :self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])	
			elif ccc == 2:
				
				sss = str(self.txtsearch.get_text()).lower()
				slname = str(s).lower()
				a = slname.find(sss)
				

				if sss == None or a != -1:
					a = utils.list_running_screenlets()
					b = s + 'Screenlet'

					if slinfo.autostart == True :self.model.append(['<span size="9000">%s</span>' % s, img, slinfo])	
					#self.txtsearch.get_text('')info.autostart
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
	
	def reset_selected_screenlet(self):
		sel = self.view.get_selected_items()
		if sel and len(sel) > 0 and len(sel[0]) > 0:
			it = self.model.get_iter(sel[0][0])
			if it:
				info = self.model.get_value(it, 2)
				if screenlets.show_question(None, _('Do you really want to reset the %sScreenlet configuration?' % info.name), _('Reset Screenlet')):
					# delete screenlet's config directory 
					os.system('rm -rf %s/%s' % (DIR_CONFIG, info.name))
					# remove entry from model
					
				
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
  		if USER == 0:	# add note about "root-mode"
			w.set_title(APP_NAME + ' (root mode)')
		else:
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
		self.tips.set_tip(but1, _('Launch/add a new instance of the selected Screenlet ...'))
		self.tips.set_tip(but2, _('Install a new Screenlet, SuperKaramba or Web Widget or Web Application  ...'))
		self.tips.set_tip(but3, _('Permanently uninstall/delete the currently selected Screenlet ...'))
		self.tips.set_tip(but4, _('Reset this Screenlet configuration (will only work if screenlet isnt running)'))
		self.tips.set_tip(but5, _('Install new theme for this screenlet'))
		self.tips.set_tip(but6, _('Restart all screenlets that have auto start at login'))
		self.tips.set_tip(but7, _('Close all Screenlets running'))
		self.tips.set_tip(but8, _('New Screenlets Options/Properties'))						
		self.tips.set_tip(but9, _('Create a Desktop shortcut for this Screenlet'))
		self.label = gtk.Label('')
		self.label.set_line_wrap(1)
		self.label.set_width_chars(70)
		self.label.set_alignment(0, 0)
		self.label.set_size_request(-1, 65)
    		self.btnsearch = gtk.Button("")
    		self.searchbox = gtk.HBox()
    		self.txtsearch = gtk.Entry()
		self.btnsearch.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND, 
			gtk.ICON_SIZE_BUTTON))
    		self.btnsearch.connect("clicked",self.redraw_screenlets, 'enter')
    		self.txtsearch.connect("changed",self.redraw_screenlets, 'enter')
    		self.txtsearch.connect("backspace",self.redraw_screenlets, 'backspace')

    		self.searchbox.pack_start(self.txtsearch, False)
    		self.searchbox.pack_start(self.btnsearch, False)
		butbox.pack_start(self.searchbox, False,0,3)
		self.combo = gtk.combo_box_new_text()
		self.combo.append_text(_('All Screenlets'))
		self.combo.append_text(_('Running Screenlets'))
		self.combo.append_text(_('Autostart Screenlets'))
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
		but_download = gtk.Button('Get more screenlets')
		but_download.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_DOWN, 
			gtk.ICON_SIZE_BUTTON))
		but_about.connect('clicked', self.button_clicked, 'about')
		but_close.connect('clicked', self.button_clicked, 'close')
		but_download.connect('clicked', self.button_clicked, 'download')
		self.tips.set_tip(but_about, _('Show info about this dialog ...'))
		self.tips.set_tip(but_download, _('Download more screenlets ...'))
		self.tips.set_tip(but_close, _('Close this dialog ...'))
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
			f.write("Keep_above=True\n")
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
			f.write("Keep_above=True\n")
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
				self.model.clear()
				self.load_screenlets()
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
		logo = gtk.gdk.pixbuf_new_from_file('/usr/share/icons/screenlets.svg')
		if logo:
			dlg.set_logo(logo)
		# run/destroy
		dlg.run()
		dlg.destroy()
		
	def website_open(self, d, link, data):
		subprocess.Popen(["xdg-open", "http://www.screenlets.org"])

	def drag_data_received (self, widget, dc, x, y, sel_data, info, timestamp):
			
		print _("Data dropped ...")
		filename = ''
		# get text-elements in selection data
		txt = sel_data.get_text()
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
			installer = ScreenletInstaller()
			if not self.containsAny(filename,'%'):
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
				print _('Please install screenlets from folders without strange characters')
	def containsAll(self,str, set):
		for c in set:
			if c not in str: return 0;
		return 1;
	def containsAny(self,str, set):
		"""Check whether 'str' contains ANY of the chars in 'set'"""
		return 1 in [c in str for c in set]

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
			installer = ScreenletInstaller()
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
			print _('Installing %s') % filename
			result = False
			info = self.get_selection()
			basename	= os.path.basename(filename)
			ext	= str(filename)[len(str(filename)) -3:]
	
			tar_opts = 'xfz'
			if ext == 'bz2':
				tar_opts = 'xfj'
			x = 0
			y = 0
			
			if not info.system:
				install_dir = DIR_USER + '/' 
				themes_dir = DIR_USER + '/' + info.name + '/themes/'
				install_prefix = ''
			else:
				if not screenlets.show_question(None, _("You are about to install a theme in root mode. Continue only if you have gksudo installed, do you wish to continue?")):
					self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))	
					result = False
				themes_dir = screenlets.INSTALL_PREFIX + '/share/screenlets' + '/'  + info.name + '/themes/'
				install_dir = screenlets.INSTALL_PREFIX + '/share/screenlets' + '/' 
				install_prefix = 'gksudo '

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
				print _("list contains themes folder")
			elif os.listdir(tmpdir)[0] == info.name:
				print _("list contains the screenlet name folder")
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
				print _("only contains the themes folders")
						
			os.system('rm -rf %s/install-temp' % DIR_TMP)

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
				screenlets.launch_screenlet(info.name, debug=DEBUG_MODE)
				
		elif id == 'install':
			install_combo = gtk.combo_box_new_text()

			#go_button = gtk.Button('Install')
			install_combo.append_text('Install Screenlet')
			install_combo.append_text('Install SuperKaramba Theme')
			install_combo.append_text('Convert Web Widget')
			install_combo.append_text('Install Web Application')
			install_combo.set_active(0)
       			dialog = gtk.Dialog("Install",self.window,
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
		elif id == 'uninstall':
			self.delete_selected_screenlet()
		elif id == 'reset':
			self.reset_selected_screenlet()
		elif id == 'theme':
			self.show_install_theme_dialog()
		elif id == 'prop':
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
		elif id == 'desktop_shortcut':
			info = self.get_selection()
			name = info.name
			path = utils.find_first_screenlet_path(name)
			desk = self.get_desktop_dir()
			if name.endswith('Screenlet'):
				name = name[:-9]
			starter = '%s/%sScreenlet.desktop' % (desk, name)
			if path:
				print _("Create desktop shortcut for: %s/%sScreenlet.py") % (path, name)
				code = ['[Desktop Entry]']
				code.append('Name=%sScreenlet' % name)
				code.append('Encoding=UTF-8')
				code.append('Version=1.0')
				if os.path.exists('%s/icon.svg' % path):
					code.append('Icon=%s/icon.svg' % path)
				elif os.path.exists('%s/icon.png' % path):
					code.append('Icon=%s/icon.png' % path)
				code.append('Type=Application')
				code.append('Exec= python -u %s/%sScreenlet.py' % (path, name))
				code.append('X-GNOME-Autostart-enabled=true')
				#print code
				f = open(starter, 'w')
				if f:
					for l in code:
						f.write(l + '\n')
					f.close()
					
					return True
				print _('Failed to create autostarter for %s.') % name
				return False
		elif id == 'restartall':
			a = utils.list_running_screenlets()
			if a != None:
				for s in a:
					print _('closing %s') % str(s)
					if s.endswith('Screenlet'):
						s = s[:-9]
						try:
							self.quit_screenlet_by_name(s)
						except:
							pass
			for s in os.listdir(DIR_AUTOSTART):
		
				if s.lower().endswith('screenlet.desktop'):
					#s = s[:-17]
					os.system('sh '+ DIR_AUTOSTART + s + ' &')	
		elif id == 'closeall':
			a = utils.list_running_screenlets()
			if a != None:
				for s in a:
					print 'closing' + str(s)
					if s.endswith('Screenlet'):
						s = s[:-9]
						try:
							self.quit_screenlet_by_name(s)
						except:
							pass
		elif id == 'website':
			print "TODO: open website"

		elif id == 'download':
			subprocess.Popen(["xdg-open", screenlets.THIRD_PARTY_DOWNLOAD])
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
						os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/prefs.js ' +DIR_USER + '/' + a + '/mozilla')			
		
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
							os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/prefs.js ' +DIR_USER + '/' + a + '/mozilla')			

		
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
				print _("Launch %s") % info.name
				screenlets.launch_screenlet(info.name, debug=DEBUG_MODE)
				
			else:
				# quit screenlet
				self.quit_screenlet_by_name(info.name)
				print _("Quit %s") % info.name
				self.model.clear()
				self.load_screenlets()

	def toggle_autostart (self, widget):
		"""Callback for handling changes to the Autostart-CheckButton."""
		info = self.get_selection()
		if info:
			info.autostart = not info.autostart
			if info.autostart:
				if not self.create_autostarter(info.name):
					widget.set_active(False)
					widget.set_sensitive(False)
			else:
				self.delete_autostarter(info.name)

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
		print _("Quit!")
	
	# start the app
	
	def start (self):
		gtk.main()
		

app = ScreenletsManager()
app.start()
