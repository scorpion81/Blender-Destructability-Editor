from bge import logic
import destruction_data as dd
import math
from mathutils import Vector, Matrix
from time import clock
import bpy


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
bpyObjs = {}
startclock = dd.startclock
firstHit = False

#TODO, temporary hack
ground = None
destructors = []
#facelist = []


def compareNormals(faces, face):
    for f in faces:
        dot = round(f.normal.dot(face.normal), 5)
        prod = round(f.normal.length * face.normal.length, 5)
        #normals point in opposite directions
        if dot == -prod:
            return True
    return False

def changeMaterial(child):
    for obj in scene.objects:
        if "activated" in obj.getPropertyNames(): 
            if obj.getDistanceTo(child) < 2 and not obj["activated"]:
                o = bpyObjs[child.name]
                for f in o.data.polygons:
                    f.material_index = 0
                    f.keyframe_insert("material_index")

def project(p, n):
    
    #project point / plane by omitting coordinate which is the largest in the normal vector
    max = 0
    maxindex = 2
    for i in range(0, 3):
        co = math.fabs(n[i])
        if co > max:
            maxindex = i
            max = co
    
    if maxindex == 0:
        v1 = 1
        v2 = 2
    elif maxindex == 1:
        v1 = 0
        v2 = 2
    elif maxindex == 2:
        v1 = 0
        v2 = 1
    
 #   print(p)
    p1 = Vector((p[v1], p[v2]))
    
    return p1

def isLeft(a, b, p):
    
    return (b[0] - a[0]) * (p[1] - a[1]) - (p[0] - a[0]) * (b[1] - a[1]) 

def inside(p, n, obj):
    #print(obj)
    verts = obj.data.vertices
    edges = obj.data.edges
    wn = 0
    for e in edges:
        v1 = verts[e.vertices[0]]
        v2 = verts[e.vertices[1]]
        
        vp1 = project(v1.co, n)
        vp2 = project(v2.co, n)
        p1 = project(p, n)
        
        if (vp1[1] <= p1[1]):                         # start y <= P.y
            if (vp2[1] > p1[1]):                      # an upward crossing
                if (isLeft( vp1, vp2, p1) > 0):       # P left of edge
                    wn += 1                           # have a valid up intersect
        
        else:                                         # start y > P.y (no test needed)
            if (vp2[1] <= p1[1]):                     # a downward crossing
                if (isLeft( vp1, vp2, p1) < 0):       # P right of edge
                    wn -= 1                           # have a valid down intersect
    return wn != 0
        
def distance(p, a, b, c, obj):
    n = (c-a).cross(b-a)
    
    f = -n.dot(p-a) / n.dot(n)
    q = p + f * n
    
    dist = 10000000000
    if inside(q, n, obj):
        dist = (p - q).length
    return dist

def getFaceDistance(a, b):
    
    # hack
    #print(a, b)
    global destructors
    if a in destructors and a.name != "Ball":
        mindist = 10000000000
        obj = bpyObjs[a.name]
        for f in obj.data.polygons:
           v1 = obj.data.vertices[f.vertices[0]].co
           v2 = obj.data.vertices[f.vertices[1]].co
           v3 = obj.data.vertices[f.vertices[2]].co
           
           dist = distance(b.worldPosition, v1, v2, v3, obj)
           
           if dist < mindist:
               mindist = dist
       # print("MinDist", mindist)
        return mindist
    else:
        return a.getDistanceTo(b)


def setup():
    
    #doReturn = False
    #scene = logic.getCurrentScene()    
    
    global firstparent
    global firstShard
    global ground
    global children
    global destructors
   # global facelist
   # global startclock
    
    #temp hack
  #  player = scene.objects["Player"]
#    player.removeParent()
    
  #  startclock = clock()
    #temporarily parent
    for o in scene.objects:
        if o.name != "Player":
            if "myParent" in o.getPropertyNames():
                parent = o["myParent"]
                if parent.startswith("P_0") and \
                scene.objects[parent] not in firstparent:
                    firstparent.append(scene.objects[parent])
                print("Setting temp parent", o, parent)
                o.setParent(scene.objects[parent])
                bpyObjs[o.name] = bpy.context.scene.objects[o.name]
                o["activated"] = False
               # obj = bpyObjs[o.name]
            #    for f in obj.data.polygons:
             #       facelist.append(f)
        if o.name == "Ground":
            bpyObjs[o.name] = bpy.context.scene.objects[o.name]
        if "destructor" in o.getPropertyNames():
            destructors.append(o)
            bpyObjs[o.name] = bpy.context.scene.objects[o.name]
    
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():
            if o.name.endswith("backup"):
                bpy.context.scene.frame_current = 0
                for c in o.parent.children:
                    if c != o:
                        print ("Visible = false")
                        bpyObjs[c.name].hide_render = True
                        bpyObjs[c.name].hide = True
                     #   bpyObjs[c.name].keyframe_insert("hide_render")
                      #  bpyObjs[c.name].keyframe_insert("hide")
                        c.visible = False
                bpyObjs[o.name].hide_render = False
                bpyObjs[o.name].hide = False
            #    bpyObjs[o.name].keyframe_insert("hide_render")
           #     bpyObjs[o.name].keyframe_insert("hide")
                o.visible = True
                
  #  print(firstparent)
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():  
            print(o, o.parent, len(o.parent.children))
            
            if "flatten_hierarchy" in o.getPropertyNames():
                if o["flatten_hierarchy"]:
                    for fp in firstparent:
                        split = o.name.split(".")
                        objname = ""
                        for s in split[:-1]:
                            objname = objname + "." + s
                        objname = objname.lstrip(".")
                        
                        if bpyObjs[o.name].game.use_collision_compound:
                            firstShard[fp.name] = o
                                
                        if fp.name not in children.keys() and fp.name.endswith(objname + ".000"):
                            children[fp.name] = list()
                            children[fp.name].append(o)
                            #if o.name.startswith("P_"):
                            #    while len(o.children) != 0:
                            #        o = o.children[0]
                        elif fp.name.endswith(objname + ".000"):
                            children[fp.name].append(o)
                else:
                    if o.parent.name not in children.keys():
                        children[o.parent.name] = list()
                    if o.name.startswith("P_") and len(o.children) > 0:
                        for c in o.children:
                            if bpyObjs[c.name].game.use_collision_compound:
                            #ch = o.children[0]
                                ch = c
                                break
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
        parent = None
        for c in i[1]:    
           if bpyObjs[c.name].game.use_collision_compound:
                parent = c
                break
            
        for c in i[1]:
            totalMass = parent.mass
            if c != parent: 
                if "flatten_hierarchy" in c.getPropertyNames():
                    mass = c.mass
                    oldPar = scene.objects[i[0]]
                    split = c.name.split(".")
                    objname = ""
                    for s in split[:-1]:
                        objname = objname + "." + s
                    objname = objname.lstrip(".")
                    print("OBJNAME", objname, oldPar)
                    if c["flatten_hierarchy"] and c not in firstShard and \
                    oldPar.name.endswith(objname + ".000"):   #this should be a global setting....
                        parent = firstShard[oldPar.name]
                        print("Setting parent", c, " -> ", parent)
                        c.setParent(parent, True, False)   
                    elif c not in firstShard and oldPar.name.endswith(objname + ".000"):
                        print("Setting parent hierarchically", c, " -> ", parent)      
                        c.setParent(parent, True, False)
                        #set hierarchical masses...
                    totalMass += mass
                    
                    #oldPar = scene.objects[i[0]]
                    
                    #keep sticky if groundConnectivity is wanted
                    if isGroundConnectivity(oldPar):
                      #  print("Setting Sticky")
                        c.suspendDynamics()
                        parent.suspendDynamics()
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
    
    if owner.name.startswith("P_"):
        return
        
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
   # global facelist
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
    if owner.name != "Ball":
        for p in children.values():
            for obj in p:
                tempspeed = obj.worldLinearVelocity.length
                if tempspeed != 0:
                    #print("Temp", tempspeed)
                    speed = tempspeed    
    #for p in sensor.hitObjectList:
    #    print("HIT", p)  #always the compound object...
    
    for p in children.keys():
        for obj in children[p]:
            ownerspeed = owner.worldLinearVelocity.length
            if ownerspeed < 0.0001:
            #    print("Spd: ",ownerspeed, speed)
                ownerspeed = speed # use objects speed then
            dist = getFaceDistance(owner, obj)
            
            
            modSpeed = math.sqrt(ownerspeed / 5)
           # if not isGroundConnectivity(scene.objects[p]) and not owner.name == "Ball":
        #        modSpeed = 1
          
            if dist < modSpeed:
                dissolve(obj, 1, maxHierarchyDepth, owner)
               
#    if ground != None:            
#        for c in ground.children:
#            if getFaceDistance(owner, obj) < owner.worldLinearVelocity.length / 2:
#                dissolve(c, 1, maxHierarchyDepth, owner)
            
#recursively destroy parent relationships    
def dissolve(obj, depth, maxdepth, owner):
   
    global startclock
    global firstHit
    #global facelist
    
#    if not firstHit:
#        firstHit = True   
#        for v in children.values():
#            for c in v:
#                if not c.name.endswith("backup"): 
#                    c.visible = True
#                    bpyObjs[c.name].hide_render = False
#                    bpyObjs[c.name].hide = False
#                else:
#                    c.visible = False
#                    bpyObjs[c.name].hide_render = True
#                    bpyObjs[c.name].hide = True
#                
#                time = clock() - startclock
#                frame = time * bpy.context.scene.game_settings.fps
#               # frame = c.getActionFrame(1)
#               # print(frame)   
#                bpy.context.scene.frame_current = frame
#                #bpyObjs[c.name].keyframe_insert("hide_render")
#                #bpyObjs[c.name].keyframe_insert("hide")
            
         
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
            digitEnd = par.name.index("_", 2)
            objDepth = int(par.name[2 : digitEnd]) + 1
           # print(depth, objDepth)
            
            if depth == objDepth:
                #[activate(c, owner, grid) for c in obj.parent.children]
                activate(obj, owner, grid)
       
        if depth < maxdepth: 
            [dissolve(c, depth + 1, maxdepth, owner) for c in children[parent]]

def activate(child, owner, grid):
 #   if child.getDistanceTo(owner.worldPosition) < defaultRadius:         
    # print("activated: ", child)
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
#     if child in firstShard.values() and not isGroundConnectivity(par):
#         print("HIT PARENT", par)
#         for c in firstShard[par.name].children:
#            if not c["activated"]:
#                newParent = c
#                newParent.suspendDynamics()
#                break
#            
#         bpyObjs[newParent.name].game.use_collision_compound = True
#         for ch in firstShard[par.name].children:
#             if not ch["activated"] and ch != newParent:
           #    bpyObjs[ch.name].game.use_collision_compound = False
#                ch.removeParent()
               # ch.suspendDynamics()
           #     ch.setParent(newParent, True, False)
         
         #newParent.restoreDynamics()
                 
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
     child["activated"] = True
     
  #   changeMaterial(child)
     
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
        o["activated"] = True
      #  changeMaterial(o)
            
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