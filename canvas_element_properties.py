'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''

from Tkinter		import *
from ttk			import *

import cod2_default_element_settings

from tkMessageBox	import showinfo

class Properties:
	def __init__(self, Manage):
	
		self.manage= Manage
		self.GUI = Manage.GUI
		self.images = self.GUI.guiImages
		
		
	
	def clearProperties(self):
		frames = [self.GUI.f31, self.GUI.f32, self.GUI.f33, self.GUI.f34]
		
		for frame in frames:
			_list = frame.winfo_children()
		
			for widget in _list:
				widget.destroy()
			
	
	def entryCallbackNonElementProperty(self, property, element):
		element['properties'][property][0] = element['properties'][property][2].var.get()
		self.manage.updateOnPropertyNonElement(element, property)
	
	def entryCallback(self, property, elementID, callProperty = True):
		element = self.manage.elements[elementID]
		
		element['properties'][property][0] = element['properties'][property][2].var.get()

		self.checkValid(element, property)
	
		if callProperty:
			self.manage.updateOnProperty(element = element, property=property)
	
	def checkValid(self, element, property):
		flags = element['properties'][property][1].split('|')
		value = element['properties'][property][0]
		
		if 'CBN' in flags and value == '':
			showinfo('Warning003', 'This property cannot be empty because it causes unpredictable stuff to happen.')
			element['properties'][property][2].var.set('A')
	
	def setBadPropertyOption(self, elementID, property, element = None):
		if element == None: element = self.manage.elements[elementID]
		
		if not element['properties'][property][3].winfo_exists():
			return
		
		element['properties'][property][3].configure(background = 'red')
		if property not in element['badArgument']:
			element['badArgument'].append(property)
	
	def setGoodPropertyOption(self, elementID, property, element = None):
		if element == None: element = self.manage.elements[elementID]
		
		if not element['properties'][property][3].winfo_exists():
			return
		
		defaultColour = self.GUI.root.cget('bg')
		element['properties'][property][3].configure(background = defaultColour)
	
		if property in element['badArgument']:
			element['badArgument'].remove(property)
	
	def updatePorperties(self, elementID = None, nonElementProperty = None):
		self.clearProperties()
		
		if elementID == None and nonElementProperty == None:
			return
		
		if not elementID in self.manage.elements and nonElementProperty == None:
			return
	
		element = ''
		if (elementID != None):
			element = self.manage.elements[elementID]
		else:
			element = nonElementProperty
	
		rows = [0,0,0,0]
		for property in element['properties']:
			
			frame, rowINX = None, -1
			if property in cod2_default_element_settings.elementGroup['basic']:
				frame, rowINX = self.GUI.f31, 0
			elif property in cod2_default_element_settings.elementGroup['text']:
				frame, rowINX = self.GUI.f32, 1
			elif property in cod2_default_element_settings.elementGroup['function']:
				frame, rowINX = self.GUI.f33, 2
			elif property in cod2_default_element_settings.elementGroup['other']:
				frame, rowINX = self.GUI.f34, 3
			else:
				print 'Unknown property: ', property
				continue
				
			value = element['properties'][property][0]
			flags = element['properties'][property][1].split('|')
	
			element['properties'][property][3] = Label(frame, text = property+': ')
			element['properties'][property][3].grid(row = rows[rowINX], column = 0, sticky=W)
	
			widget = None
	
			if 'E' in flags:
				var = StringVar()
				var.set(value)
			
				widget = Entry(frame, textvariable=var)
				widget.grid(row=rows[rowINX],column=1,sticky=W,pady=3)
				
				widget.var = var
				
				if elementID != None: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, elementID = elementID: self.entryCallback(property, elementID) )
				else: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, element = element: self.entryCallbackNonElementProperty(property, element) )
				
			elif 'OM' in flags:
				values = self.getValues(flags)
				
				var = StringVar()
				
				widget = OptionMenu(frame, var, value,  *values)
				widget.grid(row=rows[rowINX],column=1,sticky=W,pady=3)
				
				widget.var = var
				
				if elementID != None: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, elementID = elementID: self.entryCallback(property, elementID) )
				else: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, element = element: self.entryCallbackNonElementProperty(property, element) )
				
			elif 'CB' in flags:
				values = self.getValues(flags)
			
				var = StringVar()
				var.set(value)
			
				widget = Combobox(frame, textvariable = var)
				widget['values'] = values
				widget.grid(row=rows[rowINX],column=1,sticky=W,pady=3)
	
				widget.var = var
	
				if elementID != None: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, elementID = elementID: self.entryCallback(property, elementID) )
				else: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, element = element: self.entryCallbackNonElementProperty(property, element) )
	
			elif 'L' in flags:
				var = StringVar()
				var.set(value)
				
				widget = Label(frame, textvariable = var)
				widget.grid(row=rows[rowINX],column=1,sticky=W,pady=3)
	
				widget.var = var
	
				if elementID != None: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, elementID = elementID: self.entryCallback(property, elementID, True) )
				else: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, element = element: self.entryCallbackNonElementProperty(property, element, True))
	
			element['properties'][property][2] = widget
	
			rows[rowINX] += 1
			
		self.manage.updatePosiotionValue(elementID)
		
	def getValues(self, flags):
		values = []
		for flag in flags:
			if flag in cod2_default_element_settings.globalDefinitions:
				for value in cod2_default_element_settings.globalDefinitions[flag]:
					values.append(value)
		return values
		
		
	def updateElementList(self):
		self.GUI.lb1.delete(0, END)
		for elementID in self.manage.elements:
			element = self.manage.elements[elementID]
			type = element['type']
			id   = element['id']
			if element.has_key('text'):
				text = element['text']
			else: text = ' / '
			if element['properties'].has_key('name'):
				type = element['properties']['name'][0]
		
			self.GUI.lb1.insert(END, '('+str(id)+') ' + type + ": " + text)
		
		
		
		
		