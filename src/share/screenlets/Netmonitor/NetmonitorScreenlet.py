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
from screenlets import Screenlet
from screenlets.options import FloatOption, BoolOption, StringOption, FontOption, ColorOption, IntOption
import cairo
import pango
import gobject
import commands
import gtk
import datetime
import os
import sys
from sys import argv
import gconf

class NetmonitorScreenlet(screenlets.Screenlet):
	"""A Screenlet that displays net traffic , and month totals"""
	
	# default meta-info for Screenlets
	__name__ = 'NetmonitorScreenlet'
	__version__ = '0.7'
	__author__ = 'Helder Fraga aka Whise'
	__desc__ =__doc__

	__timeout = None
	p_layout = None
	update_interval = 1
	__buffer = None
	dev = 'eth0'
	unit_d = 'KB'
	unit_u = 'KB'
	u1 = 0
	n1 = 0
	u2 = 0
	n2 = 0
	xo = 0
	mini = False
	download_total = 0
	upload_total = 0
	dlt = 0
	dev_choices = []
	ult = 0
	dlt = 0
	frame_color = (1, 1, 1, 1)
	color_text = (0, 0, 0, 0.6)
	font = 'FreeSans'
	mypath = argv[0][:argv[0].find('NetmonitorScreenlet.py')].strip()
	month = 0
	show_frame = True
	show_txt = True
	
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=180, height=110, uses_theme=True,ask_on_option_override=False, **keyword_args) 
		
		self.theme_name = "default"
		self.add_menuitem("toggle", "Toggle mini view")	
		self.add_default_menuitems()
		self.update_interval = self.update_interval
		#self.disable_updates = True
		self.get_devices()
		self.add_options_group('Options', '')
		self.add_option(BoolOption('Options', 'show_frame',bool(self.show_frame), 'Show frame','Show frame'))
		self.add_option(BoolOption('Options', 'show_txt',bool(self.show_txt), 'Show In Out text','Show Text'))
		self.add_option(ColorOption('Options','frame_color', 
			self.frame_color, 'Frame color', 
			'Frame color'))
		self.add_option(ColorOption('Options','color_text', 
			self.color_text, 'Text color', ''))
		self.add_option(FontOption('Options','font', 
			self.font, 'Text Font', 
			'Text font'))
		self.add_option(StringOption('Options', 'dev', self.dev,'Select Device', '',choices = self.dev_choices))
		self.add_option(StringOption('Options', 'download_total', self.download_total,'Download total this month', '',))		
		self.add_option(StringOption('Options', 'upload_total', self.upload_total,'Upload total this month', '',))
		self.add_option(BoolOption('Options', 'mini', self.mini,'Use mini mode', '',))

		self.__timeout = gobject.timeout_add(1000, self.update)
		self.gconf_client = gconf.client_get_default() 
		self.gconf_path = "/apps/screenlets/" + self.__name__
		self.gconf_client.notify_add(self.gconf_path, self.config_event)
		self.gconf_key = "/apps/screenlets/" + self.__name__ + "/month"#
		print self.gconf_client.get_int(self.gconf_key)
		#self.gconf_client.notify_add(self.gconf_key, self.update) 

	def config_event(self):
		pass

	def get_devices(self):
		if self.dev_choices != []: del self.dev_choices
		self.dev_choices = []
		data = commands.getoutput("cat /proc/net/dev |grep :")
		for f in data.split(' '):
			if f != None and f.find(':') != -1 and not f.startswith('0'):  
				self.dev_choices.append(str(f).split(':')[0])
	


	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
	#	if name == 'download_total' or name == 'upload_total' :
	#		value = str(value)
		if name != 'xo' or  name != 'download' or  name != 'upload' or  name != 'unit1' or name != 'unit2' or name != 'u2' or name != 'u1' or name != 'n2' or name != 'n1'  or  name != 'p_layout' or name != 'download_total' or name != 'upload_total':	
		
			screenlets.Screenlet.__setattr__(self, name, value)	
		if name == 'mini':
			if value == True:
				self.height = 60
			else:
				self.height = 110


		return True

	
	def menuitem_callback(self, widget, id):
		screenlets.Screenlet.menuitem_callback(self, widget, id)

		if id == "toggle":
			self.mini = not self.mini

	def on_mouse_down(self,event):
		if event.button == 3:
			self.get_devices()
			
	def get_load(self):
		try:
			data = commands.getoutput("cat /proc/net/dev")
			data = data[data.find(self.dev + ":")+5:]
			self.u1 = float( data.split()[0] )
			self.n1 = float( data.split()[8] )
			self.month = self.gconf_client.get_int(self.gconf_key)
			if self.month == 0:
				print 'no month saving new month'
				self.month = datetime.datetime.now().month
				self.gconf_client.set_int(self.gconf_key, int(self.month)) 		

			self.download = str(int(self.u1 -self.u2)/1024)
			self.upload = str(int(self.n1 -self.n2)/1024)

			if self.u2 == 0 : self.download = '0'
			if self.n2 == 0 : self.upload = '0'


		
			if str(self.month) ==  str(datetime.datetime.now().month):
				print 'same month'
				self.download_total = int(self.download_total) + (int(self.download))
				self.upload_total = int(self.upload_total) + (int(self.upload))
			else:
				print 'diferent month'

				self.download_total = 0
				self.upload_total = 0
				self.month =  datetime.datetime.now().month
				self.gconf_client.set_int(self.gconf_key, int(self.month)) 	

			if int(self.download_total) >= 1024: 

				self.dlt = float(int(self.download_total)) / 1024
				self.unit_d = 'MB'

			elif  int(self.download_total) >= (1024*1024): 
	
				self.dlt = (float(int(self.download_total)) / 1024)/1024
				self.unit_d = 'GB'

			elif  int(self.download_total) >= (1024*1024*1024): 
	
				self.dlt = ((float(int(self.download_total)) / 1024)/1024)/1024
				self.unit_d = 'TB'

			else:

				self.dlt = float(int(self.download_total))

			if int(self.upload_total) >= 1024: 

				self.ult = float(int(self.upload_total)) / 1024
				self.unit_u = 'MB'

			elif  int(self.upload_total) >= (1024*1024): 

				self.ult = (float(int(self.upload_total)) / 1024)/1024
				self.unit_u = 'GB'

			elif  int(self.upload_total) >= (1024*1024*1024): 

				self.ult = ((float(int(self.upload_total)) / 1024)/1024)/1024
				self.unit_u = 'TB'

			else:

				self.ult = float(int(self.upload_total))

			try:
				self.ult = str(self.ult)
				self.dlt = str(self.dlt)

				if self.ult.find('.') != 0 :
					self.ult = self.ult[:self.ult.find('.')+2 ].strip()
				if self.dlt.find('.')  != 0:
					self.dlt = self.dlt[:self.dlt.find('.')+2 ].strip()
				print 'download total - '+ self.dlt
				print 'upload total - ' +self.ult
			except:
				pass
			self.u2 = self.u1
			self.n2 = self.n1
			screenlets.Screenlet.__setattr__(self, 'download_total', str(self.download_total))
	
			screenlets.Screenlet.__setattr__(self, 'upload_total', str(self.upload_total))
			self.session.backend.flush()
		except:
			self.download = 0
			self.upload = 0

	


	def on_draw(self, ctx):


		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)


		ctx.set_source_rgba(1, 1, 1, 1)

		
		if len(self.session.instances) != 0:
			self.get_load()

			if self.show_frame:
				gradient = cairo.LinearGradient(0, self.height*2,0, 0)
				gradient.add_color_stop_rgba(1,*self.frame_color)
				gradient.add_color_stop_rgba(0.7,self.frame_color[0],self.frame_color[1],self.frame_color[2],1-self.frame_color[3]+0.5)

				ctx.set_source(gradient)
			
				self.draw_rectangle_advanced (ctx, 0, 0, self.width-12, self.height-12, rounded_angles=(5,5,5,5), fill=True, border_size=2, border_color=(0,0,0,0.5), shadow_size=6, shadow_color=(0,0,0,0.5))
			self.draw_icon(ctx, 10, 12,gtk.STOCK_GO_DOWN,16,16)
			self.draw_icon(ctx, 10, 32,gtk.STOCK_GO_UP,16,16)
			ctx.set_source_rgba(*self.color_text)
			self.draw_text(ctx,  str(self.download) + ' KB', -10, 12,  self.font.split(' ')[0], 14, self.width, allignment=pango.ALIGN_RIGHT,weight = 0, ellipsize = pango.ELLIPSIZE_NONE)
			self.draw_text(ctx, str(self.upload) + ' KB', -10, 30,  self.font.split(' ')[0], 14, self.width, allignment=pango.ALIGN_RIGHT,weight = 0, ellipsize = pango.ELLIPSIZE_NONE)
			if self.show_txt:self.draw_text(ctx, 'In -\nOut -', 30, 12,  self.font.split(' ')[0], 14, self.width, allignment=pango.ALIGN_LEFT,weight = 0, ellipsize = pango.ELLIPSIZE_NONE)
			
			if self.mini == False:
				self.draw_icon(ctx, 10, 64,gtk.STOCK_GO_DOWN,16,16)
				self.draw_icon(ctx, 10, 84,gtk.STOCK_GO_UP,16,16)
				self.draw_text(ctx, '<small> <small><small>Totals this Month</small></small></small>', 0,45,  self.font.split(' ')[0], 14, self.width, allignment=pango.ALIGN_CENTER,weight = 0, ellipsize = pango.ELLIPSIZE_NONE)
				if self.show_txt:self.draw_text(ctx, 'In -\nOut -' , 30, 64,  self.font.split(' ')[0], 14, self.width, allignment=pango.ALIGN_LEFT,weight = 0, ellipsize = pango.ELLIPSIZE_NONE)
			
				self.draw_text(ctx, str(self.dlt) + ' '+ self.unit_d + '\n' + str(self.ult)+ ' '+ self.unit_u, -10,64,  self.font.split(' ')[0], 14, self.width,allignment=pango.ALIGN_RIGHT,weight = 0, ellipsize = pango.ELLIPSIZE_NONE)
	

	def update (self):
	
		self.redraw_canvas()
		return True

	def on_draw_shape(self,ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			#self.theme['control-bg.svg'].render_cairo(ctx)
			ctx.set_source_rgba(1, 1, 1, 1)
			ctx.rectangle (0,0,self.width,self.height)
			ctx.fill()
			

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(NetmonitorScreenlet)
