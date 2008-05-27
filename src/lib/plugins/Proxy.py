# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free softwa

# proxy module by Helder Fraga aka whise <helder.fraga@hotmail.com>

import gconf


class Proxy:

	def __init__(self):
		self.gconf_client = gconf.client_get_default()
		self.gconf_client.notify_add("/system/http_proxy/use_http_proxy", self.get_is_active)
		self.gconf_client.notify_add("/system/http_proxy/port", self.get_port) 
		self.gconf_client.notify_add("/system/http_proxy/host", self.get_host) 
		self.get_is_active()
		self.get_port()
		self.get_host()

	def get_is_active (self):
		"""Returns if the proxy gnome settings are enabled"""
		return bool(self.gconf_client.get_bool("/system/http_proxy/use_http_proxy"))
	def get_port (self):
		"""Returns the proxy gnome settings port"""
		return self.gconf_client.get_int("/system/http_proxy/port")
	def get_host (self):
		"""Returns the proxy gnome settings host"""
		return self.gconf_client.get_string("/system/http_proxy/host")
