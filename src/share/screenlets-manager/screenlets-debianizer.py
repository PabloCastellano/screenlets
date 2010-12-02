#!/usr/bin/env python
#

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# A small app to package a screenlet into an easily distributible archive
# Useful for screenlet-developers ..
#
# (c) Guido Tabbernuk 2010
# <boamaod@gmail.com>
#
# Used code from:
# (c) RYX (Rico Pfaus) 2007 and Whise Helder Fraga
#

import sys, os, subprocess
from datetime import datetime
import screenlets
import gettext

gettext.textdomain('screenlets-manager')
gettext.bindtextdomain('screenlets-manager', screenlets.INSTALL_PREFIX +  '/share/locale')

def _(s):
	return gettext.gettext(s)

def word_wrap(string, width=80, ind1=0, ind2=0, prefix=''):
    """ word wrapping function.
        string: the string to wrap
        width: the column number to wrap at
        prefix: prefix each line with this string (goes before any indentation)
        ind1: number of characters to indent the first line
        ind2: number of characters to indent the rest of the lines
    """
    string = prefix + ind1 * " " + string
    newstring = ""
    while len(string) > width:
        # find position of nearest whitespace char to the left of "width"
        marker = width - 1
        while not string[marker].isspace():
            marker = marker - 1

        # remove line from original string and add it to the new string
        newline = string[0:marker] + "\n"
        newstring = newstring + newline
        string = prefix + ind2 * " " + string[marker + 1:]

    return newstring + string

def write_conf_file(path, contents):
	f = open(path, 'w')
	if f:
		f.write(contents)
		f.close()
	else:
		print "!!!", path
		raise Exception

# + constants
USAGE = _("""Screenlets debianizer - (c) Guido Tabbernuk 2010
Usage: screenlets-debianizer <path> [debuild keys or anything you like]
Caution!!!   You need lot of packages installed in your system as well as a bzr user set up to build a deb!
""")

# + globals (make commandline options from these)
# surpress any output if true
quiet		= False

# + functions
def msg (str):
	if not quiet:
		print str

def err (str):
	sys.stderr.write('Error: ' + str)

def die (str):
	err (str)
	sys.exit(1)


compatibility_mode = False

# + start app
# check path-argument
argc = len(sys.argv)
arg_start = 1
if argc < 2:
	die(USAGE)
else:
	path = sys.argv[arg_start]
	if path[-1] == '/':
		path = path[:-1]
	arg_start += 1

arguments = []

# check options and set vars (TODO)
if argc > arg_start:
	for var in sys.argv[arg_start:]:
		arguments.append(var)

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

sl_path = path + '/' + sl_name

# check for correct file inside path
if not os.path.isfile(sl_path + 'Screenlet.py'):
	die(_('No screenlet-file "%sScreenlet.py" found in the given path.') % sl_name)
msg(_('Found %sScreenlet.py in path.') % sl_name)

# import the screenlets module from inside the dir and lookup the class
if sys.path.count(path) == 0:
	sys.path.insert(0, path)
try:
	sl_module = __import__(sl_name + 'Screenlet')
	sys.path.remove(path)
except Exception, ex:
	die("Unable to import module '%s' from %s. (%s)" % (sl_name, path, ex))
msg(_('Successfully imported module: %s') % str(sl_module))

# lookup screenlet class
try:
	sl_class = getattr(sl_module, sl_name + 'Screenlet')
except Exception, ex:
	die(_("Unable to import class from module."))
if not issubclass(sl_class, screenlets.Screenlet):
	die(_('The class inside the module is no subclass of screenlets.Screenlet.'))
msg(_('Successfully got class from module: %s') % str(sl_class))

# create a debian control file
deb_name = screenlets.utils.get_screenlet_linux_name_by_class_name(sl_class.__name__)
deb_requires = ", ".join(map(str, sl_class.__requires__))
deb_packager = os.popen("bzr whoami").readline().replace('\n', '')
deb_desc = " "
for line in sl_class.__desc__.split('\n'):
	line = word_wrap(line, 72, ind2=1)
	deb_desc += line + "\n .\n "
screenlet_author = sl_class.__author__

print "Going for: %s" % deb_name

control = """Source: %s
Section: gnome
Priority: optional
Maintainer: %s
Uploaders: %s
Build-Depends: debhelper (>= 5)
Standards-Version: 3.7.2

Package: %s
Depends: screenlets (>= 0.1.2-9), %s
Architecture: all
Description:%sCreated by: %s""" % (deb_name, deb_packager, screenlet_author, deb_name, deb_requires, deb_desc, screenlet_author)

release = os.popen("lsb_release -cs").readline().replace('\n', '')
deb_date = os.popen("date -R").readline().replace('\n', '')
deb_version = sl_class.__version__

changelog = """%s (%s) %s; urgency=low

  * Created automatically by The Screenlets Debianizer.

 -- %s  %s""" % ( deb_name, deb_version, release, deb_packager, deb_date)

rules = """#!/usr/bin/make -f
# -*- makefile -*-
build:
clean:
	dh_testdir
	dh_testroot
	dh_clean 
install:
	dh_testdir
	dh_testroot
	dh_clean -k 
	dh_installdirs
	$(MAKE) DESTDIR=$(CURDIR)/debian/%s install
binary-indep: build install
binary-arch: build install
	dh_testdir
	dh_testroot
	dh_installchangelogs 
	dh_installdocs
	dh_installexamples
#	dh_install
#	dh_installmenu
#	dh_installdebconf
#	dh_installlogrotate
#	dh_installemacsen
#	dh_installpam
#	dh_installmime
#	dh_python
#	dh_installinit
#	dh_installcron
#	dh_installinfo
	dh_installman
	dh_link
	dh_strip
	dh_compress
	dh_fixperms
#	dh_perl
#	dh_makeshlibs
	dh_installdeb
	dh_shlibdeps
	dh_gencontrol
	dh_md5sums
	dh_builddeb
binary: binary-indep binary-arch
.PHONY: build clean binary-indep binary-arch binary install configure""" % deb_name

compat = """5"""

Makefile = """SYSTEM_SCREENLETS_DIR = $(DESTDIR)/usr/share/screenlets

install:
	mkdir -p $(SYSTEM_SCREENLETS_DIR)
	cp -r screenlet/* $(SYSTEM_SCREENLETS_DIR)
	for file in $$(ls -1 po/); do mkdir -p $(DESTDIR)/usr/share/locale/$${file%.po}/LC_MESSAGES; msgfmt -v -o $(DESTDIR)/usr/share/locale/$${file%.po}/LC_MESSAGES/lipik-screenlet.mo po/$$file; done"""

#print "=========================================================="
#print control
#print "=========================================================="

try:
	os.system('rm -rf /tmp/%s' % deb_name)
	os.system('mkdir -p /tmp/%s/debian' % deb_name)
	os.system('mkdir -p /tmp/%s/screenlet' % deb_name)

	write_conf_file('/tmp/%s/Makefile' % deb_name, Makefile)
	write_conf_file('/tmp/%s/debian/control' % deb_name, control)
	write_conf_file('/tmp/%s/debian/changelog' % deb_name, changelog)
	write_conf_file('/tmp/%s/debian/compat' % deb_name, compat)
	write_conf_file('/tmp/%s/debian/rules' % deb_name, rules)

	os.system('cp -r %s /tmp/%s/screenlet' % (path, deb_name))

	if os.path.exists("/tmp/%s/screenlet/%s/po" % (deb_name, sl_name)):
		os.system('mv /tmp/%s/screenlet/%s/po /tmp/%s' % (deb_name, sl_name, deb_name))
		os.system('rm /tmp/%s/po/*.pot' % (deb_name))

except:
	die(_('Failed to create file (no permissions?).'))

msg(_('Created all the files needed.'))

msg(_('Debianizing: %s (%s)') % (deb_name, deb_version) )

deb_arguments = " ".join(map(str, arguments))

if len(deb_arguments) > 0:
	print "Passing additional arguments: '%s'" % deb_arguments

# modify this if you want to build differently or do something more interesting
details = os.popen("cd /tmp/%s/debian && debuild %s " % (deb_name, deb_arguments)).read()

if subprocess.call("ls /tmp/%s_%s*.changes 1>/dev/null" % (deb_name, deb_version), shell=True) != 0:
	msg(details)
	die(_('Failed to debianize "%s".') % deb_name)

# UNCOMMENT ANY ONE OF FOLLOWING, IF NEEDED!
##########################################

# if you do not want it, just deb file is enough
if subprocess.call("cp /tmp/%s*deb ." % deb_name, shell=True) != 0:
	die(_('Failed to copy results "/tmp/%s*deb".') % deb_name)

# if you want all the debian files created by debuild
#os.system('cp /tmp/%s* .' % deb_name)

# if you want a whole deb structure to modify it yourself
#os.system('cp -r /tmp/%s* .' % deb_name)

############################################

# remove the files under tmp
os.system('rm -rf /tmp/%s*' % deb_name)
msg(_('Cleaned up and finished.'))

# OK
print 'OK.'
