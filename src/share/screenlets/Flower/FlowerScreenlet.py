#!/usr/bin/env python

#  FlowerScreenlet (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - a themeable growing virtual plant
# - the theme contains of: 8 different states for the complete evolution of the 
#   flower (where 1-4 are pre-blossom states and 5-8 should evolve a blossom), 
#   2 states for "wet" (1 for state1-4, 1 for state5-8), 2 states for "dry" 
#	(the same as "wet"), a pot, a "dead"-state
# - this plant needs really careful watering. It may not become wet or dry
#   for too long (how long depends on the age of the flower), otherwise it 
#   will die
# 
# TODO:
# - maybe add a water-meter? would make it a bit easier ...
# - make day_length-option editable
# - ?make a randomly varying animation between the last two states?
# - maybe make the flower interact with the WeatherScreenlet's data? would
#   require a service-class for the Weather
# - ...

import screenlets
from screenlets.options import IntOption

import cairo
import gobject


# the screenlet's class
class FlowerScreenlet (screenlets.Screenlet):
	"""A Screenlet that displays a growing plant. This plant needs really 
	careful watering. It may not become wet or dry for too long (how long 
	depends on the age of the flower), otherwise it will die. You always 
	need to give a new plant water to make it start growing at all, if not
	it may silently die before you see anything. Don't water young plants
	more than once a day. (NOTE: This is still experimental)"""
	
	# --------------------------------------------------------------------------
	# meta-info, options
	# --------------------------------------------------------------------------
	
	__name__		= 'FlowerScreenlet'
	__version__		= '0.3'
	__author__		= 'RYX (Rico Pfaus)'
	__desc__		= __doc__
	
	# internal attributes
	__dead 	= False
	__wet	= False
	__dry	= False
	__todays_water	= 0
	
	# editable options
	day_length		= 24 * 3600	# length of one day (in seconds) - 24h default
	
	# hidden options
	state 			= 0		# the current state of the flower (0-8)
	avail_water		= 0		# the amount of water the plant has available
	days_wet		= 0		# "days" the flower has been too wet
	days_dry		= 0		# "days" the flower has been too dry
	age				= 0		# age of the flower in "days"
	
	# --------------------------------------------------------------------------
	# constructor and internals
	# --------------------------------------------------------------------------
	
	def __init__ (self, **keyword_args):
		# call super (and set FlowerService as service for this Screenlet)
		screenlets.Screenlet.__init__(self, width=100, height=100,
			uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add menuitems
		self.add_menuitem('give_water', 'Give water')
		#self.add_menuitem('give_water', 'Give water')
		self.add_default_menuitems()
		# add timeout function for checking status after a certain interval
		self.__timeout = gobject.timeout_add(self.day_length * 1000, 
			self.__check_status)
		# add option group to properties-dialog
		grp = self.create_option_group('Flower', 'Flower-related settings.')
		# make 'day_length' an editable option
		"""self.add_option(IntOption('Flower', 'day_length', self.day_length, 
			'Day length', 'Length of one day (in minutes) ...', min=0, max=6 )) """
		# add hidden options
		grp.add_option(IntOption('age', self.age, '',
			'', hidden=True)) 
		grp.add_option(IntOption('state', self.state, '',
			'', hidden=True)) 
		grp.add_option(IntOption('avail_water', self.avail_water, 
			'', '', hidden=True))
		grp.add_option(IntOption('days_wet', self.days_wet, 
			'', '', hidden=True))
		grp.add_option(IntOption('days_dry', self.days_dry, 
			'', '', hidden=True))
		# cause initial water-check
		#self.__check_water()
		
	def __setattr__ (self, name, value):
		screenlets.Screenlet.__setattr__(self, name, value)
		if name=="state":
			self.redraw_canvas()
			self.update_shape()
			
	# --------------------------------------------------------------------------
	# custom functions for Flower
	# --------------------------------------------------------------------------
	
	def __check_status (self):
		"""Timeout function, called in certain intervals to check the status
		of the plant and if there are any needs or status changes."""
		print "Status check"
		# check status of water
		if self.__check_water():
			# TODO: add random-factor which can delay growing by 1-4 days
			print "Water check passed"
			# calculate new state
			if self.state < 6:
				self.state += 1 
		# get one day older
		self.age += 1
		# continue
		return True
	
	def __check_water (self):
		"""Check the water status and set the appropriate flags."""
		# chekc amount of water we got today
		print "water today %i" % int(self.state /4)
		if self.__todays_water > int(self.state /4) + 1:
			# did we get too much water at once? we're dead
			self.__die()
		else:
			self.__todays_water = 0
		# we need initial watering (else we're dead)
		if self.age == 1 and self.avail_water == 0:
			self.__die()
		# check available water
		elif self.avail_water > 2:
			print "Flower is too wet."
			# too wet? check since how many days it is like that
			# (plants in the first state die when they get too wet, plants
			# wetter than their state die, too)
			if self.days_wet > self.state or self.state == 1 or \
				self.avail_water > self.state:
				# longer wet than its state is high? we're dead ...
				self.__die()
			else:
				# there's still hope, but we shouldn't water it for a while
				self.days_wet += 1
				self.avail_water -= 1
				self.__wet = True	# indicates to draw "wet"-state
			# redraw/reshape
			self.redraw_canvas()
			self.update_shape()
		elif self.avail_water < 0:
			print "Flower is too dry."
			# too dry? check days
			# (plants in the first state die when they get dry, plants
			# dryer than their state die, too)
			if self.days_dry > self.state or self.state == 1 or \
				self.avail_water < -self.state:
				self.__die()
			else:
				# there's still hope, but we need water soon
				self.days_dry += 1
				self.avail_water -= 1
				self.__dry = True	# indicates to draw "wet"-state
			# redraw/reshape
			self.redraw_canvas()
			self.update_shape()
		else:
			# everything ok? decrease days_wet/dry-counter if above 0
			if self.days_wet > 0:
				self.days_wet -= 1
			else:
				self.__wet = False
			if self.days_dry > 0:
				self.days_dry -= 1
			else:
				self.__dry = False
			# consume some water (TODO: variation: small plants use less water)
			self.avail_water -= 1
			if self.avail_water == 0:
				self.days_wet = 0
			# return True: water check is ok, plant can grow
			return True
		return False
	
	def __die (self):
		"""Causes the flower to die."""
		print "Flower died."
		#self.state = 0			# reset state
		self.__dead = True		# indicate to draw "dead"-state
		self.redraw_canvas()
		self.update_shape()
				
	# --------------------------------------------------------------------------
	# Screenlet handlers
	# --------------------------------------------------------------------------
	
	def on_menuitem_select (self, id):
		if id=='give_water':
			if not self.__dead:
				self.avail_water += 1
				self.__todays_water += 1
		print id
	
	def on_draw (self, ctx):
		ctx.set_operator(cairo.OPERATOR_OVER)
		ctx.scale(self.scale, self.scale)
		if self.theme:
			#self.theme['flower-pot.svg'].render_cairo(ctx)
			self.theme.render(ctx, 'flower-pot')
			if self.__dead:
				# render dead state (only if age>1)
				if self.state > 0:
					#self.theme['flower-dead.svg'].render_cairo(ctx)
					self.theme.render(ctx, 'flower-dead')
			elif self.__dry:
				# render dry state, if dry
				if self.state > 4:
					#self.theme['flower-dry2.svg'].render_cairo(ctx)
					self.theme.render(ctx, 'flower-dry2')
				else:
					#self.theme['flower-dry1.svg'].render_cairo(ctx)
					print"TODO: dry1"
			else:
				# check state
				if self.state > 0:
					sf = 'flower-state' + str(self.state)# + '.svg'
					#self.theme[sf].render_cairo(ctx)
					self.theme.render(ctx, sf)
	
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)

	def on_quit (self):
		# remove timeout function when instance is deleted
		gobject.source_remove(self.__timeout)
	
	
# If the program is run directly or passed as an argument to the python
# interpreter then launch as new application
if __name__ == "__main__":
	# create session object here, the rest is done automagically
	import screenlets.session
	screenlets.session.create_session(FlowerScreenlet)
	# OR:
	#session = screenlets.session.ScreenletSession(FlowerScreenlet)
	#session.start()
	
	# old way:
	#sl = screenlets.create_new_instance('FlowerScreenlet')	
	#sl.main()
	# OR: screenlets.create_new_instance('FlowerScreenlet').main()

