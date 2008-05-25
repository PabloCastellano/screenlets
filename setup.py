#!/usr/bin/python
#
# INFO: The setup-script for the screenlets
#
# (c) 2008 Rico Pfaus (RYX), Helder Fraga (Whise), and Natan Yellin (Aantn)
#

from distutils.core import setup
import distutils.sysconfig
import os
import sys

# import screenlets to get package constants
#sys.path.insert(0, 'src/')
#import lib  # screenlets-package called 'lib' here because of the dir-names

VERSION	= '0.1.2'

def filter_filename_callback(filename):
	"""Called by make_file_list to determine which files to add/install 
	to the package and which files are to be ignored."""
	# skip temp-files
	if filename[-1] == '~':
		return False
	return True
	
def scan_dir_list(path):
	"""makes a list of all subdirectories of a path"""
	out = []
	plen = len(path) + 1
	files = os.listdir(path)
	for f in files:
		full = path + '/' + f
		if (os.path.isdir(full)):
			out.append(full)
			out.extend(scan_dir_list(full))
	return out

def make_file_list(dirlist, install_path, strip=''):
	"""Takes a list with dirnames and creates a list suitable for the 
	data_files-attribute for the setup-function that includes all files 
	within the dir. The string defined by strip will be replaced from 
	within the directory names. TODO: the strip-arg is not very secure 
	and could cause errors ... fix that!!!!!!!!!! """
	data_files = []
	for d in dirlist:
		dlst = []
		files = os.listdir(d)
		for f in files:
			full = d +'/' + f
			if os.path.isfile(full):
				if filter_filename_callback(f):
					dlst.append(full)
		data_files.append((install_path + '/' + d.replace(strip, ''), dlst))
	return data_files

# ---------------------------------------------------------------
# Create various lists of files that will be passed to setup()
# ---------------------------------------------------------------

# Create a list of scripts that will be installed into PREFIX/bin/
scripts_list = ['src/bin/screenletsd',
	'src/bin/screenlets',
	'src/bin/screenlets-manager',
	'src/bin/screenlets-daemon',
	'src/bin/screenlets-packager']

# Install screenlets into PREFIX/share/screenlets/
dirlist	= scan_dir_list('src/share/screenlets') 
files_list = make_file_list(dirlist, 'share/screenlets', 
	strip='src/share/screenlets/')	# to strip this string from filenames

# Install the manager's files into PREFIX/share/screenlets-manager
files_list.insert(0, ('share/screenlets-manager',
	['src/share/screenlets-manager/screenlets-manager.py',
	'src/share/screenlets-manager/screenlets-daemon.py',
	'src/share/screenlets-manager/screenlets-packager.py',
	'src/share/screenlets-manager/noimage.svg',
	'src/share/screenlets-manager/KarambaScreenlet.py',
	'src/share/screenlets-manager/widget.png',
	'src/share/screenlets-manager/WidgetScreenlet.py',
	'src/share/screenlets-manager/prefs.js',
	'src/share/screenlets-manager/webapp.png',
	'src/share/screenlets-manager/WebappScreenlet.py',
	'src/share/screenlets-manager/karamba.png']))


# Install desktop files and icons
files_list.insert(0, ('share/applications', ['desktop-menu/screenlets-manager.desktop']))
files_list.insert(0, ('share/icons', ['desktop-menu/screenlets.svg']))

# Install translation files
podir = os.path.join (os.path.realpath ("."), "po")
if os.path.isdir (podir):
	buildcmd = "msgfmt -o build/locale/%s/LC_MESSAGES/%s.mo po/%s.po"
	mopath = "build/locale/%s/LC_MESSAGES/%s.mo"
	destpath = "share/locale/%s/LC_MESSAGES"
	for name in os.listdir (podir):		
		if name.endswith('.po'):
			name = name.replace('screenlets-manager','screenletsmanager')
			dname = name.split('-')[1].split('.')[0]
			name = name[:-3]
			name = name.replace('screenletsmanager','screenlets-manager')
			if sys.argv[1] == "build" or sys.argv[1] == "install":
				print 'Creating language Binary for : ' + name
				if not os.path.isdir ("build/locale/%s/LC_MESSAGES" % dname):
					os.makedirs ("build/locale/%s/LC_MESSAGES" % dname)
				os.system (buildcmd % (dname,name.replace('-'+dname,''), name))
				files_list.append ((destpath % dname, [mopath % (dname,name.replace('-'+dname,''))]))
				
# ----------------------------
# Call setup()
# ----------------------------

setup(name='screenlets',
	version			= VERSION,
	description		= 'A widget framework for Linux',
	url			= 'http://www.screenlets.org',
	author			= 'Whise (Helder Fraga)<helder.fraga@hotmail.com>, RYX (Rico Pfaus) <ryx@ryxperience.com>, Sorcerer (Hendrik Kaju), Natan Yellin (Aantn) <aantny@gmail.com>',
	author_email		= 'helderfraga@hotmail.com',
	license			= 'GPL v3',
	packages		= ['screenlets'],
	package_dir		= {'screenlets': 'src/lib'},
	data_files		= files_list,
	scripts			= scripts_list
)
