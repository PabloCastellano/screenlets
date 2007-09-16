# The screenlets.sensors module contains helper-functions to aid in
# creating CPU/RAM/*-meters and in retrieving general system information.

import sys
import re
import gobject
import gettext
from datetime import datetime
import commands

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)


# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------

# calculate cpu-usage by values from /proc/stat
# (written by Bernd Wurst, various modifications by RYX)
def get_cpu_load (processor_number=1, old_cuse = [0]):
	"""Calculates the system load."""
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
	#for line in tmp:
	line = tmp[processor_number]
	if line[0:5] == "cpu%i " % processor_number:
		reg = re.compile('[0-9]+')
		load_values = reg.findall(line)
		# extract values from /proc/stat
		cuse = int(load_values[0])
		csys = int(load_values[2])
		load = cuse + csys - old_cuse[0]
		#load = int(load / self.update_interval)
		old_cuse[0] = cuse + csys
	return load

# written by Hendrik Kaju
def get_freemem ():
	"""Get free memory."""
	cached = commands.getoutput("""cat /proc/meminfo | grep Cached | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	buffers = commands.getoutput("""cat /proc/meminfo | grep Buffers | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	free = commands.getoutput("""cat /proc/meminfo | grep MemFree | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	return int(cached.split()[0])/1024 + int(buffers)/1024 + int(free)/1024

# written by Hendrik Kaju
def get_usedmem ():
	"""Get used memory."""
	total = commands.getoutput("""cat /proc/meminfo | grep MemTotal | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	cached = commands.getoutput("""cat /proc/meminfo | grep Cached | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	buffers = commands.getoutput("""cat /proc/meminfo | grep Buffers | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	free = commands.getoutput("""cat /proc/meminfo | grep MemFree | awk 'BEGIN {FS=":"} {print $2}' | awk '{print $1, $9}'""")
	return int(total)/1024 - int(cached.split()[0])/1024 - \
		int(buffers)/1024 - int(free)/1024

# written by Helder Fraga aka whise
def get_drive_info (mount_point):
	"""Returns info about the given mount point (as dict)."""
	proc = subprocess.Popen('df -h -a -P | grep ^/dev/ ', shell='true', 
		stdout=subprocess.PIPE)
	sdevs = proc.stdout.read().rsplit('\n')
	sdevs.pop()
	for stdev in sdevs:
		sdev = re.findall("(\S*)\s*", stdev)
		dev = {
			'device': sdev[0],
			'size': sdev[1],
			'used': sdev[2],
			'free': sdev[3],
			'quota': sdev[4],
			'mount': sdev[5]
		}
		if dev['mount'] == mount_point:
			return dev
	return None

# written by Hendrik Kaju
def get_uptime ():
	"""Get uptime using 'cat /proc/uptime'"""
	data1 = commands.getoutput("cat /proc/uptime")
	uptime = float( data1.split()[0] )
	days = int( uptime / 60 / 60 / 24 )
	uptime = uptime - days * 60 * 60 * 24
	hours = int( uptime / 60 / 60 )
	uptime = uptime - hours * 60 * 60
	minutes = int( uptime / 60 )
	return str(days) + " days, " + str(hours) + " hours and " + str(minutes) + " minutes"

# written by Hendrik Kaju
def get_hostname ():
	"""Get user- and hostname and return user@hostname."""
	user = commands.getoutput("echo $USER")
	hostname = commands.getoutput("hostname")
	return user + "@" + hostname

# written by Hendrik Kaju
def get_average_load ():
	"""Get average load (as 3-tuple with floats)."""
	data = commands.getoutput("cat /proc/loadavg")
	load1 = float( data.split()[0] )
	load2 = float( data.split()[1] )
	load3 = float( data.split()[2] )
	return (load1, load2, load3)

# this one needs some more finetuning. It should return an array or info-object
# with separated info ...
#def get_distro_info ():
#		#"""Get user- and hostname and return user@hostname""" written by Helder Fraga aka Whise
#	distinf = commands.getoutput("lsb_release -a")
#	return distinf

# by whise
def get_kernel ():
	"""Returns output of uname -r."""
	return commands.getoutput("uname -r")

# by whise, modified by RYX
def get_net_activity (device):
	"""This will return the total download and upload this session. As 2-tuple
	with floats)."""
	data = commands.getoutput("cat /proc/net/dev")
	data = data[data.find(device + ":") + 5:]
	return (float(data.split()[0]), float(data.split()[8]))

# written by Patrik Kullman
def get_wireless_stats (interface):
	"""Returns wireless stats as dict."""
	stats = {}
	iwcfd = popen("iwconfig " + interface)
	iwconfig = iwcfd.read(1024)
	iwcfd.close()
	essid = iwconfig[iwconfig.find('ESSID:"')+7:]
	stats['essid'] = essid[:essid.find('"')]
	if stats['essid'].strip()[:stats['essid'].strip().find("  ")] == "unassociated":
		return {"essid": "Not connected", "percentage": 0}
	else:
		bitrate = iwconfig[iwconfig.find("Bit Rate:")+9:]
		stats['bitrate'] = bitrate[:bitrate.find(" ")]
		quality = iwconfig[iwconfig.find("Link Quality=")+13:]
		quality = quality[:quality.find(" ")]
		if quality.find("/") > 0:
			stats['quality'], stats['quality_max'] = quality.split("/")
		else:
			stats['quality'] = quality
		try:
			stats['percentage'] = int(float(stats['quality'])/float(stats['quality_max'])*100)
		except:
			return {"essid": "Not connected", "percentage": 0}
		signal = iwconfig[iwconfig.find("Signal level=")+13:]
		stats['signal'] = signal[:signal.find("  ")]
		noise = iwconfig[iwconfig.find("Noise level=")+12:]
		stats['noise'] = noise[:noise.find('\n')]
		return stats

# written by Helder Fraga aka Whise
# NOTE: This one also needs refinement - it should return a list instead of a string
def get_swap ():
	"""Get a list of swap partitions."""
	swap = commands.getoutput("cat /proc/swaps")
	swap = str(swap.split()[5:])
	swap = swap.replace("'","")
	swap = swap.replace("[","")
	swap = swap.replace("]","")
	swap = swap.replace(",","")
	return str(swap)

# by whise
def get_linux_version ():
	"""Get linux version string."""
	return commands.getoutput("cat /proc/version")

# by whise
# TODO: return dict and parse the output of cpuinfo (function does not much yet)
def get_cpu_info ():	
	"""Get cpu info from /proc/cpuinfo."""
	return commands.getoutput("cat /proc/cpuinfo")

# by whise	
def get_datetime ():
	"""Get datetime.now without the need for importing datetime module."""	
	return str(datetime.now())



# ------------------------------------------------------------------------------
# CLASSES
# ------------------------------------------------------------------------------

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
		causes the Sensor to be stopped.."""
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
	
	def __init__ (self, interval=1000, cpu=0):
		"""Create a new CPUSensor which emits an 'sensor_updated'-signal after a
		given interval (default is 1000ms). The multi-cpu support is untested
		but theoretically works :)."""
		Sensor.__init__(self, interval)
		self._load 	= 0
		self._cpu	= cpu
	
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
		line = tmp[self._cpu + 1]
		if line[0:5] == "cpu%i " % self._cpu:
			reg = re.compile('[0-9]+')
			load_values = reg.findall(line[5:])
			# extract values from /proc/stat
			cuse = int(load_values[0])
			csys = int(load_values[2])
			load = cuse + csys - old_cuse[0]
			if load < 0: load = 0
			if load > 99: load = 99
			self._load = load
			old_cuse[0] = cuse + csys
			# return True to emit the "update_event"-signal
			return True
		return False


class MemorySensor (Sensor):
	
	def __init__ (self, interval=1000):
		"""Create a new RAMSensor which emits an 'sensor_updated'-signal after a
		given interval (default is 1000ms)."""
		Sensor.__init__(self, interval)
		self._freemem 	= 0
		self._usedmem	= 0
	
	# + public functions
	
	def get_freemem (self):
		"""Return the amount of currently free RAM."""
		return self._freemem
	
	def get_usedmem (self):
		"""Return the amount of currently used RAM."""
		return self._usedmem
	
	# + internals
	
	def on_update (self):
		"""Called on each interval. Calculates the load and updates the
		internal values."""
		self._freemem = get_freemem()
		self._usedmem = get_usedmem()
		return True
	

class NetSensor (Sensor):
	
	def __init__ (self, interval=1000, device='eth0'):
		"""Create a new NetSensor which emits an 'sensor_updated'-signal after a
		given interval (default is 1000ms)."""
		Sensor.__init__(self, interval)
		self._device = device
		self._downloaded, self._uploaded	= get_net_activity(device)
		self._last_down, self._last_up		= self._downloaded, self._uploaded
		
	# + public functions
	
	def get_upload_speed (self):
		"""Return the current upload speed in b/s."""
		return self._uploaded - self._last_up
	
	def get_download_speed (self):
		"""Return the current download speed in b/s."""
		return self._downloaded - self._last_down
	
	def get_uploaded (self):
		"""Return the overall upload amount."""
		return self._uploaded
	
	def get_downloaded (self):
		"""Return the overall download amount."""
		return self._downloaded
	
	# + internals
	
	def on_update (self):
		"""Called on each interval. Calculates the load and updates the
		internal values."""
		d, u = get_net_activity(self._device)
		self._last_up		= self._uploaded
		self._last_down		= self._downloaded
		self._downloaded	= int(d)
		self._uploaded		= int(u)
		#print get_net_activity(self._device)
		return True


# TEST:
if __name__ == '__main__':
	
	# some tests
	print get_hostname()
	print get_net_activity('eth0')
	print get_linux_version()
	print get_kernel()
	print get_cpu_info()
	
	# callbacks which get notified about updates of sensor's values
	def handle_cpusensor_updated (cs):
		print 'CPU0: %i%%' % cs.get_load()
	def handle_ramsensor_updated (rs):
		print 'USED RAM: %i MB' % rs.get_usedmem()
		print 'FREE RAM: %i MB' % rs.get_freemem()
	def handle_netsensor_updated (ns):
		#print (ns.get_upload_speed(), ns.get_download_speed())
		print 'UP/DOWN: %i/%i bytes/s' % (ns.get_upload_speed(), 
			ns.get_download_speed())
	
	# create sensors and connect callbacks to them
	cpu = CPUSensor()
	cpu.connect('sensor_updated', handle_cpusensor_updated)
	ram = MemorySensor(5000)
	ram.connect('sensor_updated', handle_ramsensor_updated)
	net = NetSensor(1500, 'eth0')
	net.connect('sensor_updated', handle_netsensor_updated)
	
	# start mainloop
	mainloop = gobject.MainLoop()
	mainloop.run()

