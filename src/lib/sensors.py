# The screenlets.sensors module contains helper-functions to aid in
# creating CPU/RAM/*-meters 

import sys
import re

# calculate cpu-usage by values from /proc/stat
# (written by Bernd Wurst)
def get_cpu_load (old_cuse = [0]):
	# Let's try if we can calc system load.
	try:
		f = open("/proc/stat", "r")
		tmp = f.readlines(200)
		f.close()
	except:
		print "Failed to open /proc/stat"
		sys.exit(1)
	# 200 bytes should be enough because the information we 
	# need ist typically stored in the first line. Info about individual 
	# processors (not yet supported) is in the second (, ...?) line
	for line in tmp:
		if line[0:4] == "cpu ":
			reg = re.compile('[0-9]+')
			load_values = reg.findall(line)
			# extract values from /proc/stat
			cuse = int(load_values[0])
			csys = int(load_values[2])
			load = cuse + csys - old_cuse[0]
			#load = int(load / self.update_interval)
			old_cuse[0] = cuse + csys
	return load

