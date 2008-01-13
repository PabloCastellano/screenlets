#!/usr/bin/env python

#  WirelessScreenlet (c) Patrik Kullman 2007 <patrik@yes.nu>
#
# INFO:
# - Display wireless link quality and ESSID
#
# RGBA Colors:
# 5/5: 00bf36fd
# 4/5: a9f000fd
# 3/5: ffff36fd
# 2/5: dd9800fd
# 1/5: e44321fd
# 
# 
# TODO:
# - fix proper scaling
# - make nice icons for default theme
# - make it possible to view extended information through popup/hover
#
# CHANGELOG:
# v0.2
# - doesn't crash if interface isn't associated
# - new (slightly better) icons
# - scaling works

import screenlets
from screenlets.options import StringOption
import cairo
import gtk
import pango
from os import popen
import gobject

class WirelessScreenlet(screenlets.Screenlet):
	
	# default meta-info for Screenlets
	__name__ = 'WirelessScreenlet'
	__version__ = '0.2'
	__author__ = 'Patrik Kullman'
	__desc__ = 'Display wireles link quality and ESSID'

	# internals
	__timeout = None
	__icon = 'link-0'
	__stats = {"essid": "Not updated", "percentage": 0}
	__not_connected_stats = {"essid": "Not connected", "percentage": 0}
	__update_interval = 3 # every 3 seconds

	# editable options and defaults
	interface = ''
		
	# constructor
	def __init__(self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, width=200, height=100, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add option groups
		self.__update_interval = self.__update_interval
		self.add_options_group('Wireless', 'Wireless settings')
		self.add_option(StringOption('Wireless',
			'interface', 						# attribute-name
			self.interface,						# default-value
			'Wireless interface', 						# widget-label
			'The wireless interface to use for monitoring', choices=self.get_wireless_interfaces()	# description
			))
		if self.interface == '':
			interfaces = self.get_wireless_interfaces()
			if len(interfaces) > 0:
				self.interface = interfaces[0]

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()

	def __setattr__(self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# redraw the canvas when server-info is changed since a server host/ip addition/removal will change the size of the screenlet
		if name == "_WirelessScreenlet__update_interval":
			if value > 0:
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(value * 1000, self.update)
			else:
				# TODO: raise exception!!!
				pass
		if name == "interface":
			self.update_stats()

	def update(self):
		gobject.idle_add(self.update_stats)
		return True

	def update_stats(self):
		self.__stats = self.get_wireless_stats(self.interface)
		self.__icon = self.get_icon()
		self.redraw_canvas()

	def on_draw(self, ctx):
		# if theme is loaded
		if self.theme:
			# find out how many servers that are configured and force a update_shape() when they're changed from the last draw.
			# apparently the settings doesn't get loaded until the widget is first displayed, and no update_shape is performed at
			# that point
			# make sure that the background covers all the icons
			ctx.save()
			ctx.scale(self.scale, self.scale)
			ctx.translate(0, 0)
			self.theme.render(ctx, 'background')
			ctx.restore()

			ctx.save()
			ctx.scale(self.scale, self.scale)
			ctx.translate(115, 10)
			self.theme.render(ctx, self.__icon)
			ctx.restore()

			ctx.save()
			ctx.scale(self.scale, self.scale)
			self.draw_text(ctx, '<b>' + self.__stats['essid'] + '</b>', 10, 10, 12)
			self.draw_text(ctx, str(self.__stats['percentage']) + '%', 20, 50, 20)
			ctx.restore()

			ctx.save()
			ctx.scale(self.scale, self.scale)
			ctx.translate(0, 0)
			self.theme.render(ctx, 'glass')
			ctx.restore()

	def on_draw_shape(self, ctx):
		if self.theme:
			self.on_draw(ctx)

	def draw_text(self, ctx, value, x, y, size):
		# stolen from CalcScreenlet ;)
		ctx.save()
		ctx.translate(x, y)
		p_layout = ctx.create_layout()
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Sans")
		p_fdesc.set_size(size * pango.SCALE)
		p_layout.set_font_description(p_fdesc)
		p_layout.set_width(180 * pango.SCALE)
		p_layout.set_alignment(pango.ALIGN_LEFT)
		p_layout.set_markup(value)
		ctx.set_source_rgba(1, 1, 1, 0.8)
		ctx.show_layout(p_layout)
		p_layout.set_alignment(pango.ALIGN_CENTER)
		ctx.restore()

	def get_wireless_interfaces(self):
		interfaces = []
		wfd = open("/proc/net/wireless")
		procinfo = wfd.read(1024)
		wfd.close()
		for line in procinfo.splitlines():
			colon = line.find(":")
			if colon > 0:
				interfaces.append(line[:colon].strip())
		return interfaces

	def get_wireless_stats(self, interface):
		stats = {}
		iwcfd = popen("iwconfig " + interface)
		iwconfig = iwcfd.read(1024)
		iwcfd.close()
		essid = iwconfig[iwconfig.find('ESSID:"')+7:]
		stats['essid'] = essid[:essid.find('"')]
		if stats['essid'].strip()[:stats['essid'].strip().find("  ")] == "unassociated":
			return self.__not_connected_stats
		else:
			bitrate = iwconfig[iwconfig.find("Bit Rate:")+9:]
			stats['bitrate'] = bitrate[:bitrate.find(" ")]
			quality = iwconfig[iwconfig.find("Link Quality=")+13:]
			quality = quality[:quality.find(" ")]
			if quality.find("/") > 0:
				stats['quality'], stats['quality_max'] = quality.split("/")
			else:
				stats['quality'] = quality
			stats['percentage'] = self.get_percentage(int(stats['quality']), int(stats['quality_max']))
			signal = iwconfig[iwconfig.find("Signal level=")+13:]
			stats['signal'] = signal[:signal.find("  ")]
			noise = iwconfig[iwconfig.find("Noise level=")+12:]
			stats['noise'] = noise[:noise.find('\n')]
			return stats

	def get_percentage(self, quality, quality_max):
		# use log(quality) / log(quality_max) ?
		return int(float(quality) / quality_max * 100)

	def get_icon(self):
		if self.__stats['percentage'] < 1:
			return 'link-0'
		elif self.__stats['percentage'] < 21:
			return 'link-20'
		elif self.__stats['percentage'] < 41:
			return 'link-40'
		elif self.__stats['percentage'] < 61:
			return 'link-60'
		elif self.__stats['percentage'] < 81:
			return 'link-80'
		else:
			return 'link-100'
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(WirelessScreenlet)

