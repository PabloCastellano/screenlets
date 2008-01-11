#!/usr/bin/env python




import screenlets
from screenlets.options import FloatOption, BoolOption, StringOption
from screenlets.options import create_option_from_node
import cairo
import pango
import subprocess
import re
import gobject


class DiskusageScreenlet(screenlets.Screenlet):
	"""A Diskusage Screenlet by Helder Fraga based on Jonathan Rauprich Disk screenlet."""
	
	# default meta-info for Screenlets
	__name__ = 'DiskusageScreenlet'
	__version__ = '0.3'
	__author__ = 'Helder Fraga'
	__desc__ = __doc__

	# internals
	__timeout = None
	p_layout = None	
	# settings
	update_interval = 20.0
	mount_point = '/'
	
	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=220, height=50,uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add default menu items
		self.add_default_menuitems()
		# add options
		self.add_options_group('Disk-Usage', 'Disk-Usage specific options')
		self.add_option(FloatOption('Disk-Usage', 'update_interval', 
			self.update_interval, 'Update-Interval', 
			'The interval for updating the Disk-Usage (in seconds) ...',
			min=1.0, max=60.0))
		self.add_option(StringOption('Disk-Usage', 'mount_point', 
			self.mount_point, 'Mount Point', 
			'Enter the Mountpoint for the Device you want to show'), 
			realtime=False)
		# init the timeout function
		self.update_interval = self.update_interval
		

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
				pass
	
	#function to get a list of dictionaries with device information
	#written by me
	def get_drive_info(self):
		proc = subprocess.Popen('df -h -a -P | grep ^/dev/ ', shell='true', stdout=subprocess.PIPE)
		sdevs = proc.stdout.read().rsplit('\n')
		sdevs.pop()
		for stdev in sdevs:
			sdev = re.findall("(\S*)\s*", stdev)
			dev = {
				'device': sdev[0],
				'size': sdev[1],
				'used': sdev[2],
				'free': sdev[3],
				'quota': sdev[4],
				'mount': sdev[5]
			}
			if dev['mount'] == self.mount_point:
				#print  sdev[3] + sdev[4] + sdev[5]
				return dev

		return None
	
	# timeout-function
	def update_graph(self):
		self.redraw_canvas()
		return True
	
	def on_draw(self, ctx):
		# get load
		info= self.get_drive_info()
		load= int(info['quota'].replace("%",""))
		print load
		if load > 99:
			load = 99
		elif load < 0:
			load=0
		# set size
		#ctx.scale(self.width/100.0, self.height/100.0)
		ctx.scale(self.scale, self.scale)
		ctx.set_operator(cairo.OPERATOR_OVER)
		# draw bg (if theme available)
		#ctx.set_operator(cairo.OPERATOR_OVER)
		if self.theme:
			self.theme['disk-bg.svg'].render_cairo(ctx)
		
		# draw cpu-graph

		# draw text
		
		
		ctx.save()

		ctx.translate(60, 8)

		if self.p_layout == None :
	
			self.p_layout = ctx.create_layout()
		else:
			
			ctx.update_layout(self.p_layout)
		p_fdesc = pango.FontDescription()
		#p_fdesc = pango.FontDescription("Free Sans 8")
		p_fdesc.set_family_static("Free Sans")
		p_fdesc.set_size(10*pango.SCALE)
		self.p_layout.set_font_description(p_fdesc)
		#p_layout.set_width((self.width) * pango.SCALE)
		if len(str(load))==1:
			load = "0" + str(load)
		self.p_layout.set_markup("<b>" + info['mount']  + "</b>\n <b>" +   info['free'] + "</b> free of <b>" + info['size'] + " - " + info['quota']+"</b>")
		ctx.set_source_rgba(1, 1, 1, 1)
		ctx.show_layout(self.p_layout)
		ctx.fill()
		ctx.restore()
		ctx.save()

		# draw glass (if theme available)
		if self.theme:
			#self.theme['cpumeter-graph-bg.svg'].render_cairo(ctx)
			w = (float(load) / 100.0) * 220.0
			#print "width: "+str(w)
			# get step
			#steps_height = 7
			#h = 40
			ctx.save()
			ctx.rectangle(0, 0, w, 50)
			#ctx.rectangle(20, 15+(70-h), 60, h)
			ctx.translate(25, 35)
			ctx.clip()
			#ctx.new_path()
			self.theme['disk-gauge.svg'].render_cairo(ctx)
			ctx.restore()
		if self.theme:
			try:
			
				self.theme['disk-glow.svg'].render_cairo(ctx)
			except Exception, ex:
				print 'no glass '			
			
			self.theme.render(ctx, 'drive2')
		
	def on_draw_shape(self,ctx):

		if self.theme:
			self.on_draw(ctx)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(DiskusageScreenlet)
