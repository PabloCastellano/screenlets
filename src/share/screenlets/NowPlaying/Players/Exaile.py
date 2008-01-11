#!/usr/bin/env python

# Exaile API 

import os
import dbus
import string
import gobject
from GenericPlayer import GenericAPI

#EXAILE = {'DBUS_NAME':'org.exaile.DBusInterface','DBUS_OBJECT':'/DBusInterfaceObject', \
#			'DBUS_TITLE':'get_title()','DBUS_ALBUM':'get_album()', \
#			'DBUS_ARTIST':'get_artist()','DBUS_ART':'get_cover_path()',\
#			'DBUS_PLAYING':'query()','PLAY_WORD':'playing'}

class ExaileAPI(GenericAPI):
	__name__ = 'Exaile API'
	__version__ = '0.0'
	__author__ = 'vrunner'
	__desc__ = 'API to the Exaile Music Player'

	ns = "org.exaile.DBusInterface"
	iroot = "/DBusInterfaceObject"
	iface = "org.exaile.DBusInterface"

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
		return self.playerAPI.get_title()
	
	def get_album(self):
		return self.playerAPI.get_album()

	def get_artist(self):
		return self.playerAPI.get_artist()

	def get_cover_path(self):
		return self.playerAPI.get_cover_path()

	def is_playing(self):
		if self.now_playing() == "": return False
		else: return True

	def play_pause(self):
		self.playerAPI.play()

	def next(self):
		self.playerAPI.next_track()

	def previous(self):
		self.playerAPI.prev_track()

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for Banshee, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)

	def info_changed(self, signal=None):
		if self.__timeout:
			gobject.source_remove(self.__timeout)

		try:
			# Only call the callback function if Data has changed
			if self.__curplaying != None and not self.is_playing():
				self.__curplaying = None
				self.callback_fn()

			nowplaying = self.now_playing()
			if self.is_playing() and self.__curplaying != nowplaying:
				self.__curplaying = nowplaying
				self.callback_fn()
			self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		except:
			# The player exited ? call callback function
			self.callback_fn()
			pass


	def now_playing(self):
		return self.get_artist()+self.get_title()
