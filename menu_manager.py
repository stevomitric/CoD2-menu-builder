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

class MenuManager:
	def __init__(self, GUI):
		self.GUI = GUI
		
		self.Menus = []
		
		
	def createMenu(self):
		menu = {
			'frame': Frame(),			
			'elements': {},
		}
		
		menu['canvas'] = Canvas(menu['frame'], width = 640, height = 480)
		menu['canvas'].grid(row=0,column=0)
		
		
		menu['canvas'].bind('<ButtonPress-1>', self.GUI.elementManager.buttonPress)
		menu['canvas'].bind('<ButtonRelease-1>', self.GUI.elementManager.buttonRelease)
		menu['canvas'].bind('<B1-Motion>', self.GUI.elementManager.buttonMotion)
		
		self.GUI.nb.add(menu['frame'], text = 'Menu1')
		
		self.Menus.append(menu)
		
		self.selectMenu(menu)
		
	def selectMenu(self, menu):
		if menu not in self.Menus:
			return
		
		self.GUI.canvas = menu['canvas']
		self.GUI.elementManager.canvas = menu['canvas']
		self.GUI.elementManager.elements = menu['elements']
		
		
		
		
		