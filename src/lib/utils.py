#  screenlets.session (c) RYX (Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# The screenlets.utils module contains functions that are somehow needed
# by the Screenlet-class or parts of the framework, but don't necessarily
# have to be part of the Screenlet-class itself.
#
# TODO: move more functions here when possible
#

import screenlets
import dbus
import os
import sys
import stat
import gettext
import re

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)


# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------

def find_first_screenlet_path (screenlet_name):
	"""Scan the SCREENLETS_PATH for the first occurence of screenlet "name" and 
	return the full path to it. This function is used to get the theme/data 
	directories for a Screenlet."""
	for dir in screenlets.SCREENLETS_PATH:
		try:
			for name in os.listdir(dir):
				name_py = name + 'Screenlet.py'
				path = dir + '/' + name
				if not stat.S_ISDIR(os.stat(path).st_mode):
					continue
				# if path exists
				if os.access(path + '/' + name_py, os.F_OK):
					if name == screenlet_name:
						return path
				else:
					#print "utils.find_first_screenlet_path: "+\
					#	"LISTED PATH NOT EXISTS: " + path
					pass
		except OSError: # Raised by os.listdir: the directory doesn't exist
			pass
	# nothing found
	return None

def get_screenlet_metadata (screenlet_name):
	"""Returns a dict with name, info, author and version of the given
	screenlet. Use with care because it always imports the screenlet 
	module and shouldn't be used too often due to performance issues."""
	# find path to file
	path = find_first_screenlet_path(screenlet_name)
	classname = screenlet_name + 'Screenlet'
	# add path to PYTHONPATH
	if sys.path.count(path) == 0:
		sys.path.insert(0, path)
	try:
		slmod = __import__(classname)
		cls = getattr(slmod, classname)
		sys.path.remove(path)
		return {'name'	: cls.__name__, 
			'info'		: cls.__desc__, 
			'author'	: cls.__author__, 
			'version'	: cls.__version__
			}
	except Exception, ex:
		print _("Unable to load '%s' from %s: %s ") % (screenlet_name, path, ex)
		return None

def list_available_screenlets ():
	"""Scan the SCREENLETS_PATHs for all existing screenlets and return their
	names (without trailing "Screenlet") as a list of strings."""
	sls = []
	for dir in screenlets.SCREENLETS_PATH:
		try:
			for name in os.listdir(dir):
				path = dir + '/' + name
				# check if entry is a dir
				if not stat.S_ISDIR(os.stat(path).st_mode):
					continue
				# if path exists, add it to list
				if os.access(path + '/' + name + 'Screenlet.py', os.F_OK):
					if not sls.count(name):
						sls.append(name)
				else:
					print _("LISTED PATH NOT EXISTS: ") + path
		except OSError: # Raised by os.listdir: the directory doesn't exist
			pass
	return sls

import session
def list_running_screenlets ():
	"""Returns a list with names of running screenlets or None if no
	Screenlet is currently running. Function returns False if an error
	happened!"""
	tempfile = session.TMP_DIR + '/' + session.TMP_FILE
	if not os.path.isfile(tempfile):
		return None
	f = open(tempfile, 'r')
	if f:
		running = f.readlines()
		f.close()
		for i in xrange(len(running)):
			running[i] = running[i][:-1]	# strip trailing EOL
		return running
	return False

def _contains_path (string):
	"""Internal function: Returns true if the given string contains one of the
	SCREENLETS_PATH entries."""
	for p in screenlets.SCREENLETS_PATH:
		if string.find(p) > -1:
			return True
	return False

def list_running_screenlets2 ():
	"""Returns a list with names of running screenlets. The list can be empty if
	no Screenlet is currently running."""
	p = os.popen("ps aux | awk '/Screenlet.py/{ print $11, $12, $13, $14, $15, $16 }'")
	lst = []
	regex = re.compile('/([A-Za-z0-9]+)Screenlet.py ')
	for line in p.readlines():
		if not line.endswith('awk /Screenlet.py/{\n') and line != 'sh -c\n' \
			and _contains_path(line):
			slname = regex.findall(line)
			if slname and type(slname) == list and len(slname) > 0:
				lst.append(slname[0])
	p.close()
	return lst

def get_screenlet_process (name):
	"""Returns the PID of the given screenlet (if running) or None."""
	p = os.popen("ps aux | awk '/[" + name[0] + "]" + name[1:] + \
		"Screenlet.py/{ print $2, $11, $12, $13, $14, $15, $16 }'")
	line = p.readlines()
	p.close()
	#print line
	if len(line) and _contains_path(line[0]):
		return int(line[0].split(' ')[0])
	return None


# ------------------------------------------------------------------------------
# CLASSES
# ------------------------------------------------------------------------------

class IniReader:
	"""A simple config/ini-reader class. This is only used for reading the 
	theme.conf files yet, thus it only uses string-values.
	TODO: add writing-functions and let backend use this, too"""
	
	def __init__ (self):
		self.options	= []
		self.sections	= {}
	
	def list_options (self, section=''):
		"""Return all options (alternatively only from the given section)."""
		if section != '':
			return self.sections[section]
		else:
			return self.options
	
	def get_option (self, name, section=''):
		"""Get a variable from the config (optional: only get vars from the 
		specified section)."""
		if section != '':
			l = self.sections[section]
		else:
			l = self.options
		for o in l:
			if o[0] == name:
				return o[1]
		return None
	
	def has_section (self, name):
		"""Returns true if the given section exists."""
		return self.sections.has_key(name)
	
	def load (self, filename):
		"""Load a config/ini-file and save vars in internal list."""
		f=None
		try:
			f = open (filename, "r")
		except:
			print "File " + str(filename) + " not found"
		if f:
			section_name = ''
			for line in f.readlines():
				# strip whitespace/tabs on the left
				line = line.lstrip().lstrip('\t')
				#print line
				# ignore comment, EOL and too short lines
				if len(line) < 4 or line[0] in ("#", "\n", ";"):
					pass
				else:
					# split var/value and trim
					tmp = line.split('=', 1)
					# no '=' found? check for section name
					if len(tmp) < 2 and len(line) > 5 and line[0] == '[':
						section_name = line[:-1][1:-1]
						self.sections[section_name] =  []
						#print "Section found: %s" % section_name
					else:
						# two entries? split var/value
						var = tmp[0].rstrip().rstrip('\t')
						val = tmp[1][:-1].lstrip()	# remove EOL
						#print "VAR: %s=%s" % (var, val)
						# and add them to lists
						if var != '' and val != '':
							o = [var, val]
							self.options.append(o)
							if section_name != '':
								try:
									self.sections[section_name].append(o)
								except:
									print _("Section %s not found!") % section_name
			f.close()
			return True
		else:
			return False

class Notifier:
	"""A simple and conveniet wrapper for the notification-service. Allows
	screenlets to easily pop up notes with their own icon (if any)."""
	
	def __init__ (self, screenlet=None):
		self.bus = dbus.SessionBus()
		self.notifications = dbus.Interface(\
			self.bus.get_object('org.freedesktop.Notifications', 
			'/org/freedesktop/Notifications'), 'org.freedesktop.Notifications')
		self.screenlet = screenlet

	def notify (self, message, title='', icon='', timeout=-1, screenlet=None):
		"""Send a notification to org.freedesktop.Notifications. The message
		should contain the text you want to display, title may define a title
		(summary) for the message, icon can be the full path to an icon,
		timeout can be set to the desired displaying time in milliseconds."""
		if self.bus and self.notifications:
			if not screenlet:
				screenlet = self.screenlet
			if screenlet:
				p = find_first_screenlet_path(screenlet.__class__.__name__[:-9])
				if p:
					icon = p + '/icon.svg'
				title = screenlet.__name__
			self.notifications.Notify('Screenlets', 0, icon, title, message, 
				[], {}, timeout)
			return True
		else:
			print _("Notify: No DBus running or notifications-daemon unavailable.")
		return False


if __name__ == '__main__':
	
	# get info about screenlet
	print get_screenlet_metadata('Clock')
	
	# find first path
	print "Find first occurence of a Screenlet:"
	print find_first_screenlet_path('Clock')
	print find_first_screenlet_path('Orloj')
	print find_first_screenlet_path('Weather')
	print find_first_screenlet_path('Foo')
	
	# list available
	print "\nList all installed Screenlets:"
	avail = list_available_screenlets()
	avail.sort()
	print avail
	
	# IniReader
	print "\nTest INI-reader:"
	ini = IniReader()
	if not ini.load('/usr/local/share/screenlets/CPUMeter/themes/default/theme.conf'):
		print "Error while loading ini-file"
	else:
		# check for section
		if ini.has_section('Theme'):
			# get option-values from within a section
			print ini.get_option('name', section='Theme')
			print ini.get_option('info', section='Theme')
		# check for existence of a section
		if ini.has_section('Options'):
			for o in ini.list_options(section='Options'):
				print o[0]
	
	# notify
	print "\nNotify-test:"
	n = Notifier()
	n.notify('Hi there! This is sent through screenlets.utils.Notifier.notify', 
		title='Test')
	n.notify('A second note ..', title='Another note', timeout=2000)
	n.notify('A second note ..', title='Another note', icon='/usr/local/share/screenlets/Notes/icon.svg')
	
	# some tests of the list/find screenlets functions
	print "\nRunning screenlets: "
	print list_running_screenlets2()
	print "\n"
	print get_screenlet_process('Clock')
	print get_screenlet_process('Ruler')
	print get_screenlet_process('Webtest')

