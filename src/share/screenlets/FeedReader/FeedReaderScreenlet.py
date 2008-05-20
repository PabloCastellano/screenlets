#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  FeedReaderScreenlet (c) Whise 2007 

import screenlets
from screenlets import utils
from screenlets.options import StringOption , BoolOption , IntOption , FileOption , DirectoryOption , ListOption , AccountOption , TimeOption , FontOption, ColorOption , ImageOption
from screenlets import DefaultMenuItem
import pango
import gobject
import gtk
import os

is_manager = utils.is_manager_running_me()
try:
	import feedparser
except:
	if not is_manager:
		screenlets.show_message(None,'You don\'t have Feedparser installed! \nInstall python-feedparser or copy feedparser.py from rss/ folder to your screenlets folder.')
		sys.exit()
	else:
		print 'You don\'t have Feedparser installed! \nInstall python-feedparser or copy feedparser.py from rss/ folder to your screenlets folder.'


class FeedReaderScreenlet (screenlets.Screenlet):
	"""Customizable Application Menu"""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'FeedReaderScreenlet'
	__version__	= '0.1'
	__author__	= 'Helder Fraga aka Whise'
	__desc__	= __doc__	# set description to docstring of class

	# editable options (options that are editable through the UI)


	__timeout = None
	update_interval = 5
	feed_url = "http://digg.com/rss/index.xml"
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
	feed_number = 10
	feeds_mini = []
	feeds_full = []
	links = []
	
	mouse_is_over = False
	places = []
	old_places = []
	selected = 0
	mousesel = 0
	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=235, height=200, 
			uses_theme=True,ask_on_option_override = False,  **keyword_args)
		# set theme
		self.theme_name = "default"
		# add option group
		self.add_options_group('Options', 'Options')
		# add editable option to the group

		self.add_option(StringOption('Options', 'feed_url', 
			self.feed_url, 'Feed URL', 
			'Feed URL'), realtime=False)

		self.add_option(IntOption('Options', 'update_interval', 
			self.update_interval, 'Update interval', 
			'The interval for refreshing RSS feed (in minutes)', min=1, max=60))

		self.add_option(IntOption('Options','feed_number', 
			self.feed_number, 'Number of titles to display', 
			'Number of titles to display', 
			min=1, max=50))

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
			self.color_even, 'Even row Color', 
			''))

		self.add_option(ColorOption('Options','color_odd', 
			self.color_odd, 'Odd row Color', 
			''))

		self.add_option(ColorOption('Options','color_hover', 
			self.color_hover, 'Hover Color', 
			''))

		self.add_option(BoolOption('Options','show_shadow', 
			self.show_shadow, 'Show Shadow', '',))

		self.add_option(BoolOption('Options','expanded', 
			self.expanded, 'Expanded', '',hidden=True))

		# ADD a 1 second (1000) TIMER


		self.update_interval = self.update_interval


	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'feed_number':
			if self.height != 20 + ((self.feed_number)*30) +30:
				self.height = 20 + ((self.feed_number)*30) +30		
				self.redraw_canvas()
		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(int(value * 60000), self.refresh_feed)
			else:
				self.__dict__['update_interval'] = 1
				pass
		if name == 'feed_url':
			self.get_feeds()


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
		"""Called when the screenlet's drag-icon is creatself.feeds_mini[i]ed. You can supply
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
		
		# add default menu items
		self.add_default_menuitems()
		if self.height != 20 + ((self.feed_number)*30) +30:
			self.height = 20 + ((self.feed_number)*30) +30		
			self.redraw_canvas()
		self.feed_number = self.feed_number
		self.get_feeds()

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
			 
			if y > (30):
				click = int((y )/ (30)) -1
				
				os.system('xdg-open ' + self.links[click]  + ' &')
				
		return False
	
	def on_mouse_enter (self, event):
		"""Called when the mouse enters the Screenlet's window."""
		pass

		
	def on_mouse_leave (self, event):
		"""Called when the mouse leaves the Screenlet's window."""
		self.hide_tooltip()
		self.redraw_canvas()

	def on_mouse_move(self, event):
		"""Called when the mouse moves in the Screenlet's window."""
		x = event.x / self.scale
		y = event.y / self.scale
		if y > (30):
			self.__dict__['mousesel'] = int((y )/ (30)) -1
			if self.selected != self.mousesel or y > 20 + ((self.feed_number)*30) +30:
				
				self.redraw_canvas()	
				try:
					if self.x > gtk.gdk.screen_width()/2:
						self.show_tooltip(self.feeds_full[self.mousesel],self.x-(300*self.scale),self.y	+self.mousey)
					else:
						self.show_tooltip(self.feeds_full[self.mousesel],self.x+(235*self.scale),self.y+self.mousey)
				except:pass
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

	def refresh_feed(self):
		"""Redraw canvas to update the feed, used by the timeout function"""
		print("Refreshing feed...")
		self.get_feeds()
		self.redraw_canvas()
		print("Done!")
		return True

	def get_feeds(self):
		"""Get the summary and title of the selected feed"""
		self.feeds_mini = []
		self.feeds_full = []
		self.links = []
		for i in range(self.feed_number) :
				
			self.feeds_mini.insert(i,'')
			self.feeds_full.insert(i,'')
			self.links.insert(i,'')
		url = str(self.feed_url)
		f = feedparser.parse(url)
		#
		self.feed_number = self.feed_number
		#Get the summary of the newest item (0)
		#return  f['entries'][self.feed_number]['title'] + "\n\n" + f['entries'][self.feed_number]['summary']
		#print 
		try:
			for i in range(self.feed_number) :
			
				self.feeds_mini[i] = f['entries'][i]['title'] 
				self.feeds_full[i] = f['entries'][i]['summary']
			
				self.links[i] = f["channel"].get("link", "No link")
		
		except IndexError:
			self.__feed_text = 'Refreshing...'

	def on_draw (self, ctx):
		"""In here we draw"""
		ctx.scale(self.scale, self.scale)
		y = 0
		
		if self.expanded:
			if self.show_shadow:self.draw_shadow(ctx, 0, 0, self.width-12, self.height-15,6,[0,0,0,0.3])	
		else:
			if self.show_shadow:self.draw_shadow(ctx, 0, 0, self.width-12,40-5,6,[0,0,0,0.3])	
		ctx.translate(10,10)
		ctx.set_source_rgba(self.color_back[0],self.color_back[1],self.color_back[2],self.color_back[3])
		self.draw_rounded_rectangle(ctx,0,y,5,self.width-20,20,round_bottom_right= False,round_bottom_left= False)
		ctx.set_source_rgba(self.color_title[0],self.color_title[1],self.color_title[2],self.color_title[3])
		self.draw_text(ctx, 'Feed Reader',14,y+2,self.font_title.split(' ')[0],10,self.width-20,pango.ALIGN_LEFT)
		if self.expanded:
			ctx.rotate(3.14)
			self.draw_triangle(ctx,-15,-(y+17),10,10)
			ctx.rotate(-3.14)
			
		else:
			ctx.rotate(3.14/2)
			self.draw_triangle(ctx,3,-(y+15),10,10)
			ctx.rotate(-3.14/2)
		ctx.translate(0,20)			
		if self.expanded :
			x = 0
			
			for app in range(self.feed_number):
			
				if x % 2:
					ctx.set_source_rgba(self.color_even[0],self.color_even[1],self.color_even[2],self.color_even[3])
					#is_mounted = 'Mounted'
				else:
					ctx.set_source_rgba(self.color_odd[0],self.color_odd[1],self.color_odd[2],self.color_odd[3])
				
				if self.mousesel == x and self.mouse_is_over:
					ctx.set_source_rgba(self.color_hover[0],self.color_hover[1],self.color_hover[2],self.color_hover[3])
					#self.hide_tooltip()
					#self.show_tooltip(self.feeds_full[x],self.x+self.mousex,self.y+self.mousey)				
					self.__dict__['selected'] = x

				if self.feed_number-1 == app:
					self.draw_rounded_rectangle(ctx,0,y,5,self.width-20,30,round_top_right= False,round_top_left= False)	
				else:
					self.draw_rectangle(ctx,0,y,self.width -20,30)

				ctx.set_source_rgba(self.color_text[0],self.color_text[1],self.color_text[2],self.color_text[3])
				try:
					
					self.draw_text(ctx,self.feeds_mini[app][:100],5,y+2,self.font.split(' ')[0],8,self.width-22,pango.ALIGN_LEFT)
				except:pass
				#self.draw_icon(ctx,self.width-3030,y+2,ico,16,16)
				x = x+1
				y = y +30
			
		
			

	def on_draw_shape (self, ctx):
		self.on_draw(ctx)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(FeedReaderScreenlet)

