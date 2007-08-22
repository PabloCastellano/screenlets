#!/usr/bin/env python
#
# A small app to package a screenlet into an easily distributible archive
# Useful for screenlet-developers ..
#
# (c) RYX (Rico Pfaus) 2007
#

import sys, os
from datetime import datetime
import screenlets
import gettext

gettext.textdomain('screenlets-manager')
gettext.bindtextdomain('screenlets-manager', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)


# + constants
USAGE				= _("""Screenlets packager - (c) RYX (Rico Pfaus) 2007
Usage: %s <path> [options]""") % sys.argv[0]
PACKAGE_INFO_FILE	= 'Screenlet.package'


# + globals (make commandline options from these)
# surpress any output if true
quiet		= False
# exclude these from archive
excludes	= ['*.pyo', '*.pyc', '*~', '*.bak']


# + functions
def msg (str):
	if not quiet:
		print str

def die (str):
	msg('Error: ' + str)
	sys.exit(1)


# + start app
# check path-argument
argc = len(sys.argv)
if argc < 2:
	die(USAGE)
else:
	path = sys.argv[1]
	if path[-1] == '/':
		path = path[:-1]

# check options and set vars (TODO)
if argc > 2:
	for var in sys.argv[2:]:
		print var

# check for existence of directory to be packaged
if not os.path.isdir(path):
	die(_('The specified path "%s" does not exist.') % path)
msg(_('Found path "%s".') % path)

# get name of screenlet from the pathname
try:
	sl_name = path[path.rfind('/')+1:]
except:
	die(_('Failed to extract screenlet name from path.'))
msg(_('Screenlet name is %s.') % sl_name)

# check for correct file inside path
if not os.path.isfile(path + '/' + sl_name + 'Screenlet.py'):
	die(_('No screenlet-file "%sScreenlet.py" found in the given path.') % sl_name)
msg(_('Found %sScreenlet.py in path.') % sl_name)

# import the screenlets module from inside the dir and lookup the class
if sys.path.count(path) == 0:
	sys.path.insert(0, path)
try:
	sl_module = __import__(sl_name + 'Screenlet')
	sys.path.remove(path)
except Exception, ex:
	die(_("Unable to import module '%s' from %s. (%s)") % (sl_name, path, ex))
msg(_('Successfully imported module: %s') % str(sl_module))

# lookup screenlet class
try:
	sl_class = getattr(sl_module, sl_name + 'Screenlet')
except Exception, ex:
	die(_("Unable to import class from module."))
if not issubclass(sl_class, screenlets.Screenlet):
	die(_('The class inside the module is no subclass of screenlets.Screenlet.'))
msg(_('Successfully got class from module: %s') % str(sl_class))

# create a file with the package-info inside the screenlet's dir
meta = """[Screenlet Package]
Name=%s
Author=%s
Desc=%s
Version=%s
ApiVersion=%s
Created=%s
""" % (sl_class.__name__, sl_class.__author__, sl_class.__desc__, 
	sl_class.__version__, screenlets.VERSION, 
	datetime.now().strftime("%Y/%m/%d"))
f = open('%s/%s' % (path, PACKAGE_INFO_FILE), 'w')
if f:
	f.write(meta)
	f.close()
else:
	die(_('Failed to create package info in %s.') % path)
msg(_('Created package info file.'))

# cd into path, package the whole stuff up into an archive and save it to our pwd
pwd = os.getcwd()
excl = ''
for e in excludes:
	excl += ' --exclude=' + e
os.system('cd %s && cd .. && tar cfz %s/%s.tar.gz %s %s' % (path, pwd, 
	sl_name, sl_name, excl))

# remove the metadata file
os.system('rm %s/%s' % (path, PACKAGE_INFO_FILE))
msg(_('Cleaned up and finished.'))

# OK
print 'OK.'
