#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# GmailScreenlet (c) Whise <helder.fraga@hotmail.com>
#
# INFO:



import screenlets
from screenlets.options import StringOption, IntOption
import cairo
import pango
import gtk
from os import system
from urllib import quote
import gobject
from screenlets import DefaultMenuItem,utils
import pyDes


class GmailScreenlet(screenlets.Screenlet):
	"""A screenlet that shows your unread gmail message count , click on the mail icon to go to gmail.com"""
	
	# default meta-info for Screenlets
	__name__ = 'GmailScreenlet'
	__version__ = '0.6'
	__author__ = 'Helder Fraga'
	__desc__ = 'A screenlet that shows your unread gmail message count , click on the mail icon to go to gmail.com , new version has password encryption but is  a bit more laggy.'

	# a list of the converter class objects


	__has_focus = False
	__query = ''
	__timeout = None
	# editable options
	# the name, i.e., __title__ of the active converter
	update_interval = 60
	p_layout = None
	p_layouta = None
	forecast = ''
	msgs = ' 0'
	msgss = ''
	nam = ''
	pas = ''
	ga = ''
	d = ''
	k = pyDes.triple_des("MySecretTripleDesKeyData")
	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=275, height=242, uses_theme=True,	**keyword_args)
		# set theme
		self.theme_name = "default"
		# add default menu items
		self.add_default_menuitems(DefaultMenuItem.XML)
	
		self.add_options_group('gmail', 'Gmail Screenlet settings ...')
		self.add_option(IntOption('gmail', 'update_interval', 
			self.update_interval, 'Update interval', 'The interval for updating info (in seconds ,3660 = 1 day, 25620 = 1 week)', min=30, max=25620))
		self.add_option(StringOption('gmail', 'nam', self.nam,'Select Email Account', '',),realtime=False)
		self.add_option(StringOption('gmail', 'pas', self.pas,'Select Password', '',),realtime=False)
		self.update_interval = self.update_interval

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'pas' and self.nam != '':
			


			
			self.d = self.k.encrypt(value, "*")
			value = self.d
			screenlets.Screenlet.__setattr__(self, name, value)
			value = self.k.decrypt(self.d, "*")
			self.update()
		if name == 'nam' and self.pas != '':
			self.update()

		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(int(value * 1000), self.update)

			else:
				self.__dict__['update_interval'] = 1
				pass
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()

	def update(self):
		self.check()
		self.redraw_canvas()
		return True

	def set_engine(self, name):

		for engine in self.__engines:
			if engine["name"] == name:
				break
		self.__engine = engine
		# make the option be cached and show in the Options dialog
		self.engine = engine['name']
		self.redraw_canvas()

	# I don't want to call this on_key_press, I consider such a name reserved 
	# for future versions of screenlets.
	def check(self):

		self.msa = self.k.decrypt(self.pas, "*")
	
		n = self.nam.replace('@gmail.com','')
		self.msgs = utils.get_GMail_Num(n, self.msa)




		print str(self.msgs) + ' Unread Messages'


	def on_mouse_down(self, event):
		# filter events
		if event.button != 1 or event.type != gtk.gdk.BUTTON_PRESS:
			return False
		# recalculate cursor position
		x = event.x / self.scale
		y = event.y / self.scale
		# compute space between fields
		n = 1
		m = 10
		# find if a click occured over some field...
		if x >= 50 and x <= 190:
			if y >= m and y <= 100:
				d = y - m
				if d % (20 + m) <= 20:
					self.redraw_canvas()
					return True
		if x >= 180 and y >= 180 :
			system('xdg-open http://mail.google.com/mail/')
		return False


	def on_draw(self, ctx):
		# if a converter or theme is not yet loaded, there's no way to continue
		# set scale relative to scale-attribute
		ctx.scale(self.scale, self.scale)
		# render background
		self.theme.render(ctx, 'gmail')
		
		#self.theme.render(ctx, 'urban')
		# compute space between fields
		n = 1
		m = 20
		# draw fields
		

		
		ctx.save()
		
		ctx.restore()
		# render field names
		# ctx.save()
		
		
		if self.p_layouta == None :
	
			self.p_layouta = ctx.create_layout()
		else:
			
			ctx.update_layout(self.p_layouta)
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Free Sans")

		if int(self.msgs) >= 10 and int(self.msgs) <= 99:
			p_fdesc.set_size(30 * pango.SCALE)
			ctx.translate(180, 187)
		elif int(self.msgs) >= 100 and int(self.msgs) <= 999:
			p_fdesc.set_size(24 * pango.SCALE)
			ctx.translate(175, 187)
		elif int(self.msgs) >= 1000:
			p_fdesc.set_size(20 * pango.SCALE)
			ctx.translate(170, 190)
		else:
			p_fdesc.set_size(36 * pango.SCALE)
			ctx.translate(188, 182)
		self.p_layouta.set_font_description(p_fdesc)
		self.p_layouta.set_width(290 * pango.SCALE)
		self.p_layouta.set_markup('<b>'+ str(self.msgs) +'</b>')

		ctx.set_source_rgba(1, 1, 1, 0.9)
		ctx.show_layout(self.p_layouta)
		# ...and finally something to cover this all

		#self.theme['glass.svg'].render_cairo(ctx)
		
	def on_draw_shape(self, ctx):
		if self.theme:
			ctx.scale(self.scale, self.scale)
			# the background will serve well
			self.theme.render(ctx, 'gmail')

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id == "update":
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.check()
			self.redraw_canvas()
		elif id[:4] == "add:":
			# make first letter uppercase (workaround for xml-menu)
			name = id[4].upper()+id[5:][:-9]
			 #and launch screenlet (or show error)
			if not screenlets.launch_screenlet(name):
				screenlets.show_error(self, 'Failed to add %sScreenlet.' % name)
		elif id[:6] == "engine":
			# execute shell command
			engine = id[9:][:+20]
			self.set_engine(id[9:][:+20])
			self.redraw_canvas()
			print  (engine)
		#elif id[:7] == "engine7":
		#	screenlets.show_error(self, id[8:][:+10])
			#engine = 'Mininova'
		#	self.set_engine(id[6:][:+8] )
		#	self.redraw_canvas()

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(GmailScreenlet)
