# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free softwa

# Flickr module by Helder Fraga aka whise <helder.fraga@hotmail.com>


from urllib import urlopen
import Proxy

class Flickr:

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

