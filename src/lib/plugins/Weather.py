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
# Weather plugin to obtain weather information. 
# All info is obtained from weather.com.
#
# Rastko Karadzic <rastkokaradzic@gmail.com>
#

from urllib import urlopen
import socket	
import ast
from screenlets import Plugins
proxy = Plugins.importAPI('Proxy')





def getZipCode(cityName):
	""" Finds ZIP code for a given city name from http://www.weather.com .
		Returns dictionary (or array of dictionaries if multiple cities from different countries/states found) in format:
		{'name':'cityName','country':'countryShorName', 'countryName':'countryFullName', 'state': 'state', 'key': 'cityZIP', 'type':locationType, 'class': '??'}
		example:
		{'name': 'Belgrade', 'country': 'US', 'countryName': 'UNITED STATES OF AMERICA', 'state': 'ME', 'key': 'USME0025', 'type': 1, 'class': 'location'}
	"""
	proxies = proxy.Proxy().get_proxy()
	try:
		data = urlopen('http://wxdata.weather.com/wxdata/ta/'+cityName.replace(" ","+")+'.js?max=10&key=2227ef4c-dfa4-11e0-80d5-0022198344f4',proxies=proxies).read()
		data = ast.literal_eval(data)
		return data["results"]
	except (IOError, socket.error), e:
		print "Error retrieving city zip code", e
		self.show_error((_("Error retrieving city zip code"), e))
		return None

class Weather(object):
	""" Weather plugin class used to download and parse weather data from www.weather.com """
	
	def __init__(self, ZIP="SRXX0005", use_metrics=True):
		""" Initializes Weather class with given city ZIP code and use_metrics boolean - True if want to get data in metrics unit system, else to get in imperial unit system.
			For city ZIP code look at http://www.weather.com or get and extract ti from getZipCode (see above).
		"""
		#True if use metrics unit system, false if use imperial unit system
		self.use_metrics = use_metrics
		self.ZIP = ZIP
		#Developer API key from weather.com (from Whise)
		self.api_key = "4128909340a9b2fc"
		#Partner key from weather.com (from Whise)
		self.partner_key = "1003666583"

	
	def update_zip(self, ZIP, use_metrics=True):
		self.ZIP = ZIP
		self.use_metrics = use_metrics
		
	def getCurrentConditions(self):
		""" Downloads and parses current weather conditions.	
			Returns detailed current weather condition info(temperature, wind...) stored in a dictionary.
		"""
		if self.use_metrics:
			unit = 'm'
		else:
			unit = 's'
		result = {}
		proxies = proxy.Proxy().get_proxy()
		try:
				data = urlopen('http://xoap.weather.com/weather/local/'+self.ZIP+'?cc=*&par='+self.partner_key+'&key='+self.api_key+'&unit='+unit,proxies=proxies).read()
				chunk = self.getBetween(data,"<cc>","<bar>")
				#Time and date of last update of info
				result["lsup"] = self.getBetween(chunk,"<lsup>","</lsup>")	
				#Observatory that got weather info
				result["obst"] = self.getBetween(chunk,"<obst>","</obst>")
				#Current temprature
				result["temp"] = self.getBetween(chunk,"<tmp>","</tmp>")
				#Current temperature considering the windchill factor
				result["temp_flik"] = self.getBetween(chunk,"<flik>","</flik>")
				#Text description of current temperature
				result["temp_descr"] = self.getBetween(chunk,"<t>","</t>")
				#Weather icon id
				result["icon"] = self.getBetween(chunk,"<icon>","</icon>")
				chunk = self.getBetween(data,"<bar>","</bar>")
				#Air pressure value
				result["bar"] = self.getBetween(chunk,"<r>","</r>")
				#Description of raise or fall of air pressure								
				result["bar_descr"] = self.getBetween(chunk,"<d>","</d>")
				chunk = self.getBetween(data,"<wind>","</wind>")
				#Wind speed
				result["wind_speed"] = self.getBetween(chunk,"<s>","</s>")
				#Maximum gust speed
				result["wind_gust"] = self.getBetween(chunk,"<gust>","</gust>")
				#Wind direction in degrees
				result["wind_direction_degr"] = self.getBetween(chunk,"<d>","</d")
				#Text description of wind direction
				result["wind_direction_descr"] = self.getBetween(chunk,"<t>","</t>")
				#Humidity value
				result["hmid"] = self.getBetween(data,"<hmid>","</hmid>")
				#Visibility
				result["vis"] = self.getBetween(data,"<vis>","</vis>")
				chunk = self.getBetween(data,"<uv>", "</uv>")
				#UV index
				result["uv_index"] = self.getBetween(chunk,"<i>","</i>")
				#UV text description
				result["uv_descr"] = self.getBetween(chunk,"<t>","</t>")
				#Integer dew point
				result["dewp"] = self.getBetween(data,"<dewp>","</dewp>")			
		except (IOError, socket.error), e:
			print "Error retrieving weather data", e
			self.show_error((_("Error retrieving weather data"), e))
			return None

		return result
				

		
	def getDailyWeatherData(self):
			""" Downloads and parses 5 day weather info starting from current day.
				Returns array of dictionaries. Every dictionary contains daily weather info.
				First dictionary in array contains weather info for current day.
			"""
			if self.use_metrics:
				unit = 'm'
			else:
				unit = 's'

			result = []
			proxies = proxy.Proxy().get_proxy()
			try:
				data = urlopen('http://xoap.weather.com/weather/local/'+self.ZIP+'?dayf=5&par='+self.partner_key+'&key='+self.api_key+'&unit='+unit,proxies=proxies).read()

				for x in range(5):
					dfrom = data.find('<day d=\"'+str(x))
					dto = data.find('</day>',dfrom)
					day = data[dfrom:dto]
					result.append(self.parseDailyData(day))
			except (IOError, socket.error), e:
				print "Error retrieving weather data", e
				self.show_error((_("Error retrieving weather data"), e))
				return None
			return result



	def getHourlyWeatherData(self):
			""" Downloads and parses 12 hour weather starting from next hour.
				Returns array of dictionaries. Every dictionary contains hour weather info.
				First dictionary in array contains hourly weather data for next hour.
			"""
			if self.use_metrics:
				unit = 'm'
			else:
				unit = 's'

			result = []
			try:
			
				proxies = proxy.Proxy().get_proxy()
				data = urlopen('http://xoap.weather.com/weather/local/'+self.ZIP+'?hbhf=12&par='+self.partner_key+'&key='+self.api_key+'&unit='+unit,proxies=proxies).read()
				for x in range(1,13):
					dfrom = data.find('<hour h=\"'+str(x))
					dto = data.find('</hour>',dfrom) 
					hour = data[dfrom:dto]
					result.append(self.parseHourlyData(hour))
			except (IOError, socket.error), e:
				print "Error retrieving weather data", e
				self.show_error((_("Error retrieving weather data"), e))
				return None
			return result


	def parseDailyData(self,data):
		day = self.getBetween(data, '<part p="d">', '</part>')
		day_wind = self.getBetween(day, '<wind>', '</wind>')
		night = self.getBetween(data, '<part p="n">', '</part>')
		night_wind = self.getBetween(night, '<wind>', '</wind>')

		tokenized = {
		'date': self.getBetween(data, 'dt=\"','\"'),
		'day' : self.getBetween(data, 't=\"','\"'),
		'high': self.getBetween(data, '<hi>','</hi>'),
		'low': self.getBetween(data, '<low>','</low>'),	
		'sunr': self.getBetween(data, '<sunr>','</sunr>'),
		'suns' : self.getBetween(data, '<suns>','</suns>'),		
		'day_icon' : self.getBetween(day, '<icon>','</icon>'), 
		'day_descr' : self.getBetween(day, '<t>','</t>'), 
		'day_wind_speed' : self.getBetween(day_wind, '<s>','</s>'), 
		'day_wind_dir_degr' : self.getBetween(day_wind, '<d>','</d>'), 
		'day_wind_dir_descr' : self.getBetween(day_wind, '<t>','</t>'), 
		'day_ppcp' : self.getBetween(day, '<ppcp>','</ppcp>'), 
		'day_hmid' : self.getBetween(day, '<hmid>','</hmid>'),
		'night_icon' : self.getBetween(night, '<icon>','</icon>'), 
		'night_descr' : self.getBetween(night, '<t>','</t>'), 
		'night_wind_speed' : self.getBetween(night_wind, '<s>','</s>'), 
		'night_wind_dir_degr' : self.getBetween(night_wind, '<d>','</d>'),
		'night_wind_dir_descr' : self.getBetween(night_wind, '<t>','</t>'), 
		'night_ppcp' : self.getBetween(night, '<ppcp>','</ppcp>'), 
		'night_hmid' : self.getBetween(night, '<hmid>','</hmid>'),
		}
		return tokenized

	def parseHourlyData(self,data):
		result = {
			'hour': self.getBetween(data, 'c=\"','\"'),
			'temp': self.getBetween(data, '<tmp>','</tmp>'),
			'temp_descr' : self.getBetween(data,'<t>','</t>'),
			'temp_flik': self.getBetween(data, '<flik>','</flik>'),
			'ppcp': self.getBetween(data, '<ppcp>','</ppcp>'),
			'dewp': self.getBetween(data, '<dewp>','</dewp>'),
			'hmid': self.getBetween(data, '<hmid>','</hmid>'),
			'icon': self.getBetween(data, '<icon>','</icon>')
		}
		chunk = self.getBetween(data,'<wind>','</wind>')
		result["wind_speed"] = self.getBetween(chunk,"<s>","</s>")
		result["wind_gust"] = self.getBetween(chunk,"<gust>","</gust>")
		result["wind_dir_degr"] = self.getBetween(chunk,"<d>","</d>")
		result["wind_dir_descr"] = self.getBetween(chunk,"<t>","</t>")
		return result
	
	

	def getBetween(self,data, first, last):
		x = len(first)
		begin = data.find(first) +x
		end = data.find(last, begin)
		return data[begin:end]
