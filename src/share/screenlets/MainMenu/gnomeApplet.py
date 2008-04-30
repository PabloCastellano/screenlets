#!/usr/bin/env python

import os
import sys
import screenlets

if __name__ == '__main__':
	# check for running daemon
	proc = os.popen("""ps axo "%p,%a" | grep "MainMenuScreenlet.py" | grep -v grep|cut -d',' -f1""").read()
	procs = proc.split('\n')
	print  len(procs)
	if len(procs) > 1:
		print "already started"
		service = screenlets.services.get_service_by_name("MainMenu")
		if service and service != None:
			set = service.set
			for f in service.list_instances():
				visible = service.get(f,'is_visible')
				set(f,'is_visible', not visible)
	else:
		os.system('python -u /usr/share/screenlets/MainMenu/MainMenuScreenlet.py &')	
	sys.exit()
