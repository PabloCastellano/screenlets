# Banshee API 

import os
import dbus
import string
import gobject
from GenericPlayer import GenericAPI

class BansheeAPI(GenericAPI):
	__name__ = 'Banshee API'
	__version__ = '0.0'
	__author__ = 'vrunner'
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
		else: return False

	def connect(self):
		proxy_obj = self.session_bus.get_object(self.ns, self.iroot)
		self.playerAPI = dbus.Interface(proxy_obj, self.iface)

	def get_title(self):
		return self.playerAPI.GetPlayingTitle()
	
	def get_album(self):
		return self.playerAPI.GetPlayingAlbum()

	def get_artist(self):
		return self.playerAPI.GetPlayingArtist()

	def get_cover_path(self):
		return self.playerAPI.GetPlayingCoverUri()

	def is_playing(self):
		#print self.playerAPI.GetPlayingStatus()
		if self.playerAPI.GetPlayingStatus() == 1: return True
		else: return False

	def play_pause(self):
		self.playerAPI.TogglePlaying()

	def next(self):
		self.playerAPI.Next()

	def previous(self):
		self.playerAPI.Previous()

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

			playinguri = self.playerAPI.GetPlayingUri()
			if self.is_playing() and self.__curplaying != playinguri:
				self.__curplaying = playinguri
				self.callback_fn()
			self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		except:
			# The player exited ? call callback function
			self.callback_fn()
