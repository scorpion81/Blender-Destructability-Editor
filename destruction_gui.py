from bpy import types, props, utils
from bpy.types import Object
from . import destruction_data as dd
#from destruction_data import DataStore, Grid


class DestructabilityPanel(types.Panel):
	bl_idname = "OBJECT_PT_destructability"
	bl_label = "Destructability"
	bl_context = "object"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	
	def register():
		initialize()	
  
	def draw_header(self, context):
	  #   self.layout.prop(context.object, "useDestructability", text = "")
		pass
	
	def draw(self, context):
		layout = self.layout
	  #  layout.active = context.object.useDestructability
		
		row = layout.row()
		row.label(text = "Apply this settings to:")
		row.prop(context.object.destruction, "transmitMode",  text = "")
		layout.separator()
		
		row = layout.row()
		row.prop(context.object.destruction, "destroyable", text = "Destroyable")
		row.prop(context.object.destruction, "partCount", text = "Parts")
		
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


def updateGrid(self, context):
	obj = context.object
	dim = obj.bound_box.data.dimensions.to_tuple()
	dd.DataStore.grid = dd.Grid(self.grid, obj.location.to_tuple(), dim, obj.children)
	print(dd.DataStore.grid)
	return None


## define a nested property
class DestructionContext(types.PropertyGroup):
	
	destModes = [('DESTROY_F', 'Apply Fracture Addon', 'Destroy this object using the fracture addon', 0 ), 
			 ('DESTROY_E', 'Apply Explosion Modifier', 'Destroy this object using the explosion modifier', 1),
			 ('DESTROY_P', 'Preview Explosion Modifier', 'Preview destruction with explosion modifier', 2)] 
	
	transModes = [('T_SELF', 'This Object Only', 'Apply settings to this object only', 0), 
			 ('T_CHILDREN', 'Direct Children', 'Apply settings to direct children as well', 1),
			 ('T_ALL_CHILDREN', 'All Descendants', 'Apply settings to all descendants as well', 2),
			 ('T_SELECTED', 'Selected Objects', 'Apply settings to all selected as well', 3),
			 ('T_LAYERS', 'Active Layers', 'Apply settings to all objects on active layers as well', 4), 
			 ('T_ALL', 'All Objects', 'Apply settings to all objects as well', 5) ]
	
   # nested = props.FloatProperty(name="Nested", default=0.0)
	destroyable = props.BoolProperty(name = "destroyable",
						 description = "This object can be destroyed, according to parent relations")
	
	partCount = props.IntProperty(name = "partCount", default = 1, min = 1, max = 10000)
	destructionMode = props.EnumProperty(items = destModes)
	destructor = props.BoolProperty(name = "destructor", 
						description = "This object can trigger destruction")
	isGround = props.BoolProperty(name = "isGround", 
	 description = "This object serves as a hard point, objects not connected to it will be destroyed")
	 
	groundConnectivity = props.BoolProperty(name = "groundConnectivity", 
	description = "Determines whether connectivity of parts of this object is calculated, so only unconnected parts collapse according to their parent relations")
	grid = props.IntVectorProperty(name = "grid", default = (1, 1, 1), min = 1, max = 100, 
										  subtype ='XYZ', update = updateGrid )
	destructorTargets = props.CollectionProperty(type = types.PropertyGroup, name = "destructorTargets")
	grounds = props.CollectionProperty(type = types.PropertyGroup, name = "grounds")
	transmitMode = props.EnumProperty(items = transModes, name = "Transmit Mode")
	active_target = props.IntProperty(name = "active_target", default = 0)
	active_ground = props.IntProperty(name = "active_ground", default = 0)
	groundSelector = props.StringProperty(name = "groundSelector")
	targetSelector = props.StringProperty(name = "targetSelector")
	
   
def initialize():
	print("HELLOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
	utils.register_class(DestructionContext)
	Object.destruction = props.PointerProperty(type = DestructionContext, name = "DestructionContext")  
		
#def uninitialize():
#   utils.unregister_class(DestructionContext)   

def register():  
	#utils.register_class(DestructionContext)
	initialize()
	utils.register_class(AddGroundOperator)
	utils.register_class(RemoveGroundOperator)
	utils.register_class(AddTargetOperator)
	utils.register_class(RemoveTargetOperator)
	utils.register_class(DestructabilityPanel)  
  
def unregister():
	utils.unregister_class(DestructabilityPanel)
	utils.unregister_class(AddGroundOperator)
	utils.unregister_class(RemoveGroundOperator)
	utils.unregister_class(AddTargetOperator)
	utils.unregister_class(RemoveTargetOperator)
	utils.unregister_class(DestructionContext)
	 
if __name__ == "__main__":
	register()  