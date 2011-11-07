from bge import logic, events
from time import clock
from mathutils import Vector, Matrix
import math
#from bpy import ops, data

class P:
    pass

#def init():
#     scene = logic.getCurrentScene()
#     player = scene.objects["Player"]
#     mat_rot = Matrix.Rotation(math.radians(45.0), 3, 'X')
#     print (mat_rot)
#     player.worldOrientation = mat_rot
   
def aim():
    
    mouse = logic.mouse
    scene = logic.getCurrentScene()
    player = scene.objects["Player"]
    eye = scene.objects["Eye"]
    player.applyRotation((0,0, -(round(mouse.position[0],2) - 0.5)))
    eye.applyRotation((round(mouse.position[1],2)- 0.5, 0, 0), True)
    
#    bPlayer = data.objects["Player"]
#    bEye = data.objects["Eye"]
#    
#    bPlayer.rotation_euler = player.worldOrientation.to_euler() 
#    bEye.rotation_euler = (eye.orientation.to_euler()[0] , 0, 0)
#        
    mouse.position = ((0.5, 0.5))
    
    #applyRotation to blender scene too
    

def shoot():

    mouse = logic.mouse
    scene = logic.getCurrentScene()
    launcher = scene.objects["Launcher"]
    control = launcher.controllers["Python"]
    act = control.actuators["Shoot"]
    
    speed = 0
    axis = launcher.worldOrientation * Vector((0, -5, 0))
    if mouse.events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_ACTIVATED:
        P.startclock = clock()
    
    if mouse.events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_RELEASED:
        speed = clock() - P.startclock
        print(speed)
    
        linVelocity = axis * speed * 20 
        print(linVelocity)
    
        act.linearVelocity = linVelocity
        control.activate(act)
    
    
    
    
    
        
        
    

