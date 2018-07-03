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
				
		if 'BW' in flags:
			value = '{ ' + value + ' }'
				
		toWrite += indent+property+ _calculateTabs(property)  +value+'\n'
	
	return toWrite
	
def exportAsMenu(Menus, saveto = 'C:/users/stevo/desktop/test.menu'):
	# Variable init
	toWrite = ''
	
	# Includes
	toWrite += '#include "ui_mp/menudef.h"\n'
	toWrite += '\n'
	
	# Local definitions
	#toWrite += cod2_default_element_settings.getCusotmDefs()
	
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
	
# -------------------------------------------------------------------------------------------------------------
	
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
	
def processInclude(data):
	
	for i in range(len(data)):
		item = data[i][0]
	
		if item == '#include':
			path = data[i][1].replace('"','')
			print path
			data.pop(i)
			
			path = 'Data/cod2_menus/' + path
			file = open(path, 'rb')
			filedata = file.read().replace('\r', '')
			while '/*' in filedata: filedata = filedata.split('/*', 1)[0] + filedata.split('/*', 1)[1].split('*/', 1)[1]
			filedata = processData(filedata)
			
			file.close()
			
			for segment in filedata[::-1]:
				data.insert(i, segment)
				
			break
			
	return data
	
def loadItemDef(GUI, data, inx):
	bracketNum = 0
	bracketValue = ''
	lastItem = ''
	
	elementID = GUI.elementManager.createItemElement()
	element = GUI.elementManager.elements[elementID]
	
	element['properties']['text'][2].var.set('')
	
	for i in range(inx, len(data)):
		item = data[i][0]
		value = ' '.join(data[i][1:]).replace('"', '')
		if value in cod2_default_element_settings.globalDefinitions['custom']:
			value = cod2_default_element_settings.globalDefinitions['custom'][value]
		
		if item == '{':
			bracketNum += 1
		elif item == '}':
			bracketNum -= 1
			
			if bracketNum == 1 and bracketValue != '':
				if lastItem in element['properties']:
					element['properties'][lastItem][2].var.set(bracketValue)
					element['properties'][lastItem][0] = bracketValue
				bracketValue = ''
				lastItem = item
			
		elif bracketNum == 2:
			bracketValue += item + ' ' + value + ' '

		
		elif item in element['properties'] and bracketNum == 1:
			element['properties'][item][2].var.set(value)
			element['properties'][item][0] = value
			
			lastItem = item
			
		else:
			lastItem = item
			log('Unknown Property: ' + item)
			
		if not bracketNum:
			break
	
	if element['properties'].has_key('rect'):
		while element['properties']['rect'][0].count(' ') < 5:
			element['properties']['rect'][0] += ' 0'
			element['properties']['rect'][2].var.set(element['properties']['rect'][0])
	
	return i
	
def loadMenuDef(GUI, data, inx):
	bracketNum, skip = 0, 0
	bracketValue = ''
	lastItem = ''
	
	menu = GUI.MenuManager.createMenu()
	GUI.nb.select(menu['id'])
	GUI.MenuManager.selectMenu(menu)
	
	for i in range(inx, len(data)):

		if i < skip:
			continue
			
		item = data[i][0]
		value = ' '.join(data[i][1:]).replace('"', '')

		
		if item == '{':
			bracketNum += 1
		elif item == '}':
			bracketNum -= 1
			
			if bracketNum == 1 and bracketValue != '':
				if lastItem in menu['properties']:
					menu['properties'][lastItem][0] = bracketValue
				bracketValue = ''
				lastItem = item
			
		elif bracketNum == 2:
			bracketValue += item + ' ' + value + ' '
			
		elif item in menu['properties'] and bracketNum == 1:
			#log('Menu property: '+ item+ ', value: '+ value)
			menu['properties'][item][0] = value
			lastItem = item
		elif item.lower() == 'itemdef':
			skip = loadItemDef(GUI, data, i+1) +1
		else:
			lastItem = item
			print item
			
		if not bracketNum:
			break
			
	GUI.MenuManager.updateTabName(menu['id'], menu['properties']['name'][0])
	menu['name'] =  menu['properties']['name'][0]
	
def importMenuFile(GUI, filePath = 'C:/users/stevo/desktop/ingame.menu' ):
	file = open(filePath, 'rb')
	data = file.read().replace('\r', '')
	file.close()
	
	while '/*' in data: data = data.split('/*', 1)[0] + data.split('/*', 1)[1].split('*/', 1)[1]
	
	data = processData(data)
	while '#include' in [item for sublist in data for item in sublist]:
		data = processInclude(data)
		
	for i in range(len(data)):
		for i2 in range(len(data[i])):
			item = data[i][i2].lower()
			
			if item == '#define':
				variable = data[i][1]
				value = ' '.join(data[i][2:])
				
				if cod2_default_element_settings.getValueFromKey(variable) == variable:
					cod2_default_element_settings.globalDefinitions['custom'][variable] = value
			
			if item == 'menudef':
				loadMenuDef(GUI, data, i+1)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	