#!/usr/bin/env python

#
#Copyright (C) 2007 Nemanja Jovicic
##From v0.6 added new stuff and fixed several bugs
#
##Version 0.6 was created by Helder Fraga
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
from sys import argv

class NetmonitorScreenlet(screenlets.Screenlet):
	"""A Screenlet that displays net traffic , and month totals"""
	
	# default meta-info for Screenlets
	__name__ = 'NetmonitorScreenlet'
	__version__ = '0.7'
	__author__ = 'Helder Fraga aka whise , thanks to Jovicic Nemanja for some bug fixes'
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
	data = commands.getoutput("cat /proc/net/dev |grep :")
	for f in data.split(':'):
		f = f[::-1]
		f = f[:f.find(' ') ].strip()
		f = f[::-1]
		print f
		if f != None	 and f != '0':  dev_choices.append(str(f))



	mypath = argv[0][:argv[0].find('NetmonitorScreenlet.py')].strip()
	month = 0
	download = 0
	upload = 0
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=230, height=120, uses_theme=True, **keyword_args) 
		
		self.theme_name = "default"
		self.add_menuitem("toggle", "Toggle mini view")	
		self.add_default_menuitems()
		self.update_interval = self.update_interval
		#self.disable_updates = True

		self.add_options_group('Options', '')
		self.add_option(StringOption('Options', 'dev', self.dev,'Select Device', '',choices = self.dev_choices))
		self.add_option(StringOption('Options', 'download_total', self.download_total,'Download total this month', '',))		
		self.add_option(StringOption('Options', 'upload_total', self.upload_total,'Upload total this month', '',))
		self.add_option(BoolOption('Options', 'mini', self.mini,'Use mini mode', '',))

		self.__timeout = gobject.timeout_add(1000, self.update)

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
			
	def get_load(self):
		data = commands.getoutput("cat /proc/net/dev")
		data = data[data.find(self.dev + ":")+5:]
		self.u1 = float( data.split()[0] )
		self.n1 = float( data.split()[8] )

		if self.month == 0:
			if not os.path.isfile(self.mypath + 'month'):
				f =  open( self.mypath + "month","w") #// open for for write
				f.close()

			f =  open( self.mypath + "month","r") #// open for for read
			self.month = f.read()
			f.close()
			#this if statement is changed in 0.6.9 because old one was causing bug
			if str(self.month) < '1' or str(self.month) > '12':
				print 'no month saving new month'				
				self.month = datetime.datetime.now().month
				f =  open( self.mypath + "month","w") #// open for for write
				f.write(str(self.month))
				f.close()
		
		# added because of fixing overflow bug v0.6.7----------------
		if self.u1<self.u2: self.u2=0
		if self.n1<self.n2: self.n2=0
		#-----------------------------------------------------
		self.download = str(long(self.u1 -self.u2))#/1024) measure in bytes
		self.upload = str(long(self.n1 -self.n2))#/1024)
		#printf for testing and debugging------------
		#print 'self.u1: '+str(self.u1)
		#print 'self.u2: '+str(self.u2)
		#print 'u1-u2: '+str(long(self.u1 -self.u2))
		#print 'download: ' +self.download+' B/s'
		#print 'upload: ' +self.upload+' B/s'
		#------------------------------------
		if self.u2 == 0 : self.download = '0'
		if self.n2 == 0 : self.upload = '0'


		
		if str(self.month) ==  str(datetime.datetime.now().month):
			print 'same month'
			self.download_total = long(self.download_total) + (long(self.download)/1024)
			self.upload_total = long(self.upload_total) + (long(self.upload)/1024)
		else:
			print 'diferent month'

			self.download_total = 0
			self.upload_total = 0
			self.month =  datetime.datetime.now().month
			f =  open( self.mypath + "month","w") #// open for for write
			f.write(str(self.month))
			f.close()
		# added because of fixing bug 0.6.1
		self.unit_d = 'KB' 
		self.unit_u = 'KB'
		#-------------------------------------------------------------------
		# added because of fixing bug 0.6.2 
		if long(self.download_total) < 0: 
			 self.download_total=0-self.download_total
		#---------------------------------------
		#repaired because of fixing bug 0.6.3		
		elif long(self.download_total) >= (1024*1024*1024): 

			self.dlt = ((float(long(self.download_total)) / 1024)/1024)/1024
			self.unit_d = 'TB'

		elif  long(self.download_total) >= (1024*1024): 

			self.dlt = (float(long(self.download_total)) / 1024)/1024
			self.unit_d = 'GB'

		elif  long(self.download_total) >= (1024): 

			self.dlt = float(long(self.download_total)) /1024
			self.unit_d = 'MB'
		
		else:

			self.dlt = float(long(self.download_total))
		#--------------------------------------------------------------------------
		#added because of fixing bug 0.6.2
		if long(self.upload_total) < 0: 
			 self.upload_total=0-self.upload_total
		#---------------------------------------
		#repaired because of fixing bug 0.6.3		
		elif long(self.upload_total) >= (1024*1024*1024): 

			self.ult = ((float(long(self.upload_total)) / 1024)/1024)/1024
			self.unit_u = 'TB'
		elif long(self.upload_total) >= (1024*1024): 

			self.ult = (float(long(self.upload_total)) / 1024)/1024
			self.unit_u = 'GB'

		elif  long(self.upload_total) >= (1024): 

			self.ult = float(long(self.upload_total)) /1024
			self.unit_u = 'MB'

		else:

			self.ult = float(long(self.upload_total))
		#--------------------------------------------------------------------------
		try:
			self.ult = str(self.ult)
			self.dlt = str(self.dlt)

			if self.ult.find('.') != 0 :
				self.ult = self.ult[:self.ult.find('.')+2 ].strip()
			if self.dlt.find('.')  != 0:
				self.dlt = self.dlt[:self.dlt.find('.')+2 ].strip()
			print 'download total: '+ self.dlt+self.unit_d
			print 'upload total: ' +self.ult+self.unit_u
			
		except:
			pass
		self.u2 = self.u1
		self.n2 = self.n1
		screenlets.Screenlet.__setattr__(self, 'download_total', str(self.download_total))

		screenlets.Screenlet.__setattr__(self, 'upload_total', str(self.upload_total))
		
		print 'download month: ' +self.download_total+' B'
		print 'upload month: ' +self.upload_total+' B'
		print 'download: ' +self.download+' B/s'
		print 'upload: ' +self.upload+' B/s'

		self.session.backend.flush()
	


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
		ctx.save()

		ctx.translate(50, 8)
		if self.theme:
			
			self.theme.render(ctx, 'updown')
		ctx.restore()

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
			try:

				self.get_load()
			except:
				pass

			if  long(self.download) >= (1024*1024): 
			#if download MB
				self.p_layout.set_markup('<small><b>     ' + str(long(self.download)/(1024*1024))  + ' <small>MB/s</small></b></small>')
			elif  long(self.download) >= 1024: 
			#if download KB
				self.p_layout.set_markup('<small><b>     ' + str(long(self.download)/1024)  + ' <small>KB/s</small></b></small>')
			#id download B
			elif long(self.download)>=0:
				self.p_layout.set_markup('<small><b>     ' + str(self.download)  + ' <small>B/s</small></b></small>')	
			ctx.show_layout(self.p_layout)
	
			if  long(self.upload) >= (1024*1024): 
			#if upload MB
				self.p_layout.set_markup('\n<small><b>     ' + str(long(self.upload)/(1024*1024))  + ' <small>MB/s</small></b></small>')
			elif  long(self.upload) >= 1024: 
			#if upload KB
				self.p_layout.set_markup('\n<small><b>     ' + str(long(self.upload)/1024)  + ' <small>KB/s</small></b></small>')
			#id download B
			elif long(self.upload)>=0:
				self.p_layout.set_markup('\n<small><b>     ' + str(self.upload)  + ' <small>B/s</small></b></small>')	
			self.p_layout.alignment = pango.ALIGN_RIGHT
			ctx.show_layout(self.p_layout)
			#-------------------------------------------------------------------------------------------

			if self.mini == False:
				self.p_layout.alignment = pango.ALIGN_RIGHT
		
				ctx.translate(-20,50)
				#December
				if str(self.month)=='12':
					self.p_layout.set_markup('<small><small><small>***December total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#November
				if str(self.month)=='11':
					self.p_layout.set_markup('<small> <small><small>***November total:</small></small></small>')	
					ctx.show_layout(self.p_layout)
				#October
				if str(self.month)=='10':
					self.p_layout.set_markup('<small> <small><small>***October total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#September
				if str(self.month)=='9':
					self.p_layout.set_markup('<small> <small><small>***September total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#August
				if str(self.month)=='8':
					self.p_layout.set_markup('<small> <small><small>***August total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#July
				if str(self.month)=='7':
					self.p_layout.set_markup('<small> <small><small>***July total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#June
				if str(self.month)=='6':
					self.p_layout.set_markup('<small> <small><small>***June total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#May
				if str(self.month)=='5':
					self.p_layout.set_markup('<small> <small><small>***May total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#April
				if str(self.month)=='4':
					self.p_layout.set_markup('<small> <small><small>***April total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#March
				if str(self.month)=='3':
					self.p_layout.set_markup('<small> <small><small>***March total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#February
				if str(self.month)=='2':
					self.p_layout.set_markup('<small> <small><small>***February total:</small></small></small>')
					ctx.show_layout(self.p_layout)
				#January
				if str(self.month)=='1':
					self.p_layout.set_markup('<small> <small><small>***January total:</small></small></small>')
					ctx.show_layout(self.p_layout)		
			#------------------------------------------------------------------------------------------
				try:
					self.p_layout.set_markup('<small>       ' + str(self.dlt) + ' '+ self.unit_d + '\n       ' + str(self.ult)+ ' '+ self.unit_u+"</small>")
				
					ctx.translate(10,18)
					ctx.show_layout(self.p_layout)	
					self.theme.render(ctx, 'updown')
				except:
					pass
	def update (self):
	
		self.redraw_canvas()
			#except Exception, ex:
			#		print 'no value yet'			
		return True

	def on_draw_shape(self,ctx):
		
		if self.theme:
			self.on_draw(ctx)
			

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(NetmonitorScreenlet)
