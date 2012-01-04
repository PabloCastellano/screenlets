#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @license  GNU General Public License Version 3
# @author   Akira Ohgaki <akiraohgaki@gmail.com>
# @link     https://launchpad.net/webframe

# Modified 2011 by Guido Tabbernuk <boamaod@gmail.com>

import sys
import os

import gobject
import gtk
import screenlets

# use gettext for translation
import gettext

_ = screenlets.utils.get_translator(__file__)

def tdoc(obj):
	obj.__doc__ = _(obj.__doc__)
	return obj

@tdoc
class WebframeScreenlet(screenlets.Screenlet):
    """ A Screenlet to browse the Web"""

    __name__ = 'WebframeScreenlet'
    __version__ = '3.0.2'
    __author__ = 'Akira Ohgaki'
    __desc__ = __doc__

    gecko_browser = None
    webkit_browser = None
    autoreload = None

    base_dir = os.path.dirname(sys.argv[0])
    default_theme = 'Black'
    gecko_browser_profile = 'mozilla'
    widget = None
    widget_width = 350
    widget_height = 510
    widget_border = 15
    browser_engines = ['webkit', 'gecko']
    browser_width = widget_width  - widget_border * 2 #320
    browser_height = widget_height - widget_border * 2 #480
    autoreload_interval = 0 #minutes
    autoreload_max_interval = 120 #minutes
    home_uri = ''
    search_uri = 'http://www.google.com/m'
    about_uri = 'https://launchpad.net/webframe'
    last_uri = ''

    def __init__(self, **keyword_args):
        screenlets.Screenlet.__init__(
            self,
            width=self.widget_width,
            height=self.widget_height,
            uses_theme=True,
            is_widget=False,
            is_sticky=True,
            resize_on_scroll=False,
            **keyword_args
        )
        self.theme_name = self.default_theme
        self.add_options_group(
            _('Webframe'),
            _('Preferences for this Webframe instance')
        )
        self.add_option(screenlets.options.StringOption(
            _('Webframe'),
            'home_uri',
            str(self.home_uri),
            _('Home page'),
           
        ))
        self.add_option(screenlets.options.IntOption(
            _('Webframe'),
            'autoreload_interval',
            self.autoreload_interval,
            _('Auto reload (minutes)'),
            _('0 is disable an auto reload event'),
            min=0,
            max=self.autoreload_max_interval
        ))
        self.add_option(screenlets.options.ListOption(
            _('Webframe'),
            'browser_engines',
            self.browser_engines,
            _('Web browser engine'),
            _('Set default engine to the first item of list')
        ))
        self.add_option(screenlets.options.IntOption(
            _('Webframe'),
            'widget_width',
            self.widget_width,
            _('Width'),
            _('Width of the widget'),
            min=1,
            max=10000
        ))
        self.add_option(screenlets.options.IntOption(
            _('Webframe'),
            'widget_height',
            self.widget_height,
            _('Height'),
            _('Height of the widget'),
            min=1,
            max=10000
        ))
        self.add_option(screenlets.options.IntOption(
            _('Webframe'),
            'widget_border',
            self.widget_border,
            _('Border width'),
            _('Thickness of border in pixels'),
            min=1,
            max=2000
        ))

    def on_after_set_atribute(self, name, value):
        if name == 'autoreload_interval':
            self.set_autoreload(value)
        elif name in ('widget_width', 'widget_height', 'widget_border'):
            self.browser_width = self.widget_width  - self.widget_border * 2 #320
            self.browser_height = self.widget_height - self.widget_border * 2 #480
            self.update_size()
            if self.window:
                self.redraw_canvas()
                self.update_shape()
                self.window.show_all()

    def on_init(self):
        if not self.theme:
            print 'Theme could not be loaded.'
        self.embed_browser()
        self.set_autoreload(self.autoreload_interval)
        if self.home_uri:
            self.browser_action('load_uri', self.home_uri)
        else:
            self.browser_action('load_uri', self.search_uri)
        self.add_menuitem('go_back', _('Back'))
        self.add_menuitem('go_forward', _('Forward'))
        self.add_menuitem('reload', _('Reload'))
        self.add_menuitem('load_home_uri', _('Home'))
        self.add_menuitem('load_search_uri', _('Search'))
        self.add_menuitem('open_uri', _('View in Browser'))
        self.add_default_menuitems()
#        self.add_menuitem('open_about_uri', _('About Webframe'))

    def on_menuitem_select(self, id):
        if id == 'go_back':
            self.browser_action('go_back')
        elif id == 'go_forward':
            self.browser_action('go_forward')
        elif id == 'reload':
            self.browser_action('reload')
        elif id == 'load_home_uri':
            self.browser_action('load_uri', self.home_uri)
        elif id == 'load_search_uri':
            self.browser_action('load_uri', self.search_uri)
#        elif id == 'open_about_uri':
#            os.system("gnome-open '" + self.about_uri + "'")
        elif id == 'open_uri':
            os.system("gnome-open '" + self.browser_action('get_uri') + "'")

    def on_mouse_enter(self, event):
        self.set_autoreload(0)

    def on_unfocus(self, event):
        self.set_autoreload(self.autoreload_interval)

    def on_draw(self, context):
        context.scale(self.scale, self.scale)
        if self.theme:
            themes_dir = sys.path[0] + '/themes/'
            bg_file = themes_dir + self.theme_name + '/bg'
            # check the contents
            if os.path.isfile(bg_file + ".svg"):
                bg_file = bg_file + ".svg"
            elif os.path.isfile(bg_file + ".png"):
                bg_file = bg_file + ".png"
            else:
                bg_file = None
            self.theme.draw_scaled_image(context, 0, 0, bg_file, self.width, self.height)
        else:
            context.set_source_rgba(0, 0, 0, 0.7)
            context.rectangle(0, 0, self.widget_width, self.widget_height)
            context.fill()

    def on_draw_shape(self, context):
        self.on_draw(context)

    def update_size(self):
        if self.widget is not None:
            self.widget.set_border_width(self.widget_border)
            self.widget.set_size_request(self.browser_width, self.browser_height)
            self.width = self.widget_width
            self.height = self.widget_height

    def embed_browser(self):
        """ Embed a web browser
        """
        self.widget = gtk.VBox()
        self.widget.set_border_width(self.widget_border)
        self.widget.set_size_request(self.browser_width, self.browser_height)
        if self.browser_engines[0] == 'gecko':
            try:
                self.setup_gecko_browser()
                self.gecko_browser.set_size_request(self.browser_width, self.browser_height)
                self.widget.pack_start(self.gecko_browser, True, True, 0)
            except:
                print 'Gecko engine could not be initialized.'
        elif self.browser_engines[0] == 'webkit':
            try:
                self.setup_webkit_browser()
                self.webkit_browser.set_size_request(self.browser_width, self.browser_height)
                scrolled_window = gtk.ScrolledWindow()
                scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                scrolled_window.add(self.webkit_browser)
                self.widget.pack_start(scrolled_window, True, True, 0)
            except:
                print 'WebKit engine could not be initialized.'
        self.window.add(self.widget)
        self.window.show_all()

    def setup_gecko_browser(self):
        """ Setup a Gecko web browser
            Python GtkMozembed Reference Manual:
            http://www.pygtk.org/pygtkmozembed/index.html
        """
        import gtkmozembed
        if hasattr(gtkmozembed, 'set_profile_path'):
            gtkmozembed.set_profile_path(self.base_dir, self.gecko_browser_profile)
        else:
            gtkmozembed.gtk_moz_embed_set_profile_path(self.base_dir, self.gecko_browser_profile)
        self.gecko_browser = gtkmozembed.MozEmbed()

    def setup_webkit_browser(self):
        """ Setup a WebKit web browser
            WebKitGTK+ Reference Manual:
            http://webkitgtk.org/reference/index.html
        """
        import webkit
        self.webkit_browser = webkit.WebView()
        settings = self.webkit_browser.get_settings()
        settings.set_property('enable-default-context-menu', False)
        self.webkit_browser.set_settings(settings)

    def browser_action(self, action, uri=''):
        """ Web browser action
        """
        if self.gecko_browser:
            if action == 'go_back':
                self.gecko_browser.go_back()
            elif action == 'go_forward':
                self.gecko_browser.go_forward()
            elif action == 'reload':
                self.gecko_browser.reload(True)
            elif action == 'load_uri':
                self.gecko_browser.load_url(uri)
            elif action == 'get_uri':
                return self.gecko_browser.get_location()
        elif self.webkit_browser:
            if action == 'go_back':
                self.webkit_browser.go_back()
            elif action == 'go_forward':
                self.webkit_browser.go_forward()
            elif action == 'reload':
                self.webkit_browser.reload()
            elif action == 'load_uri':
                self.webkit_browser.load_uri(uri)
            elif action == 'get_uri':
                return self.webkit_browser.get_property('uri')

    def set_autoreload(self, interval):
        """ Set an auto reload event
        """
        if self.autoreload:
            gobject.source_remove(self.autoreload)
        if (interval > 0) and (self.gecko_browser or self.webkit_browser):
            self.last_uri = self.browser_action('get_uri')
            self.autoreload = gobject.timeout_add(60000 * interval, self.autoreload_handler)

    def autoreload_handler(self):
        """ Auto reload event handler
        """
        if self.last_uri == self.browser_action('get_uri'):
            self.browser_action('reload')
            return True
        else:
            return False

if __name__ == '__main__':
    screenlets.session.create_session(WebframeScreenlet)
