# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#  screenlets.utils (c) Whise (Helder Fraga) 2008 <helder.fraga@hotmail.com>
#  Originaly by RYX (Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# TODO: move more functions here when possible
#

import screenlets
import gtk
import dbus
import os
import sys
import stat
import gettext
import re
import urllib
gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', screenlets.INSTALL_PREFIX +  '/share/locale')
import gobject
from distutils.version import LooseVersion
import subprocess
import commands
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulStoneSoup
from xdg.BaseDirectory import *
DIR_USER = os.path.join(xdg_config_home,'screenlets')
DIR_CONFIG = os.path.join(xdg_config_home,'screenlets')

try:
	import gnomevfs
except:
	pass
	
def _(s):
	return gettext.gettext(s)

# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def html_to_pango (html):	
	"""Simple html to pango stripper."""
	s = MLStripper()
	s.feed(html)
	no_html = s.get_data()
	decoded = BeautifulStoneSoup(no_html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	result = decoded.encode("UTF-8")
	return result.strip(" \n")


def get_autostart_dir():
	"""Returns the system autostart directory"""
        desktop_environment = 'gnome'

        if os.environ.get('KDE_FULL_SESSION') == 'true':
            desktop_environment = 'kde'
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            desktop_environment = 'gnome'
        else:
            try:
                info = commands.getoutput('xprop -root _DT_SAVE_MODE')
                if ' = "xfce4"' in info:
                    desktop_environment = 'xfce'
            except (OSError, RuntimeError):
                pass



	if desktop_environment == 'kde':
		return os.environ['HOME'] + '/.kde/Autostart/'
	elif desktop_environment == 'gnome':
		return xdg_config_home+'/autostart/'
	elif desktop_environment == 'xfce':
		return xdg_config_home+'/autostart/'

if os.geteuid()==0:
	# we run as root, install system-wide
	USER = 0
	DIR_USER		= screenlets.INSTALL_PREFIX + '/share/screenlets'
	DIR_AUTOSTART	= '/etc/xdg/autostart'			# TODO: use pyxdg here
else:
	# we run as normal user, install into $HOME
	USER = 1
	DIR_USER = os.path.join(xdg_config_home,'screenlets')
	DIR_AUTOSTART = get_autostart_dir()



def is_manager_running_me():
	"""checks if the one starting the screenlet is the screenlets manager"""
	if str(sys.argv[0]).find('screenlets-manager') != -1:
		return True
	else:
		return False

def containsAll(str, set):
	"""Check whether 'str' contains ALL of the chars in 'set'"""
	for c in set:
		if c not in str: return 0;
	return 1;
def containsAny(str, set):
	"""Check whether 'str' contains ANY of the chars in 'set'"""
	return 1 in [c in str for c in set]

def create_autostarter (name):
	"""Create a .desktop-file for the screenlet with the given name in 
	$HOME/.config/autostart."""
	if not os.path.isdir(DIR_AUTOSTART):
		# create autostart directory, if not existent
		if screenlets.show_question(None, 
			_("There is no existing autostart directory for your user account yet. Do you want me to automatically create it for you?"), 
			_('Error')):
			print "Auto-create autostart dir ..."
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
			print 'Removed duplicate entry'
	if not os.path.isfile(starter) and not os.path.exists(xdg_config_home+'/autostart/CalendarScreenlet'):
		path = find_first_screenlet_path(name)
		if path:
			print "Create autostarter for: %s/%sScreenlet.py" % (path, name)
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
			print 'Failed to create autostarter for %s.' % name
			return False
	else:
		print "Starter already exists."
		return True

def delete_autostarter ( name):
	"""Delete the autostart for the given screenlet."""
	if name.endswith('Screenlet'):
		name = name[:-9]
	print 'Delete autostarter for %s.' % name
	os.system('rm %s%sScreenlet.desktop' % (DIR_AUTOSTART, name))
	for f in os.listdir(DIR_AUTOSTART):
		a = f.find(name + 'Screenlet')
		if a != -1:
			print str(f) + ' duplicate entry'
			os.system('rm %s%s' % (chr(34)+DIR_AUTOSTART,f+chr(34)))
			print 'Removed duplicate entry'

def get_screenlet_linux_name_by_class_path(path):
	"""Returns screenlet name on form 'foobar-screenlet' by main screenlet class file path."""
	return path.lower().replace(".py", "").split("/")[path.count("/")].replace("screenlet", "-screenlet")

def get_screenlet_linux_name_by_class_name(name):
	"""Returns screenlet name on form 'foobar-screenlet' by screenlet class name."""
	return name.lower().replace("screenlet", "-screenlet")

def get_screenlet_linux_name_by_short_class_name(name):
	"""Returns screenlet name on form 'foobar-screenlet' by shortened screenlet class name."""
	return name.lower() + "-screenlet"

def is_screenlets_ppa_enabled():
	"""Detect if Screenlets default PPA is enabled on system."""
	result = commands.getstatusoutput("ls /etc/apt/sources.list.d/screenlets*ppa*.list | xargs grep '^deb.*'")[0]
	return result == 0

def get_more_screenlets_ubuntu():
	if not is_screenlets_ppa_enabled():
		print "PPA not enabled yet"
		if screenlets.show_question(None, _('The Screenlets PPA is not listed among Software Sources. Adding this enables installing individual screenlets from Package Manager (or Software Center) and by clicking on an AptURL on web pages like Gnome-look.org. Would you like to add the Screenlets PPA to your system?'), title=_("Do you want to enable the Screenlets PPA?")):
			result = commands.getstatusoutput('gksudo add-apt-repository ppa:screenlets-dev/ppa && gksudo apt-get update')[0]
			if result == 0:
				screenlets.show_message(None, _('The Screenlets PPA added successfully.'), title=_("Success!"))
			else:
				screenlets.show_error(None, _('Adding the Screenlets PPA failed.'), title=_("Failed!"))
	print "show web page anyway"
	subprocess.Popen(["xdg-open", screenlets.THIRD_PARTY_DOWNLOAD])


def get_translator(path):
	"""Returns translator by screenlet class path from __file__."""
	mo_domain = get_screenlet_linux_name_by_class_path(path)

	t = gettext.translation(mo_domain, screenlets.INSTALL_PREFIX +  '/share/locale', fallback = True)

	if not isinstance(t, gettext.GNUTranslations):
		cut_path_here = path.rfind('/')
		if cut_path_here > 0:
			screenlet_dir = path[0:cut_path_here]
		else:
			screenlet_dir = os.getcwd()
		mo_dir = screenlet_dir + "/mo"
		t = gettext.translation(mo_domain, mo_dir, fallback = True)
	return t.lgettext

def _contains_path (string):
	"""Internal function: Returns true if the given string contains one of the
	Screenlets paths."""
	# use saved paths for performance reasons
	for path in screenlets.SCREENLETS_PATH:
		if string.find(path) > -1:
			return True
	return False

def create_user_dir ():
	"""Create the userdir for the screenlets."""
	if not os.path.isdir(DIR_USER):
		try:
			os.mkdir(DIR_USER)
		except:
			print 'coulnt create user dir '+DIR_USER


def find_first_screenlet_path (screenlet_name):
	"""Scan the Screenlets paths for the occurence of screenlet "name" with the
	highest version and return the full path to it. This function is used to get
	the theme/data directories for a Screenlet and run the Screenlet."""
	available_versions_paths = []
	# use saved paths for performance reasons
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
						available_versions_paths.append(path)
				else:
					#print "utils.find_first_screenlet_path: "+\
					#	"LISTED PATH NOT EXISTS: " + path
					pass
		except OSError: # Raised by os.listdir: the directory doesn't exist
			pass
	if len(available_versions_paths) == 1:
		return available_versions_paths[0]
	elif len(available_versions_paths) > 1:
		path_and_version = []
		for version_path in available_versions_paths:
			path_and_version.append({'version': get_screenlet_metadata_by_path(version_path)['version'], 'path': version_path})

		sorted_versions = sorted(path_and_version, key=lambda x: LooseVersion(x["version"]), reverse=True)
		return sorted_versions[0]['path']

	# nothing found
	return None

def get_screenlet_icon (screenlet_name,width,height):
	img = gtk.gdk.pixbuf_new_from_file_at_size(\
			screenlets.INSTALL_PREFIX + '/share/screenlets-manager/noimage.svg',width,height)
	# use saved paths for performance reasons
	for path in screenlets.SCREENLETS_PATH:
		for ext in ['svg', 'png']:
			img_path = "%s/%s/icon.%s" % (path, screenlet_name, ext)
			if os.path.isfile(img_path):
				try:
					img = gtk.gdk.pixbuf_new_from_file_at_size(img_path,width,height)
				except Exception, ex:
					pass
	return img

def getBetween(data, first, last):
	x = len(first)
	begin = data.find(first) +x
	end = data.find(last, begin)
	return data[begin:end]

def get_screenlet_metadata_by_path (path):
	"""Returns a dict with name, info, author and version of the given
	screenlet. Use with care because it may import the screenlet 
	module and shouldn't be used too often due to performance issues."""

	chunks = path.split('/')
	classname = chunks[len(chunks)-1] + 'Screenlet'

	try:
		slfile = open(path + '/'+ classname + '.py','r')
		sldata = slfile.read()
		slfile.close()
		name = getBetween(sldata,'__name__','\n')
		name1 = getBetween(name ,"'","'")
		if name1.find(' = ') != -1: name1 = getBetween(name ,chr(34),chr(34))
		info = getBetween(sldata,'__desc__','\n')
		info1 = getBetween(info ,"'","'")
		if info1.find(' = ') != -1: info1 = getBetween(info ,chr(34),chr(34))
		if info1.find('_doc_') != -1: 
			info1 = getBetween(sldata ,'class ' + classname,'__name__')		
			info1 = getBetween(info1 ,chr(34) +chr(34)+chr(34),chr(34)+chr(34)+chr(34))
		author = getBetween(sldata,'__author__','\n')
		author1 = getBetween(author ,"'","'")
		if author1.find(' = ') != -1: author1 = getBetween(author ,chr(34),chr(34))
		version = getBetween(sldata,'__version__','\n')
		version1 = getBetween(version ,"'","'")
		if version1.find(' = ') != -1: version1 = getBetween(version ,chr(34),chr(34))
		requires1=[]
		if sldata.find('__requires__') > 0:
			requires = getBetween(sldata,'__requires__',']')
			if len(requires) > 0:
				cleaned = requires.split('[')[1].replace("'", "").replace('"', '').replace('\n', '').replace('\t', '')
				requires1 = "".join(cleaned.split()).split(",")

		return {'name'	: name1, 
			'info'		: gettext.dgettext(get_screenlet_linux_name_by_class_name(name1), info1), 
			'author'	: author1, 
			'version'	: version1,
			'requires'	: requires1
			}		
	except:
		try:
	# add path to PYTHONPATH
			if sys.path.count(path) == 0:
				sys.path.insert(0, path)
			slmod = __import__(classname)
			cls = getattr(slmod, classname)
			sys.path.remove(path)
			return {'name'	: cls.__name__, 
				'info'		: gettext.dgettext(get_screenlet_linux_name_by_class_name(cls.__name__), cls.__desc__), 
				'author'	: cls.__author__, 
				'version'	: cls.__version__,
				'requires'	: cls.__requires__
				}
		except Exception, ex:
			print "Unable to load '%s' from %s: %s " % (screenlet_name, path, ex)
			return None

def get_screenlet_metadata (screenlet_name):
	"""Returns a dict with name, info, author and version of the given
	screenlet. Use with care because it always imports the screenlet 
	module and shouldn't be used too often due to performance issues."""
	# find path to file
	path = find_first_screenlet_path(screenlet_name)

	return get_screenlet_metadata_by_path(path)

def refresh_available_screenlet_paths ():
	"""Checks the system Screenlets directory for screenlet packs
	and updates screenlets.SCREENLETS_PATH. Doesn't remove outdated paths
	(this doesn't hurt anyone)."""
	paths = screenlets.SCREENLETS_PATH
	for name in os.listdir(screenlets.DIR_USER_ROOT):
		path = screenlets.DIR_USER_ROOT + '/' + name
		# check if entry is a dir
		if name.startswith(screenlets.SCREENLETS_PACK_PREFIX):
			if path not in paths:
				if stat.S_ISDIR(os.stat(path).st_mode):
					paths.append(path)

def list_available_screenlets ():
	"""Scan the Screenlets paths for all existing screenlets and return their
	names (without trailing "Screenlet") as a list of strings."""
	sls = []
	# first refresh
	refresh_available_screenlet_paths()
	# use saved paths for performance reasons
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
					pass
		except OSError: # Raised by os.listdir: the directory doesn't exist
			pass
	sls.sort()
	return sls

import session
def list_running_screenlets ():
	"""Returns a list with names of running screenlets or None if no
	Screenlet is currently running. Function returns False if an error
	happened!"""
	running = []
	tempfile = screenlets.TMP_DIR + '/' + screenlets.TMP_FILE
	if not os.path.isfile(tempfile):
		return None
	f = open(tempfile, 'r')
	if f:
		running = f.readlines()
		f.close()
		for i in xrange(len(running)):
			running[i] = running[i][:-1]	# strip trailing EOL
		
	p = os.popen("ps aux | awk '/Screenlet.py/{ print $11, $12, $13, $14, $15, $16 }'")
	lst = []
	regex = re.compile('/([A-Za-z0-9]+)Screenlet.py ')
	for line in p.readlines():
		if not line.endswith('awk /Screenlet.py/{\n') and line != 'sh -c\n' \
			and _contains_path(line):
			slname = regex.findall(line)
			if slname and type(slname) == list and len(slname) > 0:
				lst.append(slname[0]+'Screenlet')
	p.close()
	for a in lst:
		if a not in running:
			running.append(a)
	return running



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
				lst.append(slname[0]+'Screenlet')
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

def get_user_dir(key, default):
	"""http://www.freedesktop.org/wiki/Software/xdg-user-dirs"""

	user_dirs_dirs = os.path.expanduser("~/.config/user-dirs.dirs")
	if os.path.exists(user_dirs_dirs):
		f = open(user_dirs_dirs, "r")
		for line in f.readlines():
			if line.startswith(key):
				return os.path.expandvars(line[len(key)+2:-2])
	return default	

def get_daemon_iface ():
	"""Check if the daemon is already running and return its interface."""
	bus = dbus.SessionBus()
	if bus:
		try:
			proxy_obj = bus.get_object(screenlets.DAEMON_BUS, screenlets.DAEMON_PATH) 
			if proxy_obj:
				return dbus.Interface(proxy_obj, screenlets.DAEMON_IFACE)

		except Exception, ex:
			print "Error in ScreenletsManager.connect_daemon: %s" % ex
	return None

def get_desktop_dir():
	"""Returns desktop dir"""
	desktop_dir =  get_user_dir("XDG_DESKTOP_DIR", os.path.expanduser("~/Desktop"))
	desktop_dir = urllib.unquote(desktop_dir)
	return desktop_dir

def get_filename_on_drop(sel_data):
	"""Returns filenames of window droped files"""
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

def quit_screenlet_by_name ( name):
	"""Quit all instances of the given screenlet type."""
	# get service for instance and call quit method
	service = screenlets.services.get_service_by_name(name)
	if service:
		service.quit()

def quit_all_screenlets():

	a = list_running_screenlets()
	if a != None:
		for s in a:
			if s.endswith('Screenlet'):
				s = s[:-9]
			try:
				quit_screenlet_by_name(s)
			except:
				pass

def restart_all_screenlets():
	quit_all_screenlets()
	for s in os.listdir(DIR_AUTOSTART):
		if s.lower().endswith('screenlet.desktop'):
			#s = s[:-17]
			os.system('sh '+ DIR_AUTOSTART + s + ' &')

def readMountFile( filename):
	"""Reads fstab file"""
	fstab = []
	f = open(filename, 'r')
	for line in f:
		if (not line.isspace() and not line.startswith('#') and not line.lower().startswith('none')) :
			fstabline = line.split()
			if fstabline[1] != 'none' and fstabline[1] != '/proc': fstab.append(fstabline[1])
	
	fstab.sort()
	return fstab

def read_file( filename):
	"""Reads a file"""
	f = open(filename, 'r')
	t = f.read()
	f.close()
	return t


def strip_html(string):
	"""Strips HTML tags of a string"""
	return re.sub(r"<.*?>|</.*?>","",string)



def lookup_daemon_autostart ():
	"""Adds Screenlets-daemon to autostart if not already"""
	if not os.path.isdir(DIR_AUTOSTART):
	# create autostart directory, if not existent
		if screenlets.show_question(None, _("There is no existing autostart directory for your user account yet. Do you want me to automatically create it for you?"), _('Error')):
			print "Auto-create autostart dir ..."
			os.system('mkdir %s' % DIR_AUTOSTART)
			if not os.path.isdir(DIR_AUTOSTART):
				screenlets.show_error(None, _("Automatic creation failed. Please manually create the directory:\n%s") % DIR_AUTOSTART, _('Error'))
				return False
		else:
			screenlets.show_message(None, _("Please manually create the directory:\n%s") % DIR_AUTOSTART)
			return False
	starter = '%sScreenlets Daemon.desktop' % (DIR_AUTOSTART)

	if not os.path.isfile(starter) and os.path.isfile('%sscreenlets-daemon.desktop' % (DIR_AUTOSTART)) == False:
		print "Create autostarter for: Screenlets Daemon"
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
		print 'Failed to create autostarter for %s.' % name
		return False
	else:
		print "Starter already exists."
		return True

def launch_screenlet(screenlet):
	"""Launches a screenlet"""
	name = str(screenlet)
	if not screenlets.launch_screenlet(name):
		screenlets.show_error(None, _('Failed to add %sScreenlet.') % name)



def xdg_open(name):
	"""Opens anything"""
	os.system('xdg-open ' + name + ' &')

# ------------------------------------------------------------------------------
# CLASSES
# ------------------------------------------------------------------------------

class ScreenletInfo(object):
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


class IniReader(object):
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
			print "File %s not found" % str(filename)
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
									print "Section %s not found!" % section_name
			f.close()
			return True
		else:
			return False



class Notifier(object):
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
			print "Notify: No DBus running or notifications-daemon unavailable."
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

