from bge import logic

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

def setup():
    scene = logic.getCurrentScene()
    for o in scene.objects:
        if "myParent" in o.attrDict:
            o.setParent(o["myParent"])
        o.suspendDynamics()    

def collide():
    
    #colliders have collision sensors attached, which trigger for registered destructibles only
    
    #first the script controller brick, its sensor and owner are needed
    control = logic.getCurrentController()
    sensor = control.sensors["Collision"]
    owner = sensor.owner
    #treat each hit object, check hierarchy
    print(sensor.hitObjectList)
    for parent in sensor.hitObjectList:
        dissolve(parent, 1, hierarchyDepth, owner)
                 
#recursively destroy parent relationships    
def dissolve(parent, depth, maxdepth, owner):
    print("dissolving level: ", depth)
    if isDestroyable(parent) and isRegistered(parent, owner):
        if depth < maxdepth: 
            [dissolve(c, depth + 1, maxdepth, owner) for c in parent.children]
            [activate(c, owner) for c in parent.children]
        activate(parent, owner)

def activate(child, owner):
 #   if child.getDistanceTo(owner.worldPosition) < defaultRadius:
     print("activated: ", child)
     child.removeParent()
     child.restoreDynamics() 
    

def isDestroyable(destroyable):
    return True

def isRegistered(destroyable, destructor):
    return True

   
    
    
    
    #in a radius around collision check whether this are shards of a destructible /or 
    #whether it is a destructible at all if it is activate cell children and reduce integrity of
    #cells if ground connectivity is taken care of
    