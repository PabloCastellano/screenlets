#!/usr/bin/env python

# Options-system (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - a dynamic Options-system that allows very easy creation of
#   objects with embedded configuration-system.
#   NOTE: The Dialog is not very nice yet - it is not good OOP-practice
#   because too big functions and bad class-layout ... but it works
#   for now ... :)
#
# TODO:
# - own widgets for all option-types (e.g. ListOptionWidget, ColorOptionWidget)
# - TimeOption, DateOption
# - allow options to disable/enable other options
# - support for EditableOptions-subclasses as options
# - separate OptionEditorWidget from Editor-Dialog
# - place ui-code into screenlets.options.ui-module
#

import screenlets
import utils

import os		
import gtk, gobject
import xml.dom.minidom
from xml.dom.minidom import Node
import gettext

gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')

def _(s):
	return gettext.gettext(s)


# -----------------------------------------------------------------------
# Option-classes and subclasses
# -----------------------------------------------------------------------

class Option(gobject.GObject):
	"""An Option stores information about a certain object-attribute. It doesn't
	carry information about the value or the object it belongs to - it is only a
	one-way data-storage for describing how to handle attributes."""
	
	__gsignals__ = dict(option_changed=(gobject.SIGNAL_RUN_FIRST,
		gobject.TYPE_NONE, (gobject.TYPE_OBJECT,)))
	
	def __init__ (self, name, default, label, desc,  
		disabled=False, hidden=False, callback=None, protected=False,
		realtime=True):
		"""Creates a new Option with the given information."""
		super(Option, self).__init__()
		self.name = name
		self.label = label
		self.desc = desc
		self.default = default
		self.disabled = disabled
		self.hidden = hidden
		# callback to be notified when this option changes
		self.callback = callback
		# real-time update?
		self.realtime = realtime
		# protected from get/set through service
		self.protected = protected
		
	def on_import (self, strvalue):
		"""Callback - called when an option gets imported from a string. 
		This function MUST return the string-value converted to the required 
		type!"""
		return strvalue.replace("\\n", "\n")
	
	def on_export (self, value):
		"""Callback - called when an option gets exported to a string. The
		value-argument needs to be converted to a string that can be imported 
		by the on_import-handler. This handler MUST return the value 
		converted to a string!"""
		return str(value).replace("\n", "\\n")
	

class FileOption (Option):
	"""An Option-subclass for string-values that contain filenames. Adds
	a patterns-attribute that can contain a list of patterns to be shown
	in the assigned file selection dialog. The show_pixmaps-attribute
	can be set to True to make the filedialog show all image-types 
	supported by gtk.Pixmap. If the directory-attributue is true, the
	dialog will ony allow directories."""

	def __init__ (self, name, default, label, desc, 
		patterns=['*'], image=False, directory=False, **keyword_args):
		Option.__init__(self, name, default,label, desc, **keyword_args)
		self.patterns	= patterns
		self.image		= image
		self.directory	= False


class ImageOption (Option):
	"""An Option-subclass for string-values that contain filenames of
	image-files."""


class DirectoryOption (Option):
	"""An Option-subclass for filename-strings that contain directories."""


class BoolOption (Option):
	"""An Option for boolean values."""
	
	def on_import (self, strvalue):
		if strvalue == "True":
			return True
		return False


class StringOption (Option):
	"""An Option for values of type string."""
	
	def __init__ (self, name, default, label, desc, 
		choices=None, password=False, **keyword_args):
		Option.__init__(self, name, default,label, desc, **keyword_args)
		self.choices	= choices
		self.password	= password


class IntOption (Option):
	"""An Option for values of type number (can be int or float)."""
	
	def __init__ (self, name, default, label, desc,  min=0, max=0, 
		increment=1, **keyword_args):
		Option.__init__(self, name, default, label, desc, **keyword_args)
		self.min = min
		self.max = max
		self.increment = increment
	
	def on_import (self, strvalue):
		"""Called when IntOption gets imported. Converts str to int."""
		try:
			if strvalue[0]=='-':
				return int(strvalue[1:]) * -1
			return int(strvalue)
		except:
			print _("Error during on_import - option: %s.") % self.name
			return 0


class FloatOption (IntOption):
	"""An Option for values of type float."""
	
	def __init__ (self, name, default, label, desc, digits=1, 
		**keyword_args):
		IntOption.__init__(self, name, default, label, desc,
			**keyword_args)
		self.digits = digits
	
	def on_import (self, strvalue):
		"""Called when FloatOption gets imported. Converts str to float."""
		if strvalue[0]=='-':
			return float(strvalue[1:]) * -1.0
		return float(strvalue)


class FontOption (Option):
	"""An Option for fonts (a simple StringOption)."""


class ColorOption (Option):
	"""An Option for colors. Stored as a list with 4 values (r, g, b, a)."""
	
	def on_import (self, strvalue):
		"""Import (r, g, b, a) from comma-separated string."""
		# strip braces and spaces
		strvalue = strvalue.lstrip('(')
		strvalue = strvalue.rstrip(')')
		strvalue = strvalue.strip()
		# split value on commas
		tmpval = strvalue.split(',')
		outval = []
		for f in tmpval:
			# create list and again remove spaces
			outval.append(float(f.strip()))
		return outval
	
	def on_export (self, value):
		"""Export r, g, b, a to comma-separated string."""
		l = len(value)
		outval = ''
		for i in xrange(l):
			outval += str(value[i])
			if i < l-1:
				outval += ','
		return outval


class ListOption (Option):
	"""An Option-type for list of strings."""

	def on_import (self, strvalue):
		"""Import python-style list from a string (like [1, 2, 'test'])"""
		lst = eval(strvalue)
		return lst
	
	def on_export (self, value):
		"""Export list as string."""
		return str(value)


import gnomekeyring
class AccountOption (Option):
	"""An Option-type for username/password combos. Stores the password in
	the gnome-keyring (if available) and only saves username and auth_token
	through the screenlets-backend.
	TODO:
	- not create new token for any change (use "set" instead of "create" if
	  the given item already exists)
	- use usual storage if no keyring is available but output warning
	- on_delete-function for removing the data from keyring when the
	  Screenlet holding the option gets deleted"""
	
	def __init__ (self, name, default, label, desc, **keyword_args):
		Option.__init__ (self, name, default, label, desc, 
			protected=True, **keyword_args)
		# check for availability of keyring
		if not gnomekeyring.is_available():
			raise Exception(_('GnomeKeyring is not available!!'))	# TEMP!!!
		# THIS IS A WORKAROUND FOR A BUG IN KEYRING (usually we would use
		# gnomekeyring.get_default_keyring_sync() here):
		# find first available keyring
		keyring_list = gnomekeyring.list_keyring_names_sync()
		if len(keyring_list) == 0:
			raise Exception(_('No keyrings found. Create one first!'))
		else:
			# we prefer the default keyring
			if keyring_list.count('default') > 0:
				self.keyring = 'default'
			else:
				print _("Warn: No default keyring found, storage not permanent!")
				self.keyring = keyring_list[0]
	
	def on_import (self, strvalue):
		"""Import account info from a string (like 'username:auth_token'), 
		retrieve the password from the storage and return a tuple containing
		username and password."""
		# split string into username/auth_token
		#data = strvalue.split(':', 1)
		(name, auth_token) = strvalue.split(':', 1)
		if name and auth_token:
			# read pass from storage
			try:
				pw = gnomekeyring.item_get_info_sync('session', 
					int(auth_token)).get_secret()
			except Exception, ex:
				print _("ERROR: Unable to read password from keyring: %s") % ex
				pw = ''
			# return
			return (name, pw)
		else:
			raise Exception(_('Illegal value in AccountOption.on_import.'))
	
	def on_export (self, value):
		"""Export the given tuple/list containing a username and a password. The
		function stores the password in the gnomekeyring and returns a
		string in form 'username:auth_token'."""
		# store password in storage
		attribs = dict(name=value[0])
		auth_token = gnomekeyring.item_create_sync('session', 
			gnomekeyring.ITEM_GENERIC_SECRET, value[0], attribs, value[1], True) 
		# build value from username and auth_token
		return value[0] + ':' + str(auth_token)

"""#TEST:
o = AccountOption('None', 'pop3_account', ('',''), 'Username/Password', 'Enter username/password here ...')
# save option to keyring
exported_account = o.on_export(('RYX', 'mysecretpassword'))
print exported_account
# and read option back from keyring
print o.on_import(exported_account)


import sys
sys.exit(0)"""

class TimeOption (ColorOption):
	"""An Option-subclass for string-values that contain dates."""



# -----------------------------------------------------------------------
# OptionGroup class
# -----------------------------------------------------------------------

class OptionGroup (list):
	"""A container that is used to group options."""
	
	def __init__ (self, name, info=''):
		self._name	= name
		self._info	= info
	
	def __repr__ (self):
		s = ''
		for el in self: s += str(el) + ', '
		return '<OptionGroup (%i elements): %s>' % (len(self), s)
	
	def add_option (self, option, callback=None):
		"""Add an option to this group and add a callvback, if needed."""
		self.append(option)
		if callback:
			option.connect("option_changed", callback)
	
	def get_info (self):
		"""Return the info for this group."""
		return self._info
	
	def get_name (self):
		"""Return the name of this group."""
		return self._name
	
	def get_option_by_name (self, name):
		"""Get an Option whithin this OptionGroup by its name."""
		for o in self:
			if o.name == name:
				return o
		return None
	
	def remove_option_by_name (self, name):
		"""Remove an option from this OptionGroup by its name."""
		for o in self:
			if o.name == name:
				del o
				return True
		return True
	

# -----------------------------------------------------------------------
# EditableOptions-class and needed functions
# -----------------------------------------------------------------------

def create_option_from_node (node):
	"""Create an Option from an XML-node with option-metadata."""
	#print "TODO OPTION: " + str(cn)
	otype = node.getAttribute("type")
	oname = node.getAttribute("name")
	ohidden = node.getAttribute("hidden")
	odefault	= None
	oinfo		= ''
	olabel		= ''
	omin		= None
	omax		= None
	oincrement	= 1
	ochoices	= ''
	odigits		= None
	if otype and oname:
		# parse children of option-node and save all useful attributes
		for attr in node.childNodes:
			if attr.nodeType == Node.ELEMENT_NODE:
				if attr.nodeName == 'label':
					olabel = attr.firstChild.nodeValue
				elif attr.nodeName == 'info':
					oinfo = attr.firstChild.nodeValue
				elif attr.nodeName == 'default':
					odefault = attr.firstChild.nodeValue
				elif attr.nodeName == 'min':
					omin = attr.firstChild.nodeValue
				elif attr.nodeName == 'max':
					omax = attr.firstChild.nodeValue
				elif attr.nodeName == 'increment':
					oincrement = attr.firstChild.nodeValue
				elif attr.nodeName == 'choices':
					ochoices = attr.firstChild.nodeValue
				elif attr.nodeName == 'digits':
					odigits = attr.firstChild.nodeValue
		# if we have all needed values, create the Option
		if odefault:
			# create correct classname here
			cls = otype[0].upper() + otype.lower()[1:] + 'Option'
			#print 'Create: ' +cls +' / ' + oname + ' ('+otype+')'
			# and build new instance (we use on_import for setting default val)
			clsobj = getattr(__import__(__name__), cls)
			opt = clsobj(oname, None, olabel, oinfo)
			opt.default = opt.on_import(odefault)
			# set values to the correct types
			if cls == 'IntOption':
				if omin:
					opt.min = int(omin)
				if omax:
					opt.max = int(omax)
				if oincrement:
					opt.increment = int(oincrement)
			elif cls == 'FloatOption':
				if odigits:
					opt.digits = int(odigits)
				if omin:
					opt.min = float(omin)
				if omax:
					opt.max = float(omax)
				if oincrement:
					opt.increment = float(oincrement)
			elif cls == 'StringOption':
				if ochoices:
					opt.choices = ochoices
			return opt
	return None
	

class EditableOptions:
	"""The EditableOptions can be inherited from to allow objects to export 
	editable options for editing them with the OptionsEditor-class."""
	
	def __init__ (self):
		self._options = []
		# TODO: remove this somewhen, only for backwards support
		self.add_options_group = self.create_option_group
	
	def add_option (self, obj):
		"""DEPRECATED"""
		print "WARNING: add_option is not supported any longer, instead create an OptionGroup, add your Options to it and add it via add_option_group."
	
	def add_option_group (self, group):
		"""Add an OptionGroup-object to this EditableOptions-object."""	
		self._options.append(group)
	
	def create_option_group (self, name, info):
		"""Create a new OptionGroup with name/info, add it to this object
		and return a reference to it."""
		group = OptionGroup(name, info)
		self.add_option_group(group)
		return group
	
	def disable_option (self, name, disabled=True):
		"""Disable the inputs for a certain Option.
		TODO: make default and rename old version"""
		o = self.get_option_by_name(name)
		if o:
			o.disabled = disabled
			return True
		return False
	
	def get_option_group_by_name (self, name):
		"""Return the OptionGroup with the given name."""
		for grp in self._options:
			if grp.get_name() == name:
				return grp
		return None
	
	def get_option_groups (self):
		"""Return a list with all OptionGroups within this object."""
		return self._options
	
	def get_option_by_name (self, name):
		"""Searches all options in all groups within this object and returns
		the first found Option with the given name.
		TODO: rename and deprecate old version"""
		for grp in self._options:
			for o in grp:
				if o.name == name:
					return o
		return None
	
	def has_option_groups (self):
		"""Returns true if this object has option groups."""
		return len(self._options)
	
	def add_options_from_file (self, filename):
		"""This function creates options from an XML-file with option-metadata.
		TODO: make this more reusable and place it into module (once the groups
		are own objects)."""
		# create xml document
		try:
			doc = xml.dom.minidom.parse(filename)
		except:
			raise Exception(_('Invalid XML in metadata-file (or file missing): "%s".') % filename)
		# get rootnode
		root = doc.firstChild
		if not root or root.nodeName != 'screenlet':
			raise Exception(_('Missing or invalid rootnode in metadata-file: "%s".') % filename)
		# ok, let's check the nodes: this one should contain option-groups
		groups = []
		for node in root.childNodes:
			# we only want element-nodes
			if node.nodeType == Node.ELEMENT_NODE:
				#print node
				if node.nodeName != 'group' or not node.hasChildNodes():
					# we only allow groups in the first level (groups need children)
					raise Exception(_('Error in metadata-file "%s" - only <group>-tags allowed in first level. Groups must contain at least one <info>-element.') % filename)
				else:
					# ok, create a new group and parse its elements
					name	= node.getAttribute("name")
					info	= ''
					options	= []
					if not name:
						raise Exception(_('No name for group defined in "%s".') % filename)
					# check all children in group
					for on in node.childNodes:
						if on.nodeType == Node.ELEMENT_NODE:
							if on.nodeName == 'info':
								# info-node? set group-info
								info = on.firstChild.nodeValue
							elif on.nodeName == 'option':
								# option node? parse option node
								opt = create_option_from_node (on)
								# ok? add it to list
								if opt:
									options.append(opt)
								else:
									raise Exception(_('Invalid option-node found in "%s".') % filename)
					# create new group and add options to it
					if len(options):
						group = OptionGroup(name, info)
						self.add_option_group(group)
						for o in options:
							group.add_option(o)



# -----------------------------------------------------------------------
# OptionsDialog and UI-classes
# -----------------------------------------------------------------------

class ListOptionDialog (gtk.Dialog):
	"""An editing dialog used for editing options of the ListOption-type."""
	
	model = None
	tree = None
	buttonbox = None
	
	# call gtk.Dialog.__init__
	def __init__ (self):
		super(ListOptionDialog, self).__init__(_("Edit List"), 
			flags=gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
			buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
				gtk.STOCK_OK, gtk.RESPONSE_OK))
		# set size
		self.resize(300, 370)
		self.set_keep_above(True)	# to avoid confusion
		# init vars
		self.model = gtk.ListStore(str)
		# create UI
		self.create_ui()
	
	def create_ui (self):
		"""Create the user-interface for this dialog."""
		# create outer hbox (tree|buttons)
		hbox = gtk.HBox()
		hbox.set_border_width(10)
		hbox.set_spacing(10)
		# create tree
		self.tree = gtk.TreeView(model=self.model)
		self.tree.set_headers_visible(False)
		self.tree.set_reorderable(True)
		#self.tree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
		col = gtk.TreeViewColumn('')
		cell = gtk.CellRendererText()
		#cell.set_property('cell-background', 'cyan')
		cell.set_property('foreground', 'black')
		col.pack_start(cell, False)
		col.set_attributes(cell, text=0)
		self.tree.append_column(col)
		self.tree.show()
		hbox.pack_start(self.tree, True, True)
		#sep = gtk.VSeparator()
		#sep.show()
		#hbox.add(sep)
		# create  buttons
		self.buttonbox = bb = gtk.VButtonBox()
		self.buttonbox.set_layout(gtk.BUTTONBOX_START)
		b1 = gtk.Button(stock=gtk.STOCK_ADD)
		b2 = gtk.Button(stock=gtk.STOCK_EDIT)
		b3 = gtk.Button(stock=gtk.STOCK_REMOVE)
		b1.connect('clicked', self.button_callback, 'add')
		b2.connect('clicked', self.button_callback, 'edit')
		b3.connect('clicked', self.button_callback, 'remove')
		bb.add(b1)
		bb.add(b2)
		bb.add(b3)
		self.buttonbox.show_all()
		#hbox.add(self.buttonbox)
		hbox.pack_end(self.buttonbox, False)
		# add everything to outer hbox and show it
		hbox.show()
		self.vbox.add(hbox)
		
	def set_list (self, lst):
		"""Set the list to be edited in this editor."""
		for el in lst:
			self.model.append([el])
	
	def get_list (self):
		"""Return the list that is currently being edited in this editor."""
		lst = []
		for i in self.model:
			lst.append(i[0])
		return lst
	
	def remove_selected_item (self):
		"""Remove the currently selected item."""
		sel = self.tree.get_selection()
		if sel:
			it = sel.get_selected()[1]
			if it:
				print self.model.get_value(it, 0)
				self.model.remove(it)
	
	def entry_dialog (self, default = ''):
		"""Show entry-dialog and return string."""
		entry = gtk.Entry()
		entry.set_text(default)
		entry.show()
		dlg = gtk.Dialog(_("Add/Edit Item"), flags=gtk.DIALOG_DESTROY_WITH_PARENT,
			buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, 
			gtk.RESPONSE_OK))
		dlg.set_keep_above(True)
		dlg.vbox.add(entry)
		resp = dlg.run()
		ret = None
		if resp == gtk.RESPONSE_OK:
			ret = entry.get_text()
		dlg.destroy()
		return ret
				
	def button_callback (self, widget, id):
		print "PRESS: "+id
		if id == 'remove':
			self.remove_selected_item()
		if id == 'add':
			new = self.entry_dialog()
			if new != None:
				self.model.append([new])
		if id == 'edit':
			sel = self.tree.get_selection()
			if sel:
				it = sel.get_selected()[1]
				if it:
					new = self.entry_dialog(self.model.get_value(it, 0))
					if new != None:
						#self.model.append([new])
						self.model.set_value(it, 0, new)
	
	
# TEST	
"""dlg = ListOptionDialog()
dlg.set_list(['test1', 'afarew34s', 'fhjh23faj', 'yxcdfs58df', 'hsdf7jsdfh'])
dlg.run()
print "RESULT: " + str(dlg.get_list())
dlg.destroy()
import sys
sys.exit(1)"""
# /TEST

class OptionsDialog (gtk.Dialog):
	"""A dynamic options-editor for editing Screenlets which are implementing 
	the EditableOptions-class."""
	
	_shown_object = None
	
	def __init__ (self, width, height):
		# call gtk.Dialog.__init__
		super(OptionsDialog, self).__init__(
			_("Edit Options"), flags=gtk.DIALOG_DESTROY_WITH_PARENT |
			gtk.DIALOG_NO_SEPARATOR,
			buttons = (#gtk.STOCK_REVERT_TO_SAVED, gtk.RESPONSE_APPLY,
				gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
		# set size
		self.resize(width, height)
		self.set_keep_above(True)	# to avoid confusion
		self.set_border_width(10)
		# create attribs
		self.page_about		= None
		self.page_options	= None
		self.page_themes	= None
		self.vbox_editor	= None
		self.hbox_about		= None
		self.infotext		= None
		self.infoicon		= None
		# create theme-list
		self.liststore	= gtk.ListStore(object)
		self.tree		= gtk.TreeView(model=self.liststore)
		# create/add outer notebook
		self.main_notebook = gtk.Notebook()
		self.main_notebook.show()
		self.vbox.add(self.main_notebook)
		# create/init notebook pages
		self.create_about_page()
		self.create_themes_page()
		self.create_options_page()
		# crete tooltips-object
		self.tooltips = gtk.Tooltips()
	
	# "public" functions
	
	def reset_to_defaults (self):
		"""Reset all entries for the currently shown object to their default 
		values (the values the object has when it is first created).
		NOTE: This function resets ALL options, so BE CARFEUL!"""
		if self._shown_object:
			for o in self._shown_object.__options__:
				# set default value
				setattr(self._shown_object, o.name, o.default)

	def set_info (self, name, info, copyright='', version='', icon=None):
		"""Update the "About"-page with the given information."""
		# convert infotext (remove EOLs and TABs)
		info = info.replace("\n", "")
		info = info.replace("\t", " ")
		# create markup
		markup = '\n<b><span size="xx-large">' + name + '</span></b>'
		if version:
			markup += '  <span size="large"><b>' + version + '</b></span>'
		markup += '\n\n'+info+'\n<span size="small">\n'+copyright+'</span>'
		self.infotext.set_markup(markup)
		# icon?
		if icon:
			# remove old icon
			if self.infoicon:
				self.infoicon.destroy()
			# set new icon
			self.infoicon = icon
			self.infoicon.set_alignment(0.0, 0.10)
			self.infoicon.show()
			self.hbox_about.pack_start(self.infoicon, 0, 1, 10)
		else:
			self.infoicon.hide()

	def show_options_for_object (self, obj):
		"""Update the OptionsEditor to show the options for the given Object.
		The Object needs to be an EditableOptions-subclass."""
		self._shown_object = obj
		# create notebook for groups
		notebook = gtk.Notebook()
		self.vbox_editor.set_border_width(10)
		self.vbox_editor.add(notebook)
		# get all options/groups
		for o in obj.get_option_groups():
			print o
			if isinstance(o, OptionGroup):
				# create box for tab-page
				page = gtk.VBox()
				page.set_border_width(10)
				info = o.get_info()
				if info != '':
					info = gtk.Label(info)
					info.set_alignment(0, 0)
					page.pack_start(info, 0, 0, 7)
				# create VBox for inputs
				box = gtk.VBox()
				box.set_border_width(5)
				# add box to page
				page.add(box)
				page.show_all()
				# add new notebook-page
				label = gtk.Label(o.get_name())
				notebook.append_page(page, label)
				# and create inputs
				for option in o:
					if option.hidden == False:
						val = getattr(obj, option.name)
						w = self.get_widget_for_option(option, val)
						if w:
							box.pack_start(w, 0, 0)
							w.show()
		notebook.show()	
		# show/hide themes tab, depending on whether the screenlet uses themes
		if obj.uses_theme and obj.theme_name != '':
			self.show_themes_for_screenlet(obj)
		else:
			self.page_themes.hide()
	
	def show_themes_for_screenlet (self, obj):
		"""Update the Themes-page to display the available themes for the
		given Screenlet-object."""
		# list with found themes
		found_themes = []
		# now check all paths for themes
		for path in screenlets.SCREENLETS_PATH:
			p = path + '/' + obj.get_short_name() + '/themes'
			print p
			#p = '/usr/local/share/screenlets/Clock/themes'	# TEMP!!!
			try:
				dircontent = os.listdir(p)
			except:
				print _("Path %s not found.") % p
				continue
			# check all themes in path
			for name in dircontent:
				# load themes with the same name only once
				if found_themes.count(name):
					continue
				found_themes.append(name)
				# build full path of theme.conf
				theme_conf	= p + '/' + name + '/theme.conf'
				# if dir contains a theme.conf
				if os.access(theme_conf, os.F_OK):
					# load it and create new list entry
					ini = screenlets.utils.IniReader()
					if ini.load(theme_conf):
						# check for section
						if ini.has_section('Theme'):
							# get metainfo from theme
							th_fullname	= ini.get_option('name', 
								section='Theme')
							th_info		= ini.get_option('info', 
								section='Theme')
							th_version	= ini.get_option('version', 
								section='Theme')
							th_author	= ini.get_option('author', 
								section='Theme')
							# create array from metainfo and add it to liststore
							info = [name, th_fullname, th_info, th_author, 
								th_version]
							self.liststore.append([info])
				else:
					# no theme.conf in dir? just add theme-name
					self.liststore.append([[name, '-', '-', '-', '-']])
				# is it the active theme?
				if name == obj.theme_name:
					# select it in tree
					print "active theme is: %s" % name
					sel = self.tree.get_selection()
					if sel:
						it = self.liststore.get_iter_from_string(\
							str(len(self.liststore)-1))
						if it:
							sel.select_iter(it)

	# UI-creation
	
	def create_about_page (self):
		"""Create the "About"-tab."""
		self.page_about = gtk.HBox()
		# create about box
		self.hbox_about = gtk.HBox()
		self.hbox_about.show()
		self.page_about.add(self.hbox_about)
		# create icon
		self.infoicon = gtk.Image()
		self.infoicon.show()
		self.page_about.pack_start(self.infoicon, 0, 1, 10)
		# create infotext
		self.infotext = gtk.Label()
		self.infotext.use_markup = True
		self.infotext.set_line_wrap(True)
		self.infotext.set_alignment(0.0, 0.0)
		self.infotext.show()
		self.page_about.pack_start(self.infotext, 1, 1, 5)
		# add page
		self.page_about.show()
		self.main_notebook.append_page(self.page_about, gtk.Label(_('About ')))	
	
	def create_options_page (self):
		"""Create the "Options"-tab."""
		self.page_options = gtk.HBox()
		# create vbox for options-editor
		self.vbox_editor	= gtk.VBox(spacing=3)
		self.vbox_editor.set_border_width(5)
		self.vbox_editor.show()
		self.page_options.add(self.vbox_editor)
		# show/add page
		self.page_options.show()
		self.main_notebook.append_page(self.page_options, gtk.Label(_('Options ')))

	def create_themes_page (self):
		"""Create the "Themes"-tab."""
		self.page_themes = gtk.VBox(spacing=5)
		self.page_themes.set_border_width(10)
		# create info-text list
		txt = gtk.Label(_('Themes allow you to easily switch the appearance of your Screenlets. On this page you find a list of all available themes for this Screenlet.'))
		txt.set_size_request(450, -1)
		txt.set_line_wrap(True)
		txt.set_alignment(0.0, 0.0)
		txt.show()
		self.page_themes.pack_start(txt, False, True)
		# create theme-selector list
		self.tree.set_headers_visible(False)
		self.tree.connect('cursor-changed', self._tree_cursor_changed)
		self.tree.show()
		col = gtk.TreeViewColumn('')
		cell = gtk.CellRendererText()
		col.pack_start(cell, True)
		#cell.set_property('foreground', 'black')
		col.set_cell_data_func(cell, self._render_cell)
		self.tree.append_column(col)
		# wrap tree in scrollwin
		sw = gtk.ScrolledWindow()
		sw.set_shadow_type(gtk.SHADOW_IN)
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		sw.add(self.tree)
		sw.show()
		# add vbox and add tree/buttons
		vbox = gtk.VBox()
		vbox.pack_start(sw, True, True)
		vbox.show()
		# show/add page
		self.page_themes.add(vbox)
		self.page_themes.show()
		self.main_notebook.append_page(self.page_themes, gtk.Label(_('Themes ')))
		
	def _render_cell (self, tvcolumn, cell, model, iter):
		"""Callback for rendering the cells in the theme-treeview."""
		# get attributes-list from Treemodel
		attrib = model.get_value(iter, 0)
		# set colors depending on state
		col = '555555'
		name_uc = attrib[0][0].upper() + attrib[0][1:]
		# create markup depending on info
		if attrib[1] == '-' and attrib[2] == '-':
			mu = '<b><span weight="ultrabold" size="large">' + name_uc + \
			'</span></b> (no info available)'
		else:
			mu = '<b><span weight="ultrabold" size="large">' + name_uc + \
				'</span></b> v' + attrib[4] + '\n<small><span color="#555555' +\
				'">' + attrib[2].replace('\\n', '\n') + \
				'</span></small>\n<i><small>by '+str(attrib[3])+'</small></i>'
		# set markup
		cell.set_property('markup', mu)
	
	# UI-callbacks
	
	def _tree_cursor_changed (self, treeview):
		"""Callback for handling selection changes in the Themes-treeview."""
		sel = self.tree.get_selection()
		if sel:
			s = sel.get_selected()
			if s:
				it = s[1]
				if it:
					attribs = self.liststore.get_value(it, 0)
					if attribs and self._shown_object:
						#print attribs
						# set theme in Screenlet (if not already active)
						if self._shown_object.theme_name != attribs[0]:
							self._shown_object.theme_name = attribs[0]
	
	# option-widget creation (should be split in several classes)
	
	def get_widget_for_option (self, option, value=None):
		"""Return a gtk.*Widget with Label within a HBox for a given option.
		NOTE: This is incredibly ugly, ideally all Option-subclasses should
		have their own widgets - like StringOptionWidget, ColorOptionWidget, 
		... and then be simply created dynamically"""
		t = option.__class__
		widget = None
		if t == BoolOption:
			widget = gtk.CheckButton()
			widget.set_active(value)
			widget.connect("toggled", self.options_callback, option)
		elif t == StringOption:
			if option.choices:
				# if a list of values is defined, show combobox
				widget = gtk.combo_box_new_text()
				p = -1
				i = 0
				for s in option.choices:
					widget.append_text(s)
					if s==value:
						p = i
					i+=1
				widget.set_active(p)
			else:
				widget = gtk.Entry()
				widget.set_text(value)
				# if it is a password, set text to be invisible
				if option.password:
					widget.set_visibility(False)
			widget.connect("changed", self.options_callback, option)
		elif t == IntOption or t == FloatOption:
			widget = gtk.SpinButton()
			if t == FloatOption:
				widget.set_digits(option.digits)
				widget.set_increments(option.increment, 
					int(option.max/option.increment))
			else:
				widget.set_increments(option.increment, 
					int(option.max/option.increment))
			if option.min!=None and option.max!=None:
				widget.set_range(option.min, option.max)
			widget.set_value(value)
			widget.connect("value-changed", self.options_callback, option)
		elif t == ColorOption:
			widget = gtk.ColorButton(gtk.gdk.Color(int(value[0]*65535), 
				int(value[1]*65535), int(value[2]*65535)))
			widget.set_use_alpha(True)
			print value
			print value[3]
			widget.set_alpha(int(value[3]*65535))
			widget.connect("color-set", self.options_callback, option)
		elif t == FontOption:
			widget = gtk.FontButton()
			widget.set_font_name(value)
			widget.connect("font-set", self.options_callback, option)		
		elif t == FileOption:
			widget = gtk.FileChooserButton(_("Choose File"))
			widget.set_filename(value)
			widget.set_size_request(180, 28)
			widget.connect("selection-changed", self.options_callback, option)
		elif t == DirectoryOption:
			dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
				gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK),
				action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
			widget = gtk.FileChooserButton(dlg)
			widget.set_title(_("Choose Directory"))
			widget.set_filename(value)
			widget.set_size_request(180, 28)
			widget.connect("selection-changed", self.options_callback, option)
		elif t == ImageOption:
			# create entry and button (entry is hidden)
			entry = gtk.Entry()
			entry.set_text(value)
			entry.set_editable(False)
			but = gtk.Button('')
			# util to reload preview image
			def create_preview (filename):
				if filename and os.path.isfile(filename):
					pb = gtk.gdk.pixbuf_new_from_file_at_size(filename, 64, -1)
					if pb:
						img = gtk.Image()
						img.set_from_pixbuf(pb)
						return img
				img = gtk.image_new_from_stock(gtk.STOCK_MISSING_IMAGE, 
					gtk.ICON_SIZE_LARGE_TOOLBAR)
				img.set_size_request(64, 64)
				return img
			# create button
			def but_callback (widget):
				dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
					gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
				dlg.set_title(_("Choose Image"))
				dlg.set_keep_above(True)
				dlg.set_filename(entry.get_text())
				flt = gtk.FileFilter()
				flt.add_pixbuf_formats()
				dlg.set_filter(flt) 
				prev = gtk.Image()
				box = gtk.VBox()
				box.set_size_request(150, -1)
				box.add(prev)
				prev.show()
				# add preview widget to filechooser
				def preview_callback(widget):
					fname = dlg.get_preview_filename()
					if fname and os.path.isfile(fname):
						pb = gtk.gdk.pixbuf_new_from_file_at_size(fname, 150, -1)
						if pb:
							prev.set_from_pixbuf(pb)
							dlg.set_preview_widget_active(True)
						else:
							dlg.set_preview_widget_active(False)
				dlg.set_preview_widget_active(True)
				dlg.connect('selection-changed', preview_callback)
				dlg.set_preview_widget(box)
				# run 
				response = dlg.run()
				if response == gtk.RESPONSE_OK:
					entry.set_text(dlg.get_filename())
					but.set_image(create_preview(dlg.get_filename()))
					self.options_callback(dlg, option)
				dlg.destroy()
			# load preview image
			but.set_image(create_preview(value))
			but.connect('clicked', but_callback)
			# create widget
			widget = gtk.HBox()
			widget.add(entry)
			widget.add(but)
			but.show()
			widget.show()
			# add tooltips
			#self.tooltips.set_tip(but, 'Select Image ...')
			self.tooltips.set_tip(but, option.desc)
		elif t == ListOption:
			entry= gtk.Entry()
			entry.set_editable(False)
			entry.set_text(str(value))
			entry.show()
			img = gtk.Image()
			img.set_from_stock(gtk.STOCK_EDIT, 1)
			but = gtk.Button('')
			but.set_image(img)
			def open_listeditor(event):
				# open dialog
				dlg = ListOptionDialog()
				# read string from entry and import it through option-class
				# (this is needed to always have an up-to-date value)
				dlg.set_list(option.on_import(entry.get_text()))
				resp = dlg.run()
				if resp == gtk.RESPONSE_OK:
					# set text in entry
					entry.set_text(str(dlg.get_list()))
					# manually call the options-callback
					self.options_callback(dlg, option)
				dlg.destroy()
			but.show()
			but.connect("clicked", open_listeditor)
			self.tooltips.set_tip(but, _('Open List-Editor ...'))
			self.tooltips.set_tip(entry, option.desc)
			widget = gtk.HBox()
			widget.add(entry)
			widget.add(but)
		elif t == AccountOption:
			widget = gtk.HBox()
			vb = gtk.VBox()
			input_name = gtk.Entry()
			input_name.set_text(value[0])
			input_name.show()
			input_pass = gtk.Entry()
			input_pass.set_visibility(False)	# password
			input_pass.set_text(value[1])
			input_pass.show()
			but = gtk.Button(stock=gtk.STOCK_APPLY)
			but.show()
			but.connect("clicked", self.apply_options_callback, option, widget)
			vb.add(input_name)
			vb.add(input_pass)
			vb.show()
			self.tooltips.set_tip(but, _('Apply username/password ...'))
			self.tooltips.set_tip(input_name, _('Enter username here ...'))
			self.tooltips.set_tip(input_pass, _('Enter password here ...'))
			widget.add(vb)
			widget.add(but)
		elif t == TimeOption:
			widget = gtk.HBox()
			input_hour		= gtk.SpinButton()#climb_rate=1.0)
			input_minute	= gtk.SpinButton()
			input_second	= gtk.SpinButton()
			input_hour.set_range(0, 23)
			input_hour.set_max_length(2)
			input_hour.set_increments(1, 1)
			input_hour.set_numeric(True)
			input_hour.set_value(value[0])
			input_minute.set_range(0, 59)
			input_minute.set_max_length(2)
			input_minute.set_increments(1, 1)
			input_minute.set_numeric(True)
			input_minute.set_value(value[1])
			input_second.set_range(0, 59)
			input_second.set_max_length(2)
			input_second.set_increments(1, 1)
			input_second.set_numeric(True)
			input_second.set_value(value[2])
			input_hour.connect('value-changed', self.options_callback, option)
			input_minute.connect('value-changed', self.options_callback, option)
			input_second.connect('value-changed', self.options_callback, option)
			self.tooltips.set_tip(input_hour, option.desc)
			self.tooltips.set_tip(input_minute, option.desc)
			self.tooltips.set_tip(input_second, option.desc)
			widget.add(input_hour)
			widget.add(gtk.Label(':'))
			widget.add(input_minute)
			widget.add(gtk.Label(':'))
			widget.add(input_second)
			widget.add(gtk.Label('h'))
			widget.show_all()
		else:
			widget = gtk.Entry()
			print _("unsupported type '%s'") % str(t)
		hbox = gtk.HBox()
		label = gtk.Label()
		label.set_alignment(0.0, 0.0)
		label.set_label(option.label)
		label.set_size_request(180, 28)
		label.show()
		hbox.pack_start(label, 0, 1)
		if widget:
			if option.disabled:		# option disabled?
				widget.set_sensitive(False)
				label.set_sensitive(False)
			#label.set_mnemonic_widget(widget)
			self.tooltips.set_tip(widget, option.desc)
			widget.show()
			# check if needs Apply-button
			if option.realtime == False:
				but = gtk.Button(stock=gtk.STOCK_APPLY)
				but.show()
				but.connect("clicked", self.apply_options_callback, 
					option, widget)
				b = gtk.HBox()
				b.show()
				b.pack_start(widget, 0, 0)
				b.pack_start(but, 0, 0)
				hbox.pack_start(b, 0, 0)
			else:
				#hbox.pack_start(widget, -1, 1)
				hbox.pack_start(widget, 0, 0)
		return hbox
	
	def read_option_from_widget (self, widget, option):
		"""Read an option's value from the widget and return it."""
		if not widget.window:
			return False
		# get type of option and read the widget's value
		val	= None
		t	= option.__class__
		if t == IntOption:
			val = int(widget.get_value())
		elif t == FloatOption:
			val = widget.get_value()
		elif t == StringOption:
			if option.choices:
				# if default is a list, handle combobox
				val = widget.get_active_text()
			else:
				val = widget.get_text()
		elif t == BoolOption:
			val = widget.get_active()
		elif t == ColorOption:
			col = widget.get_color()
			al = widget.get_alpha()
			val = (col.red/65535.0, col.green/65535.0, 
				col.blue/65535.0, al/65535.0)
		elif t == FontOption:
			val = widget.get_font_name()
		elif t == FileOption or t == DirectoryOption or t == ImageOption:
			val = widget.get_filename()
			#print widget
		#elif t == ImageOption:
		#	val = widget.get_text()
		elif t == ListOption:	
			# the widget is a ListOptionDialog here
			val = widget.get_list()
		elif t == AccountOption:
			# the widget is a HBox containing a VBox containing two Entries
			# (ideally we should have a custom widget for the AccountOption)
			for c in widget.get_children():
				if c.__class__ == gtk.VBox:
					c2 = c.get_children()
					val = (c2[0].get_text(), c2[1].get_text())
		elif t == TimeOption:
			box = widget.get_parent()
			inputs = box.get_children()
			val = (int(inputs[0].get_value()), int(inputs[2].get_value()), 
				int(inputs[4].get_value()))
		else:
			print _("OptionsDialog: Unknown option type: %s") % str(t)
			return None
		# return the value
		return val
	
	# option-widget event-handling
	
	# TODO: custom callback/signal for each option?
	def options_callback (self, widget, optionobj):
		"""Callback for handling changed-events on entries."""
		print _("Changed: %s") % optionobj.name
		if self._shown_object:
			# if the option is not real-time updated,
			if optionobj.realtime == False:
				return False
			# read option
			val = self.read_option_from_widget(widget, optionobj)
			if val != None:
				#print "SetOption: "+optionobj.name+"="+str(val)
				# set option
				setattr(self._shown_object, optionobj.name, val)
				# notify option-object's on_changed-handler
				optionobj.emit("option_changed", optionobj)
		return False

	def apply_options_callback (self, widget, optionobj, entry):
		"""Callback for handling Apply-button presses."""
		if self._shown_object:
			# read option
			val = self.read_option_from_widget(entry, optionobj)
			if val != None:
				#print "SetOption: "+optionobj.name+"="+str(val)
				# set option
				setattr(self._shown_object, optionobj.name, val)
				# notify option-object's on_changed-handler
				optionobj.emit("option_changed", optionobj)
		return False



# ------ ONLY FOR TESTING ------------------:
if __name__ == "__main__":

	import os
	
	# this is only for testing - should be a Screenlet
	class TestObject (EditableOptions):
		
		testlist = ['test1', 'test2', 3, 5, 'Noch ein Test']
		pop3_account = ('Username', '')
		
		# TEST
		pin_x		= 100
		pin_y		= 6
		text_x		= 19
		text_y		= 35
		font_name	= 'Sans 12'
		rgba_color	= (0.0, 0.0, 1.0, 1.0)
		text_prefix	= '<b>'
		text_suffix	= '</b>'
		note_text	= ""	# hidden option because val has its own editing-dialog
		random_pin_pos	= True
		opt1 = 'testval 1'
		opt2 = 'testval 2'
		filename2	= ''
		filename	= ''
		dirname		= ''
		font = 'Sans 12'
		color = (0.1, 0.5, 0.9, 0.9)
		name = 'a name'
		name2 = 'another name'
		combo_test = 'el2'
		flt = 0.5
		x = 10
		y = 25
		width = 30
		height = 50
		is_sticky = False
		is_widget = False
		time	= (12, 32, 49)		# a time-value (tuple with ints)
		
		def __init__ (self):
			EditableOptions.__init__(self)
			# NEW way of seting options:
			# create option groups
			"""group_tst = OptionGroup('Test', 'Test options ...')
			group_gen = OptionGroup('General', 'The general options for this Object ...')
			group_win = OptionGroup('Window', 'The Window-related options for this Object ...')
			# add groups to Screenlet
			self.add_option_group(group_tst)
			self.add_option_group(group_gen)
			self.add_option_group(group_win)"""
			# short way of creating OptionGroups
			group_tst = self.create_option_group('Test', 
				'Test options ...')
			group_gen = self.create_option_group('General', 
				'The general options for this Object ...')
			group_win = self.create_option_group('Window', 
				'The Window-related options for this Object ...')
			# add options
			group_tst.add_option(StringOption('opt1', self.opt1,
				'NewOpt 1', 'A string option ...'))
			group_tst.add_option(StringOption('opt2', self.opt2,
				'NewOpt 2', 'A second string option ...', realtime=False))
			group_tst.add_option(ImageOption('filename2', os.environ['HOME'],
				'Image-Test', 'Testing the ImageOption-type ...'))
			group_tst.add_option(DirectoryOption('dirname', os.environ['HOME'],
				'Directory-Test', 'Testing a FileOption-type ...'))
			group_gen.add_option(ListOption('testlist', self.testlist,
				'ListOption-Test', 'Testing a ListOption-type ...'))
			group_gen.add_option(StringOption('name', 'TESTNAME',
				'Testname', 'The name/id of this Screenlet-instance ...', 
				realtime=False))
			group_gen.add_option(AccountOption('pop3_account', 
				self.pop3_account, 'Username/Password', 
				'Enter username/password here ...'))
			group_gen.add_option(StringOption('name2', 'TESTNAME2',
				'String2', 'Another string-test ...'))
			group_gen.add_option(StringOption('combo_test', "el1", 'Combo', 
				'A StringOption displaying a drop-down-list with choices...', 
				choices=['el1', 'el2', 'element 3']))
			group_gen.add_option(FloatOption('flt', 30, 
				'A Float', 'Testing a FLOAT-type ...', 
				min=0, max=gtk.gdk.screen_width(), increment=0.01, digits=4))
			group_win.add_option(IntOption('x', 30, 
				'X-Position', 'The X-position of this Screenlet ...', 
				min=0, max=gtk.gdk.screen_width()))
			group_win.add_option(IntOption('y', 30, 
				'Y-Position', 'The Y-position of this Screenlet ...',
				min=0, max=gtk.gdk.screen_height()))
			group_win.add_option(IntOption('width', 300, 
				'Width', 'The width of this Screenlet ...', min=100, max=1000))
			group_win.add_option(IntOption('height', 150, 
				'Height', 'The height of this Screenlet ...', 
				min=100, max=1000))
			group_win.add_option(BoolOption('is_sticky', True, 
				'Stick to Desktop', 'Show this Screenlet always ...'))
			group_win.add_option(BoolOption('is_widget', False,  
				'Treat as Widget', 'Treat this Screenlet as a "Widget" ...'))
			group_tst.add_option(FontOption('font', 'Sans 14', 
				'Font', 'The font for whatever ...'))
			group_tst.add_option(ColorOption('color', (1, 0.35, 0.35, 0.7), 
				'Color', 'The color for whatever ...'))
			group_tst.add_option(FileOption('filename', os.environ['HOME'],
				'Filename-Test', 'Testing a FileOption-type ...',
				patterns=['*.py', '*.pyc']))
			group_tst.add_option(TimeOption('time', self.time,
				'TimeOption-Test', 'Testing a TimeOption-type ...'))
			# TEST
			self.disable_option('width')
			self.disable_option('height')
			# TEST: load options from file
			#self.add_options_from_file('/home/ryx/Desktop/python/screenlets/screenlets-0.0.9/src/share/screenlets/Notes/options.xml')
		
		def __setattr__(self, name, value):
			self.__dict__[name] = value
			print name + "=" + str(value)
		
		def get_short_name(self):
			return self.__class__.__name__[:-6]

			
		
	# this is only for testing - should be a Screenlet
	class TestChildObject (TestObject):
		
		uses_theme = True
		theme_name = 'test'
		
		def __init__ (self):
			TestObject.__init__(self)
			# init properties
			self.anothertest = 'sdhglksdgklsdg'
			# init options
			group = self.get_option_group_by_name ('Test')
			group.add_option(StringOption('anothertest', self.anothertest,
				'Another Test', 'An attribute in the subclass  ...'))
	
	
	# TEST: load/save
	# TEST: option-editing
	to = TestChildObject()
	#print to.export_options_as_list()
	se = OptionsDialog(500, 380)#, treeview=True)
	#img = gtk.image_new_from_stock(gtk.STOCK_ABOUT, 5)
	img = gtk.Image()
	img.set_from_file('../share/screenlets/Notes/icon.svg')
	se.set_info('TestOptions', 
		'A test for an extended options-dialog with embedded about-info.' + 
		' Can be used for the Screenlets to have all in one ...\nNOTE:' + 
		'<span color="red"> ONLY A TEST!</span>',
		'(c) RYX 2007', version='v0.0.1', icon=img)
	se.show_options_for_object(to)
	resp = se.run()
	if resp == gtk.RESPONSE_OK:
		print "OK"
	else:
		print "Cancelled."
	se.destroy()
	#print to.export_options_as_list()

