'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''

import copy

def loadDef(data, inx1, inx2):
	_def = {
		'type': '',
		'key': '',
		'value': '',
	
		'startINX': inx1,
		'endINX': inx1,
		
		'arguments': [],
	}

	key = data[inx1][inx2]
	value = []
	
	if '(' in key:
		_def['type'] = 'function'
		
		function = ' '.join(data[inx1][inx2:]).replace('\\', '')
		key = key.split('(')[0]
		
		arguments = function.split('(')[1].split(')')[0].split(', ')
		
		
		inx1 += 1
		value = [data[inx1][:]]
		while  ( value[-1][-1] == '\\'  or ( len(value[-1][-1]) and value[-1][-1][-1] == '\\' ) ) and inx1 < len(data):
			inx1 += 1
			
			if value[-1][-1] == '\\': 
				value[-1].pop( len(value[-1])-1 )
			else:
				value[-1][-1] = value[-1][-1][:-1]
				
			value.append( data[inx1] )
		
		_def['arguments'] = arguments
		_def['function'] = function
	
	else:
		_def['type'] = 'standard'
		
		value = []
		for item in data[inx1][inx2+1:]:
			value.append(item)
		
		while (value[-1] == '\\' or ( len(value[-1]) and value[-1][-1] == '\\' ) ) and inx1 < len(data):
			inx1 += 1
			
			if value[-1] == '\\':
				value.pop( len(value)-1 )
			else:
				value[-1] = value[-1][:-1]
			
			for item in data[inx1]:
				value.append( item )
	
	_def['key'] = key
	_def['value'] = value
	_def['endINX'] = inx1
	return _def

def checkStandardDefs(line, defs):
	for _def in defs:
		if _def['type'] != 'standard':
			continue
	
		inx = 0
	
		while inx < len(line):
			item = line[inx]
	
			add = ['', ',', ')', '(']
	
			for _ in add:
				if item == _def['key']+_:
					line.pop(inx)
					
					for i in range(len(_def['value'])):
						line.insert(inx+i, _def['value'][i] )
					
					line[inx+len(_def['value'])-1] += _
					
					break
				
			inx += 1
	
	return line
	
def checkFunctionDefs(data, inx, defs):
	if data[inx][0] == '#ifndef':
		return data
	
	for _def in defs:
		if _def['type'] != 'function':
			continue
	
		line = data[inx]
		
		for i in range(len(line)):
			item = line[i]
			
			if item.startswith(_def['key']):
				function = ' '.join(line[i:]).replace('\\', '')
				
				arguments = function.split('(')[1].split(')')[0].split(', ')
				print arguments
				insertData = copy.deepcopy(_def['value'])
				for a1 in range(len(insertData)):
					for a2 in range(len( insertData[a1] )):
						for a3 in range(len(_def['arguments'])):
							if insertData[a1][a2] == _def['arguments'][a3]:
								insertData[a1][a2] = arguments[a3]
				
				data.pop(inx)
				
				for i2 in range(len(insertData)):
					data.insert(inx+i2, insertData[i2] )

				return data
			
	return data
	
def processData(data):
	defs = []
	for i in range(len(data)):
		item = data[i]
	
		data[i] = checkStandardDefs(item, defs)
	
		if item[0] == '#define':
			defs.append(loadDef(data, i, 1))
	
	
	# delete defs from file
	deleteLines = {}
	for _def in defs:
		for i in range(_def['startINX'], _def['endINX']+1):
			deleteLines[i] = True
	newData = []
	for i in range(len(data)):
		if not deleteLines.has_key(i):
			newData.append(data[i]);
	data = newData
	
	
	# check for standard defs
	for i in range(len(data)):
		item = data[i]
		
		data[i] = checkStandardDefs(item, defs)
	
	# check for function defs
	inx = 0
	while inx < len(data):
		item = data[inx]
		
		data = checkFunctionDefs(data, inx, defs)
		
		inx += 1
		
	#print data
	#for i in defs:
	#	print i['key'], i['value']
	return data

