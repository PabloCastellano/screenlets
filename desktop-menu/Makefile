# This makefile installs all .desktop-files and the menu/directory-files
# required for adding the screenlets to the main menu. I am unsure how or if
# this works on KDE-systems, so I named this folder "gnome" for now.

# TODO: check if XDG is available
XDG_DATA_DIRS=/usr/share

# install menu and desktop files
install:
	cp $(HOME)/.config/menus/applications.menu $(HOME)/.config/menus/applications.menu.bak
	@echo "Makefile: Backed up old applications.menu in $(HOME)/.config/menus/"
	cp applications.menu $(HOME)/.config/menus
	cp applications/* $(XDG_DATA_DIRS)/applications
	cp desktop-directories/* $(XDG_DATA_DIRS)/desktop-directories
	@echo "Makefile: The Screenlets should now have their own submenu in your Applications-menu ..."

