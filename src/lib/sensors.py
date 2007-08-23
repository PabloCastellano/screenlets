# The screenlets.sensors module contains helper-functions to aid in
# creating CPU/RAM/*-meters 

import sys
import re
import gobject
import gettext

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)

# calculate cpu-usage by values from /proc/stat
# (written by Bernd Wurst)
def get_cpu_load (old_cuse = [0]):
	# Let's try if we can calc system load.
	try:
		f = open("/proc/stat", "r")
		tmp = f.readlines(200)
		f.close()
	except:
		print _("Failed to open /proc/stat")
		sys.exit(1)
	# 200 bytes should be enough because the information we 
	# need ist typically stored in the first line. Info about individual 
	# processors (not yet supported) is in the second (, ...?) line
	for line in tmp:
		if line[0:4] == "cpu ":
			reg = re.compile('[0-9]+')
			load_values = reg.findall(line)
			# extract values from /proc/stat
			cuse = int(load_values[0])
			csys = int(load_values[2])
			load = cuse + csys - old_cuse[0]
			#load = int(load / self.update_interval)
			old_cuse[0] = cuse + csys
	return load


# CLASSES

class Sensor (gobject.GObject):
	"""A base class for deriving new Sensor-types from."""
	
	# define custom signals
	__gsignals__ = dict( \
		sensor_updated	= (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
		sensor_stopped	= (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()) )
	
	def __init__ (self, interval=1000):
		"""Create a new sensor which updates after the given interval."""
		gobject.GObject.__init__(self)
		self._timeout_id	= None
		self._interval		= interval
		# start sensor timeout
		self.set_interval(interval)
	
	# + public functions
	
	def get_interval (self):
		"""Get the update-interval time for this Sensor."""
		return self._interval
	
	def set_interval (self, ms):
		"""Set the update-interval time for this Sensor and start it."""
		if self._timeout_id:
			gobject.source_remove(self._timeout_id)
		if ms and ms > 10:
			self._interval		= ms
			self._timeout_id	= gobject.timeout_add(ms, self.__timeout)
			return True
		return False
	
	def stop (self):
		"""Immediately stop this sensor and emit the "sensor_stopped"-signal."""
		self.set_interval(0)
		self.emit('sensor_stopped')
	
	# + handlers to be overridden in subclasses
	
	def on_update (self):
		"""Override this handler in subclasses to implement your calculations
		and update the Sensor's attributes. Must return True to emit a signal
		which can then be handled within the screenlets, returning False
		causes the Sensor to be stoped.."""
		return True
	
	# + internals
	
	def __timeout (self):
		"""The timeout function. Does nothing but calling the on_update
		handler and emitting a signal if the handler returned True."""
		# call sensor's on_update-handler
		if self.on_update():
			self.emit('sensor_updated')			
			return True
		# on_update returned False? Stop
		self.stop()
		return False
	

class CPUSensor (Sensor):
	"""A very simple CPU-sensor."""
	
	def __init__ (self, interval=1000):
		"""Create a new CPUSensor which emits an 'sensor_updated'-signal after a
		given interval (default is 1000ms)."""
		Sensor.__init__(self, interval)
		self._load = 0
	
	# + public functions
	
	def get_load (self):
		"""Return the current CPU-load."""
		return self._load
	
	# + internals
	
	def on_update (self, old_cuse=[0]):
		"""Called on each interval. Calculates the CPU-load and updates the
		internal load-value."""
		try:
			f = open("/proc/stat", "r")
			tmp = f.readlines(200)
			f.close()
		except:
			print _("CPUSensor: Failed to open /proc/stat. Sensor stopped.")
			self.stop()
		for line in tmp:
			if line[0:4] == "cpu ":
				reg = re.compile('[0-9]+')
				load_values = reg.findall(line)
				# extract values from /proc/stat
				cuse = int(load_values[0])
				csys = int(load_values[2])
				load = cuse + csys - old_cuse[0]
				if load < 0 : load=0
				if load > 100 :  load=100
				self._load = load
				old_cuse[0] = cuse + csys
				# return True to emit the "update_event"-signal
				return True
		return False


# TEST:
if __name__ == '__main__':
	
	# callback which gets notified about updates of sensor's value
	def handle_sensor_updated (cpusensor):
		print '%i%%' % cpusensor.get_load()
	
	# create sensor and connect callback to it
	cpu = CPUSensor()
	cpu.connect('sensor_updated', handle_sensor_updated)
	
	# start mainloop
	mainloop = gobject.MainLoop()
	mainloop.run()

