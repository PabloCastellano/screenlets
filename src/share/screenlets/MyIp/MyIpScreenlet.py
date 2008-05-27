#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#MyIpScreenlet (c) Whise <helder.fraga@hotmail.com>

import screenlets
from screenlets.options import FloatOption, BoolOption, StringOption, FontOption, ColorOption, IntOption
from screenlets import DefaultMenuItem
import cairo
import pango
import gobject
from urllib import urlopen
from screenlets import Plugins
proxy = Plugins.importAPI('Proxy')



class MyIpScreenlet(screenlets.Screenlet):
	"""A Screenlet that displays Internet Ip"""
	
	# default meta-info for Screenlets
	__name__ = 'MyIpScreenlet'
	__version__ = '0.3'
	__author__ = 'Helder Fraga aka Whise (c) 2007'
	__desc__ = 'A Screenlet that displays Internet Ip'

	font_color = (1,1,1, 0.8)
	background_color = (0,0,0, 0.8)
	myip = ""
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=50,uses_theme=True, **keyword_args) 

		self.theme_name = "default"
		self.add_default_menuitems(DefaultMenuItem.XML)
                self.add_options_group('Options',
                        'The Options widget settings')


		self.add_option(ColorOption('Options','font_color', 
			self.font_color, 'Text color', 'font_color'))
		self.add_option(ColorOption('Options','background_color', 
			self.background_color, 'Back color(only with default theme)', 'only works with default theme'))
	
		self.gen()
		self.__timeout = gobject.timeout_add(24 * 60 * 60 * 1000, self.update)

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()

	def update (self):
		self.gen()
		self.redraw_canvas()
		return True # keep running this event	

		

	def gen(self):
		try:
			proxies = proxy.Proxy().get_proxy()
			self.myip = str(urlopen("http://www.whatismyip.com/automation/n09230945.asp",proxies=proxies).read())

		except:
			from screenlets import sensors
			self.myip = str(sensors.net_get_ip())

	def on_draw(self, ctx):
		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			self.theme.render(ctx,'background')

			ctx.set_source_rgba(*self.background_color)
			if self.theme_name == 'default':self.draw_rounded_rectangle(ctx,0,0,6,200,40)
			ctx.set_source_rgba(1, 1, 1, 1)
			ctx.set_source_rgba(*self.font_color)
			self.draw_text(ctx,'IP - ' + self.myip,0,10, 'FreeSans',16, self.width,allignment = pango.ALIGN_CENTER)
			try:self.theme.render(ctx,'glass')
			except:pass

	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id[:4] == "upda":
			self.gen()
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()

	def on_draw_shape(self,ctx):
		ctx.rectangle(0,0,self.width,self.height)
		ctx.fill()
		self.on_draw(ctx)

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(MyIpScreenlet)
