#!/usr/bin/env python

#  WallpaperClockScreenlet by Whise aka Helder Fraga
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


import screenlets
from screenlets.options import StringOption, BoolOption, ImageOption
import screenlets.options
from screenlets import DefaultMenuItem
import gtk
import gobject
try:
	import Image
except:
	print 'Error - Please install python image module'
from commands import getoutput
from sys import path
import os
from datetime import datetime
import math, decimal

class WallpaperClockScreenlet (screenlets.Screenlet):
	"""A Screenlet that displays clock wallpapers , you can get wallpaper clocks from http://www.vladstudio.com/wallpaperclock/ , to install the wcz file drag drop it into the screenlet area , use the install menu or  extract the file to the wallpaper folder inside the screenlet folder"""
	
	# --------------------------------------------------------------------------
	# meta-info, options
	# --------------------------------------------------------------------------
	
	__name__		= 'WallpaperClockScreenlet'
	__version__		= '2.0'
	__author__		= 'Helder Fraga based aka Whise , The Wallpaper Clocks are completly made by Vlad Gerasimov at http://www.vladstudio.com , you need a package called python imaging installed'
	__desc__		= __doc__

	time = datetime.now()
	# attributes

	__timeout = None
	# editable options

	dec = decimal.Decimal
	visible = True
	image = None
	image1 = None
	_time = datetime.now()
	month = ''
	day = ''
	hour = ''
	minute = ''
	weekday = ''
	hour_format = '24'
	mouseover = False
	mypath =path[0] + '/'
	wall = ''
	p_layout = None
	home = getoutput("echo $HOME")

	wall_sel = os.listdir(mypath + 'wallpapers')
	# --------------------------------------------------------------------------
	# constructor and internals
	# --------------------------------------------------------------------------
	
	def __init__ (self, **keyword_args):


		screenlets.Screenlet.__init__(self, width=72, height=92,
			uses_theme=True, drag_drop=True, **keyword_args)

		# set theme
		self.theme_name = "default"

		self.add_default_menuitems(DefaultMenuItem.XML)

		self.add_options_group('WallpaperClock', 'WallpaperClock-related settings ...')
		# add editable options
		self.add_option(StringOption('WallpaperClock', 'hour_format', self.hour_format, 'Hour-Format', 'The hour-format (12/24) ...', choices=['12', '24']))		
		self.add_option(BoolOption('WallpaperClock', 'mouseover', self.mouseover, 
			'Hide when mouse not over', 'Hide when mouse not over'))
		self.add_option(StringOption('WallpaperClock', 'wall', self.wall,'Current Wallpaper Clock', '',choices=self.wall_sel))
		self.wall = self.wall
		self.__timeout = gobject.timeout_add(60000, self.update)
		self.__buttons_timeout = gobject.timeout_add(100, 
						self.update_buttons)
		self.update()
	def __setattr__ (self, name, value):

		screenlets.Screenlet.__setattr__(self, name, value)
		self.redraw_canvas()

	def install (self, filename):
		"""Install a screenlet from a given archive-file. Extracts the
		contents of the archive to the user's screenlet dir."""
		print 'Installing %s' % filename
		result = False

		basename	= os.path.basename(filename)
		extension	= str(filename)[len(str(filename)) -3:]

		tar_opts = '-o'
	
		if extension == 'Wcz' or  extension == 'wcz'	or extension == 'WCZ':
			if not os.path.isdir(self.mypath + '/wallpapers/' + basename):
				os.mkdir(self.mypath + '/wallpapers/' + basename)
			os.system('unzip %s %s -d %s' % (tar_opts, filename, self.mypath + '/wallpapers/' + basename))
			screenlets.show_message(self,"Wallpaper clock  has been succesfully installed. if not please install unzip" )
			result = True

		else:
			screenlets.show_message(self,"Archive is not a wallpaper clock archive , if it is extract it manually")
		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_default_menuitems()
		return result

	def on_drop (self, x, y, sel_data, timestamp):
		print "Data dropped ..."
		filename = ''
	
		txt = sel_data.get_text()
		if txt:
			if txt[-1] == '\n':
				txt = txt[:-1]
			txt.replace('\n', '\\n')
		
			if txt.startswith('file://'):
				filename = txt[7:]
			else:
				screenlets.show_error(self, 'Invalid string: %s.' % txt)
		else:
			
			uris = sel_data.get_uris()
			if uris and len(uris)>0:
		
				filename = uris[0][7:]
		if filename != '':

			self.install (filename)	


	def position(self,now=None): 
		dec = decimal.Decimal
		if now is None: 
			now = datetime.now()

		diff = now - datetime(2001, 1, 1)
		days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
		lunations = dec("0.20439731") + (days * dec("0.03386319269"))

		return lunations % dec(1)

	def phase(self,pos): 
		dec = decimal.Decimal
		index = (pos * dec(8)) + dec("0.5")
		index = math.floor(index)
		return {
      0: "New Moon", 
      1: "Waxing Crescent", 
      2: "First Quarter", 
      3: "Waxing Gibbous", 
      4: "Full Moon", 
      5: "Waning Gibbous", 
      6: "Last Quarter", 
      7: "Waning Crescent"
   }[int(index) & 7]
   

	def get_zodiac(self,day,month):
		if month == 1:
			if day <= 19:
				zodiac = 'Capricorn'
			else:
				zodiac = 'Aquarius'
		if month == 2:
			if day <= 18:
				zodiac = 'Aquarius'
			else:
				zodiac = 'Pisces'
		if month == 3:
			if day <= 20:
				zodiac = 'Pisces'
			else:
				zodiac = 'Aries'
		if month == 4:
			if day <= 19:
				zodiac = 'Aries'
			else:
				zodiac = 'Taurus'
		if month == 5:
			if day <= 20:
				zodiac = 'Taurus'
			else:
				zodiac = 'Gemini'
		if month == 6:
			if day <= 20:
				zodiac = 'Gemini'
			else:
				zodiac = 'Cancer'
		if month == 7:
			if day <= 22:
				zodiac = 'Cancer'
			else:
				zodiac = 'Leo'
		if month == 8:
			if day <= 22:
				zodiac = 'Leo'
			else:
				zodiac = 'Virgo'
		if month == 9:
			if day <= 22:
				zodiac = 'Virgo'
			else:
				zodiac = 'Libra'
		if month == 10:
			if day <= 22:
				zodiac = 'Libra'
			else:
				zodiac = 'Scorpio'
		if month == 11:
			if day <= 21:
				zodiac = 'Scorpio'
			else:
				zodiac = 'Sagittarius'
		if month == 12:
			if day <= 21:
				zodiac = 'Sagittarius'
			else:
				zodiac = 'Capricorn'
		return zodiac	

	def on_init(self):
		self.update()
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()

	def update_buttons(self):
		x, y = self.window.get_pointer()
		x /= (2*self.scale)
		y /= (2*self.scale)
		al_last = self.__buttons_alpha
		if x >= 0 and x < 100 and y >= 0 and y <= 15:	# top line
			self.__buttons_alpha = min(self.__buttons_alpha + 0.2, 1.0)
		else:
			self.__buttons_alpha = max(self.__buttons_alpha - 0.2, 0.0)
		if self.__buttons_alpha != al_last:
			self.redraw_canvas()
		return True
		
	def get_day (self):
		"""Only needed for the service."""
		return self._time.strftime("%d")
	def get_month (self):
		"""Only needed for the service."""
		return self._time.strftime("%m")
	def get_hour24 (self):
		"""Only needed for the service."""
		return self._time.strftime("%H")
	def get_hour (self):
		"""Only needed for the service."""
		if self.hour_format == '24' :
			return self._time.strftime("%H")
		elif self.hour_format == '12' :
			return self._time.strftime("%I")
	def get_minute (self):
		"""Only needed for the service."""
		return self._time.strftime("%M")
	def get_weekday (self):
		"""Only needed for the service."""
		return self._time.strftime("%w")
	def get_year (self):
		"""Only needed for the service."""
		return self._time.strftime("%y")

	def set_image(self):
		if self.wall != '':
			try:
				self.image = Image.open(self.mypath+'wallpapers/' +self.wall+'/bg.jpg')
			except:
				pass
			try:
				self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/month'+ self.month+'.png')
				self.image.paste(self.image1, (0,0), self.image1)
			except:
				pass
			try:
				self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/day'+ self.day+'.png')
				self.image.paste(self.image1, (0,0), self.image1)
			except:
				pass
			
			try:
				self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/weekday'+ self.weekday+'.png')
				self.image.paste(self.image1, (0,0), self.image1)
			except:
				pass
			try:
				self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/moonphase'+ self.moon+'.png')
				self.image.paste(self.image1, (0,0), self.image1)
			except:
				pass			
			try:
				self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/zodiac'+ self.zodiac +'.png')
				self.image.paste(self.image1, (0,0), self.image1)
			except:
				pass
			if self.hour_format == '12' :
				try:
					if os.path.isfile (self.mypath+'wallpapers/' +self.wall+'/am.png'):
	
						if int(self.get_hour24())> 12:
							self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/pm.png')
							self.image.paste(self.image1, (0,0), self.image1)
						else:
							self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/am.png')
							self.image.paste(self.image1, (0,0), self.image1)
					#self.hour = str(int(self.hour)/2)
				except:
					pass
			try:
				self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/hour'+ self.hour+'.png')
				self.image.paste(self.image1, (0,0), self.image1)
			except:
				pass
			try:
				self.image.save ('/tmp/wallpaper.png')
			except:
				pass
			try:
				self.image1 = Image.open(self.mypath+'wallpapers/' +self.wall+'/minute'+ self.minute+'.png')
				self.image.paste(self.image1, (0,0), self.image1)
			except:
				pass
			try:
			
				self.image.save (self.home + '/wallpaper.png')
			except:
				pass
			try:
				os.system("gconftool-2 -t string -s /desktop/gnome/background/picture_filename " + self.home + '/wallpaper.png')
				os.system("gconftool-2 -t bool -s /desktop/gnome/background/draw_background False")
				os.system("gconftool-2 -t bool -s /desktop/gnome/background/draw_background True")
			except:
				pass
			try:
				os.system("/usr/bin/dcop kdesktop KBackgroundIface setWallpaper " + self.home + "/wallpaper.png 7")
			except:
				pass
			self.image = None
			self.image1 = None
	
		print 'updated wallpaper ' + self.wall
	
	
	def update(self):
		dec = decimal.Decimal

		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_default_menuitems()


		self._time = datetime.now()
		self.month = self.get_month()
		self.day = self.get_day()
		self.minute = self.get_minute()
		self.year = self.get_year()
		self.hour24 = self.get_hour24()

		pos = self.position()
		phasename = self.phase(pos)
		self.moon = int(((((float(pos))*100)/3.333333))) +1

		self.zodiac = self.get_zodiac(int(self.day),int(self.month))

		self.moon = str(self.moon)
		self.hour = self.get_hour()
		if os.path.isfile (self.mypath+'wallpapers/' +self.wall+'/hour25.png'):

				if int(self.hour24) <= 12:
					self.hour = str(((int(self.hour24)*60)/12)+(int(self.minute)/12))
				else:
					self.hour = str((((int(self.hour24)*60)/12)-60)+(int(self.minute)/12))

		
		self.weekday = self.get_weekday()



		if self.month[0] == '0' : 
			self.month = self.month[1]
		
		if self.day[0] == '0' : 
			self.day = self.day[1]

		if self.hour[0] == '0':
			if len(str(self.hour)) == 2:
				self.hour = self.hour[1]
			if len(str(self.hour)) == 1:
				self.hour = self.hour[0]
	
		if self.minute[0] == '0' : 
			self.minute = self.minute[1]

		if self.weekday == '0' : 
			self.weekday = '7'

		self.set_image ()
		self.redraw_canvas()
		print 'updated' + '   ' + self.month + '   ' +self.day + '   ' +self.hour + '   ' +self.minute + '   ' +self.weekday + '   ' +self.moon + '   ' +self.zodiac
	

		return True

	def update_buttons(self):
		x, y = self.window.get_pointer()
		x /= (self.scale)
		y /= (self.scale)
		
		if x >= 0 and x < 72 and y >= 0 and y <= 92:	# top line
			if self.theme:
			# if something is dragged over, lighten up the whole thing
				if self.mouseover == True:
					self.visible = True
		else:
			if self.mouseover == True:
				self.visible = False
		return True
	
	def on_draw (self, ctx):

		ctx.scale(self.scale*0.7, self.scale*0.7)
		if self.theme:
			# if something is dragged over, lighten up the whole thing
			if self.visible == True:
				self.theme.render(ctx, 'WallpaperClock-bg')
			else:
				pass

		
	def show_install_dialog (self):
		"""Craete/Show the install-dialog."""
		# create filter
		flt = gtk.FileFilter()
		flt.add_pattern('*.wcz')

		# create dialog
		dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dlg.set_current_folder(os.environ['HOME'])
		dlg.set_title(('Install a Wallpaper Clock'))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			
			# try installing and show result dialog
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			self.install (filename)	
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
		
		

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id[:6] == "change":
			# TODO: use DBus-call for this
			self.wall = id[6:]
			self.update()
		if id[:7] == "Install":
			# TODO: use DBus-call for this
			self.show_install_dialog()
		if id == "visit":
			# TODO: use DBus-call for this
			#self.switch_hide_show()

			os.system('firefox http://www.vladstudio.com/wallpaperclock/' + " &")
		if id == "wallinfo":
			# TODO: use DBus-call for this
			#self.switch_hide_show()
				if os.path.isfile (self.mypath+'wallpapers/' +self.wall+'/clock.ini'):
					f = open(self.mypath+'wallpapers/' +self.wall+'/clock.ini')
					text = f.read()
					author = text[text.find('name'):]
					author = author[:author.find('refreshhourinterval')].strip()
					screenlets.show_message(self, str(author))
				#os.system('firefox http://www.vladstudio.com/wallpaperclock/' + " &")

	def on_draw_shape (self, ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			self.theme.render(ctx, 'WallpaperClock-bg')


	
# If the program is run directly or passed as an argument to the python
# interpreter then launch as new application
if __name__ == "__main__":
	# create session object here, the rest is done automagically
	import screenlets.session
	screenlets.session.create_session(WallpaperClockScreenlet)

