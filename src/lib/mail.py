import screenlets
import dbus
import os
import sys
import stat
import gettext
import re
import urllib
gettext.textdomain('screenlets')
gettext.bindtextdomain('screenlets', '/usr/share/locale')
import gobject
import socket
import threading
try:
	import poplib
except ImportError, err:
	print " !!!Please install python poplib :", err

try:
	import gnomevfs
except ImportError, err:
	print " !!!Please install python gnomevfs :", err


def get_KMail_num():
	"""This gets the unread mail number of kmail"""
	kmail = commands.getoutput("dcop kmail default checkMail; sleep 5; echo ' ' | tr -d '\n'; dcop kmail KMailIface getFolder /Krealia/Inbox > /dev/null; dcop 'DCOPRef(kmail,FolderIface)' unreadMessages | tr -d '\n'; echo ' '")
	if kmail.find("ERROR: Couldn't attach to DCOP server!") != -1:
		return None
	else:
		return kmail

def get_GMail_Num(login, password):
	"""This output the number of messages of gmail box"""
	f = os.popen("wget --no-check-certificate -qO - https://" + login + ":" + password + "@mail.google.com/mail/feed/atom")
	a = f.read()
	f.close()
	match = re.search("<fullcount>([0-9]+)</fullcount>", a)
	if match == None:
		return None
	else:
		return match.group(1)



def get_Mail_Num(server, login, passwd):
	"""This output the number of messages of mail box"""
	m = poplib.POP3(server)
	m.user(login)
	m.pass_(passwd)
	out = m.stat()
	m.quit()
	num = out[0]
	return num


def send_mail(smtp_server,fromaddr,toaddrs, subject,msg):
	import smtplib
	server = smtplib.SMTP(smtp_server)
	server.sendmail(fromaddr, toaddrs, subject + msg)
	server.quit()

#------CLASSES----------
#-----------------------

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
		print "IMAPBackend: Connecting to IMAP-server ... please wait."
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


class Mailer:
    """
    Class that retrieve the information from an Imap, Pop or mbox account

    All the email-related operation lies in this few lines
    """
    import imaplib
    import poplib
    import mailbox
    from sys import exc_info
    from os import stat, utime, path, listdir
    
    
    def __init__(self, config):
        self.config=config
        self.last_size=-1
        self.size=-1
        self.mbox_size = 0
        self.mbox_mtime = 0

    def __call__(self):
        self.last_size=self.size

        try:
            # IMAP4
            #
            if self.config['method']=='imap4':
                s = self.imaplib.__dict__['IMAP4'+['','_SSL']
                                          [self.config['ssl']]]\
                                          (self.config['host'])
                s.login(self.config['user_name'],self.config['user_password'])
                s.select()
                size = len(s.search(None, 'UNSEEN')[1][0].split())
                s.logout()
                
            # POP3
            #
            elif self.config['method']=='pop3':
                s = self.poplib.__dict__['POP3'+['','_SSL']
                                         [self.config['ssl']]]\
                                         (self.config['host'])
                s.user(self.config['user_name'])
                s.pass_(self.config['user_password'])
                size = len(s.list()[1])
                
            # Maildir
            #
            # This was reported to work with qmail, but it is untested with
            # other mail servers -- for maximum portability, one could
            # still rewrite next four lines using the mailbox Python module
            # (in core libraries).
            #
            elif self.config['method'] == 'maildir':
                mdir_path = getenv('MAILDIR', self.config['mailspool'])
                mdir_new = self.path.join(self.path.expanduser(mdir_path), 'new')

                size = len([f for f in self.listdir(mdir_new) if f[0] != '.'])

            # Unix mbox
            #
            elif self.config['method'] == 'mbox':
                mbox_path = getenv('MAIL',self.config['mailspool'])
                # Get mbox inode properties
                #
                s = self.stat(mbox_path)
                if (s.st_size == self.mbox_size and
                    s.st_mtime == self.mbox_mtime):
                    size = self.last_size	# mbox has not changed on disk
                else:
                    size = 0			# mbox has changed
                    for m in self.mailbox.PortableUnixMailbox(file(mbox_path)):
                        if m.get('status','N').find('N') != -1:
                            size += 1
                            
                    # Trick the system into thinking the mbox inode was not
                    # accessed since last modification. From 'manual.txt'
                    # of mutt 1.5.8:
                    #
                    # [ ... new mail is detected by comparing the last
                    # modification time to the last access time.
                    # Utilities like biff or frm or any other program
                    # which accesses the mailbox might cause Mutt to
                    # never detect new mail for that mailbox if they
                    # do not properly reset the access time.
                    # Backup tools are another common reason for updated
                    # access times. ]
                    #
                    self.utime(mbox_path, (s.st_atime, s.st_mtime))

                    # Remember size and time
                    #
                    self.mbox_size = s.st_size
                    self.mbox_mtime = s.st_mtime
                    
            # Uknown access method
            #
            else:
                raise RuntimeError('unknown access method `%s\'' %
                                   self.config['method'])
        except:
            # Exception handling: output a significant printout
            #
            size = -1
            print '='*80
            print traceback.print_exception(*self.exc_info())
            print '='*80
            print self.config
            print '='*80
            
        self.size = size
        return size


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

