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

def log(msg, state = 'INFO'):
	print state.upper() + ': ' + msg

def _calculateTabs(value):
	TABMAX = 7

	numOfTabs = ( TABMAX*4 - len(value) ) / 4
	
	if (len(value)%4 !=0): numOfTabs += 1
	
	return '\t'*numOfTabs

def _writeProperties(element, indent):
	toWrite = ''
	
	for property in cod2_default_element_settings.elementOrder:
		if property not in element['properties']:
			continue
	
		value = element['properties'][property][0]
		flags = element['properties'][property][1]
		
		if 'DNIIN' in flags and not value:
			continue
		
		if 'S' in flags:
			value = '"' + value + '"'
				
		toWrite += indent+property+ _calculateTabs(property)  +value+'\n'
	
	return toWrite
	
def exportAsMenu(Menus, saveto = 'C:/users/stevo/desktop/test.menu'):
	# Variable init
	toWrite = ''
	
	# Includes
	toWrite += '#include "ui_mp/menudef.h"\n'
	toWrite += '\n'
	
	# Header part
	toWrite += '\n{\n'
	
	for menu in Menus:
		
		# Menu header
		toWrite += '\tmenuDef\n'
		toWrite += '\t{\n'
		
		# Menu properties 
		toWrite += _writeProperties(menu, '\t'*2)
		
		# Seperate menu and elements
		toWrite += '\n\n'
		
		# Elements
		for elementID in menu['elements']:
			element = menu['elements'][elementID]
	
			# Element header
			toWrite += '\t\titemDef\n'
			toWrite += '\t\t{\n'
	
			# Element properties
			toWrite += _writeProperties(element, '\t'*3)
			
			toWrite += '\t\t}\n'
			toWrite += '\n'
	
		toWrite += '\t}\n\n'
		
		
	toWrite += '}\n'
	
	
	file = open(saveto, 'wb')
	file.write(toWrite)
	file.close()
	
def getSegments(data):
	segments, segment = [], ''
	inside = 0
	
	for i in data:
		if i == '"':
			inside = 1-inside
	
		if i == '\t' or (i == ' ' and not inside):
			if segment != '':
				if '//' in segment:
					segment = ''
					break
					
				segments.append(segment)
			segment = ''	
		else:
			segment += i

			
	if segment != '':
		segments.append(segment)
	
	return segments
				
def processData(data):
	data = data.split('\n')
	
	newData = []
	
	for line in data:
		# Separete in new lines
		segments = getSegments(line)
		if segments:
			newData.append(segments)

		# all in one
		#segments = getSegments(line)
		#for segment in segments:
		#	if segment:
		#		newData.append(segment)
		
		
	return newData
	

def loadItemDef(GUI, data, inx):
	bracketNum = 0
	
	elementID = GUI.elementManager.createItemElement()
	element = GUI.elementManager.elements[elementID]
	
	element['properties']['text'][2].var.set('')
	
	for i in range(inx, len(data)):
		item = data[i][0]
		value = ' '.join(data[i][1:]).replace('"', '')
		
		if item == '{':
			bracketNum += 1
		elif item == '}':
			bracketNum -= 1
		elif item in element['properties'] and bracketNum == 1:
			element['properties'][item][2].var.set(value)
			element['properties'][item][0] = value
			
		if not bracketNum:
			break
	
def loadMenuDef(GUI, data, inx):
	bracketNum = 0
	
	menu = GUI.MenuManager.createMenu()
	GUI.nb.select(menu['id'])
	GUI.MenuManager.selectMenu(menu)
	
	for i in range(inx, len(data)):
		item = data[i][0]
		value = ' '.join(data[i][1:]).replace('"', '')

		
		if item == '{':
			bracketNum += 1
		elif item == '}':
			bracketNum -= 1
		elif item in menu['properties'] and bracketNum == 1:
			log('Menu property: '+ item+ ', value: '+ value)
		elif item.lower() == 'itemdef':
			loadItemDef(GUI, data, i+1)
		
		
		if not bracketNum:
			break
			
def importMenuFile(GUI, filePath = 'C:/users/stevo/desktop/ingame.menu' ):
	file = open(filePath, 'rb')
	data = file.read().replace('\r', '')
	file.close()
	
	data = processData(data)
	
	
	for i in range(len(data)):
		for i2 in range(len(data[i])):
			item = data[i][i2].lower()
			
			if item == '#define':
				variable = data[i][1]
				value = ' '.join(data[i][2:])
			
				cod2_default_element_settings.globalDefinitions['custom'][variable] = value
			
			if item == 'menudef':
				loadMenuDef(GUI, data, i+1)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	