'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''


class Manage:
	def __init__(self, canvas, images):
		self.elements = {}
		
		self.canvas = canvas
		self.images = images
		
		self.settings = {
			'defaultPos': [640/2, 480/2],
		
		}
		
		self.selectedElement = -1
		
	def createLabelElement(self):
		element = {
			'text': 'Example Text',
			'colour': 'black',
			'pos': self.settings['defaultPos'][:],
			'rect': [124,48],
			'size': 12,
			
			'offsetMoveX': 0,
			'offsetMoveY': 0,
		}
		
		
		
		
		element['bbox'] = self.canvas.create_rectangle(0, 0, 0, 0, outline="Rosy Brown1", width=2, state = 'hidden')
		element['move'] = self.canvas.create_image(0, 0, image=self.images['move'], state = 'hidden')
		element['moveF'] = self.canvas.create_image(0, 0, image=self.images['moveF'], state = 'hidden')
		
		elementID = self.canvas.create_text(0,0, fill=element['colour'], font="default "+str(element['size']), text= element['text'], anchor = 'nw')
		element['id'] = elementID
		
		self.elements[elementID] = element
		
		self.selectElement(elementID)
		
	def calculateCords(self, element):
		self.canvas.coords(element['bbox'], element['pos'][0],  element['pos'][1],  element['pos'][0]+ element['rect'][0],  element['pos'][1]+ element['rect'][1] )
		self.canvas.coords(element['id'], element['pos'][0],  element['pos'][1] )
		self.canvas.coords(element['move'], element['pos'][0]+element['rect'][0]/2,  element['pos'][1]+ element['rect'][1]/2)
		self.canvas.coords(element['moveF'], element['pos'][0]+element['rect'][0]/2,  element['pos'][1]+ element['rect'][1]/2)
		
		
	def buttonPress(self, event):
		
		if not self.selectedElement in self.elements:
			return	
		
		self.elements[self.selectedElement]['offsetMoveX'] = event.x - self.elements[self.selectedElement]['pos'][0]
		self.elements[self.selectedElement]['offsetMoveY'] = event.y - self.elements[self.selectedElement]['pos'][1]
		
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'normal' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], outline="dark red" )
	
	def selectElement(self, elementID):
		if self.selectedElement in self.elements:
			pass
	
		self.selectedElement = elementID
		
		self.canvas.itemconfigure(self.elements[elementID]['bbox'], state = 'normal' )
		self.canvas.itemconfigure(self.elements[elementID]['move'], state = 'normal' )
		
		self.calculateCords(self.elements[elementID])
	
	
	def buttonRelease(self, event):
		if not self.selectedElement in self.elements:
			return
			
		self.canvas.itemconfigure(self.elements[self.selectedElement]['moveF'], state = 'hidden' )
		self.canvas.itemconfigure(self.elements[self.selectedElement]['bbox'], outline="Rosy Brown1" )
		
	def buttonMotion(self, event):
		if not self.selectedElement in self.elements:
			return	
	
		self.elements[self.selectedElement]['pos'][0] = event.x - self.elements[self.selectedElement]['offsetMoveX']
		self.elements[self.selectedElement]['pos'][1] = event.y - self.elements[self.selectedElement]['offsetMoveY']
		
		self.calculateCords(self.elements[self.selectedElement])
		
		
		
		
		
		
		
		
		
		
		
		