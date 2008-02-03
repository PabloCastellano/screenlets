# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  screenlets.session (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# This module contains the ScreenletSession-class which handles the lower-level
# things like startup, multiple instances and sessions. It should also become
# the interface for load/save operations. The ScreenletSession is further
# responsible for handling command-line args to the Screenlet and should maybe
# offer some convenient way of setting Screenlet-options via commandline (so
# one can do "NotesScreenlet --theme_name=green --scale=0.5" and launch the
# Note with the given theme and scale)..
#
#
# INFO:
# - When a screenlet gets launched:
#   - the first instance of a screenlet creates the Session-object (within the
#     __main__-code)
#   - the session object investigates the config-dir for the given Screenlet
#     and restores available instances
#   - else (if no instance was found) it simply creates a new instance of the 
#     given screenlet and runs its mainloop
# - the --session argument allows setting the name of the session that will be
#   used by the Screenlet (to allow multiple configs for one Screenlet)
#
# TODO:
# - set attributes via commandline??
#

import os
import glob
import random
from xdg import BaseDirectory

import backend			# import screenlets.backend module
import services
import utils

import dbus	# TEMPORARY!! only needed for workaround

import gettext

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)


# temporary path for saving files for opened screenlets
TMP_DIR		= '/tmp/screenlets'
TMP_FILE	= 'screenlets.' + os.environ['USER'] + '.running'


class ScreenletSession (object):
	"""The ScreenletSession manages instances of a Screenlet and handles
	saving/restoring options. Each Screenlet contains a reference to its 
	session. Multiple instances of the same Screenlet share the same
	session-object."""
	
	# constructor
	def __init__ (self, screenlet_classobj, backend_type='caching', name='default'):
		object.__init__(self)
		# check type
		if not screenlet_classobj.__name__.endswith('Screenlet'):
			# TODO: also check for correct type (Screenlet-subclass)!!
			raise Exception(_("""ScreenletSession.__init__ has to be called with a
			 valid Screenlet-classobject as first argument!"""))
		# init props
		self.name 		= name
		self.screenlet 	= screenlet_classobj
		self.instances 	= []
		self.tempfile	= TMP_DIR + '/' + TMP_FILE
		# check sys.args for "--session"-argument and override name, if set
		self.__parse_commandline()
		# set session path (and create dir-tree if not existent)
		p = screenlet_classobj.__name__[:-9] + '/' + self.name + '/'
		self.path = BaseDirectory.load_first_config('Screenlets/' + p)
		if self.path == None:
			self.path = BaseDirectory.save_config_path('Screenlets/' + p)
		if self.path:
			if backend_type == 'caching':
				self.backend = backend.CachingBackend(path=self.path)
			elif backend_type == 'gconf':
				self.backend = backend.GconfBackend()	
		else:
			# no config-dir? use dummy-backend and note about problem
			self.backend = backend.ScreenletsBackend()
			print _("Unable to init backend - settings will not be saved!")
		# WORKAROUND: connect to daemon (ideally the daemon should watch the 
		#             tmpfile for changes!!)
		self.connect_daemon()
	
	def connect_daemon (self):
		"""Connect to org.screenlets.ScreenletsDaemon."""
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
				print _("Error in screenlets.session.connect_daemon: %s") % ex
	
	def create_instance (self, id=None, **keyword_args):
		"""Create a new instance with ID 'id' and add it to this session. The 
		function returns either the new Screenlet-instance or None."""
		print _("Creating new instance: ")
		# if id is none or already exists
		if id==None or id=='' or self.get_instance_by_id(id) != None:
			print _("ID is unset or already in use - creating new one!")
			id = self.__get_next_id()
			dirlst = glob.glob(self.path + '*')
			tdlen = len(self.path)
			for filename in dirlst:
				filename = filename[tdlen:]		# strip path from filename
				print _('File: %s') % filename
				if filename.endswith(id + '.ini'):
				# create new instance
					sl = self.create_instance(id=filename[:-4], enable_saving=False)
					if sl:
						# set options for the screenlet
						print _("Set options in %s") % sl.__name__
						#self.__restore_options_from_file (sl, self.path + filename)
						self.__restore_options_from_backend(sl, self.path+filename)
						sl.enable_saving(True)
						# and call init handler
						sl.finish_loading()
						return sl
		sl = self.screenlet(id=id, session=self, **keyword_args)
		if sl:
			self.instances.append(sl)		# add screenlet to session
			# and cause initial save to store INI-file in session dir
			sl.x = sl.x
			return sl
		return None
	
	def delete_instance (self, id):
		"""Delete the given instance with ID 'id' and remove its session file.
		When the last instance within the session is removed, the session dir 
		is completely removed."""
		sl = self.get_instance_by_id(id)
		if sl:
			# remove instance from session
			self.instances.remove(sl)
			# remove session file
			try:
				self.backend.delete_instance(id)
			except Exception:
				print _("Failed to remove INI-file for instance (not critical).")
			# if this was the last instance
			if len(self.instances) == 0:
				# maybe show confirmation popup?
				print _("Removing last instance from session")
				# TODO: remove whole session directory
				print _("TODO: remove self.path: %s") % self.path
				try:
					os.rmdir(self.path)
				except:
					print _("Failed to remove session dir '%s' - not empty?") % self.name
				# ...
				# quit gtk on closing screenlet
				sl.quit_on_close = True
			else:
				print _("Removing instance from session but staying alive")
				sl.quit_on_close = False
			# delete screenlet instance
			sl.close()
			del sl
			return True
		return False
	
	def get_instance_by_id (self, id):
		"""Return the instance with the given id from within this session."""
		for inst in self.instances:
			if inst.id == id:
				return inst
		return None

	def quit_instance (self, id):
		"""quit the given instance with ID 'id'"""
		
		sl = self.get_instance_by_id(id)
		if sl:
			print self.instances
			# remove instance from session


			if len(self.instances) == 1:
				sl.quit_on_close = True
			else:
				print _("Removing instance from session but staying alive")
				sl.quit_on_close = False
			self.backend.flush()
			sl.close()
			self.instances.remove(sl)
			print sl
			# remove session file
			return True
		return False

	
	def start (self):
		"""Start a new session (or restore an existing session) for the
		current Screenlet-class. Creates a new instance when none is found.
		Returns True if everything worked well, else False."""
		# check for a running instance first and use dbus-call to add
		# a new instance in that case
		#sln = self.screenlet.get_short_name()
		sln = self.screenlet.__name__[:-9]
		running = utils.list_running_screenlets()
		if running and running.count(self.screenlet.__name__) > 0:
		#if services.service_is_running(sln):
			print _("Found a running session of %s, adding new instance by service.") % sln
			srvc = services.get_service_by_name(sln)
			if srvc:
				print _("Adding new instance through: %s") % str(srvc)
				srvc.add('')
				return False
		# ok, we have a new session running - indicate that to the system
		self.__register_screenlet()
		# check for existing entries in the session with the given name
		print _("Loading instances in: %s") % self.path
		if self.__load_instances():
			# restored existing entries?
			print _("Restored instances from session '%s' ...") % self.name
			# call mainloop of first instance (starts application)
			#self.instances[0].main()
			self.__run_session(self.instances[0])
		else:
			# create new first instance
			print _('No instance(s) found in session-path, creating new one.')
			sl = self.screenlet(session=self, id=self.__get_next_id())
			if sl:
				# add screenlet to session
				self.instances.append(sl)
				# now cause a save of the options to initially create the
				# INI-file for this instance
				self.backend.save_option(sl.id, 'x', sl.x)
				# call on_init-handler
				sl.finish_loading()
				# call mainloop and give control to Screenlet
				#sl.main()
				self.__run_session(sl)
			else:
				print _('Failed creating instance of: %s') % self.classobj.__name__
				# remove us from the running screenlets
				self.__unregister_screenlet()
				return False
		# all went well
		return True
	
	def __register_screenlet (self):
		"""Create new entry for this session in the global TMP_FILE."""
		# if tempfile not exists, create it
		if not os.path.isfile(self.tempfile) and not self.__create_tempfile():
			print _('Error: Unable to create temp entry - screenlets-manager will not work properly.')
			return False
		# open temp file for appending data
		f = open(self.tempfile, 'a')
		if f:
			# if screenlet not already added
			running = utils.list_running_screenlets()
			if running.count(self.screenlet.__name__) == 0:
				print _("Creating new entry for %s in %s") % (self.screenlet.__name__, self.tempfile)
				f.write(self.screenlet.__name__ + '\n')
			f.close()
		# WORKAROUND: for now we manually add this to the daemon,
		#             ideally the daemon should watch the tmpdir for changes
		if self.daemon_iface:
			self.daemon_iface.register_screenlet(self.screenlet.__name__)
	
	def __create_tempfile (self):
		"""Create the global temporary file for saving screenlets. The file is 
		used for indicating which screnlets are currently running."""
		# check for existence of TMP_DIR and create it if missing
		if not os.path.isdir(TMP_DIR):
			print _("No global tempfile found, creating new one.")
			os.mkdir(TMP_DIR)
			if not os.path.isdir(TMP_DIR):
				print _('Error: Unable to create temp directory %s - screenlets-manager will not work properly.') % TMP_DIR
				return False
		else:
			# create entry in temp dir
			f = open(self.tempfile, 'w')
			f.close()
			return True
	
	def __unregister_screenlet (self, name=None):
		"""Delete this session's entry from the gloabl tempfile (and delete the
		entire file if no more running screenlets are set."""
		if not name:
			name = self.screenlet.__name__
		# WORKAROUND: for now we manually unregister from the daemon,
		#             ideally the daemon should watch the tmpfile for changes
		if self.daemon_iface:
			try:
				self.daemon_iface.unregister_screenlet(name)
			except Exception, ex:
				print _("Failed to unregister from daemon: %s") % ex
		# /WORKAROUND
		# get running screenlets
		running = utils.list_running_screenlets()
		if running and len(running) > 0:
			print _("Removing entry for %s from global tempfile %s") % (name, self.tempfile)
			try:
				running.remove(name)
			except:
				# not found, so ok
				print _("Entry not found. Will (obviously) not be removed.")
				return True
			# still running screenlets?
			if running and len(running) > 0:
				# re-save new list of running screenlets
				f = open(self.tempfile, 'w')
				if f:
					for r in running:
						f.write(r + '\n')
					f.close()
					return True
				else:
					print _("Error global tempfile not found. Some error before?")
				return False
			else:
				print _('No more screenlets running.')
				self.__delete_tempfile(name)
		else:
			print _('No screenlets running?')
			return False
	
	def __delete_tempfile (self, name=None):
		"""Delete the tempfile for this session."""
		if self.tempfile and os.path.isfile(self.tempfile):
			print _("Deleting global tempfile %s") % self.tempfile
			try:
				os.remove(self.tempfile)
				return True
			except:
				print _("Error: Failed to delete global tempfile")
				return False
	
	def __get_next_id (self):
		"""Get the next ID for an instance of the assigned Screenlet."""
		num = 1
		sln = self.screenlet.__name__[:-9]
		id = sln + str(num)
		while self.get_instance_by_id(id) != None:
			id = sln + str(num)
			num += 1
		return id
		
	def __load_instances (self):
		"""Check for existing instances in the current session, create them 
		and store them into self.instances if any are found. Returns True if 
		at least one instance was found, else False."""
		dirlst = glob.glob(self.path + '*')
		tdlen = len(self.path)
		for filename in dirlst:
			filename = filename[tdlen:]		# strip path from filename
			print _('File: %s') % filename
			if filename.endswith('.ini'):
				# create new instance
				sl = self.create_instance(id=filename[:-4], enable_saving=False)
				if sl:
					# set options for the screenlet
					print _("Set options in %s") % sl.__name__
					#self.__restore_options_from_file (sl, self.path + filename)
					self.__restore_options_from_backend(sl, self.path+filename)
					sl.enable_saving(True)
					# and call init handler
					sl.finish_loading()
				else:
					print _("Failed to create instance of '%s'!") % filename[:-4]
		# if instances were found, return True, else False
		if len(self.instances) > 0:
			return True
		return False
	
	# replacement for above function
	def __restore_options_from_backend (self, screenlet, filename):
		"""Restore and apply a screenlet's options from the backend."""
		# disable the canvas-updates in the screenlet
		screenlet.disable_updates = True
		# get options for SL from backend
		opts = self.backend.load_instance(screenlet.id)
		if opts:
			for o in opts:
				# get the attribute's Option-object from Screenlet
				opt = screenlet.get_option_by_name(o)
				# NOTE: set attribute in Screenlet by calling the
				# on_import-function for the Option (to import
				# the value as the required type)
				if opt:
					setattr(screenlet, opt.name, opt.on_import(opts[o]))
		# re-enable updates and call redraw/reshape
		screenlet.disable_updates = False
		screenlet.redraw_canvas()
		screenlet.update_shape()
	
	def __run_session (self, main_instance):
		"""Run the session by calling the main handler of the given Screenlet-
		instance. Handles sigkill (?) and keyboard interrupts."""
		# add sigkill-handler
		import signal
		def on_kill():
			print _("Screenlet has been killed. TODO: make this an event")
		signal.signal(signal.SIGTERM, on_kill)
		# set name of tempfile for later (else its missing after kill)
		tempfile = self.screenlet.__name__
		# start
		try:
			# start mainloop of screenlet
			main_instance.main()
		except KeyboardInterrupt:
			# notify when daemon is closed
			self.backend.flush()
			print _("Screenlet '%s' has been interrupted by keyboard. TODO: make this an event") % self.screenlet.__name__
		except Exception, ex:
			print _("Exception in ScreenletSession: ") + ex
		# finally delete the tempfile
		self.__unregister_screenlet(name=tempfile)
	
	def __parse_commandline (self):
		"""Check commandline args for "--session" argument and set session
		name if found. Runs only once during __init__.
		TODO: handle more arguments and maybe allow setting options by
		commandline"""
		import sys
		for arg in sys.argv[1:]:
			# name of session?
			if arg.startswith('--session=') and len(arg)>10:
				self.name = arg[10:]



def create_session (classobj, backend='caching', threading=False):
	"""A very simple utility-function to easily create/start a new session."""
	if threading:
		import gtk
		gtk.gdk.threads_init()
	session = ScreenletSession(classobj, backend_type=backend)
	session.start()

