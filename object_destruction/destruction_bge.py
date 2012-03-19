from bge import logic
import destruction_data as dd
import math
from mathutils import Vector, Matrix
from time import clock
import bpy
from threading import Timer


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

#define Parameters for each object ! here defined for testing purposes
maxHierarchyDepth = 1 # this must be stored per destructor, how deep destruction shall be
doReturn = False
integrity = 0.5

children = {}
scene = logic.getCurrentScene()
gridValid = False
firstparent = []
firstShard = {}
bpyObjs = {}
delay = 0
#alive_threshold = 5

#TODO, temporary hack
ground = None
destructors = []

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
    if a in destructors and isGround(a):
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

def descendants(p):
    ret = []
    ret.extend(p.children)
    for c in p.children:
        ret.extend(descendants(c))
    return ret 


#def decideDeactivation(obj):
#    if not obj.invalid and obj.getLinearVelocity() <= alive_threshold:
#        obj.suspendDynamics()               

def setup():
    
    global firstparent
    global firstShard
    global ground
    global children
    global destructors
    
    #temporarily parent
    for o in scene.objects:
        if o.name != "Player":
            if "myParent" in o.getPropertyNames():
                parent = o["myParent"]
                
                if bpy.context.scene.hideLayer != 1:
                    if parent not in scene.objects:
                        p = scene.addObject(parent, parent)
                    else:
                        p = scene.objects[parent]    
                else:
                    p = scene.objects[parent]
                
                if parent.startswith("P_0") and p not in firstparent:
                    firstparent.append(p)
                print("Setting temp parent", o, parent)
                o.setParent(p)
                bpyObjs[o.name] = bpy.context.scene.objects[o.name]
                o["activated"] = False
        if o.name == "Ground":
            bpyObjs[o.name] = bpy.context.scene.objects[o.name]
        if "destructor" in o.getPropertyNames():
            destructors.append(o)
            bpyObjs[o.name] = bpy.context.scene.objects[o.name]
    
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():  
            #print(o, o.parent, len(o.parent.children))
            if "flatten_hierarchy" in o.getPropertyNames():
                if o["flatten_hierarchy"]:
                    for fp in firstparent:
                        
                        desc = descendants(fp)
                      #  print(desc)
                        if bpyObjs[o.name].game.use_collision_compound and o in desc :
                            if fp.name not in firstShard.keys():
                                print("Setting compound", o.name)
                                firstShard[fp.name] = o
                                 
                        if fp.name not in children.keys() and o in desc and not o.name.startswith("P_"):
                            children[fp.name] = list()
                            children[fp.name].append(o.name)
                            
                        elif o in desc and not o.name.startswith("P_"):
                            children[fp.name].append(o.name)
                            
                else:
                     if not o.name.startswith("P_"):
                        if o.parent.name not in children.keys():
                            children[o.parent.name] = list()
                        children[o.parent.name].append(o.name)
    
    for o in scene.objects:
        if "myParent" in o.getPropertyNames(): 
            o.removeParent()                   
            
    print(len(children))
         
    compounds = {}
    realcompounds = {}              
    
    for i in children.items():
        parent = None
        oldPar = scene.objects[i[0]]  
        split = oldPar.name.split(".")
        temp = split[0]
        
        if len(split) >= 4:
            start = temp.split("_")[3]
        else:
            start = temp
         
        
        #backup = bpyObjs[oldPar.name].destruction.backup
        
        for c in i[1]:    
            if bpyObjs[c].game.use_collision_compound or \
            bpyObjs[c].destruction.wasCompound:
                parent = c
                if start not in compounds.keys():
                    compounds[start] = list()
                compounds[start].append(c)
                
                if bpyObjs[c].game.use_collision_compound:
                    realcompounds[start] = c
                
                 
        for c in i[1]:
            if c != parent:
                o = scene.objects[c] 
                if "flatten_hierarchy" in o.getPropertyNames():
                    if o["flatten_hierarchy"] and o not in firstShard:
                        #if oldPar.name in firstShard: 
                        parent = firstShard[oldPar.name]
                        print("Setting parent", o, " -> ", parent)
                        o.setParent(parent, True, False)   
                    elif c not in firstShard:
                        #if c != backup:
                        print("Setting parent hierarchically", c, " -> ", parent)  
                        o.setParent(parent, True, False)
                 
                    #keep sticky if groundConnectivity is wanted
                    if isGroundConnectivity(oldPar):
                        o.suspendDynamics()
                     #   scene.objects[parent].suspendDynamics()
                        ground = scene.objects["Ground"]
                        o.setParent(ground, True, False)
        
        if start not in compounds.keys():
            return
        
        print(compounds[start])                
        if len(compounds[start]) > 1:
            real = scene.objects[realcompounds[start]]
            for c in compounds[start]:
                if c != real.name:
                    childs = [ob for ob in scene.objects[c].children]
                    for ch in childs:
                        print("Re-Setting compound", ch,  " -> ", real) 
                        ch.removeParent()
                        ch.setParent(real, True, False)
                        #ch["compound"] = c
                    
                    o = scene.objects[c]    
                    print("Re-Setting compound", o,  " -> ", real) 
                    o.setParent(real, True, False)
                                   
                        
def checkSpeed():
    #print("In checkSpeed")
    global gridValid
    control = logic.getCurrentController()
    owner = control.sensors["Always"].owner #name it correctly
    
    
    if owner.name.startswith("P_"):
        return
    
    for p in children.keys():
        for obj in children[p]:
            if obj == owner.name and not isGroundConnectivity(scene.objects[p]):
                return 
        
    vel = owner.linearVelocity
    thresh = 0.001
    if math.fabs(vel[0]) < thresh and math.fabs(vel[1]) < thresh and math.fabs(vel[2]) < thresh:
        if not gridValid:
            calculateGrids()
            gridValid = True
        

def calculateGrids():
    
    #recalculate grid after movement
    global firstparent
    global firstShard
    global ground
    global children
    
    print("In Calculate Grids")
    
    
    for o in scene.objects:
        if isGroundConnectivity(o) or (isGround(o) and not isDestructor(o)):
            print("ISGROUNDCONN")
            
            bbox = getFloats(o["gridbbox"])
            dim = getInts(o["griddim"])
            
            grounds = getGrounds(o)
            groundObjs = [logic.getCurrentScene().objects[g.name] for g in grounds]
            
            for fp in firstparent:
                #fp = scene.objects[f]
                if o.name in fp.name:
                    [g.setParent(fp, False, False) for g in groundObjs]
                    
                    oldRot = Matrix(fp.worldOrientation)
                    fp.worldOrientation = Vector((0, 0, 0))
                    for g in grounds:
                        g.pos = Vector(logic.getCurrentScene().objects[g.name].worldPosition)
                        print(g.pos)
                        
                    
                    childs = [scene.objects[c] for c in children[o.name]]
                    grid = dd.Grid(dim, o.worldPosition, bbox, childs, grounds)
                    grid.buildNeighborhood()
                    grid.findGroundCells() 
                    dd.DataStore.grids[o.name] = grid
                    
                    fp.worldOrientation = oldRot
                    [g.removeParent() for g in groundObjs]
            
           # ground = groundObjs[0]
        
    print("Grids: ", dd.DataStore.grids) 
    

def distSpeed(owner, obj, maxDepth):
    speed = (owner.worldLinearVelocity - obj.worldLinearVelocity).length
    dist = getFaceDistance(owner, obj)
            
    modSpeed = 1 + speed
    if owner.name == "Ball": # and bpy.context.scene.hideLayer == 1:
        modSpeed = math.sqrt(speed / 2)
    
    depth = math.ceil(maxDepth * 1.0 / modSpeed) 
    #return dist < modSpeed
    return dist, modSpeed, depth
    
def collide():
    
    global maxHierarchyDepth
    global ground
    #colliders have collision sensors attached, which trigger for registered destructibles only
    
    #first the script controller brick, its sensor and owner are needed
    control = logic.getCurrentController()
    scene = logic.getCurrentScene()
    sensor = control.sensors["Collision"]
    owner = sensor.owner
    
   
    maxHierarchyDepth = owner["hierarchy_depth"]
    
    gridValid = False
    
   # print("collide")
    
    objs = []
    for p in children.keys():
        for objname in children[p]:
          #  print("objname", p, objname)
            if not objname.startswith("P_"):
                objs.append(objname)
            
    for ob in objs:
        if ob in scene.objects:
            obj = scene.objects[ob]
            dist, speed, depth =  distSpeed(owner, obj, maxHierarchyDepth)
            if dist < speed:   
                dissolve(obj, depth, maxHierarchyDepth, owner)
    
            
                
def swapBackup(obj):    
    
    global children
    global firstparent
    
    print("swap backup")
    ret = []   
    
    parent = bpy.context.scene.objects[obj.name].destruction.is_backup_for
    if parent == "":
        return
    if parent not in scene.objects:
       par = scene.addObject(parent, parent)
    else:
       par = scene.objects[parent]
    
    #TODO: hack -> find first parent, ground connectivity on subparents is unsupported by now.
    #what about loose parts parents (they have another name mostly) ?
    #maybe store a reference to the firstparent directly.
    temp = parent.split(".")[0]
    pstart = temp.split("_")[3]
    
    first = None
    for fp in firstparent:
        temp = fp.name.split(".")[0]
        fstart = temp.split("_")[3]
        if fstart == pstart:
            first = fp
          
    childs= bpy.context.scene.objects[parent].destruction.children
    compound = None
    for c in childs:
        if bpy.context.scene.objects[c.name].game.use_collision_compound: 
            mesh = bpy.context.scene.objects[c.name].data.name
            print("Adding compound", c.name)
            compound = scene.addObject(c.name, c.name)
            compound.replaceMesh(mesh, True, True)
            if not isGroundConnectivity(first):
                compound.worldPosition += obj.worldPosition
            ret.append(compound)
                     
    for c in childs:
        if c.name != compound.name and c.name != obj.name:
            print("Adding children", c.name)
            
            if c.name.startswith("P_"):
                name = bpy.context.scene.objects[c.name].destruction.backup
            else:
                name = c.name
            
            mesh = bpy.context.scene.objects[name].data.name
            o = scene.addObject(name, name)
            o.replaceMesh(mesh, True, True)
            if not isGroundConnectivity(first):
                o.worldPosition += obj.worldPosition
                o.setParent(compound, True, False)
            else:
                
                if not o.invalid:
                    o.suspendDynamics()
                    o.setParent(ground, True, False)
                         
            ret.append(o)
    
    if not isGroundConnectivity(first):        
        compound.worldOrientation = obj.worldOrientation
        compound.linearVelocity = obj.linearVelocity
        compound.angularVelocity = obj.angularVelocity
    else:
        compound.setParent(ground, True, False)
    
    if parent in children.keys():
        children[parent].remove(obj.name)
    obj.endObject()
    
    for r in ret:
        if parent not in children.keys():
            children[parent] = list()
        children[parent].append(r.name)
    
    if isGroundConnectivity(first):
        calculateGrids()
      
    return ret

def inside(c):
    return c in scene.objects
   
#recursively destroy parent relationships    
def dissolve(obj, depth, maxdepth, owner):
   # print("dissolve")               
    parent = None
    for p in children.keys():
        if obj.name in children[p]:
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
        if par != None and par.name != "Ground":
            digitEnd = par.name.split("_")[1]
            objDepth = int(digitEnd)
            bDepth = backupDepth(obj)
            
            #swap and re-check distance
          #  print(depth, objDepth+1, bDepth+1)
            if bpy.context.scene.hideLayer != 1 and depth == bDepth + 1 and isBackup(obj):
                print(depth, bDepth+1)
                objs = swapBackup(obj)
                obj["swapped"] = True
                #[activate(ob, owner, grid) for ob in objs if distSpeed(owner,ob)]
            
            if depth == objDepth + 1:
                activate(obj, owner, grid)
       
        if depth < maxdepth and parent != None: 
            childs = [scene.objects[c] for c in children[parent] if inside(c)]
            [dissolve(c, depth + 1, maxdepth, owner) for c in childs]

def activate(child, owner, grid):
    
    # print("activated: ", child)
     global integrity
     global firstShard
     global delay
     
     if "dead_delay" in owner.getPropertyNames():
        delay = owner["dead_delay"]
     else:
        delay = 0
     
     parent = None
     for p in children.keys():
        if child.name in children[p]:
            parent = p
            break
    # print("PARENT", parent)
     #ground is parent when connectivity is used    
     if parent == None:
         par = ground
     else:
         par = scene.objects[parent]
                 
     #if isGroundConnectivity(par) or isGround(par) and gridValid:
     if isGroundConnectivity(par) and gridValid:
         if grid != None:
             cells = dict(grid.cells)
             gridPos = grid.getCellByName(child.name)
             
             if gridPos in cells.keys():
                 cell = cells[gridPos]
                 
                 if delay == 0:
                    if (child.name in cell.children):
                        cell.children.remove(child.name)
                
                 if not cell.integrity(integrity):
                    print("Low Integrity, destroying cell!")
                    destroyCell(cell, cells)
                    
                    
                 for c in cells.values():
                    destroyNeighborhood(c)
                 
                 for c in cells.values():
                    c.visit = False
    
     child.restoreDynamics()
     
    
     if delay == 0:              
        child.removeParent()
        child["activated"] = True
        
        if parent != None:
            if child.name in children[parent]:
                children[parent].remove(child.name)
     else:
        if not child.invalid:
            t = Timer(delay, child.suspendDynamics)
            t.start()
            
def isGroundConnectivity(obj):
    if obj == None or "groundConnectivity" not in obj.getPropertyNames():
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
    if obj == None or "isGround" not in obj.getPropertyNames():
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

def backupDepth(backup):
    parent = bpy.context.scene.objects[backup.name].destruction.is_backup_for
    if parent != "":
        split = parent.split("_")[1]
        return int(split)
    return -10

def isBackup(backup):
    swapped = "swapped" not in backup.getPropertyNames()
    return swapped
        

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
    
    global delay
    
    if delay == 0:
        for item in cells.items():
            if cell == item[1] and item[0] in cells:
                del cells[item[0]]
                break
        
    print("Destroyed: ", cell.gridPos)
    childs = [c for c in cell.children]
    for child in cell.children:
      #  print("cell child: ", o)
        if child in scene.objects:
            o = scene.objects[child]
            o.restoreDynamics()
            if delay == 0:
                o.removeParent()
                childs.remove(child)
                o["activated"] = True
            else:
                if not o.invalid:
                    t = Timer(delay, o.suspendDynamics)
                    t.start()
        else:
            childs.remove(child) #remove invalid child
                    
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