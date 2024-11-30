#!/usr/bin/env python3
import numpy as np

import tkinter as tk
from tkinter import ttk

root = tk.Tk()

h = ttk.Scrollbar(root, orient=tk.HORIZONTAL)
v = ttk.Scrollbar(root, orient=tk.VERTICAL)

c = tk.Canvas(root, scrollregion=(0,0,1000,1000), height=300, width=300,
			  yscrollcommand=v.set, xscrollcommand=h.set)

h['command'] = c.xview
v['command'] = c.yview

l2 = c.create_rectangle(20, 20, 40, 40, fill='green', outline='blue')
l3 = c.create_rectangle(40, 40, 80, 80, fill='yellow', outline='blue')

l = c.create_rectangle(10, 10, 10, 10, fill='red', outline='blue',
					   state='hidden')
def inside_bbox(bbox, pos):
	return all(
			[bbox[0] < pos[0],
			 bbox[1] < pos[1],
			 bbox[2] > pos[0],
			 bbox[3] > pos[1]]
	)

class App:
	def __init__(self):
		self.size = np.array([10,10])
		self.select = False
		self.scroll_start = (0, 0)
		self.markers = []
		self.dragged = None
		self.drag_origin = (0,0)

	def add_marker(self, pos, size):
		m = Marker(c, len(self.markers), pos, size)
		self.markers.append(m)

	def select_marker(self, pos):
		_id = c.find_closest(pos[0], pos[1])
		tags = c.gettags(_id)
		# print(f"clicked on {tags}")
		for m in self.markers:
			if len(tags) > 1 and m.tags[1] == tags[1]:
				if inside_bbox(m.bbox, pos):
					# print(f'selecting {tags}')
					m.select(True)
				else:
					m.select(False)
			else:
				m.select(False)

a = App()

def bbox_from_pos(pos, size):
	return pos[0]-size[0], pos[1]-size[1], pos[0]+size[0], pos[1]+size[1]

class Marker():
	def __init__(self, canvas, i, pos, size):
		self.canvas = canvas
		self.id = i
		self.tags = ('marker', self.maketag(i))
		self.pos = pos
		self.size = size
		self.items = []
		self.text = None
		self.selected = False
		self.create()

	def delete(self):
		for it in self.items:
			self.canvas.delete(it)

	def set_id(self, _id):
		self.id = _id
		self.canvas.itemconfigure(self.text, text=str(_id))

	def create(self):
		c = self.canvas
		# main rect
		self.items.append(
				c.create_rectangle(bbox_from_pos(self.pos, self.size),
					   tags=self.tags))
		self.items.append(
				c.create_rectangle(bbox_from_pos(self.pos, self.size),
					   outline='white', dash='4 4 4 4', tags=self.tags))
		# small rect in upper right corner (outside rect) for label
		rsize = (5,7)
		urpos = (self.pos[0]+self.size[0]+rsize[0]+1,
		   self.pos[1]-self.size[1]+rsize[1])
		self.items.append(c.create_rectangle(bbox_from_pos(urpos, rsize),
						outline='magenta', fill='magenta', tags=self.tags))
		# number
		tpos = urpos
		self.text = c.create_text(tpos, text=str(self.id), tags=self.tags)
		self.items.append(self.text)
		# bouding box to show when selected
		self.bbox = c.bbox(self.tags[1])
		pad = 2
		self.bbox = (
				self.bbox[0] - pad,
				self.bbox[1] - pad,
				self.bbox[2] + pad,
				self.bbox[3] + pad)
		self.outer = c.create_rectangle(self.bbox,
						outline='magenta', tags=self.tags, state=tk.HIDDEN)
		self.items.append(self.outer)
	def maketag(self, i):
		return f"m{i}"

	def select(self, state):
		if state:
			self.canvas.itemconfigure(self.outer, state=tk.NORMAL)
			self.selected = True
		else:
			self.canvas.itemconfigure(self.outer, state=tk.HIDDEN)
			self.selected = False

def toggle_select(event):
	a.select = not a.select
	if a.select:
		c.itemconfigure(l, state='normal')
	else:
		c.itemconfigure(l, state='hidden')

def motion(event):
	# print(event.x, event.y)
	s = a.size
	x = c.canvasx(event.x)
	y = c.canvasy(event.y)
	c.coords(l, x-s[0], y-s[1], x+s[0], y+s[1])

def resize(event, only_x=False):
	for i in range(2):
		if a.size[i] > 1 and (event.num == 4 or event.delta < 0):
			a.size[i] -= 1
		if a.size[i] < 100 and (event.num == 5 or event.delta > 0):
			a.size[i] += 1
		if only_x:
			break
	motion(event)
	# print(a.size)

def scroll_start(event):
	c.config(yscrollincrement=3)
	c.config(xscrollincrement=3)
	a.scroll_start = (event.x, event.y)

def scroll(event):
	dx = event.x - a.scroll_start[0]
	dy = event.y - a.scroll_start[1]
	c.xview('scroll', dx, 'units')
	c.yview('scroll', dy, 'units')
	a.scroll_start = (event.x, event.y)

def click_action(event):
	x = c.canvasx(event.x)
	y = c.canvasy(event.y)
	if a.select:
		place_marker(x,y)
	else:
		select_marker(x,y)
		drag_start(x,y)

def select_marker(x,y):
	a.select_marker((x,y))

def place_marker(x,y):
	a.add_marker((x,y), a.size)

def delete_last_marker():
	if len(a.markers) != 0:
		m = a.markers.pop()
		m.delete()

def delete_closest_marker(event):
	x = c.canvasx(event.x)
	y = c.canvasy(event.y)
	if len(a.markers) != 0:
		_id = c.find_closest(x, y)
		tags = c.gettags(_id)
		# print(f"deleting {tags}")
		for i,m in enumerate(a.markers):
			if len(tags) > 1 and m.tags[1] == tags[1]:
				_m = a.markers.pop(i)
				_m.delete()
				break
		for i,m in enumerate(a.markers):
			m.set_id(i)

def drag_start(x, y):
	for m in a.markers:
		if m.selected:
			# print(f"drag_start {m.tags}")
			a.dragged = m.tags[1]
			a.drag_origin = (x,y)
		# print(m.tags, m.selected)

def drag_stop(event):
	a.dragged = None
	a.drag_origin = (0,0)

def drag(event):
	x = c.canvasx(event.x)
	y = c.canvasy(event.y)
	delta = (x - a.drag_origin[0], y - a.drag_origin[1])
	c.move(a.dragged, delta[0], delta[1])
	a.drag_origin = (x,y)

c.bind("<Motion>", motion)
c.bind("<Button-1>", click_action)
c.bind("<MouseWheel>", resize)
c.bind("<Button-4>", resize)
c.bind("<Button-5>", resize)
c.bind("<Alt-MouseWheel>", lambda e: resize(e, only_x=True))
c.bind("<Alt-Button-4>", lambda e: resize(e, only_x=True))
c.bind("<Alt-Button-5>", lambda e: resize(e, only_x=True))
c.bind("<ButtonRelease-1>", drag_stop)
c.bind("<B1-Motion>", drag)


c.bind("<Button-3>", scroll_start)
c.bind("<B3-Motion>", scroll)

c.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
h.grid(column=0, row=1, sticky=(tk.W, tk.E))
v.grid(column=1, row=0, sticky=(tk.N, tk.S))

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

root.bind_all("s", toggle_select)
root.bind_all("q", lambda _: root.destroy())
root.bind_all("d", lambda _: delete_last_marker())
root.bind_all("D", delete_closest_marker)
root.mainloop()
