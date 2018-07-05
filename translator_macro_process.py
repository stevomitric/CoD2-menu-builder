'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''

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
	value = [data[inx1][inx2+1:]]
	
	if '(' in key:
		_def['type'] = 'function'
		
		function = ' '.join(data[inx1][inx2:]).replace('\\', '')
		key = key.split('(')[0]
		
		arguments = function.split('(')[1].split(')')[0].split(', ')
		
		
		inx1 += 1
		value = [data[inx1][:]]
		while value[-1][-1] == '\\' and inx1 < len(data):
			inx1 += 1
			value[-1].pop( len(value[-1])-1 )
			value.append( data[inx1] )
		
		_def['arguments'] = arguments
		_def['function'] = function
	
	else:
		_def['type'] = 'standard'
	
		while value[-1][-1] == '\\' and inx1 < len(data):
			inx1 += 1
			value[-1].pop( len(value[-1])-1 )
			value.append( data[inx1] )

	
	_def['key'] = key
	_def['value'] = value
	_def['endINX'] = inx1
	return _def

def checkLineInDefs(data, inx, defs):
	for i in range(len(data[inx])):
		item = data[inx][i]

		for _def in defs:
			pass
			if item.startswith(_def['key']):
				print 'FOUND DEF'
			
	return data
	
def processData(data):
	defs = []
	
	for i in range(len(data)):
		item = data[i]
	
		#data = checkLineInDefs(data, i, defs)
	
		if item[0] == '#define':
			defs.append(loadDef(data, i, 1))
	
	
	deleteLines = {}
	for _def in defs:
		for i in range(_def['startINX'], _def['endINX']+1):
			deleteLines[i] = True
	newData = []
	for i in range(len(data)):
		if not deleteLines.has_key(i):
			newData.append(data[i]);
	data = newData
	
	print data
	
	return data

