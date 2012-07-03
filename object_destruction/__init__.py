bl_info = {
    "name": "Destructability Editor",
    "author": "scorpion81",
    "version": (1, 1),
    "blender": (2, 6, 3),
    "api": 48468,
    "location": "Object > Destructability",
    "description": "Define how game engine shall handle destruction of objects",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/Destructability",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=30567&group_id=153&atid=467",
    "category": "Object"}


if not __name__ in "__main__":
    if "bpy" in locals():
       import imp
       imp.reload(destruction_gui)
    else:
        from object_destruction import destruction_gui
        from object_destruction.blendgit import frontend_git 

import bpy

def register():
    bpy.utils.register_module(__name__)
    

def unregister():
    bpy.utils.unregister_module(__name__)
     
if __name__ == "__main__":
    print("IN INITPY MAIN")
    import destruction_gui
    destruction_gui.register()
    