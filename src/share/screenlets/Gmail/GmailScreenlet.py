#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# GmailScreenlet (c) Whise <helder.fraga@hotmail.com>



import screenlets
from screenlets.options import StringOption, IntOption, AccountOption
import cairo
import pango
import gtk
from os import system
import gobject
from screenlets import DefaultMenuItem
from screenlets import Plugins
mail = Plugins.importAPI('Mail')



class GmailScreenlet(screenlets.Screenlet):
	"""A screenlet that shows your unread gmail message count , click on the mail icon to go to gmail.com"""
	
	# default meta-info for Screenlets
	__name__ = 'GmailScreenlet'
	__version__ = '0.7'
	__author__ = 'Helder Fraga'
	__desc__ = 'A screenlet that shows your unread gmail message count'

	# a list of the converter class objects



	__timeout = None
	update_interval = 60
	forecast = ''
	msgs = ' 0'
	account = ('', '')	

	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=275, height=242, uses_theme=True,	**keyword_args)
		# set theme
		self.theme_name = "default"
		# add default menu items

		self.add_options_group('gmail', 'Gmail Screenlet settings ...')
		self.add_option(IntOption('gmail', 'update_interval', 
			self.update_interval, 'Update interval', 'The interval for updating info (in seconds ,3660 = 1 day, 25620 = 1 week)', min=30, max=25620))
		self.add_option(AccountOption('gmail', 'account', 
			self.account, 'Username/Password', 
			'Enter username/password here ...'))
		self.update_interval = self.update_interval

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'account':
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
		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_default_menuitems()

	def update(self):
		self.check()
		self.redraw_canvas()
		return True

	def check(self):

		if self.account[0] != '' and self.account[1] != '':
			n = self.account[0].replace('@gmail.com','')
			try:
				self.msgs = mail.get_GMail_Num(n, self.account[1])
				print str(self.msgs) + ' Unread Messages'
			except:self.msgs = 0
		else:
			self.msgs = 0


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
		ctx.scale(self.scale, self.scale)
		# render background
		self.theme.render(ctx, 'gmail')
	

		if self.msgs == None: self.msgs = 0
		if int(self.msgs) < 10:
			s = 36
			x,y = (188, 182)
		elif int(self.msgs) >= 10 and int(self.msgs) <= 99:
			s = 30
			x,y =(180, 187)
		elif int(self.msgs) >= 100 and int(self.msgs) <= 999:
			s = 24
			x,y =(175, 187)
		elif int(self.msgs) >= 1000:
			s = 20
			ctx.translate(170, 190)
		else:
			s = 36
			x,y = (188, 182)

		ctx.set_source_rgba(1, 1, 1, 0.9)
		self.draw_text(ctx,'<b>'+ str(self.msgs) +'</b>',x,y, 'FreeSans',s, self.width)
		
	def on_draw_shape(self, ctx):
		if self.theme:
			ctx.scale(self.scale, self.scale)

			self.theme.render(ctx, 'gmail')

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id == "update":
			self.check()
			self.redraw_canvas()


# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(GmailScreenlet)
