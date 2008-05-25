#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

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
import imaplib
import os
from gtk import Tooltips
from screenlets import mail

# error messages
MSG_CONNECTION_FAILED	= "Error while connecting to server."
MSG_FETCH_MAILS_FAILED	= "Unable to retrieve mails from server."
MSG_AUTH_FAILED = """Error on login - invalid login data given? Some hosts
may block connections for a certain interval before allowing reconnects."""




# superclass for new backends (could be improved, I guess - currently only
# designed for retrieving the number of mails in the backend because some
# backend do not support counting of new-mails)



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
	__timeout					= None
	__mailbackend			= None
	__status					= mail.MailCheckStatus.IDLE
	__mailbox_status	=	mail.MailboxStatus.UNKNOWN
	__blinking				= False
	__blink_phase			= 0
	__blink_timeout		= None
	__tooltips				= Tooltips()
	
	# editable options
	check_interval	= 1		# minutes!!!
	mail_client		= 'evolution'
	known_mailcount	= 0		# hidden option to remember number of known mails
	unseen_count			= 0
	backend_type	= 'IMAP'
	
	# POP3/IMAP-options (should be added by backend)
	pop3_server		= ''
	pop3_account	= ('', '')		# username/pass for POP3 mailbox
	imap_host			= ''
	imap_account	= ('','')
	
	# constructor
	def __init__ (self, **keyword_args):
		# call super
		screenlets.Screenlet.__init__(self, uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# init default backend
		#self.set_backend(mail.POP3Backend)
		# add menuitems
		self.add_menuitem('check_mail', 'Check now!')
		self.add_menuitem('open_client', 'Open client ...')

		# add option groups
		self.add_options_group('E-Mail', 'General MailCheck options ...')
		self.add_options_group('POP3', 'POP3-account options ...')
		self.add_options_group('IMAP', 'IMAP-account options ...')
		# add editable options
		self.add_option(StringOption('E-Mail','backend_type', self.backend_type,
			'Backend-Type', 'The type of the backend for getting mails ...',
			choices=['POP3', 'IMAP']))
		self.add_option(IntOption('E-Mail','check_interval', 
			self.check_interval, 'Checking interval (minutes)', 
			'The interval (in minutes) after that is checked for new mail ...', 
			min=1, max=1200))
		self.add_option(StringOption('E-Mail','mail_client', self.mail_client,
			'Mail-Client', 'The e-mail client-application to open ...'))
		# POP3 settings (TODO: let this be added by the backend)
		self.add_option(StringOption('POP3','pop3_server', self.pop3_server,
			'Server URL', 'The url of the POP3-server to check ...'), 
			realtime=False)
		self.add_option(AccountOption('POP3', 'pop3_account', 
			self.pop3_account, 'Username/Password', 
			'Enter username/password here ...'))
		# IMAP settings
		self.add_option(StringOption('IMAP', 'imap_host', self.imap_host,
			'Server URL', 'The hostname of the IMAP server to check ...'), 
			realtime=False)
		self.add_option(AccountOption('IMAP','imap_account',self.imap_account,
			'Username/Password','Enter username/password here ...'))
        # hidden options
#		self.add_option(IntOption('E-Mail','known_mailcount', 
#			self.known_mailcount, '', '', hidden=True))
#		self.add_option(IntOption('E-Mail','unchecked_mails', 
#			self.unchecked_mails, '', '', hidden=True))
		# TEST: add options from metadata (NOTE: need less backend.mailcount > self.known_mailcountugly way for this)
		# TEST: add options from metadata (NOTE: need less ugly way for this)
		#mypath = __file__[:__file__.rfind('/')]
		#self.add_options_from_file( mypath + '/' + self.__name__ + '.xml')	
		# init notify-support
		#screenlets.utils.init_notify()
		self.notifier = screenlets.utils.Notifier(self)
		# init mailcheck
		self.set_check_interval(self.check_interval)

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()
	
	def __setattr__ (self, name, value):
		screenlets.Screenlet.__setattr__(self, name, value)
		if name == 'check_interval':
			self.set_check_interval(value)
		elif name in ('known_mailcount', 'unchecked_mails'):
			self.redraw_canvas()
		elif name == 'backend_type':
			if self.has_started:screenlets.show_message(self, 'Restart required')
			if value == 'POP3':
				self.set_backend(mail.POP3Backend)
			elif value == 'IMAP':
				self.set_backend(mail.IMAPBackend)
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
			self.__mailbackend.stop()
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
			self.__status = mail.MailCheckStatus.REFRESH 
			self.redraw_canvas()
			self.__mailbackend.start()
		return False	# in case we are run as a timeout
	
	def set_check_interval (self, interval):
		"""Set the interval time after that is checked for new mails (in 
		minutes)."""
		if self.__timeout:
			gobject.source_remove(self.__timeout)
		self.__timeout = gobject.timeout_add(interval * 60000, 
			self.run_mailcheck)
	
		
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
		"""Draw the text with the unread count."""
		if self.unseen_count > 0:
			ctx.translate(16, 41) # TODO: use options here
			p_layout = ctx.create_layout()
			p_fdesc = pango.FontDescription("Free Sans Bold 10")
			p_layout.set_font_description(p_fdesc)
			p_layout.set_markup(str(self.unseen_count))
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
	
	def handle_check_finished (self, backend, status, mailbox_status):
		"""Gets called whenver the backend-thread finished its job. Checks
		the status of the backend and performs the needed actions.
		Starts new timeout after getting called"""
		print "handle_check_finished(); status = %i, mailbox_status = %i" % (status, mailbox_status)
		self.unseen_count = backend.unseen_count
		if status == mail.MailCheckStatus.ERROR:
			#screenlets.show_error(self, backend.error)	# threading-problem!!!
			self.notifier.notify(backend.error)
		self.__status = status
		self.__mailbox_status = mailbox_status
		#threading.g_thread_init()
		#gobject.gdk_threads_init()
		self.redraw_canvas()
		# finally we re-add the timeout-function to init the next check
		# (we don't use more than one thread this way and avoid duplicate 
		# and/or hanging threads in the background)
		self.set_check_interval(self.check_interval)

	
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
			if self.__mailbox_status == mail.MailboxStatus.UNREAD_MAIL or \
				self.__mailbox_status == mail.MailboxStatus.NEW_MAIL:
				#self.theme['mailcheck-got-mail.svg'].render_cairo(ctx)
				self.theme.render(ctx, 'mailcheck-got-mail')
			else:
				self.theme.render(ctx, 'mailcheck-bg')
		# blinking?
		if self.blinking():
			self.draw_blinking(ctx)
		# draw icon?
		if self.__status == mail.MailCheckStatus.REFRESH:
			print "draw refresh icon"
			self.draw_icon(ctx, 'refresh')
		elif self.__status == mail.MailCheckStatus.ERROR:
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

