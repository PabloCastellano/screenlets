#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# (c) 2007 RYX (aka Rico Pfaus) <ryx@ryxperience.com>

# This is another example of accessing the new ScreenletService. It can be used
# to access signals and methods within a Screenlet from other applications or
# other Screenlets.

# import services-module
import screenlets.services

# check for Notes-service
if not screenlets.services.service_is_running('Notes'):
	print "Notes-service not found. Please launch the NotesScreenlet first."
else:
	# get general interface for the NotesScreenlet
	iface = screenlets.services.get_service_by_name('Notes')
	
	# if interface was returned, 
	if iface:
		try:
			# get list with instance ids
			ids = iface.list_instances()
			for id in ids:
				print id
			
			# easily get id of first instance
			#instance_id = ids[0]
			instance_id = iface.get_first_instance()

			# + SIGNALS: connecting to signals in a screenlet
			def instance_added (instance_id):
				print "Signal received: Instance '%s' added." % (instance_id)
			def instance_removed (instance_id):
				print "Signal received: Instance '%s' removed." % (instance_id)
			iface.connect_to_signal('instance_added', instance_added)
			iface.connect_to_signal('instance_removed', instance_removed)
			
			# + METHDODS: remote-calling of methods in a Screenlet
			# call testing functions
			iface.debug('Hello World!')
			iface.test()
			# add a new instance
			iface.add('myNotes')
			iface.add('myNotes2')
			iface.set('myNotes2', 'theme_name', 'girlie')
			iface.set('myNotes2', 'note_text', 'SCREENLETS!!!')
			iface.set('myNotes2', 'x', 500)
			iface.set('myNotes2', 'y', 700)
			
			# start mainloop (needed to receive events)
			import gobject
			mainloop = gobject.MainLoop()
			mainloop.run()

		except Exception, e:
			print "Error: " + str(e)

