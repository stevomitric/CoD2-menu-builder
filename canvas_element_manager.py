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
import canvas_element_properties


import copy, tkMessageBox

from Tkinter 	import *
from ttk		import *

class Manage:
	def __init__(self, GUI):	
		self.GUI = GUI
		
		self.elements = {}
		self.canvas = GUI.canvas
		
		self.images = GUI.guiImages
		self.propertiesManagment = canvas_element_properties.Properties(self)
		
		
		self.settings = {
			'defaultPos': [640/2, 480/2],
		
		}
		
		self.selectedElement = -1
		
	def createLabelElement(self):
		element = {
			'type': 'label',
		
			'properties': copy.deepcopy(cod2_default_element_settings.labelSettings),
		
			'text': 'Example Text',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		
		
		
		
		element['bbox'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="Rosy Brown1", width=2, state = 'hidden')
		element['move'] = self.canvas.create_image(0, 0, image=self.images['move'], state = 'hidden')
		element['moveF'] = self.canvas.create_image(0, 0, image=self.images['moveF'], state = 'hidden')
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'sw')
		element['id'] = elementID
		
		self.elements[elementID] = element
		
		self.selectElement(elementID)
		
		self.propertiesManagment.updateElementList()
		
	def calculateCords(self, element):
		self.canvas.coords(element['bbox'], element['pos'][0],  element['pos'][1],  element['pos'][0]+ element['rect'][2],  element['pos'][1]-element['rect'][3] )
		self.canvas.coords(element['id'], element['pos'][0],  element['pos'][1] )
		self.canvas.coords(element['move'], element['pos'][0]+element['rect'][2]/2,  element['pos'][1]- element['rect'][3]/2)
		self.canvas.coords(element['moveF'], element['pos'][0]+element['rect'][2]/2,  element['pos'][1]- element['rect'][3]/2)
		
	def updateOnProperty(self):
		if not self.selectedElement in self.elements:
			return
		
		element = self.elements[self.selectedElement]
		
		
		# Text
		if element['properties'].has_key('text'):
			newValue = element['properties']['text'][2].var.get()
			if element['text'] != newValue:
				element['text'] = newValue
				self.canvas.itemconfigure(element['id'], text = element['text'])
				self.propertiesManagment.updateElementList()
		
		
		# Position (origin)
		if element['properties'].has_key('origin'):
			newValue = element['properties']['origin'][2].var.get()
			if str(element['pos'][0]) + " " + str(element['pos'][1]) != newValue:
				try:
					element['pos'] = [int(newValue.split(' ')[0]), int(newValue.split(' ')[1])]
				except:
					return
		
		# Rectangle
		if element['properties'].has_key('rect'):
			newValue = element['properties']['rect'][2].var.get()
			if str(element['rect']).replace('[','').replace(']', '').replace(',','') != newValue:
				try:
					element['rect'] = [int(newValue.split(' ')[0]), int(newValue.split(' ')[1]), int(newValue.split(' ')[2]), int(newValue.split(' ')[3]), int(newValue.split(' ')[4]) , int(newValue.split(' ')[5])]
					tkMessageBox.showinfo('Warning 001', 'Changing "rect" value may result in unwanted positioning of elements. The last two arguments represent widget alignment. They have been set to HORIZONTAL_ALIGN_FULLSCREEN and VERTICAL_ALIGN_FULLSCREEN (4 4) which means that item will "stretch", following players aspect-ratio.')
				except:
					self.propertiesManagment.setBadPropertyOption(element['id'], 'rect')
					return
			
				self.calculateCords(element)
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'rect')
			
		
		# Font size (textscale)
		if element['properties'].has_key('textscale'):
			try:
				newValue = float(cod2_default_element_settings.getValueFromKey(element['properties']['textscale'][2].var.get()))
			except:
				newValue = element['size']
				self.propertiesManagment.setBadPropertyOption(element['id'], 'textscale')
				return
				
			if element['size'] != newValue:
				element['size'] = newValue
				self.canvas.itemconfigure(element['id'], font = "default "+str(int(element['size']*31.3) ) )
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'textscale')
		
	def updateOnPropertyNonElement(self, element):
		
		# Name
		if element['properties'].has_key('name'):
			newValue = element['properties']['name'][2].var.get()
			
			if element['properties']['name'] != newValue:
				if element['type'] == 'menu':
					self.GUI.MenuManager.updateTabName( self.GUI.nb.select(), newValue )
		
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
			
			if self.inside(x,y, ((element['pos'][0], element['pos'][1]-element['rect'][3] ), (element['pos'][0]+element['rect'][2], element['pos'][1]) ) ):
				self.selectElement(elementID)
				return
	
		self.disselectElement()
		self.propertiesManagment.clearProperties()
	
	def inside(self, x, y, ((ax,ay), (bx,by) ) ):
		return (x > ax and x < bx) and (y > ay and y < by)
	
	def removeAll(self):
		self.disselectElement()
		
		self.canvas.delete("all")
		self.elements = {}
	
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
			self.propertiesManagment.updatePorperties(elementID)


	
	def updatePositionPorperties(self, elementID):
		widget = self.elements[self.selectedElement]['properties']['origin'][2]
		value = self.elements[self.selectedElement]['properties']['origin'][0]
		
		if not widget:
			return
	
		widget.delete('0', 'end')
		widget.insert('0', value)
	
	def listboxSelect(self):
		try:
			index = int(self.GUI.lb1.curselection()[0])
			elementID = int(self.GUI.lb1.get(index).split('(', 1)[1].split(')', 1)[0])
		except:
			return
	
		self.selectElement(elementID)
	
	def buttonRelease(self, event):
		if not self.selectedElement in self.elements:
			return
			
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'hidden' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], outline="Rosy Brown1" )
		
	def updatePosiotionValue(self, elementID):
		if not elementID in self.elements:
			return	
	
		self.elements[elementID]['properties']['origin'][0] = str(self.elements[elementID]['pos'][0]) + " " + str(self.elements[elementID]['pos'][1])
		self.updatePositionPorperties(elementID)
		
	def buttonMotion(self, event):
		if not self.selectedElement in self.elements:
			return	
	
		self.elements[self.selectedElement]['pos'][0] = event.x - self.elements[self.selectedElement]['offsetMoveX']
		self.elements[self.selectedElement]['pos'][1] = event.y - self.elements[self.selectedElement]['offsetMoveY']
		
		self.updatePosiotionValue(self.selectedElement)
		
		self.calculateCords(self.elements[self.selectedElement])
		
		
		
		
		
		
		
		
		
		
		
		