# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# The services-module contains the ScreenletService-class and a set of utility
# functions to work with Screenlet-services from within other applications.
#
# (c) 2007 by RYX (Rico Pfaus)
#
# TODO: 
# - add missing default actions and signals (similar for all screenlets)
# - maybe abstract the dbus-related stuff and create subclasses which implement 
#   different communication methods? Later.
# - get_available_services() ... get list with names/ids of services
# 


import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib
import gettext

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)

# quick access to dbus decorator-method (to avoid importing dbus in screenlets
# and keep the possibility to create custom decorators in the future)
action = dbus.service.method
signal = dbus.service.signal


# service base-class
class ScreenletService (dbus.service.Object):
	"""The ScreenletService contains the boilerplate code for creating new
	dbus-objects for Screenlets. Subclasses can easily implement new functions 
	to allow controlling and managing Screenlets through DBus in any way 
	imaginable. This class should implement the default actions available for 
	all screenlets - add, delete, get, set, (move?)"""
	
	BUS 	= 'org.screenlets' #'org.freedesktop.Screenlets'
	PATH	= '/org/screenlets/' #'/org/freedesktop/Screenlets/'
	IFACE 	= 'org.screenlets.ScreenletService' #'org.freedesktop.ScreenletService'
	
	def __init__ (self, screenlet, name, id=None):
		# check types and vals
		if name == '':
			raise Exception(_('No name set in ScreenletService.__init__!'));
		# init props
		self.screenlet	= screenlet
		self.name		= name
		self.BUS		= self.BUS + '.' + name
		self.objpath	= self.PATH + name
		if id:
			self.objpath += '/' + id		# add id to path, if set
		# call super
		dbus.service.Object.__init__(self, dbus.service.BusName(self.BUS, 
			bus=dbus.SessionBus(), do_not_queue=True), self.objpath)
		
	@action(IFACE)
	def test (self):
		print "TEST: %s" % str(self.screenlet)

	@action(IFACE)
	def debug (self, string):
		"""Dump a string to the console."""
		print "DEBUG: " + string
	
	@action(IFACE)
	def add (self, id):
		"""Ask the assigned Screenlet to add a new instance of itself to 
		its session. The new Screenlet will have the ID defined by 'id'.
		The ID of the new instance is returned, so you can auto-generate an ID
		by passing an empty string. The function returns None if adding a 
		new instance failed for some reason."""
		sl = self.screenlet.session.create_instance(id)
		sl.finish_loading()
		if sl != None:
			return sl.id
		return False

	@action(IFACE)
	def get (self, id, attrib):
		"""Ask the assigned Screenlet to return the given attribute's value. If
		'id' is defined, the instance with the given id will be accessed, 
		else the main instance is used. Protected attributes are not returned
		by this function.
		TODO: Throw exception on error? ... could be abused to crash the app"""
		if id:
			sl = self.screenlet.session.get_instance_by_id(id)
			if not sl:
				sl = self.screenlet
			o = sl.get_option_by_name(attrib)
			if not o.protected:
				return getattr(sl, attrib)
			else:
				print _("Cannot get/set protected options through service.")
				return None
	
	@action(IFACE)
	def get_first_instance (self):
		"""Get the ID of the first existing instance of the assigned 
		Screenlet (within the screenlet's active session)."""
		if len(self.screenlet.session.instances):
			return self.screenlet.session.instances[0].id
		return None
	
	@action(IFACE)
	def list_instances (self):
		"""Return a list with IDs of all existing instances of the assigned 
		Screenlet (within the screenlet's active session)."""
		lst = []
		for sl in self.screenlet.session.instances:
			lst.append (sl.id)
		return lst
	
	@action(IFACE)
	def quit (self):
		"""Quit all instances of the screenlet. Similar to selecting Quit
		from the menu."""
		self.screenlet.destroy(self.screenlet.window)
	
	@action(IFACE)
	def set (self, id, attrib, value):
		"""Ask the assigned Screenlet to set the given attribute to 'value'. The 
		instance with the given id will be accessed. """
		sl = self.screenlet.session.get_instance_by_id(id)
		if sl == None:
			raise Exception(_('Trying to access invalid instance "%s".') % id)
		if sl.get_option_by_name(attrib) == None:
			raise Exception(_('Trying to access invalid option "%s".') % attrib)
		else:
			o = sl.get_option_by_name(attrib)
			if not o.protected:
				setattr(sl, attrib, value)
			else:
				print _("Cannot get/set protected options through service.")
	
	@signal(IFACE)
	def instance_added (self, id):
		"""This signal gets emitted whenever a new instance of the assigned 
		Screenlet gets added."""
	
	@signal(IFACE)
	def instance_removed (self, id):
		"""This signal gets emitted whenever an instance of the assigned
		Screenlet gets removed."""
	

def get_service_by_name (name, interface=ScreenletService.IFACE):
	"""This currently returns a dbus.Interface-object for remote-accessing the 
	ScreenletService through dbus, but that may change in the future to some 
	more abstracted system with support for multiple IPC-backends."""
	bus = dbus.SessionBus()
	if bus:
		try:
			path = ScreenletService.PATH + name
			proxy_obj = bus.get_object(ScreenletService.BUS + '.' + name, path)
			if proxy_obj:
				#return dbus.Interface(proxy_obj, ScreenletService.IFACE)
				return dbus.Interface(proxy_obj, interface)
		except Exception, ex:
			print _("Error in screenlets.services.get_service_by_name: %s") % str(ex)
	return None

def service_is_running (name):
	"""Checks if the given service is available (ie. the given Screenlet has at
	least one running instance) and returns True or False."""
	bus = dbus.SessionBus()
	if bus:
		try:
			path = ScreenletService.PATH + name
			if bus.get_object(ScreenletService.BUS + '.' + name, path):
				return True
		except Exception:
			pass
	return False

#print is_service_running('Flower')

