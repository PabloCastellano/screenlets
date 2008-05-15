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
from screenlets.options import BoolOption, StringOption, FontOption, ListOption, IntOption,ColorOption
import Mplayer
import cairo
import pango
import screenlets
import gobject
import sys
import gtk
import commands

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
	radio_station = 'http://80.65.234.120:8000/ Frequence 3'
	
	mplayer_record = None
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
	radio_name_font = 'FreeSans'
	radio_name_color = (1,1,1,0.6)
	radio_name_x = 5
	radio_name_y = 5
	radio_name_fontsize = 25
	radio_name_fontwidth = 200
	song_name_font = 'FreeSans'
	song_name_x = 5
	song_name_y = 35
	song_name_fontsize = 10
	song_name_fontwidth = 200
	song_name_color = (1,1,1,0.6)
	play_button_x = 5
	play_button_y = 50
	play_button_width = 32
	play_button_height = 24
	stop_button_x = 40
	stop_button_y = 50
	stop_button_width = 32
	stop_button_height = 24
	home = commands.getoutput("echo $HOME")
	file_to_save = home + '/stream.mp3'	
	custom_radio_list = ['http://cidadefm.clix.pt/asx/outros/cidade20.asx Cidade Fm']
	
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=100, uses_theme=True,ask_on_option_override=False, **keyword_args) 
		
		self.theme_name = "default"

		self.pipe = None
		self.add_options_group('Radio', 'Settings')
		self.add_option(ListOption('Radio', 'custom_radio_list',
			self.custom_radio_list, 'Custom Radios',
			'Custom radios: stream _space_ radio name'))
		self.add_option(StringOption('Radio', 'password', 
			self.radio_station, 'radio', 
			'Radio stream address <space> radio name',hidden= True), realtime=False)
		self.add_option(FontOption('Radio','radio_name_font', 
			self.radio_name_font, 'Radio Name Font', 
			'radio_name_font'))
		self.add_option(ColorOption('Radio','radio_name_color', 
			self.radio_name_color, 'Radio Name Text color', 'radio_name_color'))
		self.add_option(IntOption('Screenlet', 'radio_name_x', 
			self.radio_name_x, 'Radio Name x position', 'radio_name_x', 
			min=0, max=self.width,hidden= True))
		self.add_option(IntOption('Screenlet', 'radio_name_y', 
			self.radio_name_y, 'Radio Name y position', 'radio_name_y', 
			min=0, max=self.height,hidden= True))
		self.add_option(IntOption('Screenlet', 'radio_name_fontsize', 
			self.radio_name_fontsize, 'Radio Name fontsize', 'radio_name_fontsize', 
			min=5, max=50,hidden= True))
		self.add_option(IntOption('Screenlet', 'radio_name_fontwidth', 
			self.radio_name_fontwidth, 'Radio Name fontwidth', 'radio_name_fontwidth', 
			min=5, max=self.width,hidden= True))
		self.add_option(FontOption('Radio','song_name_font', 
			self.song_name_font, 'Song Title Font', 
			'song_name_font'))
		self.add_option(ColorOption('Radio','song_name_color', 
			self.song_name_color, 'Radio Name Text color', 'song_name_color'))
		self.add_option(IntOption('Screenlet', 'song_name_x', 
			self.song_name_x, 'Radio Name x position', 'song_name_x', 
			min=0, max=self.width,hidden= True))
		self.add_option(IntOption('Screenlet', 'song_name_y', 
			self.song_name_y, 'Radio Name y position', 'song_name_y', 
			min=0, max=self.height,hidden= True))
		self.add_option(IntOption('Screenlet', 'song_name_fontsize', 
			self.song_name_fontsize, 'Radio Name fontsize', 'song_name_fontsize', 
			min=5, max=50,hidden= True))
		self.add_option(IntOption('Screenlet', 'song_name_fontwidth', 
			self.song_name_fontwidth, 'Radio Name fontwidth', 'song_name_fontwidth', 
			min=5, max=self.width,hidden= True))
		self.add_option(IntOption('Screenlet', 'play_button_x', 
			self.play_button_x, 'Play button x position', 'play_button_x', 
			min=0, max=self.width,hidden= True))
		self.add_option(IntOption('Screenlet', 'play_button_y', 
			self.play_button_y, 'Play button y position', 'play_button_y', 
			min=0, max=self.height,hidden= True))
		self.add_option(IntOption('Screenlet', 'play_button_width', 
			self.play_button_width, 'Play button width', 'play_button_width', 
			min=0, max=self.width,hidden= True))
		self.add_option(IntOption('Screenlet', 'play_button_height', 
			self.play_button_height, 'Play button height', 'play_button_height', 
			min=0, max=self.height,hidden= True))


		self.add_option(IntOption('Screenlet', 'stop_button_x', 
			self.stop_button_x, 'Play button x position', 'stop_button_x', 
			min=0, max=self.width,hidden= True))
		self.add_option(IntOption('Screenlet', 'stop_button_y', 
			self.stop_button_y, 'Play button y position', 'stop_button_y', 
			min=0, max=self.height,hidden= True))
		self.add_option(IntOption('Screenlet', 'stop_button_width', 
			self.stop_button_width, 'Play button width', 'stop_button_width', 
			min=0, max=self.width,hidden= True))
		self.add_option(IntOption('Screenlet', 'stop_button_height', 
			self.stop_button_height, 'Play button height', 'stop_button_height', 
			min=0, max=self.height,hidden= True))
		self.add_option(BoolOption('Radio', 'enable_title_scroll', self.enableTitleScroll,
			'Scroll title', 'Have song titles that are too long scroll across the display'), realtime=True)

		self.add_option(StringOption('Radio', 'title_scroll_speed', "Medium",
			'Title Scroll Speed', 'How fast the title will scroll',
			choices = self.__titleScrollSpeedLabels), realtime=True)
		self.add_option(StringOption('Radio', 'file_to_save', 
			self.file_to_save, 'Record stream file', 
			'Radio stream record to file'), realtime=False)
			

		self.radio_station = self.radio_station
		
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_submenuitem("Custom Radios", "Custom Radios",self.custom_radio_list)
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

	def record(self):
		if self.mplayer_record == None:
			self.mplayer_record = Mplayer.Mplayer(self)
		self.close_record_stream()
		ta = self.radio_station
		
		ta = ta[:ta.find(' ') ].strip()

		if ta[len(ta)-3:] == 'ram' or ta[len(ta)-3:] == 'Ram' or ta[len(ta)-2:] == 'rm' or ta[len(ta)-3:] == 'RAM' or ta[len(ta)-2:] == 'RM' or ta[len(ta)-4:] == 'rmvb' or ta[len(ta)-3:] == 'm3u' or ta[len(ta)-3:] == 'pls' or ta[len(ta)-3:] == 'asx':
			ta = ' -playlist ' + ta
			print 'PLEASE WAIT , REAL MEDIA STREAMS TAKE A WHILE TO LOAD'

		if ta[:len(' http://www.minist')] == 'http://www.ministr':
			
			ta = ' -playlist ' + ta
			print 'PLEASE WAIT , REAL MEDIA STREAMS TAKE A WHILE TO LOAD'
		self.mplayer_record.record(ta,self.file_to_save)



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
			print ' Error found , is mplayer installed?'
		else:
			self.stopScrollLoop()
			
		ta = self.radio_station
		
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

	def close_record_stream (self):
		try:
			self.mplayer_record.close_record()
		except:
			print 'Error found when stoping recording stream'
		#self.close_play_stream()
		#self.start_stop()

	def close_play_stream (self):
		try:
			self.mplayer.close()
		except:
			print 'Error found when closing playing stream'

		#retval = self.pipe.close()
		
	def stop(self):
		try:	
			self.mplayer.close()
		except Exception, ex:
			print 'sdfsdf'
		else:
			self.stopScrollLoop()
		
							

	def on_quit(self):
		"""Called when a keypress-event occured in Screenlet's window."""
		self.close_play_stream()
		self.close_record_stream()	

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id == 'b': print id
		if id[:4] == "http":
			self.radio_station = id
			self.start_stop()
			self.redraw_canvas()

		if id[:6] == "startp":
			print 'start playing'
			self.start_stop()
			self.redraw_canvas()

		if id[:6] == "startr":
			print 'start recording'
			self.record()

		if id[:5] == "stopr":
			print 'stop recording'
			self.close_record_stream()

		if id[:5] == "stopp":
			print 'stop playing'
			self.close_play_stream()
			self.redraw_canvas()

		if id[:3] == "mms":
			self.radio_station = id
			
			self.start_stop()
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()

		if id[:4] == "rtsp":
			self.radio_station = id
			
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


		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_submenuitem("Custom Radios", "Custom Radios",self.custom_radio_list)
		self.add_default_menuitems()
		
	def on_mouse_down(self,event):
		x = event.x / self.scale
		y = event.y / self.scale

		
		if event.button == 1:
			if x <= self.play_button_width +self.play_button_x and x >= self.play_button_x and y <= self.play_button_height +self.play_button_y and y >= self.play_button_y:
				self.but1 = '_press'					
				self.start_stop()
				self.redraw_canvas()
				return True

			elif x <= self.stop_button_width +self.stop_button_x and x >= self.stop_button_x and y <= self.stop_button_height +self.stop_button_y and y >= self.stop_button_y:
				self.but2 = '_press'
				self.close_play_stream()
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
			self.theme.render(ctx,'background')
			try:self.theme.render(ctx, 'logo')
			except:pass
			tb = self.radio_station
			tb = tb[tb.find(" ")+1:]
			tb = tb[:11]
			ctx.set_source_rgba(*self.radio_name_color)
			self.draw_text(ctx,tb, self.radio_name_x, self.radio_name_y, self.radio_name_font.split(' ')[0], self.radio_name_fontsize,  self.radio_name_fontwidth,pango.ALIGN_LEFT)
			tc = self.displayedStreamTitle
			tc = tc[:STREAM_TITLE_MAX_LENGTH]
			ctx.set_source_rgba(*self.song_name_color)
			self.draw_text(ctx,tc, self.song_name_x, self.song_name_y, self.song_name_font.split(' ')[0], self.song_name_fontsize,  self.song_name_fontwidth,pango.ALIGN_LEFT)


			self.draw_play_button(ctx)
			self.draw_stop_button(ctx)
			try:self.theme.render(ctx,'glass')
			except:pass


	def draw_play_button(self,ctx):
		ctx.save()
		ctx.translate(self.play_button_x,self.play_button_y)
		self.theme.render(ctx, 'play'+ self.but1)
		ctx.restore()

	
	def draw_stop_button(self,ctx):
		ctx.save()
		ctx.translate(self.stop_button_x,self.stop_button_y)
		self.theme.render(ctx, 'stop'+ self.but2)
		ctx.restore()


	def on_draw_shape(self,ctx):
		if self.theme:
			self.on_draw(ctx)

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(RadioScreenlet)
