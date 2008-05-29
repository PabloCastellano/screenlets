# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# Audacious API (c) Whise (Helder Fraga) 2008 <helder.fraga@hotmail.com>


import os
import string
import gobject
from GenericPlayer import GenericAPI
import commands

class AudaciousAPI(GenericAPI):
	__name__ = 'Audacious API'
	__version__ = '0.0'
	__author__ = 'Whise (Helder Fraga)'
	__desc__ = 'Audacious API to a Music Player'

	playerAPI = None

	__timeout = None
	__interval = 2

	callbackFn = None
	__curplaying = None


	def __init__(self, session_bus):
		# Ignore the session_bus. Initialize a dcop connection
		GenericAPI.__init__(self, session_bus)
	
	# Check if the player is active : Returns Boolean
	# A handle to the dbus interface is passed in : doesn't need to be used
	# if there are other ways of checking this (like dcop in amarok)
	def is_active(self, dbus_iface):
		proc = os.popen("""ps axo "%p,%a" | grep "audacious" | grep -v grep|cut -d',' -f1""").read()
		procs = proc.split('\n')
		if len(procs) > 1:
			return True
		else:
			return False
	def connect(self):
		pass
	
	# The following return Strings
	def get_title(self):
		try:
			a =  commands.getoutput('audtool --current-song').split(' - ')[2]
			return a
		except:
			return ''
	
	def get_album(self):
		try:
			a =  commands.getoutput('audtool --current-song').split(' - ')[1]
			return a
		except:
			return ''

	def get_artist(self):
		try:
			a =  commands.getoutput('audtool --current-song').split(' - ')[0]
			return a
		except:
			return ''


	def get_cover_path(self):
		try:
			t = commands.getoutput('audtool --current-song-filename')
			t = t.replace('file://','')
			t = t.split('/')
			basePath = ''
			for l in t:
				if l.find('.') == -1:
					basePath = basePath + l +'/'
		
			names = ['Album', 'Cover', 'Folde']
			for x in os.listdir(basePath):
				if os.path.splitext(x)[1] in [".jpg", ".png"] and (x.capitalize()[:5] in names):
					coverFile = basePath + x
					return coverFile
		except: return ''
		return ''
#path

	# Returns Boolean
	def is_playing(self):
		return True

	# The following do not return any values
	def play_pause(self):
		os.system('audtool --playback-playpause &')

	def next(self):
		os.system('audtool --playlist-advance &')

	def previous(self):
		os.system('audtool --playlist-reverse &')

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for Listen, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		#self.playerAPI.connect_to_signal("playingUriChanged", self.info_changed)

	def info_changed(self, signal=None):
		# Only call the callback function if Data has changed
		if self.__curplaying != commands.getoutput('audtool --current-song'):
			self.__curplaying = commands.getoutput('audtool --current-song')
			self.callback_fn()

		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)

