#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#
#RadioScreenlet (c) Whise <helder.fraga@hotmail.com>

from screenlets import DefaultMenuItem
from screenlets.options import BoolOption, StringOption, FontOption, ListOption, IntOption
import Mplayer
import cairo
import pango
import screenlets
import gobject
import sys
import gtk

STREAM_TITLE_MAX_LENGTH = 32

class RadioScreenlet(screenlets.Screenlet):
	"""A Radio Streaming Screenlet."""
	
	# default meta-info for Screenlets
	__name__ = 'RadioScreenlet'
	__version__ = '0.4'
	__author__ = 'Helder Fraga aka Whise (c) 2007'
	__desc__ = 'A Radio Streaming Screenlet , you can add more radios on the menu.xml file , see inside on how to, this version requires Mplayer installed with codecs and no longuer gstreamer , plays http, mms, rtsp , rm ,ram and others'
	__timeout = 1000
	playing = False
	pipe = None
	but1 = ''
	but2 = ''
	password = 'http://80.65.234.120:8000/ Frequence 3'
	
	p_layout = None
	mplayer = None
	
	__titleScrollSpeedLabels = ["Slow", "Medium", "Fast"]
	__titleScrollSpeeds = [1000, 500, 250]
	streamTitle = ""
	displayedStreamTitle = ""
	scrollTimestep = 500
	scrollLoopTimerHandle = 0
	enableTitleScroll = True
	streamTitleScrollIndex = 0
	streamTitleScrollForward = True
	mypath = sys.argv[0][:sys.argv[0].find('RadioScreenlet.py')].strip()
	stationList = ();
	
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=100, uses_theme=True, **keyword_args) 
		
		self.theme_name = "default"
		self.add_default_menuitems(DefaultMenuItem.XML)

		self.pipe = None
		self.add_options_group('Radio', 'Settings')
		self.add_option(StringOption('Radio', 'password', 
			self.password, 'radio', 
			'Radio stream address <space> radio name',), realtime=False)
		self.add_option(BoolOption('Radio', 'enable_title_scroll', self.enableTitleScroll,
			'Scroll title', 'Have song titles that are too long scroll across the display'), realtime=True)
		self.add_option(StringOption('Radio', 'title_scroll_speed', "Medium",
			'Title Scroll Speed', 'How fast the title will scroll',
			choices = self.__titleScrollSpeedLabels), realtime=True)
				
		#self.player = gst.element_factory_make("playbin", "player")
		#fakesink = gst.element_factory_make('fakesink', "my-fakesink")
		#self.player.set_property("video-sink", fakesink)
		#bus = self.player.get_bus()
		#bus.add_signal_watch()
		#bus.connect('message', self.on_message)
		self.password = self.password
		password = self.password
		
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'password':
			screenlets.Screenlet.__setattr__(self, name, value)
			self.redraw_canvas()
		elif name == 'title_scroll_speed':
			self.scrollTimestep = self.__titleScrollSpeeds[self.__titleScrollSpeedLabels.index(value)]
			self.stopScrollLoop()
			self.startScrollLoop()
		elif name == 'enable_title_scroll':
			self.enableTitleScroll = value
			if self.enableTitleScroll:
				self.startScrollLoop()
			else:
				self.stopScrollLoop()
				self.scrollTitleHandler()
				self.redraw_canvas()

	#
	#  Makes the stream title scroll by if it's too long
	#
	def scrollTitleHandler(self):
		if len(self.streamTitle) > STREAM_TITLE_MAX_LENGTH and self.enableTitleScroll:
			startIndex = self.streamTitleScrollIndex
			endIndex = self.streamTitleScrollIndex + STREAM_TITLE_MAX_LENGTH
			self.displayedStreamTitle = self.streamTitle[startIndex:endIndex]
			self.redraw_canvas()
			
			if self.streamTitleScrollForward and len(self.streamTitle) > self.streamTitleScrollIndex + STREAM_TITLE_MAX_LENGTH:
				self.streamTitleScrollIndex = self.streamTitleScrollIndex + 1
			elif not self.streamTitleScrollForward and 0 < self.streamTitleScrollIndex:
				self.streamTitleScrollIndex = self.streamTitleScrollIndex - 1
			else: #switch directions and "pause" when we reach the end in our current direction
				self.streamTitleScrollForward = not self.streamTitleScrollForward
				if self.streamTitleScrollForward:
					self.streamTitleScrollIndex = 0
				else:
					self.streamTitleScrollIndex = len(self.streamTitle) - STREAM_TITLE_MAX_LENGTH
		else:
			self.displayedStreamTitle = self.streamTitle
			
		return True
	def startScrollLoop(self):
		if self.scrollLoopTimerHandle == 0:
			self.scrollLoopTimerHandle = gobject.timeout_add(self.scrollTimestep, self.scrollTitleHandler)
	def stopScrollLoop(self):
		if self.scrollLoopTimerHandle:
			gobject.source_remove(self.scrollLoopTimerHandle)
		self.scrollLoopTimerHandle = 0
	
	#def on_mouse_down(self, event):
		# do the active button's action
	#	if event.button == 1:
	#		self.gen()
	def start_stop(self):
		if self.mplayer == None:
			self.mplayer = Mplayer.Mplayer(self)
			self.mplayer.addStreamTitleChangeListener(self.handleStreamTitleChange)
			
		#if self.button.get_label() == "Start":
		#	filepath = self.entry.get_text()
			#if os.path.exists(filepath):
			#self.button.set_label("Stop")
		try:
			self.mplayer.close()
		except Exception, ex:
			print 'sdfsdf'
		finally:
			self.stopScrollLoop()
			
		ta = self.password
		
		ta = ta[:ta.find(' ') ].strip()

		if ta[len(ta)-3:] == 'ram' or ta[len(ta)-3:] == 'Ram' or ta[len(ta)-2:] == 'rm' or ta[len(ta)-3:] == 'RAM' or ta[len(ta)-2:] == 'RM' or ta[len(ta)-4:] == 'rmvb' or ta[len(ta)-3:] == 'm3u' or ta[len(ta)-3:] == 'pls' or ta[len(ta)-3:] == 'asx':
			ta = ' -playlist ' + ta
			print 'PLEASE WAIT , REAL MEDIA STREAMS TAKE A WHILE TO LOAD'

		if ta[:len(' http://www.minist')] == 'http://www.ministr':
			
			ta = ' -playlist ' + ta
			print 'PLEASE WAIT , REAL MEDIA STREAMS TAKE A WHILE TO LOAD'
		print ta
		self.mplayer.play(ta)
		self.startScrollLoop()
				#self.player.set_state(gst.STATE_PLAYING)
	
	def handleStreamTitleChange(self, source, newStreamTitle):
		print "Stream title changed: " + newStreamTitle
		self.streamTitle = newStreamTitle
		self.displayedStreamTitle = self.streamTitle
		self.redraw_canvas()
		
		self.streamTitleScrollIndex = 0
		self.streamTitleScrollForward = True
		return True
	
	def send_command (self, command):
		try:
			self.mplayer.close()
		except:
			pass

		#retval = self.pipe.close()
		
	def stop(self):
		try:	
			self.mplayer.close()
		except Exception, ex:
			print 'sdfsdf'
		finally:
			self.stopScrollLoop()
		
							

	def on_quit(self):
		"""Called when a keypress-event occured in Screenlet's window."""
		self.send_command('quit')
	

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id[:4] == "http":
			self.password = id
			
			self.start_stop()
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()
		if id[:4] == "star":
			#self.password = id
			self.start_stop()
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()
		if id[:4] == "stop":
			#self.password = id
			self.send_command('quit')
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()
		if id[:3] == "mms":
			self.password = id
			
			self.start_stop()
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()

		if id[:4] == "rtsp":
			self.password = id
			
			self.start_stop()
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()
		if id[:3] == "add":
			dialog = gtk.Dialog("New radio stream", self.window)
			dialog.resize(300, 100)
			dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, 
				gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
			entrybox = gtk.Entry()
			entrybox.set_text('Stream url')
			dialog.vbox.add(entrybox)
			entrybox.show()	
			# run dialog
			response = dialog.run()
			if response == gtk.RESPONSE_OK:
				
				dialog1 = gtk.Dialog("New radio stream", self.window)
				dialog1.resize(300, 100)
				dialog1.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, 
					gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
				entrybox1 = gtk.Entry()
				entrybox1.set_text('Radio Name')
				dialog1.vbox.add(entrybox1)
				entrybox1.show()	
				# run dialog
				response = dialog1.run()
				if response == gtk.RESPONSE_OK:
					a = entrybox.get_text()
					b = entrybox1.get_text()
					f = open (self.mypath + 'menu.xml','r')
					tmp = f.read()
					xml = tmp
					tmp = tmp.replace('	<!-- Custom radios here -->','	<!-- Custom radios here -->\n'+'		<item label="'+b+'" id="' +a +' ' + b +'"/>')
					f.close()
					f = open (self.mypath + 'menu.xml','w')
					f.write(tmp)
					f.close()
				dialog1.hide()
			dialog.hide()
	def on_mouse_enter (self, event):
		print 'enter'
        
	def on_mouse_leave (self, event):
		print 'leave'
		
	def on_mouse_down(self,event):
		x = event.x / self.scale
		y = event.y / self.scale

		
		if event.button == 1 and y >= 50:
			if x <= 37 and x >= 5:
				self.but1 = '_press'			
				
				self.start_stop()
				self.redraw_canvas()
				return True
			elif x >= 40 and x <72:
				self.but2 = '_press'
				self.send_command('quit')
				self.redraw_canvas()
				return True
		
	def on_mouse_up(self,button):

		self.but1 = ''
		self.but2 = ''
		self.redraw_canvas()
		return True
	def on_draw(self, ctx):
		
		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			self.theme['background.svg'].render_cairo(ctx)
			self.theme['disk-glow.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'radio')
			
			ctx.save()
			ctx.translate(5, 5)
			if self.p_layout == None :
				self.p_layout = ctx.create_layout()
			else:
				ctx.update_layout(self.p_layout)
				
			p_fdesc = pango.FontDescription()
			p_fdesc.set_family_static("Free Sans")
			tb = self.password
			tb = tb[tb.find(" ")+1:]
			tb = tb[:11]

			p_fdesc.set_size(25 * pango.SCALE)
			
			self.p_layout.set_font_description(p_fdesc)
			self.p_layout.set_width((200) * pango.SCALE)
			self.p_layout.set_markup(tb)

			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.show_layout(self.p_layout)
			ctx.fill()
			
			p_fdesc = pango.FontDescription()
			p_fdesc.set_family_static("Free Sans")
			tc = self.displayedStreamTitle
			tc = tc[:STREAM_TITLE_MAX_LENGTH]

			p_fdesc.set_size(10 * pango.SCALE)
			
			self.p_layout.set_font_description(p_fdesc)
			self.p_layout.set_width((200) * pango.SCALE)
			self.p_layout.set_markup(tc)
			
			ctx.translate(0, 30)
			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.show_layout(self.p_layout)
			ctx.fill()
			
			ctx.restore()

			ctx.translate(5,50)
			self.theme.render(ctx, 'play'+ self.but1)
			ctx.translate(35,0)
			self.theme.render(ctx, 'stop'+ self.but2)
	def on_draw_shape(self,ctx):

		if self.theme:
			
			self.on_draw(ctx)

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(RadioScreenlet)
