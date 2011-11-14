from bpy import types, props, utils, ops, data
from bpy.types import Object, Scene
from . import destruction_data as dd
#import destruction_data as dd
import bpy

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
      #  if context.active_object.destruction.previewDone: 
      #      return
        
        print("previewExplo", parts, granularity, thickness)
        
        ops.object.duplicate()
        backup = context.active_object
        backup.name = context.object.name
        context.scene.objects.unlink(backup)
        print("Backup created: ", backup)
        
        context.scene.objects.active = context.object
        
        #granularity -> subdivision of object in editmode, + particle size enabled (set manually)
        if granularity > 0:
            ops.object.mode_set(mode = 'EDIT')
            ops.mesh.subdivide(number_cuts = granularity)
            ops.object.mode_set()
        
        ops.object.particle_system_add()
        ops.object.modifier_add(type = 'EXPLODE')
        ops.object.modifier_add(type = 'SOLIDIFY')
        
        explode = context.object.modifiers[len(context.active_object.modifiers)-2]
        solidify = context.object.modifiers[len(context.active_object.modifiers)-1]
        
        #get modifier stackindex later, for now use a given order.
        settings = context.object.particle_systems[0].settings        
        settings.count = parts
        settings.frame_start = 2
        settings.frame_end = 2
        settings.distribution = 'RAND'
        
        explode = context.object.modifiers[len(context.active_object.modifiers)-2]
        explode.use_edge_cut = True
       
        solidify.thickness = thickness
        
   #     context.active_object.destruction.previewDone = True
   #     context.active_object.destruction.applyDone = False
        return backup
        
        
        
    def applyExplo(self, context, parts, granularity, thickness):
        #create objects from explo by applying it(or by loose parts)
        #check modifier sequence before applying it 
        #(if all are there; for now no other modifiers allowed in between)
        print("applyExplo", parts, granularity, thickness)
        
 #       if context.object.destruction.applyDone:
 #           return
        
        backup = self.previewExplo(context, parts, granularity, thickness)
        context.object.destruction.applyDone = True
        context.object.destruction.previewDone = False
        
        context.object.destruction.pos = context.object.location.to_tuple()
        bbox = context.object.bound_box.data.dimensions.to_tuple()
        
        context.scene.objects.active = context.object
        
        split = context.object.name.split(".")
        parentName = ""
        nameStart = ""
        nameEnd = ""
        
        if len(split) == 2:
            nameStart = split[0]
            nameEnd = split[1]
        else:
            nameStart = context.object.name
            context.object.name = nameStart + ".000"
            nameEnd = "000"
            
        parentName = "P0_" + nameStart + "." + nameEnd
   
        #and parent them all to an empty created before -> this is the key
        #P_name = Parent of
        
    #    print(name, context.object.name)
        children = context.scene.objects
        largest = nameEnd
        print(context.object.parent)
        if context.object.parent != None:
            pLevel = context.object.parent.name.split("_")[0]
            level = int(pLevel.lstrip("P"))
            level += 1
            #get child with lowest number, must search for it if its not child[0]
            parentName = "P" + str(level) + "_" + context.object.name
       #     children = context.active_object.parent.children
            print("Subparenting...", children)
            length = len(context.object.parent.children)
            
            #get the largest child index number, hopefully it is the last one and hopefully
            #this scheme will not change in future releases !
            largest = context.object.parent.children[length - 1].name.split(".")[1]
          #  nr = int(largest) + 1
          #  largest = self.endStr(nr)
            
            
        
        #context.scene.objects.active = context.object
       # destruction = context.object.destruction
        explode = context.object.modifiers[len(context.active_object.modifiers)-2]
        solidify = context.object.modifiers[len(context.active_object.modifiers)-1]
        
        #if object shall stay together
        settings = context.object.particle_systems[0].settings  
        settings.physics_type = 'NO'
        settings.normal_factor = 0.0
        
        context.scene.frame_current = 2
       
        ops.object.modifier_apply(modifier = explode.name)
        ops.object.modifier_apply(modifier = solidify.name)
        
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
        
        
        
#        children = data.objects
#        largest = nameEnd
#        print(context.object.parent)
#        if context.object.parent != None:
#            pLevel = context.object.parent.name.split("_")[0]
#            level = int(pLevel.lstrip("P"))
#            level += 1
#            #get child with lowest number, must search for it if its not child[0]
#            parentName = "P" + str(level) + "_" + context.object.parent.children[0].name
#       #     children = context.active_object.parent.children
#            print("Subparenting...", children)
#            length = len(context.object.parent.children)
#            
#            #get the largest child index number, hopefully it is the last one and hopefully
#            #this scheme will not change in future releases !
#            largest = context.active_object.parent.children[length - 1].name.split(".")[1]
#          #  nr = int(largest) + 1
#          #  largest = self.endStr(nr)
#            
        
        print("Largest: ", largest)    
            
        ops.object.add(type = 'EMPTY') 
        context.active_object.game.physics_type = 'RIGID_BODY'            
        context.active_object.game.radius = 0.01  
        context.active_object.game.use_ghost = True        
        context.active_object.name = parentName   
        context.active_object.parent = context.object.parent
        context.active_object.destruction.gridBBox = bbox
      #  context.active_object.destruction["backup"] = backup
      #  print("Backup stored: ", context.active_object.destruction["backup"])
        dd.DataStore.backups[context.active_object.name] = backup
        
      #  childs = []
      #  for c in context.object.children:
      #      childs.append(c)
      #      c.parent = None
            
      #  context.active_object.location = context.object.location
        context.active_object.destruction.pos = context.object.destruction.pos
        
        context.active_object.destruction.destroyable = True
       # copyDataSet(context.object, context.active_object)
        
        context.scene.objects.active = context.object
        [self.applyDataSet(context, c, largest, parentName) for c in children if 
         self.isRelated(context, c, nameStart)]   
         
        ops.object.origin_set(type = 'ORIGIN_GEOMETRY') 
        
     
        
     #   context.scene.active_objects = dd.DataStore.backupChild
        
      #  print(context.active_object.name, context.active_object.children)
             
    
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

    def applyDataSet(self, context, c, nameEnd, parentName):
        split = c.name.split(".")
        end = split[1]
        
        if (int(end) > int(nameEnd)) or self.isBeingSplit(c, parentName):
            print(int(end) > int(nameEnd), self.isBeingSplit(c, parentName))
            self.assign(c, parentName)  
        
    def assign(self, c, parentName):
         
        c.parent = data.objects[parentName]
        c.game.physics_type = 'RIGID_BODY'
        c.game.collision_bounds_type = 'CONVEX_HULL'
        c.game.collision_margin = 0.00 
        c.game.radius = 0.01
        c.game.use_collision_bounds = True 
        c.select = True   
        
        c.destruction.transmitMode = 'T_SELF'
        c.destruction.destroyable = False
        c.destruction.partCount = 1
        c.destruction.wallThickness = 0.01
        c.destruction.pieceGranularity = 0
        c.destruction.destructionMode = 'DESTROY_F'
    
    def isBeingSplit(self, c, parentName):
        #if context.object.parent == None:
        #    return True
        #parent and child have the same index number->this child was being split
        if parentName.split(".")[1] == c.name.split(".")[1]:
            #context.scene.objects.unlink(data.objects[child.name])
            return True
        return False
    
  #  def copyDataSet(oldObj, newObj):
  #      newObj.destruction.partCount = oldObj.destruction.partCount
  #      newObj.destruction.wallThickness = oldObj.destruction.wallThickness
  #      newObj.destruction.pieceGranularity = oldObj.destruction.pieceGranularity
  #      newObj.destruction.groundConnectivity = oldObj.groundConnectivity...
        
       
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
    
    def isRelated(self, context, c, nameStart):
        return (c.name.startswith(nameStart) and not self.isChild(context,c)) or self.isChild(context, c)    
        
    def isChild(self, context, child):
        return context.active_object.destruction.transmitMode == 'T_CHILDREN' and \
              child.parent == context.active_object
              
    def endStr(self, nr):
        if nr < 10:
            return "00" + str(nr)
        if nr < 100:
            return "0" + str(nr)
        return str(nr)
    

def updateGrid(self, context):
#    obj = context.object
#    dim = obj.bound_box.data.dimensions.to_tuple()
#    grid = dd.Grid(self.gridDim, obj.location.to_tuple(), dim, obj.children)
#    grid.buildNeighborhood()
#    dd.DataStore.grids[obj.name] = grid
    #context.object.grid = grid
    #print(obj.name, context.object.grid)
    return None

def updateDestructionMode(self, context):
   # dd.DataStore.proc.processDestruction(context)
    #p = Processor()
    #p.processDestruction(context)
    return None

def updatePartCount(self, context):
   # print(bpy.context, context)
   # print(bpy.context.active_object, context.active_object)
   # print(bpy.context.object, context.object)
    #p = Processor()
    #p.processDestruction(context)
#    dd.DataStore.proc.processDestruction(context)
    return None

def updateWallThickness(self, context):
#    dd.DataStore.proc.processDestruction(context)
    return None

def updatePieceGranularity(self, context):
  #  dd.DataStore.proc.processDestruction(context)
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
    #re apply to children -> process
#    dd.DataStore.proc.processDestruction(context)
    return None 

def updateValidTargets(self, context):
    
    while len(context.object.destruction.validTargets) > 0:
        del context.object.destruction.validTargets[0]
        
    for o in data.objects:
        if o.type == 'MESH' and o.name != context.object.name: 
        # and o not in grounds
            context.object.destruction.validTargets.add()
            context.object.destruction.validTargets.name = o.name
   
    return None

def updateValidGrounds(self, context):
    
    while len(context.object.destruction.validGrounds) > 0:
        del context.object.destruction.validGrounds[0]
        
    for o in data.objects:
        if o.type == 'MESH' and o.name != context.object.name: 
        # and o not in grounds
            context.object.destruction.validGrounds.add()
            context.object.destruction.validGrounds.name = o.name
            
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
    gridDim = props.IntVectorProperty(name = "grid", default = (1, 1, 1), min = 1, max = 100, 
                                          subtype ='XYZ', update = updateGrid )
    gridBBox = props.FloatVectorProperty(name = "gridbbox", default = (0, 0, 0))
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
    
    validTargets = props.CollectionProperty(name = "validTargets", type = types.PropertyGroup)
    validGrounds = props.CollectionProperty(name = "validGrounds", type = types.PropertyGroup)
    pos = props.FloatVectorProperty(name = "pos" , default = (0, 0, 0))
 #   grid = None
    
def initialize():
#    print("HELLOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
#    utils.register_class(DestructionContext)
    Object.destruction = props.PointerProperty(type = DestructionContext, name = "DestructionContext")
    Scene.player = props.BoolProperty(name = "player")
    Scene.converted = props.BoolProperty(name = "converted")
  #  Scene.backup = props.PointerProperty(name = "backup", type = Object)
    dd.DataStore.proc = Processor()  
  #  updateValidTargets(None, bpy.context)
  #  updateValidGrounds(None, bpy.context)
    
def uninitialize():
    del Object.destruction
    utils.unregister_class(DestructionContext)
    
def setObject(context, object):
    copy = context.copy()
    copy["object"] = object
    return copy
    