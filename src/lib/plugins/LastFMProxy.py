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

# LastFMProxy API by atie

import os
import string
import gobject
import mpdclient2
import urllib2
from GenericPlayer import GenericAPI

class LastFMProxyAPI(GenericAPI):
	__name__ = 'LastFMProxy API'
	__version__ = '0.0'
	__author__ = 'atie'
	__desc__ = 'LastFMProxy API to a Music Player'

	playerAPI = None

	__timeout = None
	__interval = 3

	callbackFn = False
	__curplaying = None

	def __init__(self, session_bus):
		# Ignore the session_bus. Initialize a mpdclient connection
		GenericAPI.__init__(self, session_bus)
	
	# Check if the player is active : Returns Boolean
	# A handle to the dbus interface is passed in : doesn't need to be used
	def is_active(self, dbus_iface):
		app = mpdclient2.connect()
		if not app: return False
		else: 
			proc = os.popen("""ps axo "%p,%a" | grep "last" | grep -v grep|cut -d',' -f1""").read()
			procs = proc.split('\n')
			if len(procs) > 1:
				return True
			else:
				return False


	# Make a connection to the Player
	def connect(self):
		self.playerAPI = mpdclient2.connect()
		
	# Get LastFMProxy dump
	def getdump(self):
		try:
			dump = urllib2.urlopen('http://localhost:1881/np').read()
		except urllib2.HTTPError, e:
			print "Cannot retrieve URL: HTTP Error Code", e.code
		except urllib2.URLError, e:
			print "Cannot retrieve URL: " + e.reason[1]
		return dump	
		
	def getBetween(self, dump, first, last):
		x = len(first)
		begin = dump.find(first) +x
		end = dump.find(last, begin)
		return dump[begin:end]

	# The following return Strings
	# FIXME, maybe.
	def get_title(self):
		#return getattr(self.playerAPI.currentsong(), 'np_title = ', ';')
		dump = self.getdump()
		return self.getBetween(dump, 'np_title = \'', '\';')
	
	# FIXME if necessary
	def get_album(self):
		dump = self.getdump()
		return self.getBetween(dump, 'np_album = \'', '\';')
    
	# FIXME if necessary
	def get_artist(self):
		dump = self.getdump()
		return self.getBetween(dump, 'np_creator = \'', '\';')
    
    # FIXME, if necessary, currently by the amazoncoverartsearch 
	def get_cover_path(self):
		#return os.environ['HOME']+"/.covers/"+self.get_artist()+\
        # " - "+self.get_album()+".jpg"
		#return ""
		# No need to search Amazon, one image file for now playing
		#path = os.environ['HOME']+"/.covers/image_by_lfproxy.jpg"
		path = os.environ['HOME']+"/.covers/"+self.get_artist()+\
         " - "+self.get_album()+".jpg"
		dump = self.getdump()
		f = open(path, 'wb')
		image = urllib2.urlopen(self.getBetween(dump, 'np_image = \'',
		'\'')).read()
		f.write(image)
		f.close()
		return path


	# Returns Boolean
	def is_playing(self):
		if self.playerAPI.status().state in ['play']:
			return True
		else: return False

	# The following do not return any values
	def play_pause(self):
		self.playerAPI.pause(1)

	def next(self):
		self.playerAPI.next()

	def previous(self):
		self.playerAPI.previous()

	def register_change_callback(self, fn):
		self.callback_fn = fn
		# Could not find a callback signal for mpd, so just calling after some time interval
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
		#self.playerAPI.connect_to_signal("playingUriChanged", self.info_changed)

	def info_changed(self, signal=None):
		# Only call the callback function if Data has changed
		if self.__curplaying != getattr(self.playerAPI.currentsong(),
		'title', ''):
			self.__curplaying = getattr(self.playerAPI.currentsong(), 'title', '')
			self.callback_fn()

		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)

