# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


# Listen API by vrunner

import os
import dbus
import string
import gobject
from GenericPlayer import GenericAPI

#LISTEN = {'DBUS_NAME':'org.gnome.Listen','DBUS_OBJECT':'/org/gnome/listen', \
#			'DBUS_TITLE':'get_title()','DBUS_ALBUM':'get_album()', \
#			'DBUS_ARTIST':'get_artist()','DBUS_ART':'get_cover_path()',\
#			'DBUS_PLAYING':'playing()','PLAY_WORD':False}

class ListenAPI(GenericAPI):
	__name__ = 'Listen API'
	__version__ = '0.0'
	__author__ = 'vrunner'
	__desc__ = 'API to the Listen Music Player'

	ns = "org.gnome.Listen"
	iroot = "/org/gnome/listen"
	iface = "org.gnome.Listen"

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
		return self.playerAPI.current_playing().split(" - ",3)[0]
		#return self.playerAPI.get_title()
	
	def get_album(self):
		return self.playerAPI.current_playing().split(" - ",3)[1][1:]
		#return self.playerAPI.get_album()

	def get_artist(self):
		artist = self.playerAPI.current_playing().split(" - ",3)[2]
		return artist[0:len(artist)-1]
		#return self.playerAPI.get_artist()

	def get_cover_path(self):
		return os.environ['HOME']+"/.cache/listen/cover/"+\
			string.lower(self.get_album()+".jpg")
		#return self.playerAPI.get_cover_path()

	def is_playing(self):
		#if self.playerAPI.playing() == "False": return False
		if self.playerAPI.current_playing() == "": return False
		else: return True

	def play_pause(self):
		self.playerAPI.play_pause()

	def next(self):
		self.playerAPI.next()

	def previous(self):
		self.playerAPI.previous()

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for Listen, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		#self.playerAPI.connect_to_signal("playingUriChanged", self.info_changed)

	def info_changed(self, signal=None):
		# Only call the callback function if Data has changed
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		try:
			if self.__curplaying != self.playerAPI.current_playing():
				self.__curplaying = self.playerAPI.current_playing()
				self.callback_fn()

			self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		except:
			# The player exited ? call callback function
			self.callback_fn()

