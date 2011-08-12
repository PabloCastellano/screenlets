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
