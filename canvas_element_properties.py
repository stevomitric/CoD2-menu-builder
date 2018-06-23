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

class Properties:
	def __init__(self, Manage):
	
		self.manage= Manage
		self.GUI = Manage.GUI
		self.images = self.GUI.guiImages
		
		
	
	def clearProperties(self):
		_list = self.GUI.f3.winfo_children()
	
		for widget in _list:
			widget.destroy()
			
	
	def entryCallbackNonElementProperty(self, property, element):
		element['properties'][property][0] = element['properties'][property][2].var.get()
		self.manage.updateOnPropertyNonElement(element)
	
	def entryCallback(self, property, elementID):
		element = self.manage.elements[elementID]
		
		element['properties'][property][0] = element['properties'][property][2].var.get()
	
		self.manage.updateOnProperty()
	
	def setBadPropertyOption(self, elementID, property):
		self.manage.elements[elementID]['properties'][property][3].configure(background = 'red')
	
	def setGoodPropertyOption(self, elementID, property):
		defaultColour = self.GUI.root.cget('bg')
		self.manage.elements[elementID]['properties'][property][3].configure(background = defaultColour)
	
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
	
		row = 0
		for property in element['properties']:
			value = element['properties'][property][0]
			flags = element['properties'][property][1].split('|')
	
			element['properties'][property][3] = Label(self.GUI.f3, text = property+': ')
			element['properties'][property][3].grid(row = row, column = 0, sticky=W)
	
			widget = None
	
			if 'E' in flags:
				var = StringVar()
				var.set(value)
			
				widget = Entry(self.GUI.f3, textvariable=var)
				widget.grid(row=row,column=1,sticky=W,pady=3)
				
				widget.var = var
				
				if elementID != None: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, elementID = elementID: self.entryCallback(property, elementID) )
				else: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, element = element: self.entryCallbackNonElementProperty(property, element) )
				
			elif 'OM' in flags:
				values = self.getValues(flags)
				
				var = StringVar()
				
				widget = OptionMenu(self.GUI.f3, var, value,  *values)
				widget.grid(row=row,column=1,sticky=W,pady=3)
				
				widget.var = var
				
				if elementID != None: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, elementID = elementID: self.entryCallback(property, elementID) )
				else: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, element = element: self.entryCallbackNonElementProperty(property, element) )
				
			elif 'CB' in flags:
				values = self.getValues(flags)
			
				var = StringVar()
				var.set(value)
			
				widget = Combobox(self.GUI.f3, textvariable = var)
				widget['values'] = values
				widget.grid(row=row,column=1,sticky=W,pady=3)
	
				widget.var = var
	
				if elementID != None: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, elementID = elementID: self.entryCallback(property, elementID) )
				else: widget.var.trace('w', lambda a=0,b=0,c=0,d=0,e=0,f=0, self=self, property = property, element = element: self.entryCallbackNonElementProperty(property, element) )
	
			elif 'L' in flags:
				widget = Label(self.GUI.f3, text = value)
				widget.grid(row=row,column=1,sticky=W,pady=3)
	
			element['properties'][property][2] = widget
	
			row += 1
			
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
			text = element['text']
		
			self.GUI.lb1.insert(END, '('+str(id)+') ' + type + ": " + text)
		
		
		
		
		