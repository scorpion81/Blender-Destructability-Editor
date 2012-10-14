bl_info = {
    "name": "Destructability Editor",
    "author": "scorpion81, plasmasolutions(Tester)",
    "version": (1, 2),
    "blender": (2, 6, 4),
    "api": 51287,
    "location": "Physics > Destruction",
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
        from object_destruction import destruction_gui as dg

import bpy

from bpy.types import Context
StructRNA = bpy.types.Struct.__bases__[0]
olddraw = None
oldcopy = None

#override some methods here, no need to change the original files this way
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


def physics_add(self, layout, md, name, type, typeicon, toggles):
    sub = layout.row(align=True)
    if md:
        sub.context_pointer_set("modifier", md)
        sub.operator("object.modifier_remove", text=name, icon='X')
        if(toggles):
            sub.prop(md, "show_render", text="")
            sub.prop(md, "show_viewport", text="")
    else:
        sub.operator("object.modifier_add", text=name, icon=typeicon).type = type
        
        
def draw(self, context):
    ob = context.object

    layout = self.layout
    layout.label("Enable physics for:")
    split = layout.split()
    col = split.column()

    if(context.object.field.type == 'NONE'):
        col.operator("object.forcefield_toggle", text="Force Field", icon='FORCE_FORCE')
    else:
        col.operator("object.forcefield_toggle", text="Force Field", icon='X')

    if(ob.type == 'MESH'):
        physics_add(self, col, context.collision, "Collision", 'COLLISION', 'MOD_PHYSICS', False)
        physics_add(self, col, context.cloth, "Cloth", 'CLOTH', 'MOD_CLOTH', True)
        physics_add(self, col, context.dynamic_paint, "Dynamic Paint", 'DYNAMIC_PAINT', 'MOD_DYNAMICPAINT', True)

    col = split.column()

    if(ob.type == 'MESH' or ob.type == 'LATTICE'or ob.type == 'CURVE'):
        physics_add(self, col, context.soft_body, "Soft Body", 'SOFT_BODY', 'MOD_SOFT', True)

    if(ob.type == 'MESH'):
        physics_add(self, col, context.fluid, "Fluid", 'FLUID_SIMULATION', 'MOD_FLUIDSIM', True)
        physics_add(self, col, context.smoke, "Smoke", 'SMOKE', 'MOD_SMOKE', True)  
    
    #destruction    
    if (ob.type == 'MESH'):
        
        if not context.object.destEnabled:
            icon = 'MOD_EXPLODE'
        else:
            icon = 'X'
            
        col.operator("destruction.enable", text="Destruction", icon=icon)

#a hacky solution
#Context.copy = copy    
    
def register():
    bpy.utils.register_module(__name__)
    #unregister some panels again manually
    bpy.types.Object.destEnabled = bpy.props.BoolProperty(name = "destEnabled", default = False)
    
    bpy.utils.unregister_class(dg.DestructionFracturePanel)
    bpy.utils.unregister_class(dg.DestructionPhysicsPanel)
    bpy.utils.unregister_class(dg.DestructionSetupPanel)
    bpy.utils.unregister_class(dg.DestructionHierarchyPanel)
    bpy.utils.unregister_class(dg.DestructionRolePanel)
    
    global olddraw
    global oldcopy
    
    olddraw = bpy.types.PHYSICS_PT_add.draw
    oldcopy = Context.copy
    
    bpy.types.PHYSICS_PT_add.draw = draw
    Context.copy = copy
    
def unregister():
    bpy.utils.unregister_module(__name__)
    
    global olddraw
    global oldcopy
    
    bpy.types.PHYSICS_PT_add.draw = olddraw
    Context.copy = oldcopy
    del bpy.types.Object.destEnabled
     
if __name__ == "__main__":
    print("IN INITPY MAIN")
    from object_destruction import destruction_gui
    #destruction_gui.register()