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
# It also implements class XMLConverters that is used like a provider for various 
# linear converters loaded from xml file.
# 
# (c) 2012 by Rastko Karadzic <rastkokaradzic@gmail.com>
#

import xml.dom.minidom as minidom
from LinearConverter import *


        
class XMLConverters():
    """Class XMLConverters serves all kind of linear converters that are initialized from xml file"""
    __name__ = 'XMLConverters'
    __version__='0.1'
    #path to xml file
    xml_path = 'converters.xml'
    #Structure of xml file
    #<xmlconverters> 
    #<converter name='temperature'> attribute name is name of converter
    #       <unit name='C'> attribute name  is  name of unit
    #              <ratio>1</ratio> 
    #              <offset>0</ratio> 
    #       </unit>
    #          ...
    # </converter>
    #          ...
    #</xmlconverters>
    
    
    #dom object
    dom = 0
    #dictionary that stores units like LinearConverter.name:LinearConverter
    converters = None
    
    def __init__(self):
        """Parses xml file and initializes all converters found in xml file"""
        self.dom = minidom.parse(self.xml_path)
        converter_nodes = self.dom.getElementsByTagName('converter')
        self.converters = {}
        for conv in converter_nodes:
            tmp = LinearConverter()
            unit_nodes = conv.getElementsByTagName('unit')
            in_name = conv.getAttribute('name')
            for unit in unit_nodes:
                u = LinearUnit(unit.getAttribute('name'),  float(unit.getElementsByTagName('ratio')[0].childNodes[0].nodeValue), float(unit.getElementsByTagName('offset')[0].childNodes[0].nodeValue))
                tmp.append_unit(u)
            self.converters[in_name] = tmp       
       
    def available_converters(self):
        """Returns list of names of available converters"""
        return self.converters.keys();

    def get_converter(self,  in_name):
        """For given name returns converter typeof LinearConverter"""
        if in_name in self.converters:
            return self.converters[in_name]
        else:
            print 'There is no defined converter in xml file with name' + in_name
            return None



