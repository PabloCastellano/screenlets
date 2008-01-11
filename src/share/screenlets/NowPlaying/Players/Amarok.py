#!/usr/bin/env python

# Amarok API 

import os
import string
import gobject
import pydcop
from GenericPlayer import GenericAPI

class AmarokAPI(GenericAPI):
	__name__ = 'Amarok API'
	__version__ = '0.0'
	__author__ = 'vrunner'
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
		app = pydcop.anyAppCalled("amarok")
		if not app: return False
		else: return True

	# Make a connection to the Player
	def connect(self):
		self.playerAPI = pydcop.anyAppCalled("amarok").player
	
	# The following return Strings
	def get_title(self):
		return self.playerAPI.title()
	
	def get_album(self):
		return self.playerAPI.album()

	def get_artist(self):
		return self.playerAPI.artist()

	def get_cover_path(self):
		return self.playerAPI.coverImage()

	# Returns Boolean
	def is_playing(self):
		return self.playerAPI.isPlaying()

	# The following do not return any values
	def play_pause(self):
		self.playerAPI.playPause()

	def next(self):
		self.playerAPI.next()

	def previous(self):
		self.playerAPI.prev()

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for Listen, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		#self.playerAPI.connect_to_signal("playingUriChanged", self.info_changed)

	def info_changed(self, signal=None):
		# Only call the callback function if Data has changed
		if self.__curplaying != self.playerAPI.nowPlaying():
			self.__curplaying = self.playerAPI.nowPlaying()
			self.callback_fn()

		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)

