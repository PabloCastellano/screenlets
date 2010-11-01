import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst

class gstreamer(object):

	def __init__(self):
		self.player = gst.element_factory_make("playbin", "player")
		fakesink = gst.element_factory_make('fakesink', "my-fakesink")
		self.player.set_property("video-sink", fakesink)
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect('message', self.on_message)

		self.player = gst.Pipeline("player")
		source = gst.element_factory_make("filesrc", "file-source")
		self.player.add(source)
		demuxer = gst.element_factory_make("oggdemux", "demuxer")
		self.player.add(demuxer)
		demuxer.connect("pad-added", self.demuxer_callback)
		self.audio_decoder = gst.element_factory_make("vorbisdec", "vorbis-decoder")
		self.player.add(self.audio_decoder)
		audioconv = gst.element_factory_make("audioconvert", "converter")
		self.player.add(audioconv)
		audiosink = gst.element_factory_make("autoaudiosink", "audio-output")
		self.player.add(audiosink)

		gst.element_link_many(source, demuxer)
		gst.element_link_many(self.audio_decoder, audioconv, audiosink)

		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.on_message)


	def demuxer_callback(self, demuxer, pad):
		adec_pad = self.audio_decoder.get_pad("sink")
		pad.link(adec_pad)


	def start(self):
		try:			
			self.player.set_property('uri', ta)
			self.player.set_state(gst.STATE_PLAYING)
		except Exception, ex:
			print 'unable to connect'

	def stop(self):
			
			self.player.set_state(gst.STATE_NULL)

	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)

		elif t == gst.MESSAGE_ERROR:
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.player.set_state(gst.STATE_NULL)

	def rewind_callback(self, w):
		pos_int = self.player.query_position(self.time_format, None)[0]
		seek_ns = pos_int - (10 * 1000000000)
		self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)
		
	def forward_callback(self, w):
		pos_int = self.player.query_position(self.time_format, None)[0]
		seek_ns = pos_int + (10 * 1000000000)
		self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)
	
	def convert_ns(self, time_int):
		time_int = time_int / 1000000000
		time_str = ""
		if time_int >= 3600:
			_hours = time_int / 3600
			time_int = time_int - (_hours * 3600)
			time_str = str(_hours) + ":"
		if time_int >= 600:
			_mins = time_int / 60
			time_int = time_int - (_mins * 60)
			time_str = time_str + str(_mins) + ":"
		elif time_int >= 60:
			_mins = time_int / 60
			time_int = time_int - (_mins * 60)
			time_str = time_str + "0" + str(_mins) + ":"
		else:
			time_str = time_str + "00:"
		if time_int > 9:
			time_str = time_str + str(time_int)
		else:
			time_str = time_str + "0" + str(time_int)
			
		return time_str


