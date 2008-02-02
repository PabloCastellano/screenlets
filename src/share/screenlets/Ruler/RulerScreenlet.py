#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  RulerScreenlet (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - a very basic screen-ruler with theming support
# 
# TODO:
# - owner-draw the scale and split the template into three parts
# - cm/pixel/inch modes
# - scale-interval and -length
# - ...

import screenlets
import cairo

#import os
#print "PWD: "+os.getcwd()

class RulerScreenlet (screenlets.Screenlet):
	"""A very simple screen-ruler Screenlet with theming support."""
	
	# default meta-info for Screenlets
	__name__	= 'RulerScreenlet'
	__version__	= '0.1'
	__author__	= 'RYX (Rico Pfaus) 2007'
	__desc__	= __doc__
	
	def __init__ (self, **keyword_args):
		#call super (and not show window yet)
		screenlets.Screenlet.__init__(self, show_window=False, 
			uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# theme loaded? set window size according to theme-size
		if self.theme:
			sizes = (self.theme.width, self.theme.height)
		else:
			sizes = (500, 100)
		self.window.resize(sizes[0], sizes[1])
		self.width	= sizes[0]
		self.height	= sizes[1]
		self.update_shape()
		# finally, show window
		self.window.show()

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()
	
	def on_draw (self, ctx):
		ctx.set_operator(cairo.OPERATOR_OVER)
		ctx.scale(self.scale, self.scale)
		if self.theme:
			#self.theme['ruler-bg.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'ruler-bg')
	
	def on_draw_shape (self,ctx):
		# simply call drawing handler and pass shape-context
		self.on_draw(ctx)

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(RulerScreenlet)

