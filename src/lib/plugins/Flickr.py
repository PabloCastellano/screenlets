#
# Flickr module by Helder Fraga aka whise <helder.fraga@hotmail.com>
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

from urllib import urlopen
import Proxy

class Flickr(object):

	url_list = {}


	def __init__(self):
		pass

	def get_image_list(self,url):
		"""Returns a Tuple containing images links and webpage links of a flickr url"""
		list_a = []
		self.url_list = {}
		proxies = Proxy.Proxy().get_proxy()	
		sourcetxt = urlopen(url,proxies=proxies).read()
		while sourcetxt.find("Photo" + chr(34)) != -1:
			image = sourcetxt[sourcetxt.find("Photo" + chr(34))+7:]
			sourcetxt = image
			sourceimage = image[image.find("a href=" + chr(34))+8:]
			sourceimage = sourceimage[:sourceimage.find(chr(34)) ].strip()
			realimage = image[image.find("mg src=" + chr(34))+8:]
			realimage = realimage[:realimage.find(chr(34)) ].strip()
			imageurl = 'http://www.flickr.com' + sourceimage
			list_a.append(realimage)
			self.url_list[realimage] = imageurl
		return list_a


	def save_image(self,url,path):
		"""Saves the image from url in path"""
		proxies = Proxy.Proxy().get_proxy()
		sourcetxt = urlopen(url,proxies=proxies).read()
		fileObj = open( path,"w") #// open for for write
		fileObj.write(sourcetxt)
		fileObj.close()

