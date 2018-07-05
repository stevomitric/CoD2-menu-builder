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
from tkMessageBox	import showinfo, askyesno

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
			'ICONdeletemenu': 'data/icons/deletemenu.png',
			'ICONaddmenu': 'data/icons/addmenu.png',
			'ICONmoveg': 'data/icons/moveg.png',
			'ICONinvisible': 'data/icons/invisible.png',
			'ICONkeyboard': 'data/icons/keyboard.png',
			'ICONslider': 'data/icons/slider.png',
			'ICONlist': 'data/icons/list.png',
		
		
			'CODgradient': 'data/gradient.png',
		
			'move': 'data/icons/move.png',
			'moveF': 'data/icons/moveF.png',
			'background': 'data/transparent.png',
			'background2': 'data/cod2dx7.png',
			'background3': 'data/cod2dx9.png',
			'nopreview': 'data/nopreview.png',
			'slider': 'data/slider.png',
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
		self.root.resizable(False, False)
		
		self.GUILoadImages()
		
		self.menubar 	= Menu(self.root)
		filemenu 		= Menu(self.menubar, tearoff=0)
		
		importmenu 		= Menu(filemenu, tearoff=0)
		importmenu.add_command(label="Menu file (.menu)", command = self.menuImportFile )
		
		exportmenu 		= Menu(filemenu, tearoff=0)
		exportmenu.add_command(label="Menu file (.menu)", command = self.exportMenu )
		
		filemenu.add_cascade(label="Import", menu = importmenu)
		filemenu.add_cascade(label="Export", menu = exportmenu)
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.root.quit)
		self.menubar.add_cascade(label="File", menu=filemenu)
		
		self.menubar.add_cascade(label="Settings", command = self.programSettings)
		
		#self.menubar.add_cascade(label="Elements")
		
		
		
		#self.menubar.add_cascade(label="help")
		self.root.config(menu=self.menubar)
		
		self.f2 = LabelFrame(self.root, text = 'Menus')
		self.nb = Notebook(self.f2)
		
		self.loadMenuOptions()
		
		self.canvas = ''
		self.elementManager = canvas_element_manager.Manage(self)
		
		self.f11 = LabelFrame(self.root, text = 'Add Element')
		
		self.b0 = Button(self.f11, text = 'Item', image = self.guiImages['ICONblank'], compound="left", width = 7, command = self.elementManager.createItemElement, state = 'disabled' )
		self.b1 = Button(self.f11, text = 'Label', image = self.guiImages['ICONtext'], compound="left", width = 7, command = self.elementManager.createLabelElement )
		self.b2 = Button(self.f11, text = 'Button', image = self.guiImages['ICONbutton'], compound="left", width = 7, command = self.elementManager.createButtonElement )
		self.b3 = Button(self.f11, text = 'Rect', image = self.guiImages['ICONrectangle'], compound="left", width = 7, command = self.elementManager.createRectElement )
		self.b4 = Button(self.f11, text = 'Image', image = self.guiImages['ICONimage'], compound="left", width = 7, command = self.imageUpload )
		self.b6 = Button(self.f11, text = 'Field', image = self.guiImages['ICONkeyboard'], compound="left", width = 7, command = self.elementManager.createFieldElement )
		self.b7 = Button(self.f11, text = 'Slider', image = self.guiImages['ICONslider'], compound="left", width = 7, command = self.elementManager.createSliderElement)
		self.b8 = Button(self.f11, text = 'Multi', image = self.guiImages['ICONlist'], compound="left", width = 7, command = self.elementManager.createListElement)
		
		self.f12 = LabelFrame(self.root, text = 'Tools')
		
		self.b5 = Button(self.f12, text = 'Menu', image = self.guiImages['ICONmenu'], compound="left", width = 7, command = self.MenuManager.loadMenuProperties )
		self.b9 = Button(self.f12, text = '', image = self.guiImages['ICONdeletemenu'], compound="left", width = 0, command =  self.deleteMenuPressed)
		self.b10 = Button(self.f12, text = '', image = self.guiImages['ICONaddmenu'], compound="left", width = 0, command = self.MenuManager.createMenu )
		
		
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
		self.b7.grid(row=0,column = 6, padx= 3)
		self.b8.grid(row=0,column = 7, padx= 3)
		
		self.f12.grid(row=0, column=1, sticky = (W,E), padx=5)
		self.b5.grid(row=0, column = 0, padx=3)
		self.b9.grid(row=0, column = 1, padx=3)
		self.b10.grid(row=0, column = 2, padx=3)
		
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
		
		self.root.bind('<KeyPress>', self.elementManager.keypress)
		self.root.bind('<KeyRelease>', self.elementManager.keyrelease)
		
		self.root.bind('<Control-c>', lambda _: self.elementManager.copySelected() )
		self.root.bind('<Control-v>', lambda _: self.elementManager.pasteSelected() )
		
		#self.root.after(1000,  lambda: translator.importMenuFile(self) )
		
		self.root.mainloop()
		
	def menuImportFile(self):
		top = Toplevel()
		top.geometry('300x175')
		top.title('Import')
		
		top.file = StringVar()
		top.file.set('Import File: ')
	
		Button(top, text = 'Change', width = 15, command = lambda: self.browseImportOpen(top) ).place(x=10,y=10)
		top.l1 = Label(top, textvariable = top.file, width = 28)
		top.l1.place(x=120,y=14)
	
		top.ul = BooleanVar()
		top.ul.set(False)
	
		top.inc = IntVar()
		top.inc.set(0)
	
		Radiobutton(top, text = 'Use default cod2 files for #include', variable = top.inc, value=0).place(x=10,y=50)
		Radiobutton(top, text = 'Use imported menu location for #include', variable = top.inc, value=1, state = 'disabled').place(x=10,y=75)
		Checkbutton(top, text = 'Display console (log) when importing files', variable = top.ul).place(x=10,y=100)
	
		Button(top, text = 'Import', width = 15, command = lambda: self.importMenu(top) ).place(x=100,y=140)
		
		
	def browseImportOpen(self, top):
		name = askopenfilename(parent = top)
		if not name: return
		
		top.file.set('Import File: ' + name)
		
	def importMenu(self, top):
	
		if top.ul.get():
			top2 = Toplevel()
			top2.title('Import console')
			top2.tx = Text(top2, height = 20, width = 100)
			top2.tx.grid(row= 0, column = 0)
		else:
			top2 = ''
		
		#top.bind("<Destroy>", top2.destroy)
	
		self.root.after(100, lambda: self.beginImport(top, top2) )
	
	def beginImport(self, top, top2 = ''):
		res = translator.importMenuFile(self, top.file.get()[13:], out = top2)
		if res == -1:
			showinfo('Error 004', 'Invalid file location. (Could not open: '+top.file.get()[13:]+', errno 22) ', parent = top)
			return
		elif res == -2:
			showinfo('Error 005', 'Error occured during data processing. Check console for details.', parent = top)
			return
		elif res == -3:
			showinfo('Error 006', 'Error occured during menu creation. Check console for details.', parent = top)
			return
			
		top.destroy()
		if top2:
			top2.lift()
		
	def programSettings(self):
		top = Toplevel()
		top.geometry('300x110')
		top.title('Settings')
		
		top.snap = StringVar()
		top.snap.set( str( self.elementManager.settings['snapping'] ) )
		top.snap.trace('w', lambda a='',b='',c='' : self.changeSettings(top, 'snapping') )
		top.autobbox = BooleanVar()
		top.autobbox.set( str( self.elementManager.settings['autoUpdateBBOX'] ) )
		top.autobbox.trace('w', lambda a='',b='',c='' : self.changeSettings(top, 'autoUpdateBBOX') )
		top.autoalign = BooleanVar()
		top.autoalign.set( str( self.elementManager.settings['autoAlignText'] ) )
		top.autoalign.trace('w', lambda a='',b='',c='' : self.changeSettings(top, 'autoAlignText') )
		
		Label(top, text = 'Snapping: ').grid(row = 0, column = 0, padx=10,pady=10, sticky='w')
		Entry(top, width = 5 , textvariable = top.snap).grid(row = 0, column = 1)
		Label(top, text = 'Snap key (hold):   CTRL' ).grid(row = 0, column = 3, padx = 40)
		
		Checkbutton(top, variable = top.autobbox, text = 'Auto update element rect (BBOX) ').grid(row = 1, column = 0, padx=10,pady=5,columnspan=4, sticky='w')
		Checkbutton(top, variable = top.autoalign, text = 'Auto align text inside rect ').grid(row = 2, column = 0, padx=10,pady=5,columnspan=4, sticky='w')
		
	def changeSettings(self, top, key, value = ''):
		try:
			if key == 'snapping':
				value = int(top.snap.get())
			elif key == 'autoUpdateBBOX':
				value = top.autobbox.get()			
			elif key == 'autoAlignText':
				value = top.autoalign.get()
		except:
			return
		
		self.elementManager.settings[key] = value
		
		
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
	
		Checkbutton(top, text = 'Use Macros when saving', variable = top.um, state = 'disabled').place(x=10,y=50)
	
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
		self.elementManager.createImageElement( 'COD'+top.cb.var.get() )
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
		self.MenuManager.selectMenu( self.MenuManager.identifyMenuBasedOnID(self.nb.select()) )
		
	def deleteMenuPressed(self, *event):
		res = askyesno('Confirm', 'Are you sure you want to delete this menu ?')
		if not res: return
	
		self.MenuManager.removeMenu(self.nb.select())
		
	def loadMenuOptions(self):
		self.menuPopup 		= Menu(self.root, tearoff=0)
		self.menuPopup.add_command(label="Add new Menu", command = self.MenuManager.createMenu)
		self.menuPopup.add_command(label="Delete this menu", command = self.deleteMenuPressed)
		
		self.nb.bind("<Button-3>", self.menuPopupEvent)
		
	def menuPopupEvent(self, event):
		self.menuPopup.post(event.x_root, event.y_root)
		
	def loadRightMenuOptions(self):
	
		self.rightMenu 		= Menu(self.root, tearoff=0)
		newBackground 		= Menu(self.rightMenu, tearoff=0)
		newBackground.add_command(label="Transparent", command = lambda: self.changeBG('background') )
		newBackground.add_command(label="Toujane/CoD2 DX7", command = lambda: self.changeBG('background2') )
		newBackground.add_command(label="Toujane/CoD2 DX9 (blured)", command = lambda: self.changeBG('background3') )
	
		self.rightMenuS 		= Menu(self.root, tearoff=0)
		self.rightMenuS.add_command(label="Copy selected element", command = self.elementManager.copySelected )
		self.rightMenuS.add_command(label="Paste element", command = self.elementManager.pasteSelected)
		self.rightMenuS.add_command(label="Delete selected element", command =self.elementManager.deleteElement )
		self.rightMenuS.add_separator()
		self.rightMenuS.add_command(label="Delete all elements", command = self.elementManager.deleteAllElements)
		
		
		self.rightMenu.add_cascade(label="Change background", menu = newBackground)
		self.rightMenu.add_command(label="Paste element", command = self.elementManager.pasteSelected)
		self.rightMenu.add_command(label="Delete all elements", command = self.elementManager.deleteAllElements)
		
	def changeBG(self, bg):
		menu = self.MenuManager.identifyMenuBasedOnID(self.nb.select())
		self.MenuManager.updateBackground(menu, bg)
		
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