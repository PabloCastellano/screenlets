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
	__version__ = '0.6'
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
	mini = True
	download_total = 0
	upload_total = 0
	dlt = 0
	dev_choices = []
	ult = 0
	dlt = 0


	mypath = argv[0][:argv[0].find('NetmonitorScreenlet.py')].strip()
	month = 0
	
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=120, uses_theme=True, **keyword_args) 
		
		self.theme_name = "default"
		self.add_menuitem("toggle", "Toggle mini view")	
		self.add_default_menuitems()
		self.update_interval = self.update_interval
		#self.disable_updates = True
		self.get_devices()
		self.add_options_group('Options', '')
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
				self.dev_choices.append(str(f)[:-1])



	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
	#	if name == 'download_total' or name == 'upload_total' :
	#		value = str(value)
		if name != 'xo' or  name != 'download' or  name != 'upload' or  name != 'unit1' or name != 'unit2' or name != 'u2' or name != 'u1' or name != 'n2' or name != 'n1'  or  name != 'p_layout' or name != 'download_total' or name != 'upload_total':	
		
			screenlets.Screenlet.__setattr__(self, name, value)	



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
		if self.theme:
			if self.mini == True:
				self.theme['background-mini.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'Network')
			else:
				self.theme['background.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'Network')

		ctx.set_source_rgba(1, 1, 1, 1)
		ctx.translate(50, 8)
		if self.p_layout == None :
	
			self.p_layout = ctx.create_layout()
		else:
			
			ctx.update_layout(self.p_layout)
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Free Sans")
		p_fdesc.set_size(16 * pango.SCALE)
		self.p_layout.set_font_description(p_fdesc)

		
		if len(self.session.instances) != 0:
			self.get_load()

#		self.download = '999'
#		self.upload = '999'
#		self.dlt = '9999'
#		self.ult = '9999'
		
		
			self.p_layout.set_markup('<b> In -    ' + str(self.download)  + '  KB'  + '\n Out - '  + str(self.upload) + '  KB' + '</b>')




			ctx.show_layout(self.p_layout)
			if self.mini == False:
				self.p_layout.alignment = pango.ALIGN_RIGHT
				self.p_layout.set_markup('<small> <small><small>Totals this Month</small></small></small>\nIn -   ' + str(self.dlt) + ' '+ self.unit_d + '\nOut - ' + str(self.ult)+ ' '+ self.unit_u)
				ctx.translate(-5,45)
				ctx.show_layout(self.p_layout)		

		
			
	


	

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
