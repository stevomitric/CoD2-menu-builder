# Call of duty 2 Menu builder

Simple GUI tool that allows you to create .menu files with it. Language used to make it: Python 2.7.15.



# Installation (windows)

Download compiled version CoD2_menu_builder_win64.rar, extract it (all of it) and run "CoD2 Menu Builder.exe". 

You can also run it with python 2.7.x. You would need to install latest version of PIL module. with command: pip install pillow


# Ussage

There are 5 frames:
 - Add element: allows you to add different elements such as: label (text), button, rectangle, image, text field, slider, multi
   - Label: Labels are simple text widgets that have decorative purpose.
   - Button: Buttons (as said in cod2 menu defs) are "Text with border", but they allow us to call some events when they are pressed, on focus, entered ... 
   - Eectangle: They are, well, rectangles that can be colourd and basically act as decoration.
   - Image: Rescalable image for decoration
   - Text field: When selected they will monitor for user input (keyboard) and save it to a client dvar. We can call them "GUI entry" (google it)
   - Slider: Movable dot that corresponds to range of values [1-100].
   - Multi Field: List of options that switch when clicked. Option list is given as a client dvar and result is also stored as a client dvar.
 - Tools: Menu properties, Delete Menu, Add menu
 - Menus: Gives you a graphical representation of how will your menu look in game
 - Properties: Everything you can change about one element (or menu)
 - Elements: Gives you a list of menus elements. You can select one by pressing on it (useful if your element is completely covered by another)
 
 
You can only import menus that are made by this tool (some others work but its not recommende).
