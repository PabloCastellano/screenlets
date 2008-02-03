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
from urllib2 import urlopen


class MyIpScreenlet(screenlets.Screenlet):
	"""A Screenlet that displays Internet Ip"""
	
	# default meta-info for Screenlets
	__name__ = 'MyIpScreenlet'
	__version__ = '0.2'
	__author__ = 'Helder Fraga aka Whise (c) 2007'
	__desc__ = 'A Screenlet that displays Internet Ip'
	p_layout = None
	myip = ""
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=200, height=50,uses_theme=True, **keyword_args) 

		self.theme_name = "default"
		self.add_default_menuitems(DefaultMenuItem.XML)

		self.gen()
		self.__timeout = gobject.timeout_add(24 * 60 * 60 * 1000, self.update)
	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'password':
			self.redraw_canvas()
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()

	def update (self):
		self.gen()
		self.redraw_canvas()
		return True # keep running this event	
	#def on_mouse_down(self, event):
		# do the active button's action
	#	if event.button == 1:
	#		self.gen()
		
	#def on_key_down(self, keycode, keyvalue, event):
	#	"""Called when a keypress-event occured in Screenlet's window."""
	#	key = gtk.gdk.keyval_name(event.keyval)
	#	if key == "Return" or key == "Tab":
	#		self.gen()
		

	def gen(self):
		site = urlopen("http://www.whatismyip.com/automation/n09230945.asp")
		self.myip = site.read()


	def on_draw(self, ctx):
		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			self.theme['background.svg'].render_cairo(ctx)
			self.theme['glass.svg'].render_cairo(ctx)
			ctx.save()
			ctx.translate(2, 9)
			if self.p_layout == None :
	
				self.p_layout = ctx.create_layout()
			else:
			
				ctx.update_layout(self.p_layout)
			p_fdesc = pango.FontDescription()
			p_fdesc.set_family_static("Free Sans")
			p_fdesc.set_size(16 * pango.SCALE)
			self.p_layout.set_font_description(p_fdesc)
			self.p_layout.set_width(((8 - 25) * pango.SCALE))
			#screenlets.show_message(self,self.password)
			self.p_layout.set_markup('IP - ' + self.myip)
			ctx.set_source_rgba(1, 1, 1, 1)
			ctx.show_layout(self.p_layout)
			ctx.fill()
			ctx.restore()
			
			ctx.save
	def on_menuitem_select (self, id):
		"""handle MenuItem-events in right-click menu"""
		if id[:4] == "upda":
			self.gen()
			# TODO: use DBus-call for this
			#self.switch_hide_show()
			self.redraw_canvas()

	def on_draw_shape(self,ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			
			self.theme['background.svg'].render_cairo(ctx)
			self.theme['glass.svg'].render_cairo(ctx)

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(MyIpScreenlet)
