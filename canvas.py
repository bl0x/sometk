#!/usr/bin/env python3
import numpy as np
import logging
import json

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

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

class WidgetLogger(logging.Handler):
    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.setLevel(logging.WARNING)
        self.widget = widget
        self.widget.config(state='disabled')
        self.widget.tag_config("INFO", foreground="black")
        self.widget.tag_config("DEBUG", foreground="grey")
        self.widget.tag_config("WARNING", foreground="orange")
        self.widget.tag_config("ERROR", foreground="red")
        self.widget.tag_config("CRITICAL", foreground="red", underline=1)

        self.red = self.widget.tag_configure("red", foreground="red")
    def emit(self, record):
        self.widget.config(state='normal')
        # Append message (record) to the widget
        self.widget.insert(tk.END, f"{record.message}\n", record.levelname)
        self.widget.see(tk.END)  # Scroll to the bottom
        self.widget.config(state='disabled') 
        self.widget.update() # Refresh the widget

class MarkerList():
	def __init__(self, app):
		self.app = app
		self.window = tk.Toplevel()
		self.window.title("Marker list")
		columns = ("ID", "Position", "Size")
		self.tw = ttk.Treeview(self.window, columns=columns)
		self.tw.column("ID", width=30)
		self.tw.column("Position", width=150)
		for c in columns:
			self.tw.heading(c, text=c)
		self.tw['show'] = 'headings'
		self.tw.grid(row=0, column=0, sticky="nesw")
		self.sb = ttk.Scrollbar(self.window, orient="vertical",
						  command=self.tw.yview)
		self.tw.configure(yscrollcommand=self.sb.set)
		self.tw.bind('<Control-a>', lambda _: self.tw.selection_add(self.tw.get_children()))
		self.tw.bind('<Control-c>', lambda _: self.copy_markers())
		self.sb.grid(row=0, column=1, sticky="ns")
		self.copy = ttk.Button(self.window, text="Copy", command=self.copy_markers)
		self.copy.grid(row=1, column=0, sticky="we")
		self.window.columnconfigure(0, weight=1)
		self.window.rowconfigure(0, weight=1)
		## done
		self.window.withdraw()
		self.update()
	def copy_markers(self):
		root.clipboard_clear()
		root.clipboard_append("# marker_id pos_x pos_y size_x size_y\n")
		for m in self.app.markers:
			root.clipboard_append(f"{m.id} {m.pos[0]} {m.pos[1]} {m.size[0]} {m.size[1]}\n") 
	def clear(self):
		self.tw.delete(*self.tw.get_children())
	def add(self):
		for m in self.app.markers:
			self.tw.insert('', tk.END, values=(m.id, str(m.pos), str(m.size)))
	def update(self):
		self.clear()
		self.add()

class App:
	def __init__(self):
		self.size = np.array([10,10])
		self.select = False
		self.scroll_start = (0, 0)
		self.markers = []
		self.dragged = None
		self.drag_origin = (0,0)
		self.log_level = tk.StringVar()
		self.log_level.set("WARNING")
		self.MARKERS_FILE = ".app_markers"
		self.mlist = MarkerList(self)
		self.restore()

	def show_marker_list(self, event):
		if self.mlist.window.state() == 'normal':
			self.mlist.window.withdraw()
		else:
			self.mlist.window.state('normal')

	def show_edit_menu(self, event):
		m = tk.Menu(root, tearoff=0)
		m.add_command(label = "Copy markers", underline=0,
				command=self.mlist.copy_markers)
		try:
			m.tk_popup(event.x_root, event.y_root)
		finally:
			m.grab_release()

	def load_markers(self):
		try:
			with open(self.MARKERS_FILE, "r") as f:
				data = json.load(f)
				for m in data["markers"]:
					self.add_marker(m["pos"],
					 np.array(m["size"]),
					 _id=m["id"])
		except E:
			print(f"oops: {E}")
			pass

	def restore(self):
		self.load_markers()

	def save_markers(self):
		with open(self.MARKERS_FILE, "w") as f:
			data = {"markers": []}
			for m in self.markers:
				data["markers"].append(m.dict())
			json.dump(data, f)

	def shutdown(self):
		self.save_markers()

	def add_marker(self, pos, size, _id=None):
		if _id is None:
			_id = len(self.markers)
		m = Marker(c, _id, pos, size)
		self.markers.append(m)
		self.mlist.update()

	def click_action(self, event):
		x = c.canvasx(event.x)
		y = c.canvasy(event.y)
		if self.select:
			self.place_marker(x,y)
		else:
			self.select_marker(x,y)
			self.drag_start(x,y)

	def place_marker(self, x,y):
		self.add_marker((x,y), self.size)

	def delete_last_marker(self):
		if len(self.markers) != 0:
			m = self.markers.pop()
			m.delete()
			self.mlist.update()

	def delete_closest_marker(self, event):
		x = c.canvasx(event.x)
		y = c.canvasy(event.y)
		if len(self.markers) != 0:
			_id = c.find_closest(x, y)
			tags = c.gettags(_id)
			logging.info(f"deleting {tags}")
			for i,m in enumerate(self.markers):
				if len(tags) > 1 and m.tags[1] == tags[1]:
					_m = self.markers.pop(i)
					_m.delete()
					break
			for i,m in enumerate(self.markers):
				m.set_id(i)
		self.mlist.update()

	def select_marker(self, pos):
		_id = c.find_closest(pos[0], pos[1])
		tags = c.gettags(_id)
		logging.debug(f"clicked on {tags}")
		for m in self.markers:
			if len(tags) > 1 and m.tags[1] == tags[1]:
				if inside_bbox(m.bbox, pos):
					logging.info(f'selecting {tags}')
					m.select(True)
				else:
					logging.debug(f'marker "{m.tags}" not inside bbox')
					logging.debug(f' bbox: {m.bbox}')
					logging.debug(f' pos : {pos}')
					m.select(False)
			else:
				logging.debug(f'marker "{m.tags}" no match for {tags}')
				m.select(False)

def bbox_from_pos(pos, size):
	return pos[0]-size[0], pos[1]-size[1], pos[0]+size[0], pos[1]+size[1]

class Marker():
	def __init__(self, canvas, i, pos, size):
		self.canvas = canvas
		self.id = i
		self.tags = ('marker', self.maketag(i))
		self.pos = pos
		self.size = size.copy()
		self.items = []
		self.text = None
		self.selected = False
		self.create()

	@classmethod
	def from_dict(cls, canvas, data):
		return cls(canvas, data["id"], data["pos"], data["size"])

	def dict(self):
		return {"id": self.id,
		  "pos": list(self.pos),
		  "size": self.size.tolist()
		}

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
		# bounding box to show when selected
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

a = App()

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
	logging.debug(a.size)

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

def drag_start(x, y):
	for m in a.markers:
		if m.selected:
			logging.info(f"drag_start {m.tags}")
			a.dragged = m
			a.drag_origin = (x,y)
		logging.debug(f"{m.tags}, {m.selected}")

def drag_stop(event):
	if a.dragged is not None:
		a.dragged.bbox = c.bbox(a.dragged.tags[1])
		a.dragged = None
		a.drag_origin = (0,0)

def drag(event):
	if a.dragged is not None:
		x = c.canvasx(event.x)
		y = c.canvasy(event.y)
		delta = (x - a.drag_origin[0], y - a.drag_origin[1])
		c.move(a.dragged.tags[1], delta[0], delta[1])
		a.drag_origin = (x,y)

c.bind("<Motion>", motion)
c.bind("<Button-1>", a.click_action)
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

st = scrolledtext.ScrolledText(root, state='disabled')
st.grid(column=0, row=2, sticky=(tk.W), columnspan=2)

level_l  = tk.Label(root, text="Log level:")
level_l.grid(column=0, row=3)

def change_log_level():
	wl.setLevel(a.log_level.get())
	print(a.log_level.get())

level_cb = ttk.Combobox(root, textvariable=a.log_level)
level_cb['values'] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
level_cb['state'] = 'readonly'
level_cb.bind('<<ComboboxSelected>>', lambda _: change_log_level())
level_cb.grid(column=1, row=3)

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger()
wl = WidgetLogger(st)
logger.addHandler(wl)

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

def shutdown():
	a.shutdown()
	root.destroy()

root.bind_all("s", toggle_select)
root.bind_all("q", lambda _: shutdown())
root.bind_all("d", lambda _: a.delete_last_marker())
root.bind_all("D", a.delete_closest_marker)
root.bind_all("m", a.show_marker_list)
root.bind_all("e", a.show_edit_menu)
root.mainloop()
