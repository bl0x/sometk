#!/usr/bin/env python3

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
class App:
	def __init__(self):
		self.size = 10
		self.select = False
		self.scroll_start = (0, 0)

a = App()

def toggle_select(event):
	a.select = not a.select
	if a.select:
		c.itemconfigure(l, state='normal')
	else:
		c.itemconfigure(l, state='hidden')

def motion(event):
	print(event.x, event.y)
	s = a.size
	x = c.canvasx(event.x)
	y = c.canvasy(event.y)
	c.coords(l, x-s, y-s, x+s, y+s)

def resize(event):
	if a.size > 1 and (event.num == 4 or event.delta < 0):
		a.size -= 1
	if a.size < 100 and (event.num == 5 or event.delta > 0):
		a.size += 1
	motion(event)
	print(a.size)

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

c.bind("<Motion>", motion)
c.bind("<MouseWheel>", resize)
c.bind("<Button-4>", resize)
c.bind("<Button-5>", resize)

c.bind("<Button-3>", scroll_start)
c.bind("<B3-Motion>", scroll)

c.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
h.grid(column=0, row=1, sticky=(tk.W, tk.E))
v.grid(column=1, row=0, sticky=(tk.N, tk.S))

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

root.bind_all("s", toggle_select)
root.mainloop()
