from bge import logic
import destruction_data as dd
import math
from mathutils import Vector, Matrix

#this is the bge part of the destructability editor.
#it actually executes the destruction according to its definition.

#check if object  is destroyable

#if we take care about ground /hardpoint connection of registered grounds
#determine which cells are ground and at each impact check cell neighborhood (availability and integrity)

#then check for ground connection; if none, do collapse, activate all children(according to availability)
#and if desired the whole ascendancy tree.
#this is an additional flag -> how many hierarchy levels each destructor can destroy

#if there is ground connection inactivate all cell children.

#then wait for collision, if it is a registered destroyer, activate children according to speed an mass of destroyer (larger radius) for testing purposes create/register player balls as destroyer automatically. to each destroyable. 

sensorName = "D_destructor" 
massFactor = 4
speedFactor = 2
defaultRadius = 2
#define Parameters for each object ! here defined for testing purposes
hierarchyDepth = 1 # this must be stored per destructor, how deep destruction shall be
#otherwise 1 level each collision with destroyer / ground
#maxDepth = 10  #this must be stored in scene
doReturn = False
integrity = 0.5

def setup():
    
    #doReturn = False
    scene = logic.getCurrentScene()
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():
            parent = o["myParent"]
            if parent.startswith("P0"):
                firstparent = scene.objects[parent]
            o.setParent(parent, False, False)
            print(o.parent)
        o.suspendDynamics() 
    
    #rotate parent HERE by 45 degrees, X Axis (testwise)
   # firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
    #oldOrientation = Matrix(firstparent.worldOrientation)
    
    print("In Setup")
    for o in scene.objects:
        if isGroundConnectivity(o):
            print("ISGROUNDCONN")
            bbox = getFloats(o["gridbbox"])
            dim = getInts(o["griddim"])
            
            grounds = getGrounds(o)
            groundObjs = [logic.getCurrentScene().objects[g.name] for g in grounds]
            [g.setParent(firstparent, False, False) for g in groundObjs]
            oldRot = Matrix(firstparent.worldOrientation)
            firstparent.worldOrientation = Vector((0, 0, 0))
            for g in grounds:
                g.pos = Vector(logic.getCurrentScene().objects[g.name].worldPosition)
                print(g.pos)
                
          #  firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
        #    [g.removeParent() for g in groundObjs]
            
            grid = dd.Grid(dim, o.worldPosition, bbox, o.children, grounds)
            grid.buildNeighborhood()
            grid.findGroundCells() 
            dd.DataStore.grids[o.name] = grid
            
           # firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
            firstparent.worldOrientation = oldRot
            [g.removeParent() for g in groundObjs]
        
    print("Grids: ", dd.DataStore.grids)  
    
    #rotate parent HERE by 45 degrees, X Axis (testwise)
    #firstparent.worldOrientation = Vector((math.radians(45), 0, 0))

def collide():
    
    #colliders have collision sensors attached, which trigger for registered destructibles only
    
    #first the script controller brick, its sensor and owner are needed
    control = logic.getCurrentController()
    scene = logic.getCurrentScene()
    sensor = control.sensors["Collision"]
    owner = sensor.owner
    #treat each hit object, check hierarchy
  #  print(sensor.hitObjectList)
    for obj in sensor.hitObjectList:
   #for obj in scene.objects:
    #    if obj.getDistanceTo(owner) < 2.0:
        dissolve(obj, 1, hierarchyDepth, owner)
                 
#recursively destroy parent relationships    
def dissolve(obj, depth, maxdepth, owner):
  #  print("dissolving level: ", depth)
 #   print("isDestroyable / isRegistered: ", isDestroyable(obj.parent), isRegistered(obj.parent, owner))
    if isDestroyable(obj.parent) and isRegistered(obj.parent, owner):
        
        grid = None
        if obj.parent.name in dd.DataStore.grids.keys():
            grid = dd.DataStore.grids[obj.parent.name]
                 
#        if isGroundConnectivity(obj.parent) and not isGround(obj.parent):
#            if grid != None:
#                cells = [c for c in grid.cells.values()]
#                for c in cells:
#                    destroyNeighborhood(c)
#                     
        if depth < maxdepth: 
            [dissolve(c, depth + 1, maxdepth, owner) for c in obj.parent.children]
            [activate(c, owner, grid) for c in obj.parent.children]
        activate(obj, owner, grid)

def activate(child, owner, grid):
 #   if child.getDistanceTo(owner.worldPosition) < defaultRadius:         
    # print("activated: ", child)
     global integrity
     if isGroundConnectivity(child.parent) and not isGround(child.parent):
         if grid != None:
             cells = dict(grid.cells)
             gridPos = grid.getCellByName(child.name)
             cell = cells[gridPos]
             
             if (child.name in cell.children):
                cell.children.remove(child.name)
            
             if not cell.integrity(integrity):
                print("Low Integrity, destroying cell!")
                destroyCell(cell, cells)
                
                
             for c in cells.values():
                destroyNeighborhood(c)
             
             for c in cells.values():
                c.visit = False
                
     child.removeParent()
     child.restoreDynamics() 

def isGroundConnectivity(obj):
    if "groundConnectivity" not in obj.getPropertyNames():
        return False
    return obj["groundConnectivity"]

def isGround(obj):
    return obj["isGround"]    

def isDestroyable(destroyable):
    if destroyable == None:
        return False
    return destroyable["destroyable"]

def isGround(obj):
    return obj["isGround"]

def isRegistered(destroyable, destructor):
    if destroyable == None:
        return False
    if not destructor["destructor"]:
        return False
    
    targets = destructor["destructorTargets"].split(" ")
    for t in targets:
        if t == destroyable.name:
            return True
        
    return False

def getFloats(str):
    parts = str.split(" ")
    return (float(parts[0]), float(parts[1]), float(parts[2]))

def getInts(str):
    parts = str.split(" ")
    return (int(parts[0]), int(parts[1]), int(parts[2]))

def getGrounds(obj):
    if "grounds" not in obj.getPropertyNames():
        return None
    grounds = []
    print(obj["grounds"])
    parts = obj["grounds"].split(" ")
    for part in parts:
        p = part.split(";")
        if p[0] == "" or p[0] == " ":
            continue
        ground = dd.Ground()
        ground.name = p[0]
       # ground.pos = logic.getCurrentScene().objects[ground.name].worldPosition
        vert = p[1]
        verts = vert.split("_")
        for coords in verts:
            coord = coords.split(",")
#            i = 0
#            for c in coord:
#                print(i, c, float(c))
#                i += 1    
            vertexStart = (float(coord[0]), float(coord[1]), float(coord[2]))
            vertexEnd = (float(coord[3]), float(coord[4]), float(coord[5]))
            edge = (vertexStart, vertexEnd)
            ground.edges.append(edge)
        grounds.append(ground)
    return grounds
        

def destroyNeighborhood(cell):
    
    global doReturn
    global integrity
#
    doReturn = False
    destlist = []
    destructionList(cell, destlist)
    
#    for c in destlist:
#       if c.isGroundCell and c.integrity(integrity): 
#           print("GroundCell Found:", c.center)
#           return
        
    #destroy unconnected cells -> enable physics within radius -> fuzzy
 #   print("Destruction List(no ground)", len(destlist))
   # cells = dict(cell.grid.cells)
    cells = cell.grid.cells
    
    for c in destlist:
        destroyCell(c, cells)  
   
    
def destroyCell(cell, cells):
    for item in cells.items():
        if cell == item[1] and item[0] in cells:
            del cells[item[0]]
            break
        
    print("Destroyed: ", cell.gridPos)
    childs = [c for c in cell.children]
    for child in cell.children:
      #  print("cell child: ", o)
        o = logic.getCurrentScene().objects[child]
        o.removeParent()
        o.restoreDynamics()
        childs.remove(child)
            
    cell.children = childs      
  #  cell.grid.cells = cells
    

def destructionList(cell, destList):
    
    global doReturn
    global integrity  
    
#   if cell.visit:
#        return
#    cell.visit = True
    
    if (cell.isGroundCell and cell.integrity(integrity)) or cell.visit:
        #print("GroundCell Found:", cell.gridPos)
        while len(destList) > 0:
            c = destList.pop()
            c.visit = True
        doReturn = True    
        return
    
    for neighbor in cell.neighbors:
        if doReturn:
            return    
        if neighbor != None: 
            if not neighbor in destList:
                destList.append(neighbor)
                if neighbor.integrity(integrity):
                    destructionList(neighbor, destList)
                        
    #append self to destlist ALWAYS (if not already there)          
    if cell not in destList:         
        destList.append(cell)
       
    #in a radius around collision check whether this are shards of a destructible /or 
    #whether it is a destructible at all if it is activate cell children and reduce integrity of
    #cells if ground connectivity is taken care of
    