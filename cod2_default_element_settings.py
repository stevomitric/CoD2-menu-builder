'''       __ ___________            
  _______/  |\_   _____/__  ______  
 /  ___/\   __\    __)_\  \/ /  _ \ 
 \___ \  |  | |        \\   (  <_> )
/____  > |__|/_______  / \_/ \____/ 
     \/              \/             

stevo.mitric@yahoo.com

This code has no licence, feel free to do whatever you want with it.
'''

labelSettings = {
	'name': 		['label', 'E|S', None],
	'visible':		['MENU_TRUE', 'OM|bool', None],
	'rect':			['0 0 128 24', 'E', None],
	'origin':		['0 0', 'E', None],
	'forecolor':	['1 1 1', 'CB|globalColours', None],
	'type':			['ITEM_TYPE_TEXT', 'L', None],
	'text':			['Example Text', 'E|S', None],
	'textfont':		['UI_FONT_NORMAL', 'CB|F|font', None],
	'textscale':	['GLOBAL_TEXT_SIZE', 'CB|size', None],
}



globalDefinitions = {
	'type': {
		'ITEM_TYPE_TEXT':				'0',
		'ITEM_TYPE_BUTTON':				'1',
		'ITEM_TYPE_RADIOBUTTON':		'2',
		'ITEM_TYPE_CHECKBOX':			'3',
		'ITEM_TYPE_EDITFIELD': 			'4',
		'ITEM_TYPE_COMBO': 				'5',
		'ITEM_TYPE_LISTBOX':			'6',
		'ITEM_TYPE_MODEL': 				'7',
		'ITEM_TYPE_OWNERDRAW': 			'8',
		'ITEM_TYPE_NUMERICFIELD':		'9',
		'ITEM_TYPE_SLIDER':				'10',
		'ITEM_TYPE_YESNO': 				'11',
		'ITEM_TYPE_MULTI': 				'12',
		'ITEM_TYPE_DVARENUM': 			'13',
		'ITEM_TYPE_BIND':				'14',
		'ITEM_TYPE_MENUMODEL': 			'15',
		'ITEM_TYPE_VALIDFILEFIELD':		'16',
		'ITEM_TYPE_DECIMALFIELD':		'17',
		'ITEM_TYPE_UPREDITFIELD':		'18',
	
	},
	
	'align': {
		'ITEM_ALIGN_LEFT':				'0',
		'ITEM_ALIGN_CENTER':			'1',
		'ITEM_ALIGN_RIGHT':				'2',
		'ITEM_ALIGN_CENTER2':			'3',
	},
	
	'windowborder': {
		'WINDOW_BORDER_NONE':			'0',
		'WINDOW_BORDER_FULL':			'1',
		'WINDOW_BORDER_HORZ':			'2',
		'WINDOW_BORDER_VERT':			'3',
	},
	
	'windowstyle': {
		'WINDOW_STYLE_EMPTY':			'0',
		'WINDOW_STYLE_FILLED':			'1',
		'WINDOW_STYLE_GRADIENT':		'2',
		'WINDOW_STYLE_SHADER':			'3',
	},
	
	'font': {
		'UI_FONT_NORMAL':				'1',
		'UI_FONT_BOLD':					'4',
	
	},

	'bool': {
		'MENU_TRUE':					'1',
		'MENU_FALSE':					'0',
	},
	
	'globalColours': {
		'GLOBAL_FOCUSED_COLOR':			'.98 .827 .58 1',
		'GLOBAL_UNFOCUSED_COLOR':		'1 1 1 1',
		'GLOBAL_DISABLED_COLOR':		'.35 .35 .35 1',
		'UI_FOCUS_COLOR':				'.96 .66 .04 1',
	},
	
	
	'size': {
		'GLOBAL_TEXT_SIZE':				'.35',
		'GLOBAL_HEADER_SIZE':			'.50',
	},
}





