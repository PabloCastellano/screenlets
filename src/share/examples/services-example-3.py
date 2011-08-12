#!/usr/bin/env python

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

# (c) 2007 RYX (aka Rico Pfaus) <ryx@ryxperience.com>

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

