#!/usr/bin/env python
#

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

# A small app to package a screenlet into an easily distributible archive
# Useful for screenlet-developers ..
#
# (c) Guido Tabbernuk 2010, 2012
# <boamaod@gmail.com>
#
# Used code from:
# (c) RYX (Rico Pfaus) 2007 and Whise Helder Fraga
#

import sys, os, subprocess
from datetime import datetime
import screenlets
import textwrap
import gettext

gettext.textdomain('screenlets-manager')
gettext.bindtextdomain('screenlets-manager', screenlets.INSTALL_PREFIX +  '/share/locale')

def _(s):
	return gettext.gettext(s)

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

paragraphed_desc = sl_class.__desc__.replace("\t", " ").strip().split('\n\n')

desktop_desc = " ".join(paragraphed_desc[0].split())

deb_synopsis = None
deb_desc = ""
for line in paragraphed_desc:
	print line
	if deb_synopsis is None:
		lead = line.split("\n")
		wrapped = textwrap.wrap(lead[0].strip(), 63)
		deb_synopsis = wrapped[0]
		if len(wrapped) > 1:
			del(lead[0])
			del(wrapped[0])
			line = "\n".join(wrapped) + "\n".join(lead) # will continue the sentence truncated in synopsis
			print "SYN(CUT_WRAP)", deb_synopsis
		else:
			if len(lead) > 1:
				del(lead[0])
				line = "\n".join(lead) # will continue the sentence truncated in synopsis
				print "SYN(CUT_LEAD)", deb_synopsis
			else:
				print "SYN", deb_synopsis
				continue # description starts as a new paragraph
	current_addition = " " + "\n ".join(textwrap.wrap(" ".join(line.split()), 76)) + "\n .\n"
	print current_addition
	deb_desc += current_addition
if deb_desc.endswith(" .\n"):
	deb_desc = deb_desc[:len(deb_desc)-3]

if deb_synopsis is None:
	deb_synopsis = "a screenlet called" + sl_class.__name__
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
Description: %s
%s""" % (deb_name, deb_packager, screenlet_author, deb_name, deb_requires, deb_synopsis, deb_desc)

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
XDG_DESKTOP_FILES_DIR = $(DESTDIR)/usr/share/applications/screenlets

install:
	mkdir -p $(SYSTEM_SCREENLETS_DIR)
	cp -r screenlet/* $(SYSTEM_SCREENLETS_DIR)
	mkdir -p $(XDG_DESKTOP_FILES_DIR)
	cp -r xdg-desktop/* $(XDG_DESKTOP_FILES_DIR)
	for file in $$(ls -1 po/); do mkdir -p $(DESTDIR)/usr/share/locale/$${file%.po}/LC_MESSAGES; msgfmt -v -o $(DESTDIR)/usr/share/locale/$${file%.po}/LC_MESSAGES/""" + deb_name + ".mo po/$$file; done"

#print "=========================================================="
#print control
#print "=========================================================="

desktop_file = """[Desktop Entry]
Name=%s
Encoding=UTF-8
Version=1.0
Type=Application
GenericName=Desktop widget
Comment=%s
Exec= python -u /usr/share/screenlets/%s/%sScreenlet.py
""" % (sl_name, desktop_desc, sl_name, sl_name)

try:

	icon = None
	if os.path.exists("%s/icon.svg" % path):
		icon = "icon.svg"
	elif os.path.exists("%s/icon.png" % path):
		icon = "icon.png"
	if icon is not None:
		desktop_file += "Icon=/usr/share/screenlets/%s/%s" % (sl_name, icon)

	os.system('rm -rf /tmp/%s' % deb_name)
	os.system('mkdir -p /tmp/%s/debian' % deb_name)
	os.system('mkdir -p /tmp/%s/screenlet' % deb_name)

	write_conf_file('/tmp/%s/Makefile' % deb_name, Makefile)
	write_conf_file('/tmp/%s/debian/control' % deb_name, control)
	write_conf_file('/tmp/%s/debian/changelog' % deb_name, changelog)
	write_conf_file('/tmp/%s/debian/compat' % deb_name, compat)
	write_conf_file('/tmp/%s/debian/rules' % deb_name, rules)

	os.system('mkdir -p /tmp/%s/xdg-desktop' % deb_name)
	write_conf_file('/tmp/%s/xdg-desktop/%s.desktop' % (deb_name, deb_name), desktop_file)
	os.system('chmod a+x /tmp/%s/xdg-desktop/*' % deb_name)

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
