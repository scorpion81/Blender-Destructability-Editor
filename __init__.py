bl_info = {
	"name": "Destructability Editor",
	"author": "scorpion81",
	"version": (0, 1),
	"blender": (2, 6, 0),
	"api": 41226,
	"location": "Object > Destructability",
	"description": "Define how game engine shall handle destruction of objects",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Object"}


if "bpy" in locals():
	import imp
#   imp.reload(destruction_data)
	imp.reload(destruction_gui)
else:
#   from . import destruction_data
    from . import destruction_gui

import bpy
#import destruction_data
#import destruction_gui

def register():
   # bpy.utils.register_module(destruction_data)
	bpy.utils.register_module(__name__)
   # destruction_gui.register()
	

def unregister():
#   destruction_gui.unregister()
#   destruction_gui.uninitialize()
	bpy.utils.unregister_module(__name__)
#   bpy.utils.register_module(destruction_data)
	 
if __name__ == "__main__":
	print("IN INITPY MAIN")
#	destruction_gui.initialize()
	register()
#   destruction_gui.initialize()
	