#!/usr/bin/env python

#  StorageScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - A simple storage-Screenlet that collects things dragged onto it.
#   This is mainly a testbed for the new drag&drop features but can
#   be really useful once ready.
# 
# TODO:
# - add some usefulness :D
# - ...

import screenlets
from screenlets.options import StringOption, ListOption
from screenlets import DefaultMenuItem

import cairo
import gtk


class StorageScreenlet (screenlets.Screenlet):
	"""A container for dragging things onto/into it (UNFINISHED AND ONLY
	FOR DEMONSTRATION YET)."""
	
	# default meta-info for Screenlets
	__name__	= 'StorageScreenlet'
	__version__	= '0.1'
	__author__	= 'RYX (Rico Pfaus) 2007'
	__desc__	= __doc__
	
	# internals
	
	# options
	uris	= []
	texts	= []
	
	# constructor
	def __init__ (self, **keyword_args):
		# call super (and init drag&drop)
		screenlets.Screenlet.__init__(self, drag_drop=True, 
			uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add menuitems
		self.add_menuitem('show_data', 'Show content ...')
		# add default menu items
		self.add_default_menuitems(DefaultMenuItem.DELETE |
			DefaultMenuItem.PROPERTIES |
			DefaultMenuItem.THEMES)
		# add option group
		group = self.create_option_group('Storage', 'Storage-options.')
		# add some editable options
		group.add_option(ListOption('uris', self.uris, 'Stored URLs', 
			'The list of URLs stored in this Storage ...'))		
		group.add_option(ListOption('texts', self.texts, 'Stored Texts', 
			'The list of texts stored in this Storage ...'))
	
	def on_menuitem_select (self, id):
		print id
	
	def on_drag_enter (self, drag_context, x, y, timestamp):
		self.redraw_canvas()
	
	def on_drag_leave (self, drag_context, timestamp):
		self.redraw_canvas()
	
	def on_drop (self, x, y, sel_data, timestamp):
		print "Data dropped ..."
		txt = sel_data.get_text()
		if txt[-1] == '\n':
			txt = txt[:-1]
		txt.replace('\n', '\\n')
		print "TEXT: "+txt
		if txt:
			self.texts.append(txt)		# DOES NOT CALL __SETATTR__ !!!
			self.texts = self.texts		# so we need to call it manually
		uris = sel_data.get_uris()
		if uris:
			self.uris.append(uris)
			self.uris = self.uris	
		#print sel_data.get_pixbuf()
		#print sel_data.get_targets()
		
	def on_draw (self, ctx):
		# set scale rel. to scale-attribute
		ctx.scale(self.scale, self.scale)
		# if theme is loaded
		if self.theme:
			# render svg-file
			if self.dragging_over:
				#self.theme['storage-dragged-over.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'storage-dragged-over')
			else:
				#self.theme['storage-empty.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'storage-empty')
		else:
			ctx.set_source_rgba(1, 1, 1, 0.8)
			ctx.rectangle(0, 0, 100, 100)
			ctx.fill()
	
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)


# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(StorageScreenlet)

