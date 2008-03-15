#
# INFO: The setup-script for the screenlets
#
# (c) RYX (Rico Pfaus) 2007 ...
#

from distutils.core import setup
import os
import sys

# import screenlets to get package constants (like path/prefix)
#sys.path.insert(0, 'src/')
#import lib	# screenlets-package called 'lib' here because of the dir-names



#----------------------------------------------------------------------------
# CONFIGURATION
#----------------------------------------------------------------------------

# install prefix (if you want to change this, change it in src/lib/__init__.py)
INSTALL_PREFIX	= '/usr'
# global install-path for daemon and screenlets-packages
INSTALL_PATH	= INSTALL_PREFIX + '/share/screenlets'
# current version of package
VERSION			= '0.0.13'

#----------------------------------------------------------------------------
# FUNCTIONS
#----------------------------------------------------------------------------

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



#----------------------------------------------------------------------------
# RUN SETUP
#----------------------------------------------------------------------------

# + Create list with additional files to be installed (passed as 
#   data_files-attribute to setup-function):

# - screenlets-subdirs and all their data go into INSTALL_PATH/<name>/...
dirlist		= scan_dir_list('src/share/screenlets')
files_list	= make_file_list(dirlist, INSTALL_PATH, 
	strip='src/share/screenlets/')	# to strip this string from filenames

# - our pseudo-"binaries" go into INSTALL_PREFIX/bin
files_list.insert(0, (INSTALL_PREFIX + '/bin', ['bin/screenletsd']))
files_list.insert(0, (INSTALL_PREFIX + '/bin', ['bin/screenlets-manager']))
files_list.insert(0, (INSTALL_PREFIX + '/bin', ['bin/screenlets-packager']))

# - the manager and its files go into INSTALL_PATH + '-manager'
files_list.insert(0, (INSTALL_PATH + '-manager', 
	['src/share/screenlets-manager/screenlets-manager.py',
	'src/share/screenlets-manager/screenlets-daemon.py',
	'src/share/screenlets-manager/screenlets-packager.py',
	'src/share/screenlets-manager/noimage.svg',
	'src/share/screenlets-manager/KarambaScreenlet.py',
	'src/share/screenlets-manager/karamba.png']))
	
#Desktop file and icon for screenlets-manager
files_list.insert(0, ('/usr/share/applications', ['desktop-menu/screenlets-manager.desktop']))
files_list.insert(0, ('/usr/share/icons', ['desktop-menu/screenlets.svg']))
	
# + Call setup function (installs screenlets into python's root)
setup(name = 'screenlets',
	# metainfo for this package
	version			= VERSION,
	author			= 'RYX (Rico Pfaus)',
	author_email	= 'ryx@ryxperience.com',
	url				= 'http://www.screenlets.org',
	license			= 'GPL v3',
	description		= 'Screenlets - widget-like mini-applications combining '+\
		'usability and eye-candy on the modern, composited Linux-desktop.',
	# packages (go into python-packages and become globally available)
	packages		= ['screenlets'],
	package_dir		= {'screenlets': 'src/lib'},
	# additional files to be installed
	data_files		= files_list
	)

