import sys
import os
sys.path.append(sys.path[0])

def importAPI(module):
	sys.path.append(os.path.dirname(__file__))
	mod = __import__(module)
	return mod
