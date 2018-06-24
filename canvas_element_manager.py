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
		
			'autoUpdateBBOX': True,
		}
		
		self.selectedElement = -1
	
	def createButtonElement(self):
		element = {
			'type': 'button',
			'badArgument': [],
			'name': 'button',
		
			'properties': copy.deepcopy(cod2_default_element_settings.buttonSettings),
		
			'text': 'Example Button',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			'bold': '',
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
	
		element['bbox'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="Rosy Brown1", width=2, state = 'hidden')
		element['border'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="Rosy Brown1", width=2, state = 'hidden')
		element['move'] = self.canvas.create_image(0, 0, image=self.images['move'], state = 'hidden')
		element['moveF'] = self.canvas.create_image(0, 0, image=self.images['moveF'], state = 'hidden')
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.elements[elementID] = element
		
		self.selectElement(elementID)

		self.propertiesManagment.updateElementList()
		
		self.calculateCords(element)
	
	def createLabelElement(self):
		element = {
			'type': 'label',
			'badArgument': [],
			'name': 'label',
		
			'properties': copy.deepcopy(cod2_default_element_settings.labelSettings),
		
			'text': 'Example Text',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			'bold': '',
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		
		
		
		
		element['bbox'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="Rosy Brown1", width=2, state = 'hidden')
		element['border'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="Rosy Brown1", width=2, state = 'hidden')
		element['move'] = self.canvas.create_image(0, 0, image=self.images['move'], state = 'hidden')
		element['moveF'] = self.canvas.create_image(0, 0, image=self.images['moveF'], state = 'hidden')
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.elements[elementID] = element
		
		self.selectElement(elementID)
		
		self.propertiesManagment.updateElementList()
	
		self.calculateCords(element)
	
	def updateRectSizeBasedOnFont(self, element):
		if not self.settings['autoUpdateBBOX']:
			return
	
		x1, y1, x2, y2 = self.canvas.bbox(element['id'])
		
		element['rect'][2] = x2-x1
		element['rect'][3] = y2-y1
		
		element['properties']['rect'][2].var.set(' '.join(str(x) for x in element['rect']))
		
		self.calculateCords(element)
		
	def calculateCords(self, element):
		self.canvas.coords(element['bbox'], element['pos'][0],  element['pos'][1],  element['pos'][0]+ element['rect'][2],  element['pos'][1]+element['rect'][3] )

		self.canvas.coords(element['id'], element['pos'][0],  element['pos'][1] )
		self.canvas.coords(element['move'], element['pos'][0]+element['rect'][2]/2,  element['pos'][1]+ element['rect'][3]/2)
		self.canvas.coords(element['moveF'], element['pos'][0]+element['rect'][2]/2,  element['pos'][1]+ element['rect'][3]/2)
		
		if element.has_key('border'):
			self.canvas.coords(element['border'], element['pos'][0],  element['pos'][1],  element['pos'][0]+ element['rect'][2],  element['pos'][1]+element['rect'][3] )
		
		if element['properties'].has_key('textaligny') and element['properties']['textaligny'][2] != None:
			element['properties']['textaligny'][2].var.set(str(element['rect'][3]))
		
	def updateOnProperty(self, element = None):
		
		if element == None:
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
				self.updateRectSizeBasedOnFont(element)
				
		
		# Position (origin)
		if element['properties'].has_key('origin'):
			newValue = element['properties']['origin'][2].var.get()
			if str(element['pos'][0]) + " " + str(element['pos'][1]) != newValue:
				try:
					element['pos'] = [int(newValue.split(' ')[0]), int(newValue.split(' ')[1])]
				except:
					return
		
				self.calculateCords(element)
		
		# Rectangle
		if element['properties'].has_key('rect'):
			newValue = element['properties']['rect'][2].var.get()
			if str(element['rect']).replace('[','').replace(']', '').replace(',','') != newValue or 'rect' in element['badArgument']:
				try:
					element['rect'] = [int(newValue.split(' ')[0]), int(newValue.split(' ')[1]), int(newValue.split(' ')[2]), int(newValue.split(' ')[3]), int(newValue.split(' ')[4]) , int(newValue.split(' ')[5])]
					if element['rect'][4] != 4 or element['rect'][5] != 4:
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
				
			if element['size'] != newValue or 'textscale' in element['badArgument']:
				element['size'] = newValue
				self.canvas.itemconfigure(element['id'], font = ("default ", str(int(element['size']*32)), element['bold'] ) )
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'textscale')
				self.updateRectSizeBasedOnFont(element)
		
		# bold 
		if element['properties'].has_key('textfont'):
			newValue = cod2_default_element_settings.getValueFromKey(element['properties']['textfont'][2].var.get())
		
			if element['bold'] != newValue:
				element['bold'] = newValue
				self.canvas.itemconfigure(element['id'], font = ("default ", str(int(element['size']*32)), element['bold'] ) )
				self.updateRectSizeBasedOnFont(element)
		
		
		
		# Font colour (forecolor)
		if element['properties'].has_key('forecolor'):
			newValue = cod2_default_element_settings.getValueFromKey(element['properties']['forecolor'][2].var.get())

			if element['colour'] != newValue or 'forecolor' in element['badArgument']:
				try:
					rgb = self.getRGBA(newValue)[0:3]
				except:
					self.propertiesManagment.setBadPropertyOption(element['id'], 'forecolor')
					return
					
				element['colour'] = newValue
				self.canvas.itemconfigure(element['id'], fill = self.RGBtoHex(rgb) )
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'forecolor')
		
		# Name
		if element['properties'].has_key('name'):
			newValue = element['properties']['name'][2].var.get()
			
			if element['name'] != newValue:
				self.propertiesManagment.updateElementList()
				element['name'] = newValue
		
		
		# Border
		if element['properties'].has_key('border'):
			newValue = cod2_default_element_settings.getValueFromKey(element['properties']['border'][2].var.get())
			
			if newValue == '1':
				self.canvas.itemconfigure(element['border'], state = 'normal')
			else:
				self.canvas.itemconfigure(element['border'], state = 'hidden')
				
		# Bordercolour
		if element['properties'].has_key('bordercolor'):
			newValue = cod2_default_element_settings.getValueFromKey(element['properties']['bordercolor'][2].var.get())
			try:
				rgb = self.getRGBA(newValue)[0:3]
			except:
				self.propertiesManagment.setBadPropertyOption(element['id'], 'bordercolor')
				return
				
			self.canvas.itemconfigure(element['border'], outline = self.RGBtoHex(rgb))
			self.propertiesManagment.setGoodPropertyOption(element['id'], 'bordercolor')
		
	def updateOnPropertyNonElement(self, element):
		
		# Name
		if element['properties'].has_key('name'):
			newValue = element['properties']['name'][2].var.get()
			
			if element['name'] != newValue:
				if element['type'] == 'menu':
					self.GUI.MenuManager.updateTabName( self.GUI.nb.select(), newValue )
					element['name'] = newValue
		
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
			
			if self.inside(x, y, ((element['pos'][0], element['pos'][1] ), (element['pos'][0]+element['rect'][2], element['pos'][1]+element['rect'][3]) ) ):
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
	
	def disselectElement(self, clearListbox = True):
		if not self.selectedElement in self.elements:
			return
	
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], state = 'hidden' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['move'], state = 'hidden' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'hidden' )
	
		self.selectedElement = -1
		
		if clearListbox:
			self.GUI.lb1.selection_clear(0, END)
	
	def selectElement(self, elementID, clearListbox = True):
		oldSelect = self.selectedElement
	

		if self.selectedElement in self.elements:
			self.disselectElement(clearListbox)
	
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
	
		self.selectElement(elementID, clearListbox = False)
	
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
		
		
	def RGBtoHex(self, rgb):
		return '#%02x%02x%02x' % rgb
		
	def getRGBA(self, _str):
		rgba = ( float(_str.split(' ')[0] )*255, float(_str.split(' ')[1] )*255, float(_str.split(' ')[2] )*255, float(_str.split(' ')[3] )*255 )
		
		if rgba[0] > 255 or rgba[1] > 255 or rgba[2] > 255:
			raise RuntimeError
		
		return rgba
		
		