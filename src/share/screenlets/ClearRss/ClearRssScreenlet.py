#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  ClearRssScreenlet (c) Whise <helder.fraga@hotmail.com>
#


import screenlets
import cairo
import pango
import sys
import gtk
import gobject
from screenlets import DefaultMenuItem, utils
from screenlets.options import IntOption, BoolOption, StringOption, FontOption, ColorOption, FloatOption
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

class ClearRssScreenlet(screenlets.Screenlet):
	"""Screenlet for reading RSS and Atom feeds , with the ability to scroll through all of the rss txt , ability to visit the rss news site"""
	
	__name__ = 'ClearRssScreenlet'
	__version__ = '0.1'
	__author__ = 'Helder Fraga aka Whise based on Rss Screenlet Hendrik Kaju'
	__desc__ = 'Screenlet for reading RSS and Atom feeds , with the ability to scroll through all of the rss txt , ability to visit the rss news site'
	
	#Internals
	__timeout = None
	__feed_text = "Refreshing..."
	scrol = 180
	text_x = 10
	text_y = 10
	feed_name = ""
	feed_url = ""
	feed_number = 0
	font_name = "Free Sans 11"
	font = 'FreeSans'
	use_custom_feed = False
	rgba_color = (1, 1, 1, 0.9)
	update_interval = 5
	show_feed_name = True
	a = ''
	__button_pressed = 1
	p_layout = None
	background_color = (0,0,0, 0.8)

	def __init__(self, **keyword_args):
		"""Create a RssScreenlet instance"""
		screenlets.Screenlet.__init__(self, width=200, height=200, 
			uses_theme=True, **keyword_args)
		self.theme_name = "default"
		self.add_menuitem("next", "next")
		self.add_options_group('Rss', 'Rss-specific settings.')
		self.add_options_group('Text', 'Text settings.')
		self.add_option(ColorOption('Text', 'rgba_color', 
			self.rgba_color, 'Default Color', 
			'The default color of the text (when no Markup is used) ...'))
		self.add_option(FontOption('Text','font', 
			self.font, 'Text Font', 
			'Text font'))
		self.add_option(StringOption('Rss', 'feed_name', 
			self.feed_name, 'Feed name', 
			'Feed name',), realtime=False)
		self.add_option(StringOption('Rss', 'feed_url', 
			self.feed_url, 'Feed URL', 
			'Feed URL'), realtime=False)
		self.add_option(IntOption('Rss', 'update_interval', 
			self.update_interval, 'Update interval', 
			'The interval for refreshing RSS feed (in minutes)', min=1, max=60))
		self.add_option(ColorOption('Rss','background_color', 
			self.background_color, 'Back color(only with default theme)', 'only works with default theme'))
		#self.add_menuitem("next", "next")
		#self.add_menuitem("prev", "prev")
		self.update_interval = self.update_interval
		gobject.timeout_add(int(100), self.show_text)
		self.set_feed("Digg", "http://digg.com/rss/index.xml")
	def __setattr__(self, name, value):
		screenlets.Screenlet.__setattr__(self, name, value)
		if name in ('text_x', 'text_y', 'font_name', 
				'rgba_color', 'feed_text', 'feed_name', 
				'feed_url', 'show_feed_name'):
			if self.window:
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
		if name == 'font': self.font_name = str(value).split(' ')[0]

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems(DefaultMenuItem.XML)
		self.add_default_menuitems()

							
	def menuitem_callback(self, widget, id):
		screenlets.Screenlet.menuitem_callback(self, widget, id)
		if id=="next":
			if len(self.__feed_text)> self.scrol:
	
				self.scrol = self.scrol + 180
			self.redraw_canvas()
		if id=="prev":
			if self.scrol > 180:
		
				self.scrol = self.scrol - 180
			self.redraw_canvas()
		if id=="select_feed":
			self.show_feed_dialog()
		if id=="option_changed":
			self.option_changed()
		if id=="refresh":
			self.refresh_feed()
		if id=="prev_item":
			self.scrol = 180
			self.feed_number = self.feed_number + 1
			self.refresh_feed()
		if id=="next_item":
			self.scrol = 180
			self.feed_number = self.feed_number - 1
			self.refresh_feed()
		#TODO: create only one callback for set_feed
		if id =="firefox":
			print self.link
			
			if self.link != '':
				os.system("firefox " + self.link +" &")
				print 'going1'
			
		if id =="set_feed_gnome":
			self.set_feed("GnomeFiles", "http://www.gnomefiles.org/gnomefiles.xml")
		if id =="set_feed_dig":
			self.set_feed("Digg", "http://digg.com/rss/index.xml")
		if id =="set_feed_linuxinsider":
			self.set_feed("Linux Insider", "http://linuxinsider.com/perl/syndication/rssfull.pl")
		if id =="set_feed_ubuntuforums":
			self.set_feed("Ubuntuforums.org", "http://ubuntuforums.org/external.php?type=RSS2")
		if id =="set_feed_distrowatch":
			self.set_feed("Distrowatch", "http://distrowatch.com/news/dw.xml")
		if id =="set_feed_bbc":
			self.set_feed("BBC News", "http://newsrss.bbc.co.uk/rss/newsonline_world_edition/front_page/rss.xml")
		if id =="set_feed_osnews":
			self.set_feed("OSNews", "http://osnews.com/files/recent.xml")
		if id =="set_feed_script":
			self.set_feed("Scripting News", "http://www.scripting.com/rss.xml")
		if id =="set_feed_cnet":
			self.set_feed("CNET News.com", "http://news.com.com/2547-1_3-0-5.xml")
		if id =="set_feed_yahoo":
			self.set_feed("Yahoo Tech", "http://rss.news.yahoo.com/rss/tech")
		if id =="set_feed_wired":
			self.set_feed("Wired News", "http://www.wired.com/news_drop/netcenter/netcenter.rdf")
		if id =="set_feed_glook":
			self.set_feed("Gnome-look", "http://www.gnome-look.org/gnome-look-content.rdf")
		#TODO: fix feeds with images
		"""if id =="set_feed_cnn":
		self.set_feed("CNN", "http://rss.cnn.com/rss/cnn_latest.rss")"""
	def on_mouse_down(self, event):
		
		if event.type == gtk.gdk.BUTTON_PRESS:
			return self.detect_button(event.x, event.y)
		else:
			return True
		return False

	def on_mouse_up(self, event):
		# do the active button's action
		if self.__button_pressed:
			if self.__button_pressed == 3:
				if len(self.__feed_text)> self.scrol:
				
					self.scrol = self.scrol + 180
					self.redraw_canvas()
			elif self.__button_pressed == 2:
				self.scrol = 180
				self.redraw_canvas()
			elif self.__button_pressed == 1:
				if self.scrol > 180:
			
					self.scrol = self.scrol - 180
					self.redraw_canvas()
			self.__button_pressed = 0
			self.redraw_canvas()
		return False

	def detect_button(self, x, y):
		x /= (self.scale)
		y /= (self.scale)
		button_det = 0
		if y >= 183 and y <= 196.7:
			if x >= 135 and x <= 149:
				button_det = 1
			elif x >= 155 and x <= 168:
				button_det = 2
			elif x >= 174 and x <= 187:
				button_det = 3
		self.__button_pressed = button_det
		if button_det:
			self.redraw_canvas()
			return True	# we must return boolean for Screenlet.button_press
		else:
			return False

	def on_draw(self, ctx):
		ctx.scale(self.scale, self.scale)

		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			ctx.set_source_rgba(*self.background_color)
			if self.theme_name == 'default':self.draw_rounded_rectangle(ctx,0,0,17,200,200)
			self.theme.render(ctx,'background')
		ctx.save()
		feed_text = self.__feed_text
		name = str(self.feed_name)
		om = '<span font_desc="'+self.font_name+'">'
		cm = '</span>'
		if len(self.__feed_text)> self.scrol:
			self.a = '...(more)'
		else:
			self.a = ''
		self.b = '\n'
		if self.scale > 1 or self.scale <= 0.7:
			self.b =''
		feed_text = self.strip_ml_tags(feed_text)
		ctx.set_source_rgba(*self.rgba_color)
		t = "<b>" + name + "</b>" + "\n" + self.b + feed_text[:self.scrol][self.scrol-180:] + self.a
		self.draw_text(ctx, t , self.text_x, self.text_y, self.font_name, 9.5, (self.width - self.text_x) , pango.ALIGN_LEFT)
		ctx.fill()
		ctx.restore()
		
	def on_draw_shape(self,ctx):
		ctx.rectangle(0,0,self.width,self.height)
		ctx.fill()
		self.on_draw(ctx)

	def strip_ml_tags(self,in_text):
	
		# convert in_text to a mutable object (e.g. list)
		s_list = list(in_text)
		i,j = 0,0
	
		while i < len(s_list):
		# iterate until a left-angle bracket is found
			if s_list[i] == '<':
				while s_list[i] != '>':
				
					s_list.pop(i)
				
			# pops the right-angle bracket, too
				s_list.pop(i)
			else:
				i=i+1
			
		# convert the list back into text
		join_char=''
		return join_char.join(s_list)

	def get_feed(self):
		"""Get the summary and title of the selected feed"""
		url = str(self.feed_url)
		f = feedparser.parse(url)

		try:
			self.__feed_text = f['entries'][self.feed_number]['title'] + "\n\n" + f['entries'][self.feed_number]['summary']
			self.link = f["channel"].get("link", "No link")
			
		except IndexError:
			self.__feed_text = 'Refreshing...'

	def refresh_feed(self):
		"""Redraw canvas to update the feed, used by the timeout function"""
		print("Refreshing feed...")
		self.scrol = 180
		self.get_feed()
		self.redraw_canvas()
		print("Done!")
		return True
		
	def show_text(self):
		"""Show text on startup properly, return false to do it only once"""
		print("Loading text...")
		self.get_feed()
		self.redraw_canvas()
		print("Done!")
		return False

	def set_feed(self, name, url):
		"""Helper function to set the active feed"""
		self.feed_name = name
		self.feed_url = url
		self.refresh_feed()

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(ClearRssScreenlet)

