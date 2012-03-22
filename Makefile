#-------------------------------------------------------------------------------
# Screenlets (c) RYX (aka Rico Pfaus) 2007-2009 <ryx@ryxperience.com>
# 
# [for full list of authors see file AUTHORS]
#-------------------------------------------------------------------------------
#
# A simple makefile to allow installing/uninstalling screenlets and performing
# other actions like creating a source-package or documentation.
#

VERSION		= `cat VERSION`
PREFIX		= /usr
INSTALL_LOG	= install.log

.PHONY : docs
.PHONY : uninstall

all:
	@echo "Makefile: Available actions: install, uninstall, clean, docs, source_package"

# install
install:
	-mkdir /etc/screenlets
	@echo $(PREFIX) > /etc/screenlets/prefix
	@echo $(VERSION) > /etc/screenlets/version
	python setup.py install --record=$(INSTALL_LOG) --prefix=$(PREFIX)
	cp desktop-menu/screenlets-daemon.desktop $(HOME)/.config/autostart

# uninstall
uninstall:
	rm -rf $(shell cat $(INSTALL_LOG))
	rm -rf /etc/screenlets
	rm -f $(INSTALL_LOG)
	rm -f $(HOME)/.config/autostart/screenlets-daemon.desktop
	@echo "Makefile: Screenlets removed."

# remove temporary files created by install
# note: this does not remove the install log
clean:
	python setup.py clean
	rm -rf dist
	rm -rf build
	@echo "Makefile: Temporary files have been removed."

# echo documentation options
docs:
	@echo "Available documentation: doxydoc, pydoc, and epydoc."
	@echo "To generate doxydoc documentation (recommended) please run:"
	@echo "	make doxydoc"

# create API-documentation (using doxgen)
doxydoc:
	doxygen doxygen.conf

# create API-documentation (using pydoc)
pydoc:
	make -C docs

# create API-documentation (using epydoc)
epydoc:
	epydoc --html --output=docs/epydoc --name="Screenlets $(VERSION)" screenlets screenlets.backend screenlets.drawing screenlets.install screenlets.menu screenlets.options screenlets.Plugins screenlets.session screenlets.services screenlets.sensors screenlets.utils screenlets.plugins.Amarok screenlets.plugins.AmazonCoverArtSearch screenlets.plugins.Banshee screenlets.plugins.CoverSearch screenlets.plugins.Exaile screenlets.plugins.GenericPlayer screenlets.plugins.iCal screenlets.plugins.keyring screenlets.plugins.Listen screenlets.plugins.Loader screenlets.plugins.Mail screenlets.plugins.Mplayer screenlets.plugins.Proxy screenlets.plugins.Quodlibet screenlets.plugins.Rhythmbox screenlets.plugins.Sonata screenlets.plugins.Songbird

# create API-documentation
menu:
	make -C desktop-menu
	
# build a source-release
source_package:
	python setup.py sdist --formats=bztar
	@echo "Makefile: Source-package is ready and waiting in ./dist ..."

