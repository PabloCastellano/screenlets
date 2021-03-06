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
#
# Rythmbox API 

import os
import dbus
from GenericPlayer import GenericAPI
import urllib
from urlparse import urlparse

class RhythmboxAPI(GenericAPI):
	__name__ = 'Rhythmbox'
	__version__ = '0.0'
	__author__ = 'vrunner'
	__desc__ = 'API to the Rhythmbox Music Player'

	ns = "org.gnome.Rhythmbox"
	playerAPI = None
	shellAPI = None

	callback_fn = None

	# Extended Functions from the GenericAPI

	def __init__(self, session_bus):
		GenericAPI.__init__(self, session_bus)

	def is_active(self, dbus_iface):
		if self.ns in dbus_iface.ListNames(): return True
		else: return False

	def connect(self):
		proxy_obj1 = self.session_bus.get_object(self.ns, '/org/gnome/Rhythmbox/Player')
		proxy_obj2 = self.session_bus.get_object(self.ns, '/org/gnome/Rhythmbox/Shell')
		self.playerAPI = dbus.Interface(proxy_obj1, self.ns+".Player")
		self.shellAPI = dbus.Interface(proxy_obj2, self.ns+".Shell")

	def get_title(self):
		tmp = self.getProperty('rb:stream-song-title')
		if tmp: return tmp
		else: return self.getProperty('title')
	
	def get_album(self):
		tmp = self.getProperty('rb:stream-song-album')
		if tmp: return tmp
		else: return self.getProperty('album')

	def get_artist(self):
		tmp = self.getProperty('rb:stream-song-artist')
		if tmp: return tmp
		else: return self.getProperty('artist')

	# **MUST HAVE** the "COVER ART" Plugin enabled
	# (or the "Art Display-Awn" Plugin)
	
	def get_cover_path(self):
		# Return the Expected Path (will be ignored by NowPlaying if it doesn't
		# exist

		coverFile = self.getProperty('rb:coverArt-uri')
		if coverFile != None:
			if os.path.isfile(coverFile):
				return coverFile
			
		coverFile = os.environ['HOME']+"/.cache/rhythmbox/covers/"+self.get_artist()+" - "+self.get_album()+".jpg"
		if not os.path.isfile(coverFile):
			baseURL = urlparse( urllib.url2pathname( self.playerAPI.getPlayingUri() ) )
			basePath = os.path.dirname( baseURL.path )
			names = ['Album', 'Cover', 'Folde']
			for x in os.listdir(basePath):
				if os.path.splitext(x)[1] in [".jpg", ".png"] and (x.capitalize()[:5] in names):
					coverFile = basePath + '/' + x
					return coverFile
 		return coverFile
 


	def is_playing(self):
		try:
			test_playing = self.playerAPI.getPlaying()
			if self.playerAPI.getPlaying() == 1: return True
			else: return False
		except DBusException:
			return False

	def play_pause(self):
		if self.is_playing:
			self.playerAPI.playPause(False)
		else:
			self.playerAPI.playPause(True)

	def next(self):
		self.playerAPI.next()

	def previous(self):
		self.playerAPI.previous()

	def register_change_callback(self, fn):
		if(self.callback_fn == None):
			#print "Registering Callback"
			self.callback_fn = fn
			self.playerAPI.connect_to_signal("playingChanged", self.info_changed)
			self.playerAPI.connect_to_signal("playingUriChanged", self.info_changed)
			self.playerAPI.connect_to_signal("playingSongPropertyChanged", self.info_changed)

	# Internal Functions
	def getProperty(self, name):
		try:
			val = self.shellAPI.getSongProperties(self.playerAPI.getPlayingUri())[name]
			return val
		except:
			return None

	def info_changed(self, *args, **kwargs):
		self.callback_fn()

