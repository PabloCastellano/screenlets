# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# Amarok API by Whise and vrunner

import os
import string
import gobject
try:
	import pydcop
	dcop = True
except:
	print 'Pydcop not found , will work limited'
	dcop = False
from GenericPlayer import GenericAPI
import commands

class AmarokAPI(GenericAPI):
	__name__ = 'Amarok API'
	__version__ = '0.0'
	__author__ = 'Whise and vrunner'
	__desc__ = 'Amarok API to a Music Player'

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
		if dcop:
			app = pydcop.anyAppCalled("amarok")
			if not app: return False
			else: return True
		else:
			proc = os.popen("""ps axo "%p,%a" | grep "amarokapp" | grep -v grep|cut -d',' -f1""").read()
			procs = proc.split('\n')
			if len(procs) > 1:
				return True
			else:
				return False
	def connect(self):
		if dcop:
			self.playerAPI = pydcop.anyAppCalled("amarok").player
		else:pass
	
	# The following return Strings
	def get_title(self):
		if dcop:
			return self.playerAPI.title()
		else:
			return commands.getoutput('dcop amarok player title')
	
	def get_album(self):
		if dcop:
			return self.playerAPI.album()
		else:
			return commands.getoutput('dcop amarok player album')

	def get_artist(self):
		if dcop:
			return self.playerAPI.artist()
		else:
			return commands.getoutput('dcop amarok player artist')


	def get_cover_path(self):
		if dcop:
			return self.playerAPI.coverImage()
		else:
			path =  commands.getoutput('dcop amarok player coverImage')
			if path.find('130@nocover.png') != -1:
				t = commands.getoutput('dcop amarok player path')
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

		return ''

	# Returns Boolean
	def is_playing(self):
		if dcop:
			return self.playerAPI.isPlaying()
		else:
			return commands.getoutput('dcop amarok player isPlaying')

	# The following do not return any values
	def play_pause(self):
		if dcop:
			self.playerAPI.playPause()
		else:
			os.system('amarok -t &')

	def next(self):
		if dcop:
			self.playerAPI.next()
		else:
			os.system('amarok -f &')

	def previous(self):
		if dcop:
			self.playerAPI.prev()
		else:
			os.system('amarok -r &')

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for Listen, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		#self.playerAPI.connect_to_signal("playingUriChanged", self.info_changed)

	def info_changed(self, signal=None):
		# Only call the callback function if Data has changed
		if dcop:
			if self.__curplaying != self.playerAPI.nowPlaying():
				self.__curplaying = self.playerAPI.nowPlaying()
				self.callback_fn()
		else:
			if self.__curplaying != commands.getoutput('dcop amarok player nowPlaying'):
				self.__curplaying = commands.getoutput('dcop amarok player nowPlaying')
				self.callback_fn()

		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)

