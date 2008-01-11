from ConvertScreenlet import Converter

# An example of writing a (rather advanced) converter module. Please see also 
# the documentation of the converter class if you haven't done so.

# Every converter class MUST contain:
class BaseConverter(Converter):
	"""A converter which converts numbers between decimal, hexadecimal and octal 
	bases."""

	# __name__: the name of the class
	__name__ = 'BaseConverter'
	# __title__: a short description to be shown in the menu and Options dialog
	__title__ = 'Dec / Hex / Oct'
	# other meta-info - only for those who read the sources :-)
	# not currently shown anywhere, but this can change in near future
	__author__ = 'Vasek Potocek'
	__version__ = '0.1'
	
	# the number of fields and their captions
	num_fields = 3
	field_names = ['Dec', 'Hex', 'Oct']
	
	# filter_key function - see ConvertScreenlet.py for details
	def filter_key(self, key):
		if self.active_field == 0:
			return key in '0 1 2 3 4 5 6 7 8 9'.split()
		elif self.active_field == 1:
			return key in '0 1 2 3 4 5 6 7 8 9 A B C D E F a b c d e f'.split()
		elif self.active_field == 2:
			return key in '0 1 2 3 4 5 6 7'.split()

	# convert function - see ConvertScreenlet.py for details
	def convert(self):
		bases = [10, 16, 8]
		# read the current value in active field
		val = int(self.values[self.active_field], bases[self.active_field])
		# compute self.values in all fields
		self.values[0] = str(val)
		# strip off leading "0x" and make uppercase
		self.values[1] = hex(val)[2:].upper()
		self.values[2] = oct(val)[1:]
		if not self.values[2]: # this can happen in oct
			self.values[2] = '0'
		# strip off trailing 'L' if the self.value falls into long
		for i in range(3):
			if self.values[i][-1] == 'L':
				self.values[i] = self.values[i][:-1]
