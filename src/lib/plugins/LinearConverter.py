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

# This module contains classes (LinearUnit, LinearConverter) for conversions 
# that can be represented as linar function y=kx+n. 
# 
# 
# (c) 2012 by Rastko Karadzic <rastkokaradzic@gmail.com>
#

class LinearUnit(object):
    """LinearUnit contains info about linear conversion units. It gets 3 variables: name,
    ratio and offset. Field name represents name of unit(e.g. 'mm','KB','F'),
    ratio represents x and offset represents n in formula y=kx+n.  Ratio and offset represents a relative value to a base unit.
    Every LinearConverter must contain a base unit whose ratio=1 and offset=0."""
    __name__ = 'LinearUnit'
    __version__='0.1'
    #Units variables
    name = None
    ratio = None
    offset = None
    
    def __init__(self, in_name,  in_ratio=1,  in_offset=0):
        # gets and store units info
        self.name = in_name
        self.ratio = in_ratio
        self.offset = in_offset
        
class LinearConverter(object):
    """This class represents linear converter. It contains units of some type (e.g. length or temperature),
        and convert method for converting."""
    __name__ = 'LinearConverter'
    __version__='0.1'
    #name of converter (e.g. temperature)
    name = None
    #dictionary that stores units like LinearUnit.name:LinearUnit
    units = None
    
    def __init__(self):
        self.units = {}
    
    def set_name(self,  in_name):
        self.name = in_name
    
    def append_unit(self,  in_unit):
        """Appends unit typeof LinearUnit into converter"""
        self.units[in_unit.name] = in_unit
    
    def available_units(self):
        """Returns list of available units for conversion in this converter"""
        return self.units.keys()
    
    def get_unit(self, in_name):
        """Gets unit typeof LinearUnit for given name"""
        if in_name in self.units:
            return self.units[in_name]
        else:
            print 'Unit ' + in_name + ' is not defined'

    def convert(self,  unit_from,  unit_to,  value):
        """Converts given value from unit_from to unit_to and returns result. unit_to and unit_from are typeof LinearUnit"""
        return ((value-unit_from.offset)/unit_from.ratio) * unit_to.ratio + unit_to.offset

