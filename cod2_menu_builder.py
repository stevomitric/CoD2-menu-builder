'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''

from Tkinter 	import *
from ttk		import *
from threading	import Thread
from PIL 		import Image, ImageTk

import Tkinter as tk

import os, canvas_element_manager

class Main:
	def __init__(self):
		
		self.initVariables()
		
		self.GUIDraw()
		
		
	def initVariables(self):
		self.guiImages = {
			'ICONtext': 'data/icons/text.png',
			'ICONbutton': 'data/icons/button.png',
			'ICONrectangle': 'data/icons/rectangle.png',
			'ICONimage': 'data/icons/image.png',
			'ICONblank': 'data/icons/blank.png',
		
			'move': 'data/icons/move.png',
			'moveF': 'data/icons/moveF.png',
			'background': 'data/transparent.png'
		}
		
		self.canvasElements = {}
		
		
		
	def GUIResizeImage(self, img, size):
		return img.resize(size)
		
	def GUILoadImages(self):
		for imageID in self.guiImages.copy():
			image = self.guiImages[imageID]
			if os.path.isfile(image):
				self.guiImages[imageID] = Image.open(image)

				if imageID.startswith('ICON'):
					self.guiImages[imageID] = self.GUIResizeImage(self.guiImages[imageID], (15,15) )
				
				self.guiImages[imageID] = ImageTk.PhotoImage(self.guiImages[imageID])

		
	def GUIDraw(self):
		self.root = Tk()
		self.root.geometry('900x550')
		self.root.title('Call of Duty 2 Menu Builder - stEvo')
		
		self.GUILoadImages()
		
		self.menubar = Menu(self.root)
		filemenu = Menu(self.menubar, tearoff=0)
		filemenu.add_command(label="Open")
		filemenu.add_command(label="Save")
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.root.quit)
		self.menubar.add_cascade(label="File", menu=filemenu)
		
		self.menubar.add_cascade(label="Settings")
		
		self.menubar.add_cascade(label="Elements")
		
		self.menubar.add_cascade(label="help")
		self.root.config(menu=self.menubar)
		
		self.f2 = LabelFrame(text = 'Canvas')
		self.f2.grid(row=1, column=0)
		
		self.canvas = Canvas(self.f2, width = 640, height = 480)
		self.elementManager = canvas_element_manager.Manage(self)
		
		self.f1 = LabelFrame(text = 'Add Element')
		self.f1.grid(row=0, column=0, sticky = W)
		
		self.b0 = Button(self.f1, text = 'Item', image = self.guiImages['ICONblank'], compound="left", width = 7)
		self.b1 = Button(self.f1, text = 'Label', image = self.guiImages['ICONtext'], compound="left", width = 7, command = self.elementManager.createLabelElement )
		self.b2 = Button(self.f1, text = 'Button', image = self.guiImages['ICONbutton'], compound="left", width = 7)
		self.b3 = Button(self.f1, text = 'Rect', image = self.guiImages['ICONrectangle'], compound="left", width = 7)
		self.b4 = Button(self.f1, text = 'Image', image = self.guiImages['ICONimage'], compound="left", width = 7)
		
		self.f3 = LabelFrame(text = 'Properties', width = 240, height = 100)
		self.f3.grid(row=1, column=1, padx = 5, sticky = N)
		
		
		self.b0.grid(row=1,column = 0, padx= 3)
		self.b1.grid(row=1,column = 1, padx= 3)
		self.b2.grid(row=1,column = 2, padx= 3)
		self.b3.grid(row=1,column = 3, padx= 3)
		self.b4.grid(row=1,column = 4, padx= 3)
		self.canvas.grid(row=0, column=0)
		
		self.coreLoadBackground()
		
		self.canvas.bind(' <ButtonPress-1>', self.elementManager.buttonPress)
		self.canvas.bind(' <ButtonRelease-1>', self.elementManager.buttonRelease)
		self.canvas.bind(' <B1-Motion>', self.elementManager.buttonMotion)
		
		
		self.root.mainloop()
		
		
	def coreLoadBackground(self):
		if 'background' in self.canvasElements:
			self.canvas.delete(self.canvasElements['background'])
		
		self.canvasElements['background'] = self.canvas.create_image(0,0, image=self.guiImages['background'], anchor=NW)
		self.canvas.tag_lower(self.canvasElements['background'])
		
		
		
		
		
		
if __name__ == '__main__':
	Main()