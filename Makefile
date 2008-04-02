#-------------------------------------------------------------------------------
#  Screenlets - (c) 2007 by RYX (aka Rico Pfaus) <ryx@ryxperience.com>
#-------------------------------------------------------------------------------
#
# only a simple makefile to allow installing screenlets (and performing some
# other actions like creating a source-package or the documentation)
#

all:
	@echo "Makefile: Available actions: install, clean, docs, source_package"

# install the Screenlets
install:
	python setup.py install
	cp desktop-menu/screenlets.svg /usr/share/icons
	cp desktop-menu/screenlets-manager.desktop /usr/share/applications
	cp desktop-menu/screenlets-daemon.desktop $(HOME)/.config/autostart

# uninstall the Screenlets (NOT FINISHED)
uninstall:
	rm -rf /usr/local/share/screenlets*
	rm -rf /usr/local/bin/screenlets*
	rm -rf /usr/lib/python2.4/site-packages/screenlets*
	rm -rf /usr/lib/python2.5/site-packages/screenlets*
	rm -r /usr/share/screenlets
	rm -r /usr/share/screenlets-manager
	rm /usr/bin/screenlets*
	rm /usr/share/icons/screenlets.svg
	@echo "Makefile: Uninstall of python-libs not supported yet ..."
	@echo "          To uninstall, run 'rm -rf /usr/lib/python2.x/site-packages/screenlets*'"
	@echo "          Replace '2.x' with your installed python version (e.g. '2.5')"

# remove all files created by install
clean:
	python setup.py clean
	rm -r dist
	rm -r build
	rm MANIFEST
	@echo "Makefile: Temporary files have been removed ..."

# create API-documentation (using doxgen)
doxydoc:
	doxygen doxygen.conf

# create API-documentation (using pydoc)
pydoc:
	make -C docs

# create API-documentation (using epydoc)
epydoc:
	epydoc --html --output=docs/epydoc --name="Screenlets 0.1" screenlets screenlets.backend screenlets.options screenlets.utils screenlets.session screenlets.services screenlets.sensors

# create API-documentation
menu:
	make -C desktop-menu
	
# build a source-release
source_package:
	python setup.py sdist --formats=bztar
	@echo "Makefile: Source-package is ready and waiting in ./dist ..."

