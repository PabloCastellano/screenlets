#!/usr/bin/env python

#  MailCheckScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - A Screenlet to check for new mails on a backend (POP3-server, maildir, 
#   gmail, imap, ...).
# 
# TODO:
# - bug: refresh-icon remains when backend switches to IDLE after being in 
#   GOT_MAIL-state
# - optional evolution-integration?
# - fix displaying of number of mails (make optional), maybe only on hover?
# - add SSL-support to POP3Backend
# - backends need to be able to supply their own editbale options which
#   are only visible when the given backend is set (needs improvement in
#   options-system)
#
# IDEAS:
# - send email by dragging text onto the Screenlet (show popup-dialog asking
#   for a mail address, maybe with contact-list or evolution-integration)
#

import screenlets
import screenlets.utils
from screenlets.options import StringOption, IntOption, BoolOption
from screenlets.options import AccountOption

import gobject
import threading
import cairo
import pango
import socket
import math
import poplib
import os
from gtk import Tooltips


# error messages
MSG_CONNECTION_FAILED	= "Error while connecting to server."
MSG_FETCH_MAILS_FAILED	= "Unable to retrieve mails from server."
MSG_AUTH_FAILED = """Error on login - invalid login data given? Some hosts
may block connections for a certain interval before allowing reconnects."""


# the current operational status of the mailcheck
class MailCheckStatus:
	REFRESH		= 1
	GOT_MAIL	= 2
	ERROR		= 3
	IDLE		= 100


# superclass for new backends (could be improved, I guess - currently only
# designed for retrieving the number of mails in the backend because some
# backend do not support counting of new-mails)
class MailCheckBackend (gobject.GObject):
	"""The backend class which performs checking for mail and offers access
	to the current mail-backend. By subclassing this class you can add multiple
	mail-backends to the MailCheckScreenlet (e.g. pop3, maildir, imap, 
	gmail, ...)."""
	
	__gsignals__ = dict(check_finished=(gobject.SIGNAL_RUN_FIRST,
		gobject.TYPE_NONE, (gobject.TYPE_INT,)))
	
	def __init__ (self, name, screenlet):
		gobject.GObject.__init__(self)
		# properties
		self.name		= name					# name of backend
		self.screenlet	= screenlet				# assigned MailCheckScreenlet
		self.refreshing	= False					# not refreshing yet
		self.mailcount	= 0						# num of mails found on server
		self.status		= MailCheckStatus.IDLE	# status of the backend
		self.error		= ''					# human-readable error message
		self.options	= []					# ???additonal Options for backend
		self.thread	= None
	
	def check_mail (self):
		"""This handler should be overridden by subclasses to add new types
		of checking mails in a backend. This handler has to set self.mailcount 
		to the number of mails found in the backend. The return value is
		ignored, set self.error and self.status to return results."""
	
	def start (self):
		"""Start receiving mails from the backend. Runs self.__execute as
		a separate thread."""
		self.thread = threading.Thread(target=self.__execute).start()
		
	def __execute (self):
		"""Execute the thread and call the check-mail function."""
		# set status to REFRESH and call check_mail-handler to fetch mails
		self.refreshing	= True
		self.status		= MailCheckStatus.REFRESH
		self.check_mail()
		# notify registered handlers that we are ready with checking
		self.emit('check_finished', self.status)
		# and set status back to idle
		self.status		= MailCheckStatus.IDLE
		# not refreshing anymore
		self.refreshing	= False


# IMAPBackend was contributed by Robert Gartler - thanks :)
class IMAPBackend(MailCheckBackend):
	"""A backend for retrieving the mailcount from an IMAP server."""

	def __init__ (self, screenlet):
		# call super
		MailCheckBackend.__init__(self, 'IMAP', screenlet)

	def check_mail(self):
		# set default timeout for all socket connections to 30 secs
		socket.setdefaulttimeout(30000)
		print "POP3Backend: Connecting to IMAP-server ... please wait."
		try:
			server = IMAP4(self.screenlet.imap_server)
		except:
			self.error	= MSG_CONNECTION_FAILED
			self.status	= MailCheckStatus.ERROR
			return False
		user, passwd=self.screenlet.imap_account
		try:
			server.login(user,passwd)
		except:
			self.error	= MSG_AUTH_FAILED
			self.status	= MailCheckStatus.ERROR
			server.logout()
			return False

		typ,data = server.select()
		if typ == 'OK':
			msgnum = int(data[0])
			if msgnum > self.mailcount:
				diff = msgnum - self.mailcount
				self.mailcount	= msgnum
				self.status		= MailCheckStatus.GOT_MAIL
				print "GOT_MAIL"
			elif msgnum <= self.mailcount:
				self.mailcount	= msgnum
				self.status		= MailCheckStatus.IDLE
				print "IDLE"
		else:
			self.error	= MSG_FETCH_MAILS_FAILED
			self.status	= MailCheckStatus.ERROR
			server.logout()
		return False


class POP3Backend (MailCheckBackend):
	"""A backend for retrieving the mailcount from a POP3 server."""
	
	def __init__ (self, screenlet):
		# call super
		MailCheckBackend.__init__(self, 'POP3', screenlet)
		# init additional attributes for this backend-type
		# TODO: add POP3-specific options to the backend instead of having them
		# defined in the screenlet by default (ideally they should be only shown
		# when the POP3-backend is active
		
	def check_mail (self):
		# set default timeout for all socket connections to 30 secs
		socket.setdefaulttimeout(30000)
		print "POP3Backend: Connecting to POP3-server ... please wait."
		#self.screenlet.redraw_canvas()
		try:
			server = poplib.POP3(self.screenlet.pop3_server)
		except:
			self.error	= MSG_CONNECTION_FAILED
			self.status = MailCheckStatus.ERROR
			return False
		# authenticate
		user, pw = self.screenlet.pop3_account
		#print "ACCOUNT IS %s/%s!!" % (o[0], o[1])
		try:
			# TODO: remove print here once ready!!!!
			print server.user(user)
			print server.pass_(pw)
		except:
			self.error	= MSG_AUTH_FAILED
			self.status = MailCheckStatus.ERROR
			server.quit()
			return False
		# get list with mails (response, list-of-mails)
		resp = server.list()
		if resp[0].startswith('+OK'):
			messages = resp[1]
			#print messages
			msgnum = len(messages)
			if msgnum > self.mailcount:
				diff = msgnum - self.mailcount
				self.mailcount = msgnum
				self.status = MailCheckStatus.GOT_MAIL
				print "GOT_MAIL"
			elif msgnum <= self.mailcount:
				self.mailcount = msgnum
				self.status = MailCheckStatus.IDLE
				print "IDLE"
		else:
			self.error	= MSG_FETCH_MAILS_FAILED
			self.status	= MailCheckStatus.ERROR
			#server.quit()
			#return False
		# close connection
		server.quit()
		return False


class MailCheckScreenlet (screenlets.Screenlet):
	"""A Screenlet that notifies you about new e-mail. When you
	receive new mail, the icon starts flashing and you get quick access to your 
	favorite eMail-client program. <span color="red">WARNING: Password is saved 
	as plain text if you don't have gnomekeyring installed!!!!</span>"""
	
	# default meta-info for Screenlets
	__name__	= 'MailCheckScreenlet'
	__version__	= '0.3'
	__author__	= 'RYX (aka Rico Pfaus) 2007'
	__desc__	= __doc__
	
	# internals
	__timeout		= None
	__mailbackend	= None
	__status		= MailCheckStatus.IDLE
	__blinking		= False
	__blink_phase	= 0
	__blink_timeout	= None
	__tooltips		= Tooltips()
	
	# editable options
	check_interval	= 1		# minutes!!!
	mail_client		= 'evolution'
	known_mailcount	= 0		# hidden option to remember number of known mails
	unchecked_mails	= 0		# hidden option to remember unchecked mails
	backend_type	= 'POP3'
	
	# POP3/IMAP-options (should be added by backend)
	pop3_server		= ''
	pop3_account	= ('', '')		# username/pass for POP3 mailbox
	imap_server		= ''
	imap_account	= ('','')
	
	# constructor
	def __init__ (self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# init default backend
		self.set_backend(POP3Backend)
		# add menuitems
		self.add_menuitem('check_mail', 'Check now!')
		self.add_menuitem('open_client', 'Open client ...')
		self.add_default_menuitems()
		# add option groups
		grp_mail = self.create_option_group('E-Mail', 'General mail-options.')
		grp_pop3 = self.create_option_group('POP3 ', 'POP3-account options.')
		grp_imap = self.create_option_group('IMAP ', 'IMAP-account options.')
		# add editable options
		grp_mail.add_option(StringOption('backend_type', self.backend_type,
			'Backend-Type', 'The type of the backend for getting mails ...',
			choices=[ 'IMAP']))
		grp_mail.add_option(IntOption('check_interval', 
			self.check_interval, 'Checking interval (minutes)', 
			'The interval (in minutes) after that is checked for new mail ...', 
			min=1, max=1200))
		grp_mail.add_option(StringOption('mail_client', self.mail_client,
			'Mail-Client', 'The e-mail client-application to open ...'))
		# POP3 settings (TODO: let this be added by the backend)
		grp_pop3.add_option(StringOption('pop3_server', self.pop3_server,
			'Server URL', 'The url of the POP3-server to check ...', 
			realtime=False))
		grp_pop3.add_option(AccountOption('pop3_account', self.pop3_account, 
			'Username/Password', 'Enter username/password here ...'))
		# IMAP settings
		grp_imap.add_option(StringOption('imap_server', self.imap_server,
			'Server URL', 'The url of the IMAP-server to check ...', 
			realtime=False))
		grp_imap.add_option(AccountOption('imap_account',self.imap_account,
			'Username/Password','Enter username/password here ...'))
        # hidden options
		grp_mail.add_option(IntOption('known_mailcount', self.known_mailcount, 
			'', '', hidden=True))
		grp_mail.add_option(IntOption('unchecked_mails', self.unchecked_mails, 
			'', '', hidden=True))
		# TEST: add options from metadata (NOTE: need less ugly way for this)
		#mypath = __file__[:__file__.rfind('/')]
		#self.add_options_from_file( mypath + '/' + self.__name__ + '.xml')	
		# init notify-support
		#screenlets.utils.init_notify()
		self.notifier = screenlets.utils.Notifier(self)
		# init mailcheck
		self.set_check_interval(self.check_interval)
	
	def __setattr__ (self, name, value):
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'check_interval':
			self.set_check_interval(value)
		elif name in ('known_mailcount', 'unchecked_mails'):
			self.redraw_canvas()
		elif name == 'backend_type':
			if value == 'POP3':
				self.set_backend(POP3Backend)
			elif value == 'IMAP':
				self.set_backend(IMAPBackend)
			else:
				screenlets.show_error(self, 'Invalid backend type: %s' % value)
	
	# --------------------------------------------------------------------------
	# custom functions for this screenlet
	# --------------------------------------------------------------------------
	
	def set_backend (self, backend_class):
		"""Creates a new instance of the given backend-class and sets it
		as the new backend for receiving mails. Also connects to the
		signals and disconnects/quits the currently active backend.
		TODO: check for running acton and ask for confirmation"""
		if self.__mailbackend:
			# check for refresh-status in curr. backend
			# disconnect signals and remove backend
			print "BACKEND SET, TODO: remove/free"
			pass
		else:
			# create new backend and connect to its signals
			self.__mailbackend = backend_class(self)
			self.__mailbackend.connect('check_finished', 
				self.handle_check_finished)
	
	def run_mailcheck (self):
		"""Check the current backend for email (executes backend-thread and
		returns False)."""
		# TODO: add function in backend to check if all needed things are set
		# like server/pass/user/... - if not, show error
		# if it is not currently refreshing
		if not self.__mailbackend.refreshing:
			self.__mailbackend.start()
			# workaround, cause backend shouldn't call redraw
			self.__status = MailCheckStatus.REFRESH 
			self.redraw_canvas()
		return False	# in case we are run as a timeout
	
	def set_check_interval (self, interval):
		"""Set the interval time after that is checked for new mails (in 
		minutes)."""
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(interval * 60000, 
			self.run_mailcheck)
	
	def reset_to_idle (self):
		"""Reset the status back to idle state. (REMOVE???)"""
		self.stop_blinking()
		self.__status == MailCheckStatus.IDLE
		self.redraw_canvas()
		self.unchecked_mails = 0
		
	# blinking
	
	def blinking (self):
		"""Return true if blinking, else False."""
		return self.__blink_timeout != None
	
	def blink_interval (self):
		"""Timeout-interval function for blink-effect."""
		if self.blinking():
			#print "BLINK"
			self.__blink_phase += 0.1
			if self.__blink_phase > 0.7:
				self.__blink_phase = 0.0
			self.redraw_canvas()
			return True
		return False
	
	def start_blinking (self):
		"""Start blinking animation."""
		if not self.blinking():
			self.__blink_timeout = gobject.timeout_add(100, self.blink_interval)
	
	def stop_blinking (self):
		"""Stop blinking animation."""
		self.__blink_phase	= 0.0
		if self.__blink_timeout:
			gobject.source_remove(self.__blink_timeout)
			self.__blink_timeout = None
	
	# drawing
	
	def draw_blinking (self, ctx):
		"""Draw the white overlay for the blink-effect."""
		ctx.save()
		ctx.set_operator(cairo.OPERATOR_ATOP)
		ctx.rectangle(0, 0, self.width, self.height)
		ctx.set_source_rgba(1, 1, 1, self.__blink_phase)
		ctx.fill()
		ctx.save()
	
	def draw_icon (self, ctx, name, rotation=0):
		"""Draw the given icon (only a simple image) from within the theme."""
		ctx.save()
		ctx.set_operator(cairo.OPERATOR_OVER)
		ctx.translate(self.width-48, self.height-48)
		ctx.rotate(rotation)
		self.theme.render(ctx, 'mailcheck-icon-' + name)
		#self.theme['mailcheck-icon-' + name + '.svg'].render_cairo(ctx)
		ctx.restore()
	
	def draw_text (self, ctx):
		"""Draw the text with the mail count."""
		ctx.translate(16, 41) # TODO: use options here
		p_layout = ctx.create_layout()
		p_fdesc = pango.FontDescription("Free Sans Bold 10")
		p_layout.set_font_description(p_fdesc)
		if self.known_mailcount > -1:
			mnumstr = str(self.known_mailcount)
		else:
			mnumstr = "-"
		p_layout.set_markup(str(self.unchecked_mails) + '|' + mnumstr)
		ctx.set_source_rgba(0.5, 0.5, 0.5, 0.3)
		ctx.show_layout(p_layout)
		ctx.fill()
		ctx.translate(-1, -1)
		ctx.set_source_rgba(0, 0, 0, 1)	# TODO: option!
		ctx.show_layout(p_layout)
		ctx.fill()
	
	# --------------------------------------------------------------------------
	# signal-handler for MailCheckBackend
	# --------------------------------------------------------------------------
	
	def handle_check_finished (self, backend, status):
		"""Gets called whenver the backend-thread finished its job. Checks
		the status of the backend and performs the needed actions.
		Starts new timeout after getting called"""
		#gtk.gdk.threads_enter()	# start critical section
		if status == MailCheckStatus.GOT_MAIL:
			print "You got %i mail(s)." % backend.mailcount
			# if we got mail, check if we got more mails than last time
			if backend.mailcount > self.known_mailcount:
				self.__status = status					# yup, we got new mail
				self.unchecked_mails = backend.mailcount - self.known_mailcount
				self.known_mailcount = backend.mailcount
				print "You got %i new mail(s)." % self.unchecked_mails
				# start blinking
				self.start_blinking()
			else:
				self.__status = MailCheckStatus.IDLE
		elif status == MailCheckStatus.ERROR:
			# if we had an error
			self.__status = status
			#screenlets.show_error(self, backend.error)	# threading-problem!!!
			self.notifier.notify(backend.error)
		else:
			self.reset_to_idle()
		# and redraw the screenlet
		self.redraw_canvas()
		# finally we re-add the timeout-function to init the next check
		# (we don't use more than one thread this way and avoid duplicate 
		# and/or hanging threads in the background)
		self.set_check_interval(self.check_interval)
		#gtk.gdk.threads_leave()	# end critical section
	
	# --------------------------------------------------------------------------
	# overridden Screenlet-handlers
	# --------------------------------------------------------------------------
	
	def on_menuitem_select (self, id):
		if id == 'check_mail':
			self.run_mailcheck()
		elif id == 'open_client':
			# TODO: execute e-mail application
			self.reset_to_idle()
			if self.mail_client != '':
				os.system(self.mail_client + '&')
			else:
				screenlets.show_error(self, "You have to define an "+\
					"eMail-client to be opened by this action (e.g. "+\
					"evolution or thunderbird). Go to the Properties in "+\
					"the right-click menu to define your client of choice.")
	
	def on_draw (self, ctx):
		ctx.scale(self.scale, self.scale)
		if self.theme:
			if self.__status == MailCheckStatus.GOT_MAIL or \
				self.unchecked_mails == True:
				#self.theme['mailcheck-got-mail.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'mailcheck-got-mail')
			else:
				self.theme.render(ctx, 'mailcheck-bg')
		# blinking?
		if self.blinking():
			self.draw_blinking(ctx)
		# draw icon?
		if self.__status == MailCheckStatus.REFRESH:
			self.draw_icon(ctx, 'refresh')
		elif self.__status == MailCheckStatus.ERROR:
			self.draw_icon(ctx, 'error')
		# draw text (TODO: make optional)
		self.draw_text(ctx)
		
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)
	
	def on_quit (self):
		# clear timeout
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		if self.blinking():
			self.stop_blinking()
		if self.__mailbackend.refreshing:
			print "Waiting for backend to finish its current job (if this takes too long we may have a hanging thread, restart your gnome session in that case)."
			del self.__mailbackend


# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(MailCheckScreenlet, threading=True)

