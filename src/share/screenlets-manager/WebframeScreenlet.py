#!/usr/bin/env python

# WebframeScreenlet
#
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

import sys
import os
import gettext

import gobject
import gtk
import screenlets

_ = screenlets.utils.get_translator(__file__)

def tdoc(obj):
    obj.__doc__ = _(obj.__doc__)
    return obj

@tdoc

class WebframeScreenlet(screenlets.Screenlet):
    """A Screenlet to browse the web"""

    __name__ = 'WebframeScreenlet'
    __version__ = '0.4.0'
    __author__ = 'Akira Ohgaki'
    __requires__ = ['python-webkit']
    __desc__ = __doc__

    browser = None
    webkit_browser = None
    gecko_browser = None
    autoreload = None

    default_theme = 'Black'
    gecko_browser_profile = 'mozilla'
    browser_engines = ['webkit', 'gecko']
    browser_width = 480
    browser_min_width = 200
    browser_max_width = 2000
    browser_height = 320
    browser_min_height = 200
    browser_max_height = 2000
    browser_border_width = 15
    browser_border_min_width = 10
    browser_border_max_width = 20
    autoreload_interval = 0 # minutes
    autoreload_max_interval = 120 # minutes
    home_uri = ''
    search_uri = 'http://www.google.com/m'
    last_uri = ''

    def __init__(self, **keyword_args):
        screenlets.Screenlet.__init__(
            self,
            width=self.browser_width + self.browser_border_width * 2,
            height=self.browser_height + self.browser_border_width * 2,
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
            _('Set your favorite pages')
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
        self.add_option(screenlets.options.IntOption(
            _('Webframe'),
            'browser_width',
            self.browser_width,
            _('Width'),
            _('Width of the browser viewport'),
            min=self.browser_min_width,
            max=self.browser_max_width
        ))
        self.add_option(screenlets.options.IntOption(
            _('Webframe'),
            'browser_height',
            self.browser_height,
            _('Height'),
            _('Height of the browser viewport'),
            min=self.browser_min_height,
            max=self.browser_max_height
        ))
        self.add_option(screenlets.options.IntOption(
            _('Webframe'),
            'browser_border_width',
            self.browser_border_width,
            _('Border width'),
            _('Thickness of border in pixels'),
            min=self.browser_border_min_width,
            max=self.browser_border_max_width
        ))
        self.add_option(screenlets.options.ListOption(
            _('Webframe'),
            'browser_engines',
            self.browser_engines,
            _('Web browser engine'),
            _('Set default engine to the first item of list')
        ))

    def on_after_set_atribute(self, name, value):
        if self.browser:
            if name == 'autoreload_interval':
                self.set_autoreload(self.autoreload_interval)
            elif name in ('browser_width', 'browser_height', 'browser_border_width'):
                self.width = self.browser_width + self.browser_border_width * 2
                self.height = self.browser_height + self.browser_border_width * 2
                self.browser.set_border_width(self.browser_border_width)
                self.redraw_canvas()

    def on_init(self):
        if not self.theme:
            #screenlets.show_message(self, _('Theme could not be loaded.'))
            print(_('Theme could not be loaded.'))
        self.init_browser()
        self.browser.set_border_width(self.browser_border_width)
        self.window.add(self.browser)
        self.window.show_all()
        if self.home_uri:
            self.browser_action('load_uri', self.home_uri)
        else:
            self.browser_action('load_uri', self.search_uri)
        self.set_autoreload(self.autoreload_interval)
        self.add_menuitem('go_back', _('Back'))
        self.add_menuitem('go_forward', _('Forward'))
        self.add_menuitem('reload', _('Reload'))
        self.add_menuitem('load_home_uri', _('Home'))
        self.add_menuitem('load_search_uri', _('Search'))
        self.add_menuitem('open_uri', _('View in Browser'))
        self.add_default_menuitems()

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
        elif id == 'open_uri':
            os.system("gnome-open '" + self.browser_action('get_uri') + "'")

    def on_mouse_enter(self, event):
        self.set_autoreload(0)

    def on_unfocus(self, event):
        self.set_autoreload(self.autoreload_interval)

    def on_draw(self, context):
        context.scale(self.scale, self.scale)
        theme_dir = self.get_screenlet_dir() + '/themes/' + self.theme_name
        bg_file = theme_dir + '/bg.png'
        left_file = theme_dir + '/left.png'
        right_file = theme_dir + '/right.png'
        top_file = theme_dir + '/top.png'
        bottom_file = theme_dir + '/bottom.png'
        left_top_file = theme_dir + '/left-top.png'
        left_bottom_file = theme_dir + '/left-bottom.png'
        right_top_file = theme_dir + '/right-top.png'
        right_bottom_file = theme_dir + '/right-bottom.png'
        left_center_file = theme_dir + '/left-center.png'
        right_center_file = theme_dir + '/right-center.png'
        top_center_file = theme_dir + '/top-center.png'
        bottom_center_file = theme_dir + '/bottom-center.png'
        image_files = (
            bg_file,
            left_file, right_file, top_file, bottom_file,
            left_top_file, left_bottom_file, right_top_file, right_bottom_file,
            left_center_file, right_center_file, top_center_file, bottom_center_file
        )
        is_collect = True
        for image_file in image_files:
            if not os.path.isfile(image_file):
                is_collect = False
                break
        if self.theme and is_collect:
            bg_size = self.theme.get_image_size(bg_file)
            left_size = self.theme.get_image_size(left_file)
            right_size = self.theme.get_image_size(right_file)
            top_size = self.theme.get_image_size(top_file)
            bottom_size = self.theme.get_image_size(bottom_file)
            left_top_size = self.theme.get_image_size(left_top_file)
            left_bottom_size = self.theme.get_image_size(left_bottom_file)
            right_top_size = self.theme.get_image_size(right_top_file)
            right_bottom_size = self.theme.get_image_size(right_bottom_file)
            left_center_size = self.theme.get_image_size(left_center_file)
            right_center_size = self.theme.get_image_size(right_center_file)
            top_center_size = self.theme.get_image_size(top_center_file)
            bottom_center_size = self.theme.get_image_size(bottom_center_file)
            left_scaled_height = (self.height - left_top_size[1] - left_center_size[1] - left_bottom_size[1]) / 2
            right_scaled_height = (self.height - right_top_size[1] - right_center_size[1] - right_bottom_size[1]) / 2
            top_scaled_width = (self.width - left_top_size[0] - top_center_size[0] - right_top_size[0]) / 2
            bottom_scaled_width = (self.width - left_bottom_size[0] - bottom_center_size[0] - right_bottom_size[0]) / 2
            self.theme.draw_scaled_image(
                context,
                self.browser_border_width,
                self.browser_border_width,
                bg_file,
                self.browser_width,
                self.browser_height
            )
            self.theme.draw_scaled_image(
                context,
                0,
                left_top_size[1],
                left_file,
                left_size[0],
                left_scaled_height
            )
            self.theme.draw_scaled_image(
                context,
                0,
                left_top_size[1] + left_scaled_height + left_center_size[1],
                left_file,
                left_size[0],
                self.height - left_top_size[1] - left_scaled_height - left_center_size[1] - left_bottom_size[1]
            )
            self.theme.draw_scaled_image(
                context,
                self.width - right_size[0],
                right_top_size[1],
                right_file,
                right_size[0],
                right_scaled_height
            )
            self.theme.draw_scaled_image(
                context,
                self.width - right_size[0],
                right_top_size[1] + right_scaled_height + right_center_size[1],
                right_file,
                right_size[0],
                self.height - right_top_size[1] - right_scaled_height - right_center_size[1] - right_bottom_size[1]
            )
            self.theme.draw_scaled_image(
                context,
                left_top_size[0],
                0,
                top_file,
                top_scaled_width,
                top_size[1]
            )
            self.theme.draw_scaled_image(
                context,
                left_top_size[0] + top_scaled_width + top_center_size[0],
                0,
                top_file,
                self.width - left_top_size[0] - top_scaled_width - top_center_size[0] - right_top_size[0],
                top_size[1]
            )
            self.theme.draw_scaled_image(
                context,
                left_bottom_size[0],
                self.height - bottom_size[1],
                bottom_file,
                bottom_scaled_width,
                bottom_size[1]
            )
            self.theme.draw_scaled_image(
                context,
                left_bottom_size[0] + bottom_scaled_width + bottom_center_size[0],
                self.height - bottom_size[1],
                bottom_file,
                self.width - left_bottom_size[0] - bottom_scaled_width - bottom_center_size[0] - right_bottom_size[0],
                bottom_size[1]
            )
            self.theme.draw_image(
                context,
                0,
                0,
                left_top_file
            )
            self.theme.draw_image(
                context,
                0,
                self.height - left_bottom_size[1],
                left_bottom_file
            )
            self.theme.draw_image(
                context,
                self.width - right_top_size[0],
                0,
                right_top_file
            )
            self.theme.draw_image(
                context,
                self.width - right_bottom_size[0],
                self.height - right_bottom_size[1],
                right_bottom_file
            )
            self.theme.draw_image(
                context,
                0,
                left_top_size[1] + left_scaled_height,
                left_center_file
            )
            self.theme.draw_image(
                context,
                self.width - right_center_size[0],
                right_top_size[1] + right_scaled_height,
                right_center_file
            )
            self.theme.draw_image(
                context,
                left_top_size[0] + top_scaled_width,
                0,
                top_center_file
            )
            self.theme.draw_image(
                context,
                left_bottom_size[0] + bottom_scaled_width,
                self.height - bottom_center_size[1],
                bottom_center_file
            )
        else:
            context.set_source_rgba(0, 0, 0, 0.7)
            context.rectangle(0, 0, self.width, self.height)
            context.fill()

    def on_draw_shape(self, context):
        self.on_draw(context)

    def init_browser(self):
        """ Initialize a web browser
        """
        self.browser = gtk.VBox()
        if self.browser_engines[0] == 'webkit':
            try:
                self.init_webkit_browser()
                scrolled_window = gtk.ScrolledWindow()
                scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                scrolled_window.add(self.webkit_browser)
                self.browser.pack_start(scrolled_window, True, True, 0)
            except:
                #screenlets.show_error(self, _('WebKit engine could not be initialized.'))
                print(_('WebKit engine could not be initialized.'))
        elif self.browser_engines[0] == 'gecko':
            try:
                self.init_gecko_browser()
                self.browser.pack_start(self.gecko_browser, True, True, 0)
            except:
                #screenlets.show_error(self, _('Gecko engine could not be initialized.'))
                print(_('Gecko engine could not be initialized.'))

    def init_webkit_browser(self):
        """ Initialize a WebKit web browser
            WebKitGTK+ Reference Manual:
            http://webkitgtk.org/reference/index.html
        """
        import webkit
        self.webkit_browser = webkit.WebView()
        settings = self.webkit_browser.get_settings()
        settings.set_property('enable-default-context-menu', False)
        self.webkit_browser.set_settings(settings)

    def init_gecko_browser(self):
        """ Initialize a Gecko web browser
            Python GtkMozembed Reference Manual:
            http://www.pygtk.org/pygtkmozembed/index.html
        """
        import gtkmozembed
        if hasattr(gtkmozembed, 'set_profile_path'):
            gtkmozembed.set_profile_path(self.get_screenlet_dir(), self.gecko_browser_profile)
        else:
            gtkmozembed.gtk_moz_embed_set_profile_path(self.get_screenlet_dir(), self.gecko_browser_profile)
        self.gecko_browser = gtkmozembed.MozEmbed()

    def browser_action(self, action, uri=''):
        """ Web browser action
        """
        if self.webkit_browser:
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
        elif self.gecko_browser:
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

    def set_autoreload(self, interval):
        """ Set an auto reload event
        """
        if self.autoreload:
            gobject.source_remove(self.autoreload)
        if (interval > 0) and (self.webkit_browser or self.gecko_browser):
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
