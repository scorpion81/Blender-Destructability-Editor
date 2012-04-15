from bge import logic
import destruction_data as dd
import math
from mathutils import Vector, Matrix
from time import clock
import bpy
from threading import Timer
import sys


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
#destructors = []

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
    
    dist = sys.maxsize #10000000000
    if inside(q, n, obj):
        dist = (p - q).length
    return dist

def getFaceDistance(a, b):
    
    # hack
    #print(a, b)
    if isDestructor(a) and isGround(a):
        mindist = sys.maxsize# 10000000000
        obj = bpyObjs[a.name]
        #obj = bpy.context.scene.objects[a.name]
        for f in obj.data.polygons:
           v1 = obj.data.vertices[f.vertices[0]].co
           v2 = obj.data.vertices[f.vertices[1]].co
           v3 = obj.data.vertices[f.vertices[2]].co
           
           dist = distance(b.worldPosition, v1, v2, v3, obj)
           
           if dist < mindist:
               mindist = dist
               #print("MinDist", mindist, a)
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

def setupClusters():
    #setup clusters
    clusterchilds = {}
    parents = [p for p in scene.objects if p.name.startswith("P_")]
    
    #determine max level
    level = 0
    for p in parents:
        lev = int(p.name.split("_")[1])
        if lev > level:
            level = lev
            
    #compare with max level
    leafparents = []        
    for p in parents:
        lev = int(p.name.split("_")[1])
        if lev == level:
            leafparents.append(p)
            
    childs = [c for c in scene.objects if hasMyParent(c, leafparents)]
    
    for p in leafparents:
        par = bpy.context.scene.objects[p.name]
        if par.destruction.cluster:
            for c in childs:
                ch = bpy.context.scene.objects[c.name]
                if not ch.name.startswith("P_") and ch.destruction.is_backup_for == "":  

                   bboxX = ch.bound_box.data.dimensions[0]
                   bboxY = ch.bound_box.data.dimensions[1]
                   bboxZ = ch.bound_box.data.dimensions[2]
                   distVec = c.worldPosition - p.worldPosition
                   if distVec[0] <= par.destruction.cluster_dist[0] / 100 * bboxX and \
                       distVec[1] <= par.destruction.cluster_dist[1] / 100 * bboxY and \
                       distVec[2] <= par.destruction.cluster_dist[2] / 100 * bboxZ:
                           c.setParent(p)
                           if p.name not in clusterchilds.keys():
                                clusterchilds[p.name] = []
                           clusterchilds[p.name].append(c.name)
                           
    #append to higher parents as well
    for p in parents:
        desc = descendants(p)
        for n in clusterchilds.keys():
            if scene.objects[n] in desc:
                for d in desc:
                    if d.name.startswith("P_"):
                        for c in clusterchilds[n]:
                            ch = scene.objects[c]
                            ch.setParent(d) #evtl verdoppeln der objekte....(mehrere Parents geht nicht....)
    

def hasMyParent(obj, leafparents):
    return "myParent" in obj.getPropertyNames() and \
    scene.objects[obj["myParent"]] in leafparents 

def setup():
    
    global firstparent
    global firstShard
    global ground
    global children
   # global destructors
    
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
       # if isDestructor(o):
        #    destructors.append(o)
        #    bpyObjs[o.name] = bpy.context.scene.objects[o.name]
        
    setupClusters()
        
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():  
            #print(o, o.parent, len(o.parent.children))
            if flattenHierarchy(o):
                for fp in firstparent:
                    desc = descendants(fp)
                    if bpyObjs[o.name].game.use_collision_compound and o in desc :
                        if fp.name not in firstShard.keys():
                            print("Setting compound", o.name)
                            fp["compound"] = o.name
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
                    oldPar["compound"] = c
                
                 
        for c in i[1]:
            if c != parent:
                o = scene.objects[c]
                #if isDeformable(o):
                #    p = scene.objects[parent]
                #    print("PARENT", p)
                #    o.setSoftbodyLJoint(p) # joints must be set between adjacent(!) objects
                #    o["joint"] = parent
                #    o.suspendDynamics()
                #    p.suspendDynamics()
                     
                if flattenHierarchy(o) and o not in firstShard:
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
                    #parent.suspendDynamics()
                    ground = scene.objects["Ground"]
                    o.setParent(ground, True, False)
        
        if start in compounds.keys():
            print(compounds[start])                
            if len(compounds[start]) > 1: #TODO, what if there are no real compounds left... use other layers for correct substitution
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

    #swap immediately
    if bpy.context.scene.hideLayer != 1:
        for p in firstparent:
            par = bpy.context.scene.objects[p.name]
            swapBackup(scene.objects[par.destruction.backup])
                                           
def checkSpeed():
    #print("In checkSpeed")
    global gridValid
    control = logic.getCurrentController()
    owner = control.sensors["Always"].owner #name it correctly
    
    
    if owner.name.startswith("P_"):
        return
    
    for p in children.keys():
        for obj in children[p]:
            
            if p not in scene.objects:
                return
            
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
        if isGroundConnectivity(o):# or (isGround(o) and not isDestructor(o)):
            print("ISGROUNDCONN")
            
          #  bbox = getFloats(o["gridbbox"])
        #    dim = getInts(o["griddim"])
            gridbbox = bpy.context.scene.objects[o.name].destruction.gridBBox
            griddim = bpy.context.scene.objects[o.name].destruction.gridDim
            
            bbox = (gridbbox[0], gridbbox[1], gridbbox[2])
            dim = (griddim[0], griddim[1], griddim[2])
            
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
    

def distSpeed(owner, obj, maxDepth, lastSpeed):
    speed = 0
    tempSpeed = (owner.worldLinearVelocity - obj.worldLinearVelocity).length
    if owner.name != "Ball":
        if tempSpeed != 0:
            speed = tempSpeed
        else:
            speed = lastSpeed # only compound parents have a speed....
    else:
        speed = tempSpeed
    
    dist = getFaceDistance(owner, obj)
    
 #   print(owner, obj, dist, speed)        
    modSpeed = 1 + 0.025 *speed
    if owner.name == "Ball": # and bpy.context.scene.hideLayer == 1:
       modSpeed = math.sqrt(speed / 2)
    
    if modSpeed > 0:
        depth = math.ceil(maxDepth * 1.0 / modSpeed)
    else:
        depth = 1 
    #return dist < modSpeed
    return dist, modSpeed, depth
    
def collide():
    
    global maxHierarchyDepth
    global ground
    global firstparent
    #colliders have collision sensors attached, which trigger for registered destructibles only
    
    #first the script controller brick, its sensor and owner are needed
    control = logic.getCurrentController()
    scene = logic.getCurrentScene()
    sensor = control.sensors["Collision"]
    owner = sensor.owner
    
   
    maxHierarchyDepth = hierarchyDepth(owner)
    
    gridValid = False
    
    #print("collide")
    cellsToCheck = []
    lastSpeed = 0 
    #low speed ball makes no damage, so ignore it in collision calculation
    if owner.name == "Ball":
        if owner.worldLinearVelocity.length < 8:
            return
        
    for fp in firstparent:
        if not isGroundConnectivity(fp):
            if "compound" in fp.getPropertyNames() and fp["compound"] in scene.objects:
                compound = scene.objects[fp["compound"]]
                if (compound.worldLinearVelocity.length < 0.05 and owner.name == "Ground"):
                    return #if compound does not move, ignore collisions...
        else: # a quicker pre-test of cells (less than objects)
            if fp.name in dd.DataStore.grids.keys():
                grid = dd.DataStore.grids[fp.name] 
                for cell in grid.cells.values():
                    modSpeed = math.sqrt(owner.worldLinearVelocity.length / 2)
                    celldist = (owner.worldPosition - Vector(cell.center)).length
                    if celldist < modSpeed:
                        cellsToCheck.append(cell)
                          
                
    #g = scene.objects["Plane"]
    #print(sensor.hitObjectList)
    #if g in sensor.hitObjectList:
    #    return       
    
    
        
    objs = []
    if len(cellsToCheck) == 0: #without grid, check all objects (bad)
        for p in children.keys():
            for objname in children[p]:
            #  print("objname", p, objname)
                if not objname.startswith("P_"):
                    objs.append(objname)
    else:
        for c in cellsToCheck:
            objs.extend(c.children)
    
    lastSpeed = 0        
    for ob in objs:
        if ob in scene.objects:
            obj = scene.objects[ob]
            dist, speed, depth =  distSpeed(owner, obj, maxHierarchyDepth, lastSpeed)
            if speed > 0:
                lastSpeed = speed
            
            strength = 0 #handle bomb here
            if "strength" in owner.getPropertyNames():
                strength = owner["strength"]
                depth = maxHierarchyDepth #blow all apart
            
            if dist < speed or dist < strength:  
                dissolve(obj, depth, maxHierarchyDepth, owner)
            #if isDeformable(obj):
            #    obj.cutSoftbodyLink(owner.worldPosition, dist)
            #    child.setSoftbodyPose(True, True)

#def destroyCellDelayed(cell, cells):
#    #break connection then destroy cell after a delay
#    for item in cells.items():
#        if cell == item[1] and item[0] in cells:
#            del cells[item[0]]
#            break
#    
#    childs = [c for c in cell.children]
#    for child in cell.children:
#      #  print("cell child: ", o)
#        if child in scene.objects:
#           # o = scene.objects[child]
#           # o.restoreDynamics()
#        #    o.removeParent()
#            childs.remove(child)
#         #   o["activated"] = True
#        else:
#            childs.remove(child) #remove invalid child
#                    
#    cell.children = childs 
#    #timer...
    

                         

def checkGravityCollapse():
    #check for gravity collapse (with ground connectivity)
    global firstparent
    
    if not bpy.context.scene.useGravityCollapse:
        return 
    
    for first in firstparent:
        if isGroundConnectivity(first):
            if first.name in dd.DataStore.grids.keys():
                grid = dd.DataStore.grids[first.name]
                if grid.dim[2] > 1:
                    intPerLayer = 0.5 / (grid.cellCounts[2] - 1)
                    for layer in range(0, grid.cellCounts[2]):
                        if not grid.layerIntegrity(layer, 0.75 - layer * intPerLayer):
                            #print("layer integrity low, destroying layer", layer)
                            cells = dict(grid.cells)
                            
                            #tilt building ?
                            #g = scene.objects["Ground"]
                            #g.worldOrientation = Matrix.Rotation(math.radians(15), 3, 'X')
                            [destroyCell(c, cells, None) for c in grid.cells.values() if grid.inLayer(c, layer)]
                            
                            for c in cells.values():
                                destroyNeighborhood(c)
                 
                            for c in cells.values():
                                c.visit = False
                                
                            #apply horizontal impulse according to cell distribution to make
                            #object rotate...
                            #g.worldOrientation = Matrix.Rotation(math.radians(0), 3, 'X')
                            break    
 
def findCompound(childs):
    compound = None
    for c in childs:
        if bpy.context.scene.objects[c.name].game.use_collision_compound and \
        not c.name in bpy.context.scene.backups: 
            mesh = bpy.context.scene.objects[c.name].data.name
            print("Adding compound", c.name)
            compound = scene.addObject(c.name, c.name)
            compound.replaceMesh(mesh, True, True)    
            return compound
    if compound == None:
        for c in childs:
            compound = bpy.context.scene.objects[c.name].destruction.backup
            print("Testing: ", compound)
            if compound != None and compound != "" and \
            bpy.context.scene.objects[compound].game.use_collision_compound:
                print("Adding compound(b)", compound)
                if compound not in scene.objects:
                    #mesh = bpy.context.scene.objects[compound].data.name
                    comp = scene.addObject(compound, compound)
                    #comp.replaceMesh(mesh, True, True)
                    return comp
                return scene.objects[compound]
        
        #descend if necessary
#        for c in childs:
#            ch= bpy.context.scene.objects[c.name].destruction.children
#            return findCompound(ch, c.name, True)
                

def findFirstParent(parent):
    #TODO: hack -> find first parent, ground connectivity on subparents is unsupported by now.
    #what about loose parts parents (they have another name mostly) ?
    #maybe store a reference to the firstparent directly.
    temp = parent.split(".")[0]
    pstart = temp.split("_")[3]
    
    for fp in firstparent:
        temp = fp.name.split(".")[0]
        fstart = temp.split("_")[3]
        if fstart == pstart:
            return fp
    return None
                        
                
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
    
    parents = {}  
    
    first = findFirstParent(parent)
          
    childs= bpy.context.scene.objects[parent].destruction.children
    compound = findCompound(childs)
    
    if compound != None:
        #if not isGroundConnectivity(first):   
        parents[compound.name] = parent    
        ret.append(compound)
        par["compound"] = compound.name       
                   
    for c in childs:
        if c.name != compound.name and c.name != obj.name:
            
            if c.name.startswith("P_"):
                
                if c.name in scene.objects:
                    cPar = scene.objects[c.name]
                else:
                    cPar = scene.addObject(c.name, c.name)
                
                name = bpy.context.scene.objects[c.name].destruction.backup
                parents[name] = c.name
                parents[c.name] = parent
                ret.append(cPar)
                if name == compound.name:
                    continue
            else:
                name = c.name
                parents[name] = parent
            
            print("Adding children", name)
            mesh = bpy.context.scene.objects[name].data.name
            o = scene.addObject(name, name)
            o.replaceMesh(mesh, True, True)
            if not isGroundConnectivity(first):
           #     o.worldPosition = obj.worldPosition
                o.setParent(compound, True, False)
            else:
                
                if not o.invalid:
                    o.suspendDynamics()
                    o.setParent(ground, False, False)
                         
            ret.append(o)
    
    if not isGroundConnectivity(first):
        compound.worldPosition = obj.worldPosition        
        compound.worldOrientation = obj.worldOrientation
        compound.linearVelocity = obj.linearVelocity
        compound.angularVelocity = obj.angularVelocity
    else:
        compound.setParent(ground, False, False)
    
    if parent in children.keys():
        if obj.name in children[parent]:
            children[parent].remove(obj.name)
    obj.endObject()
    
   # if objParent in children.keys():
    #    if parent in children[objParent]:
     #       children[objParent].remove(parent)
    #parent.endObject()
    
    for r in ret:
        p = parents[r.name]
        if p not in children.keys():
            children[p] = list()
        children[p].append(r.name)
    
    if isGroundConnectivity(first):
        calculateGrids()
      
    return ret

#def pChildren(parent):
#    childs = bpy.context.scene.objects[parent.name].destruction.children
#    ret = []
#    for c in childs:
#        if c.name in scene.objects:
#            ret.append(scene.objects[c.name])
#        else:
#            ret.append(scene.addObject(c.name, c.name))
#    return ret
   
#recursively destroy parent relationships    
def dissolve(obj, depth, maxdepth, owner):
    #print("dissolve", obj, depth)               
    parent = None
    for p in children.keys():
        if obj.name in children[p]:
            parent = p
            break
        
    par = None
    if parent != None:
        if parent in scene.objects:
            par = scene.objects[parent]
        else:
            par = scene.addObject(parent, parent)
    else:
        par = ground
       
    
   # print("Owner:", owner, isRegistered(par, owner), isDestroyable(par), parent, par)
     
    if isDestroyable(par) and (isRegistered(par, owner) or isGround(par)):
        
        grid = None
        if par.name in dd.DataStore.grids.keys():
            grid = dd.DataStore.grids[par.name]                
        
        #only activate objects at current depth
        if par != None:# and par.name != "Ground":
            digitEnd = par.name.split("_")[1]
            objDepth = int(digitEnd) 
            
            if obj.name.startswith("P_"):
                backup = bpy.context.scene.objects[obj.name].destruction.backup
                if backup in scene.objects:
                    obj = scene.objects[backup]
                else:
                    return
                
            bDepth = backupDepth(obj)
             
            #print(depth, objDepth+1, bDepth+1)
            first = findFirstParent(par.name)
            if bpy.context.scene.hideLayer != 1 and isBackup(obj) and ((depth == bDepth+1) or \
            ((depth == bDepth) and not isGroundConnectivity(first))):
                print(depth, bDepth, isGroundConnectivity(first))
                if bpy.context.scene.objects[obj.name].game.use_collision_compound:
                   for ch in obj.children:
                        ch.removeParent()
                        if isBackup(ch):
                            swapBackup(ch)
                            ch["swapped"] = True
                        else:
                            activate(ch, owner, grid)
                            
                objs = swapBackup(obj)
                obj["swapped"] = True
              #  [activate(ob, owner, grid) for ob in objs]
            
            if (depth == objDepth+1) or (depth == objDepth):
                activate(obj, owner, grid)
            
        if depth < maxdepth and parent != None:
#                pParent = None
#                for p in children.keys():
#                    if parent in children[p]:
#                        pParent = p
#                        break
#              #  print(children[p], parent)
#                if pParent != None:
            [dissolve(scene.objects[c], depth+1, maxdepth, owner) for c in children[parent]]

def activate(child, owner, grid):
    
    # print("activated: ", child)
     global integrity
     global firstShard
     global delay
     
     delay = deadDelay(owner)
     
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
         
     #remove all compound children if it is hit
    # if bpy.context.scene.objects[child.name].game.use_collision_compound:
    #     for ch in child.children:
    #         ch.removeParent()
    #         ch.restoreDynamics()     
                 
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
                    #print("Low Integrity, destroying cell!")
                    destroyCell(cell, cells, None)
                    
                    
                 for c in cells.values():
                    destroyNeighborhood(c)
                 
                 for c in cells.values():
                    c.visit = False
    
     child.restoreDynamics()
     
    
     if delay == 0:              
        child.removeParent()
        child["activated"] = True
        
    #    if isDeformable(child):
    #       child.setSoftbodyPose(True, True)
           
    #       if "joint" in child.getPropertyNames():
    #            child.cutSoftbodyJoint(scene.objects[child["joint"]])
        
        if parent != None:
            if child.name in children[parent]:
                children[parent].remove(child.name)
     else:
        if not child.invalid:
            t = Timer(delay, child.suspendDynamics)
            t.start()

#def isDeformable(obj):
#    if obj == None:
#        return False
#    return bpy.context.scene.objects[obj.name].destruction.deform
            
def isGroundConnectivity(obj):
    global children
    
    if obj == None:
        return False
    if obj.name in children.keys(): #valid parent
        groundConnectivity = bpy.context.scene.objects[obj.name].destruction.groundConnectivity
        return groundConnectivity
    else:
        return False
#    if obj == None or "groundConnectivity" not in obj.getPropertyNames():
#        return False
#    return obj["groundConnectivity"]

def isDestroyable(obj):
    if obj == None:
        return False
    destroyable = bpy.context.scene.objects[obj.name].destruction.destroyable
    return destroyable
#    if destroyable == None or "destroyable" not in destroyable.getPropertyNames():
#        return False
#    return destroyable["destroyable"]

def isDestructor(obj):
    if obj == None:
        return False
    destructor = bpy.context.scene.objects[obj.name].destruction.destructor
    return destructor
#    if obj == None or "destructor" not in obj.getPropertyNames():
#        return False
#    return obj["destructor"]

def isGround(obj):
    
    if obj == None:
        return False
    if obj.name in bpyObjs.keys():
        isground = bpyObjs[obj.name].destruction.isGround
        return isground
    else:
        return False
#    if obj == None or "isGround" not in obj.getPropertyNames():
#        return False
#    return obj["isGround"]

def flattenHierarchy(obj):
    if obj == None:
        return False
    flatten = bpy.context.scene.objects[obj.name].destruction.flatten_hierarchy
 #   print("Flatten: ", obj, flatten)
    return flatten

def hierarchyDepth(obj):
    if obj == None:
        return -1
    depth = bpy.context.scene.objects[obj.name].destruction.hierarchy_depth
    return depth

def deadDelay(obj):
    if obj == None:
        return 0
    delay = bpy.context.scene.objects[obj.name].destruction.dead_delay
    return delay

def isRegistered(destroyable, destructor):
#    if destroyable == None:
#        return False
#    if not destructor["destructor"]:
#        return False
    
   # targets = destructor["destructorTargets"].split(" ")
#    print(targets, destructor)

    if not isDestroyable(destroyable):
        return False
    if not isDestructor(destructor):
        return False
     
    targets = bpy.context.scene.objects[destructor.name].destruction.destructorTargets
    for t in targets:
        if t.name == destroyable.name:
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
        

#def getFloats(str):
#    parts = str.split(" ")
#    return (float(parts[0]), float(parts[1]), float(parts[2]))
#
#def getInts(str):
#    parts = str.split(" ")
#    return (int(parts[0]), int(parts[1]), int(parts[2]))
#
def getGrounds(obj):
    grounds = bpy.context.scene.objects[obj.name].destruction.grounds
    print(grounds)
    ret = []
    for ground in grounds:
        g = dd.Ground()
        g.name = ground.name
        
        bGround = bpy.context.scene.objects[ground.name].bound_box.data.to_mesh(bpy.context.scene, False, 'PREVIEW')
        for e in bGround.edges:
            vStart = bGround.vertices[e.vertices[0]].co
            vEnd = bGround.vertices[e.vertices[1]].co
            g.edges.append((vStart, vEnd))
        ret.append(g)
    print("RET", ret)
    return ret
    
#    if "grounds" not in obj.getPropertyNames():
#        return None
#    grounds = []
#    print(obj["grounds"])
#    parts = obj["grounds"].split(" ")
#    for part in parts:
#        p = part.split(";")
#        if p[0] == "" or p[0] == " ":
#            continue
#        ground = dd.Ground()
#        ground.name = p[0]
#  
#        vert = p[1]
#        verts = vert.split("_")
#        for coords in verts:
#            coord = coords.split(",")
# 
#            vertexStart = (float(coord[0]), float(coord[1]), float(coord[2]))
#            vertexEnd = (float(coord[3]), float(coord[4]), float(coord[5]))
#            edge = (vertexStart, vertexEnd)
#            ground.edges.append(edge)
#        grounds.append(ground)
#    return grounds

def destroyFalling(children):
    print("destroyFalling")
    for c in reversed(children):
        c.restoreDynamics()
        c.removeParent()

def destroyNeighborhood(cell):
    
    global doReturn
    global integrity

    doReturn = False
    destlist = []
    destructionList(cell, destlist)
    
    cells = cell.grid.cells
    
    compound = None
    
    if bpy.context.scene.useGravityCollapse:
        for c in destlist:
            for ch in c.children:
                if bpyObjs[ch].game.use_collision_compound: #find highest compound!
                    compound = scene.objects[ch]
                    compound.removeParent()
                    break
            if compound != None:
                break
        
    children = []
    for c in destlist:
        children.extend(destroyCell(c, cells, compound))
    
    if compound != None:
        compound.restoreDynamics()
        t = Timer(bpy.context.scene.collapse_delay, destroyFalling, args = [children])
        t.start()
    
     
def destroyCell(cell, cells, compound):
    
    global delay
    
    ret = []
    if delay == 0:
        for item in cells.items():
            if cell == item[1] and item[0] in cells:
                del cells[item[0]]
                break
        
   # print("Destroyed: ", cell.gridPos)
    childs = [c for c in cell.children]
    for child in cell.children:
      #  print("cell child: ", o)
        if child in scene.objects:
            o = scene.objects[child]
            
            if compound != None:
               o.setParent(compound, True, False)
               ret.append(o)
               childs.remove(child) 
            else:
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
    return ret      
    

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