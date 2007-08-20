#!/usr/bin/env python

# This is an example of accessing the new ScreenletService. It can be used
# to access signals and methods within a Screenlet from other applications or
# other Screenlets.

# import services-module
import screenlets.services

# check if our needed service is running, exit if not
if not screenlets.services.service_is_running('MailCheck'):
	print "MailCheckScreenlet is not running."
	import sys
	sys.exit(1)

# get interface to the MailCheckScreenlet's service
mc =  screenlets.services.get_service_by_name('MailCheck')

# if interface was returned, 
if mc:
	try:
		# get id of first instance (we only want one here)
		instance_id = mc.get_first_instance()
		
		print "try getting/setting normal values"
		print mc.get(instance_id, 'x')
		mc.set(instance_id, 'x', 400)
		
		print "try getting/setting protected values"
		print mc.get(instance_id, 'pop3_account')
		mc.set(instance_id, 'pop3_account', ('user', 'pass'))
		
		# start mainloop (needed to receive events)
		import gobject
		mainloop = gobject.MainLoop()
		mainloop.run()

	except Exception, e:
		print "Error: " + str(e)

