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


# Banshee API by Whise and vrunner

import os
import dbus
import string
import gobject
import urllib
from GenericPlayer import GenericAPI

class BansheeAPI(GenericAPI):
	__name__ = 'Banshee API'
	__version__ = '0.0'
	__author__ = 'Whise and vrunner'
	__desc__ = 'API to the Banshee Music Player'

	ns = "org.gnome.Banshee"
	iroot = "/org/gnome/Banshee/Player"
	iface = "org.gnome.Banshee.Core"
	playerAPI = None

	__timeout = None
	__interval = 2

	callbackFn = None
	__curplaying = None

	# Extended Functions from the GenericAPI

	def __init__(self, session_bus):
		GenericAPI.__init__(self, session_bus)

	def is_active(self, dbus_iface):
		if self.ns in dbus_iface.ListNames(): return True
		else: 
			self.ns = "org.bansheeproject.Banshee"
			self.iroot = "/org/bansheeproject/Banshee/PlayerEngine"
			self.iface = "org.bansheeproject.Banshee.PlayerEngine"
			if self.ns in dbus_iface.ListNames(): return True
			else:return False

	def connect(self):
		proxy_obj = self.session_bus.get_object(self.ns, self.iroot)
		self.playerAPI = dbus.Interface(proxy_obj, self.iface)

	def get_title(self):
		try:
			return self.playerAPI.GetPlayingTitle()
			
		except:
			return self.playerAPI.GetCurrentTrack()['name']
	
	def get_album(self):
		try:
			return self.playerAPI.GetPlayingAlbum()
			
		except:
			return self.playerAPI.GetCurrentTrack()['album']

	def get_artist(self):
		try:
			return self.playerAPI.GetPlayingArtist()
			
		except:
			return self.playerAPI.GetCurrentTrack()['artist']

	def get_cover_path(self):
		try:
			return self.playerAPI.GetPlayingCoverUri()
		except:
			
			t = self.playerAPI.GetCurrentUri().replace('file://','')
			t = urllib.unquote(unicode.encode(t, 'utf-8'))
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

	def is_playing(self):
		try:
			if self.playerAPI.GetPlayingStatus() == 1: return True
			else: return False
		except:
			if self.playerAPI.GetCurrentState() == 'playing':return True
			else: return False


	def play_pause(self):
		self.playerAPI.TogglePlaying()

	def next(self):
		try:
			self.playerAPI.Next()
		except: os.system(' banshee-1 --next &')

	def previous(self):
		try:
			self.playerAPI.Previous()
		except: os.system(' banshee-1 --previous &')

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for Banshee, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)

	def info_changed(self, signal=None):
		# Only call the callback function if Data has changed
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		try:
			if self.__curplaying != None and not self.is_playing():
				self.__curplaying = None
				self.callback_fn()
			try:
				playinguri = self.playerAPI.GetPlayingUri()
			except:
				playinguri = self.playerAPI.GetCurrentUri()
			if self.is_playing() and self.__curplaying != playinguri:
				self.__curplaying = playinguri
				self.callback_fn()
			self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		except:
			# The player exited ? call callback function
			self.callback_fn()
