############################################################################
# Programmers: Jiva DeVoe <jiva@devoesquared.com>
# Filename: iCal.py
# http://www.devoesquared.com/Software/iCal_Module
#
# Contributors / Alterations:
# stefan natchev: april 15, 2005 - added support for dates with ranges
# stefan natchev: april 16, 2005 - added more recurrance support
# Aaron A. Seigo aseigo@kde.org: January 2006 - patches for event lookup for multi-day events. (see occursOn)
# Danil Dotsenko dd@accentsolution.com: June 15, 2006 - reworked file rutine in ICalReader to work with generic paths and added fileFilter and check for correct header.
# Danil Dotsenko dd@accentsolution.com: -----||------ - reworked other functions for efficiency.
# Paul van Erk: July 3, 2006 - fixed a bug where all-day events would be counted as 2 days (and 2-day events as 3, etc)
# Danil Dotsenko dd@accentsolution.com: Sept 04, 2006 - changed the iCalReader class init rutine to init on the basis of raw data list, not filenames. This allows reading files from remote sources.
#  Warning! with this version (20060904) I am braking backward compatibility in __init__() arguments of ICalReader
#
# version 20060904
#
# "2-Clause" BSD license
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
############################################################################

import os
import os.path
import re
import datetime
import time

class ICalReader:
	def __init__(self, dataLines = None):
		'''
		iCal.ICalReader([dataList])

		Initializes the iCal reader and parses the list type object for events.
		The list type object with iCal contents is optional.
		You can call readFiles(file name list) and readEvents(iCal data lines) separately.
		'''
		self.events = []
		if dataLines:
			self.readEvents(dataLines)

	def readFiles(self, fileList):
		'''
		readFiles(fileList)

		This function accepts ARRAY with list of local file names.
		We put contents of the files into one big list and feed to readEvents()
		We only work with files, no folders or wildcards.
		'''
		dataLines = []
		for item in range(fileList.__len__()):
			if os.path.isfile(fileList[item]): # not sure why I am doing it, your code should...
				tempFile = open(fileList[item], 'r')
				dataLines.extend(tempFile.readlines())
				tempFile.close()
		if dataLines:
			self.readEvents(dataLines)

	def readURL(self, url):
		'''
		Put rutine to fetch and convert a resource into lines and feed it to readEvents()
		'''
		dataLines = None
		try:
			import urllib2
			tempFile = urllib2.urlopen(url)
			dataLines = tempFile.readlines()
			tempFile.close()
		except:
			tempFile = open(url,'r')
			dataLines = tempFile.readlines()
			tempFile.close()
		if dataLines:
			self.readEvents(dataLines)

	def readEvents(self, lines, emptyEvents=False):
		if emptyEvents:
			self.events = []
			# this is here for MY convenience. Don't rely on this.
			# Instead just to iCalObject.events = {} in your code.
			# The latter allows emptying events with functions like readURL and readFiles
		mask = {}
		mask['BEGIN'] = re.compile("^BEGIN:VEVENT")
		mask['END'] = re.compile("^END:VEVENT")
		inEvent= False
		for line in lines: # this will only work if there is no such thing as nested VEVENTs. It assumes there is one END:VEVENT fro every openning BEGIN
			if mask['BEGIN'].match(line):
				eventLines = []
				inEvent = True
			elif mask['END'].match(line) and inEvent:
				# note: BEGIN: and END: are not included in the list.
				self.events.append(self.parseEvent(eventLines))
				inEvent = False
			elif inEvent:
				eventLines.append(line)

	def parseEvent(self, lines):
		event = ICalEvent()
		startDate = None
		rule = None
		endDate = None
		#it has to have something for a summary(?) -s
		event.summary = ''
		mask={}
		mask['Summary']=re.compile("^SUMMARY:(.*)")
		mask['DTStart']=re.compile("^DTSTART;.*:(.*).*")
		mask['DTEnd']=re.compile("^DTEND;.*:(.*).*")
		mask['DTStartTZ']=re.compile("^DTSTART:(.*)T.*Z")
		mask['DTEndTZ']=re.compile("^DTEND:(.*)T.*Z")
		mask['ExDate']=re.compile("^EXDATE.*:(.*)")
		mask['RRule']=re.compile("^RRULE:(.*)")
		timed = '1'
		for line in lines:
			if mask['Summary'].match(line):
				event.summary = mask['Summary'].match(line).group(1)
			#these are the dtstart/dtend with no time range
			elif mask['DTStart'].match(line):
				startDate = self.parseDate(mask['DTStart'].match(line).group(1))
				timed = '0'
			elif mask['DTEnd'].match(line):
				endDate = self.parseDate(mask['DTEnd'].match(line).group(1))
				timed = '0'
			#these are the ones that are 'ranged'
			elif mask['DTStartTZ'].match(line):
				startDate = self.parseDate(mask['DTStartTZ'].match(line).group(1))
			elif mask['DTEndTZ'].match(line):
				endDate = self.parseDate(mask['DTEndTZ'].match(line).group(1))
			elif mask['ExDate'].match(line):
				event.addExceptionDate(self.parseDate(mask['ExDate'].match(line).group(1)))
			elif mask['RRule'].match(line):
				rule = mask['RRule'].match(line).group(1)
		event.startDate = startDate
		event.endDate = endDate
		event.timed = timed
		if rule:
			event.addRecurrenceRule(rule)
		return event

	#def parseTodo(self, lines):
	#	todo = ICalTodo()
	#	startDate = None
	#	endDate = None

	def parseDate(self, dateStr):
		year = int(dateStr[0:4])
		if year < 1970:
			year = 1970
		month = int(dateStr[4:4+2])
		day = int(dateStr[6:6+2])
		try:
			hour = int(dateStr[9:9+2])
			minute = int(dateStr[11:11+2])
		except:
			hour = 0
			minute = 0
		return datetime.datetime(year, month, day, hour, minute)

	def selectEvents(self, selectFunction):
		note = datetime.datetime.today()
		self.events.sort()
		events = filter(selectFunction, self.events)
		return events

	def todaysEvents(self, event):
		return event.startsToday()

	def tomorrowsEvents(self, event):
		return event.startsTomorrow()

	def afterTodaysEvents(self, event):
		return event.startsAfterToday()

	def eventsFor(self, date):
		note = datetime.datetime.today()
		self.events.sort()
		ret = []
		for event in self.events:
			#if event.startsOn(date):
			if event.occursOn(date):
				ret.append(event)
		return ret

		year = int(dateStr[0:4])
		if year < 1970:
			year = 1970

		month = int(dateStr[4:4+2])
		day = int(dateStr[6:6+2])
		try:
			hour = int(dateStr[9:9+2])
			minute = int(dateStr[11:11+2])
		except:
			hour = 0
			minute = 0

class ICalEvent:
	def __init__(self):
		self.exceptionDates = []
		self.dateSet = None

	def __str__(self):
		return self.summary

	def __eq__(self, otherEvent):
		return self.startDate == otherEvent.startDate

	def addExceptionDate(self, date):
		self.exceptionDates.append(date)

	def addRecurrenceRule(self, rule):
		self.dateSet = DateSet(self.startDate, self.endDate, rule)

	def startsToday(self):
		return self.startsOn(datetime.datetime.today())

	def startsTomorrow(self):
		tomorrow = datetime.datetime.fromtimestamp(time.time() + 86400)
		return self.startsOn(tomorrow)

	def startsAfterToday(self):
		return self.startsAfter(datetime.datetime.today())

	def startsOn(self, date):
		return (self.startDate.year == date.year and
			self.startDate.month == date.month and
			self.startDate.day == date.day or
			(self.dateSet and self.dateSet.includes(date)))

	def occursOn(self, date):
		if (self.timed == '0'):
			return (self.startsOn(date) or (self.startDate < date and self.endDate >= date) and self.endDate != date)
		else:
			return (self.startsOn(date) or (self.startDate < date and self.endDate >= date))

	def startsAfter(self, date):
		return (self.startDate > date)

	def startTime(self):
		return self.startDate

#class ICalTodo:

#strange...
#class DateParser:
def parse(dateStr):
	year = int(dateStr[0:4])
	if year < 1970:
		year = 1970

	month = int(dateStr[4:4+2])
	day = int(dateStr[6:6+2])
	try:
		hour = int(dateStr[9:9+2])
		minute = int(dateStr[11:11+2])
	except:
		hour = 0
		minute = 0
	return datetime.datetime(year, month, day, hour, minute)


class DateSet:
	def __init__(self, startDate, endDate, rule):
		self.startDate = startDate
		self.endDate = endDate
		self.startWeekNumber = startDate.isocalendar()[1]
		self.frequency = None
		self.count = None
		self.interval = 1
		self.untilDate = None
		self.byMonth = None
		self.byDate = None
		self.parseRecurrenceRule(rule)

	def parseRecurrenceRule(self, rule):
		if re.compile("FREQ=(.*?);").match(rule):
			self.frequency = re.compile("FREQ=(.*?);").match(rule).group(1)

		if re.compile("COUNT=(\d*)").search(rule):
			self.count = int(re.compile("COUNT=(\d*)").search(rule).group(1))

		if re.compile("UNTIL=(.*?);").search(rule):
			#homebrewed
			self.untilDate = parse(re.compile("UNTIL=(.*?);").search(rule).group(1))
		if re.compile("INTERVAL=(\d*);").search(rule):
			self.interval = int(re.compile("INTERVAL=(\d*);").search(rule).group(1))

		if re.compile("BYMONTH=(.*?);").search(rule):
			self.byMonth = re.compile("BYMONTH=(.*?);").search(rule).group(1)

		if re.compile("BYDAY=(.*?);").search(rule):
			self.byDay = re.compile("BYDAY=(.*?);").search(rule).group(1)



	def includes(self, date):
		if date == self.startDate:
			return True

		if self.untilDate and date > self.untilDate:
			return False

		if self.frequency == 'DAILY':
			if self.interval:
				increment = self.interval
			else:
				increment = 1
			d = self.startDate
			counter = 0
			while(d < date):
				if self.count:
					counter += 1
					if counter >= self.count:
						return False

				d = d.replace(day=d.day+1)

				if (d.day == date.day and
					d.year == date.year and
					d.month == date.month):
					return True

		elif self.frequency == 'WEEKLY':
			if self.startDate.weekday() == date.weekday():
			   #make sure the interval is proper -Milo
			   if self.startWeekNumber % self.interval == date.isocalendar()[1] % self.interval:
				  return True
			   else:
				  return False
			else:
				if self.endDate:
					for n in range(0, self.endDate.day - self.startDate.day):
						newDate = self.startDate.replace(day=self.startDate.day+n)
						if newDate.weekday() == date.weekday():
							return True

		elif self.frequency == 'MONTHLY':
			pass

		elif self.frequency == 'YEARLY':
			pass

		return False


if __name__ == '__main__':
	reader = ICalReader()
	# reader.readURL('http://www.google.com/calendar/ical/4dmslp71qlvjhl1q6g6f88gfv4@group.calendar.google.com/public/basic.ics')
	reader.readURL('file:///home/dd/musor/icalout.ics')
	for event in reader.events:
		print event
