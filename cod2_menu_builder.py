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

from tkFileDialog	import askopenfilename, asksaveasfilename
from tkMessageBox	import showinfo

import Tkinter as tk

import os, canvas_element_manager, copy, menu_manager, translator

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
			'ICONmenu': 'data/icons/menu.png',
			'ICONmoveg': 'data/icons/moveg.png',
			'ICONinvisible': 'data/icons/invisible.png',
			'ICONkeyboard': 'data/icons/keyboard.png',
		
		
			'CODgradient': 'data/gradient.png',
		
			'move': 'data/icons/move.png',
			'moveF': 'data/icons/moveF.png',
			'background': 'data/transparent.png',
			'nopreview': 'data/nopreview.png',
		}
		self.guiRawImageData = { }
		
		self.MenuManager = menu_manager.MenuManager(self)
		
		
		
	def GUIResizeImage(self, img, size):
		return img.resize(size)
		
	def GUILoadImages(self):
		for imageID in copy.deepcopy(self.guiImages):
			image = self.guiImages[imageID]
			if os.path.isfile(image):
				self.guiImages[imageID] = Image.open(image)

				if imageID.startswith('ICON'):
					self.guiImages[imageID] = self.GUIResizeImage(self.guiImages[imageID], (15,15) )

				self.guiRawImageData[imageID] = self.guiImages[imageID]
				self.guiImages[imageID] = ImageTk.PhotoImage(self.guiImages[imageID])

		
	def GUIDraw(self):
		self.root = Tk()
		self.root.geometry('935x590')
		self.root.title('Call of Duty 2 Menu Builder - stEvo')
		
		self.GUILoadImages()
		
		self.menubar 	= Menu(self.root)
		filemenu 		= Menu(self.menubar, tearoff=0)
		
		importmenu 		= Menu(filemenu, tearoff=0)
		importmenu.add_command(label="Menu file (.menu)")
		
		exportmenu 		= Menu(filemenu, tearoff=0)
		exportmenu.add_command(label="Menu file (.menu)", command = self.exportMenu )
		
		filemenu.add_cascade(label="Import", menu = importmenu)
		filemenu.add_cascade(label="Export", menu = exportmenu)
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.root.quit)
		self.menubar.add_cascade(label="File", menu=filemenu)
		
		self.menubar.add_cascade(label="Settings")
		
		self.menubar.add_cascade(label="Elements")
		
		
		
		self.menubar.add_cascade(label="help")
		self.root.config(menu=self.menubar)
		
		self.f2 = LabelFrame(self.root, text = 'Menus')
		self.nb = Notebook(self.f2)
		
		self.loadMenuOptions()
		
		self.canvas = ''
		self.elementManager = canvas_element_manager.Manage(self)
		
		self.f11 = LabelFrame(self.root, text = 'Add Element')
		
		self.b0 = Button(self.f11, text = 'Item', image = self.guiImages['ICONblank'], compound="left", width = 7)
		self.b1 = Button(self.f11, text = 'Label', image = self.guiImages['ICONtext'], compound="left", width = 7, command = self.elementManager.createLabelElement )
		self.b2 = Button(self.f11, text = 'Button', image = self.guiImages['ICONbutton'], compound="left", width = 7, command = self.elementManager.createButtonElement )
		self.b3 = Button(self.f11, text = 'Rect', image = self.guiImages['ICONrectangle'], compound="left", width = 7, command = self.elementManager.createRectElement )
		self.b4 = Button(self.f11, text = 'Image', image = self.guiImages['ICONimage'], compound="left", width = 7, command = self.imageUpload )
		self.b6 = Button(self.f11, text = 'Field', image = self.guiImages['ICONkeyboard'], compound="left", width = 7, command = self.elementManager.createFieldElement )
		
		self.f12 = LabelFrame(self.root, text = 'Tools')
		
		self.b5 = Button(self.f12, text = 'Menu', image = self.guiImages['ICONmenu'], compound="left", width = 7, command = self.MenuManager.loadMenuProperties )
		
		
		self.f3 = LabelFrame(self.root, text = 'Properties', width = 240, height = 350)
		self.f3nb = Notebook(self.f3, width = 250)
		
		self.f31 = Frame( width = 250, height = 550)
		self.f32 = Frame( width = 230, height = 550)
		self.f33 = Frame( width = 230, height = 550)
		self.f34 = Frame( width = 230, height = 550)
		
		self.f3nb.add(self.f31, text = 'Basic', padding = 5, sticky = 'wnes')
		self.f3nb.add(self.f32, text = 'Text', padding = 5, sticky = 'wnes')
		self.f3nb.add(self.f33, text = 'Functions', padding = 5, sticky = 'wnes')
		self.f3nb.add(self.f34, text = 'Other', padding = 5, sticky = 'wnes')
		
		self.f4 = LabelFrame(self.root, text = 'Elements')
		
		
		self.lb1 = Listbox(self.f4, width = 41, relief = 'flat', height = 5)
		
		self.f11.grid(row=0, column=0, sticky = (W,E))
		self.b0.grid(row=0,column = 0, padx= 3)
		self.b1.grid(row=0,column = 1, padx= 3)
		self.b2.grid(row=0,column = 2, padx= 3)
		self.b3.grid(row=0,column = 3, padx= 3)
		self.b4.grid(row=0,column = 4, padx= 3)
		self.b6.grid(row=0,column = 5, padx= 3)
		
		self.f12.grid(row=0, column=1, sticky = (W,E), padx=5)
		self.b5.grid(row=0, column = 0, padx=3)
		
		self.f2.grid(row=1, column=0, rowspan=2)
		self.root.rowconfigure(1, weight=1)
		
		self.nb.grid(row=0, column=0)
		
		self.f3.grid(row=1, column=1, padx = 5, sticky = (N,W,E,S))
		self.f3nb.grid(row=0,column=0,sticky = (N,W,E,S) )
		
		self.f4.grid(row=2, column=1, padx = 5, sticky = (N,W,E,S))
		
		self.lb1.grid(row=0,column=0,sticky = (N,W,E,S))
		
		self.loadRightMenuOptions()
		self.MenuManager.createMenu()
		
		self.nb.bind('<<NotebookTabChanged>>', self.newMenuPressed)
		self.lb1.bind('<<ListboxSelect>>', lambda _:self.elementManager.listboxSelect())
		
		self.root.mainloop()
		
	def exportMenu(self):
		top = Toplevel()
		top.geometry('300x120')
		top.title('Export menu')
	
		top.saveTo = StringVar()
		top.saveTo.set('Save to: ' + os.path.join(os.environ["HOMEPATH"], "Desktop\\test.menu"))
	
		Button(top, text = 'Change', width = 15, command = lambda: self.browseExportToSave(top) ).place(x=10,y=10)
		top.l1 = Label(top, textvariable = top.saveTo, width = 28)
		top.l1.place(x=120,y=14)
	
		top.um = BooleanVar()
		top.um.set(False)
	
		Checkbutton(top, text = 'Use Macros when saving', variable = top.um).place(x=10,y=50)
	
		Button(top, text = 'Export', width = 15, command = lambda: self.exportMenuAction(top) ).place(x=100,y=85)
	
	def browseExportToSave(self, top):
		name = asksaveasfilename(parent = top)
		if not name: return
		
		top.saveTo.set('Save to: ' + name)
		
		
	def exportMenuAction(self, top):
		path = top.saveTo.get()[9:]
		translator.exportAsMenu(self.MenuManager.Menus, saveto = path)
		top.destroy()
		
	def imageUpload(self):
		top = Toplevel()
		top.geometry('300x400')
		
		Button(top, text = 'Upload Image', width = 16, command = lambda: self.uploadImage(top) ).grid(row=0,column = 0,padx=10,pady=10)
		Label(top, text = 'Formats: DDS, PNG, JPG, BMP').grid(row = 0, column = 1)
		
		Label(top, text = 'Preview Image: ').grid(row=1,column = 0,padx=10,pady=0)
		var = StringVar()
		
		top.images = []
		for image in self.guiImages:
			if image.startswith('COD'):
				top.images.append(image[3:])
		
		
		top.cb = Combobox(top, textvariable = var)
		top.cb['values'] = top.images
		
		
		top.cb.grid(row=1,column = 1,padx=0,pady=0)
		top.cb.var = var
		
		top.canvas = Canvas(top, width = 250, height = 250)
		
		top.canvas.grid(row=3,column =0, columnspan = 2, pady=20)
		top.image = top.canvas.create_image(1,2, image = self.guiImages['nopreview'], anchor='nw')
		
		Button(top, text = 'Continue', width = 16, command = lambda top=top: self.getValue(top) ).grid(row=4,column = 0,columnspan=2,padx=10,pady=0)
		
		
		var.trace('w', lambda a='',b='',c='',self=self,top=top: self.onUpdateImage(top) )
		
	def getValue(self, top):
		self.elementManager.imageSettings( 'COD'+top.cb.var.get() )
		top.destroy()
		
	def onUpdateImage(self, top):
		imgname = 'COD'+top.cb.var.get()
		if not self.guiImages.has_key(imgname):
			top.canvas.itemconfigure(top.image, image = self.guiImages['nopreview'])
		else:
			top.tempimage = self.guiRawImageData[imgname]
			top.tempimage = top.tempimage.resize((250,250), Image.ANTIALIAS)
			top.tempimage = ImageTk.PhotoImage(top.tempimage)
			
			top.canvas.itemconfigure(top.image, image = top.tempimage)
		
	def uploadImage(self, top):
		name = askopenfilename( parent = top)
		if not name: return
		
		try:
			image = Image.open(name)
			imageTK = ImageTk.PhotoImage(image)
			name = 'COD'+os.path.basename(name).rsplit('.')[0]
			self.guiImages[name] = imageTK
			self.guiRawImageData[name] = image
			top.cb.var.set(name[3:])
			top.images.append(name[3:])
			top.cb.configure(values = top.images)
		except:
			showinfo('Error 002', 'Invalid/not supported image file', parent = top)
			top.canvas.itemconfigure(top.image, image = self.guiImages['nopreview'])
		
	def newMenuPressed(self, event):
		name = self.nb.tab(self.nb.select(), "text")
		self.MenuManager.selectMenu( self.MenuManager.identifyMenuBasedOnName(name) )
		
	def deleteMenuPressed(self, *event):
		self.MenuManager.removeMenu(self.nb.select())
		
	def loadMenuOptions(self):
		self.menuPopup 		= Menu(self.root, tearoff=0)
		self.menuPopup.add_command(label="Add new Menu", command = self.MenuManager.createMenu)
		self.menuPopup.add_command(label="Delete this menu", command = self.deleteMenuPressed)
		
		self.nb.bind("<Button-3>", self.menuPopupEvent)
		
	def menuPopupEvent(self, event):
		self.menuPopup.post(event.x_root, event.y_root)
		
	def loadRightMenuOptions(self):
		self.rightMenuS 		= Menu(self.root, tearoff=0)
		self.rightMenuS.add_command(label="Copy selected element", command = self.elementManager.copySelected )
		self.rightMenuS.add_command(label="Paste element", command = self.elementManager.pasteSelected)
		self.rightMenuS.add_command(label="Delete selected element")
		self.rightMenuS.add_separator()
		self.rightMenuS.add_command(label="Reset properties to default")
		
		self.rightMenu 		= Menu(self.root, tearoff=0)
		self.rightMenu.add_command(label="Change background")
		self.rightMenu.add_command(label="Paste element", command = self.elementManager.pasteSelected)
		self.rightMenu.add_command(label="Delete all elements")
		
	def rightMenuPopupEventSelected(self, event):
		self.rightMenuS.post(event.x_root, event.y_root)
		
	def rightMenuPopupEvent(self, event):
		self.rightMenu.post(event.x_root, event.y_root)
		
	def coreLoadBackground(self):
		if 'background' in self.canvasElements:
			self.canvas.delete(self.canvasElements['background'])
		
		self.canvasElements['background'] = self.canvas.create_image(0,0, image=self.guiImages['background'], anchor=NW)
		self.canvas.tag_lower(self.canvasElements['background'])
		
		
		
		
		
		
if __name__ == '__main__':
	Main()