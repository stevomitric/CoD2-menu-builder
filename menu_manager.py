'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''

from Tkinter 		import *
from ttk			import *

from tkMessageBox 	import showinfo
from PIL			import Image, ImageTk

import copy, cod2_default_element_settings

class MenuManager:
	def __init__(self, GUI):
		self.GUI = GUI
		
		self.Menus = []
		
		self.inx = 0
		
	def createMenu(self):
		menu = {
			'type': 'menu',
			'badArgument': [],
		
			'frame': Frame(),			
			'elements': {},
			'name': 'Menu'+str(self.inx),
			'background': 'background',
			'backImageColour': (0, 0, 0, 128),
			'style': 'WINDOW_STYLE_EMPTY',
			
			'properties': copy.deepcopy(cod2_default_element_settings.menuSettings),
		}
		self.inx += 1
		
		menu['properties']['name'][0] = menu['name']
		
		menu['canvas'] = Canvas(menu['frame'], width = 640, height = 480)
		menu['canvas'].grid(row=0,column=0)
		menu['canvasBG'] = menu['canvas'].create_image(0,0, image=self.GUI.guiImages[menu['background'] ], anchor=NW)
		menu['canvasFill'] = menu['canvas'].create_image(0,0, anchor=NW)
		
		menu['canvas'].bind('<ButtonPress-1>', self.GUI.elementManager.buttonPress)
		menu['canvas'].bind('<ButtonRelease-1>', self.GUI.elementManager.buttonRelease)
		menu['canvas'].bind('<B1-Motion>', self.GUI.elementManager.buttonMotion)
		
		menu['canvas'].bind('<ButtonPress-3>', self.GUI.elementManager.rightButtonPress)
		
		
		self.GUI.nb.add(menu['frame'], text = menu['name'], padding = 5)
		
		self.Menus.append(menu)
		
		menu['id'] = self.GUI.nb.tabs()[-1]
		
		#self.selectMenu(menu)

		return menu
		
	def updateBackImage(self, element):
		if element['style']	== 'WINDOW_STYLE_FILLED':

			element['imageFill'] = Image.new('RGBA', (640, 480), element['backImageColour'] )
			element['imageFillR'] = ImageTk.PhotoImage(element['imageFill'])
			element['canvas'].itemconfigure(element['canvasFill'], image = element['imageFillR'])

		if element['style'] == 'WINDOW_STYLE_EMPTY':
			element['canvas'].itemconfigure(element['canvasFill'], image = '')
		
	def loadMenuProperties(self):
		self.GUI.elementManager.disselectElement()
	
		name = self.GUI.nb.tab(self.GUI.nb.select(), "text")
		menu = self.identifyMenuBasedOnName(name)
	
		self.GUI.elementManager.propertiesManagment.updatePorperties(nonElementProperty = menu)
	
	def updateTabName(self, tab, name):
		self.GUI.nb.tab(tab, text = name)
	
	def removeMenu(self, id):
		if len(self.Menus) <= 1:
			showinfo('Error 001', 'Cannot delete last Menu.')
			return
		
		self.GUI.elementManager.removeAll()

		name = self.GUI.nb.tab(id, "text")
		menu = self.identifyMenuBasedOnName(name)
	
		self.GUI.nb.forget(id)
	
		self.Menus.remove(menu)
	
	def identifyMenuBasedOnName(self, name):
		for menu in self.Menus:
			if menu['name'] == name:
				return menu
		return None
		
	def selectMenu(self, menu):
		if menu not in self.Menus:
			return
			
		self.GUI.elementManager.disselectElement()
		self.GUI.elementManager.propertiesManagment.clearProperties()
		
		self.GUI.canvas = menu['canvas']
		self.GUI.elementManager.canvas = menu['canvas']
		self.GUI.elementManager.elements = menu['elements']
		
		self.GUI.elementManager.propertiesManagment.updateElementList()
		
		
		