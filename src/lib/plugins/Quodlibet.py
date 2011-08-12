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

#  Quodlibet API (c) Whise (Helder Fraga) 2008 <helder.fraga@hotmail.com>


import os
import dbus
from GenericPlayer import GenericAPI
import urllib
from urlparse import urlparse

class QuodlibetAPI(GenericAPI):
	__name__ = 'Quodlibet'
	__version__ = '0.1'
	__author__ = 'Whise'
	__desc__ = 'API to the Quodlibet Music Player'

	ns = "net.sacredchao.QuodLibet"
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
		proxy_obj1 = self.session_bus.get_object(self.ns, '/net/sacredchao/QuodLibet')
	#	proxy_obj2 = self.session_bus.get_object(self.ns, '/org/gnome/Rhythmbox/Shell')
		self.playerAPI = dbus.Interface(proxy_obj1, self.ns)
		#self.shellAPI = dbus.Interface(proxy_obj2, self.ns+".Shell")

	def get_title(self):
		try:
			return self.playerAPI.CurrentSong()['title']
		except:
			return ''
	def get_album(self):
		try:
			return self.playerAPI.CurrentSong()['album']
		except:
			return ''

	def get_artist(self):
		try:
			return self.playerAPI.CurrentSong()['artist']
		except:
			return ''

	# **MUST HAVE** the "COVER ART" Plugin enabled
	# (or the "Art Display-Awn" Plugin)
	
	def get_cover_path(self):
		# Return the Expected Path (will be ignored by NowPlaying if it doesn't
		# exist
		coverFile = os.environ["HOME"] + "/.quodlibet/current.cover"
		if os.path.isfile(coverFile):
			return coverFile
		else:
			current = os.environ["HOME"] + "/.quodlibet/current"
			f = open(current, "r")
			tmp = f.readlines(200)
			f.close()
			for line in tmp:
				if line.startswith('~filename'):
					t = line.replace('~filename=','')
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

	def is_playing(self):
		if self.get_title() != '': return True
		else: return False

	def play_pause(self):
		self.playerAPI.PlayPause()

	def next(self):
		self.playerAPI.Next()

	def previous(self):
		self.playerAPI.Previous ()

	def register_change_callback(self, fn):
		if(self.callback_fn == None):
			#print "Registering Callback"
			self.callback_fn = fn
			self.playerAPI.connect_to_signal("SongStarted", self.info_changed)
			self.playerAPI.connect_to_signal("SongEnded", self.info_changed)
			#self.playerAPI.connect_to_signal("playingSongPropertyChanged", self.info_changed)

	# Internal Functions
#	def getProperty(self, name):
##		try:
#			val = self.shellAPI.getSongProperties(self.playerAPI.getPlayingUri())[name]
#			return val
#		except:
#			return None
#
	def info_changed(self, *args, **kwargs):
		self.callback_fn()

