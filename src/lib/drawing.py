# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# Screenlets Drawing Helder Fraga aka Whise <helder.fraga@hotmail.com>


import gtk, cairo, pango, math

class Drawing:
	"""Contains static drawing functions."""
	
	@staticmethod
	def clear_cairo_context (ctx):
		"""Fills the given cairo.Context with fully transparent white."""
		ctx.save()
		ctx.set_source_rgba(1, 1, 1, 0)
		ctx.set_operator (cairo.OPERATOR_SOURCE)
		ctx.paint()
		ctx.restore() 
	
	@staticmethod
	def get_text_width(ctx, text, font, p_layout=None, p_fdesc=None):
		"""Returns the pixel width of a given text"""
		return Drawing.get_text_extents(ctx, text, font, p_layout, p_fdesc)[2]

	@staticmethod
	def get_text_extents(ctx, text, font, p_layout=None, p_fdesc=None):
		"""Returns the pixel extents of a given text"""
		ctx.save()
		
		if p_layout is None:
			p_layout = ctx.create_layout()
		else:
			ctx.update_layout(p_layout)
			
		if p_fdesc is None:
			p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static(font)
		p_layout.set_font_description(p_fdesc)
		p_layout.set_text(text)
		extents, lextents = p_layout.get_pixel_extents()
		ctx.restore()
		return extents
	
	@staticmethod
	def get_text_line_count(ctx, text, font, p_layout=None, p_fdesc=None): 	
		"""Returns the line count of a given text""" 	
		ctx.save() 	
		
		if p_layout is None : 	
			p_layout = ctx.create_layout() 	
		else: 	
			ctx.update_layout(p_layout) 
				
		if p_fdesc is None:
			p_fdesc = pango.FontDescription() 	
			
		p_fdesc.set_family_static(font) 	
		p_layout.set_font_description(p_fdesc) 	
		p_layout.set_text(text) 	
		ctx.restore() 	
		return p_layout.get_line_count()
	
	@staticmethod
	def get_text_line(ctx, text, font, line, p_layout=None, p_fdesc=None): 	
		"""Returns a line of a given text""" 	
		ctx.save() 	
		# create the pango layout
		if p_layout is None : 	
			p_layout = ctx.create_layout() 	
		else: 	
			ctx.update_layout(p_layout) 
		# create the pango font description
		if p_fdesc is None:
			p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static(font) 	
		p_layout.set_font_description(p_fdesc) 	
		p_layout.set_text(text) 	
		ctx.restore() 	
		return p_layout.get_line(line)
	
	@staticmethod
	def check_for_icon(icon):
		try:
			icontheme = gtk.icon_theme_get_default()
			image = icontheme.load_icon (icon,32,32)
			return True
		except:
			return False

	@staticmethod
	def draw_text(ctx, text, x, y, font, size, width, allignment=pango.ALIGN_LEFT,
		justify=False, weight=0, ellipsize=pango.ELLIPSIZE_NONE, p_layout=None, p_fdesc=None):
		"""Draws text"""
		ctx.save()
		ctx.translate(x, y)
		if p_layout is None :
			p_layout = ctx.create_layout()
		else:
			ctx.update_layout(p_layout)
		if p_fdesc is None:
			p_fdesc = pango.FontDescription()
		p_fdesc.set_family_static(font)
		p_fdesc.set_size(size * pango.SCALE)
		p_fdesc.set_weight(weight)
		p_layout.set_font_description(p_fdesc)
		p_layout.set_width(width * pango.SCALE)
		p_layout.set_alignment(allignment)
		p_layout.set_justify(justify)
		p_layout.set_ellipsize(ellipsize)
		p_layout.set_markup(text)
		ctx.show_layout(p_layout)
		ctx.restore()

	@staticmethod
	def draw_circle(ctx,x,y,width,height,fill=True):
		"""Draws a circule"""
		ctx.save()
		ctx.translate(x, y)
		ctx.arc(width/2,height/2,min(height,width)/2,0,2*math.pi)
		if fill: ctx.fill()
		else: ctx.stroke()
		ctx.restore()

	@staticmethod
	def draw_triangle(ctx,x,y,width,height,fill=True):
		"""Draws a circule"""
		ctx.save()
		ctx.translate(x, y)
		ctx.move_to(width-(width/3), height/3)
		ctx.line_to(width,height)
		ctx.rel_line_to(-(width-(width/3)), 0)
		ctx.close_path()
		if fill: ctx.fill()
		else: ctx.stroke()
		ctx.restore()

	@staticmethod
	def draw_line(ctx,start_x,start_y,end_x,end_y,line_width = 1,close=False,preserve=False):
		"""Draws a line"""
		ctx.save()
		ctx.move_to(start_x, start_y)
		ctx.set_line_width(line_width)
		ctx.rel_line_to(end_x, end_y)
		if close: ctx.close_path()
		if preserve: ctx.stroke_preserve()
		else: ctx.stroke()
		ctx.restore()

	@staticmethod
	def draw_rectangle(ctx,x,y,width,height,fill=True):
		"""Draws a rectangle"""
		ctx.save()
		ctx.translate(x, y)
		ctx.rectangle (0,0,width,height)
		if fill:ctx.fill()
		else: ctx.stroke()
		ctx.restore()
	
	@staticmethod
	def draw_rectangle_advanced (ctx, x, y, width, height, rounded_angles=(0,0,0,0),
		fill=True, border_size=0, border_color=(0,0,0,1), shadow_size=0, shadow_color=(0,0,0,0.5)):
		"""Draws a rectangle with several extra options.
		TODO: Rewrite and compact this function!"""
		ctx.save()
		ctx.translate(x, y)
		s = shadow_size
		w = width
		h = height
		rounded = rounded_angles
		if shadow_size > 0:
			ctx.save()
			
			#top shadow
			gradient = cairo.LinearGradient(0,s,0,0)
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.rectangle(s+rounded[0],0, w-rounded[0]-rounded[1], s)
			ctx.fill()

			#bottom
			gradient = cairo.LinearGradient(0, s+h, 0, h+(s*2))
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.rectangle(s+rounded[2], s+h, w-rounded[2]-rounded[3], s)
			ctx.fill()

			#left
			gradient = cairo.LinearGradient(s, 0, 0, 0)
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.rectangle(0, s+rounded[0], s, h-rounded[0]-rounded[2])
			ctx.fill()

			#right
			gradient = cairo.LinearGradient(s+w, 0, (s*2)+w, 0)
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.rectangle(s+w, s+rounded[1], s, h-rounded[1]-rounded[3])
			ctx.fill()
			ctx.restore

			#top-left
			gradient = cairo.RadialGradient(s+rounded[0], s+rounded[0], rounded[0], s+rounded[0], s+rounded[0], s+rounded[0])
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.new_sub_path()
			ctx.arc(s,s,s, -math.pi, -math.pi/2)
			ctx.line_to(s+rounded[0],0)
			ctx.line_to(s+rounded[0],s)
			ctx.arc_negative(s+rounded[0],s+rounded[0],rounded[0], -math.pi/2, math.pi)
			ctx.line_to(0, s+rounded[0])
			ctx.close_path()
			ctx.fill()

			#top-right
			gradient = cairo.RadialGradient(w+s-rounded[1], s+rounded[1], rounded[1], w+s-rounded[1], s+rounded[1], s+rounded[1])
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.new_sub_path()
			ctx.arc(w+s,s,s, -math.pi/2, 0)
			ctx.line_to(w+(s*2), s+rounded[1])
			ctx.line_to(w+s, s+rounded[1])
			ctx.arc_negative(w+s-rounded[1], s+rounded[1], rounded[1], 0, -math.pi/2)
			ctx.line_to(w+s-rounded[1], 0)
			ctx.close_path()
			ctx.fill()

			#bottom-left
			gradient = cairo.RadialGradient(s+rounded[2], h+s-rounded[2], rounded[2], s+rounded[2], h+s-rounded[2], s+rounded[2])
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.new_sub_path()
			ctx.arc(s,h+s,s, math.pi/2, math.pi)
			ctx.line_to(0, h+s-rounded[2])
			ctx.line_to(s, h+s-rounded[2])
			ctx.arc_negative(s+rounded[2], h+s-rounded[2], rounded[2], -math.pi, math.pi/2)
			ctx.line_to(s+rounded[2], h+(s*2))
			ctx.close_path()
			ctx.fill()

			#bottom-right
			gradient = cairo.RadialGradient(w+s-rounded[3], h+s-rounded[3], rounded[3], w+s-rounded[3], h+s-rounded[3], s+rounded[3])
			gradient.add_color_stop_rgba(0,*shadow_color)
			gradient.add_color_stop_rgba(1,shadow_color[0], shadow_color[1], shadow_color[2], 0)
			ctx.set_source(gradient)
			ctx.new_sub_path()
			ctx.arc(w+s,h+s,s, 0, math.pi/2)
			ctx.line_to(w+s-rounded[3], h+(s*2))
			ctx.line_to(w+s-rounded[3], h+s)
			ctx.arc_negative(s+w-rounded[3], s+h-rounded[3], rounded[3], math.pi/2, 0)
			ctx.line_to((s*2)+w, s+h-rounded[3])
			ctx.close_path()
			ctx.fill()
			ctx.restore()

			#the content starts here!
			ctx.translate(s, s)
		else:
			ctx.translate(border_size, border_size)

		#and now the rectangle
		if fill:
			ctx.line_to(0, rounded[0])
			ctx.arc(rounded[0], rounded[0], rounded[0], math.pi, -math.pi/2)
			ctx.line_to(w-rounded[1], 0)
			ctx.arc(w-rounded[1], rounded[1], rounded[1], -math.pi/2, 0)
			ctx.line_to(w, h-rounded[3])
			ctx.arc(w-rounded[3], h-rounded[3], rounded[3], 0, math.pi/2)
			ctx.line_to(rounded[2], h)
			ctx.arc(rounded[2], h-rounded[2], rounded[2], math.pi/2, -math.pi)
			ctx.close_path()
			ctx.fill()

		if border_size > 0:
			ctx.save()
			ctx.line_to(0, rounded[0])
			ctx.arc(rounded[0], rounded[0], rounded[0], math.pi, -math.pi/2)
			ctx.line_to(w-rounded[1], 0)
			ctx.arc(w-rounded[1], rounded[1], rounded[1], -math.pi/2, 0)
			ctx.line_to(w, h-rounded[3])
			ctx.arc(w-rounded[3], h-rounded[3], rounded[3], 0, math.pi/2)
			ctx.line_to(rounded[2], h)
			ctx.arc(rounded[2], h-rounded[2], rounded[2], math.pi/2, -math.pi)
			ctx.close_path()
			ctx.set_source_rgba(*border_color)
			ctx.set_line_width(border_size)
			ctx.stroke()
			ctx.restore()
		ctx.restore()

	@staticmethod
	def draw_rounded_rectangle(ctx, x, y, rounded_angle, width, height,
		round_top_left=True, round_top_right=True, round_bottom_left=True,
		round_bottom_right=True, fill=True):
		"""Draws a rounded rectangle"""
		ctx.save()
		ctx.translate(x, y)
		padding=0 # Padding from the edges of the window
		rounded=rounded_angle # How round to make the edges. 20 is normal.
		w = width
		h = height

		# Move to top corner
		ctx.move_to(0+padding+rounded, 0+padding)
			
		# Top right corner and round the edge
		if round_top_right:
			ctx.line_to(w-padding-rounded, 0+padding)
			ctx.arc(w-padding-rounded, 0+padding+rounded, rounded, (math.pi/2 )+(math.pi) , 0)
		else:
			ctx.line_to(w-padding, 0+padding)

		# Bottom right corner and round the edge
		if round_bottom_right:
			ctx.line_to(w-padding, h-padding-rounded)
			ctx.arc(w-padding-rounded, h-padding-rounded, rounded, 0, math.pi/2)
		else:
			ctx.line_to(w-padding, h-padding)       	

		# Bottom left corner and round the edge.
		if round_bottom_left:
			ctx.line_to(0+padding+rounded, h-padding)
			ctx.arc(0+padding+rounded, h-padding-rounded, rounded,math.pi/2, math.pi)
		else:	
			ctx.line_to(0+padding, h-padding)
		
		# Top left corner and round the edge
		if round_top_left:
			ctx.line_to(0+padding, 0+padding+rounded)
			ctx.arc(0+padding+rounded, 0+padding+rounded, rounded, math.pi, (math.pi/2 )+(math.pi))
		else:
			ctx.line_to(0+padding, 0+padding)
		
		# Fill in the shape.
		if fill:ctx.fill()
		else: ctx.stroke()
		ctx.restore()

	@staticmethod
	def draw_quadrant_shadow(ctx, x, y, from_r, to_r, quad, col):
		gradient = cairo.RadialGradient(x,y,from_r,x,y,to_r)
		gradient.add_color_stop_rgba(0,col[0],col[1],col[2],col[3])
		gradient.add_color_stop_rgba(1,col[0],col[1],col[2],0)
		ctx.set_source(gradient)
		ctx.new_sub_path()
		if quad==0: ctx.arc(x,y,to_r, -math.pi, -math.pi/2)
		elif quad==1: ctx.arc(x,y,to_r, -math.pi/2, 0)
		elif quad==2: ctx.arc(x,y,to_r, math.pi/2, math.pi)
		elif quad==3: ctx.arc(x,y,to_r, 0, math.pi/2)
		ctx.line_to(x,y)
		ctx.close_path()
		ctx.fill()

	@staticmethod
	def draw_side_shadow(ctx, x, y, w, h, side, col):
		"""side: 0 - left, 1 - right, 2 - top, 3 - bottom"""
		gradient = None
		if side==0:
			gradient = cairo.LinearGradient(x+w,y,x,y)
		elif side==1:
			gradient = cairo.LinearGradient(x,y,x+w,y)
		elif side==2:
			gradient = cairo.LinearGradient(x,y+h,x,y)
		elif side==3:
			gradient = cairo.LinearGradient(x,y,x,y+h)
		if gradient:
			gradient.add_color_stop_rgba(0,col[0],col[1],col[2],col[3])
			gradient.add_color_stop_rgba(1,col[0],col[1],col[2],0)
			ctx.set_source(gradient)
		ctx.rectangle(x,y,w,h)
		ctx.fill()

	@staticmethod
	def draw_shadow(ctx, x, y, w, h, shadow_size, col):
		s = shadow_size
		#r = layout.window.radius
		r = s
		rr = r+s
		h = h-r
		if h < 2*r: h = 2*r

		# TODO: Offsets [Will need to change all places doing 
		#       x+=shadow_size/2 or such to use the offsets then
		ctx.save()
		ctx.translate(x,y)

		# Top Left
		Drawing.draw_quadrant_shadow(ctx, rr, rr, 0, rr, 0, col)
		# Left
		Drawing.draw_side_shadow(ctx, 0, rr, r+s, h-2*r, 0, col)
		# Bottom Left
		Drawing.draw_quadrant_shadow(ctx, rr, h-r+s, 0, rr, 2, col)
		# Bottom
		Drawing.draw_side_shadow(ctx, rr, h-r+s, w-2*r, s+r, 3, col)
		# Bottom Right
		Drawing.draw_quadrant_shadow(ctx, w-r+s, h-r+s, 0, rr, 3, col)
		# Right
		Drawing.draw_side_shadow(ctx, w-r+s, rr, s+r, h-2*r, 1, col)
		# Top Right
		Drawing.draw_quadrant_shadow(ctx, w-r+s, rr, 0, rr, 1, col)
		# Top
		Drawing.draw_side_shadow(ctx, rr, 0, w-2*r, s+r, 2, col)

		ctx.restore()

	@staticmethod
	def get_image_size(pix):
		"""Gets a picture width and height"""
		pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
		iw = pixbuf.get_width()
		ih = pixbuf.get_height()
		puxbuf = None
		return iw,ih

	@staticmethod
	def draw_image(ctx,x,y, pix):
		"""Draws a picture from specified path"""
		ctx.save()
		ctx.translate(x, y)	
		pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
		format = cairo.FORMAT_RGB24
		if pixbuf.get_has_alpha():
			format = cairo.FORMAT_ARGB32
		iw = pixbuf.get_width()
		ih = pixbuf.get_height()
		image = cairo.ImageSurface(format, iw, ih)
		image = ctx.set_source_pixbuf(pixbuf, 0, 0)
		
		ctx.paint()
		puxbuf = None
		image = None
		ctx.restore()

	@staticmethod
	def draw_icon(ctx,x,y, pix,width=32,height=32):
		"""Draws a gtk icon """
		ctx.save()
		ctx.translate(x, y)	
		icontheme = gtk.icon_theme_get_default()
		image = icontheme.load_icon (pix,width,height)
		ctx.set_source_pixbuf(image, 0, 0)
		ctx.paint()
		icontheme = None
		image = None
		ctx.restore()

	@staticmethod
	def draw_scaled_image(ctx,x,y, pix, w, h):
		"""Draws a picture from specified path with a certain width and height"""
		ctx.save()
		ctx.translate(x, y)	
		pixbuf = gtk.gdk.pixbuf_new_from_file(pix).scale_simple(w,h,gtk.gdk.INTERP_HYPER)
		format = cairo.FORMAT_RGB24
		if pixbuf.get_has_alpha():
			format = cairo.FORMAT_ARGB32

		iw = pixbuf.get_width()
		ih = pixbuf.get_height()
		image = cairo.ImageSurface(format, iw, ih)

		matrix = cairo.Matrix(xx=iw/w, yy=ih/h)
		image = ctx.set_source_pixbuf(pixbuf, 0, 0)
		if image is not None :image.set_matrix(matrix)
		ctx.paint()
		puxbuf = None
		image = None
		ctx.restore()
