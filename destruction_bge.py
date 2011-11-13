from bge import logic
import destruction_data as dd

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
def setup():
    
    #doReturn = False
    scene = logic.getCurrentScene()
    for o in scene.objects:
        if "myParent" in o.getPropertyNames():
            o.setParent(o["myParent"], False, False)
            print(o.parent)
        o.suspendDynamics() 
    
    
    for o in scene.objects:
        if isGroundConnectivity(o):
            bbox = getFloats(o["gridbbox"])
            dim = getInts(o["griddim"])
            grid = dd.Grid(dim, o.worldPosition, bbox, o.children)
            grid.buildNeighborhood()
            dd.DataStore.grids[o.name] = grid    
        
    print("Grids: ", dd.DataStore.grids)   

def collide():
    
    #colliders have collision sensors attached, which trigger for registered destructibles only
    
    #first the script controller brick, its sensor and owner are needed
    control = logic.getCurrentController()
    sensor = control.sensors["Collision"]
    owner = sensor.owner
    #treat each hit object, check hierarchy
    print(sensor.hitObjectList)
    for obj in sensor.hitObjectList:
        dissolve(obj, 1, hierarchyDepth, owner)
                 
#recursively destroy parent relationships    
def dissolve(obj, depth, maxdepth, owner):
    print("dissolving level: ", depth)
    print("isDestroyable / isRegistered: ", isDestroyable(obj.parent), isRegistered(obj.parent, owner))
    if isDestroyable(obj.parent) and isRegistered(obj.parent, owner):
        
        grid = None
        if obj.parent.name in dd.DataStore.grids.keys():
            grid = dd.DataStore.grids[obj.parent.name]
                 
        if isGroundConnectivity(obj.parent) and not isGround(obj.parent):
            if grid != None:
                cells = [c for c in grid.cells.values()]
                if len(cells) > 0:
                    destroyNeighborhood(cells[0])
                    return
                
        if depth < maxdepth: 
            [dissolve(c, depth + 1, maxdepth, owner) for c in obj.parent.children]
            [activate(c, owner) for c in obj.parent.children]
        activate(obj, owner)

def activate(child, owner):
 #   if child.getDistanceTo(owner.worldPosition) < defaultRadius:         
     print("activated: ", child)
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
        

def destroyNeighborhood(cell):
    
    global doReturn
    
    destlist = []
    destructionList(cell, destlist)
    doReturn = False
    
    for cell in destlist:
        if cell.isGroundCell and cell.integrity(0.45):
            return
        
    #destroy unconnected cells -> enable physics within radius -> fuzzy
    print("Destruction List", len(destlist))
    cells = dict(cell.grid.cells)
    for cell in destlist:
        for item in cell.grid.cells.items():
            if cell == item[1] and item[0] in cells:
                del cells[item[0]]
        
        print("Destroyed: ", cell.gridPos)
        childs = [c for c in cell.children]
        for o in cell.children:
            print("cell child: ", o)
            o.removeParent()
            o.restoreDynamics()
            childs.remove(o)
            
        cell.children = childs
            
    cell.grid.cells = cells

def destructionList(cell, destList):
    
    global doReturn  
    
    if doReturn:
        return
    
    if cell.isGroundCell:
        destList.append(cell)
        doReturn = True
        return
    
    for i in range(0,6):
        neighbor = cell.neighbors[i]
        if neighbor != None and not neighbor in destList:
            destList.append(neighbor)
           # if neighbor.integrity(0.45):
            destructionList(neighbor, destList)
    
    #no neighbors found            
    if len(destList) == 0:         
        destList.append(cell)
       
    
    
    #in a radius around collision check whether this are shards of a destructible /or 
    #whether it is a destructible at all if it is activate cell children and reduce integrity of
    #cells if ground connectivity is taken care of
    