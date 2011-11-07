from bpy import types, props, utils, ops, data
from bpy.types import Object
from . import destruction_data as dd

#do the actual non-bge processing here

class Processor():
                  
    def processDestruction(self, context):
       # self.context = context
      
        modes = {DestructionContext.destModes[0][0]: "self.applyFracture(parts)",
                 DestructionContext.destModes[1][0]: "self.applyExplo(context, parts, granularity, thickness)"}
               #  DestructionContext.destModes[2][0]: "self.previewExplo(context, parts, granularity, thickness)" } 
        #make an object backup if necessary (if undo doesnt handle this)
        #according to mode call correct method
        mode = context.object.destruction.destructionMode
        parts = context.object.destruction.partCount
        granularity = context.object.destruction.pieceGranularity
        thickness = context.object.destruction.wallThickness
        destroyable = context.object.destruction.destroyable
        
        if (parts > 1) and destroyable:
            print(mode, modes[mode])
            eval(modes[mode])
        
        return None
    
    
    def previewExplo(self, context, parts, granularity, thickness):
        #create modifiers if not there
        
        if context.object.destruction.previewDone: 
            return
        
        print("previewExplo", parts, granularity, thickness)
        
        #granularity -> subdivision of object in editmode, + particle size enabled (set manually)
        if granularity > 0:
            ops.object.mode_set(mode = 'EDIT')
            ops.mesh.subdivide(number_cuts = granularity)
            ops.object.mode_set()
        
        ops.object.particle_system_add()
        ops.object.modifier_add(type = 'EXPLODE')
        ops.object.modifier_add(type = 'SOLIDIFY')
        
        #get modifier stackindex later, for now use a given order.
        settings = context.object.particle_systems[0].settings        
        settings.count = parts
        settings.frame_start = 2
        settings.frame_end = 2
        settings.distribution = 'RAND'
       
        
        explo = context.object.modifiers[1]
        explo.use_edge_cut = True
        
        solid = context.object.modifiers[2]
        solid.thickness = thickness
        
        context.object.destruction.previewDone = True
        context.object.destruction.applyDone = False
        
        
        
    def applyExplo(self, context, parts, granularity, thickness):
        #create objects from explo by applying it(or by loose parts)
        #check modifier sequence before applying it 
        #(if all are there; for now no other modifiers allowed in between)
        print("applyExplo", parts, granularity, thickness)
        
 #       if context.object.destruction.applyDone:
 #           return
        
        self.previewExplo(context, parts, granularity, thickness)
        context.object.destruction.applyDone = True
        context.object.destruction.previewDone = False
        
        pos = context.object.location.to_tuple()
        name = context.object.name
        parentName = "P_" + name
        
       # ops.object.add(type = 'EMPTY')
   #     context.object.select = True
        #context.scene.objects.active = data.objects["Empty"]
        #ops.object.parent_set(type = 'OBJECT')
        
        #context.scene.objects.active = context.object
        destruction = context.object.destruction
        solid = context.object.modifiers[2]  
        explo = context.object.modifiers[1]
        
        #if object shall stay together
        settings = context.object.particle_systems[0].settings  
        settings.physics_type = 'NO'
        settings.normal_factor = 0.0
        
        context.scene.frame_current = 2
       
        ops.object.modifier_apply(modifier = explo.name)
        ops.object.modifier_apply(modifier = solid.name)
        
        #must select particle system before somehow
        ops.object.particle_system_remove() 
        ops.object.mode_set(mode = 'EDIT')
        ops.mesh.select_all(action = 'DESELECT')
        #omit loose vertices, otherwise they form an own object!
        ops.mesh.select_by_number_vertices(type='OTHER')
        ops.mesh.delete(type = 'VERT')
        ops.mesh.select_all(action = 'SELECT')
        ops.mesh.separate(type = 'LOOSE')
        ops.object.mode_set()
        print("separated")
        
        #and parent them all to an empty created before -> this is the key
        #P_name = Parent of
        
        ops.object.add(type = 'EMPTY') 
        context.active_object.name = parentName
        print(name, context.object.name)
        
        [self.applyDataSet(c) for c in data.objects if c.name.startswith(name)]   
        ops.object.parent_set(type = 'OBJECT')
        
        print(context.active_object.name, context.active_object.children)
             
    
    def applyFracture(self,parts):
        #make fracture gui available as sublayout in panel
        #simply call the operator and parent the context
        #children with same Name and different number
        #when applying hierarchical fracturing, append hierarchy level number to part number
        #_1, _2 and so on
      #  print("applyFracture", parts)  
      #  data.objects["Cube"].select = True
      #  ops.object.duplicate()
        
        #data.objects["Cube"].select = True
        #data.objects["Cube.001"].select = True
      #  ops.object.modifier_add(type = 'EXPLODE')
       # ops.object.modifier_apply()
        #ops.object.editmode_toggle()
        #ops.object.editmode_toggle()
        
       # ops.object.add()
       # data.objects["Cube"].select = True
       # data.objects["Cube.001"].select = True
       # ops.object.parent_set()
       return None
    
    def valid(self,context, child):
        return child.name.startswith(context.object.name) #and \
#               len(child.data.vertices) > 1)

    def applyDataSet(self, c):
        c.destruction.destroyable = False
        c.destruction.parts = 1
        c.destruction.granularity = 0
        c.destruction.thickness = 0.01
        c.select = True
        
    def applyKnife(self, context, parts, jitter, thickness):
        pass
        
        #create an empty as parent
        
        #for 1 ... parts
        
        #make a random OperatorMousePath Collection to define cut path, the higher the jitter
        #the more deviation from path
        
        #pick a random part
        
        #apply the cut, exact cut
        
        #select loop-to-region to get a half (the smaller one ?)
        
        #separate object
        
        #parent object to empty
    

def updateGrid(self, context):
    obj = context.object
    dim = obj.bound_box.data.dimensions.to_tuple()
    dd.DataStore.grid = dd.Grid(self.grid, obj.location.to_tuple(), dim, obj.children)
    dd.DataStore.grid.buildNeighborhood()
    print(dd.DataStore.grid)
    return None

def updateDestructionMode(self, context):
   # dd.DataStore.proc.processDestruction(context)
    p = Processor()
    p.processDestruction(context)
    return None

def updatePartCount(self, context):
    dd.DataStore.proc.processDestruction(context)
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
             ('DESTROY_E', 'Apply Explosion Modifier', 'Destroy this object using the explosion modifier', 1)]
            # ('DESTROY_P', 'Preview Explosion Modifier', 'Preview destruction with explosion modifier', 2)] 
    
    transModes = [('T_SELF', 'This Object Only', 'Apply settings to this object only', 0), 
             ('T_CHILDREN', 'Direct Children', 'Apply settings to direct children as well', 1),
             ('T_ALL_CHILDREN', 'All Descendants', 'Apply settings to all descendants as well', 2),
             ('T_SELECTED', 'Selected Objects', 'Apply settings to all selected as well', 3),
             ('T_LAYERS', 'Active Layers', 'Apply settings to all objects on active layers as well', 4), 
             ('T_ALL', 'All Objects', 'Apply settings to all objects as well', 5) ]
    
   # nested = props.FloatProperty(name="Nested", default=0.0)
    destroyable = props.BoolProperty(name = "destroyable",
                         description = "This object can be destroyed, according to parent relations")
    
    partCount = props.IntProperty(name = "partCount", default = 10, min = 1, max = 999, update = updatePartCount)
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

    wallThickness = props.FloatProperty(name = "wallThickness", default = 0.01, min = 0.01, max = 10,
                                      update = updateWallThickness)
    pieceGranularity = props.IntProperty(name = "pieceGranularity", default = 3, min = 0, max = 100, 
                                         update = updatePieceGranularity)
    applyDone = props.BoolProperty(name = "applyDone", default = False)
    previewDone = props.BoolProperty(name = "previewDone", default = False)
    
def initialize():
#   print("HELLOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
#   utils.register_class(DestructionContext)
    Object.destruction = props.PointerProperty(type = DestructionContext, name = "DestructionContext")
    dd.DataStore.proc = Processor()  
    
def uninitialize():
    del Object.destruction
    utils.unregister_class(DestructionContext)