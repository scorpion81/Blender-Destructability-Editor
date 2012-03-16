bl_info = {
    "name": "Destructability Editor",
    "author": "scorpion81",
    "version": (1, 0),
    "blender": (2, 6, 2),
    "api": 44682,
    "location": "Object > Destructability",
    "description": "Define how game engine shall handle destruction of objects",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/Destructability",
    "tracker_url": "",
    "category": "Object"}


if not __name__ in "__main__":
    if "bpy" in locals():
       import imp
       imp.reload(destruction_gui)
    else:
        from . import destruction_gui

import bpy

def register():
    bpy.utils.register_module(__name__)
    

def unregister():
    bpy.utils.unregister_module(__name__)
     
if __name__ == "__main__":
    print("IN INITPY MAIN")
    import destruction_gui
    destruction_gui.register()
    
