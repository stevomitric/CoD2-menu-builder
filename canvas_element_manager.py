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


import copy, tkMessageBox, translator

from Tkinter 	import *
from ttk		import *
from PIL		import Image, ImageTk

class Manage:
	def __init__(self, GUI):	
		self.GUI = GUI
		
		self.elements = {}
		self.canvas = GUI.canvas
		
		self.images = GUI.guiImages
		self.propertiesManagment = canvas_element_properties.Properties(self)
		
		
		self.settings = {
			'defaultPos': [640/2, 480/2],
		
			'autoUpdateBBOX': False,
			'autoAlignText': False,
			'snapping': 20,
			'isSnapping': False,
			
			'originPoint': [0 ,0],
			
			'orderNum': 1,
		}
		
		self.selectedElement = -1
		self.copiedElement = -1
		self.keyPressed = {}
	
	def createRectElement(self):
		element = {
			'type': 'rect',
			'badArgument': [],
			'name': 'rect',
			'supportsScalle': 1,
		
			'properties': copy.deepcopy(cod2_default_element_settings.rectSettings),
			'image': Image.new('RGBA', (200, 200), (0,0,0,128) ),
			
			'backImageColour': (0, 0, 0, 128),
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,200,200, 4, 4],
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		element['imageR'] = ImageTk.PhotoImage(element['image'])

		elementID = self.canvas.create_image( element['pos'][0], element['pos'][1], image = element['imageR'], anchor='nw' )
		element['id'] = elementID

		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)
		
		return elementID
		
	def createImageElement(self, imageID=''):
		if not self.GUI.guiRawImageData.has_key(imageID):
			self.GUI.guiRawImageData[imageID] = Image.new('RGBA', (1, 1), (0,0,0,0) )
	
		element = {
			'type': 'image',
			'badArgument': [],
			'name': 'image',
			'supportsScalle': 1,
		
			'properties': copy.deepcopy(cod2_default_element_settings.imageSettings),
			'imageOriginal': self.GUI.guiRawImageData[imageID],
			'image': self.GUI.guiRawImageData[imageID],
			
			'style': 'WINDOW_STYLE_SHADER',
			
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,self.GUI.guiRawImageData[imageID].size[0],self.GUI.guiRawImageData[imageID].size[1], 4, 4],
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		element['imageR'] = ImageTk.PhotoImage(element['image'])
		element['properties']['rect'][0] = " ".join( str(i) for i in element['rect'] )
		element['properties']['background'][0] = imageID[3:]
		
		elementID = self.canvas.create_image( element['pos'][0], element['pos'][1], image = element['imageR'], anchor='nw' )
		element['id'] = elementID

		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)	
		return elementID
		
	def createButtonElement(self):
		element = {
			'type': 'button',
			'badArgument': [],
			'name': 'button',
			'supportsScalle': 1,
			'supportBackImage': 1,
		
			'properties': copy.deepcopy(cod2_default_element_settings.buttonSettings),

			'style': 'WINDOW_STYLE_EMPTY',
			'colour': 'black',
			'text': 'Example Button',
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			'bold': '',
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}

		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)
		return elementID
		
	def createFieldElement(self):
		element = {
			'type': 'field',
			'badArgument': [],
			'name': 'field',
			'supportsScalle': 1,
			'supportBackImage': 1,
		
			'properties': copy.deepcopy(cod2_default_element_settings.fieldSettings),
		
			'text': 'You typed:',
			'style': 'WINDOW_STYLE_EMPTY',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			'bold': '',
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)	
		return elementID
	
	def createSliderElement(self):
		element = {
			'type': 'slider',
			'badArgument': [],
			'name': 'slider',
			'supportsScalle': 1,
			'supportBackImage': 1,
			
			'properties': copy.deepcopy(cod2_default_element_settings.sliderSettings),
			
		
			'style': 'WINDOW_STYLE_EMPTY',
			'text': 'Example Slider',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			'bold': '',
			
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		
		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)
		return elementID
	
	def createLabelElement(self):
		element = {
			'type': 'label',
			'badArgument': [],
			'name': 'label',
			'supportsScalle': 1,
		
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
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)
		
		return elementID
		
	def createListElement(self):
		element = {
			'type': 'list',
			'badArgument': [],
			'name': 'list',
			'supportsScalle': 1,
			'supportBackImage': 1,
		
			'properties': copy.deepcopy(cod2_default_element_settings.listSettings),
		
			'style': 'WINDOW_STYLE_EMPTY',
			'text': 'You have chosen: ',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			'bold': '',
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)
	
		return elementID
		
	def createItemElement(self):
		element = {
			'type': 'item',
			'badArgument': [],
			'name': 'item',
			'supportsScalle': 1,
			'supportBackImage': 1,
		
			'properties': copy.deepcopy(cod2_default_element_settings.itemSettings),

			'image': Image.new('RGBA', (1,1), (0,0,0,1) ),
			'imageOriginal': Image.new('RGBA', (1,1), (0,0,0,1) ),
			'imageR': '',
			'background': '',
			
			'style': 'WINDOW_STYLE_EMPTY',
			'colour': 'black',
			'text': 'Example Button',
			'pos': [0,0],
			'rect': [0,0,128,24, 4, 4],
			'size': 12,
			'bold': '',
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}

		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.initElementIcons(element)
		self.elements[elementID] = element
		self.selectElement(elementID)
		self.propertiesManagment.updateElementList()
		self.calculateCords(element)
		
		return elementID
		
	def initElementIcons(self, element):
		element['bbox'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="#f4a273", width=2, state = 'hidden')
		element['border'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="black", width=2, state = 'hidden')
		element['move'] = self.canvas.create_image(0, 0, image=self.images['move'], state = 'hidden')
		element['moveF'] = self.canvas.create_image(0, 0, image=self.images['moveF'], state = 'hidden')
		element['moveG'] = self.canvas.create_image(0, 0, image=self.images['ICONmoveg'], state = 'hidden')
		element['invisible'] = self.canvas.create_image(0, 0, image=self.images['ICONinvisible'], state = 'hidden')
		
		if not element.has_key('supportsScalle'):
			self.canvas.itemconfigure(element['moveG'], image = '')	
			
		if element.has_key('background'):
			element['background'] = self.canvas.create_image(0, 0, image='', anchor = 'nw')
	
		if element.has_key('supportBackImage'):
			element['backImage'] = Image.new('RGBA', (200, 200), (0,0,0,128) )
			element['backImageColour'] = (0, 0, 0, 128)
			element['backImageC'] = self.canvas.create_image(0, 0, image='', anchor = 'nw')
	
		if element['type'] == 'slider':
			self.initSlider(element)
	
		element['order'] = self.getOrder()
	
	def initSlider(self, element):
		element['sliderImageorg'] = self.GUI.guiRawImageData['slider']
		element['sliderImageR'] = ImageTk.PhotoImage(element['sliderImageorg'])
		element['sliderImage'] = self.canvas.create_image(0, 0, image= element['sliderImageR'], anchor = 'nw')

	def updateRectSizeBasedOnFont(self, element):
		if not self.settings['autoUpdateBBOX'] or not element.has_key('text'):
			return
	
		x1, y1, x2, y2 = self.canvas.bbox(element['id'])
		
		element['rect'][2] = x2-x1
		element['rect'][3] = y2-y1
		
		if element['type'] == 'field':
			element['rect'][2] += 100
		
		if element.has_key('sliderImageorg'):
			element['rect'][2] += 150
		
		element['properties']['rect'][2].var.set(' '.join(str(x) for x in element['rect']))
		
		self.calculateCords(element, updateImage = True)
		
	def calculateTextAligment(self, element):
		allowrdtypes = ['label', 'item', 'button', 'slider', 'field', 'list']
		
		if element['type'] not in allowrdtypes or not element['properties'].has_key('textaligny'):
			return
	
		x, y = self.canvas.coords(element['id'])
		x1, y1, x2, y2 = self.canvas.bbox(element['id'])
		
		y -= y2-y1
		
		if self.settings['autoAlignText']:
			value = y2-y1
			alignY = element['properties']['textaligny'][0] = str(value)
			if element['properties']['textaligny'][2] != None:
				element['properties']['textaligny'][2].var.set(str(value))
		
		alignX = int(element['properties']['textalignx'][0])
		alignY = int(element['properties']['textaligny'][0])
		
		x+=alignX
		y+=alignY
		
		self.canvas.coords(element['id'], (x,y) )
		
		
	def calculateCords(self, element, updateImage = False):
		self.calculateOriginPoint(element)
	
		self.canvas.coords(element['bbox'], (element['pos'][0]+element['originPoint'][0]+element['rect'][0]),  (element['pos'][1]+element['originPoint'][1]+element['rect'][1]), (element['pos'][0]+element['originPoint'][0]+ element['rect'][2]+element['rect'][0]),  (element['pos'][1]+element['originPoint'][1]+element['rect'][3]+element['rect'][1]) )

		self.canvas.coords(element['id'], element['pos'][0]+element['originPoint'][0]+element['rect'][0],  element['pos'][1]+element['originPoint'][1]+element['rect'][1] )
		self.canvas.coords(element['move'], element['pos'][0]+element['originPoint'][0]+element['rect'][0]+element['rect'][2]/2,  element['pos'][1]+element['originPoint'][1]+element['rect'][1]+ element['rect'][3]/2)
		self.canvas.coords(element['moveF'], element['pos'][0]+element['originPoint'][0]+element['rect'][0]+element['rect'][2]/2,  element['pos'][1]+element['originPoint'][1]+element['rect'][1]+element['rect'][3]/2)
		self.canvas.coords(element['moveG'], element['pos'][0]+element['originPoint'][0]+element['rect'][2]+element['rect'][0],  element['pos'][1]+element['originPoint'][1]+ element['rect'][3]+element['rect'][1])
		self.canvas.coords(element['invisible'], element['pos'][0]+element['originPoint'][0],  element['pos'][1]+element['originPoint'][1])
		
		self.calculateTextAligment(element)
		
		if element.has_key('border'):
			self.canvas.coords(element['border'], element['pos'][0]+element['originPoint'][0]+element['rect'][0],  element['pos'][1]+element['originPoint'][1]+element['rect'][1],  element['pos'][0]+element['originPoint'][0]+element['rect'][0]+ element['rect'][2],  element['pos'][1]+element['originPoint'][1]+element['rect'][1]+element['rect'][3] )

			
		if element.has_key('supportBackImage'):
			self.canvas.coords(element['backImageC'], element['pos'][0]+element['originPoint'][0]+element['rect'][0],  element['pos'][1]+element['originPoint'][1]+element['rect'][1] )
			
		if element.has_key('background'):
			self.canvas.coords(element['background'], element['pos'][0]+element['originPoint'][0],  element['pos'][1]+element['originPoint'][1] )
		
		if element['type'] == 'rect':
			if updateImage:
				try:
					element['image'] = Image.new('RGBA', (element['rect'][2], element['rect'][3]), element['backImageColour'] )
					element['imageR'] = ImageTk.PhotoImage(element['image'])
					self.canvas.itemconfigure(element['id'], image = element['imageR'])
				except: pass
		
		if element['type'] == 'image' or element['properties'].has_key('background'):
			if updateImage:
				try:
					element['image'] = element['imageOriginal'].resize((element['rect'][2]+element['rect'][0], element['rect'][3]+element['rect'][1]), Image.ANTIALIAS )
					element['imageR'] = ImageTk.PhotoImage(element['image'])
					if element['type'] == 'image': self.canvas.itemconfigure(element['id'], image = element['imageR'])
					else: self.canvas.itemconfigure(element['background'], image = element['imageR'])
				except: pass
				
			if element['style'] != 'WINDOW_STYLE_SHADER':
				if element['type'] == 'image': self.canvas.itemconfigure(element['backImageC'], image = '')
				else: self.canvas.itemconfigure(element['background'], image = '' )
					
		if element.has_key('sliderImageorg'):
			x1, y1, x2, y2 = self.canvas.bbox(element['id'])
			value = x2-x1
			element['sliderImageR'] = ImageTk.PhotoImage(element['sliderImageorg'])
			self.canvas.coords(element['sliderImage'], element['pos'][0]+element['rect'][0]+element['originPoint'][0]+value,  element['pos'][1]+element['rect'][1]+element['originPoint'][1])
			self.canvas.itemconfigure(element['sliderImage'], image = element['sliderImageR'])
		
		if element.has_key('supportBackImage'):
			if updateImage:

				if element['style'] != 'WINDOW_STYLE_FILLED':
					self.canvas.itemconfigure(element['backImageC'], image = '')
				else:
					try:
						element['backImage'] = Image.new('RGBA', (element['rect'][2], element['rect'][3]), element['backImageColour'] )
						element['backImageR'] = ImageTk.PhotoImage(element['backImage'])
						self.canvas.itemconfigure(element['backImageC'], image = element['backImageR'])
					except: pass
		
		
	def updateOnProperty(self, element = None, property = None):
		
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
				
				if element['type'] == 'list' or (element['properties'].has_key('dvarFloatList') and element['properties']['type'] == 'ITEM_TYPE_MULTI'):
					self.updateListText(element)
				
				self.propertiesManagment.updateElementList()
				self.updateRectSizeBasedOnFont(element)
				self.calculateCords(element, updateImage = True)
		
		# Position (origin)
		if element['properties'].has_key('origin') and property == 'origin':
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['origin'][2].var.get())
			if str(element['pos'][0]) + " " + str(element['pos'][1]) != newValue:
				try:
					element['pos'] = [int(newValue.split(' ')[0]), int(newValue.split(' ')[1])]
				except:
					return
		
				self.calculateCords(element)
		
		# Rectangle
		if element['properties'].has_key('rect'):
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['rect'][2].var.get())
			if str(element['rect']).replace('[','').replace(']', '').replace(',','') != newValue or 'rect' in element['badArgument']:
				try:
					element['rect'] = [int(newValue.split(' ')[0]), int(newValue.split(' ')[1]), int(newValue.split(' ')[2]), int(newValue.split(' ')[3]), int(newValue.split(' ')[4]) , int(newValue.split(' ')[5])]
					if element['rect'][4] ==5  or element['rect'][5] == 5 or element['rect'][4] ==6  or element['rect'][5] == 6:
						tkMessageBox.showinfo('Warning 001', '''You have set elements alignment to "noscale" and what that means is positional and size properties of element will not change on different resolutions (different from 640x480). This is probably not what you wanted (unles you know what youre doing) ''')
				except:
					self.propertiesManagment.setBadPropertyOption(element['id'], 'rect')
					return
			
				self.calculateCords(element, updateImage = True)
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'rect')
			
		
		# Font size (textscale)
		if element['properties'].has_key('textscale'):
			try:
				newValue = float(cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['textscale'][2].var.get()))
			except:
				newValue = element['size']
				self.propertiesManagment.setBadPropertyOption(element['id'], 'textscale')
				return
				
			if element['size'] != newValue or 'textscale' in element['badArgument']:
				element['size'] = newValue
				self.canvas.itemconfigure(element['id'], font = ("default ", str(int(element['size']*32)), element['bold'] ) )
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'textscale')
				self.updateRectSizeBasedOnFont(element)
				self.calculateCords(element)
				
		
		# bold 
		if element['properties'].has_key('textfont'):
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['textfont'][2].var.get())
		
			if element['bold'] != newValue:
				element['bold'] = newValue
				self.canvas.itemconfigure(element['id'], font = ("default ", str(int(element['size']*32)), element['bold'] ) )
				self.updateRectSizeBasedOnFont(element)
		
		
		
		# forecolor
		if element['properties'].has_key('forecolor'):
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['forecolor'][2].var.get())

			if element['colour'] != newValue or 'forecolor' in element['badArgument']:
				try:
					rgba = self.getRGBA(newValue)
					rgb = rgba[0:3]
				except:
					self.propertiesManagment.setBadPropertyOption(element['id'], 'forecolor')
					return
					
				if element.has_key('sliderImageorg'):
					self.reColorImage(rgba, element['sliderImageorg'])
					self.calculateCords(element, updateImage = True)
					
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
		if element['properties'].has_key('border') and property == 'border':
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['border'][2].var.get())
			if newValue == '1':
				self.canvas.itemconfigure(element['border'], state = 'normal')
			elif newValue == '0':
				self.canvas.itemconfigure(element['border'], state = 'hidden')
				
		# Bordercolour
		if element['properties'].has_key('bordercolor') and property == 'bordercolor':
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['bordercolor'][2].var.get())
			try:
				rgb = self.getRGBA(newValue)[0:3]
			except:
				self.propertiesManagment.setBadPropertyOption(element['id'], 'bordercolor')
				return
				
			self.canvas.itemconfigure(element['border'], outline = self.RGBtoHex(rgb))
			self.propertiesManagment.setGoodPropertyOption(element['id'], 'bordercolor')
		
		# Backcolour
		if element['properties'].has_key('backcolor') and property == 'backcolor':
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['backcolor'][2].var.get())
			try:
				rgba = self.getRGBA(newValue)[:]
			except:
				self.propertiesManagment.setBadPropertyOption(element['id'], 'backcolor')
				return
			
			element['backImageColour'] = rgba
			self.calculateCords(element, updateImage = True)
			self.propertiesManagment.setGoodPropertyOption(element['id'], 'backcolor')
		
		# Visible
		if element['properties'].has_key('visible') and property == 'visible':
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['visible'][2].var.get())
			
			if newValue == '1':
				self.canvas.itemconfigure(element['invisible'], state = 'hidden')
			else:
				self.canvas.itemconfigure(element['invisible'], state = 'normal')
		
		# Style
		if element['properties'].has_key('style') and property == 'style' and element.has_key('style'):
			newValue = element['properties']['style'][2].var.get()
		
			if element['style'] != newValue:
				element['style'] = newValue
				self.calculateCords(element, updateImage = True)
				
		# dvarFloatList
		if element['properties'].has_key('dvarFloatList') and property == 'dvarFloatList':
			self.updateListText(element)	
			
		# textalign
		if element['properties'].has_key('textalign') and property == 'textalign':
			newValue = element['properties']['textalign'][2].var.get()
			
			if newValue == 'ITEM_ALIGN_LEFT':
				self.canvas.itemconfigure(element['id'], anchor = 'nw')
			elif newValue == 'ITEM_ALIGN_CENTER':
				self.canvas.itemconfigure(element['id'], anchor = 'n')
			elif newValue == 'ITEM_ALIGN_RIGHT':
				self.canvas.itemconfigure(element['id'], anchor = 'ne')
				
		# background
		if element['properties'].has_key('background') and property == 'background':
			newValue = element['properties']['background'][2].var.get()
			if not newValue.startswith('COD'): newValue  = 'COD' + newValue
			
			if self.GUI.guiRawImageData.has_key(newValue):
				element['imageOriginal'] = self.GUI.guiRawImageData[newValue]
				element['image'] = self.GUI.guiRawImageData[newValue]
		
				element['imageR'] = ImageTk.PhotoImage(element['image'])
		
				self.calculateCords(element, updateImage = True)
				
		# textaligny
		if element['properties'].has_key('textaligny') and property == 'textaligny':
			try:
				newValue = int(element['properties']['textaligny'][2].var.get())
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'textaligny')
				self.calculateCords(element)
			except:
				self.propertiesManagment.setBadPropertyOption(element['id'], 'textaligny')
				
		# textalignx
		if element['properties'].has_key('textalignx') and property == 'textalignx':
			try:
				newValue = int(element['properties']['textalignx'][2].var.get())
				self.propertiesManagment.setGoodPropertyOption(element['id'], 'textalignx')
				self.calculateCords(element)
			except:
				self.propertiesManagment.setBadPropertyOption(element['id'], 'textalignx')
		
	def updateListText(self, element, property = 'dvarFloatList'):
		try:
			value = element['properties'][property][0].replace('{', '').replace(' ', '').split('"')[1]
			self.canvas.itemconfigure(element['id'], text = element['text'] + " " + value)
			self.propertiesManagment.setGoodPropertyOption(element['id'], property)
		except:
			self.propertiesManagment.setBadPropertyOption(element['id'], property)
		
	def updateOnPropertyNonElement(self, element, property):
		
		# Name
		if element['properties'].has_key('name'):
			newValue = element['properties']['name'][2].var.get()
			
			if element['name'] != newValue:
				if element['type'] == 'menu':
					self.GUI.MenuManager.updateTabName( self.GUI.nb.select(), newValue )
					element['name'] = newValue
		
		# Style
		if element['properties'].has_key('style'):
			newValue = element['properties']['style'][2].var.get()
		
			if element['style'] != newValue:
				element['style'] = newValue
				self.GUI.MenuManager.updateBackImage(element)
			
		# Backcolour
		if element['properties'].has_key('backcolor') and property == 'backcolor':
			newValue = cod2_default_element_settings.getMultipleValuesFromKey(element['properties']['backcolor'][2].var.get())
			try:
				rgba = self.getRGBA(newValue)[:]
			except:
				self.propertiesManagment.setBadPropertyOption('', 'backcolor', element)
				return
			
			element['backImageColour'] = rgba
			self.GUI.MenuManager.updateBackImage(element)
			self.propertiesManagment.setGoodPropertyOption('', 'backcolor', element)
		
		
	def buttonPress(self, event):
		if self.selectedElement in self.elements:
			element = self.elements[self.selectedElement]
			if self.inside(event.x, event.y, ((element['pos'][0]+element['originPoint'][0]+element['rect'][0], element['pos'][1]+element['originPoint'][1]+element['rect'][1] ), (element['pos'][0]+element['originPoint'][0]+element['rect'][0]+element['rect'][2], element['pos'][1]+element['originPoint'][1]+element['rect'][1]+element['rect'][3]) ) ):
				pass
			else:
				self.selectOnPress(event.x, event.y)
		else:
			self.selectOnPress(event.x, event.y)
				
		if not self.selectedElement in self.elements:
			return
		
		element = self.elements[self.selectedElement]
		
		self.elements[self.selectedElement]['offsetMoveX'] = event.x - self.elements[self.selectedElement]['pos'][0]+element['originPoint'][0]
		self.elements[self.selectedElement]['offsetMoveY'] = event.y - self.elements[self.selectedElement]['pos'][1]+element['originPoint'][1]
		
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'normal' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], outline="dark red" )
	
	def selectOnPress(self, x, y):
		elements = translator.getSortedDic(self.elements)[::-1]
		for element in elements:
			elementID = element['id']
			
			if element.has_key('supportsScalle') and self.selectedElement != -1 and self.inside(x, y, ((element['pos'][0]+element['originPoint'][0]+element['rect'][0]+element['rect'][2]-10, element['pos'][1]+element['originPoint'][1]+element['rect'][1] + element['rect'][3]-10 ), (element['pos'][0]+element['originPoint'][0]+element['rect'][0]+element['rect'][2]+10, element['pos'][1]+element['originPoint'][1]+element['rect'][1]+element['rect'][3]+10) ) ):
				element['scalling'] = [x,y]

				return
				
			elif self.inside(x, y, ((element['pos'][0]+element['originPoint'][0]+element['rect'][0], element['pos'][1]+element['originPoint'][1]+element['rect'][1] ), (element['pos'][0]+element['originPoint'][0]+element['rect'][0]+element['rect'][2], element['pos'][1]+element['originPoint'][1]+element['rect'][1]+element['rect'][3]) ) ):
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
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveG'], state = 'hidden' )
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
		self.canvas.itemconfigure(self.elements[elementID]['moveG'], state = 'normal' )
		
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
		element = self.elements[self.selectedElement]
			
		self.canvas.itemconfigure(element['moveF'], state = 'hidden' )
		self.canvas.itemconfigure(element['bbox'], outline="#f4a273" )
		
		if element.has_key('scalling'):
			element.pop('scalling')
		
	def updatePosiotionValue(self, elementID):
		if not elementID in self.elements:
			return	
	
		self.elements[elementID]['properties']['origin'][0] = str(self.elements[elementID]['pos'][0]) + " " + str(self.elements[elementID]['pos'][1])
		self.updatePositionPorperties(elementID)
		
	def updateRectValue(self, elementID):
		if not elementID in self.elements:
			return	
		element = self.elements[elementID]
	
		element['properties']['rect'][0] = " ".join( str(i) for i in element['rect'] )
		
		element['properties']['rect'][2].var.set(element['properties']['rect'][0])

		
	def rightButtonPress(self, event):
		if self.selectedElement not in self.elements:
			self.GUI.rightMenuPopupEvent(event)
			return
	
		self.GUI.rightMenuPopupEventSelected(event)
		
		
	def buttonMotion(self, event):
		if not self.selectedElement in self.elements:
			return
		element = self.elements[self.selectedElement]
	
		if element.has_key('scalling'):
			element['rect'][2] += event.x - element['scalling'][0]
			element['rect'][3] += event.y - element['scalling'][1]
			element['scalling'] = event.x, event.y
			
			if self.settings['isSnapping']:
				element['rect'][2], element['rect'][3] = self.fixSnap(element['rect'][2], element['rect'][3])
				element['scalling'] = self.fixSnap(event.x, event.y)
			
			self.calculateCords(element, updateImage = True)
			self.updateRectValue(self.selectedElement)
			
		else: 
			element['pos'][0] = event.x - element['offsetMoveX'] +element['originPoint'][0]
			element['pos'][1] = event.y - element['offsetMoveY'] +element['originPoint'][1]
		
			if self.settings['isSnapping']:
				element['pos'][0],element['pos'][1] = self.fixSnap(element['pos'][0],element['pos'][1])
		
			self.updatePosiotionValue(self.selectedElement)
		
			self.calculateCords(element)
		
	def copySelected(self):
		if self.selectedElement not in self.elements:
			return
		self.copiedElement = self.selectedElement
		
	def copyDataToFrom(self, ID1, ID2):
		doNotCopy = ['bbox', 'border', 'move', 'moveF', 'moveG', 'invisible', 'backImageC', 'id', 'imageR', 'sliderImage', 'sliderImageR', 'sliderImageorg']
		
		element1 = self.elements[ID1]
		element2 = self.elements[ID2]
		
		for data in element2:
			if data in doNotCopy:
				continue
			elif data == 'properties':
				for property in element2[data]:
					element1[data][property][0] = element2[data][property][0]
					element1[data][property][2].var.set(element2[data][property][2].var.get())
			
			else:
				element1[data] = copy.deepcopy(element2[data])
		
		self.calculateCords(element1, updateImage = True)
		
	def pasteSelected(self):
		if self.copiedElement not in self.elements:
			return
		
		element = self.elements[self.copiedElement]
		
		if element['type'] == 'rect':
			ID1 = self.createRectElement()
			self.copyDataToFrom(ID1, self.copiedElement)
		elif element['type'] == 'label':
			ID1 = self.createLabelElement()
			self.copyDataToFrom(ID1, self.copiedElement)
		elif element['type'] == 'image':
			ID1 = self.createImageElement()
			self.copyDataToFrom(ID1, self.copiedElement)
		elif element['type'] == 'button':
			ID1 = self.createButtonElement()
			self.copyDataToFrom(ID1, self.copiedElement)
		elif element['type'] == 'slider':
			ID1 = self.createSliderElement()
			self.copyDataToFrom(ID1, self.copiedElement)
		elif element['type'] == 'field':
			ID1 = self.createFieldElement()
			self.copyDataToFrom(ID1, self.copiedElement)
		elif element['type'] == 'list':
			ID1 = self.createListElement()
			self.copyDataToFrom(ID1, self.copiedElement)
		
		
	def deleteAllElements(self):
		for element in self.elements.copy():
			self.deleteElement(self.elements[element])
	
	def deleteElement(self, element = None):
		if element == None and self.selectedElement not in self.elements:
			return
		
		if not element:
			element = self.elements[self.selectedElement]
		
		canvasElements = ['bbox', 'border', 'move', 'moveF', 'moveG', 'invisible',  'backImageC', 'id', 'sliderImage']
		
		for canvasElement in canvasElements:
			if element.has_key(canvasElement):
				try:
					self.canvas.delete(element[canvasElement])
				except :pass
		
		self.disselectElement()
		self.propertiesManagment.clearProperties()
		
		if element['id'] in self.elements:
			self.elements.pop(element['id'])
		
		self.propertiesManagment.updateElementList()
		
	def reColorImage(self, rgb, img):
		pixels = img.load() # create the pixel map
		for i in range(img.size[0]): # for every pixel:
			for j in range(img.size[1]):
				pixels[i,j] = (rgb[0], rgb[1], rgb[2], pixels[i,j][3])
		
	def fixSnap(self, x, y=None):
		snap = self.settings['snapping']
		
		difX, difY = x%snap, 0
		if y != None: difY = y%snap
		if (difX > snap/2): difX = - (snap-difX)
		if (y!=None and difY > snap/2): difY = - (snap-difY)
		
		x -= difX
		if (y!=None): y -= difY

		if y != None:
			return (x,y)
		return x
		
	def keypress(self, event):
		self.keyPressed[event.keycode] = 1
		
		if event.keycode == 17:
			self.settings['isSnapping'] = True
		
	def keyrelease(self, event):
		if event.keycode in self.keyPressed:
			self.keyPressed.pop(event.keycode)
		
		if event.keycode == 17:
			self.settings['isSnapping'] = False
		
	def RGBtoHex(self, rgb):
		return '#%02x%02x%02x' % rgb
		
	def getRGBA(self, _str):
		rgba = ( int(float(_str.split(' ')[0] )*255), int(float(_str.split(' ')[1] )*255), int(float(_str.split(' ')[2] )*255), int(float(_str.split(' ')[3] )*255) )

		if rgba[0] > 255 or rgba[1] > 255 or rgba[2] > 255:
			raise RuntimeError
		
		return rgba
		
	def calculateOriginPoint(self, element):
		element['originPoint'] = [0,0]
		if element['rect'][4] == 2 or element['rect'][4] == 7:
			element['originPoint'][0] = 640/2
		elif element['rect'][4] == 3:
			element['originPoint'][0] = 640
		else:
			element['originPoint'][0] = 0
			
		if element['rect'][5] == 2 or element['rect'][5] == 7:
			element['originPoint'][1] = 480/2
		elif element['rect'][5] == 3:
			element['originPoint'][1] = 480
		else:
			element['originPoint'][1] = 0
		
	def getOrder(self):
		self.settings['orderNum'] += 1
		return self.settings['orderNum']

		
	