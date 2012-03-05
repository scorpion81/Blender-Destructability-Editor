from bge import logic, events
from time import clock
from mathutils import Vector, Matrix
import math
import Rasterizer
import destruction_bge as db

class P:
    pass
   
def aim():
    
    mouse = logic.mouse
    scene = logic.getCurrentScene()
    player = scene.objects["Player"]
    eye = scene.objects["Eye"]
    player.applyRotation((0,0, -(round(mouse.position[0],2) - 0.5)))
    eye.applyRotation((round(mouse.position[1],2)- 0.5, 0, 0), True)
    mouse.position = ((0.5, 0.5))
       

def shoot():

    mouse = logic.mouse
    scene = logic.getCurrentScene()
    launcher = scene.objects["Launcher"]
    for c in launcher.controllers:
        if "Python" in c.name:
            control = c
    act = []
    for a in control.actuators:
        if "Shoot" in a.name:
            act.append(a)
    
    speed = 0
    axis = launcher.worldOrientation * Vector((0, 0, -5))
    if mouse.events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_ACTIVATED:
        P.startclock = clock()
    
    if mouse.events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_RELEASED:
        speed = clock() - P.startclock
        print(speed)
    
        linVelocity = axis * speed * 20 
        print(linVelocity)
    
        balls = []
        for a in act:
            #control.activate(a)
            a.instantAddObject()
            #lastObj = scene.addObject(a.object, a.object)
    
            #here the ball is in the scene, change Parenting....TODO
            lastobj = a.objectLastCreated
           # last.suspendDynamics()
            balls.append(lastobj)
        
        parent = None    
        for b in balls:
            if "myParent" in b.getPropertyNames():
                parent = scene.objects[b["myParent"]]
                b.setParent(parent)
                if parent.name not in db.children.keys():
                    db.children[parent.name] = list()
                db.children[parent.name].append(b)
        
        if parent != None:
            childs = [c for c in parent.children]
            last = parent.children[-1]
            last.removeParent()    
            for c in childs:
                if c != last:
                    c.removeParent()
                    c.setParent(last, True, False)
                    
            last.linearVelocity = linVelocity      
        else:
            balls[0].linearVelocity = linVelocity
                      
    
def screenshot():
    Rasterizer.makeScreenshot("shot#")
        
    
    
    
        
        
    