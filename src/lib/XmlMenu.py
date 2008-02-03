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

# creates a nw gtk.ImageMenuItem from a given icon-/filename.
# If no absolute path is given, the function checks for the name 
# of the icon within the current gtk-theme.
def imageitem_from_name (filename, label, icon_size=32):
	"""Creates a nw gtk.ImageMenuItem from a given icon-/filename."""
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
			print _("Error while creating image from file: %s") % filename
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

def create_menu_from_file (filename, callback):
	"""Creates a menu from an XML-file and returns None if something went wrong"""
	doc = None
	try:
		doc = xml.dom.minidom.parse(filename)
	except Exception, e:
		print _("XML-Error: %s") % str(e)
		return None
	return create_menu_from_xml(doc.firstChild, callback)



class ApplicationMenu:
	"""A utility-class to simplify the creation of gtk.Menus from directories with 
	desktop-files. Reads all files in one or multiple directories into its internal list 
	and offers an easy way to create entire categories as complete gtk.Menu 
	with gtk.ImageMenuItems. """
	
	# the path to read files from
	__path = ""
	# list with apps (could be called "cache")
	__applications = []
	
	# constructor
	def __init__ (self, path):
		self.__path = path
		self.__categories = {}
		self.read_directory(path)

	# read all desktop-files in a directory into the internal list
	# and sort them into the available categories
	def read_directory (self, path):
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
					print _("Exception: %s") % str(ex)
					print _("An error occured with desktop-file: %s") % file
	
	# return a gtk.Menu with all app in the given category
	def get_menu_for_category (self, cat_name, callback):
		# get apps in the given category
		applist = []
		for app in self.__applications:
			try:
				if (';'+app['Categories']).count(';'+cat_name+';') > 0:
					applist.append(app)
			except:
				pass
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
		
	
"""
# TEST:

# menu-callback
def menu_handler(item, id):
	# now check id
	if id[:5]=="exec:":
		print "EXECUTE: " + id[5:]

def button_press(widget, event):
	widget.menu.popup(None, None, None, event.button, 
				event.time)
	return False

def destroy(widget, event):
	gtk.main_quit()



# ApplicationMenu test

appmenu = ApplicationMenu('/usr/share/applications')

win = gtk.Window()
win.resize(200, 200)
win.connect("delete_event", destroy)
but = gtk.Button("Press!")
but.menu = gtk.Menu()
lst = ["Development", "Office", "Game", "Utility"]
for i in xrange(len(lst)):
	item = gtk.MenuItem(lst[i])
	submenu = appmenu.get_menu_for_category(lst[i], menu_handler)
	if submenu:
		item.set_submenu(submenu)
		item.show()
		but.menu.append(item)
but.menu.show()
but.connect("button_press_event", button_press)
win.add(but)
but.show()
win.show()
gtk.main()
"""

# XML/Appmenu TEST
if __name__ == "__main__":
	
	import screenlets.utils
	
	# menu callback
	def xml_menu_handler (item, id):
		print "ID: "+str(id)
		# now check id
		if id[:5]=="exec:":
			print "EXECUTE: " + id[5:]

	def button_press (widget, event):
		widget.menu.popup(None, None, None, event.button, 
					event.time)
		return False

	def destroy (widget, event):
		gtk.main_quit()

	# create menu from XML-file
	p = screenlets.utils.find_first_screenlet_path('Control')
	print p
	menu = create_menu_from_file(p + "/menu.xml", xml_menu_handler)
	if menu:
		win = gtk.Window()
		win.resize(200, 200)
		win.connect("delete_event", destroy)
		but = gtk.Button("Press!")
		but.menu = menu
		but.connect("button_press_event", button_press)
		win.add(but)
		but.show()
		win.show()
		gtk.main()
	else:
		print _("Error while creating menu.")
