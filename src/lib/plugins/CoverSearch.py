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


from AmazonCoverArtSearch import AmazonCoverArtSearch
from Loader import Loader
import os

import threading
import time

class CoverSearch (threading.Thread):
	loader = None
	Result = False
	artist = ""
	album = ""
	callback_fn = False

	AlbumCover = "/tmp/nowplaying-album.jpg"

	def __init__(self):
		self.loader = Loader()
		self.engine = AmazonCoverArtSearch(self.loader)
		self.Result = False
		threading.Thread.__init__(self)

	def initData(self, artist, album, fn):
		self.artist = artist
		self.album = album
		self.callback_fn = fn

	def saveimg(self, data):
		fobj = open(self.AlbumCover,"w")
		fobj.write(data)
		fobj.close()
		self.Result = True

	def cb(self, itm, artist, album, result, *args):
		data = self.engine.get_best_match_urls(result)
		if data and self.artist == artist and self.album == album: 
			#print data[0]
			self.loader.get_url(data[0], self.saveimg)

	def run(self):
		if os.path.exists(self.AlbumCover): os.remove(self.AlbumCover)
		self.Result = False
		self.engine.search (self.artist, self.album, self.cb)
		while True:
			if self.Result: 
				break
			if not self.engine.search_next ():
				break

		cover = False
		if os.path.exists(self.AlbumCover):
			cover = self.AlbumCover

		#print threading.currentThread()
		self.callback_fn(cover)
		return None
