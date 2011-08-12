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

#  Sonata API (c) Whise (Helder Fraga) 2008 <helder.fraga@hotmail.com>


import os
import dbus
import gobject
import mpdclient2
from GenericPlayer import GenericAPI

class SonataAPI(GenericAPI):
    __name__ = 'Sonata API'
    __version__ = '0.0'
    __author__ = ''
    __desc__ = ''


    playerAPI = None

    __timeout = None
    __interval = 2

    callbackFn = None
    __curplaying = None


    ns = "org.MPD.Sonata"
    iroot = "/org/MPD/Sonata"
    iface = "org.MPD.SonataInterface"

    host = 'localhost'
    port = 6600
    musicdir = '/media/MULTIMEDIA/music/'

    def __init__(self, session_bus):
        GenericAPI.__init__(self, session_bus)
    
    # Check if the player is active : Returns Boolean
    # A handle to the dbus interface is passed in : doesn't need to be used
    # if there are other ways of checking this (like dcop in amarok)
    def is_active(self, dbus_iface):
        if self.ns in dbus_iface.ListNames(): return True
        else: return False

    # Make a connection to the Player
    def connect(self):
        proxy_obj = self.session_bus.get_object(self.ns, self.iroot)
        self.playerAPI = dbus.Interface(proxy_obj, self.iface)    

    # The following return Strings
    def get_title(self):
	song = mpdclient2.connect().currentsong()
        return song.title
    
    def get_album(self):
	song = mpdclient2.connect().currentsong()
        return song.album

    def get_artist(self):
	song = mpdclient2.connect().currentsong()
        return song.artist

    def get_cover_path(self):
                artist = self.get_artist()
                album = self.get_album()
                filename = os.path.expanduser("~/.covers/" + artist + "-" + album + ".jpg")
                if os.path.isfile(filename):
                        return filename

		try:
			t = mpdclient2.connect().currentsong().file
			t = t.replace('file://','')
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
		except: return ''
                return ''
                

    # Returns Boolean
    def is_playing(self):
                status = mpdclient2.connect().status()
                return (status.state != 'stop')

    # The following do not return any values
    def play_pause(self):
                status = mpdclient2.connect().status()
                if status.state == 'play':
                        mpdclient2.connect().pause(1)
                elif status.state == 'pause':
                        mpdclient2.connect().pause(0)
                else:
                        mpdclient2.connect().play()

    def next(self):
        mpdclient2.connect().next()

    def previous(self):
        mpdclient2.connect().previous()

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

            playinguri = self.get_title()
            if self.is_playing() and self.__curplaying != playinguri:
                self.__curplaying = playinguri
                self.callback_fn()
            self.__timeout = gobject.timeout_add(self.__interval * 1000, self.info_changed)
        except:
            # The player exited ? call callback function
            self.callback_fn()
