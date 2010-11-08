# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# a very hackish, XML-based menu-system (c) RYX (Rico Pfaus) 2007
#
# NOTE: This thing is to be considered a quick hack and it lacks on all ends.
#       It should be either improved (and become a OOP-system ) or removed
#       once there is a suitable alternative ...
#

import glob, gtk
import xml.dom.minidom
from xml.dom.minidom import Node
import os
import gettext

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)

def add_menuitem (menu, label, callback=None, cb_data=None):
	"""Convenience function to create a menuitem, connect
	a callback, and	add the menuitem to menu."""
	if label == "-":
		item = gtk.SeparatorMenuItem()
	else:
		item = gtk.MenuItem(label)
	return add_menuitem_with_item(menu, item, callback, cb_data)

def add_image_menuitem (menu, stock, label=None, callback=None, cb_data=None):
	"""Convenience function to create an ImageMenuItem, connect
	a callback, and add the menuitem to menu."""
	item = ImageMenuItem(stock, label)
	return add_menuitem_with_item(menu, item, callback, cb_data)
	
def add_menuitem_with_item (menu, item, callback=None, cb_data=None):
	"""Convenience function to add a menuitem to a menu
	and connect a callback."""
	if callback:
		if cb_data:
			item.connect("activate", callback, cb_data)
		else:
			item.connect("activate", callback)
	menu.append(item)
	item.show()
	return item

def create_menu_from_file (filename, callback):
	"""Creates a menu from an XML-file and returns None if something went wrong"""
	doc = None
	try:
		doc = xml.dom.minidom.parse(filename)
	except Exception, e:
		print "XML-Error: %s" % str(e)
		return None
	return create_menu_from_xml(doc.firstChild, callback)

def create_menu_from_xml (node, callback, icon_size=22):
	"""Create a gtk.Menu by an XML-Node"""
	menu = gtk.Menu()
	for node in node.childNodes:
		#print node
		type = node.nodeType
		if type == Node.ELEMENT_NODE:
			label = node.getAttribute("label")
			id = node.getAttribute("id")
			item = None
			is_check = False
			# <item> gtk.MenuItem
			if node.nodeName == "item":
				item = gtk.MenuItem(label)
			# <checkitem> gtk.CheckMenuItem
			elif node.nodeName == "checkitem":
				item = gtk.CheckMenuItem(label)
				is_check = True
				if node.hasAttribute("checked"):
					item.set_active(True)
			# <imageitem> gtk.ImageMenuItem
			elif node.nodeName == "imageitem":
				icon = node.getAttribute("icon")
				item = imageitem_from_name(icon, label, icon_size)
			# <separator> gtk.SeparatorMenuItem
			elif node.nodeName == "separator":
				item = gtk.SeparatorMenuItem()
			# <appdir> 
			elif node.nodeName == "appdir":
				# create menu from dir with desktop-files
				path = node.getAttribute("path")
				appmenu = ApplicationMenu(path)
				cats = node.getAttribute("cats").split(",")
				for cat in cats:
					item = gtk.MenuItem(cat)
					#item = imageitem_from_name('games', cat)
					submenu = appmenu.get_menu_for_category(cat, callback)
					item.set_submenu(submenu)
					item.show()
					menu.append(item)
				item = None	# to overjump further append-item calls
			# <scandir> create directory list
			elif node.nodeName == "scandir":
				# get dirname, prefix, suffix, replace-list, skip-list
				dir = node.getAttribute("directory")
				# replace $HOME with environment var
				dir = dir.replace('$HOME', os.environ['HOME'])
				#expr = node.getAttribute("expr")
				idprfx = node.getAttribute("id_prefix")
				idsufx = node.getAttribute("id_suffix")
				srch = node.getAttribute("search").split(',')
				repl = node.getAttribute("replace").split(',')
				skp = node.getAttribute("skip").split(',')
				# get filter attribute
				flt = node.getAttribute("filter")
				if flt=='':
					flt='*'
				# scan directory and append items to current menu
				#fill_menu_from_directory(dir, menu, callback, regexp=expr, filter=flt)
				fill_menu_from_directory(dir, menu, callback, filter=flt,
					id_prefix=idprfx, id_suffix=idsufx, search=srch, 
					replace=repl, skip=skp)
			# item created?
			if item:
				if node.hasChildNodes():
					# ... call function recursive and set returned menu as submenu
					submenu = create_menu_from_xml(node, 
						callback, icon_size)
					item.set_submenu(submenu)
				item.show()
				if id:
					item.connect("activate", callback, id)
				menu.append(item)
	return menu

def fill_menu_from_directory (dirname, menu, callback, filter='*',
	id_prefix='', id_suffix='', search=[], replace=[], skip=[]):
	"""Create MenuItems from a directory.
	TODO: use regular expressions"""
	# create theme-list from theme-directory
	lst = glob.glob(dirname + "/" + filter)
	#print "Scanning: "+dirname + "/" + filter 
	lst.sort()
	dlen = len(dirname) + 1
	# check each entry in dir
	for filename in lst:
		#print "FILE: " + filename
		fname = filename[dlen:]
		# file allowed?
		if skip.count(fname)<1:
			#print "OK"
			# create label (replace unwanted strings)
			l = len(search) 
			if l>0 and l == len(replace):
				for i in xrange(l):
					fname = fname.replace(search[i], replace[i])
			# create label (add prefix/suffix/replace)
			id = id_prefix + fname + id_suffix
			#print "NAME: "+fname
			# create menuitem 
			item = gtk.MenuItem(fname)
			item.connect("activate", callback, id)
			item.show()
			menu.append(item)

def imageitem_from_name (filename, label, icon_size=32):
	"""Creates a new gtk.ImageMenuItem from a given icon/filename.
	If an absolute path is not given, the function checks for the name
	of the icon within the current gtk-theme."""
	item = gtk.ImageMenuItem(label)
	image = gtk.Image()
	if filename and filename[0]=='/':
		# load from file
		try:
			image.set_from_file(filename)
			pb = image.get_pixbuf()
			# rescale, if too big
			if pb.get_width() > icon_size :
				pb2 = pb.scale_simple(
					icon_size, icon_size, 
					gtk.gdk.INTERP_HYPER)
				image.set_from_pixbuf(pb2)
			else:
				image.set_from_pixbuf(pb)
		except:
			print "Error while creating image from file: %s" % filename
			return None
	else:
		image.set_from_icon_name(filename, 3)	# TODO: use better size
	if image:
		item.set_image(image)
	return item

def read_desktop_file (filename):
	"""Read ".desktop"-file into a dict
	NOTE: Should use utils.IniReader ..."""
	list = {}
	f=None
	try:
		f = open (filename, "r")
	except:
		print "Error: file %s not found." % filename
	if f:
		lines = f.readlines()
		for line in lines:
			if line[0] != "#" and line !="\n" and line[0] != "[":
				ll = line.split('=', 1)
				if len(ll) > 1:
					list[ll[0]] = ll[1].replace("\n", "")
	return list

#-----------------------------------------------
# Classes
#-----------------------------------------------

class ApplicationMenu(object):
	"""A utility-class to simplify the creation of gtk.Menus from directories with 
	desktop-files. Reads all files in one or multiple directories into its internal list 
	and offers an easy way to create entire categories as complete gtk.Menu 
	with gtk.ImageMenuItems. """
	
	# the path to read files from
	__path = ""
	# list with apps (could be called "cache")
	__applications = []
	
	def __init__ (self, path):
		"""constructor"""
		self.__path = path
		self.__categories = {}
		self.read_directory(path)

	def read_directory (self, path):
		"""read all desktop-files in a directory into the internal list
		and sort them into the available categories"""
		dirlst = glob.glob(path + '/*')
		#print "Path: "+path
		namelen = len(path)
		for file in dirlst:
			if file[-8:]=='.desktop':
				fname = file[namelen:]
				#print "file: "+fname
				df = read_desktop_file(file)
				name = ""
				icon = ""
				cmd = ""
				try:
					name = df['Name']
					icon = df['Icon']
					cmd = df['Exec']
					cats = df['Categories'].split(';')
					#typ = df['Type']
					#if typ == "Application":
					self.__applications.append(df)
				except Exception, ex:
					print "Exception: %s" % str(ex)
					print "An error occured with desktop-file: %s" % file
	
	def get_menu_for_category (self, cat_name, callback):
		"""returns a gtk.Menu with all apps in the given category"""
		# get apps in the category
		applist = []
		for app in self.__applications:
			try:
				if (';'+app['Categories']).count(';'+cat_name+';') > 0:
					applist.append(app)
			except:
				pass

		# remove duplicates
		for app in applist:
			if applist.count(app) > 1: 
				applist.remove(app)
		# sort list
		applist.sort()
		# create menu from list
		menu = gtk.Menu()
		for app in applist:
			item = imageitem_from_name(app['Icon'], app['Name'], 24)
			if item:
				item.connect("activate", callback, "exec:" + app['Exec'])
				item.show()
				menu.append(item)
		# return menu
		return menu

class DefaultMenuItem(object):
	"""A container with constants for the default menuitems"""
	
	# default menuitem constants (is it right to increase like this?)
	NONE		= 0
	DELETE		= 1
	THEMES		= 2
	INFO		= 4
	SIZE		= 8
	WINDOW_MENU	= 16
	PROPERTIES	= 32
	DELETE		= 64
	QUIT 		= 128
	QUIT_ALL 	= 256
	# EXPERIMENTAL!! If you use this, the file menu.xml in the 
	# Screenlet's data-dir is used for generating the menu ...
	XML			= 512
	ADD		 	= 1024
	# the default items
	STANDARD	= 1|2|8|16|32|64|128|256|1024


class ImageMenuItem(gtk.ImageMenuItem):
	"""A menuitem with a custom image and label.
	To set the image to a non-stock image, just
	create the menuitem without an image and then
	set the image with the appropriate method."""
	
	def __init__ (self, stock=gtk.STOCK_MISSING_IMAGE, label=None):
		"""stock: a stock image or 'none'.
		label: text to set as the label or None."""
		# call the superclass
		super(ImageMenuItem, self).__init__(stock)
		
		# get the label and image for later
		self.label = self.get_child()
		self.image = self.get_image()
		
		# set the label to custom text
		if label is not None:
			self.set_label(label)
	
	def set_image_from_file (self, filename):
		"""Set the image from file."""
		self.image.set_from_file(filename)
		
	def set_image_from_pixbuf (self, pixbuf):
		"""Set the image from a pixbuf."""
		self.image.set_from_pixbuf(pixbuf)
		
	def set_image_from_stock(self, name):
		"""Set the image from a stock image."""
		self.image.set_from_stock(name, gtk.ICON_SIZE_MENU)
		
	def set_label(self, text):
		"""Set the label's text."""
		self.label.set_text(text)
	
	def set_image_size (self, width, height):
		"""Resize the menuitem's image."""
		self.image.set_size_request(width, height)
