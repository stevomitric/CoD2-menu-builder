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
		segments = getSegments(line)
		if segments:
			newData.append(segments)

	return newData
	
def importMenuFile(GUI, filePath = 'C:/users/stevo/desktop/test.menu' ):
	file = open(filePath, 'rb')
	data = file.read().replace('\r', '')
	file.close()
	
	data = processData(data)
	print data
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	