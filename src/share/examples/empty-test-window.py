import gtk
#from gobject import GObject

# A simple testbed
#


# testing app class
class TestApp:

	def __init__ (self):
		self.win = gtk.Window()
		self.win.show()
		self.win.connect('delete-event', self.handle_delete)
		
	def start (self):
		gtk.main()
	
	def handle_delete (self, window, event):
		print "Bye!"
		gtk.main_quit()

# TEST
app = TestApp()
app.start()

