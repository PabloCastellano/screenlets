from Convert import RatioConverter

class SizeConverter(RatioConverter):
	"""A converter which converts sizes between B, kB, MB and GB."""
	
	__name__ = 'SizeConverter'
	__title__ = 'B / kB / MB / GB'
	__author__ = 'Hendrik Kaju'
	__version__ = '0.2'

	num_fields = 4
	field_names = ['B', 'kB', 'MB', 'GB']
	weights = [1, 1024, 1024 * 1024, 1024 * 1024 * 1024]
