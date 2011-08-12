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

from Convert import RatioConverter

# This is an example use of the RatioConverter superclass. See also
# the documentation of Converter and RatioConverter in ConvertScreenlet.py, for 
# description of the variables, please.
class LengthConverter(RatioConverter):
	"""A converter which converts lengths between centimeters and inches."""
	
	# These fields must be defined in every screenlet:
	# __name__: the name of the class
	__name__ = 'LengthConverter'
	# __title__: a short description to be shown in the menu and Options dialog
	__title__ = 'cm / inches'
	# author and version - not currently shown anywhere
	__author__ = 'Vasek Potocek'
	__version__ = '0.2'

	# the number of fields and their captions
	num_fields = 2
	field_names = ['cm', 'in']
	
	# The relative weights of the fields. Here, we set 1 for cm and 2.54 for an 
	# inch, meaning one inch is a unit 2.54 times larger than a centimeter. Note 
	# that the values will be in an inversed ratio.
	weights = [1, 2.54]
