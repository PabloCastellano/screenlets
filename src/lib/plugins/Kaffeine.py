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

# Kaffeine API (c) Whise (Helder Fraga) 2008 <helder.fraga@hotmail.com>


import os
import string
import gobject
from GenericPlayer import GenericAPI
import commands

class KaffeineAPI(GenericAPI):
	__name__ = 'Kaffeine API'
	__version__ = '0.0'
	__author__ = 'Whise (Helder Fraga)'
	__desc__ = 'Kaffeine API to a Music Player'

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
		proc = os.popen("""ps axo "%p,%a" | grep "kaffeine" | grep -v grep|cut -d',' -f1""").read()
		procs = proc.split('\n')
		if len(procs) > 1:
			return True
		else:
			return False
	def connect(self):
		pass
	
	# The following return Strings
	def get_title(self):
		return commands.getoutput('dcop kaffeine KaffeineIface title')
	
	def get_album(self):
		return commands.getoutput('dcop kaffeine KaffeineIface album')

	def get_artist(self):
		return commands.getoutput('dcop kaffeine KaffeineIface artist')


	def get_cover_path(self):
		t = commands.getoutput('dcop kaffeine KaffeineIface getFileName')
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
#path

	# Returns Boolean
	def is_playing(self):
		return commands.getoutput('dcop kaffeine KaffeineIface isPlaying')

	# The following do not return any values
	def play_pause(self):
		if self.is_playing():
			os.system('dcop kaffeine KaffeineIface pause &')
		else:
			os.system('dcop kaffeine KaffeineIface play &')
	def next(self):
		os.system('dcop kaffeine KaffeineIface next &')

	def previous(self):
		os.system('dcop kaffeine KaffeineIface previous &')

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for Listen, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		#self.playerAPI.connect_to_signal("playingUriChanged", self.info_changed)

	def info_changed(self, signal=None):
		# Only call the callback function if Data has changed
		if self.__curplaying != commands.getoutput('dcop kaffeine KaffeineIface title'):
			self.__curplaying = commands.getoutput('dcop kaffeine KaffeineIface title')
			self.callback_fn()

		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)

