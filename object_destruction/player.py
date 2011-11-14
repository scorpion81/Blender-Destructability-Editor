from bge import logic, events
from time import clock
from mathutils import Vector, Matrix
import math
#from bpy import ops, data

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
    control = launcher.controllers["Python"]
    act = control.actuators["Shoot"]
    
    speed = 0
    axis = launcher.worldOrientation * Vector((0, 0, -5))
    if mouse.events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_ACTIVATED:
        P.startclock = clock()
    
    if mouse.events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_RELEASED:
        speed = clock() - P.startclock
        print(speed)
    
        linVelocity = axis * speed * 20 
        print(linVelocity)
    
        act.linearVelocity = linVelocity
        control.activate(act)
    
    
    
    
    
        
        
    