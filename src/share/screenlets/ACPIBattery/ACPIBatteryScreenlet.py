#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  ACPIBatteryScreenlet (c) JMDK 2007 
#
# This screenlets is heavily based on the CPUMeterScreenlet by RYX
#
# INFO:
# - a simple ACPI Battery meter
# 
# This screenlets is heavily based on the CPUMeterScreenlet by RYX

import screenlets
from screenlets.options import IntOption, BoolOption, StringOption
import cairo
import pango
import sys
import gobject
from os import listdir,path

class ACPIBatteryScreenlet(screenlets.Screenlet):
	"""A simple ACPI Battery meter."""
	
	# default meta-info for Screenlets
	__name__ = 'ACPIBatteryScreenlet'
	__version__ = '0.2'
	__author__ = 'JMDK'
	__desc__ = 'A themeable ACPI Battery meter.'

	# internals
	__timeout = None
	__flag=0
	
	# settings
	update_interval = 5
	file_auto = True
	file_path='/proc/acpi/battery/BAT0/'
	state_file='state'
	info_file='info'
	alarm_threshold = 5
	show_time = True
	show_percent = True
	show_background = True
	
	# constructor
	def __init__(self, **keyword_args):
		#call super (and not show window yet)
		screenlets.Screenlet.__init__(self, uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add settings
		self.add_options_group('ACPI Battery', 'ACPI Battery specific options')
		self.add_option(IntOption('ACPI Battery', 'update_interval', 
			self.update_interval, 'Update interval', 
			'The interval for updating the ACPI Battery meter (in seconds) ...',
			min=1, max=60))
		self.add_option(IntOption('ACPI Battery', 'alarm_threshold', 
			self.alarm_threshold, 'Alarm threshold', 
			'The threshold triggering the low battery alarm (in precent) ...',
			min=1, max=100))
		self.add_option(BoolOption('ACPI Battery', 'file_auto', 
			self.file_auto, 'Guess battery file', 'Try to guess which battery to use ...'))
		self.add_option(StringOption('ACPI Battery', 'file_path', 
			self.file_path, 'Battery files path', 'Path to the battery files ...'),
			realtime=False)
		self.add_option(StringOption('ACPI Battery', 'state_file', 
			self.state_file, 'Battery state file', 'Name of the battery state file ...'),
			realtime=False)
		self.add_option(StringOption('ACPI Battery', 'info_file', 
			self.info_file, 'Battery info file', 'Name of the battery info file ...'),
			realtime=False)
		self.add_option(BoolOption('ACPI Battery', 'show_time', 
			self.show_time, 'Display time', 'Show remaining time on ACPI battery meter ...'))
		self.add_option(BoolOption('ACPI Battery', 'show_percent', 
			self.show_percent, 'Display percentage', 'Show percentage on ACPI battery meter ...'))
		self.add_option(BoolOption('Screenlet', 'show_background', 
			self.show_background, 'Show background', 'Set this Screenlet to show/hide its background ...'))
		# init the timeout function
		self.update_interval = self.update_interval
		self.file_auto = self.file_auto
		self.file_path = self.file_path
	
	# attribute-"setter", handles setting of attributes
	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# check for this Screenlet's attributes, we are interested in:
		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(int(value * 1000), self.update_graph)
			else:
				# TODO: raise exception!!!
				self.__dict__['update_interval'] = 1
		elif name == "file_auto":
			if value:
				dirs=listdir('/proc/acpi/battery/');
				dirs.sort();
				try:
					self.__dict__['file_path']='/proc/acpi/battery/'+dirs[0]+'/'
				except IndexError:
					pass
				
		elif name == "file_path":
			if self.__flag>0:
				self.__dict__['file_auto']=0
			self.__flag+=1
	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()			
	def getValue(self):
		charge_status='NA'
		ispresent='no'
		if path.exists(self.file_path+self.state_file):
			file=open(self.file_path+self.state_file,'r')
			while 1:
				line = file.readline()
				if ((not line)|(line.find('present') > -1)): break
			if line:
				linelist=line.rstrip('\n').split(' ')
				i=1
				while (i<len(linelist)):
					if ((linelist[i]=='yes')|(linelist[i]=='no')):
						ispresent=linelist[i]
						break
					else: i+=1
			if (ispresent=='yes'):
				while 1:
					line = file.readline()
					if ((not line)|(line.find('charging state') > -1)): break
				if line:
					linelist=line.rstrip('\n').split(' ')
					i=1
					while (i<len(linelist)):
						if ((linelist[i]=='charged')|(linelist[i]=='charging')|(linelist[i]=='discharging')):
							charge_status=linelist[i]
							break
						else: i+=1
				while 1:
					line = file.readline()
					if ((not line)|(line.find('present rate') > -1)): break
				linelist=line.split(' ')
				i=0
				while (i<len(linelist)):
					if (linelist[i].isdigit()):
						present_rate=linelist[i]
						break
					else: i+=1
				while 1:
					line = file.readline()
					if ((not line)|(line.find('remaining') > -1)): break
				linelist=line.split(' ')
				i=0
				while (i<len(linelist)):
					if (linelist[i].isdigit()):
						remaining=linelist[i]
						break
					else: i+=1
			else:
				present_rate=1
				remaining=1				
			file.close()
		else:
			present_rate=1
			remaining=1
		if (ispresent=='yes'):
			if path.exists(self.file_path+self.state_file):
				file=open(self.file_path+self.info_file,'r')
				while 1:
					line = file.readline()
					if ((not line)|(line.find('last full') > -1)): break
				linelist=line.split(' ')
				i=0
				while (i<len(linelist)):
					if (linelist[i].isdigit()):
						last_full=linelist[i]
						break
					else: i+=1
				file.close()
			else:
				last_full=1
		else:
			last_full=1
		if int(present_rate)==0: present_rate='1000';
		return (charge_status,present_rate,remaining,last_full)
		
	# timeout-function
	def update_graph(self):
		self.redraw_canvas()
		return True
	
	def on_draw(self, ctx):
		(charge_status,present_rate,remaining,last_full)=self.getValue()
		percents="%3i" % ((100*int(remaining)) / int(last_full))
		# set size
		ctx.scale(self.scale, self.scale)
		# draw bg (if theme available)
		ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme and self.show_background:
			self.theme['acpibattery-bg.svg'].render_cairo(ctx)
		self.theme['acpibattery-battery.svg'].render_cairo(ctx)
		if charge_status=='charged': 
			time_value='  Full'
		elif charge_status=='discharging':
			t=(60*int(remaining))/int(present_rate)
			time_value="%02i:%02i" % (int(t/60),int(t%60))
			if int(percents)<=self.alarm_threshold:
				self.theme['acpibattery-alarm.svg'].render_cairo(ctx)				
			else:
				self.theme['acpibattery-using.svg'].render_cairo(ctx)
		elif charge_status=='charging':
			t=(60*(int(last_full)-int(remaining)))/int(present_rate)
			time_value="%02i:%02i" % (int(t/60),int(t%60))
			self.theme['acpibattery-charging.svg'].render_cairo(ctx)
		else:
			time_value='   NA'
			percents='   0'
			self.theme['acpibattery-alarm.svg'].render_cairo(ctx)				
		if charge_status=='NA':
			# draw message
			ctx.save()
			#ctx.set_operator(cairo.OPERATOR_OVER)
			p_layout = ctx.create_layout()
			ctx.translate(37,5)
			p_fdesc = pango.FontDescription("Free Sans 14")
			#p_fdesc.set_family_static("Free Sans")
			#p_fdesc.set_size(25 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup('   No')
			ctx.set_source_rgba(1, 0, 0, 1)
			ctx.show_layout(p_layout)
			ctx.fill()
			ctx.restore()							
			ctx.save()
			#ctx.set_operator(cairo.OPERATOR_OVER)
			p_layout = ctx.create_layout()
			ctx.translate(37,26)
			p_fdesc = pango.FontDescription("Free Sans 12")
			#p_fdesc.set_family_static("Free Sans")
			#p_fdesc.set_size(25 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup(' battery')
			ctx.set_source_rgba(1, 0, 0, 1)
			ctx.show_layout(p_layout)
			ctx.fill()
			ctx.restore()									
		elif self.show_time and self.show_percent:
			# draw percent and time
			ctx.save()
			#ctx.set_operator(cairo.OPERATOR_OVER)
			p_layout = ctx.create_layout()
			ctx.translate(37,5)
			p_fdesc = pango.FontDescription("Free Sans 16")
			#p_fdesc.set_family_static("Free Sans")
			#p_fdesc.set_size(25 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup(percents+"%")
			if int(percents)<=self.alarm_threshold:
				ctx.set_source_rgba(1, 0, 0, 1)
			else:
				ctx.set_source_rgba(1, 1, 1, 1)
			ctx.show_layout(p_layout)
			ctx.fill()
			ctx.restore()							
			ctx.save()
			#ctx.set_operator(cairo.OPERATOR_OVER)
			p_layout = ctx.create_layout()
			ctx.translate(37,26)
			p_fdesc = pango.FontDescription("Free Sans 14")
			#p_fdesc.set_family_static("Free Sans")
			#p_fdesc.set_size(25 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup(time_value)
			if int(percents)<=self.alarm_threshold:
				ctx.set_source_rgba(1, 0, 0, 1)
			else:
				ctx.set_source_rgba(1, 1, 1, 1)
			ctx.show_layout(p_layout)
			ctx.fill()
			ctx.restore()							
		elif self.show_time:
			# draw time
			ctx.save()
			#ctx.set_operator(cairo.OPERATOR_OVER)
			p_layout = ctx.create_layout()
			ctx.translate(37,13)
			p_fdesc = pango.FontDescription("Free Sans 16")
			#p_fdesc.set_family_static("Free Sans")
			#p_fdesc.set_size(25 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup(time_value)
			if int(percents)<=self.alarm_threshold:
				ctx.set_source_rgba(1, 0, 0, 1)
			else:
				ctx.set_source_rgba(1, 1, 1, 1)
			ctx.show_layout(p_layout)
			ctx.fill()
			ctx.restore()				
		else:
			# draw percent
			ctx.save()
			#ctx.set_operator(cairo.OPERATOR_OVER)
			p_layout = ctx.create_layout()
			ctx.translate(37,13)
			p_fdesc = pango.FontDescription("Free Sans 16")
			#p_fdesc.set_family_static("Free Sans")
			#p_fdesc.set_size(25 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup(percents+"%")
			if int(percents)<=self.alarm_threshold:
				ctx.set_source_rgba(1, 0, 0, 1)
			else:
				ctx.set_source_rgba(1, 1, 1, 1)
			ctx.show_layout(p_layout)
			ctx.fill()
			ctx.restore()
		# draw glass (if theme available)
		if self.theme:
			self.theme['acpibattery-glass.svg'].render_cairo(ctx)
		
	def on_draw_shape(self,ctx):
		if self.theme:
			# set size rel to width/height
			#ctx.scale(self.width/100.0, self.height/100.0)
			ctx.scale(self.scale, self.scale)
			self.theme['acpibattery-bg.svg'].render_cairo(ctx)

	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(ACPIBatteryScreenlet)
