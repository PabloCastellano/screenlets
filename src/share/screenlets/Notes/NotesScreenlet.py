#!/usr/bin/env python

#  NotesScreenlet (c) RYX (aka Rico Pfaus) 2007 <ryx@ryxperience.com>
#
# INFO:
# - a simple sticky note application
# 
# TODO:
# - !!fix crazy cursor movement on moving UP
# - !!fix missing/buggy key-handling
# - !!use clipping around cursor instead of full redraw
# - !!better handling of special-chars within text (on BACKSPACE)
# - try to get informed about end of begin_move_drag-operation
# - copy/paste
# - separate shadow into its own theme and add distance when picked up
# - maybe use another "paper" for the dragged-state
# - randomly rotate notes after they were "picked up"

import screenlets
from screenlets.options import IntOption, BoolOption, StringOption
from screenlets.options import FontOption, ColorOption

import gtk
import cairo
import pango
import sys
import random


class NotesScreenlet (screenlets.Screenlet):
	"""A sticky notes Screenlet with In-Place-Editing, support for Themes and 
	Pango-Markup compatibility (NOTE: still unfinished, but usable)."""
	
	# default meta-info for Screenlets
	__name__	= 'NotesScreenlet'
	__version__	= '0.5.2'
	__author__	= 'RYX (Rico Pfaus) 2007'
	__desc__	= __doc__
	
	# internal vars
	__editing		= True		# we are editing, show cursor
	__cursor_index	= 0			# current cursor position
	__pin_var_rot	= 0.0		# pin-rotation variation
	__pin_var_x		= 0.0		# pin x-position variation
	__pin_var_y		= 0.0		# pin y-position variation
	
	# TEST: experimental yet
	#__textlen	= 0				# length of entire text (excluding special chars!)
	#__lines		= [[0, '']]		# list with lists [line_length, line_text]
	#__curline	= 0				# current line (index in __lines)
	# /TEST
	
	# editable options
	pin_x		= 100
	pin_y		= 6
	text_x		= 19
	text_y		= 35
	font_name	= 'Sans Bold 12'
	rgba_color	= (0.0, 0.0, 1.0, 1.0)
	text_prefix	= ''
	text_suffix	= ''
	note_text	= ""	# hidden option because val has its own editing-dialog
	random_pin_pos	= True
	
	# constructor
	def __init__ (self, text="", **keyword_args):
		# call super (and init themes and drag/drop)
		screenlets.Screenlet.__init__(self, width=200, height=200, 
			uses_theme=True, drag_drop=True, **keyword_args) 
		# init attributes (not directly, that would cause redraw)
		self.__dict__['note_text'] = text
		self.__cursor_index = len(text)
		# init pango context/layout
		self.p_context = self.window.get_pango_context()
		if self.p_context:
			self.p_layout = pango.Layout(self.p_context)
			self.p_layout.set_font_description(\
				pango.FontDescription(self.font_name))
			self.__update_layout_width()
		# set theme (redraws canvas)
		self.theme_name = "default"
		# add menu-items
		self.add_menuitem("edit_text", "Edit...")
		self.add_menuitem("", "-")
		self.add_menuitem("copy", "Copy")
		self.add_menuitem("paste", "Paste")
		self.add_menuitem("", "-")
		self.add_menuitem("clear", "Clear")
		# add default menuitems
		self.add_default_menuitems()
		# add settings groups
		grp_txt	= self.create_option_group('Text ', 
			'Text-/Font-related settings for the sticknotes.')
		grp_lo	= self.create_option_group('Layout ', 
			'The Layout-related settings for the sticknotes..')
		# add editable options
		grp_lo.add_option(IntOption('pin_x', self.pin_x, 'X-Position of Pin', 
			'The X-Position of the tack/pin for the sticknote ...', 
			min=0, max=200))
		grp_lo.add_option(IntOption('pin_y', self.pin_y, 'Y-Position of Pin', 
			'The Y-Position of the tack/pin for the sticknote ...', 
			min=0, max=200))
		grp_lo.add_option(BoolOption('random_pin_pos', self.random_pin_pos, 
			'Randomize Pin', 'If active, the pin/tack will be slightly '+\
			'moved randomly whenever the note is picked up ...'))
		grp_txt.add_option(FontOption('font_name', self.font_name, 
			'Default Font', 'Default font of the text (without Markup) ...'))
		grp_txt.add_option(ColorOption('rgba_color', self.rgba_color, 
			'Default Color', 'Default color of the text (without Markup) ...'))
		grp_txt.add_option(IntOption('text_x', self.text_x, 'X-Position of Text', 
			'The X-Position of the text-rectangle\'s upper left corner ...', 
			min=0, max=200))
		grp_txt.add_option(IntOption('text_y', self.text_y, 'Y-Position of Text', 
			'The Y-Position of the text-rectangle\'s upper left corner ...', 
			min=0, max=200))
		grp_txt.add_option(StringOption('text_prefix', self.text_prefix, 
			'Text-Prefix', 'The text/Pango-Markup before the text ...'))
		grp_txt.add_option(StringOption('text_suffix', self.text_suffix, 
			'Text-Suffix', 'The text/Pango-Markup after the text ...'))
		# add hidden "note_text"-option (to save but not show in editor)
		grp_txt.add_option(StringOption('note_text', self.note_text, 
			'Note-Text', 'The text on this sticky note ...', hidden=True))
				
	def __setattr__ (self, name, value):
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# check attribute name
		if name == 'note_text':
			self.set_text (value)
		elif name == 'font_name':
			if value != '':
				self.p_layout.set_font_description(pango.FontDescription(value))
				self.redraw_canvas()
		elif name in ('width', 'height', 'pin_x', 'pin_y', 'text_x', 
			'text_y', 'text_suffix', 'text_prefix', 'random_pin_pos', 
			'rgba_color'):
			if name == 'text_x':
				# text position changed? update layout width
				self.__update_layout_width()
			elif name == 'text_prefix' or name == 'text_suffix':
				self.note_text = self.note_text	# update text to apply
			# redraw, if we have a window
			if self.window:
				self.redraw_canvas()
				self.update_shape()
	
	# "public" functions
	
	# TEMPORARY: should be fully replaced by real-time editing (sooner or later)
	def show_edit_dialog (self):
		# create dialog
		dialog = gtk.Dialog("Edit Note", self.window)
		dialog.resize(self.width, self.height)
		dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, 
			gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		# create textview
		textview = gtk.TextView()
		textview.set_wrap_mode(gtk.WRAP_WORD)
		textbuffer = gtk.TextBuffer()
		textbuffer.set_text(self.note_text)
		textview.set_buffer(textbuffer)
		dialog.vbox.add(textview)
		textview.show()
		# run dialog
		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			self.note_text = textbuffer.get_text(
				textbuffer.get_start_iter(), 
				textbuffer.get_end_iter())
		dialog.hide()
	
	def set_text (self, text):
		"""Set the text in the Notes, store the text length and call a redraw
		of the Screenlet's area."""
		self.p_layout.set_markup(self.text_prefix + text + self.text_suffix)
		self.__textlen = len(text)
		self.redraw_canvas()
	
	def clear_text (self):
		"""Clear the current note text."""
		self.note_text = ''
		self.__cursor_index = 0
		#print "CLEARED!"
		#print self.__textlen
	
	def insert_text (self, text):
		"""Insert the given string at the current position.
		TODO: generally check text for EOLs and special-chars here"""
		# set note text
		self.note_text = self.note_text[:self.__cursor_index] + text + \
			self.note_text[self.__cursor_index:]
		# and update cursor index
		self.__cursor_index += len(text)
	
	# parsing/text-handling
	
	def insert_backspace (self):
		"""Remove one char backwards from the current position."""
		if self.__cursor_index > 0:
			# remove char at cursor index - 1
			self.note_text = self.note_text[:self.__cursor_index-1] + \
				self.note_text[self.__cursor_index:]
			self.__cursor_index -= 1
			
	def insert_eol (self):
		"""Insert an EOL (linebreak) at the current position."""
		self.insert_text("\n")
	
	def get_last_eol (self):
		"""Find previous EOL from cursor position. Returns absolute position in
		text, not the distance in chars."""
		p = self.__cursor_index - 1
		while p > 0:
			if self.note_text[p] == '\n':
				return p
			p -= 1
		return 0
		
	def get_next_eol (self):
		"""Find next EOL from cursor position."""
		p = self.note_text.find('\n', self.__cursor_index)
		if p == -1 or p > self.__textlen - 1:
			return self.__textlen - 1
		return p
	
	def get_cursor_offset (self):
		"""Returns the offset (in chars) of the cursor from the beginning of the
		current line."""
		leol = self.get_last_eol()
		dist = self.__cursor_index - leol
		if dist > -1:
			return dist
		return 0
	
	# cursor movement
	
	def cursor_left (self):
		"""Move the cursor one line left and redraw.
		TODO: redraw only changed area."""
		if self.__cursor_index > 0:
			self.__cursor_index -= 1
			self.redraw_canvas()
				
	def cursor_up (self):
		"""Move the cursor one line up and redraw.
		TODO: redraw only changed area, fix weirdness."""
		self.__cursor_index = self.get_last_eol() - self.get_cursor_offset()
		if self.__cursor_index < 0:
			self.__cursor_index = 0
		self.redraw_canvas()
	
	def cursor_right (self):
		"""Move the cursor one line right and redraw.
		TODO: redraw only changed area."""
		if self.__cursor_index < len(self.note_text):
			self.__cursor_index += 1
			self.redraw_canvas()

	def cursor_down (self):
		"""Move the cursor one line down and redraw.
		TODO: redraw only changed area."""
		self.__cursor_index = self.get_next_eol() + self.get_cursor_offset()
		if self.__cursor_index >=  self.__textlen:
			self.__cursor_index = self.__textlen
		self.redraw_canvas()
	
	def cursor_home (self):
		"""Move the cursor to the beginning of the current line (last EOL)."""
		p = self.get_last_eol()
		if p > 0:
			self.__cursor_index = p
		else:
			self.__cursor_index = 0
		self.redraw_canvas()
	
	def cursor_end (self):
		"""Move the cursor to the end of the current line (next EOL)."""
		self.__cursor_index = self.get_next_eol()
		self.redraw_canvas()
		
	# internals
	
	def __update_layout_width (self):
		"""Update the width of the layout."""
		self.p_layout.set_width(((self.width - (self.text_x * 2)) * \
			pango.SCALE))
		self.p_layout.set_wrap(pango.WRAP_CHAR)
	
	# drawing
	
	def draw_pin (self, ctx):
		"""Draw the pin at its position to the given context."""
		ctx.translate(self.pin_x, self.pin_y)
		# add some variation?
		if self.random_pin_pos:
			ctx.rotate(self.__pin_var_rot)
			ctx.translate(self.__pin_var_x, self.__pin_var_y)
		# render pin
		ctx.set_operator (cairo.OPERATOR_OVER)
		if self.theme.loaded:
			#self.theme["note-pin.svg"].render_cairo(ctx)
			self.theme.render(ctx, 'note-pin')
	
	def draw_text (self, ctx):
		"""Draw the pango-layout to the given context."""
		ctx.save()
		ctx.translate(self.text_x, self.text_y)
		ctx.set_source_rgba(self.rgba_color[0], self.rgba_color[1], 
			self.rgba_color[2], self.rgba_color[3])
		ctx.show_layout(self.p_layout)
		ctx.fill()
		ctx.restore()
	
	def draw_cursor (self, ctx):
		"""Draw the cursor to the given context."""
		if self.__cursor_index > 0:
			cr		= self.p_layout.get_cursor_pos(self.__cursor_index)[1]
			cr_h	= cr[3] / pango.SCALE
		else:
			cr 		= (0, 0, 2, 16)
			cr_h	= 16		# workaround ...
		cr_w = 2
		cr_x = self.text_x + (cr[0] / pango.SCALE) - 1
		cr_x += cr[2] / pango.SCALE
		cr_y = self.text_y + (cr[1] / pango.SCALE)
		ctx.rectangle(cr_x, cr_y, cr_w, cr_h)
		#ctx.set_source_rgba(1, 1, 1, 0.7)
		ctx.fill()

	# screenlet event handlers
	
	def on_key_down (self, code, key, event):
		"""Handle keypress events, needed for in-place editing."""
		#print "Keyval: "+str(event.keyval)
		#print "Key: "+str(event.string)
		code = event.keyval
		# HTML-special chars? &, <, >
		if code == 38:
			self.insert_text('&amp;')
		elif code == 60:
			self.insert_text('&gt;')
		elif code == 62:
			self.insert_text('&lt;')
		# valid ascii char?
		elif code > 20 and code < 256:
			self.insert_text(event.string)
		# ENTER?
		elif code == 65293:
			self.insert_eol()
		# BACKSPACE?
		elif code == 65288:
			self.insert_backspace()
		# HOME? go to last EOL or pos -1
		elif code == 65360:
			self.cursor_home()
		# END?
		elif code == 65367:
			self.cursor_end()
		# LEFT-ARROW?
		elif code == 65361:
			self.cursor_left()
		# UP-ARROW?
		elif code == 65362:
			self.cursor_up()
		# RIGHT-ARROW?
		elif code == 65363:
			self.cursor_right()
		# DOWN-ARROW?
		elif code == 65364:
			self.cursor_down()
		#print "cursorIndex: "+str(self.__cursor_index)
	
	def on_drop (self, x, y, sel_data, timestamp):
		print "SOMETHING DROPPED!! TODO: ask for confirmation if text not empty"
		txt = sel_data.get_text()
		if txt != "":
			self.note_text += txt
	
	def on_focus (self, event):
		if self.__editing == False:
			self.__editing = True
			self.redraw_canvas()	# TODO: only redraw cursor area
	
	def on_unfocus (self, event):
		if self.__editing == True and self.is_dragged == False:
			self.__editing = False
			self.redraw_canvas()
	
	def on_menuitem_select (self, id):
		if id=="edit_text":
			self.show_edit_dialog()
		elif id == 'copy':
			print "TODO: copy to clipboard"
		elif id == 'clear':
			self.clear_text()
		elif id == 'paste':
			print "TODO: paste text from clipboard"
	
	def on_mouse_down (self, event):
		if event.button == 1:
			self.__pin_var_rot = (random.random()-0.5)/2
			self.__pin_var_x = random.random()
			self.__pin_var_y = random.random()
			self.redraw_canvas()
		return False
	
	# the drawing-handler, draws this Screenlet's background/visuals
	def on_draw (self, ctx):
		# set scale
		ctx.scale(self.scale, self.scale)
		# translate while dragging
		if self.is_dragged:
			ctx.translate(-5, -5)
		#else:
			#else, add a small randomized rotation
			#ctx.rotate((random.random()-0.5)/25)
			# TODO: resize window to fit after rotation
		# render bg
		ctx.set_operator (cairo.OPERATOR_OVER)
		if self.theme.loaded:
			#self.theme["note-bg.svg"].render_cairo(ctx)
			self.theme.render(ctx, 'note-bg')
		# render text
		self.draw_text(ctx)
		# draw cursor?
		if self.__editing:
			self.draw_cursor(ctx)
		# draw pin if not dragging
		if self.is_dragged == False:
			self.draw_pin(ctx)
	
	# this handler draws the Screenlets window-shape to make
	# the window-background click-through in transparent areas
	def on_draw_shape (self,ctx):
		#set scale
		ctx.scale(self.scale, self.scale)
		# just render bg
		if self.theme:
			#self.theme["note-bg.svg"].render_cairo(ctx)
			self.theme.render(ctx, 'note-bg')
	
	# other event handling
	
	# NOTE: self.is_dragged doesn't work properly .. this needs fixing
	def configure_event (self, widget, event):
		# if dragged before, redraw canvas
		if self.is_dragged==True:
			#print "Drag ended?"
			self.is_dragged=False
			self.redraw_canvas()
		# call super
		screenlets.Screenlet.configure_event(self, widget, event)
		return False
	

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(NotesScreenlet)

