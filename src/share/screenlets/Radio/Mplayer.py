import sys, os, fcntl, gobject, time, re

STATUS_TIMEOUT = 1000

#
#  Provides simple piped I/O to an mplayer process.
#
class Mplayer:
	
	pymp, mplayerIn, mplayerOut = None, None, None
	inputHandler, eofHandler, statusQuery = 0, 0, 0
	paused = False
	streamTitle = ""
	streamTitleChangeListeners = []
	
	#
	#  Initializes this Mplayer with the specified Pymp.
	#
	def __init__(self, pymp):
		self.pymp = pymp
		
	#
	#   Plays the specified target.
	#
	def play(self, target):
		
		mpc = "mplayer -slave -quiet " + target + " 2>/dev/null"
		
		self.mplayerIn, self.mplayerOut = os.popen2(mpc)  #open pipe
		fcntl.fcntl(self.mplayerOut, fcntl.F_SETFL, os.O_NONBLOCK)

		self.startInputHandler()
		self.startEofHandler()
		self.startStatusQuery()
		
	#
	#  Issues command to mplayer.
	#
	def cmd(self, command):
		
		if not self.mplayerIn:
			return
		
		try:
			self.mplayerIn.write(command + "\n")
			self.mplayerIn.flush()  #flush pipe
		except StandardError:
			return
		
	#
	#  Toggles pausing of the current mplayer job and status query.
	#
	def pause(self):
		if not self.mplayerIn:
			return
			
		if self.paused:  #unpause
			self.startStatusQuery()
			self.paused = False
			
		else:  #pause
			self.stopStatusQuery()
			self.paused = True
			
		self.cmd("pause")
		
	#
	#  Seeks the amount using the specified mode.  See mplayer docs.
	#
	def seek(self, amount, mode=0):
		pass
	
	#
	#  Cleanly closes any IPC resources to mplayer.
	#
	def close(self):
		self.stopStatusQuery()  #cancel query
		self.stopEofHandler()  #cancel eof monitor
		self.stopInputHandler() #cancel input monitor
				
		if self.paused:  #untoggle pause to cleanly quit
			self.pause()
		
		self.cmd("quit")  #ask mplayer to quit
		
		try:			
			self.mplayerIn.close()	 #close pipes
			self.mplayerOut.close()
		except StandardError:
			pass
			
		self.mplayerIn, self.mplayerOut = None, None
		#self.pymp.control.setProgress(-1)  #reset bar
		
	#
	#  Triggered when mplayer's stdout reaches EOF.
	#
	def handleEof(self, source, condition):
		
		self.stopStatusQuery()  #cancel query
		
		self.mplayerIn, self.mplayerOut = None, None
		
	#	if self.pymp.playlist.continuous:  #play next target
	#		self.pymp.playlist.next(None, None)
	#	else:  #reset progress bar
	#		self.pymp.control.setProgress(-1)
			
		return False
	
	#
	#  Triggered when mplayer's stdout reaches EOF.
	#
	def handleInput(self, source, condition):
		try:
		    for line in self.mplayerOut:
		        self.lookForStreamTitle(line)
		finally:
			return True
	
	#
	#  Triggered when mplayer prints something stdout.
	#
	def lookForStreamTitle(self, line):
		matches = re.search("(?<=StreamTitle=\')(.*)(\';StreamUrl=)", line)
		if matches:
			self.streamTitle = matches.group(1)
			for listener in self.streamTitleChangeListeners:
				keepListener = listener(self, self.streamTitle)
				if not keepListener:
					self.streamTitleChangeListeners.remove(listener)
	
	#
	#  Queries mplayer's playback status and upates the progress bar.
	#
	def queryStatus(self):
		
		self.cmd("get_percent_pos")  #submit status query
		self.cmd("get_time_pos")
		
		time.sleep(0.05)  #allow time for output
		
		line, percent, seconds = None, -1, -1
		
		while True:
			try:  #attempt to fetch last line of output
				line = self.mplayerOut.readline()
			except StandardError, detail:
				break
				
			if not line: break
			
			if line.startswith("ANS_PERCENT_POSITION"):
				percent = int(line.replace("ANS_PERCENT_POSITION=", ""))
			
			if line.startswith("ANS_TIME_POSITION"):
				seconds = float(line.replace("ANS_TIME_POSITION=", ""))
		
		#self.pymp.control.setProgress(percent, seconds)
		return True
		
	#
	#  Add a listener that will be called every time a change in stream title is detected.
	#  The signature of the callback should be:
	#	def callback(source, newStreamTitle)
	#
	def addStreamTitleChangeListener(self, callback):
		self.streamTitleChangeListeners.append(callback)
	
	#
	#  Removes a stream title change listener.
	#
	def removeStreamTitleChangeListener(self, callback):
		self.streamTitleChangeListeners.remove(callback)
	
	#
	#  Inserts the status query monitor.
	#
	def startStatusQuery(self):
		self.statusQuery = gobject.timeout_add(STATUS_TIMEOUT, self.queryStatus)
		
	#
	#  Removes the status query monitor.
	#
	def stopStatusQuery(self):
		if self.statusQuery:
			gobject.source_remove(self.statusQuery)
		self.statusQuery = 0
		
	#
	#  Inserts the EOF monitor.
	#
	def startEofHandler(self):
		self.eofHandler = gobject.io_add_watch(self.mplayerOut, gobject.IO_HUP, self.handleEof)
	
	#
	#  Removes the EOF monitor.
	#
	def stopEofHandler(self):
		if self.eofHandler:
			gobject.source_remove(self.eofHandler)
		self.eofHandler = 0
	
	#
	#  Inserts the input monitoy.
	#
	def startInputHandler(self):
		self.inputHandler = gobject.io_add_watch(self.mplayerOut, gobject.IO_IN, self.handleInput)
	
	#
	#  Removes the EOF monitor.
	#
	def stopInputHandler(self):
		if self.inputHandler:
			gobject.source_remove(self.inputHandler)
		self.inputHandler = 0
		
#End of file
