# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#  screenlets.install (c) RYX (Rico Pfaus 2007) <ryx@ryxperience.com>,
#  Whise (Helder Fraga) 2008 <helder.fraga@hotmail.com>
#

import screenlets
from screenlets import utils
import os
import gettext

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', screenlets.INSTALL_PREFIX +  '/share/locale')


# stub for gettext
def _(s):
	#return s
	return gettext.gettext(s)


if os.geteuid()==0:
	# we run as root, install system-wide
	USER = 0
	DIR_USER		= screenlets.DIR_USER_ROOT
	DIR_AUTOSTART	= '/etc/xdg/autostart'			# TODO: use pyxdg here
else:
	# we run as normal user, install into $HOME
	USER = 1
	DIR_USER		= screenlets.DIR_USER
	DIR_AUTOSTART = utils.get_autostart_dir()

class ScreenletInstaller(object):
	"""A simple utility to install screenlets into the current user's directory 
	(so either into $HOME/.screenlets/ for normal users or, if run as root, 
	into screenlets.INSTALL_PREFIX/share/screenlets/)."""
	
	def __init__ (self):
		self._message = ''
	
	
	def get_info_from_package_name (self, filename):
		"""Return all info we can get from the package-name or return None
		if something went wrong. If nothing failed, the returned value is
		a 4-tuple of the form: (name, version, basename, extension)."""
		base	= os.path.basename(filename)
		ext		= str(filename)[len(str(filename)) -3:]
		# prepend "tar." if we have a bz2 or gz archive
		tar_opts = 'xfz'
		if ext == 'bz2':
			tar_opts = 'xfj'
		if ext == 'skz': 
			screenlets.show_error(None,_('This type of karamba theme is not supported yet\n Only older versions can be used'))
			return False
		# extract archive to temporary dir

		if not os.path.isdir('/tmp/screenlets/'):
			os.system('mkdir ' + '/tmp/screenlets/')
		try: os.system('rm -rf /tmp/screenlets/install-temp')
		except: pass		
		tmpdir = '/tmp/screenlets' + '/install-temp/'
		os.system('mkdir %s' % tmpdir)
		
		

		os.system('tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), tmpdir))
		for dd in os.listdir(tmpdir):
			if str(dd).endswith('.theme'):
				os.system('mv ' + tmpdir + ' ' + '/tmp/screenlets/' + dd[:-6])
				os.system('mkdir %s' % tmpdir)
				os.system('mv ' + '/tmp/screenlets/' + dd[:-6] + ' '+ tmpdir)
				name = dd[:-6]
				return (name, ext)

		for d in tmpdir : #for each item in folders
  			if os.path.exists(d) and os.path.isdir(d): #is it a valid folder?
				for f in os.listdir(tmpdir): 
					
					name = f
		try:
			print name
			return (name, ext)
		except:

			return False
	
	def get_result_message (self):
		"""Return a human-readable result message about the last operation."""
		return self._message
	
	def is_installed (self, name):
		"""Checks if the given screenlet with the name defined by 'name' 
		(without trailing 'Screenlet') is already installed in the current
		install target location."""
		return os.path.isdir(DIR_USER + '/' + name)
			
	def install (self, filename):
		"""Install a screenlet from a given archive-file. Extracts the
		contents of the archive to the user's screenlet dir."""
		print 'Installing %s' % filename
		result = False
		# get name of screenlet
		#basename	= os.path.basename(filename)
		#extension	= os.path.splitext(filename)
		#name		= basename[:basename.find('.')]
		#print name
		info = self.get_info_from_package_name(filename)
		if info == False:
			self._message= _("Archive is damaged or unsupported, use only tar, bz2 or gz.")
			return False
		name	= info[0]
		ext		= info[1]
		
		tar_opts = 'xfz'
		if ext == 'bz2':
			tar_opts = 'xfj'
			
			

		# check if screenlet is already installed
		#found_path = screenlets.utils.find_first_screenlet_path(name)
		if self.is_installed(name):#found_path != None:
			if screenlets.show_question(None,(_("The %(slet)sScreenlet is already installed in '%(dir)s'.\nDo you wish to continue?") % {"slet":name, "dir":DIR_USER}),(_('Install %s') % (name))):
				pass
			else:
				self._message= _('%sScreenlet is already installed') % (name)
				return False
		# check extension and create appropriate args for tar
		tmpdir = screenlets.DIR_TMP + '/install-temp'
		# verify contents
		if not os.path.isdir('%s/%s' % (tmpdir, name)):
			# dir missing
			self._message = _("Invalid archive. Archive must contain a directory with the screenlet's name.")
		elif not os.path.isfile('%s/%s/%sScreenlet.py' % (tmpdir, name, name)):
			# Not a screenlet , lets check for karamba theme
			themename = ''
			for findtheme in os.listdir('%s/%s/' % (tmpdir, name)):
				if str(findtheme).lower().endswith('.theme'):
					print findtheme
					if themename == '':
						print tmpdir + '/'+ name + '/' + themename[:-6] + '.py'
						if not os.path.isfile(tmpdir + '/'+ name + '/' + findtheme[:-6] + '.py'):
							themename = findtheme[:-6]
						else:
							self._message = _("Compatibility for this karamba theme is not yet implemented")
							return False
			if themename != '':
				name1 = name.replace(' ','')
				name1 = name1.replace('-','')
				name1 = name1.replace('.','')
				name1 = name1.replace('_','')
				print name1
				#os.system('tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), DIR_USER))
				#os.system('mkdir %s/%s' % (DIR_USER,name1))
				if self.is_installed(name1):os.system('rm -rf %s/%s' % (DIR_USER, name1))
				
				os.system('mv %s/%s %s/%s ' % (chr(34) + tmpdir, name + chr(34),DIR_USER,name1))#tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), DIR_USER))
				os.system('mkdir %s/%s/themes' % (DIR_USER,name1))
				os.system('mkdir %s/%s/themes/default' % (DIR_USER,name1))
				os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/karamba.png ' + DIR_USER + '/' + name1 + '/themes/default/')
				if os.path.isfile(DIR_USER + '/' + name1 + '/icon.png') == False or os.path.isfile(DIR_USER + '/' + name1 + '/icon.svg') == False:
					os.system('cp ' + screenlets.INSTALL_PREFIX + '/share/screenlets-manager/karamba.png ' + DIR_USER + '/' + name1 + '/icon.png')
				widgetengine = open(screenlets.INSTALL_PREFIX + '/share/screenlets-manager/KarambaScreenlet.py', 'r')
				enginecopy = widgetengine.read()
				widgetengine.close()
				widgetengine = None
				enginecopy = enginecopy.replace('KarambaScreenlet',name1 + 'Screenlet')

				enginesave = open(DIR_USER + '/' + name1 + '/' + name1 + 'Screenlet.py','w')
				enginesave.write(enginecopy)
				enginesave.close()
				self._message = _("Karamba theme was successfully installed")
				result = True	
			else:self._message = _("Invalid archive. Archive does not contain a screenlet or a valid karamba theme.")


			







		else:
			# check for package-info

			if not os.path.isfile('%s/%s/Screenlet.package' % (tmpdir, name)):
				if screenlets.show_question(None,(_("%s was not packaged with the screenlet packager. Do you wish to continue and try to install it?") % (name)),(_('Install %s') % (name))):
					pass
				else:
					self._message = _("This package was not packaged with the screenlet packager.")
					return False	
			
			# copy archive to user dir (and create if not exists)
			utils.create_user_dir()
			os.system('tar %s %s -C %s' % (tar_opts, chr(34)+filename+chr(34), DIR_USER))
			# delete package info from target dir
			os.system('rm %s/%s/Screenlet.package' % (DIR_USER, name))
			# set msg/result
			self._message = _("The %sScreenlet has been succesfully installed.") % name
			result = True
		# remove temp contents
		os.system('rm -rf %s/install-temp' % screenlets.DIR_TMP)
		# ready
		return result

