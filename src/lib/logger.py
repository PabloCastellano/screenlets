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

# Logger and command line parser for universal-applets.
# (c) 2008 Przemyslaw Firszt (pefi) <pefi@epf.pl>

import os
import sys
import logging

import screenlets

def logger_init():
	"""Initialize logger"""
	options = screenlets.COMMAND_LINE_OPTIONS
	#create main logger
	log = logging.getLogger(screenlets.LOG_NAME)
	if not options.LOG_DISABLED:
		#set log output
		if options.LOG_OUTPUT == "STDOUT":
			log_file = logging.StreamHandler(sys.stdout)
		elif options.LOG_OUTPUT == "STDERR":
			log_file = logging.StreamHandler(sys.stderr)
		elif options.LOG_OUTPUT == "FILE":
			try:
				log_file = logging.FileHandler(screenlets.LOG_FILE, "w")
			except IOError:
				print("Cannot create %s logfile. Using STDERR instead.") %(screenlets.LOG_FILE)
				log_file = logging.StreamHandler(sys.stderr)
		else:
			print("Unknown output type: %s, using STDERR instead.") %(screenlets.LOG_FILE)
			log_file = logging.StreamHandler(sys.stderr)
		#check if LOG_LEVEL is valid and set
		try:
			level = 51 - (10 * int(options.LOG_LEVEL))  #multiply by 10 and substract from 51 to fit into allowed range
			log.setLevel(level)
			log_file.setLevel(level)
		except ValueError:
			print ("LOG_LEVEL %s is not allowed. Use -h to get more information. Using LOG_LEVEL=5") %(screenlets.LOG_LEVEL)
			log.setLevel(1) #command  line paramete was wrong, but user wanted logging ..."1" means log everything
			log_file.setLevel(1)
	else:
		#do not log anything but we still have to provide logger to avoid errors
		log_file = logging.StreamHandler(sys.stderr)
		#screenlets.LOG_LEVEL = 51
		log.setLevel(51)
		log_file.setLevel(51)
	
	#set the format of log message
	log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
	log_file.setFormatter(log_formatter)
	
	#add file to logger
	log.addHandler(log_file)
	return log

log = logger_init()

def get_default_logger():
	"""This function returns default logger"""
	global log
	# Try to return the logger (an exception mean that the logger has not yet been initialized)
	try:
		return log
	except NameError:
		log = logger_init()
		if log:
			log.debug("%s: Logger initialized" %__name__)
			return log
		else:
			print("%s: Cannot initialize logger!" %__name__) #TODO to quit or not to quit? Lack of logger may cause random errors
			return None #TODO Raise Exception?


