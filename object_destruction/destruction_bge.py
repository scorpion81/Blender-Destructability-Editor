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
maxHierarchyDepth = 1 # this must be stored per destructor, how deep destruction shall be
#otherwise 1 level each collision with destroyer / ground
#maxHierarchyDepth = 2  #this must be stored in scene
doReturn = False
integrity = 0.5

children = {}
scene = logic.getCurrentScene()

def setup():
    
    #doReturn = False
    #scene = logic.getCurrentScene()    
    
    firstparent = None
    firstShard = None
    
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():
            parent = o["myParent"]
            if parent.startswith("P0"):
                firstparent = scene.objects[parent]
            
            if parent not in children.keys():
                children[parent] = list()
                children[parent].append(o)
                if parent == firstparent.name:
                    firstShard = o
            else: 
                children[parent].append(o)
            
 
    for i in children.items():
      #  scene.objects[i[0]].endObject()
        for c in i[1]: 
            if c != i[1][0]: 
                if "flatten_hierarchy" in c.getPropertyNames():
                    if c["flatten_hierarchy"]:
                        print("Setting parent", c, " -> ", firstShard)
                        c.setParent(firstShard, True, False)
                    else:
                        print("Setting parent", c, " -> ", i[1][0])      
                        c.setParent(i[1][0], True, False)
                     
   
   # calcAverages()
    
    #rotate parent HERE by 45 degrees, X Axis (testwise)
   # firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
    #oldOrientation = Matrix(firstparent.worldOrientation)
    
    #Grid neu berechnen nach Bewegung.... oder immer alles relativ zur lokalen/Worldposition
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
    
    global maxHierarchyDepth
    #colliders have collision sensors attached, which trigger for registered destructibles only
    
    #first the script controller brick, its sensor and owner are needed
    control = logic.getCurrentController()
    scene = logic.getCurrentScene()
    sensor = control.sensors["Collision"]
    owner = sensor.owner
    #treat each hit object, check hierarchy
  #  print(sensor.hitObjectList)
   
    maxHierarchyDepth = owner["hierarchy_depth"]
            
  #  for obj in sensor.hitObjectList:
#        print ("Hit: ", obj)
        
    for p in children.keys():
        print(children[p][0])
        for obj in children[p]:
            if obj.getDistanceTo(owner) < 2.0:
                dissolve(obj, 1, maxHierarchyDepth, owner)
                 
#recursively destroy parent relationships    
def dissolve(obj, depth, maxdepth, owner):
    
    parent = None
    for p in children.keys():
     #   print(p, children[p])
        if obj in children[p]:
            parent = p
            break
    par = scene.objects[parent]
          
    if isDestroyable(par) and isRegistered(par, owner):
        
        grid = None
        if par.name in dd.DataStore.grids.keys():
            grid = dd.DataStore.grids[par.name]                
        
        #only activate objects at current depth
        if par != None:
            digitEnd = par.name.index("_")
            objDepth = int(par.name[1 : digitEnd]) + 1
           # print(depth, objDepth)
            
            if depth == objDepth:
                #[activate(c, owner, grid) for c in obj.parent.children]
                activate(obj, owner, grid)
       
        if depth < maxdepth: 
            [dissolve(c, depth + 1, maxdepth, owner) for c in children[parent]]

def activate(child, owner, grid):
 #   if child.getDistanceTo(owner.worldPosition) < defaultRadius:         
     print("activated: ", child)
     global integrity
     
     parent = None
     for p in children.keys():
        if child in children[p]:
            parent = p
            break
     par = scene.objects[parent]
     
     if isGroundConnectivity(par) and not isGround(par):
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
  
        vert = p[1]
        verts = vert.split("_")
        for coords in verts:
            coord = coords.split(",")
 
            vertexStart = (float(coord[0]), float(coord[1]), float(coord[2]))
            vertexEnd = (float(coord[3]), float(coord[4]), float(coord[5]))
            edge = (vertexStart, vertexEnd)
            ground.edges.append(edge)
        grounds.append(ground)
    return grounds
        

def destroyNeighborhood(cell):
    
    global doReturn
    global integrity

    doReturn = False
    destlist = []
    destructionList(cell, destlist)
    
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
    

def destructionList(cell, destList):
    
    global doReturn
    global integrity  
    
    
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
    

#def calcAverages():
#    
#    #after building the parent relationships, unparent temporarily, set empty at average position
#    #and re-parent
#    scene = logic.getCurrentScene()
#    visited = []
#    for o in scene.objects:
#        if o.parent != None:
#            par = o.parent.parent
#            if par != None and par.name != "Player" and par.name != "Eye" and \
#            par.name != "Center":
#                if par.name not in visited:
#                    visited.append(par.name)
#                    childs = []
#                    sumx = 0
#                    sumy = 0
#                    sumz = 0
#                    for c in par.children:
#                        sumx += c.worldPosition[0]
#                        sumy += c.worldPosition[1]
#                        sumz += c.worldPosition[2]
#                        childs.append(c)
#                    length = len(par.children)
#                    if length > 0:
#                        for c in childs:
#                            c.removeParent()
#                        average = Vector((sumx / length, sumy / length, sumz / length))
#                        par.worldPosition = average
#                        print("Average: ", par.name, average)
#                        for c in childs:
#                            c.setParent(par, True, False)
#                
    