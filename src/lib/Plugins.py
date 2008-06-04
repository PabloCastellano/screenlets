import sys
import os
sys.path.append(sys.path[0])

PATH = os.path.dirname(__file__) + '/plugins'

def importAPI(module):
	"""Imports modules from plugins folder"""
	try:
		sys.path.append(PATH)
		mod = __import__(module)
		return mod
	except: return None
