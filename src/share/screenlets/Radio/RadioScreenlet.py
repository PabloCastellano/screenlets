#!/usr/bin/env python

#
#Copyright (C) 2007 Helder Fraga
#
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
#
import screenlets
from screenlets.options import BoolOption, StringOption, FontOption
from screenlets import DefaultMenuItem
import cairo
import pango



import Mplayer


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
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=100, uses_theme=True, **keyword_args) 
		
		self.theme_name = "default"
		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_default_menuitems()

		self.pipe = None
		self.add_options_group('Radio', 'Settings.')
		self.add_option(StringOption('Radio', 'password', 
			self.password, 'radio', 
			'Radio stream address <space> radio name',), realtime=False)		
		#self.player = gst.element_factory_make("playbin", "player")
		#fakesink = gst.element_factory_make('fakesink', "my-fakesink")
		#self.player.set_property("video-sink", fakesink)
		#bus = self.player.get_bus()
		#bus.add_signal_watch()
		#bus.connect('message', self.on_message)
		self.password = self.password
		password = self.password
		

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'password':
			screenlets.Screenlet.__setattr__(self, name, value)
			self.redraw_canvas()

	#def on_mouse_down(self, event):
		# do the active button's action
	#	if event.button == 1:
	#		self.gen()
	def start_stop(self):
		if self.mplayer == None:
			self.mplayer = Mplayer.Mplayer(self)
		#if self.button.get_label() == "Start":
		#	filepath = self.entry.get_text()
			#if os.path.exists(filepath):
			#self.button.set_label("Stop")
		try:
			self.mplayer.close()
		except Exception, ex:
			print 'sdfsdf'
		ta = self.password
		
		ta = ta[:ta.find(' ') ].strip()

		if ta[len(ta)-3:] == 'ram' or ta[len(ta)-3:] == 'Ram' or ta[len(ta)-2:] == 'rm' or ta[len(ta)-3:] == 'RAM' or ta[len(ta)-2:] == 'RM' or ta[len(ta)-4:] == 'rmvb' or ta[len(ta)-3:] == 'm3u' or ta[len(ta)-3:] == 'pls' or ta[len(ta)-3:] == 'asx':
			ta = ' -playlist ' + ta
			print 'PLEASE WAIT , REAL MEDIA STREAMS TAKE A WHILE TO LOAD'

		if ta[:len(' http://www.minist')] == 'http://www.ministr':
			
			ta = ' -playlist ' + ta
			print 'PLEASE WAIT , REAL MEDIA STREAMS TAKE A WHILE TO LOAD'
		print ta
		self.mplayer.play(ta )
				#self.player.set_state(gst.STATE_PLAYING)
	
			
	
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
	def on_mouse_enter (self, event):
		print 'enter'
        
	def on_mouse_leave (self, event):
		print 'leave'
	def on_mouse_down(self,event):

		x = event.x / self.scale
		y = event.y / self.scale

		
		if y >= 50:
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
			ctx.translate(5, 15)
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
			ctx.restore()

			ctx.save()
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
