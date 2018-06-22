'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''

import cod2_default_element_settings

from Tkinter 	import *
from ttk		import *

class Manage:
	def __init__(self, GUI):
		self.elements = {}
		
		self.GUI = GUI
		
		self.canvas = GUI.canvas
		self.images = GUI.guiImages
		
		self.settings = {
			'defaultPos': [640/2, 480/2],
		
		}
		
		self.selectedElement = -1
		
	def createLabelElement(self):
		element = {
			'type': 'label',
		
			'properties': cod2_default_element_settings.labelSettings.copy(),
		
			'text': 'Example Text',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [124,48],
			'size': 12,
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		
		
		
		
		element['bbox'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="Rosy Brown1", width=2, state = 'hidden')
		element['move'] = self.canvas.create_image(0, 0, image=self.images['move'], state = 'hidden')
		element['moveF'] = self.canvas.create_image(0, 0, image=self.images['moveF'], state = 'hidden')
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.elements[elementID] = element
		
		self.selectElement(elementID)
		
	def calculateCords(self, element):
		self.canvas.coords(element['bbox'], element['pos'][0],  element['pos'][1],  element['pos'][0]+ element['rect'][0],  element['pos'][1]+ element['rect'][1] )
		self.canvas.coords(element['id'], element['pos'][0],  element['pos'][1] )
		self.canvas.coords(element['move'], element['pos'][0]+element['rect'][0]/2,  element['pos'][1]+ element['rect'][1]/2)
		self.canvas.coords(element['moveF'], element['pos'][0]+element['rect'][0]/2,  element['pos'][1]+ element['rect'][1]/2)
		
		
	def buttonPress(self, event):
		self.selectOnPress(event.x, event.y)
		
		
		if not self.selectedElement in self.elements:
			return	
		
		self.elements[self.selectedElement]['offsetMoveX'] = event.x - self.elements[self.selectedElement]['pos'][0]
		self.elements[self.selectedElement]['offsetMoveY'] = event.y - self.elements[self.selectedElement]['pos'][1]
		
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'normal' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], outline="dark red" )
	
	def selectOnPress(self, x, y):
		for elementID in self.elements:
			element = self.elements[elementID]
			
			if self.inside(x,y, ((element['pos'][0], element['pos'][1] ), (element['pos'][0]+element['rect'][0], element['pos'][1]+element['rect'][1])) ):
				self.selectElement(elementID)
				return
	
		self.disselectElement()
		self.clearProperties()
	
	def inside(self, x, y, ((ax,ay), (bx,by) ) ):
		return (x > ax and x < bx) and (y > ay and y < by)
	
	def disselectElement(self):
		if not self.selectedElement in self.elements:
			return
	
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], state = 'hidden' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['move'], state = 'hidden' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'hidden' )
	
		self.selectedElement = -1
	
	def selectElement(self, elementID):
		oldSelect = self.selectedElement
	
		if self.selectedElement in self.elements:
			self.disselectElement()
	
		self.selectedElement = elementID
		
		self.canvas.itemconfigure(self.elements[elementID]['bbox'], state = 'normal' )
		self.canvas.itemconfigure(self.elements[elementID]['move'], state = 'normal' )
		
		self.calculateCords(self.elements[elementID])
	
		if oldSelect != elementID:
			self.updatePorperties(elementID)
	
	
	def clearProperties(self):
		_list = self.GUI.f3.winfo_children()
	
		for widget in _list:
			widget.destroy()
	
	def updatePorperties(self, elementID):
		self.clearProperties()
		
		if not elementID in self.elements:
			return
	
		element = self.elements[elementID]
	
		row = 0
		for property in element['properties']:
			value = element['properties'][property][0]
			flags = element['properties'][property][1].split('|')
	
			Label(self.GUI.f3, text = property+': ').grid(row = row, column = 0, sticky=W)
	
			if 'E' in flags:
				e = Entry(self.GUI.f3)
				e.grid(row=row,column=1,sticky=W,pady=3)
				
			elif 'OM' in flags:
				values = self.getValues(flags)
			
				o = OptionMenu(self.GUI.f3, StringVar(), *values)
				o.grid(row=row,column=1,sticky=W,pady=3)
				
			elif 'CB' in flags:
				values = self.getValues(flags)
				
				o = Combobox(self.GUI.f3)
				o['values'] = values
				o.grid(row=row,column=1,sticky=W,pady=3)
				
	
			row += 1
	
	def getValues(self, flags):
		values = []
		for flag in flags:
			if flag in cod2_default_element_settings.globalDefinitions:
				for value in cod2_default_element_settings.globalDefinitions[flag]:
					values.append(value)
		return values
	
	def buttonRelease(self, event):
		if not self.selectedElement in self.elements:
			return
			
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'hidden' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], outline="Rosy Brown1" )
		
	def buttonMotion(self, event):
		if not self.selectedElement in self.elements:
			return	
	
		self.elements[self.selectedElement]['pos'][0] = event.x - self.elements[self.selectedElement]['offsetMoveX']
		self.elements[self.selectedElement]['pos'][1] = event.y - self.elements[self.selectedElement]['offsetMoveY']
		
		self.calculateCords(self.elements[self.selectedElement])
		
		
		
		
		
		
		
		
		
		
		
		