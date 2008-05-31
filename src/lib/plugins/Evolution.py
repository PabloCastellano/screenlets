# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

#  Evolution api (c) Whise (Helder Fraga) 2008 <helder.fraga@hotmail.com>


def get_evolution_contacts():
	"""Returns a list of evolution contacts"""
	contacts = []

	try:
		import evolution
	except ImportError, err:
		print " !!!Please install python evolution bindings Unable to import evolution bindings:", err
	    	return None

	try:
		if evolution:
			for book_id in evolution.ebook.list_addressbooks():
				book = evolution.ebook.open_addressbook(book_id[1])
				if book:
					for contact in book.get_all_contacts():
					
						contacts.append(contact)
	except:
		if evolution:
			for book_id in evolution.list_addressbooks():
				book = evolution.open_addressbook(book_id[1])
				if book:
					for contact in book.get_all_contacts():
						
						contacts.append(contact)
                            
        return contacts
