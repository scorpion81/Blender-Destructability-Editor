bl_info = {
    "name": "BlendGit",
    "author": "scorpion81",
    "version": (1, 1),
    "blender": (2, 7, 9),
    "location": "Toolshelf",
    "description": "Keep track of revisions of blend files in git from blender",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"}

if not __name__ in "__main__":
    if "bpy" in locals():
       import imp
       imp.reload(frontend_git)
    else:
        from . import frontend_git 

import bpy

def register():
    bpy.utils.register_module(__name__)
    

def unregister():
    bpy.utils.unregister_module(__name__)
     
    
