from bpy import types, props, utils, ops, data, path
from bpy.types import Object, Scene
from . import destruction_data as dd
import bpy
import os
import random
from bpy_extras import mesh_utils
from operator import indexOf
from mathutils import Vector
#import imp
import math

#currentDir = path.abspath(os.path.split(__file__)[0])
#filepath = currentDir + "\\..\\object_fracture"
#file, path, desc = imp.find_module("fracture_ops", [filepath])
#fo = None
#try:
#   fo = imp.load_module("fo", file, path, desc)
#finally:
#    file.close()
#

#since a modification of fracture_ops is necessary, redistribute it
from . import fracture_ops as fo
imported = True
try: 
    from bpy.app.handlers import persistent
except ImportError:
    imported = False


#do the actual non-bge processing here

class Processor():
                  
    def processDestruction(self, context):
       # self.context = context
      
        modes = {DestructionContext.destModes[0][0]: "self.applyFracture(context, parts, roughness, crack_type)",
                 DestructionContext.destModes[1][0]: "self.applyExplo(context, parts, granularity, thickness)",
                 DestructionContext.destModes[2][0]: "self.applyKnife(context, parts, jitter, granularity, thickness)" } 
        #make an object backup if necessary (if undo doesnt handle this)
        #according to mode call correct method
        mode = context.object.destruction.destructionMode
        parts = context.object.destruction.partCount
        granularity = context.object.destruction.pieceGranularity
        thickness = context.object.destruction.wallThickness
        destroyable = context.object.destruction.destroyable
        roughness = context.object.destruction.roughness
        crack_type = context.object.destruction.crack_type
        groundConnectivity = context.object.destruction.groundConnectivity
        cubify = context.object.destruction.cubify
        jitter = context.object.destruction.jitter
        
        #context.scene.objects.active = context.object
        if (parts > 1) and destroyable or \
           (parts == 1) and groundConnectivity and cubify and mode == 'DESTROY_F': 
            print(mode, modes[mode])
            eval(modes[mode])
        
        return None
    
    def createBackup(self, context):
        
        ops.object.duplicate()
        backup = context.active_object
        backup.name = context.object.name
        context.scene.objects.unlink(backup)
        print("Backup created: ", backup)
        
        return backup
        
    def previewExplo(self, context, parts, granularity, thickness):
        #create modifiers if not there 
      #  if context.active_object.destruction.previewDone: 
      #      return
        
        print("previewExplo", parts, granularity, thickness)
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
        
        
    def applyExplo(self, context, parts, granularity, thickness):
        #create objects from explo by applying it(or by loose parts)
        #check modifier sequence before applying it 
        #(if all are there; for now no other modifiers allowed in between)
        print("applyExplo", parts, granularity, thickness)
        
 #       if context.object.destruction.applyDone:
 #           return
        
        
       # context.object.destruction.applyDone = True
       # context.object.destruction.previewDone = False
        
        #prepare parenting
        parentName, nameStart, largest, bbox = self.prepareParenting(context)
        backup = self.createBackup(context)
            
        #explosion modifier specific    
        self.previewExplo(context, parts, granularity, thickness)
        explode = context.object.modifiers[len(context.active_object.modifiers)-2]
        solidify = context.object.modifiers[len(context.active_object.modifiers)-1]
        
        #if object shall stay together
        settings = context.object.particle_systems[0].settings  
        settings.physics_type = 'NO'
        settings.normal_factor = 0.0
        
        context.scene.frame_current = 2
       
        ops.object.modifier_apply(modifier = explode.name)
     #   ops.object.modifier_apply(modifier = solidify.name)
        
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
                    
        
        #do the parenting
        self.doParenting(context, parentName, nameStart, bbox, backup, largest) 
       
             
    
    def doParenting(self, context, parentName, nameStart, bbox, backup, largest):
        print("Largest: ", largest)    
        
        parent = context.active_object.parent    
        ops.object.add(type = 'EMPTY') 
        context.active_object.game.physics_type = 'RIGID_BODY'            
        context.active_object.game.radius = 0.01  
        context.active_object.game.use_ghost = True        
        context.active_object.name = parentName   
        
        #clear parent and keep transform
      #  ctx = context.copy()
    #    ctx["object"] = context.active_object
    #    parent = context.object.parent
        print("PARENT: ", parent)
    #    ops.object.parent_clear(ctx, type = 'CLEAR_KEEP_TRANSFORM')
        context.active_object.parent = parent
        context.active_object.destruction.gridBBox = bbox
  
        dd.DataStore.backups[context.active_object.name] = backup
        
        parent = context.active_object
        parent.destruction.pos = context.object.destruction.pos
        parent.destruction.destroyable = True
        parent.destruction.partCount = context.object.destruction.partCount
        parent.destruction.wallThickness = context.object.destruction.wallThickness
        parent.destruction.pieceGranularity = context.object.destruction.pieceGranularity
        parent.destruction.destructionMode = context.object.destruction.destructionMode
        parent.destruction.roughness = context.object.destruction.roughness
        parent.destruction.crack_type = context.object.destruction.crack_type
        
     #   parent.destruction.grounds = context.object.destruction.grounds
        parent.destruction.gridDim = context.object.destruction.gridDim
     #   parent.destruction.destructorTargets = context.object.destruction.destructorTargets
        parent.destruction.isGround = context.object.destruction.isGround
        parent.destruction.destructor = context.object.destruction.destructor
        parent.destruction.cubify = context.object.destruction.cubify
        
        
        
        context.scene.objects.active = context.object
        [self.applyDataSet(context, c, largest, parentName) for c in context.scene.objects if 
         self.isRelated(context, c, nameStart)]   
         
      #  ops.object.origin_set(type = 'ORIGIN_GEOMETRY') 
        
        return parent
        
    def prepareParenting(self, context):
        
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
         
        return parentName, nameStart, largest, bbox    
        
        
    
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
        if parentName.split(".")[1] == c.name.split(".")[1]:
            return True
        return False
   
        
    def applyFracture(self, context, parts, roughness, crack_type):
        
        parentName, nameStart, largest, bbox = self.prepareParenting(context)
        backup = self.createBackup(context) 
        
        #fracture the sub objects if cubify is selected
       
        if context.object.destruction.cubify and context.object.destruction.groundConnectivity:
            self.cubify(context, bbox, parts, crack_type, roughness)
        else:
            fo.fracture_basic(context, [context.object], parts, crack_type, roughness)
        
        parent = self.doParenting(context, parentName, nameStart, bbox, backup, largest)
        
        for c in parent.children:
            c.destruction.groundConnectivity = False
            c.destruction.cubify = False
            c.destruction.gridDim = (1,1,1)
                         
        return None
    
    def edgeCount(self, vertex, mesh):
        occurrence = 0
        for key in mesh.edge_keys:
            if vertex == mesh.vertices[key[0]] or vertex == mesh.vertices[key[1]]:
                occurrence += 1
        print("Vertex has ", occurrence, " edges ")        
        return occurrence
        
       
    def applyKnife(self, context, parts, jitter, granularity, thickness):
        
        #create an empty as parent
        parentName, nameStart, largest, bbox = self.prepareParenting(context)
        backup = self.createBackup(context) 
        currentParts = [context.object.name]
        
        context.scene.objects.active = context.object
        ops.object.mode_set(mode = 'EDIT')
        #subdivide the object once, say 10 cuts (let the user choose this)
        ops.mesh.subdivide(number_cuts = granularity)
        ops.object.mode_set(mode = 'OBJECT')
        
        area = None
        region = None
        for a in context.screen.areas:
            if a.type == 'VIEW_3D':
                area = a
                reg = [r for r in area.regions if r.type == 'WINDOW']          
                region = reg[0]
        
        #for 1 ... parts
        while (len(currentParts) < parts):
            
             #pick a random part
            oldnames = [o.name for o in context.scene.objects]
            index = random.randint(0, len(currentParts) - 1)
            print(index, currentParts[index])
            tocut = context.scene.objects[currentParts[index]]
            
          
            parent = tocut.parent
            if parent != None:
                context.scene.objects.active = parent
                ops.transform.rotate(value = [math.radians(45.0)], axis = (0.0, 0.0, 1.0)) 
            
            context.scene.objects.active = tocut
            #make a random OperatorMousePath Collection to define cut path, the higher the jitter
            #the more deviation from path
            #opmousepath is in screen coordinates, assume 0.0 -> 1.0 since 0.5 centers it ?
            #[{"name":"", "loc":(x,y), "time":0},{...}, ...]
            
            width = region.width
            height = region.height
            startx = 0;
            starty = 0
            endx = width
            endy = height
            
#            rnd = random.randint(0,1)
#            if rnd == 1:
#                startx = random.randint(0, width)
#                starty = 0
#                endx = random.randint(0, width)
#                endy = height
#            
#            else:
#                startx = 0
#                starty = random.randint(0, height)
#                endx = width
#                endy = random.randint(0, height)
            
            path = []
            path.append(self.entry(startx,starty))
            path.append(self.entry(endx, endy))
            
            #apply the cut, exact cut
            ops.object.mode_set(mode = 'EDIT')
            ops.mesh.select_all(action = 'SELECT')
            
            ctx = context.copy()
            ctx["area"] = area
            ctx["region"] = region
            ops.mesh.knife_cut(ctx, type = 'EXACT', path = path)
           
            #select loop-to-region to get a half (the smaller one ?)
            ops.mesh.loop_to_region()
       
            #separate object by selection
            ops.mesh.separate(type = 'SELECTED')
            part = self.findNew(context, oldnames)
            currentParts.append(part)
            
            ops.mesh.select_all(action = 'SELECT')
            ops.mesh.region_to_loop()
            ops.mesh.fill()
            ops.object.mode_set(mode = 'OBJECT')
           # ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
            
            context.scene.objects.active = context.scene.objects[part]
            ops.object.mode_set(mode = 'EDIT')
            ops.mesh.select_all(action = 'SELECT')
            ops.mesh.region_to_loop()
            ops.mesh.fill()
            ops.object.mode_set(mode = 'OBJECT')
        #    ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
            
            #context.object seems to disappear so store parent in active object
            context.active_object.parent = parent
            
                    
        parent = self.doParenting(context, parentName, nameStart, bbox, backup, largest)
        
        for c in parent.children:
            c.destruction.groundConnectivity = False
            c.destruction.cubify = False
            c.destruction.gridDim = (1,1,1)
            context.scene.objects.active = c
        #    ops.object.origin_set(type = 'ORIGIN_GEOMETRY')    
            
         
        
        #parent object to empty
    def entry(self, x, y):
        return {"name":"", "loc":(x, y), "time":0}
    
    def findNew(self, context, oldnames):
        for o in context.scene.objects:
            if o.name not in oldnames:
                print("new object: ", o.name)
                return o.name
            
    
    def isRelated(self, context, c, nameStart):
        return (c.name.startswith(nameStart)) # and not self.isChild(context,c)) or self.isChild(context, c)    
        
    def isChild(self, context, child):
        return context.active_object.destruction.transmitMode == 'T_CHILDREN' and \
              child.parent == context.active_object
              
    def endStr(self, nr):
        if nr < 10:
            return "00" + str(nr)
        if nr < 100:
            return "0" + str(nr)
        return str(nr)
        
    def cubify(self, context, bbox, parts, crack_type, roughness):
        #create a cube with dim of cell size, (rotate/position it accordingly)
        #intersect with pos of cells[0], go through all cells, set cube to pos, intersect again
        #repeat always with original object
        
        grid = dd.Grid(context.object.destruction.gridDim, 
                       context.object.destruction.pos,
                       bbox, 
                       [], 
                       context.object.destruction.grounds)
            
        ops.mesh.primitive_cube_add()
        cutter = context.active_object
        cutter.name = "Cutter"
        cutter.select = False
     
        cubes = []
        for cell in grid.cells.values():
            ob = self.cubifyCell(cell,cutter, context)
            cubes.append(ob)
        
        if parts > 1: 
            fo.fracture_basic(context, cubes, parts, crack_type, roughness)
              
        context.scene.objects.unlink(context.object) 
        context.scene.objects.unlink(cutter) 
                  
      
    def cubifyCell(self, cell, cutter, context):
        context.object.select = True #maybe link it before...
        context.scene.objects.active = context.object
        
        ops.object.duplicate()
        context.object.select = False
        ob = context.active_object
        print(ob, context.selected_objects)
        
       # print(cell, cell.center)
        cutter.location = Vector(cell.center)
        cutter.dimensions = Vector(cell.dim) * 1.01
        context.scene.update()
        
        bool = ob.modifiers.new("Boolean", 'BOOLEAN')
        bool.object = cutter
        bool.operation = 'INTERSECT'
        
       # copy = context.copy()
       # copy["object"] = ob
       # ops.object.modifier_apply(copy)
        mesh = ob.to_mesh(context.scene, 
                          apply_modifiers=True, 
                          settings='PREVIEW')
        print(mesh)                  
        old_mesh = ob.data
        ob.data = None
        old_mesh.user_clear()
        
        if (old_mesh.users == 0):
            bpy.data.meshes.remove(old_mesh)  
            
        ob.data = mesh 
        ob.select = False
        ob.modifiers.remove(bool)
        
        ob.select = True
        ops.object.origin_set(type = 'ORIGIN_GEOMETRY') 
        ob.select = False
        
        context.scene.objects.active = context.object 
        
        return ob
                        
                    
def updateGrid(self, context):
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
    updateValidGrounds(context.object)       
    return None


def updateGroundConnectivity(self, context):
    return None

def updateDestructor(self, context):
    return None


def updateTransmitMode(self, context):
    return None 

def updateTransmitMode(self, context):
    return None 

def updateDestroyable(self, context):
    updateValidTargets(context.object)
    return None 

#disable decorator when persistence is not available
def unchanged(func):
    return func

pers = unchanged
if imported:
    pers = persistent

@pers
def updateValidTargets(object):
    #print("Current Object is: ", object)
    for index in range(0, len(bpy.context.scene.validTargets)):
        bpy.context.scene.validTargets.remove(index)
    
    for o in bpy.context.scene.objects:
        if o.destruction.destroyable and o != object:
           prop = bpy.context.scene.validTargets.add()
           prop.name = o.name
    return None 

@pers
def updateValidGrounds(object):
    #print("Current Object is: ", object)
    for index in range(0, len(bpy.context.scene.validGrounds)):
        bpy.context.scene.validGrounds.remove(index)
    
    for o in bpy.context.scene.objects:
        if o.destruction.isGround and o != object:
           prop = bpy.context.scene.validGrounds.add()
           prop.name = o.name
           
    return None

class DestructionContext(types.PropertyGroup):
    
    destModes = [('DESTROY_F', 'Boolean Fracture', 'Destroy this object using boolean fracturing', 0 ), 
             ('DESTROY_E', 'Explosion Modifier', 'Destroy this object using the explosion modifier', 1),
             ('DESTROY_K', 'Knife Tool', 'Destroy this object using the knife tool', 2)] 
    
    transModes = [('T_SELF', 'This Object Only', 'Apply settings to this object only', 0), 
             ('T_CHILDREN', 'Direct Children', 'Apply settings to direct children as well', 1),
             ('T_ALL_CHILDREN', 'All Descendants', 'Apply settings to all descendants as well', 2),
             ('T_SELECTED', 'Selected Objects', 'Apply settings to all selected as well', 3),
             ('T_LAYERS', 'Active Layers', 'Apply settings to all objects on active layers as well', 4), 
             ('T_ALL', 'All Objects', 'Apply settings to all objects as well', 5) ]
    
    destroyable = props.BoolProperty(name = "destroyable",
                         description = "This object can be destroyed, according to parent relations", 
                         update = updateDestroyable)
    
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
    
   
    pos = props.FloatVectorProperty(name = "pos" , default = (0, 0, 0))
 #   currentKnifePath = props.CollectionProperty(type = types.OperatorMousePath, name = "currentKnifePath")
    
    # From pildanovak, fracture script
    crack_type = props.EnumProperty(name='Crack type',
        items=(
            ('FLAT', 'Flat', 'a'),
            ('FLAT_ROUGH', 'Flat rough', 'a'),
            ('SPHERE', 'Spherical', 'a'),
            ('SPHERE_ROUGH', 'Spherical rough', 'a')),
        description='Look of the fracture surface',
        default='FLAT')

    roughness = props.FloatProperty(name="Roughness",
        description="Roughness of the fracture surface",
        min=0.0,
        max=3.0,
        default=0.5)
   # End from        

    grid = None
    jitter = props.FloatProperty(name = "jitter", default = 0.0, min = 0.0, max = 2.0) 
    
    cubify = props.BoolProperty(name = "cubify")
    subgridDim = props.IntVectorProperty(name = "subgridDim", default = (1, 1, 1), min = 1, max = 100, 
                                          subtype ='XYZ')
    cascadeGround = props.BoolProperty(name = "cascadeGround")
    
def initialize():
    Object.destruction = props.PointerProperty(type = DestructionContext, name = "DestructionContext")
    Scene.player = props.BoolProperty(name = "player")
    Scene.converted = props.BoolProperty(name = "converted")
    Scene.validTargets = props.CollectionProperty(name = "validTargets", type = types.PropertyGroup)
    Scene.validGrounds = props.CollectionProperty(name = "validGrounds", type = types.PropertyGroup)
    dd.DataStore.proc = Processor()  
  
    if hasattr(bpy.app.handlers, "object_activation" ) != 0:
        bpy.app.handlers.object_activation.append(updateValidTargets)
        bpy.app.handlers.object_activation.append(updateValidGrounds)
  
def uninitialize():
    del Object.destruction
    
    if hasattr(bpy.app.handlers, "object_activation" ) != 0:
        bpy.app.handlers.object_activation.remove(updateValidTargets)
        bpy.app.handlers.object_activation.remove(updateValidGrounds)
    