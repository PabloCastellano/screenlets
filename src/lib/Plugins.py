import sys
import os
sys.path.append(sys.path[0])

def importAPI(module):
	"""Imports modules from plugins folder"""
	try:
		sys.path.append(os.path.dirname(__file__) + '/plugins')
		mod = __import__(module)
		return mod
	except: return None
