#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  TomboyScreenlet (c) Whise 2007 

import screenlets
from screenlets import utils
from screenlets.options import StringOption , BoolOption , IntOption , FontOption, ColorOption
from screenlets import DefaultMenuItem
import pango
import gobject
import gtk
import os
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError
import re
import gnomevfs


class TomboyScreenlet (screenlets.Screenlet):
	"""Displays Tomboy Notes"""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'TomboyScreenlet'
	__version__	= '0.1'
	__author__	= 'Whise'
	__desc__	= __doc__	# set description to docstring of class

	# editable options (options that are editable through the UI)

	
	color_odd = (0, 0, 0, 0.55)
	color_even = (0, 0, 0, 0.65)
	color_title = (0.0, 0.0, 0.0, 1)
	color_text = (1,1,1,1)
	color_back = (1.0, 1.0, 1.0, 0.65)
	color_hover = (0, 0, 1.0, 0.65)
	font = "FreeSans"
	font_title = "FreeSans"
	show_shadow = True
	expanded = True
	hover = False
	number = 0


	mouse_is_over = False
	places = []
	old_places = []
	selected = 0
	mousesel = 0
	notes = None
	if os.environ.has_key("TOMBOY_PATH"):
		note_path = os.environ["TOMBOY_PATH"]
	else:
		note_path = "~/.tomboy"
	note_path = os.path.expanduser(note_path)

	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=200, height=200, 
			uses_theme=True,ask_on_option_override = False,  **keyword_args)
		# set theme
		self.theme_name = "yellow"
		# add option group
		self.add_options_group('Options', 'Options')
		# add editable option to the group

		self.add_option(FontOption('Options','font_title', 
			self.font_title, 'Title Font', 
			''))

		self.add_option(ColorOption('Options','color_title', 
			self.color_title, 'Title Color', 
			''))

		self.add_option(ColorOption('Options','color_back', 
			self.color_back, 'Title Background Color', 
			''))

		self.add_option(FontOption('Options','font', 
			self.font, 'Text Font', 
			''))

		self.add_option(ColorOption('Options','color_text', 
			self.color_text, 'Text Color', 
			''))

		self.add_option(ColorOption('Options','color_even', 
			self.color_even, 'Even Color', 
			''))

		self.add_option(ColorOption('Options','color_odd', 
			self.color_odd, 'Odd Color', 
			''))

		self.add_option(ColorOption('Options','color_hover', 
			self.color_hover, 'Hover Color', 
			''))

		self.add_option(BoolOption('Options','show_shadow', 
			self.show_shadow, 'Show Shadow', '',))

		self.add_option(BoolOption('Options','expanded', 
			self.expanded, 'Expanded', '',hidden=True))

		# ADD a 1 second (1000) TIMER

		self.ask_on_option_override = False
		
		#fstab = self.readFile('/etc/fstab')
		#mounts = self.readFile('/proc/mounts')




		self.notes = {}

		self.note_path_monitor = utils.FileMonitor(self.note_path)
		self.note_path_monitor.connect("event", self._file_event)
		self.note_path_monitor.open()

        # Load notes in an idle handler
		gobject.idle_add(self._idle_load_notes().next, priority=gobject.PRIORITY_LOW)


	def get_note(self,path):
		try:
			note_doc = parse(path)
		except (IOError, ExpatError), err:
			print " !!! Error parsing note '%s': %s" % (path, err)
			return

		try:
			title_node = note_doc.getElementsByTagName("title")[0]
			self.title = title_node.childNodes[0].data
		except (ValueError, IndexError, AttributeError):
			pass

		try:
		# Parse the ISO timestamp format .NET's XmlConvert class uses:
		# yyyy-MM-ddTHH:mm:ss.fffffffzzzzzz, where f* is a 7-digit partial
		# second, and z* is the timezone offset from UTC in the form -08:00.
			changed_node = note_doc.getElementsByTagName("last-change-date")[0]
			changed_str = changed_node.childNodes[0].data
			changed_str = re.sub("\.[0-9]*", "", changed_str) # W3Date chokes on partial seconds
			#self.timestamp = W3CDate.W3CDate(changed_str).getSeconds()
		except (ValueError, IndexError, AttributeError):
			pass

		try:
			content_node = note_doc.getElementsByTagName("note-content")[0]
			self.content_text = self._get_text_from_node(content_node).lower()
		except (ValueError, IndexError, AttributeError):
			pass

		return self.title

		note_doc.unlink()

	def _get_text_from_node(self, node):
		if node.nodeType == node.TEXT_NODE:
			return node.data
		else:
			return "".join([self._get_text_from_node(x) for x in node.childNodes])

	def _idle_load_notes(self):
		notes = {}

		try: 
			for filename in os.listdir(self.note_path):
				if filename.endswith(".note"):
					notepath = os.path.join(self.note_path, filename)
					notes[filename] = self.get_note(notepath)
					yield True
		except (OSError, IOError), err:
			print " !!! Error loading Tomboy notes:", err

		self.notes = notes
		self.redraw_canvas()
		yield False

	def _file_event(self, monitor, info_uri, ev):
		filename = os.path.basename(info_uri)

		if ev == gnomevfs.MONITOR_EVENT_CREATED:
			notepath = os.path.join(self.note_path, filename)
			self.notes[filename] = self.get_note(notepath)
			if self.height != 20 + (len(self.notes)*20) +20:
				self.height = 20 + (len(self.notes)*20) +20		
				self.redraw_canvas()

		elif self.notes.has_key(filename):
			if ev == gnomevfs.MONITOR_EVENT_DELETED:
				del self.notes[filename]
				if self.height != 20 + (len(self.notes)*20) +20:
					self.height = 20 + (len(self.notes)*20) +20		
					self.redraw_canvas()
			else:
				if self.height != 20 + (len(self.notes)*20) +20:
					self.height = 20 + (len(self.notes)*20) +20		
					self.redraw_canvas()


	def menuitem_callback(self, widget, id):
		screenlets.Screenlet.menuitem_callback(self, widget, id)
		if id=="new":
			os.system("tomboy --new-note")

	def get_items_uncached(self):
		return [self.new_note_item] + self.notes.values()



	def get_items(self):
        # Avoid ItemSource's caching
		return self.get_items_uncached()

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'notes':
			if self.height != 20 + (len(self.notes)*20) +20:
				self.height = 20 + (len(self.notes)*20) +20		
				self.redraw_canvas()
		
	
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





	def on_after_set_atribute(self,name, value):
		"""Called after setting screenlet atributes"""
		
		pass

	def on_before_set_atribute(self,name, value):
		"""Called before setting screenlet atributes"""
		
		pass


	def on_create_drag_icon (self):
		"""Called when the screenlet's drag-icon is created. You can supply
		your own icon and mask by returning them as a 2-tuple."""
		return (None, None)

	def on_composite_changed(self):
		"""Called when composite state has changed"""
		pass

	def on_drag_begin (self, drag_context):
		"""Called when the Screenlet gets dragged."""
		pass
	
	def on_drag_enter (self, drag_context, x, y, timestamp):
		"""Called when something gets dragged into the Screenlets area."""
		pass
	
	def on_drag_leave (self, drag_context, timestamp):
		"""Called when something gets dragged out of the Screenlets area."""
		pass

	def on_drop (self, x, y, sel_data, timestamp):
		"""Called when a selection is dropped on this Screenlet."""
		return False
		
	def on_focus (self, event):
		"""Called when the Screenlet's window receives focus."""
		pass
	
	def on_hide (self):
		"""Called when the Screenlet gets hidden."""
		pass
	
	def on_init (self):
		"""Called when the Screenlet's options have been applied and the 
		screenlet finished its initialization. If you want to have your
		Screenlet do things on startup you should use this handler."""
		self.add_menuitem("new", "Make new note")		
		# add default menu items
		self.add_default_menuitems()
		if self.notes != None:
			if self.height != 20 + (len(self.notes)*20) +20:
				self.height = 20 + (len(self.notes)*20) +20		
				self.redraw_canvas()
		#print utils.LoadBookmarks()
		
	def on_key_down(self, keycode, keyvalue, event):
		"""Called when a keypress-event occured in Screenlet's window."""
		#key = gtk.gdk.keyval_name(event.keyval)
		
		pass
	
	def on_load_theme (self):
		"""Called when the theme is reloaded (after loading, before redraw)."""
		pass
	
	def on_menuitem_select (self, id):
		"""Called when a menuitem is selected."""
		
		pass
	
	def on_mouse_down (self, event):
		"""Called when a buttonpress-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		
		x = event.x / self.scale
		y = event.y / self.scale
		if event.button == 1:
			if event.type == gtk.gdk._2BUTTON_PRESS and y < 30: 
				self.expanded = not self.expanded
			 
			if y > (30) and self.notes != None:
				click = int((y -10 )/ (20)) -1
				a = 0
				for note in self.notes:
					if click == a:
						
						os.system("tomboy --open-note %s/%s " % (self.note_path,note))
					a = a+1

				
		return False
	
	def on_mouse_enter (self, event):
		"""Called when the mouse enters the Screenlet's window."""
	

		
	def on_mouse_leave (self, event):
		"""Called when the mouse leaves the Screenlet's window."""
		
		self.redraw_canvas()

	def on_mouse_move(self, event):
		"""Called when the mouse moves in the Screenlet's window."""
		x = event.x / self.scale
		y = event.y / self.scale
		if y > (30):
			self.__dict__['mousesel'] = int((y -10 )/ (20)) -1
			if self.selected != self.mousesel or y > 20 + (len(self.notes)*20) +20:				
				self.redraw_canvas()
				
	def on_mouse_up (self, event):
		"""Called when a buttonrelease-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		return False
	
	def on_quit (self):
		"""Callback for handling destroy-event. Perform your cleanup here!"""
		
		return True
		
	def on_realize (self):
		""""Callback for handling the realize-event."""
	
	def on_scale (self):
		"""Called when Screenlet.scale is changed."""
		pass
	
	def on_scroll_up (self):
		"""Called when mousewheel is scrolled up (button4)."""
		pass

	def on_scroll_down (self):
		"""Called when mousewheel is scrolled down (button5)."""
		pass
	
	def on_show (self):
		"""Called when the Screenlet gets shown after being hidden."""
		pass
	
	def on_switch_widget_state (self, state):
		"""Called when the Screenlet enters/leaves "Widget"-state."""
		pass
	
	def on_unfocus (self, event):
		"""Called when the Screenlet's window loses focus."""
		pass
	
	def on_draw (self, ctx):
		"""In here we draw"""
		ctx.scale(self.scale, self.scale)
		y = 0

		if self.expanded:
			if self.show_shadow:self.draw_shadow(ctx, 0, 0, self.width-12, self.height-5,6,[0,0,0,0.3])	
		else:
			if self.show_shadow:self.draw_shadow(ctx, 0, 0, self.width-12,40-5,6,[0,0,0,0.3])	
		ctx.translate(10,10)
		ctx.set_source_rgba(self.color_back[0],self.color_back[1],self.color_back[2],self.color_back[3])
		self.draw_top_rounded_rectangle(ctx,0,y,5,self.width-20,20)
		ctx.set_source_rgba(self.color_title[0],self.color_title[1],self.color_title[2],self.color_title[3])
		self.draw_text(ctx, 'Notes',14,y+2,self.font_title.split(' ')[0],10,self.width-20,pango.ALIGN_LEFT)
		if self.expanded:
			ctx.rotate(3.14)
			self.draw_triangle(ctx,-15,-(y+17),10,10)
			ctx.rotate(-3.14)
			
		else:
			ctx.rotate(3.14/2)
			self.draw_triangle(ctx,3,-(y+15),10,10)
			ctx.rotate(-3.14/2)
		ctx.translate(0,20)			
		if self.expanded and self.notes != None:
			x = 0
			
			
			for app  in self.notes:
				if x % 2:
					ctx.set_source_rgba(self.color_even[0],self.color_even[1],self.color_even[2],self.color_even[3])
					#is_mounted = 'Mounted'
				else:
					ctx.set_source_rgba(self.color_odd[0],self.color_odd[1],self.color_odd[2],self.color_odd[3])
				if self.check_for_icon(app):
					ico = 'tomboy'
				else:
					ico = 'stock_search-and-replace'


				if self.mousesel == x and self.mouse_is_over:
					ctx.set_source_rgba(self.color_hover[0],self.color_hover[1],self.color_hover[2],self.color_hover[3])
					self.__dict__['selected'] = x

				if y +60== self.height:
					self.draw_bottom_rounded_rectangle(ctx,0,y,5,self.width-20,20)	
				else:
					self.draw_rectangle(ctx,0,y,self.width -20,20)

				ctx.set_source_rgba(self.color_text[0],self.color_text[1],self.color_text[2],self.color_text[3])
			
				self.draw_text(ctx,self.notes[app],5,y+2,self.font.split(' ')[0],10,self.width-20,pango.ALIGN_LEFT)
				a = self.get_screenlet_dir() + '/themes/' + self.theme_name + '/icon.png'
				self.draw_scaled_image(ctx,self.width-40,y+2,a,16,16)
				x = x+1
				y = y +20
			
		
			

	def on_draw_shape (self, ctx):
		self.on_draw(ctx)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(TomboyScreenlet)

