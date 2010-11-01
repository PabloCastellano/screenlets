# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free softwa

# proxy module by Helder Fraga aka whise <helder.fraga@hotmail.com>

import gconf


class Proxy(object):

	def __init__(self):
		try:
			self.gconf_client = gconf.client_get_default()
			self.gconf_client.notify_add("/system/http_proxy/use_http_proxy", self.get_is_active)
			self.gconf_client.notify_add("/system/http_proxy/port", self.get_port) 
			self.gconf_client.notify_add("/system/http_proxy/host", self.get_host) 
		except:pass
		self.get_is_active()
		self.get_port()
		self.get_host()

	def get_is_active (self):
		"""Returns if the proxy gnome settings are enabled, shoulnt be used separatly"""
		try:
			a = bool(self.gconf_client.get_bool("/system/http_proxy/use_http_proxy"))
			return a
		except:
			return None
	def get_port (self):
		"""Returns the proxy gnome settings port, shoulnt be used separatly"""
		try:
			a = self.gconf_client.get_int("/system/http_proxy/port")
			return a
		except:
			return None
	def get_host (self):
		"""Returns the proxy gnome settings host, shoulnt be used separatly"""
		try:
			a = self.gconf_client.get_string("/system/http_proxy/host")
			return a
		except:
			return None

	def get_proxy(self):
		"""Return {'http' : HOST:PORT } if available or {} if not"""
		try:
			proxy = {}
			if self.get_is_active():
				a = self.get_host()
				b = self.get_port()
				if a != None and b != None:
					c = str(a) + ':' + str(b)
					if c.find ('http://') == -1: c = 'http://' + c
					proxy['http'] = c
					return proxy
			
			else: return proxy
		except:
			return {}
