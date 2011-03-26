#
# Copyright (C) 2009 Martin Owens (DoctorMO) <doctormo@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
Base classes and basic mechanics for all screenlet options.
"""

import screenlets
from screenlets.options import _

import os
import gtk, gobject
import xml.dom.minidom
from xml.dom.minidom import Node

# -----------------------------------------------------------------------
# Option-classes and subclasses
# -----------------------------------------------------------------------

class Option(gobject.GObject):
    """An Option stores information about a certain object-attribute. It doesn't
    carry information about the value or the object it belongs to - it is only a
    one-way data-storage for describing how to handle attributes."""
    __gsignals__ = dict(option_changed=(gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, (gobject.TYPE_OBJECT,)))
    default = None
    label = None
    desc = None
    hidden = False
    disabled = False
    realtime = True
    protected = False
    widget = None

    def __init__ (self, group, name, **args):
        """Creates a new Option with the given information."""
        super(Option, self).__init__()
        self.name = name
        self.group = group
        # This should allow any of the class options to be set on init.
        for name in args.keys():
            if hasattr(self, name):
                setattr(self, name, args[name])

        # XXX for groups (TODO: OptionGroup)
        # XXX callback to be notified when this option changes
        # XXX real-time update?
        # XXX protected from get/set through service

    def on_import(self, strvalue):
        """Callback - called when an option gets imported from a string.
        This function MUST return the string-value converted to the required
        type!"""
        return strvalue.replace("\\n", "\n")

    def on_export(self, value):
        """Callback - called when an option gets exported to a string. The
        value-argument needs to be converted to a string that can be imported
        by the on_import-handler. This handler MUST return the value
        converted to a string!"""
        return str(value).replace("\n", "\\n")

    def generate_widget(self):
        """This should generate all the required widgets for display."""
        raise NotImplementedError, "Generating Widget should be done in child"

    def set_value(self, value):
        """Set the true/false value to the checkbox widget"""
        raise NotImplementedError, "Can't update the widget and local value"

    def has_changed(self):
        """Executed when the widget event kicks off."""
        return self.emit("option_changed", self)


def create_option_from_node (node, groupname):
    """Create an Option from an XML-node with option-metadata."""
    #print "TODO OPTION: " + str(cn)
    otype = node.getAttribute("type")
    oname = node.getAttribute("name")
    ohidden = node.getAttribute("hidden")
    options = {
        'default'   : None,
        'info'      : '',
        'label'     : '',
        'min'       : None,
        'max'       : None,
        'increment' : 1,
        'choices'   : '',
        'digits'    : None,
    }
    if otype and oname:
        # parse children of option-node and save all useful attributes
        for attr in node.childNodes:
            if attr.nodeType == Node.ELEMENT_NODE and attr.nodeName in options.keys():
                options[attr.nodeName] = attr.firstChild.nodeValue
        # if we have all needed values, create the Option
        if options['default']:
            # create correct classname here
            cls = otype[0].upper() + otype.lower()[1:] + 'Option'
            #print 'Create: ' +cls +' / ' + oname + ' ('+otype+')'
            # and build new instance (we use on_import for setting default val)
            clsobj = getattr(__import__(__name__), cls)
            opt = clsobj(groupname, oname, default=None,
                label=options['label'], desc=options['info'])
            opt.default = opt.on_import(options['default'])
            # set values to the correct types
            if cls == 'IntOption':
                if options['min']:
                    opt.min = int(options['min'])
                if options['max']:
                    opt.max = int(options['max'])
                if options['increment']:
                    opt.increment = int(options['increment'])
            elif cls == 'FloatOption':
                if options['digits']:
                    opt.digits = int(options['digits'])
                if options['min']:
                    opt.min = float(options['min'])
                if options['min']:
                    opt.max = float(options['max'])
                if options['increment']:
                    opt.increment = float(options['increment'])
            elif cls == 'StringOption':
                if options['choices']:
                    opt.choices = options['choices']
            return opt
    return None


class EditableOptions(object):
    """The EditableOptions can be inherited from to allow objects to export
    editable options for editing them with the OptionsEditor-class.
    NOTE: This could use some improvement and is very poorly coded :) ..."""

    def __init__ (self):
        self.__options__ = []
        self.__options_groups__ = {}
        # This is a workaround to remember the order of groups
        self.__options_groups_ordered__ = []

    def add_option (self, option, callback=None, realtime=True):
        """Add an editable option to this object. Editable Options can be edited
        and configured using the OptionsDialog. The optional callback-arg can be
        used to set a callback that gets notified when the option changes its
        value."""
        #print "Add option: "+option.name
        # if option already editable (i.e. initialized), return
        for o in self.__options__:
            if o.name == option.name:
                return False
        self.__dict__[option.name] = option.default
        # set auto-update (TEMPORARY?)
        option.realtime = realtime
        # add option to group (output error if group is undefined)
        try:
            self.__options_groups__[option.group]['options'].append(option)
        except:
            print "Options: Error - group %s not defined." % option.group
            return False
        # now add the option
        self.__options__.append(option)
        # if callback is set, add callback
        if callback:
            option.connect("option_changed", callback)
        option.connect("option_changed", self.callback_value_changed)
        return True


    def add_options_group (self, name, group_info):
        """Add a new options-group to this Options-object"""
        self.__options_groups__[name] = {'label':name,
            'info':group_info, 'options':[]}
        self.__options_groups_ordered__.append(name)
        #print self.options_groups

    def disable_option(self, name):
        """Disable the inputs for a certain Option."""
        for o in self.__options__:
            if o.name == name:
                o.disabled = True
                return True
        return False

    def enable_option(self, name):
        """Enable the inputs for a certain Option."""
        for o in self.__options__:
            if o.name == name:
                o.disabled = False
                return True
        return False

    def export_options_as_list(self):
        """Returns all editable options within a list (without groups)
        as key/value tuples."""
        lst = []
        for o in self.__options__:
            lst.append((o.name, o.on_export(getattr(self, o.name))))
        return lst

    def callback_value_changed(self, sender, option):
        """Called when a widget has updated and this needs calling."""
        if hasattr(self, option.name):
            return setattr(self, option.name, option.value)
        raise KeyError, "Callback tried to set an option that wasn't defined."

    def get_option_by_name (self, name):
        """Returns an option in this Options by it's name (or None).
        TODO: this gives wrong results in childclasses ... maybe access
        as class-attribute??"""
        for o in self.__options__:
            if o.name == name:
                return o
        return None

    def remove_option (self, name):
        """Remove an option from this Options."""
        for o in self.__options__:
            if o.name == name:
                del o
                return True
        return True

    def add_options_from_file (self, filename):
        """This function creates options from an XML-file with option-metadata.
        TODO: make this more reusable and place it into module (once the groups
        are own objects)"""
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
                    group = {}
                    group['name']        = node.getAttribute("name")
                    if not group['name']:
                        raise Exception(_('No name for group defined in "%s".') % filename)
                    group['info']        = ''
                    group['options']    = []
                    # check all children in group
                    for on in node.childNodes:
                        if on.nodeType == Node.ELEMENT_NODE:
                            if on.nodeName == 'info':
                                # info-node? set group-info
                                group['info'] = on.firstChild.nodeValue
                            elif on.nodeName == 'option':
                                # option node? parse option node
                                opt = create_option_from_node (on, group['name'])
                                # ok? add it to list
                                if opt:
                                    group['options'].append(opt)
                                else:
                                    raise Exception(_('Invalid option-node found in "%s".') % filename)

                    # create new group
                    if len(group['options']):
                        self.add_options_group(group['name'], group['info'])
                        for o in group['options']:
                            self.add_option(o)
                    # add group to list
                    #groups.append(group)


class OptionsDialog(gtk.Dialog):
    """A dynamic options-editor for editing Screenlets which are implementing
    the EditableOptions-class."""

    __shown_object = None

    def __init__ (self, width, height):
        # call gtk.Dialog.__init__
        super(OptionsDialog, self).__init__(
            _("Edit Options"), flags=gtk.DIALOG_DESTROY_WITH_PARENT |
            gtk.DIALOG_NO_SEPARATOR,
            buttons = (#gtk.STOCK_REVERT_TO_SAVED, gtk.RESPONSE_APPLY,
                gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
        # set size
        self.resize(width, height)
        self.set_keep_above(True)    # to avoid confusion
        self.set_border_width(10)
        # create attribs
        self.page_about   = None
        self.page_options = None
        self.page_themes  = None
        self.vbox_editor  = None
        self.hbox_about   = None
        self.infotext     = None
        self.infoicon     = None
        # create theme-list
        self.liststore    = gtk.ListStore(object)
        self.tree         = gtk.TreeView(model=self.liststore)
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

    def reset_to_defaults(self):
        """Reset all entries for the currently shown object to their default
        values (the values the object has when it is first created).
        NOTE: This function resets ALL options, so BE CARFEUL!"""
        if self.__shown_object:
            for o in self.__shown_object.__options__:
                # set default value
                setattr(self.__shown_object, o.name, o.default)

    def set_info(self, name, info, copyright='', version='', icon=None):
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
        The Object needs to be an EditableOptions-subclass.
        NOTE: This needs heavy improvement and should use OptionGroups once
              they exist"""
        self.__shown_object = obj
        # create notebook for groups
        notebook = gtk.Notebook()
        self.vbox_editor.add(notebook)
        for group in obj.__options_groups_ordered__:
            group_data = obj.__options_groups__[group]
            # create box for tab-page
            page = gtk.VBox()
            page.set_border_width(10)
            if group_data['info'] != '':
                info = gtk.Label(group_data['info'])
                info.show()
                info.set_alignment(0, 0)
                page.pack_start(info, 0, 0, 7)
                sep = gtk.HSeparator()
                sep.show()
                #page.pack_start(sep, 0, 0, 5)
            # create VBox for inputs
            box = gtk.VBox()
            box.show()
            box.set_border_width(5)
            # add box to page
            page.add(box)
            page.show()
            # add new notebook-page
            label = gtk.Label(group_data['label'])
            label.show()
            notebook.append_page(page, label)
            # and create inputs
            for option in group_data['options']:
                if option.hidden == False:
                    val = getattr(obj, option.name)
                    w = self.generate_widget( option, val )
                    if w:
                        box.pack_start(w, 0, 0)
                        w.show()
        notebook.show()
        # show/hide themes tab, depending on whether the screenlet uses themes
        if obj.uses_theme and obj.theme_name != '':
            self.show_themes_for_screenlet(obj)
        else:
            self.page_themes.hide()

    def generate_widget(self, option, value):
        """Generate the required widgets and add the label."""
        widget = option.generate_widget(value)
        hbox = gtk.HBox()
        label = gtk.Label()
        label.set_alignment(0.0, 0.0)
        label.set_label(option.label)
        label.set_size_request(180, 28)
        label.show()
        hbox.pack_start(label, 0, 1)
        if widget:
            if option.disabled:
                widget.set_sensitive(False)
                label.set_sensitive(False)
            self.tooltips.set_tip(widget, option.desc)
            widget.show()
            # check if needs Apply-button
            if option.realtime == False:
                but = gtk.Button(_('Apply'), gtk.STOCK_APPLY)
                but.show()
                but.connect("clicked", option.has_changed)
                b = gtk.HBox()
                b.show()
                b.pack_start(widget, 0, 0)
                b.pack_start(but, 0, 0)
                hbox.pack_start(b, 0, 0)
            else:
                hbox.pack_start(widget, 0, 0)
        return hbox


    def show_themes_for_screenlet (self, obj):
        """Update the Themes-page to display the available themes for the
        given Screenlet-object."""
        dircontent = []
        # now check all paths for themes
        for path in screenlets.SCREENLETS_PATH:
            p = path + '/' + obj.get_short_name() + '/themes'
            print p
            #p = '/usr/local/share/screenlets/Clock/themes'    # TEMP!!!
            try:
                dc = os.listdir(p)
                for d in dc:
                    dircontent.append({'name':d, 'path':p+'/'})
            except:
                print "Path %s not found." % p
        # list with found themes
        found_themes = []
        # check all themes in path
        for elem in dircontent:
            # load themes with the same name only once
            if found_themes.count(elem['name']):
                continue
            found_themes.append(elem['name'])
            # build full path of theme.conf
            theme_conf = elem['path'] + elem['name'] + '/theme.conf'
            # if dir contains a theme.conf
            if os.access(theme_conf, os.F_OK):
                # load it and create new list entry
                ini = screenlets.utils.IniReader()
                if ini.load(theme_conf):
                    # check for section
                    if ini.has_section('Theme'):
                        # get metainfo from theme
                        th_fullname = ini.get_option('name', 
                            section='Theme')
                        th_info     = ini.get_option('info', 
                            section='Theme')
                        th_version  = ini.get_option('version', 
                            section='Theme')
                        th_author   = ini.get_option('author', 
                            section='Theme')
                        # create array from metainfo and add it to liststore
                        info = [elem['name'], th_fullname, th_info, th_author, 
                            th_version]
                        self.liststore.append([info])
                    else:
                        # no theme section in theme.conf just add theme-name
                        self.liststore.append([[elem['name'], '-', '-', '-', '-']])
            else:
                # no theme.conf in dir? just add theme-name
                self.liststore.append([[elem['name'], '-', '-', '-', '-']])
            # is it the active theme?
            if elem['name'] == obj.theme_name:
                # select it in tree
                print "active theme is: %s" % elem['name']
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
        self.vbox_editor    = gtk.VBox(spacing=3)
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
        self.tree.connect('cursor-changed', self.__tree_cursor_changed)
        self.tree.show()
        col = gtk.TreeViewColumn('')
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        #cell.set_property('foreground', 'black')
        col.set_cell_data_func(cell, self.__render_cell)
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

    def __render_cell(self, tvcolumn, cell, model, iter):
        """Callback for rendering the cells in the theme-treeview."""
        # get attributes-list from Treemodel
        attrib = model.get_value(iter, 0)

        # set colors depending on state
        col = '555555'
        name_uc = attrib[0][0].upper() + attrib[0][1:]
        # create markup depending on info
        if attrib[1] == '-' and attrib[2] == '-':
            mu = '<b><span weight="ultrabold" size="large">' + name_uc + \
            '</span></b> (' + _('no info available') + ')'
        else:
            if attrib[1] == None : attrib[1] = '-'
            if attrib[2] == None : attrib[2] = '-'
            if attrib[3] == None : attrib[3] = '-'
            if attrib[4] == None : attrib[4] = '-'
            mu = '<b><span weight="ultrabold" size="large">' + name_uc + \
                '</span></b> v' + attrib[4] + '\n<small><span color="#555555' +\
                '">' + attrib[2].replace('\\n', '\n') + \
                '</span></small>\n<i><small>by '+str(attrib[3])+'</small></i>'
        # set markup
        cell.set_property('markup', mu)

    # UI-callbacks

    def __tree_cursor_changed (self, treeview):
        """Callback for handling selection changes in the Themes-treeview."""
        sel = self.tree.get_selection()
        if sel:
            s = sel.get_selected()
            if s:
                it = s[1]
                if it:
                    attribs = self.liststore.get_value(it, 0)
                    if attribs and self.__shown_object:
                        #print attribs
                        # set theme in Screenlet (if not already active)
                        if self.__shown_object.theme_name != attribs[0]:
                            self.__shown_object.theme_name = attribs[0]

