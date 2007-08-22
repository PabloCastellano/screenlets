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
	
	def __init__ (self):
		# create bus, call super
		session_bus = dbus.SessionBus()
		bus_name = dbus.service.BusName(SLD_BUS, bus=session_bus)
		dbus.service.Object.__init__(self, bus_name, SLD_PATH)
		# init properties
		self.running_screenlets = []
		# get list of currently open screenlets from system
		running = utils.list_running_screenlets()
		if running:
			self.running_screenlets = running
	
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


