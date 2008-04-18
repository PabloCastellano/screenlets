#!/usr/bin/env python

#
#TrashScreenlet Copyright (C) 2007 Helder Fraga
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
from screenlets.options import  BoolOption
import cairo
import pango
import os
import gtk
import gobject

class TrashScreenlet(screenlets.Screenlet):
	"""A shut down screenlet"""
	
	# default meta-info for Screenlets
	__name__ = 'TrashScreenlet'
	__version__ = '0.1'
	__author__ = 'Helder Fraga aka Whise (c) 2007'
	__desc__ = 'A Screenlet that shows information about your trash folder'
	
	style = False
	show_count = True
	if os.path.exists(os.environ['HOME'] +'/.local/share/Trash/files') and os.path.isdir(os.environ['HOME'] +'/.local/share/Trash/files'):
		trash_folder = os.environ['HOME'] +'/.local/share/Trash/files'
	else:
		trash_folder = os.environ['HOME'] + '/.Trash'
	item_count = 0
	def __init__(self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=128, height=160,drag_drop=True, **keyword_args) 

		self.theme_name = "default"

		self.add_options_group('Options', 'Options')
		self.add_option(BoolOption('Options', 'style', self.style, 
			'Use gtk style', 'Use gtk icon'))	
		self.add_option(BoolOption('Options', 'show_count', self.show_count, 
			'show item count', 'Show item count'))	
		self.refresh_timeout = gobject.timeout_add(1000, self.update)




	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		
		if name == 'style':
			self.redraw_canvas()

	def on_drop (self, x, y, sel_data, timestamp):
		print "Data dropped ..."
		filename = ''
		# get text-elements in selection data
		txt = sel_data.get_text()
		if txt:
			if txt[-1] == '\n':
				txt = txt[:-1]
			txt.replace('\n', '\\n')
			# if it is a filename, use it
			if txt.startswith('file://'):
				filename = txt[7:]
			else:
				screenlets.show_error(self, 'Invalid string: %s.' % txt)
		else:
			# else get uri-part of selection
			uris = sel_data.get_uris()
			if uris and len(uris)>0:
				#print "URIS: "+str(uris	)
				filename = uris[0][7:]
		if filename != '':
			#self.set_image(filename)
			import urllib
			filename = urllib.unquote(filename)
			#if screenlets.show_question(self,'Do you want to send '+ filename' in your Trash folder?'):
			os.system('mv ' + filename + ' ' + self.trash_folder)
		
	def update(self):
		self.trash_folder = os.environ['HOME'] + '/.Trash'
		self.item_count = len(os.listdir(self.trash_folder))
			#self.item_count = self.item_count + 1
		self.redraw_canvas()
		return True

	def on_mouse_down(self, event):
		if event.type == gtk.gdk._2BUTTON_PRESS: 
			if event.button == 1:
				os.system('xdg-open ' + self.trash_folder + ' &')
		
	def menuitem_callback(self, widget, id):
		screenlets.Screenlet.menuitem_callback(self, widget, id)
		if id=="clean":
			if screenlets.show_question(self,'Do you want to permanently remove all the items in your Trash folder?'):
				os.system('rm -rf ' + self.trash_folder + '/*')
				os.system('rm -rf ' + self.trash_folder + '/*.*')
				os.system('rm -rf ' + self.trash_folder + '/.*')
				self.update()
		elif id=="open":
			os.system('xdg-open ' + self.trash_folder  + ' &')

	def on_init(self):	
		self.add_menuitem("clean", "Empty Trash...")
		self.add_menuitem("open", "Open Trash...")
		#self.add_menuitem("forecast", "View extended forecast")
		self.add_default_menuitems()
		self.update()

	def on_draw(self, ctx):

		if self.theme:
			ctx.set_operator(cairo.OPERATOR_OVER)
			ctx.scale(self.scale, self.scale)
			if self.item_count == 0:
				ico = 'user-trash-empty'
				try:
					icontheme = gtk.icon_theme_get_default()
					image = icontheme.load_icon (ico,width,height)
				except:
					ico = 'emptytrash'
			else:
				ico = 'user-trash-full'
				try:
					icontheme = gtk.icon_theme_get_default()
					image = icontheme.load_icon (ico,width,height)
				except:
					ico = 'trashcan_full'
			if self.style == True:	
				try:
					self.draw_icon(ctx,0,0,ico,128,128)
				except:
					self.draw_icon(ctx,0,0,ico,128,128)				
			else:
				if self.item_count == 0:
					ico = 'user-trash-empty'
				else:
					ico = 'user-trash-full'
				self.theme.render(ctx,ico)
			if self.show_count:
				ctx.set_source_rgba(1,1,1,0.65)
				self.draw_rounded_rectangle(ctx,20,128,5,self.width-40,23)
				ctx.set_source_rgba(0,0,0,1)
				self.draw_text(ctx,str(self.item_count) + ' Items',0,132,"FreeSans",10,self.width,pango.ALIGN_CENTER)
			
	def on_draw_shape(self,ctx):
	
		if self.theme:
			self.on_draw(ctx)

if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(TrashScreenlet)
