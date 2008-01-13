#!/usr/bin/env python

#  ExampleScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - a simple example for creating a Screenlet
# 
# TODO:
# - make a nice Screenlet from ths example

import screenlets
from screenlets.options import StringOption
import cairo
import pango
import gtk
import string

class CalcScreenlet(screenlets.Screenlet):
	
	# default meta-info for Screenlets
	__name__ = 'CalcScreenlet'
	__version__ = '0.0.2'
	__author__ = 'Cobra'
	__desc__ = 'A simple Calc screenlet inspired on the equiv. OSX widget'

	# editable options
	num = [""]
	oper = []

	button_value = ''
	m = 0
	
	has_focus = False

	xscale = 2
		
	# constructor
	def __init__(self, **keyword_args):
		#call super
		screenlets.Screenlet.__init__(self, width=200, height=320, 
			**keyword_args)
		# set theme
		self.theme_name = "default"
		self.window.connect("key-press-event", self.key_press)
		self.window.connect("key-release-event", self.key_release)
		self.window.connect("focus-in-event", self.focus_in)
		self.window.connect("focus-out-event", self.focus_out)

	def on_init (self):
		print "Screenlet has been initialized."
		# add default menuitems
		self.add_default_menuitems()	
		
	def focus_in(self, widget, event):
		self.has_focus = True
		self.redraw_canvas()
	
	def focus_out(self, widget, event):
		self.has_focus = False
		self.redraw_canvas()
	
	def on_draw_shape(self, ctx):
		self.on_draw(ctx)
	
	def on_draw(self, ctx):
		# if theme is loaded
		#ctx.scale(self.width/100.0, self.width/100.0)
		ctx.scale(self.xscale, 2)
		ctx.save()

		if self.theme:
			# render the file we want
			self.theme['calc-bg-shape.svg'].render_cairo(ctx)
			if self.has_focus or self.is_dragged:
				self.theme['calc-screen-on.svg'].render_cairo(ctx)
			else:
				self.theme['calc-screen-off.svg'].render_cairo(ctx)

		ctx.restore()

		self.draw_button(ctx, '7', '7', 5 , 60, 1)
		self.draw_button(ctx, '8', '8', 28, 60, 1)
		self.draw_button(ctx, '9', '9', 51, 60, 1)

		self.draw_button(ctx, '4', '4', 5 , 83, 1)
		self.draw_button(ctx, '5', '5', 28, 83, 1)
		self.draw_button(ctx, '6', '6', 51, 83, 1)

		self.draw_button(ctx, '1', '1', 5 , 106, 1)
		self.draw_button(ctx, '2', '2', 28, 106, 1)
		self.draw_button(ctx, '3', '3', 51, 106, 1)

		self.draw_button(ctx, '0', '0', 5 , 129, 1)
		self.draw_button(ctx, 'period', '.', 28, 129, 1)
		self.draw_button(ctx, 'Delete', 'C', 51, 129, 1)

		self.draw_button(ctx, 'm+', 'm+', 8, 60, 0.7)
		self.draw_button(ctx, 'm-', 'm-', 32, 60, 0.7)
		self.draw_button(ctx, 'mc', 'mc', 56, 60, 0.7)
		self.draw_button(ctx, 'mr', 'mr', 80, 60, 0.7)

		self.draw_button(ctx, 'slash', 'calc-div.svg', 108, 60, 0.7, True)
		self.draw_button(ctx, 'asterisk', 'calc-aste.svg', 108, 87, 0.7, True)
		self.draw_button(ctx, 'minus', 'calc-minus.svg', 108, 114, 0.7, True)
		self.draw_button(ctx, 'plus', 'calc-plus.svg', 108, 141, 0.7, True)
		if self.get_current()=="" and self.peek_oper()!="":
			if self.peek_oper()=="/":
				self.draw_button(ctx, 'slash', 'calc-div-white.svg', 108, 60, 0.7, True, False, True)
			elif self.peek_oper()=="*":
				self.draw_button(ctx, 'asterisk', 'calc-aste-white.svg', 108, 87, 0.7, True, False, True)
			elif self.peek_oper()=="-":
				self.draw_button(ctx, 'minus', 'calc-minus-white.svg', 108, 114, 0.7, True, False, True)
			elif self.peek_oper()=="+":
				self.draw_button(ctx, 'plus', 'calc-plus-white.svg', 108, 141, 0.7, True, False, True)

		self.draw_button(ctx, 'equal', 'calc-equal.svg', 108, 169, 0.7, True, True)

		#if self.operation != '+' or self.last != 0:
		if self.get_current()=="" and self.peek_oper()!="":
			all = self.get_all_but_one(False)
		else:
			all = self.get_all_but_one()
		current = self.get_current()
		if (len(str(current))>11): current = "%g"%float(current)
		#if current=="": current="0"
		#self.draw_text(ctx, '<b>' + all + '</b>', 93-5*len(all), 5, 6)
		#self.draw_text(ctx, '<b>' + current + '</b>', 93-8*len(current), 13, 10)
		self.draw_text(ctx, '<b>' + all + '</b>', 5, 5, 6)
		self.draw_text(ctx, '<b>' + current + '</b>', 5, 13, 10)		

	def draw_text(self, ctx, value, x, y, size):
		ctx.save()
		ctx.translate(x, y)
		p_layout = ctx.create_layout()
		p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static("Free Mono")
		p_fdesc.set_size(size * pango.SCALE)
		p_layout.set_font_description(p_fdesc) 
		#p_layout.set_width((self.width) * pango.SCALE)
		p_layout.set_width(88 * pango.SCALE)
		p_layout.set_alignment(pango.ALIGN_RIGHT)
		p_layout.set_markup(value)
		ctx.set_source_rgba(0, 0, 0.6, 0.5)
		ctx.show_layout(p_layout)
		p_layout.set_alignment(pango.ALIGN_LEFT)
		ctx.restore()
	
	def draw_button(self, ctx, evt, value, x, y, ratio, with_svg_face=False, is_large=False, is_on_click=False):
		ctx.save()
		ctx.scale(ratio, ratio)
		ctx.translate(x, y)
		if self.theme:
			if is_on_click:
				self.theme['calc-button-clk.svg'].render_cairo(ctx)
			else:
				if self.button_value == evt:
					if is_large:
						self.theme['calc-button-large-on.svg'].render_cairo(ctx)
					else:
						self.theme['calc-button-on.svg'].render_cairo(ctx)
				else:
					if is_large:
						self.theme['calc-button-large-off.svg'].render_cairo(ctx)
					else:
						self.theme['calc-button-off.svg'].render_cairo(ctx)
		if with_svg_face and self.theme:
			self.theme[value].render_cairo(ctx)
		else:
			ctx.translate(8.5*ratio, 7)
			p_layout = ctx.create_layout()
			p_fdesc = pango.FontDescription()
			p_fdesc.set_family_static("Free Sans")
			p_fdesc.set_size(6 * pango.SCALE)
			p_layout.set_font_description(p_fdesc)
			p_layout.set_width((self.width) * pango.SCALE)
			p_layout.set_markup('<b>'+value+'</b>')
			ctx.set_source_rgba(0, 0, 0, 0.5)
			ctx.show_layout(p_layout)
		ctx.restore()


	def button_press(self, widget, event):
		#print "Button press"+str(event.button)
		if event.type != gtk.gdk.BUTTON_PRESS:
			return False

		if event.button == 1:
			if not self.detect_button_action(event.x_root-self.x, event.y_root-self.y):
				self.is_dragged = True
				widget.begin_move_drag (event.button, 
					int(event.x_root), int(event.y_root), event.time)
		elif event.button == 3:
			self.menu.popup(None, None, None, event.button, 
				event.time)
		
		return False

	def button_release(self, widget, event):
		if event.button==1 and self.button_value is not '':
			self.button_value = ''
			self.redraw_canvas()
		return False

	def draw_shape(self, ctx):
		self.draw(ctx)
	
		
	
	def detect_button_action(self, x, y):
		scale = int(self.width/100)
		#print "Action:: "+str(x/scale)+" : "+str(y/scale)
		# nx, ny : used for main buttons detection
		tab_main = [ ['7', '4', '1', '0'], ['8', '5', '2', 'period'] , ['9', '6', '3', 'Delete'] ]
		rx = x/scale
		ry = y/scale
		#print str(rx)+" : "+str(ry)
		action = False

		if rx>=77 and rx<=90:
			action = True
			if ry>=43 and ry<=56:
				self.maj_result("slash")
			elif ry>=62 and ry<=75:
				self.maj_result("asterisk")
			elif ry>=81 and ry<=94:
				self.maj_result("minus")
			elif ry>=100 and ry<=113:
				self.maj_result("plus")
			elif ry>=119 and ry<=149:
				self.maj_result("equal")
			else:
				action=False
		elif ry>=43 and ry<=56:
			action = True
			if rx>=7 and rx<=19.5:
				self.maj_result("m+")
			elif rx>=24 and rx<=36:
				self.maj_result("m-")
			elif rx>=40.5 and rx<=53:
				self.maj_result("mc")
			elif rx>=57.5 and rx<=70:
				self.maj_result("mr")
			else:
				action = False
		else:
			action = False
			nx = x/scale - 6;
			ny = y/scale - 60;
			wi = nx%23;
			if wi <= 21:
				mx = int(nx/23+1)
				my = int(ny/23+1)
				if mx>=1 and mx<=3 and my>=1 and my<=4:
					self.maj_result(tab_main[mx-1][my-1])
					#print "Button pressed : "+ self.button_value
					self.redraw_canvas()
					action = True

		#print "action="+str(action)
		return action

	def maj_result(self, value):
		import re
		
		self.button_value = value
		#print value
		if re.match ("[0-9]", value):
			if len(self.num[-1])<11:
				self.push_num(value)
		elif re.match ("period|comma", value):
			if self.get_current().find(".")==-1:
				self.push_num(".")
		elif re.match ("plus|[+]|minus|[-]|asterisk|[*]|slash|[/]", value) and self.get_current()!="":
			if value=="plus":
				value="+"
			elif value=="minus":
				value="-"
			elif value=="asterisk":
				value="*"
			elif value=="slash":
				value="/"
			if self.peek_oper()=="*" or self.peek_oper()=="/":
				# we allow "reverse polish" compute
				self.compute_polish()
			self.push_oper(value)
		elif re.match ("equal|Return", value):
			if self.get_current() is not "":
				self.compute()
		elif re.match ("Delete|BackSpace", value):
			# two level delete
			if self.get_current() is not "":
				# CE mode
				self.num[-1] = ""
			else:
				# C mode
				self.purge()
		elif value=="m+":
			self.mp()
		elif value=="m-":
			self.mm()
		elif value=="mc":
			self.mc()
		elif value=="mr":
			self.mr()
			
	def get_all_but_one(self, with_oper=True):
		s = ""
		for i in range(len(self.oper)):
			s += self.num[i]
			if i<len(self.oper)-1 or with_oper:
				s += self.oper[i]
		return s

	def mp(self):
		self.m += float(self.get_current())
	
	def mm(self):
		self.m -= float(self.get_current())
	
	def mc(self):
		self.m = 0
	
	def mr(self):
		if self.m==int(self.m): self.m=int(self.m)
		self.num[-1] = str(self.m)

	def get_all(self):
		return self.get_all_but_one(True)+self.num[-1]
		
	def get_current(self):
		if len(self.num)==0: cur =  ""
		cur = self.num[-1]
		#print "current::"+cur
		return cur

	def purge(self):
		self.num = [""]
		self.oper = []

	def compute(self):
		while len(self.oper)>0:
			#print "=== "+self.get_all()
			self.compute_one()
		if self.num[-1]=="0": self.num[-1]=""

	def compute_one(self):
		result = 0
		left = float(self.num[0])
		right = float(self.num[1])
		oper = self.oper[0]
		#print "compute "+str(len(self.oper))+" : "+str(left)+oper+str(right)
		if oper=="+":
			result = result + (left + right)
		elif oper=="-":
			result = result + (left - right)
		elif oper=="*":
			result = result + (left * right)
		elif oper=="/":
			result = result + (left / right)
		if float(result)==int(result): result=int(result)
		del self.num[0]
		self.num[0] = str(self.numerize(result))

		if float(self.num[0])==round(float(self.num[0])): 
			self.num[0] = self.num[0].split(".")[0]


		del self.oper[0]
		#self.num.append(str(result))
	
	def numerize(self, f):
		s = str(f)
		if len(s)>11:
			#print "numerize from "+s
			# We have to reduce the size of the result to 11 caracters
			is_float = (s.find(".")!=-1)
			if is_float:
				f_len = 11-s.find(".")-1
				#print "arrondi sur : "+str(f_len)
				s = "%."+str(f_len)+"f"
				s = s%f
		return float(s)

	def compute_polish(self):
		result = 0
		right = float(self.num.pop())
		left = float(self.num.pop())
		oper = self.oper.pop()
		#print "compute "+str(len(self.oper))+" : "+str(left)+oper+str(right)
		if oper=="+":
			result = result + (left + right)
		elif oper=="-":
			result = result + (left - right)
		elif oper=="*":
			result = result + (left * right)
		elif oper=="/":
			result = result + (left / right)
		if float(result)==int(result): result=int(result)
		self.num.append(str(result))

	def push_num(self, num):
		self.num[-1] += num
		return self.num[-1]
	
	def peek_oper(self):
		if len(self.oper)==0: return ""
		return self.oper[-1]
		
	def push_oper(self, oper):
		self.oper.extend(oper)
		self.num.append("")
		return False

	def pop_num(self):
		return self.num.pop()

	def pop_oper(self):
		return self.oper.pop()
	
	def key_press(self, widget, event):
		import re
		
		key = gtk.gdk.keyval_name (event.keyval)
		KPCONVERT = {'KP_Add': 'plus', 'KP_Subtract': 'minus', 'KP_Multiply': 'asterisk',
						'KP_Divide': 'slash', 'KP_Enter': 'Return'}
		if KPCONVERT.has_key(key):
				key = KPCONVERT[key]
		elif key[:3] == 'KP_':
				key = key[3:]
		ONLYDIGITS="([0-9]|comma|period|plus|minus|BackSpace|Delete|Return|asterisk|slash|equal)"
		if re.match (ONLYDIGITS, key):
			#print "Key Pressed : "+key
			self.maj_result(key)
			self.redraw_canvas()

		return False
	def key_release(self, widget, event):
		if self.button_value is not '':
			self.button_value = ''
			self.redraw_canvas()
		return False

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	import screenlets.session
	screenlets.session.create_session(CalcScreenlet)
