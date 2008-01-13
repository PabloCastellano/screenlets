#!/usr/bin/env python

# VolumeControlScreenlet (c) 2007 DeathCarrot <jsk105@ecs.soton.ac.uk>
# 
# A basic screenlet for controlling audio volume.
# Use the mousewheel to raise and lower the volume or middle click to toggle mute.
#
# TODO:
#   Add checks to make sure cmdValue actually returns a number
#   .. or think of a more versatile way of getting the volume data
#   Move size/offset information into theme-specific config files
#   Make some more themes


import screenlets
from screenlets.options import StringOption, IntOption
import pygtk
pygtk.require('2.0')
import gtk
import cairo
import commands
import os

class VolumeControlScreenlet(screenlets.Screenlet):
    """A basic screenlet for controlling audio volume"""

    # default meta-info for Screenlets
    __name__ = 'VolumeControlScreenlet'
    __version__ = '0.1.7'
    __author__ = 'DeathCarrot'
    __desc__ = 'A basic screenlet for controlling audio volume. '+\
	       'Use the mousewheel to raise and lower the volume, '+\
	       'middle click to toggle mute or '+\
	       'click on the bar to set the volume level.'

    # internal
    __currentVol = 1
    __maxVol = 1
    __cmdSet = 'amixer sset %s %s'
    __cmdGet = 'amixer sget %s | '+\
	    'awk \'$0~/Front Left:/{gsub(/[%%\[\]]/,"");print $5}\''

    # per theme options
    bar_x = 59
    bar_y = 7
    bar_width = 12
    bar_height = 75

    # editable options
    control = "Master"
    step = 2
    mixer = "xfce4-mixer"

    # constructor
    def __init__(self, **keyword_args):
	# call super
	screenlets.Screenlet.__init__(self, width=100, height=100, 
		**keyword_args)
	# connect mousewheel scroll event
	self.window.connect("scroll-event", self.on_scroll)
	# set theme
	self.theme_name = "cone"
	# add menuitem for mixer
	self.add_menuitem("mixer","Launch Mixer",self.run_mixer)
	# add default menu items

	# add option group
	self.add_options_group('Device',
	    'Settings for specifying which device and control to use')
	ctlList = commands.getoutput(
	    "amixer scontrols | awk \"{gsub(/'/,\\\" \\\");print \\$4}\"").split()
	self.add_option(StringOption('Device',	    # group name
	    'control',				    # attribute-name
	    self.control,			    # default-value
	    'Control',				    # widget-label
	    'Which control should be utilised for your device', # description
	    ctlList),				    # list contents
	    self.on_control_update		    # callback
	    )
	self.add_option(IntOption('Device',
	    'step',
	    self.step,
	    'Scroll Step',
	    'How much the volume changes on each mouse wheel click',
	    0,	# min
	    100	# max
	    ))
	self.add_option(StringOption('Device',
	    'mixer',
	    self.mixer,
	    'Mixer Command',
	    'The command to be run when mixer is launched'
	    ))
	self.on_control_update(self.control, self.control)

    def on_control_update(self, option, option2):
	# find the maximum volume and update
	self.__maxVol = int(commands.getoutput(
	    "amixer sget %s | awk '/^  Limits/{print $5}'" % (self.control)))
	print "Max vol: " + str(self.__maxVol)
	self.updateBar()

    def on_init(self):
	# add default menu items
	self.add_default_menuitems()

    def on_mouse_down(self, event):
	if event.button == 2:
	    # mute/unmute on middle click
	    commands.getoutput(self.__cmdSet % (self.control, "0"))
	    self.updateBar()
	elif event.button == 1 and \
		event.x > self.scale*self.bar_x and \
		event.x < self.scale*(self.bar_x+self.bar_width) and \
		event.y > self.scale*self.bar_y and \
		event.y < self.scale*(self.bar_y+self.bar_height):
	    self.__currentVol = (self.bar_height*self.scale +
		    self.bar_y*self.scale - event.y)/(self.bar_height*self.scale)
	    if self.__currentVol <= 0:
		# ctx.scale fails if a parameter is 0
		self.__currentVol = 0.001
	    elif self.__currentVol > 1:
		self.__currentVol = 1
	    commands.getoutput(self.__cmdSet % (self.control,
		str(self.__currentVol*self.__maxVol)))
	    self.redraw_canvas()
	return False

    # catch scroll events
    def on_scroll(self, widget, event):
	if event.direction == gtk.gdk.SCROLL_UP:
	    # volume up on scroll up
	    commands.getoutput(self.__cmdSet %
		    (self.control, str(self.step)+"+"))
	    self.updateBar()
	elif event.direction == gtk.gdk.SCROLL_DOWN:
	    # volume down on scroll up
	    commands.getoutput(self.__cmdSet %
		    (self.control, str(self.step)+"-"))
	    self.updateBar()
	return False

    def run_mixer(self, option, option2):
	os.spawnlp(os.P_NOWAIT,self.mixer)

    # read volume value and redraw bar
    def updateBar(self):
	# get current volume value
	self.__currentVol = float(commands.getoutput(
		self.__cmdGet % (self.control)))/100
	if self.__currentVol <= 0:
	    # ctx.scale fails if a parameter is 0
	    self.__currentVol = 0.001
	elif self.__currentVol > 1:
	    self.__currentVol = 1
	self.redraw_canvas()

    def on_draw(self, ctx):
	# if theme is loaded
	if self.theme:
	    ctx.scale(self.scale, self.scale)
	    # draw main part
	    self.theme['vol_base.svg'].render_cairo(ctx)
	    # save old state and mask bar
	    ctx.save()
	    ctx.rectangle(self.bar_x,
			  (self.bar_height*(1-self.__currentVol))+self.bar_y,
			  self.bar_width,
			  self.bar_height)
	    ctx.clip()
	    # draw bar
	    self.theme['vol_bar.svg'].render_cairo(ctx)
	    ctx.restore()

    def on_draw_shape(self, ctx):
	self.on_draw(ctx)

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
    import screenlets.session
    screenlets.session.create_session(VolumeControlScreenlet)

