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

#sensorName = "D_destructor" 
#massFactor = 4
#speedFactor = 2
#defaultRadius = 2
#define Parameters for each object ! here defined for testing purposes
maxHierarchyDepth = 1 # this must be stored per destructor, how deep destruction shall be
#otherwise 1 level each collision with destroyer / ground
#maxHierarchyDepth = 2  #this must be stored in scene
doReturn = False
integrity = 0.5

children = {}
scene = logic.getCurrentScene()
gridValid = False
firstparent = []
firstShard = {}

#TODO, temporary hack
ground = None
def setup():
    
    #doReturn = False
    #scene = logic.getCurrentScene()    
    
    global firstparent
    global firstShard
    global ground
    global children
    
    #temp hack
  #  player = scene.objects["Player"]
#    player.removeParent()
    
    #temporarily parent
    for o in scene.objects:
        if o.name != "Player":
            if "myParent" in o.getPropertyNames():
                parent = o["myParent"]
                if parent.startswith("P0") and \
                scene.objects[parent] not in firstparent:
                    firstparent.append(scene.objects[parent])
                print("Setting temp parent", o, parent)
                o.setParent(scene.objects[parent])
    
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():
            if o.name.endswith("backup"):
                for c in o.parent.children:
                    if c != o:
                        print ("Visible = false")
                        c.visible = False
                
  #  print(firstparent)
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():  
            print(o, o.parent, len(o.parent.children))
            
            if "flatten_hierarchy" in o.getPropertyNames():
                if o["flatten_hierarchy"]:
                    for fp in firstparent:
                        objname = o.name.split(".")[0]
                        if fp.name not in children.keys() and objname in fp.name:
                            children[fp.name] = list()
                            children[fp.name].append(o)
                            if o.name.startswith("P"):
                                while len(o.children) != 0:
                                    o = o.children[0]
                            firstShard[fp.name] = o
                        elif objname in fp.name:
                            children[fp.name].append(o)
                else:
                    if o.parent.name not in children.keys():
                        children[o.parent.name] = list()
                    if o.name.startswith("P") and len(o.children) > 0:
                        ch = o.children[0]
                    else:
                        ch = o
                    children[o.parent.name].append(ch)
                    
            
                     
            
        #remove temporary parenting
        if o.name != "Player" and o.name != "Launcher" and \
        o.name != "Eye":
            o.removeParent()
    print(len(children))
      
    for i in children.items():
      #  scene.objects[i[0]].endObject()
        for c in i[1]: 
            totalMass = i[1][0].mass
            if c != i[1][0]: 
                if "flatten_hierarchy" in c.getPropertyNames():
                    mass = c.mass
                    oldPar = scene.objects[i[0]]
                   # print("OLDPAR: ", oldPar.name)
                    objname = c.name.split(".")[0]
                    #print(objname, objname in oldPar.name)
                    if c["flatten_hierarchy"] and c not in firstShard and objname in oldPar.name:   #this should be a global setting....
                        print("Setting parent", c, " -> ", firstShard[oldPar.name])
                        c.setParent(firstShard[oldPar.name], True, False)   
                    elif c not in firstShard and objname in oldPar.name:
                        parent = i[1][0]
                        print("Setting parent hierarchically", c, " -> ", parent)      
                        c.setParent(parent, True, False)
                        #set hierarchical masses...
                    totalMass += mass
                    
                    #oldPar = scene.objects[i[0]]
                    
                    #keep sticky if groundConnectivity is wanted
                    if isGroundConnectivity(oldPar):
                      #  print("Setting Sticky")
                        c.suspendDynamics()
                        firstShard[oldPar.name].suspendDynamics()
                        ground = scene.objects["Ground"]
                        c.setParent(ground, True, False)
                        
    #    if "flatten_hierarchy" in i[1][0].getPropertyNames():
    #        firstShard.mass = totalMass
    #    else:
    #        i[1][0].mass = totalMass
                    
#    print("Children:", len(children))
def checkSpeed():
    #print("In checkSpeed")
    global gridValid
    control = logic.getCurrentController()
    owner = control.sensors["Always"].owner #name it correctly
    
    vel = owner.linearVelocity
    thresh = 0.001
    if math.fabs(vel[0]) < thresh and math.fabs(vel[1]) < thresh and math.fabs(vel[2]) < thresh:
        if not gridValid:
            calculateGrids()
            gridValid = True
        

def calculateGrids():
     #rotate parent HERE by 45 degrees, X Axis (testwise)
   # firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
    #oldOrientation = Matrix(firstparent.worldOrientation)
    
    #Grid neu berechnen nach Bewegung.... oder immer alles relativ zur lokalen/Worldposition
    global firstparent
    global firstShard
    global ground
    
    print("In Calculate Grids")
    #firstShard.suspendDynamics()
    
    for o in scene.objects:
        if isGroundConnectivity(o) or (isGround(o) and not isDestructor(o)):
            print("ISGROUNDCONN")
            
            bbox = getFloats(o["gridbbox"])
            dim = getInts(o["griddim"])
            
            grounds = getGrounds(o)
            groundObjs = [logic.getCurrentScene().objects[g.name] for g in grounds]
            
            for fp in firstparent:
                if o.name in fp.name:
                    [g.setParent(fp, False, False) for g in groundObjs]
                    
                    oldRot = Matrix(fp.worldOrientation)
                    fp.worldOrientation = Vector((0, 0, 0))
                    for g in grounds:
                        g.pos = Vector(logic.getCurrentScene().objects[g.name].worldPosition)
                        print(g.pos)
                        
                  #  firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
                #    [g.removeParent() for g in groundObjs]
                    
                    grid = dd.Grid(dim, o.worldPosition, bbox, children[o.name], grounds)
                    grid.buildNeighborhood()
                    grid.findGroundCells() 
                    dd.DataStore.grids[o.name] = grid
                    
                   # firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
                    fp.worldOrientation = oldRot
                    [g.removeParent() for g in groundObjs]
            
           # ground = groundObjs[0]
        
    print("Grids: ", dd.DataStore.grids)  
    
    #rotate parent HERE by 45 degrees, X Axis (testwise)
    #firstparent.worldOrientation = Vector((math.radians(45), 0, 0))
        
    
def collide():
    
    global maxHierarchyDepth
    global ground
    #colliders have collision sensors attached, which trigger for registered destructibles only
    
    #first the script controller brick, its sensor and owner are needed
    control = logic.getCurrentController()
    scene = logic.getCurrentScene()
    sensor = control.sensors["Collision"]
    owner = sensor.owner
    #treat each hit object, check hierarchy
  #  print(sensor.hitObjectList)
   
    maxHierarchyDepth = owner["hierarchy_depth"]
    
    gridValid = False
    
    speed = 0
    for p in children.keys():
        for obj in children[p]:
             tempspeed = obj.worldLinearVelocity.length
             if tempspeed != 0:
                speed = tempspeed
    
   # print("Speed", speed)    
    for p in children.keys():
      #  print(children[p][0])
        for obj in children[p]:
            ownerspeed = owner.worldLinearVelocity.length
            if ownerspeed < 0.0001:
                ownerspeed = speed # use objects speed then
           # print(speed)
            if obj.getDistanceTo(owner) < math.sqrt(ownerspeed / 2):
                dissolve(obj, 1, maxHierarchyDepth, owner)
    
    if ground != None:            
        for c in ground.children:
            if c.getDistanceTo(owner) < math.sqrt(owner.worldLinearVelocity.length / 2):
                dissolve(c, 1, maxHierarchyDepth, owner)
                 
#recursively destroy parent relationships    
def dissolve(obj, depth, maxdepth, owner):
   
   
    for v in children.values():
        for c in v:
            if not c.name.endswith("backup"): 
                c.visible = True
            else:
                c.visible = False
         
    parent = None
    for p in children.keys():
     #   print(p, children[p])
        if obj in children[p]:
            parent = p
            break
        
    par = None
    if parent != None:
       par = scene.objects[parent]
    else:
       par = ground
    
   # print("Owner:", owner, isRegistered(par, owner))      
    if isDestroyable(par) and isRegistered(par, owner) or isGround(par):
        
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
   #  print("activated: ", child)
     global integrity
     global firstShard
     
     parent = None
     for p in children.keys():
        if child in children[p]:
            parent = p
            break
    
     #ground is parent when connectivity is used    
     if parent == None:
         par = ground
     else:
         par = scene.objects[parent]
     
     #if parent is hit, reparent all to first child if any
     #TODO: do this hierarchical
     if child in firstShard.values() and not isGroundConnectivity(par):
         print("HIT PARENT", par)
         for ch in firstShard[par.name].children:
             ch.removeParent()
              #      ch.setParent(newParent, True, False)
         
#  #      mass = firstShard.mass
#         if len(firstShard.children) > 0:
#             newParent = firstShard.children[0]
#          #   newParent.compound = True
#             newParent.suspendDynamics()
#        #     newParent.setParent(ground, True, False)
#             for ch in firstShard.children:
#                if ch != newParent:
#                    ch.removeParent()
#                    ch.setParent(newParent, True, False)
#                    
#             newParent.mass = mass
#             firstShard = newParent        
                 
     if isGroundConnectivity(par) or isGround(par) and gridValid:
         if grid != None:
             cells = dict(grid.cells)
             gridPos = grid.getCellByName(child.name)
             
             if gridPos in cells.keys():
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
                    
    # if child.parent != None:
    #    child.parent.mass -= child.mass
    #    print("Mass : ", child.parent.mass)
        
     
     
    # if not isGroundConnectivity(par) or isGround(par):# or child != firstShard
     child.removeParent()
     child.restoreDynamics()
     
     if child in children[parent]:
        children[parent].remove(child)
     

def isGroundConnectivity(obj):
    if "groundConnectivity" not in obj.getPropertyNames():
        return False
    return obj["groundConnectivity"]

def isDestroyable(destroyable):
    if destroyable == None or "destroyable" not in destroyable.getPropertyNames():
        return False
    return destroyable["destroyable"]

def isDestructor(obj):
    if obj == None or "destructor" not in obj.getPropertyNames():
        return False
    return obj["destructor"]

def isGround(obj):
    if "isGround" not in obj.getPropertyNames():
        return False
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