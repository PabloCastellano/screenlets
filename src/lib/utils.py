# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

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
import urllib
gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')
import gobject
try:
	import gnomevfs
except:
	pass
def _(s):
	return gettext.gettext(s)


# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------

def create_user_dir ():
	"""Create the userdir for the screenlets."""
	if not os.path.isdir(os.environ['HOME'] + '/.screenlets'):
		try:
			os.mkdir(os.environ['HOME'] + '/.screenlets')
		except:
			print 'coulnt create user dir'

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


def get_GMail_Num(login, password):
	"""This output the number of messages of gmail box"""

	f = os.popen("wget --no-check-certificate -qO - https://" + login + ":" + password + "@mail.google.com/mail/feed/atom")
	a = f.read()
	f.close()
	match = re.search("<fullcount>([0-9]+)</fullcount>", a)
	if match == None:
		return None
	else:
		return match.group(1)



def get_Mail_Num(server, login, passwd):
	"""This output the number of messages of mail box"""
	try:
		import poplib
	except ImportError, err:
		print " !!!Please install python poplib :", err
	    	return None
	m = poplib.POP3(server)
	m.user(login)
	m.pass_(passwd)
	out = m.stat()
	m.quit()
	num = out[0]
	return num

def get_evolution_contacts():
	"""Returns a list of evolution contacts"""
	contacts = []

	try:
		import evolution
	except ImportError, err:
		print " !!!Please install python evolution bindings Unable to import evolution bindings:", err
	    	return None

	try:
		if evolution:
			for book_id in evolution.ebook.list_addressbooks():
				book = evolution.ebook.open_addressbook(book_id[1])
				if book:
					for contact in book.get_all_contacts():
					
						contacts.append(contact)
	except:
		if evolution:
			for book_id in evolution.list_addressbooks():
				book = evolution.open_addressbook(book_id[1])
				if book:
					for contact in book.get_all_contacts():
						
						contacts.append(contact)
                            
        return contacts

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

def get_user_dir(key, default):
	"""http://www.freedesktop.org/wiki/Software/xdg-user-dirs"""

	user_dirs_dirs = os.path.expanduser("~/.config/user-dirs.dirs")
	if os.path.exists(user_dirs_dirs):
		f = open(user_dirs_dirs, "r")
		for line in f.readlines():
			if line.startswith(key):
				return os.path.expandvars(line[len(key)+2:-2])
	return default	

def get_desktop_dir():
	"""Returns desktop dir"""
	desktop_dir =  get_user_dir("XDG_DESKTOP_DIR", os.path.expanduser("~/Desktop"))
	desktop_dir = urllib.unquote(desktop_dir)
	return desktop_dir

def get_filename_on_drop(sel_data):
	filename = ''
	filenames = []
	# get text-elements in selection data
	try:
		txt = unicode.encode(sel_data.get_text(), 'utf-8')
	except:
		txt = sel_data.get_text()
	txta = urllib.unquote(txt)
	txta = str(txta).split('\n')
		
	for txt in txta:
		if txt and txt != '':
			# if it is a filename, use it
			if txt.startswith('file://'):
				filename = txt[7:]
			else:
				print 'Invalid string: %s.' % txt
		else:
			# else get uri-part of selection
			uris = sel_data.get_uris()
			if uris and len(uris)>0:
				#print "URIS: "+str(uris	)
				filename = uris[0][7:]
		if filename != '':
			filenames.append(chr(34) +filename + chr(34))

	return filenames

def LoadPlaces():
	"""Returns mount points in media"""
	mountlist = os.popen('mount -l').read()
	prog = re.compile("^/dev/.*?\son\s/media/(.*?) .*?(\[(.*?)\])?$", re.MULTILINE)
	return prog.findall(mountlist)

def LoadBookmarks():
	"""Returns gtk bookmarks """
	_bookmarks_path = os.path.expanduser("~/.gtk-bookmarks")
	_places = []
	try:
		for line in file(_bookmarks_path):
			line = line.strip()

			if " " in line:
				uri, name = line.split(" ", 1)
				
			else:
				uri = line
				
				path = urllib.splittype(uri)[1]
				name = urllib.unquote(os.path.split(path)[1])

			try:
				if os.path.exists(uri):
					continue
                # Protect against a broken bookmarks file
			except TypeError:
				continue

			_places.append((uri, name))
		return _places
        except IOError, err:
            print "Error loading GTK bookmarks:", err

def readMountFile( filename):
	fstab = []
	f = open(filename, 'r')
	for line in f:
		if (not line.isspace() and not line.startswith('#') and not line.lower().startswith('none')) :
			fstabline = line.split()
			if fstabline[1] != 'none' and fstabline[1] != '/proc': fstab.append(fstabline[1])
	
	fstab.sort()
	return fstab

def read_file( filename):

	f = open(filename, 'r')
	t = f.read()
	f.close()
	return t


def strip_html(string):
    return re.sub(r"<.*?>|</.*?>","",string)

# ------------------------------------------------------------------------------
# CLASSES
# ------------------------------------------------------------------------------

class FileMonitor(gobject.GObject):
	'''
	A simple wrapper around Gnome VFS file monitors.  Emits created, deleted,
	and changed events.  Incoming events are queued, with the latest event
	cancelling prior undelivered events.
	'''
	
	
	__gsignals__ = {
		"event" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, gobject.TYPE_INT)),
		"created" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
		"deleted" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
	}

	def __init__(self, path):
		gobject.GObject.__init__(self)
		
		if os.path.isabs(path):
			self.path = "file://" + path
		else:
			self.path = path
		try:
			self.type = gnomevfs.get_file_info(path).type
		except gnomevfs.Error:
			self.type = gnomevfs.MONITOR_FILE

		self.monitor = None
		self.pending_timeouts = {}

	def open(self):
		if not self.monitor:
			if self.type == gnomevfs.FILE_TYPE_DIRECTORY:
				monitor_type = gnomevfs.MONITOR_DIRECTORY
			else:
				monitor_type = gnomevfs.MONITOR_FILE
			self.monitor = gnomevfs.monitor_add(self.path, monitor_type, self._queue_event)

	def _clear_timeout(self, info_uri):
		try:
			gobject.source_remove(self.pending_timeouts[info_uri])
			del self.pending_timeouts[info_uri]
		except KeyError:
			pass

	def _queue_event(self, monitor_uri, info_uri, event):
		self._clear_timeout(info_uri)
		self.pending_timeouts[info_uri] = \
			gobject.timeout_add(250, self._timeout_cb, monitor_uri, info_uri, event)

	def queue_changed(self, info_uri):
		self._queue_event(self.path, info_uri, gnomevfs.MONITOR_EVENT_CHANGED)

	def close(self):
		gnomevfs.monitor_cancel(self.monitor)
		self.monitor = None

	def _timeout_cb(self, monitor_uri, info_uri, event):
		if event in (gnomevfs.MONITOR_EVENT_METADATA_CHANGED,
                     gnomevfs.MONITOR_EVENT_CHANGED):
			self.emit("changed", info_uri)
		elif event == gnomevfs.MONITOR_EVENT_CREATED:
			self.emit("created", info_uri)
		elif event == gnomevfs.MONITOR_EVENT_DELETED:
			self.emit("deleted", info_uri)
		self.emit("event", info_uri, event)

		self._clear_timeout(info_uri)
		return False


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
			print _("File %s not found") % str(filename)
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
	if not ini.load('/usr/share/screenlets/CPUMeter/themes/default/theme.conf'):
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
	n.notify('A second note ..', title='Another note', icon='/usr/share/screenlets/Notes/icon.svg')
	
	# some tests of the list/find screenlets functions
	print "\nRunning screenlets: "
	print list_running_screenlets2()
	print "\n"
	print get_screenlet_process('Clock')
	print get_screenlet_process('Ruler')
	print get_screenlet_process('Webtest')

