from bpy import types, props, utils
from bpy.types import Object
from . import destruction_proc as dp


class DestructabilityPanel(types.Panel):
    bl_idname = "OBJECT_PT_destructability"
    bl_label = "Destructability"
    bl_context = "object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    
    def register():
        dp.initialize()

    def unregister():
        del Object.destruction
        utils.unregister_class(dp.DestructionContext)   
    
    def draw(self, context):
        layout = self.layout
      #  layout.active = context.object.useDestructability
        
        row = layout.row()
        row.label(text = "Apply this settings to:")
        row.prop(context.object.destruction, "transmitMode",  text = "")
        layout.separator()
        
        row = layout.row()
        row.prop(context.object.destruction, "destroyable", text = "Destroyable")

        col = row.column()
        col.prop(context.object.destruction, "partCount", text = "Parts")
        col.prop(context.object.destruction, "wallThickness", text = "Thickness")
        col.prop(context.object.destruction, "pieceGranularity", text = "Granularity")

        
        layout.prop(context.object.destruction, "destructionMode", text = "Destruction Mode")
        layout.separator()
       
        layout.prop(context.object.destruction, "isGround", text = "Is Connectivity Ground")
        layout.prop(context.object.destruction, "groundConnectivity", text = "Calculate Ground Connectivity")
        layout.label(text = "Connected Grounds")
        
        row = layout.row()
        row.template_list(context.object.destruction, "grounds", 
                          context.object.destruction, "active_ground", rows = 2)
        row.operator("ground.remove", icon = 'ZOOMOUT', text = "")
        
        row = layout.row()
        row.label(text = "Select Ground:")
        row.prop(context.object.destruction, "groundSelector", text = "")
        row.operator("ground.add", icon = 'ZOOMIN', text = "")
        
        row = layout.row()
        col = row.column()
        col.prop(context.object.destruction, "grid", text = "Connectivity Grid")
        layout.separator()
         
        layout.prop(context.object.destruction, "destructor", text = "Destructor")
       
        layout.label(text = "Destructor Targets")
        row = layout.row()
        row.template_list(context.object.destruction, "destructorTargets", 
                          context.object.destruction, "active_target" , rows = 2) 
        row.operator("target.remove", icon = 'ZOOMOUT', text = "")   
        
        row = layout.row()
        row.label(text = "Select Destroyable: ")
        row.prop(context.object.destruction, "targetSelector", text = "")
        row.operator("target.add", icon = 'ZOOMIN', text = "")
        
class AddGroundOperator(types.Operator):
    bl_idname = "ground.add"
    bl_label = "add ground"
    
    def execute(self, context):
        return {'FINISHED'}   
    
class RemoveGroundOperator(types.Operator):
    bl_idname = "ground.remove"
    bl_label = "remove ground"
    
    def execute(self, context):
        return {'FINISHED'}
       
        
class AddTargetOperator(types.Operator):
    bl_idname = "target.add"
    bl_label = "add target"
    
    def execute(self, context):
        return {'FINISHED'}   
    
class RemoveTargetOperator(types.Operator):
    bl_idname = "target.remove"
    bl_label = "remove target"
    
    def execute(self, context):
        return {'FINISHED'} 
