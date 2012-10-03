bl_info = {
    "name": "Destructability Editor",
    "author": "scorpion81, plasmasolutions(Tester)",
    "version": (1, 1),
    "blender": (2, 6, 4),
    "api": 51026,
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

import bpy

from bpy.types import Context
StructRNA = bpy.types.Struct.__bases__[0]

def copy(self):
    from types import BuiltinMethodType
    new_context = {}
    generic_attrs = (list(StructRNA.__dict__.keys()) +
                     ["bl_rna", "rna_type", "copy"])
    for attr in dir(self):
        if not (attr.startswith("_") or attr in generic_attrs):
            if hasattr(self, attr):
                value = getattr(self, attr)
                if type(value) != BuiltinMethodType:
                    new_context[attr] = value

    return new_context

#a hacky solution
Context.copy = copy    
    
def register():
    bpy.utils.register_module(__name__)
    

def unregister():
    bpy.utils.unregister_module(__name__)
     
if __name__ == "__main__":
    print("IN INITPY MAIN")
    from object_destruction import destruction_gui
    #destruction_gui.register()
    