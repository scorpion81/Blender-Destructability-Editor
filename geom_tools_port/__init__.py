bl_info = {
    "name": "GeomTools for Blender 2.6x",
    "author": "Guillaume 'GuieA_7' Englert, scorpion81",
    "version": (0, 1),
    "blender": (2, 6, 0),
    "api": 41226,
    "location": "Object -> GeomTools",
    "description": "Port of Blender GeomTools to 2.6x",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"}


if not __name__ in "__main__":
    if "bpy" in locals():
       import imp
       imp.reload(geom_tool)
    else:
        from . import geom_tool

import bpy

def register():
    bpy.utils.register_module(__name__)
    

def unregister():
    bpy.utils.unregister_module(__name__)
     
    