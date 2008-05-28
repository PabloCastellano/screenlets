#!/usr/bin/env python

#  NowPlayingScreenlet by magicrobomonkey
#  - Modified by vrunner to be more extensible
#
# INFO:
# - a simple viewer for currently playing 
# 
# TODO:
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import screenlets
from screenlets.options import StringOption, IntOption, BoolOption
import cairo
import dbus
import pango
import gtk
import gobject
import os.path
import sys
import re
import traceback
from screenlets import Plugins

#from dbus.mainloop.glib import DBusGMainLoop
import dbus.glib

# Get the ScreenletPath
ScreenletPath = sys.path[0]

# Add the Player Modules Path
#sys.path.append(ScreenletPath+'/Players')

# Add the Amazon Cover search Path
#sys.path.append(ScreenletPath+'/amazon')
CoverSearch = Plugins.importAPI('CoverSearch')

# Add the UI Module
sys.path.append(ScreenletPath+'/UI')
import Theme 

DBUS_NAME = "org.freedesktop.DBus"
DBUS_OBJECT = "/org/freedesktop/DBus"

# List of ModuleName:ClassName pairs
PLAYER_LIST = {'Rhythmbox':'RhythmboxAPI',
                    'Listen':'ListenAPI',
                    'Banshee':'BansheeAPI',
                    'Amarok':'AmarokAPI',
                    'Exaile':'ExaileAPI',
                    'Sonata':'SonataAPI',
                    'Kaffeine':'KaffeineAPI',
                    'Quodlibet':'QuodlibetAPI',
                    'Songbird':'SongbirdAPI',}

PLAYER_LIST_LAUNCH = ['rhythmbox','listen','banshee','amarok','exaile','sonata','quodlibet','songbird','kaffeine']
# The Screenlet
class NowPlayingScreenlet(screenlets.Screenlet):
	"""Shows Song Info"""
	
	# default meta-info for Screenlets
	__name__ = 'NowPlayingScreenlet'
	__version__ = '0.3'
	__author__ = 'magicrobotmonkey modified by Whise'
	__desc__ = 'A screenlet to show what\'s currently playing '+\
		'(and probably eventually control it) '
	
	player = False
	player_type = False
	playing = False
	cover_path = False

	play_pause_button = False
	prev_button = False

	skin = False

	coverEngine = None

	__timeout = None
	check_interval = 5 # i.e. every 5 seconds, check for a player

	__scroll_timeout = None
	scroll_interval = 300 # scroll every 300 milliseconds by default

	# Sometimes the cover fetch takes time, so wait for it
	__cover_timeout = None
	__cover_check_interval = 1 # i.e. every 2 seconds
	__num_times_cover_checked = 0
	__max_cover_path_searches = 2 # Check 3 times

	__buffer_back = None

	session_bus = None

	player_list = []
	player_start = True
	player_close = True
	default_player = ''
	default_player_old = ''
	# constructor
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, uses_theme=True,width=int(700), height=int(700), **keyword_args)

		#init dbus
		self.dbus_connect()
		# Set the Player List
		self.init_player_list()
		# set theme
		self.theme_name = "default"

		# Options
		self.add_options_group('Scrolling', 'Scroll-specific settings.')
		self.add_option(IntOption('Scrolling', 'scroll_interval',
			self.scroll_interval, 'Scroll Time (ms)', 
			'How quickly to scroll long titles ? The smaller the value the faster it is, and more CPU usage',min=50, max=5000))
		self.add_options_group('Player', 'Player settings.')
		self.add_option(BoolOption('Player', 'player_start',
			self.player_start, 'Start Player when Screenlet starts?', 
			'Start Player when Screenlet starts?'))
		self.add_option(StringOption('Player', 'default_player',
			self.default_player, 'Player to Launch', 
			'Player that starts when screenlet starts?(restart required)',choices=PLAYER_LIST_LAUNCH))
		self.add_option(BoolOption('Player', 'player_close',
			self.player_close, 'Close Player when Screenlet quits?', 
			'Start Player when Screenlet quits?'))
		# Check for Players
		self.check_for_players()
		# Init the timeout function to regularly check for players
		self.check_interval = self.check_interval

	def __setattr__(self, name, value):
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == "check_interval":
			if value > 0:
				self.__dict__['check_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(value * 1000, self.check_for_players)
			else:
				pass
		if name == "scroll_interval":
			if value > 0:
				self.__dict__['scroll_interval'] = value
				if self.__scroll_timeout:
					gobject.source_remove(self.__scroll_timeout)
				self.__scroll_timeout = gobject.timeout_add(value, self.update)
			else:
				pass
		if name == "scale":
			try:
				if value >= 1.4 : value = 1.4
				Theme.Skin.set_scale(skinxml,self.scale)

			except:
				pass

	def menuitem_callback(self, widget, id):
		screenlets.Screenlet.menuitem_callback(self, widget, id)
		if id=="playpause":
			try:
				if self.player: self.play_pause_wrapped()
			except:pass
		elif id=="next":
			try:
				if self.player: self.player.next()
			except:pass
		elif id=="previous":
			try:
				if self.player: self.player.previous()
			except:pass
		elif id=="get_skins":
			os.system('xdg-open http://gnome-look.org/content/show.php/Now+playing+Screenlet+theme+pack?content=74123')

	def on_load_theme(self): 
		
		skinxml = ScreenletPath+'/themes/'+self.theme_name+"/skin.xml"
		if os.path.exists(skinxml):
			if self.skin: self.skin.cleanup()
			self.skin = Theme.Skin(skinxml, self)
			self.width = self.skin.width
			self.height = self.skin.height
			self.set_player_callbacks()
			self.get_info()
			self.scale = self.scale
			self.skin.set_scale(self.scale)

				
			# Draw it all to a buffer
			if self.has_started:
				self.init_buffers()
				self.redraw_background_items()
			#self.scale = self.scale
				self.fullupdate()
			#if self.scale >= 1.41:
			#	self.scale = 1.40
			#	self.redraw_canvas()
			self.window.show_all()
	def on_init(self):
		#helps to load the buttons properly
			if self.default_player == '' : self.default_player = 'rhythmbox'
			print self.default_player
			self.default_player_old = self.default_player
			if self.default_player != '' and self.player_start == True:
				if self.default_player == 'amarok':
					os.system((self.default_player) +  '  \n')
				else:
					os.system((self.default_player) +  '  &')
	
			print "Screenlet has been initialized."
			# add default menuitems
			self.add_menuitem("playpause", "Play/Pause")
			self.add_menuitem("next", "Next")
			self.add_menuitem("previous", "Previous")
			self.add_menuitem("get_skins", "Get More Skins")
			self.add_default_menuitems()
			self.on_load_theme()

	def on_scale(self):
		if self.window:
			if self.skin: self.skin.set_scale(self.scale)
			self.init_buffers()
			self.redraw_background_items()
		self.redraw_canvas()
		if self.has_started:self.window.show_all()

	def on_quit(self):
		if self.default_player_old != '' and self.player_close == True:
			if self.default_player_old == 'amarok':
				os.system('dcop amarok playlist saveCurrentPlaylist &')
				os.system((self.default_player_old) + ' -s \n')
				os.system((self.default_player_old) + ' --exit  \n')
			else:
				os.system((self.default_player_old) + ' --quit &')
	def init_buffers(self):
		self.__buffer_back = gtk.gdk.Pixmap(self.window.window, 
			int(self.width * self.scale), int(self.height * self.scale), -1)
		
	def redraw_background_items(self):
		if not self.__buffer_back: return
		ctx_ns = self.__buffer_back.cairo_create()
		self.clear_cairo_context(ctx_ns)
		ctx_ns.scale(self.scale, self.scale)

		playing = False
		#print "---drawing background-ish items---"
		if self.player and self.player.is_playing(): playing = True 
		if self.theme and self.skin:
			for item in self.skin.items:
				try:
					if item.regular_updates: continue # Omit items that need regular updating
				except:
					pass
				if playing and item.display=="on-stopped": pass
				elif not playing and item.display=="on-playing": pass
				else: 
					#print item
					item.draw(ctx_ns)
	
	def dbus_connect(self):
		self.session_bus = dbus.SessionBus()
		dbus_object = self.session_bus.get_object(DBUS_NAME, DBUS_OBJECT)
		self.dbus_iface = dbus.Interface(dbus_object, DBUS_NAME)
		#self.dbus_iface.connect_to_signal("NameOwnerChanged", self._callback)
		#self.session_bus.add_signal_reciever(self._callback)#,LISTEN_NAME
		#print self.dbus_iface
		#print self.session_bus

	def init_player_list(self):
		for module,cls in PLAYER_LIST.iteritems():
			try: 
				
				mod = Plugins.importAPI(module)
				self.player_list.append(eval("mod."+cls+"(self.session_bus)"))
			except:
				print sys.exc_value
				print "Could not load "+cls+" API"
		
	def fullupdate(self):
		self.redraw_background_items()
		self.redraw_canvas()

	def update(self):
		#print "update called"
		self.redraw_canvas()
		#self.update_shape()
		return True
	
	def check_for_players(self):
		gobject.idle_add(self.dbus_check_player)
		return True

	def dbus_check_player(self):
		#first check if the current player is playing
		if self.player and self.player.is_active(self.dbus_iface):
			return

		#if we're here, our player wasnt in the list, so kill it
		self.player = False
		self.unset_player_callbacks()
		#print "no player yet.. looking for one"

		#now check all the rest
		for i,player in enumerate(self.player_list):
			if player and player.is_active(self.dbus_iface):
				print "Found a player "+player.__class__.__name__
				self.player = player
				self.player.connect()
				self.skin.set_player(self.player.__class__.__name__)
				self.get_info()
				print "Setting callbacks"
				try:
					self.player.callback_fn = None
					self.player.register_change_callback(self.get_info)
					self.set_player_callbacks()
				except AttributeError:
					pass

	def check_playing(self):
		if self.player:
			try:
				self.playing = self.player.is_playing()
				return self.playing
			except:pass
		self.playing = False
		return self.playing

	def set_cover_cb(self, path):
		if path and os.path.exists(path):
			#print "Setting cover"
			self.cover_path = path
			pixbuf = gtk.gdk.pixbuf_new_from_file(self.cover_path)
			if self.skin: 
				self.skin.set_albumcover(pixbuf)
		else: self.cover_path = False

	def cover_update_cb(self):
		if self.__cover_timeout:
			gobject.source_remove(self.__cover_timeout)
		if self.coverEngine.isAlive():
			self.__cover_timeout = gobject.timeout_add(200, self.cover_update_cb)
			return
		#print "Thread done, update"
		if self.cover_path:
			self.fullupdate()
		
			
	def check_for_cover_path(self):
		if self.check_playing():
			#print "checking for cover path "
			self.cover_path = self.player.get_cover_path()
			try :
				a = os.path.exists(self.cover_path)
			except: 
				if self.__num_times_cover_checked < self.__max_cover_path_searches:
					if self.__cover_timeout:
						gobject.source_remove(self.__cover_timeout)
					self.__cover_timeout = gobject.timeout_add(self.__cover_check_interval * 1000, 
						self.check_for_cover_path)
					self.__num_times_cover_checked += 1
				else:
					if self.__cover_timeout:
						gobject.source_remove(self.__cover_timeout)
					self.__num_times_cover_checked = 0
					# Cannot get it from the Player, try to retreive it yourself
					artist = self.player.get_artist()
					album = self.player.get_album()
					if artist and album:
						# Need to make this a thread
						self.coverEngine = CoverSearch.CoverSearch()
						self.coverEngine.initData(artist, album, self.set_cover_cb)
						self.coverEngine.start()
						self.__cover_timeout = gobject.timeout_add(200, self.cover_update_cb)
				return False
			if os.path.exists(self.cover_path):
				if self.__cover_timeout:
					gobject.source_remove(self.__cover_timeout)
				self.__num_times_cover_checked = 0
				pixbuf = gtk.gdk.pixbuf_new_from_file(self.cover_path)
				if self.skin: 
					self.skin.set_albumcover(pixbuf)
				self.fullupdate()
				#print "Found Something !"
				return True
			else:
				#print "bummer cover path doesn't exist .. lets try to search again if we can"
				if self.__num_times_cover_checked < self.__max_cover_path_searches:
					if self.__cover_timeout:
						gobject.source_remove(self.__cover_timeout)
					self.__cover_timeout = gobject.timeout_add(self.__cover_check_interval * 1000, 
						self.check_for_cover_path)
					self.__num_times_cover_checked += 1
				else:
					if self.__cover_timeout:
						gobject.source_remove(self.__cover_timeout)
					self.__num_times_cover_checked = 0
					# Cannot get it from the Player, try to retreive it yourself
					artist = self.player.get_artist()
					album = self.player.get_album()
					if artist and album:
						# Need to make this a thread
						self.coverEngine = CoverSearch.CoverSearch()
						self.coverEngine.initData(artist, album, self.set_cover_cb)
						self.coverEngine.start()
						self.__cover_timeout = gobject.timeout_add(200, self.cover_update_cb)
				return False
		elif self.__cover_timeout:
			gobject.source_remove(self.__cover_timeout)
			
				
	def get_info(self):
		#print "Getting info.."
		s = self.skin
		if s:
			try:
				if self.check_playing():
					s.set_player(self.player.__class__.__name__)
					s.set_title(self.player.get_title())
					s.set_artist(self.player.get_artist())
					s.set_album(self.player.get_album())
					if not self.check_for_cover_path():
						s.set_albumcover(None)
					self.fullupdate()
				else:
					s.set_title("")
					s.set_artist("")
					s.set_album("")
					s.set_albumcover(None)
					self.fullupdate()
			except:
				print "Player exited"
				print sys.exc_value
				traceback.print_exc(file=sys.stdout)
				# The player most probably exited. Invalidate the Player
				s.set_player("")
				s.set_title("")
				s.set_artist("")
				s.set_album("")
				s.set_albumcover(None)
				self.player = False
				self.fullupdate()

	def set_player_callbacks(self):
		if self.player and self.skin and self.skin.playercontrols_item:
			c = self.skin.playercontrols_item
			if c.prev_button:
				c.prev_button.set_callback_fn(self.player.previous)
			if c.play_pause_button:
				c.play_pause_button.set_callback_fn(self.play_pause_wrapped)
			if c.next_button:
				c.next_button.set_callback_fn(self.player.next)
			
	def play_pause_wrapped(self):
		if self.player:
			if self.skin and self.skin.playercontrols_item:
				c = self.skin.playercontrols_item
				image = "pause"
				if self.player.is_playing(): image = "play"
				c.set_images("play_pause", image)
			self.player.play_pause()
		
	def unset_player_callbacks(self):
		if self.player and self.skin and self.skin.playercontrols_item:
			c = self.skin.playercontrols_item
			if c.prev_button:
				c.prev_button.set_callback_fn(None)
			if c.play_pause_button:
				c.play_pause_button.set_callback_fn(None)
			if c.next_button:
				c.next_button.set_callback_fn(None)

	def on_draw(self, ctx):
		# Draw Non-Scrolling (not-regularly updated) Items from the Buffer
		#print "drawing stuff"
		if self.__buffer_back:
			ctx.set_operator(cairo.OPERATOR_OVER)
			ctx.set_source_pixmap(self.__buffer_back, 0, 0)
			ctx.paint()
		#print "drawn buffer back"

		# set scale rel. to scale-attribute
		ctx.scale(self.scale, self.scale)
		#print "---drawing regularly updated items---"
		# Draw Items that need regular updates (like scrolling text)
		playing = False
		try:
			if self.player and self.player.is_playing(): playing = True 
		except: playing = False
		if self.theme and self.skin:
			needUpdates = False
			for item in self.skin.items:
				try:
					if item.regular_updates: # Only draw items here that require regular updates
						if playing and item.display=="on-stopped": pass
						elif not playing and item.display=="on-playing": pass
						else: 
							# Need items to be updated - Set a timeout
							#print "drawing "+item.type
							needUpdates = True
							item.draw(ctx)
				except:
					continue

			if self.__scroll_timeout:
				gobject.source_remove(self.__scroll_timeout)
			if needUpdates:
				self.__scroll_timeout = gobject.timeout_add(int(self.scroll_interval), self.update)

	def on_draw_shape(self, ctx):
		#print "here"
		ctx.scale(self.scale, self.scale)
		ctx.set_source_rgba(1,1,1,1)
		ctx.rectangle(0,0,self.width,self.height)
		ctx.paint()

	def close(self):
		#print "here"
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		if self.__cover_timeout:
			gobject.source_remove(self.__cover_timeout)
		screenlets.Screenlet.close(self)
	
        
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(NowPlayingScreenlet)

