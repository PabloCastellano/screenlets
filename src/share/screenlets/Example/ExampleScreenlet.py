#!/usr/bin/env python

#  ExampleScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - a simple example for creating a Screenlet
# 
# TODO:
# - make a nice Screenlet from this example ;) ....

import screenlets
from screenlets.options import StringOption
from screenlets.options import create_option_from_node


class ExampleScreenlet (screenlets.Screenlet):
	"""A simple example of how to create a Screenlet"""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'ExampleScreenlet'
	__version__	= '0.3'
	__author__	= 'RYX'
	__desc__	= __doc__	# set description to docstring of class
	
	# editable options (options that are editable through the UI)
	test_text = ''
	demo_text = ''
	demo_number = ''
	
	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=200, height=200, 
			uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add default menu items
		self.add_default_menuitems()
		# add option group
		group = self.create_option_group('Example', 'This is an example of ' +\
			' editable options within an OptionGroup ...')
		# add editable option to the group
		group.add_option(StringOption('Example', # group name
			'test_text', 						# attribute-name
			self.test_text,						# default-value
			'Test-Text', 						# widget-label
			'The Test-Text option for this Screenlet ...'	# description
			))
		# NEW: load options from file "ExampleScreenlet.xml" in screenlet's dir
		self.init_options_from_metadata()	# TEST
	
	# ONLY FOR TESTING!!!!!!!!!
	def init_options_from_metadata (self):
		"""Try to load metadata-file with options. The file has to be named
		like the Screenlet, with the extension ".xml" and needs to be placed
		in the Screenlet's personal directory. 
		NOTE: This function always uses the metadata-file relative to the 
			  Screenlet's location, not the ones in SCREENLETS_PATH!!!"""
		print __file__
		p = __file__.rfind('/')
		mypath = __file__[:p]
		print mypath
		self.add_options_from_file( mypath + '/' + \
			self.__class__.__name__ + '.xml')	
	
	def on_draw (self, ctx):
		# if theme is loaded
		if self.theme:
			# set scale rel. to scale-attribute
			ctx.scale(self.scale, self.scale)
			# TEST: render example-bg into context (either PNG or SVG)
			self.theme.render(ctx, 'example-bg')
			# render svg-file
			#self.theme['example-bg.svg'].render_cairo(ctx)
			# render png-file
			#ctx.set_source_surface(self.theme['example-test.png'], 0, 0)
			#ctx.paint()
	
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(ExampleScreenlet)

