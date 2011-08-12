# coding=UTF-8

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

from Convert import Converter

class TemperatureConverter(Converter):
	"""A converter which converts temperature between Fahrenheit and Celsius."""
	
	__name__ = 'TemperatureConverter'
	__title__ = 'Fahrenheit / Celsius'
	__author__ = 'Arnav Ghosh'
	__version__ = '0.2'

	num_fields = 2
	field_names = [u'˚F', u'˚C']

	def __init__(self):
		self.active_field = 0
		self.values = ['0', '0']
		# 0˚F is not 0˚C, let's correct this by a call to convert()
		# (this leaves '0' on the active field)
		self.convert()

	def filter_key(self, key):
		if key.isdigit() or key == '+' or key == '-':
			return True
		elif key == '.':
			return not ('.' in self.values[self.active_field])
		else:
			return False
	
	def convert(self):
		try:
			val = float(self.values[self.active_field])
		except:
			val = 0		# This handles the case of a single '-' in input
		if self.active_field == 0:
			self.values[1] = '%.1f' % ((val - 32) / 1.8)
		else:
			self.values[0] = '%.1f' % ((val * 1.8) + 32)
