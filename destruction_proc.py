from bpy import types, props, utils
from bpy.types import Object
from . import destruction_data as dd

#do the actual non-bge processing here

class Processor():
    
    modes = { }
    
    def processDestruction(context, mode, parts, granularity, thickness):
        self.context = context
        #make an object backup if necessary (if undo doesnt handle this)
        #according to mode call correct method
        #if (parts > 1):
        
        return None
    
    
    def previewExplo(parts, granularity, thickness):
        #create modifiers if not there
        
        #set data to modifiers
        pass
    
    def applyExplo():
        #create objects from explo by applying it(or by loose parts)
        #check modifier sequence before applying it 
        #(if all are there; for now no other modifiers allowed in between)
        
        #and parent them all to an empty
        pass  
    
    def applyFracture(parts):
        #make fracture gui available as sublayout in panel
        #simply call the operator and parent the context
        #children with same Name and different number
        #when applying hierarchical fracturing, append hierarchy level number to part number
        #_1, _2 and so on
        pass  

def updateGrid(self, context):
	obj = context.object
	dim = obj.bound_box.data.dimensions.to_tuple()
	dd.DataStore.grid = dd.Grid(self.grid, obj.location.to_tuple(), dim, obj.children)
	dd.DataStore.grid.buildNeighborhood()
	print(dd.DataStore.grid)
	return None

def updateDestructionMode(self, context):
	return None

def updatePartCount(self, context):
	return None

def updateWallThickness(self, context):
	return None

def updatePieceGranularity(self, context):
	return None

def updateIsGround(self, context):
	return None


def updateGroundConnectivity(self, context):
	return None

#def updateGrounds(self, context)
#   pass
#template_list -> Operators

def updateDestructor(self, context):
	return None

#def updateTargets(self, context)
#   pass
#template_list -> Operators

def updateTransmitMode(self, context):
	return None    
        

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
	
	partCount = props.IntProperty(name = "partCount", default = 1, min = 1, max = 999, update = updatePartCount)
	destructionMode = props.EnumProperty(items = destModes, update = updateDestructionMode)
	destructor = props.BoolProperty(name = "destructor", 
						description = "This object can trigger destruction", update = updateDestructor)
	isGround = props.BoolProperty(name = "isGround", 
	 description = "This object serves as a hard point, objects not connected to it will be destroyed",
	 update = updateIsGround)
	 
	groundConnectivity = props.BoolProperty(name = "groundConnectivity", 
	description = "Determines whether connectivity of parts of this object is calculated, so only unconnected parts collapse according to their parent relations", update = updateGroundConnectivity)
	grid = props.IntVectorProperty(name = "grid", default = (1, 1, 1), min = 1, max = 100, 
										  subtype ='XYZ', update = updateGrid )
	destructorTargets = props.CollectionProperty(type = types.PropertyGroup, name = "destructorTargets")
	grounds = props.CollectionProperty(type = types.PropertyGroup, name = "grounds")
	transmitMode = props.EnumProperty(items = transModes, name = "Transmit Mode", update = updateTransmitMode)
	active_target = props.IntProperty(name = "active_target", default = 0)
	active_ground = props.IntProperty(name = "active_ground", default = 0)
	groundSelector = props.StringProperty(name = "groundSelector")
	targetSelector = props.StringProperty(name = "targetSelector")

	wallThickness = props.IntProperty(name = "wallThickness", default = 1, min = 1, max = 100,
									  update = updateWallThickness)
	pieceGranularity = props.IntProperty(name = "pieceGranularity", default = 0, min = 0, max = 100, 
										 update = updatePieceGranularity)
	
def initialize():
	#print("HELLOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
#	utils.register_class(DestructionContext)
	Object.destruction = props.PointerProperty(type = DestructionContext, name = "DestructionContext")  
