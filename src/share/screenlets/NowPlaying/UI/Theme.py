import pango
import cairo
import gtk
import screenlets
import cairo
import string
import xml.dom.minidom

# The Main Skin Class
# It parses the xml and creates various UI items

class Skin:
	items = []
	width = 500
	height = 200
	name = ""

	playername_item = False
	albumcover_item = False
	titlename_item = False
	artistname_item = False
	albumname_item = False
	playercontrols_item = False
	
	def __init__(self, xmlfile, obj):
		self.parseSkinXML(xmlfile, obj.theme, obj.window, obj.player)
	
	def add_item(self, item):
		self.items.append(item)
	
	def cleanup(self):
		self.items[:] = []
		if self.playercontrols_item: 
			t = self.playercontrols_item
			t.remove_old()
			t.window.remove(t.window.get_child())

	def set_scale(self, scale):
		if self.playercontrols_item:
			self.playercontrols_item.set_scale(scale)

	def set_title(self, text):
		if self.titlename_item: self.titlename_item.set_text(text)

	def set_artist(self, text):
		if self.artistname_item: self.artistname_item.set_text(text)

	def set_album(self, text):
		if self.albumname_item: self.albumname_item.set_text(text)

	def set_player(self, text):
		if self.playername_item: 
			self.playername_item.set_text(text[:text.find("API")])

	def set_albumcover(self, pixbuf):
		if self.albumcover_item: self.albumcover_item.set_image(pixbuf)

	def parseSkinXML(self, filename, theme, window, player):
		dom = xml.dom.minidom.parse(filename)
		skinobj = dom.getElementsByTagName("skin")[0]
		self.name = skinobj.getAttribute("name")
		self.width = int(skinobj.getAttribute("width"))
		self.height = int(skinobj.getAttribute("height"))
		for domitem in skinobj.childNodes:
			if domitem.nodeType == 1:
				#print domitem
				type = domitem.nodeName
				x = int(domitem.getAttribute("x"))
				y = int(domitem.getAttribute("y"))
				w = domitem.getAttribute("width")
				h = domitem.getAttribute("height")
				display = domitem.getAttribute("display")
				if w: w = int(w)
				if h: h = int(h)
				
				item = False
				if type == "image":
					src = theme[domitem.getAttribute("src")]
					item = ImageItem(src, x, y, w, h, display)
				elif type == "albumcover":
					item = ImageItem(None, x, y, w, h, display)
					self.albumcover_item = item
				elif type in ("titlename", "artistname", "albumname", "playername"):
					font = domitem.getAttribute("font")
					color = domitem.getAttribute("color")
					shadowcolor = domitem.getAttribute("shadowcolor")
					align = domitem.getAttribute("align")
					maxchars = domitem.getAttribute("maxchars")
					direction = domitem.getAttribute("direction")
					scrollstr = domitem.getAttribute("scroll")
					scroll = False
					if scrollstr and (scrollstr=="1" or string.lower(scrollstr)=="true"):
						scroll = True
					item = TextItem("", font, color, x, y, scroll, display, shadowcolor, 
											  maxchars, align, direction, w, h)
					exec "self."+type+"_item = item"
				elif type == "playercontrols":
					xd = float(x)/self.width
					yd = float(y)/self.height
					spacing = domitem.getAttribute("spacing")
					item = PlayerControls(int(spacing), xd, yd, theme, window, player, display)
					for controlitem in domitem.childNodes:
						if controlitem.nodeType == 1: 
							cw = controlitem.getAttribute("width")
							ch = controlitem.getAttribute("height")
							ctype = controlitem.nodeName
							eval("item.add_%s(%s,%s)" %(ctype,cw,ch))
					self.playercontrols_item = item
				if item: self.items.append(item)


# A Generic UI Item
class GenericItem:
	type = ""
	x = 0
	y = 0
	width = 0
	height = 0
	display = True
	regular_updates = False

	def __init__(self, type, x, y, w, h, display):
		self.type = type
		self.x = x
		self.y = y
		self.width = w
		self.height = h
		if display: self.display = display

	def draw(self, ctx):
		pass



class ImageItem(GenericItem):
	imgobj = None
	image_type = None

	def __init__(self, imgobj, x, y, w, h, display):
		GenericItem.__init__(self, "image", x, y, w, h, display)
		self.set_image(imgobj)

	def set_image(self, imgobj):
		self.imgobj = imgobj
		cl = imgobj.__class__.__name__
		mod = imgobj.__class__.__module__
		if cl=='Handle': self.image_type = "rsvg"
		elif cl=='ImageSurface': self.image_type = "surface"
		elif cl=='Pixbuf': self.image_type = "pixbuf"
		else: self.image_type = None
		#print mod+", "+cl

	def draw(self, ctx):
		# Check for the type of the image object (rsvg, surface, pixbuf)
		# Draw accordingly
		if self.imgobj != None:
			if self.image_type == "rsvg":
				size=self.imgobj.get_dimension_data()
				if size:
					ctx.save()
					ctx.move_to(self.x,self.y)
					if self.width and self.height:
						ctx.scale(float(self.width)/size[0], float(self.height)/size[1])
					self.imgobj.render_cairo(ctx)
					ctx.restore()
			elif self.image_type == "surface":
				pattern = cairo.SurfacePattern(self.imgobj)
				matrix = cairo.Matrix()
				if self.width and self.height:
					iw = float(self.imgobj.get_width())
					ih = float(self.imgobj.get_height())
					matrix.scale(iw/self.width, ih/self.height)
				matrix.translate(-self.x, -self.y)
				pattern.set_matrix(matrix)
				ctx.set_source(pattern)
				ctx.paint()
			elif self.image_type == "pixbuf":
				ctx.save()
				pw = float(self.imgobj.get_width())
				ph = float(self.imgobj.get_height())
				ctx.translate(self.x, self.y)
				#if self.width and self.height:
				#	ctx.scale(self.width/pw, self.height/ph)
				#ctx.set_source_pixbuf(self.imgobj, 0, 0)
				pixscaled = self.imgobj
				if self.width and self.height:
					pixscaled = self.imgobj.scale_simple(self.width,self.height,1)
				ctx.set_source_pixbuf(pixscaled, 0, 0)
				ctx.paint()
				ctx.restore()


class TextItem(GenericItem):
	font = "Sans 10"
	text = ""
	align = ""
	color = (0,0,0,1)
	shadowcolor = False
	rotation = False
	layout = 0

	maxchars = False
	scroll_desired = False
	scrolling = False
	cur_index = 0
	scroll_wait = 10
	scrollfiller = "     "

	def __init__(self, text, font, color, x, y, scroll_desired=False, display="", 
					shadowcolor="", maxchars="", align="left", 
					direction = "", w=0, h=0):
		GenericItem.__init__(self, "text", x, y, w, h, display)
		if font: self.font = font
		if color: self.color = self.get_rgba(color)
		if shadowcolor: self.shadowcolor = self.get_rgba(shadowcolor)
		if maxchars: self.maxchars = int(maxchars)
		if direction: self.rotation = self.get_rotation_from_direction(direction)
		self.scroll_desired = scroll_desired
		self.align = align
		self.set_text(text)
	
	def set_text(self, text):
		#print "resetting text"
		self.cur_index = 0
		self.scrolling = False
		self.regular_updates = False
		if self.maxchars and len(text) > self.maxchars:
			if self.scroll_desired:
				self.regular_updates=True
				self.scrolling = True
			else:
				text = text[0:self.maxchars]+"..."
		self.text = text
	
	def draw(self, ctx):
		# Do some Pango Magic here
		# Draw Shadow Text
		text = self.text
		if self.scrolling:
			if self.cur_index > self.scroll_wait:
				text = self.text + self.scrollfiller + self.text
				tmp = self.cur_index - self.scroll_wait
				text = text[tmp:(tmp+ self.maxchars)]
			text = text[0:self.maxchars]
			#print text
			#print self.cur_index
			self.cur_index += 1
			if self.cur_index == len(self.text+self.scrollfiller)+self.scroll_wait: self.cur_index = 0
		ctx.save()
		if self.shadowcolor: 
			self.draw_text(ctx, text, self.shadowcolor, self.x+1, self.y+1)
		# Draw Text
		self.draw_text(ctx, text, self.color, self.x, self.y)
		ctx.restore()
	
	def draw_text(self, ctx, text, c, x, y):
		ctx.save()
		p_layout = ctx.create_layout()
		p_fdesc = pango.FontDescription(self.font)
		p_layout.set_font_description(p_fdesc)
		p_layout.set_text(text)
		# Clip Pixel Region
		self.set_clip_region(ctx, p_layout, x, y)
		if text: 
			(x,y) = self.get_xy_from_alignment(p_layout, x, y)
		ctx.move_to(x,y)
		if self.rotation:
			ctx.translate(-x,-y)
			#ctx.rotate(1.5)
			ctx.rotate(self.rotation)
		ctx.set_source_rgba(c[0],c[1],c[2],c[3])
		ctx.show_layout(p_layout)
		ctx.restore()

	def get_extents(self, p_layout):
		(extents, lextents) = p_layout.get_pixel_extents()
		return extents

	def get_xy_from_alignment(self, p_layout, x, y):
		if not self.width: return (x, y)
		extents = self.get_extents(p_layout)
		fw = extents[2]+extents[0]
		fh = extents[3]+extents[1]
		if self.align == "left":
			pass
		elif self.align == "center":
			if self.layout==0:
				x = x + self.width/2.0 - fw/2.0
			elif self.layout==1:
				y = y - self.width/2.0 + fw/2.0
			elif self.layout==2:
				x = x - self.width/2.0 + fw/2.0
			elif self.layout==3:
				y = y + self.width/2.0 - fw/2.0
		elif self.align == "right":
			if self.layout==0:
				x = x + self.width - fw
			elif self.layout==1:
				y = y - self.width + fw
			elif self.layout==2:
				x = x - self.width + fw
			elif self.layout==3:
				y = y + self.width - fw
		return (x, y)

	def set_clip_region(self, ctx, p_layout, x, y):
		extents = self.get_extents(p_layout)
		fw = extents[2]+extents[0]
		fh = extents[3]+extents[1]
		if self.width:
			if self.layout == 0:
				ctx.rectangle(x, y, self.width, fh)
			if self.layout == 1:
				ctx.rectangle(x, y-self.width, fh, self.width)
			if self.layout == 2:
				ctx.rectangle(x-self.width, y-fh, self.width, fh)
			if self.layout == 3:
				ctx.rectangle(x-fh, y, fh, self.width)
			#ctx.stroke()
			ctx.clip()

	def get_rgba(self, color):
		return (
			int(color[1:3], 16)/255.0,
			int(color[3:5], 16)/255.0,
			int(color[5:7], 16)/255.0,
			int(color[7:9], 16)/255.0
		)

	def get_rotation_from_direction(self, dir):
		PI = 3.141596
		if dir == "left-right":
			self.layout = 0
			return 0
		elif dir == "down-up":
			self.layout = 1
			return -PI*0.5
		elif dir == "right-left":
			self.layout = 2
			return PI
		elif dir == "up-down":
			self.layout = 3
			return PI*0.5
		return False



class PlayerButton(screenlets.ShapedWidget):
	width = 20
	height = 20

	image = None
	image_normal = None
	image_hover = None
	image_pressed = None

	callbackfn = None

	def __init__(self, w, h):
		super(PlayerButton, self).__init__(w,h)
		self.width = w
		self.height = h
        
	def set_callback_fn(self, fn):
		self.callbackfn = fn
	
	def set_images(self, image_normal, image_hover, image_pressed):
		self.image = image_normal
		self.image_normal = image_normal
		self.image_hover = image_hover
		self.image_pressed = image_pressed

	def button_press(self, widget, event):
		if event.button==1:
			self.image = self.image_pressed
			self.queue_draw()
		return True

	def button_release(self, widget, event):
		if event.button==1:
			self.image = self.image_normal
			self.queue_draw()
			if(self.callbackfn != None): self.callbackfn()
		return False

	def enter_notify(self, widget, event):
		self.image = self.image_hover
		self.queue_draw()
		#print "mouse enter"

	def leave_notify(self, widget, event):
		self.image = self.image_normal
		self.queue_draw()
		#print "mouse leave"
	
	def draw(self, ctx):
		if(self.image != None):
			iw = float(self.image.get_width())
			ih = float(self.image.get_height())
			matrix = cairo.Matrix(xx=iw/self.width, yy=ih/self.height)
			pattern = cairo.SurfacePattern(self.image)
			pattern.set_matrix(matrix)
			ctx.move_to(0,0)
			ctx.set_source(pattern)
			ctx.paint()


class PlayerControls:
	type = "playercontrols"

	box = False
	window = False
	theme = False
	player = False

	prev_button = False
	play_pause_button = False
	next_button = False
	
	display = True
	dims = [0,0,0,0,0,0] # prev width, prev height, play_pause width ....

	def __init__(self, spacing, xratio, yratio, theme, window, player, display, w=0, h=0):
		self.box = gtk.HBox(spacing=spacing)
		alignment = gtk.Alignment(xalign=xratio, yalign=yratio)
		alignment.add(self.box)
		self.theme = theme
		self.window = window
		self.player = player
		self.window.add(alignment)
		if display: self.display = display
	
	def set_images(self, btnimg, img):
		eval("self.%s_button.set_images(self.theme['%s.png'], self.theme['%s-hover.png'], self.theme['%s-pressed.png'])" %(btnimg, img, img, img))

	def add_prev(self, w, h):
		self.add_prev_t(w, h)
		self.dims[0]=w; self.dims[1]=h
		if screenlets.Screenlet.has_started:self.window.show_all()

	def add_prev_t(self, w, h):
		self.prev_button=PlayerButton(w,h)
		self.set_images("prev", "prev")
		self.box.add(self.prev_button)
	
	def add_play_pause(self, w, h):
		self.add_play_pause_t(w, h)
		self.dims[2]=w; self.dims[3]=h
		if screenlets.Screenlet.has_started:self.window.show_all()

	def add_play_pause_t(self, w, h):
		self.play_pause_button=PlayerButton(w,h)
		image = "play"
		if self.player and self.player.is_playing(): image = "pause"
		self.set_images("play_pause", image)
		self.box.add(self.play_pause_button)
	
	def add_next(self, w, h):
		self.add_next_t(w, h)
		self.dims[4]=w; self.dims[5]=h
		if screenlets.Screenlet.has_started:self.window.show_all()

	def add_next_t(self, w, h):
		self.next_button=PlayerButton(w,h)
		self.set_images("next", "next")
		self.box.add(self.next_button)

	def remove_old(self):
		if self.box:
			for oldwidget in self.box.get_children(): 
				self.box.remove(oldwidget)

	def set_scale(self, scale):
		self.remove_old()
		b = self.dims
		if self.prev_button: 
			tmp = self.prev_button
			fn = tmp.callbackfn
			self.add_prev_t(int(b[0]*scale), int(b[1]*scale))
			self.prev_button.set_callback_fn(fn)
			tmp.destroy()
		if self.play_pause_button: 
			self.play_pause_button.scale = scale
			tmp = self.play_pause_button
			fn = tmp.callbackfn
			self.add_play_pause_t(int(b[2]*scale), int(b[3]*scale))
			self.play_pause_button.set_callback_fn(fn)
			tmp.destroy()
		if self.next_button: 
			self.next_button.scale = scale
			tmp = self.next_button
			fn = tmp.callbackfn
			self.add_next_t(int(b[4]*scale), int(b[5]*scale))
			self.next_button.set_callback_fn(fn)
			tmp.destroy()
		if screenlets.Screenlet.has_started:self.window.show_all()

	def draw(self, ctx):
		if screenlets.Screenlet.has_started:self.window.show_all()


