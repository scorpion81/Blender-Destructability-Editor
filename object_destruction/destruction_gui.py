from bpy import types, props, utils, ops, data, path
from bpy.types import Object, Scene
from . import destruction_proc as dp
from . import destruction_data as dd
import math
import os
import bpy
from mathutils import Vector
from time import clock

class DestructabilityPanel(types.Panel):
    bl_idname = "OBJECT_PT_destructability"
    bl_label = "Destructability"
    bl_context = "object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    
    def register():
        dp.initialize()

    def unregister():
        dp.uninitialize()
    
    def draw(self, context):        
        
        layout = self.layout
        
        meshChild = False
        for o in context.object.children:
            if o.type == 'MESH':
                meshChild = True
                break;
        isParent = context.object.type == 'EMPTY' and meshChild
        isMesh = context.object.type == 'MESH'
        
        if isParent:
            row = layout.row()
            row.prop(context.object.destruction, "destroyable", text = "Destroyable")
        
        if isMesh:
            row = layout.row()
            row.prop(context.object.destruction, "destructionMode", text = "Mode")

            col = layout.column()
            if context.object.destruction.destructionMode != 'DESTROY_L':
                col.prop(context.object.destruction, "partCount", text = "Parts")
            
            if context.object.destruction.destructionMode == 'DESTROY_F':
                col.prop(context.object.destruction, "roughness", text = "Roughness")
                col.prop(context.object.destruction, "crack_type", text = "Crack Type")
            elif context.object.destruction.destructionMode.startswith('DESTROY_E'):
                col.prop(context.object.destruction, "wallThickness", text = "Thickness")
                col.prop(context.object.destruction, "pieceGranularity", text = "Granularity")
            elif context.object.destruction.destructionMode == 'DESTROY_K':
                col.prop(context.object.destruction, "cut_type", text = "Cut type")
                col.prop(context.object.destruction, "jitter", text = "Jitter")
                col.prop(context.object.destruction, "pieceGranularity", text = "Granularity")
                
                row = col.row()
                row.prop(context.object.destruction, "rot_start", text = "ObjRot Start")
                row.prop(context.object.destruction, "rot_end", text = "ObjRot End")
                
                row = col.row()
                row.prop(context.object.destruction, "line_start", text = "CutLine Start")
                row.prop(context.object.destruction, "line_end", text = "CutLine End")
            elif context.object.destruction.destructionMode == 'DESTROY_V' or \
            context.object.destruction.destructionMode == 'DESTROY_VB':
                row = col.row()
                row.prop_search(context.object.destruction, "voro_volume", 
                        context.scene, "objects", icon = 'OBJECT_DATA', text = "Volume:")
                row.prop(context.object.destruction, "voro_exact_shape", text = "Use Exact Shape")
                if context.object.destruction.voro_volume != "":
                    vol = context.object.destruction.voro_volume 
                    row = col.row()            
                    row.prop_search(context.object.destruction, "voro_particles",
                        data.objects[vol],  "particle_systems", icon = 'PARTICLES', text = "Particle System")
                row = col.row()
                row.prop(context.object.destruction, "voro_path", text="Intermediate File")
                if context.object.destruction.destructionMode == 'DESTROY_VB':
                    row = col.row()
                    row.prop(context.object.destruction, "remesh_depth", text="Remesh Depth")
            if context.object.destruction.destructionMode != 'DESTROY_L':        
                row = layout.row()
                row.prop(context.object.destruction, "cubify", text = "Intersect with Grid")
            
            if context.object.destruction.destructionMode != 'DESTROY_L':
                row = layout.row()
                col = row.column()
                col.prop(context.object.destruction, "cubifyDim", text = "Intersection Grid")
        
        if isMesh or isParent:
            row = layout.row()
            row.prop(context.active_object.destruction, "transmitMode",  text = "Apply To")
        
        row = layout.row()
        names = []
        for o in data.objects:
            if o.destruction != None:
                if o.destruction.is_backup_for != None:
                    names.append(o.destruction.is_backup_for)
        if context.object.name in names and isParent:
            row.operator("object.undestroy")
        elif isMesh:
            if context.object.destruction.destructionMode != 'DESTROY_L':
                row.prop_search(context.object.destruction, "inner_material", data, 
                        "materials", icon = 'MATERIAL', text = "Inner Material:")
                row = layout.row()
                row.prop(context.object.destruction, "flatten_hierarchy", text = "Flatten Hierarchy")
                
            row = layout.row()
            row.prop(context.scene, "hideLayer", text = "Hierarchy Layer")
            row = layout.row()
            row.operator("object.destroy")
        
        layout.separator()
       
        if isMesh or isParent:
            layout.prop(context.object.destruction, "isGround", text = "Is Connectivity Ground")
        
        if isParent:
            layout.prop(context.object.destruction, "groundConnectivity", text = "Calculate Ground Connectivity")
        
            row = layout.row()
            row.label(text = "Connected Grounds")
            row.active = context.object.destruction.groundConnectivity
        
            row = layout.row()       
            row.template_list(context.object.destruction, "grounds", 
                          context.object.destruction, "active_ground", rows = 2)
            row.operator("ground.remove", icon = 'ZOOMOUT', text = "")
            row.active = context.object.destruction.groundConnectivity
        
            row = layout.row()   
            row.prop_search(context.object.destruction, "groundSelector", 
                        context.scene, "objects", icon = 'OBJECT_DATA', text = "Ground:")
                        
            row.operator("ground.add", icon = 'ZOOMIN', text = "")
            row.active = context.object.destruction.groundConnectivity
        
            row = layout.row()
            col = row.column()
            col.prop(context.object.destruction, "gridDim", text = "Connectivity Grid")
            col.active = context.object.destruction.groundConnectivity
       
        layout.separator()
        if isMesh or isParent: #if destroyables were able to be dynamic....
            layout.prop(context.object.destruction, "destructor", text = "Destructor")
        
            row = layout.row()
            row.prop(context.object.destruction, "hierarchy_depth", text = "Hierarchy Depth")
            row.active = context.object.destruction.destructor
            
            row = layout.row()
            row.prop(context.object.destruction, "dead_delay", text = "Object Death Delay")
            row.active = context.object.destruction.destructor
        
            row = layout.row()
            row.label(text = "Destructor Targets")
            row.active = context.object.destruction.destructor
        
            row = layout.row()
        
            row.template_list(context.object.destruction, "destructorTargets", 
                          context.object.destruction, "active_target" , rows = 2) 
                        
            row.operator("target.remove", icon = 'ZOOMOUT', text = "") 
            row.active = context.object.destruction.destructor  
        
            row = layout.row()
            
            row.prop_search(context.object.destruction, "targetSelector", context.scene, 
                       "objects", icon = 'OBJECT_DATA', text = "Destroyable:")
                                    
            row.operator("target.add", icon = 'ZOOMIN', text = "")
            row.active = context.object.destruction.destructor 
        
        row = layout.row()
        row.prop_search(context.object.destruction, "custom_ball", context.scene, 
                    "objects", icon = 'OBJECT_DATA', text = "Custom Ball:")
        
        row = layout.row()
        col = row.column() 
    
        col.operator("player.setup")
        col.active = not context.scene.player
    
        col = row.column()
        col.operator("player.clear")
        col.active = context.scene.player
    
        row = layout.row()
    
        txt = "To Game Parenting"
   
        row.operator("parenting.convert", text = txt)
        row.active = not context.scene.converted
        row = layout.row()
        row.operator("game.start")
        
class AddGroundOperator(types.Operator):
    bl_idname = "ground.add"
    bl_label = "add ground"
    bl_description = "Add the selected ground to ground list"
    
    def execute(self, context):
        found = False
        for prop in context.object.destruction.grounds:
            if prop.name == context.object.destruction.groundSelector:
                found = True
                break
        if not found:
            name = context.object.destruction.groundSelector
            if name == None or name == "":
                self.report({'ERROR_INVALID_INPUT'}, "Please select an object first")
                return {'CANCELLED'}  
             
            obj = context.scene.objects[name]
            context.object.destruction.groundSelector = ""
            
            if obj != context.object and obj.type == 'MESH' and obj.destruction.isGround:
                propNew = context.object.destruction.grounds.add()
                propNew.name = name
            else:
                self.report({'ERROR_INVALID_INPUT'}, "Object must be a mesh object tagged as ground object")
                return {'CANCELLED'}  
                
        return {'FINISHED'}   
    
class RemoveGroundOperator(types.Operator):
    bl_idname = "ground.remove"
    bl_label = "remove ground"
    bl_description = "Remove the selected ground from ground list"
    
    def execute(self, context):
        
        if len(context.object.destruction.grounds) == 0:
            return {'CANCELLED'}
        
        index = context.object.destruction.active_ground
        name = context.object.destruction.grounds[index].name 
        context.object.destruction.grounds.remove(index)
        context.object.destruction.active_ground = len(context.object.destruction.grounds) - 1
        
        if name not in context.scene.validGrounds:
            propNew = context.scene.validGrounds.add()
            propNew.name = name
        
        return {'FINISHED'}
       
        
class AddTargetOperator(types.Operator):
    bl_idname = "target.add"
    bl_label = "add target"
    bl_description = "Add the selected target to target list"
    
    def execute(self, context):
        found = False
        for prop in context.object.destruction.destructorTargets:
            if prop.name == context.object.destruction.targetSelector:
                found = True
                break
        if not found:
            name = context.object.destruction.targetSelector
            if name == None or name == "":
                self.report({'ERROR_INVALID_INPUT'}, "Please select an object first")
                return {'CANCELLED'}  
                 
            obj = context.scene.objects[name]
            context.object.destruction.targetSelector = ""
            
            if obj != context.object and obj.type == 'EMPTY' and \
            len(obj.children) > 0 and obj.destruction.destroyable:
                propNew = context.object.destruction.destructorTargets.add()
                propNew.name = name
            else:
                self.report({'ERROR_INVALID_INPUT'}, "Object must be another destroyable empty with children")
                return {'CANCELLED'}  
            
        return {'FINISHED'}   
    
class RemoveTargetOperator(types.Operator):
    bl_idname = "target.remove"
    bl_label = "remove target"
    bl_description = "Remove the selected target from target list"
    
    def execute(self, context):
        
        if len(context.object.destruction.destructorTargets) == 0:
            return {'CANCELLED'}
        
        index = context.object.destruction.active_target
        name = context.object.destruction.destructorTargets[index].name 
        context.object.destruction.destructorTargets.remove(index)
        context.object.destruction.active_target = len(context.object.destruction.destructorTargets) - 1
            
        return {'FINISHED'} 
    
class SetupPlayer(types.Operator):
    bl_idname = "player.setup"
    bl_label = "Setup Player"
    bl_description = "Create Player, default Ground and default Ball (or custom ball) object"
    
    def execute(self, context):
        
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        
        if context.scene.player:
             return {'CANCELLED'}
        
        context.scene.player = True
       
        
        ops.object.add()
        context.active_object.name = "Player"
       
        ops.object.add(type = 'CAMERA')
        context.active_object.name = "Eye"
         
        ops.object.add(type = 'EMPTY')
        context.active_object.name = "Launcher"
        ops.transform.translate(value = (0.5, 0.8, -0.8))
      
        data.objects["Eye"].parent = data.objects["Player"]
        data.objects["Launcher"].parent = data.objects["Eye"]
        
        data.objects["Player"].select = False
        data.objects["Eye"].select = True
        data.objects["Launcher"].select = False
        ops.transform.rotate(value = [math.radians(90)], 
                             constraint_axis = [True, False, False])
                             
        data.objects["Player"].select = True
        data.objects["Eye"].select = False
        data.objects["Launcher"].select = False
        ops.transform.rotate(value = [math.radians(90)], 
                             constraint_axis = [False, False, True])                     
        
        data.objects["Eye"].select = False
        data.objects["Player"].select = True
        ops.transform.translate(value = (3, 0, 3))
       
        ballname = context.object.destruction.custom_ball
        if ballname == None or ballname == "":
            ops.mesh.primitive_ico_sphere_add(layers = [False, True, False, False, False,
                                                        False, False, False, False, False,
                                                        False, False, False, False, False,
                                                        False, False, False, False, False])
            context.active_object.name = "Ball"
            ball = context.active_object 
            ball.game.physics_type = 'RIGID_BODY'
            ball.game.collision_bounds_type = 'SPHERE'
            ball.game.mass = 100.0
              
        else:
            ball = context.scene.objects[ballname] 
            if ball.type == 'MESH':
                context.scene.objects.active = ball
                context.active_object.game.physics_type = 'RIGID_BODY'
                context.active_object.game.collision_bounds_type = 'SPHERE' #what about non-spheres ?
                context.active_object.game.mass = 100.0
            elif ball.type == 'EMPTY' and len(ball.children) > 0 and ball.name != "Player" and \
            ball.name != "Launcher":
                for c in ball.children: 
                    context.scene.objects.active = c
                    context.active_object.game.physics_type = 'RIGID_BODY'
                    context.active_object.game.collision_bounds_type = 'CONVEX_HULL'
                    context.active_object.game.mass = 100.0
                last = ball.children[-1]
                last.game.use_collision_compound = True
            else:
                self.report({'ERROR_INVALID_INPUT'}, "The ball must be a mesh or a destroyable parent")
                return {'CANCELLED'}                                         
        
        #load bge scripts
        print(__file__)
        currentDir = path.abspath(os.path.split(__file__)[0])
        
        print(ops.text.open(filepath = currentDir + "\destruction_bge.py", internal = False))
        print(ops.text.open(filepath = currentDir + "\player.py", internal = False))
        print(ops.text.open(filepath = currentDir + "\destruction_data.py", internal = False))
        
        #setup logic bricks -player
        context.scene.objects.active = data.objects["Player"]
              
        #mouse aim and destruction setup
        ops.logic.controller_add(type = 'LOGIC_AND', object = "Player")
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        
        context.active_object.game.controllers[1].mode = 'MODULE'
        context.active_object.game.controllers[1].module = "player.aim"
        
        context.active_object.game.controllers[2].mode = 'MODULE'
        context.active_object.game.controllers[2].module = "destruction_bge.setup"
        
        ops.logic.sensor_add(type = 'ALWAYS', object = "Player")
        ops.logic.sensor_add(type = 'MOUSE', object = "Player")
        context.active_object.game.sensors[1].mouse_event = 'MOVEMENT'
        
        ops.logic.actuator_add(type = 'SCENE', object = "Player")
        context.active_object.game.actuators[0].mode = 'CAMERA'
        context.active_object.game.actuators[0].camera = data.objects["Eye"]
        
        
        context.active_object.game.controllers[0].link(
            context.active_object.game.sensors[0],
            context.active_object.game.actuators[0])
        
        context.active_object.game.controllers[1].link(
            context.active_object.game.sensors[1])
        
        context.active_object.game.controllers[2].link(
            context.active_object.game.sensors[0]) 
                     
        #keyboard movement -> 6 directions, WSADYX as keys
        
        motionkeys = [ 'W', 'S', 'A',  'D' , 'Y', 'X' ]
        offsets  =  [[0.0, 0.1, 0.0],[0.0, -0.1, 0.0], [-0.1, 0.0, 0.0],
                     [0.1, 0.0, 0.0],[0.0, 0.0, -0.1], [0.0, 0.0, 0.1] ] 
        
        for i in range(0, 6):
            ops.logic.controller_add(type = 'LOGIC_AND', object = "Player")
            ops.logic.sensor_add(type = 'KEYBOARD', object = "Player")
            ops.logic.actuator_add(type = 'MOTION', object = "Player")
            
            context.active_object.game.sensors[i+2].key = motionkeys[i]
            context.active_object.game.actuators[i+1].offset_location = offsets[i]
            
            context.active_object.game.controllers[i+3].link(
            context.active_object.game.sensors[i+2],
            context.active_object.game.actuators[i+1])
        
        #make screenshots
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        context.active_object.game.controllers[9].mode = 'MODULE'
        context.active_object.game.controllers[9].module = "player.screenshot" 
        
        ops.logic.sensor_add(type = 'KEYBOARD', object = "Player")
        context.active_object.game.sensors[8].key = 'C'
        
        context.active_object.game.controllers[9].link(
            context.active_object.game.sensors[8])
        
              
            
        #launcher
        context.scene.objects.active = data.objects["Launcher"]
        ops.logic.controller_add(type = 'PYTHON', object = "Launcher")
        
        context.active_object.game.controllers[0].mode = 'MODULE'
        context.active_object.game.controllers[0].module = "player.shoot"
        
        ops.logic.sensor_add(type = 'MOUSE', object = "Launcher")
        context.active_object.game.sensors[0].mouse_event = 'LEFTCLICK'
        
        context.active_object.game.controllers[0].link(
                context.active_object.game.sensors[0])
        
        launcher = context.active_object
        i = 0
        if len(ball.children) > 0:
            childs = [c for c in ball.children]
            context.scene.layers = [True, True, False, False, False,
                                    False, False, False, False, False,
                                    False, False, False, False, False,
                                    False, False, False, False, False]
            for b in childs:
                b.select = True
                context.scene.objects.active = b
                ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
                ops.object.transform_apply(location = True, scale = True, rotation = True)
               
                ops.object.game_property_new()
                b.game.properties[0].name = "myParent"
                b.game.properties[0].type = 'STRING'
                b.game.properties[0].value = ball.name
                
                b.select = False
                
                context.scene.objects.active = launcher
                ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Shoot", object = "Launcher")
                context.active_object.game.actuators[i].mode = 'ADDOBJECT'
                context.active_object.game.actuators[i].object = b
                
                context.active_object.game.controllers[0].link(
                    actuator = context.active_object.game.actuators[i])
                
                i += 1
            context.scene.layers = [True, False, False, False, False,
                                    False, False, False, False, False,
                                    False, False, False, False, False,
                                    False, False, False, False, False]
            
        ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Shoot", object = "Launcher")
        context.active_object.game.actuators[i].mode = 'ADDOBJECT'
        context.active_object.game.actuators[i].object = ball
            
        context.active_object.game.controllers[0].link(
                actuator = context.active_object.game.actuators[i])
        
        #ball
        context.scene.objects.active = ball
        context.active_object.destruction.destructor = True
        
        for o in context.scene.objects:
            if o.destruction.destroyable:
                target = context.active_object.destruction.destructorTargets.add()
                target.name = o.name
                     
        context.scene.objects.active = context.object
        #ground and cells
        context.object.destruction.groundConnectivity = True
        
        ops.mesh.primitive_plane_add(location = (0, 0, -0.9))
        context.active_object.name = "Ground"
        context.active_object.destruction.isGround = True
        
        g = context.object.destruction.grounds.add()
        g.name = "Ground"
        
        context.scene.objects.active = context.object
        
        context.user_preferences.edit.use_global_undo = undo
        return {'FINISHED'}
    
class ClearPlayer(types.Operator):
    bl_idname = "player.clear"
    bl_label = "Clear Player"
    bl_description = "Delete Player, default Ground and default Ball objects"
    
    def execute(self, context):
        
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        
        
        if not context.scene.player:
            return {'CANCELLED'}
        context.scene.player = False
        
        for o in data.objects:
            o.select = False
        
        context.scene.layers = [True, True, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False]
        data.objects["Player"].select = True
        data.objects["Eye"].select = True
        data.objects["Launcher"].select = True
        
        ballname = context.object.destruction.custom_ball
        if ballname != None and ballname != "":
            data.objects[ballname].select = True
            for o in data.objects:
                if "myParent" in o.game.properties:
                    #it is always the first by now
                    if ballname == o.game.properties[0].value:
                        o.select = True
        else:
            ballname = "Ball"
            data.objects["Ball"].select = True
        data.objects["Ground"].select = True
        
        for o in data.objects:
            if "Ground" in o.destruction.grounds:
                index = 0
                for g in o.destruction.grounds:
                    if g.name == "Ground":
                        found = True
                        break
                    index += 1
                if found:
                    o.destruction.grounds.remove(index)
            if ballname in o.destruction.destructorTargets:
                index = 0
                for b in o.destruction.destructorTargets:
                    if b.name == ballname:
                        found = True
                        break
                    index += 1
                if found:
                    o.destruction.destructorTargets.remove(index)
     
        ops.object.delete()
        
        context.scene.layers = [True, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False]
        
        data.texts.remove(data.texts["destruction_data.py"])                        
        data.texts.remove(data.texts["destruction_bge.py"])
        data.texts.remove(data.texts["player.py"])                        
        
        context.user_preferences.edit.use_global_undo = undo
        return {'FINISHED'}
    
        
class ConvertParenting(types.Operator):
    bl_idname = "parenting.convert"
    bl_label = "Convert Parenting"
    bl_description = "Dissolve actual parenting, it will be stored and rebuilt in the game engine"
    
    def execute(self, context):
        
        
        if not context.scene.converted:
            undo = context.user_preferences.edit.use_global_undo
            context.user_preferences.edit.use_global_undo = False
            self.convert(context)
            context.scene.converted = True
            context.user_preferences.edit.use_global_undo = undo
        else:
            self.report({'INFO'}, "Hit Undo Key to undo conversion")
            return {'CANCELLED'}
            #context.scene.objects.active = context.object
            #self.unconvert(context)
      #  context.scene.converted = not context.scene.converted
        return {'FINISHED'}
        
    
    def convert(self, context):
        
        
        #temporarily parent all grounds to the parent object
        #rotate back, unparent with keep transform
        parent = None
        groundNames = None
        oldRot = None
        grounds = []
        
        #copy ground/destructor settings over to children
        for o in context.scene.objects:
            if o.name.startswith("P_"):
                for c in o.children: 
                    c.destruction.flatten_hierarchy = o.destruction.flatten_hierarchy 
                    c.destruction.isGround = o.destruction.isGround
                    c.destruction.destructor = o.destruction.destructor
                    for p in o.destruction.destructorTargets:
                        prop = c.destruction.destructorTargets.add()
                        prop.name = p.name
      
        for o in context.scene.objects:
            
            if o.destruction.destructor and o.destruction.isGround:
                o.select = True
                print("Applying Destr Transform", o)
                ops.object.transform_apply(location = True, scale = True, rotation = True)
                o.select = False
           
            if o.name.startswith("P_0"):
                
                parent = o
                groundNames = self.grounds(context, o, True)
                gNames = groundNames.split(" ")
                grounds = [g for g in gNames if g != ""]
                for g in grounds:
                    if g != "":
                        ground = context.scene.objects[g]
                        
                        ground.select = True
                        ctx = context.copy()
                        ctx["object"] = parent
                        ops.object.parent_set(ctx)
                        ground.select = False
               
                #clear rotation and drag ground with me
                oldRot = tuple(parent.rotation_euler)    
                parent.rotation_euler = (0, 0, 0)  
                
                for g in grounds:
                    ground = context.scene.objects[g]
                    
                    ground.select = True
                    ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
                    ops.object.transform_apply(rotation = True)
                    
                    #apply scale and location also, AFTER rotation
                    ops.object.transform_apply(scale = True, location = True)
                     
                    ground.select = False
                break
            
        
        for o in context.scene.objects:    
            #poll speed of ANY destroyable object's child
            if o.parent != None:
                if o.parent.name.startswith("P_") and o.parent.name != "Player":             #regexp PNumber !!
                    context.scene.objects.active = o
                    
                    controllers = len(context.active_object.game.controllers)
                    sensors = len(context.active_object.game.sensors)
                    
                    ops.logic.controller_add(type = 'PYTHON', object = o.name)
                    ops.logic.sensor_add(type = 'ALWAYS', object = o.name)
                    context.active_object.game.sensors[sensors].name = "Always"
            
            
                    context.active_object.game.controllers[controllers].mode = 'MODULE'
                    context.active_object.game.controllers[controllers].module = "destruction_bge.checkSpeed"
            
                    context.active_object.game.controllers[controllers].link(
                    context.active_object.game.sensors[sensors])    
        
        dp.updateIsGround(context)
        dp.updateDestructor(context)          
        for o in context.scene.objects: #data.objects
            
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher":#  or o.name == "Ground":
                       continue
          #  index = -1  # currently LAST Property must be used len(props) - 1
            index = len(o.game.properties) - 1
            context.scene.objects.active = o
   
            if o.parent != None:
                index += 1
                ops.object.game_property_new()
                o.game.properties[index].name = "myParent"
                o.game.properties[index].type = 'STRING'
                o.game.properties[index].value = o.parent.name
                
            ops.object.game_property_new()
            o.game.properties[index + 1].name = "destroyable"
            o.game.properties[index + 1].type = 'BOOL'
            o.game.properties[index + 1].value = o.destruction.destroyable
            
            ops.object.game_property_new()
            o.game.properties[index + 2].name = "isGround"
            o.game.properties[index + 2].type = 'BOOL'
            o.game.properties[index + 2].value = o.destruction.isGround
            
            ops.object.game_property_new()
            o.game.properties[index + 3].name = "groundConnectivity"
            o.game.properties[index + 3].type = 'BOOL'
            o.game.properties[index + 3].value = o.destruction.groundConnectivity
            
            ops.object.game_property_new()
            o.game.properties[index + 4].name = "grounds"
            o.game.properties[index + 4].type = 'STRING'
            o.game.properties[index + 4].value = self.grounds(context, o)
            
            ops.object.game_property_new()
            o.game.properties[index + 5].name = "destructor"
            o.game.properties[index + 5].type = 'BOOL'
            o.game.properties[index + 5].value = o.destruction.destructor
            
            ops.object.game_property_new()
            o.game.properties[index + 6].name = "destructorTargets"
            o.game.properties[index + 6].type = 'STRING'
            o.game.properties[index + 6].value = self.targets(o)

            
            bbox = o.destruction.gridBBox
            dim  = o.destruction.gridDim

            ops.object.game_property_new()
            o.game.properties[index + 7].name = "gridbbox"
            o.game.properties[index + 7].type = 'STRING'
            o.game.properties[index + 7].value = str(round(bbox[0], 2)) + " " + \
                                                 str(round(bbox[1], 2)) + " " + \
                                                 str(round(bbox[2], 2)) 
            
            ops.object.game_property_new()
            o.game.properties[index + 8].name = "griddim"
            o.game.properties[index + 8].type = 'STRING'
            o.game.properties[index + 8].value = str(dim[0]) + " " + str(dim[1]) + " " + str(dim[2])
            
            ops.object.game_property_new()
            o.game.properties[index + 9].name = "hierarchy_depth"
            o.game.properties[index + 9].type = 'INT'
            o.game.properties[index + 9].value = o.destruction.hierarchy_depth
            
            ops.object.game_property_new()
            o.game.properties[index + 10].name = "dead_delay"
            o.game.properties[index + 10].type = 'FLOAT'
            o.game.properties[index + 10].value = o.destruction.dead_delay
            
            if o.parent != None:
                ops.object.game_property_new()
                o.game.properties[index + 11].name = "flatten_hierarchy"
                o.game.properties[index + 11].type = 'BOOL'
                o.game.properties[index + 11].value = o.parent.destruction.flatten_hierarchy
                
          
        #parent again , rotate to rotation, clear parent with keeptransform    
        for g in grounds:
            ground = context.scene.objects[g]
            
            
            ground.select = True
            ctx = context.copy()
            ctx["object"] = parent
            ops.object.parent_set(ctx)
            ground.select = False
       
        #restore rotation
        if parent != None:
            parent.rotation_euler = oldRot  
        
        for g in grounds:
            ground = context.scene.objects[g]
            
            ground.select = True
            ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
            ops.object.transform_apply(rotation = True)
            ground.select = False
        
  
        for o in data.objects: #restrict to P_ parents only ! no use all
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher" or o.name == "Ground":
                    continue
            
            if o.parent != None:
                if o.parent.name.startswith("P_"):    
                    o.select = True
                    context.scene.objects.active = o
                    print("Clearing parent: ", o)
                    o.hide = False
                    propNew = o.parent.destruction.children.add()
                    propNew.name = o.name
                    ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
                    o.select = False
        
        
        #destructors
        for o in context.scene.objects:
            if o.destruction.destructor:
                context.scene.objects.active = o
                
                controllers = len(context.active_object.game.controllers)
                sensors = len(context.active_object.game.sensors)
            
                
                ops.logic.controller_add(type = 'PYTHON', object = o.name)
                ops.logic.sensor_add(type = 'COLLISION', object = o.name)
                context.active_object.game.sensors[sensors].name = "Collision"
            
                context.active_object.game.sensors[sensors].use_pulse_true_level = True
            
                context.active_object.game.controllers[controllers].mode = 'MODULE'
                context.active_object.game.controllers[controllers].module = "destruction_bge.collide"
            
                context.active_object.game.controllers[controllers].link(
                context.active_object.game.sensors[sensors])                   
                       
    def unconvert(self, context):
        
        bpy.ops.ed.undo()
        
#        pos = Vector((0.0, 0.0, 0.0))
#        posFound = False
#        for o in context.scene.objects:
#             if o.name.startswith("P0"):
#                 for obj in data.objects:
#                     if obj.destruction != None:
#                         if obj.destruction.is_backup_for == o.name:
#                            pos = obj.location
#                            posFound = True
#                            break
#             if posFound:
#                 break
#        
#        for o in context.scene.objects:
#            
#            if context.scene.player:
#                if o.name == "Player" or o.name == "Eye" or \
#                   o.name == "Launcher":# or o.name == "Ground":
#                       continue
#            
#            context.scene.objects.active = o
#            
#            index = 0
#            if len(o.game.properties) > 10:
#                if "myParent" in o.game.properties:
#                    props = 11
#                    index = len(o.game.properties) - props
#                    #correct some parenting error -> children at wrong position
#                    par = data.objects[o.game.properties[index].value]
#                    if par.name.startswith("P_0"):
#                        o.location -= pos  
#                    o.parent = par
#                else: 
#                    props = 10
#                    index = len(o.game.properties) - props
#                    
#            while len(o.game.properties) > index:
#                ops.object.game_property_remove()
#            
#            #delete the last ones added
#            if o.parent != None: #here we have an additional always sensor
#                ops.logic.controller_remove(controller = "Python", object = o.name)
#                ops.logic.sensor_remove(sensor = "Always", object = o.name)
#            if o.destruction.destructor:
#                #and here should be the collision sensor
#                ops.logic.controller_remove(controller = "Python1", object = o.name)
#                ops.logic.sensor_remove(sensor = "Collision", object = o.name)
    
    def grounds(self, context, o, namesOnly = False):
       retVal = ""
       for g in o.destruction.grounds:
           if not namesOnly:
               retVal = retVal + g.name + ";" + self.getVerts(context.scene.objects[g.name], context)
           else:
               retVal = retVal + g.name + " " 
       return retVal
   
    def getVerts(self,g, context):
        #use bbox here first, maybe later exact shape -> bad performance!!
        bboxMesh = g.bound_box.data.to_mesh(context.scene, False, 'PREVIEW')
        retVal = ""
        print("GETVERTS:", bboxMesh.edge_keys, g.bound_box.data.dimensions)
        for key in bboxMesh.edge_keys:
            vStart = bboxMesh.vertices[key[0]].co
            vEnd = bboxMesh.vertices[key[1]].co
            dataStr = str(round(vStart[0], 1)) + "," + str(round(vStart[1], 1)) + "," + \
                      str(round(vStart[2], 1)) + "," + str(round(vEnd[0], 1)) + "," + \
                      str(round(vEnd[1], 1)) + "," + str(round(vEnd[2], 1)) + "_"
            retVal = retVal + dataStr
        retVal = retVal.rstrip("_")
        return retVal     
   
    def targets(self, o):
       retVal = ""
       for t in o.destruction.destructorTargets:
           retVal = retVal + t.name + " "
       return retVal
  
class DestroyObject(types.Operator):
    bl_idname = "object.destroy"
    bl_label = "Destroy Object"
    bl_description = "Start fracturing process"
    
    def execute(self, context):
        
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        #set a heavy mass as workaround, until mass update works correctly...
        context.object.game.mass = 1000
        
        if context.object.destruction.destructionMode == 'DESTROY_V' or \
        context.object.destruction.destructionMode == 'DESTROY_VB':
            vol = context.object.destruction.voro_volume
            if vol != None and vol != "":
                obj = context.scene.objects[vol]
                if obj.type != "MESH" or obj == context.object:
                   self.report({'ERROR_INVALID_INPUT'},"Object must be a mesh other than the original object")
                   return {'CANCELLED'}
        
        if context.object.destruction.destructionMode == 'DESTROY_L':        
            if context.object.parent == None or context.object.parent.type != "EMPTY":
                self.report({'ERROR_INVALID_INPUT'},"Object must be parented to an empty before")
                return {'CANCELLED'}
                  
        start = clock()                   
        dd.DataStore.proc.processDestruction(context)
        print("Decomposition Time:" , clock() - start)    
        context.user_preferences.edit.use_global_undo = undo     
        return {'FINISHED'}

class UndestroyObject(types.Operator):
    bl_idname = "object.undestroy"
    bl_label = "Undestroy Object"
    bl_description = "Manually undo object destruction, alternatively use regular undo"
    
    def execute(self, context):
        
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        
        volobj = None
        for o in data.objects:
            if o.destruction != None:
                if o.destruction.is_backup_for == context.object.name:
                    backup = o
                    vol = o.destruction.voro_volume 
                    if vol != "":
                        volobj = context.scene.objects[vol]
                        #print("VOL", volobj.name) 
        
        for o in data.objects:
            if o.destruction != None:
                if o.destruction.is_backup_for == context.object.name:
                    backup = o    
                    if context.scene.hideLayer == 1 and o != volobj:
                       # print("LINK", o.name) 
                        context.scene.objects.link(o)
                    o.select = True
                    ops.object.origin_set(type='ORIGIN_GEOMETRY')
                    o.select = False      
                    o.destruction.is_backup_for == None
                    o.use_fake_user = False
        
        for o in data.objects:
            o.select = False
            
        context.object.select = True
        self.selectShards(context.object, backup)
        ops.object.delete()
        
        context.user_preferences.edit.use_global_undo = undo     
        return {'FINISHED'}
    
    def selectShards(self, object, backup):
                
        for o in bpy.context.scene.objects:
            if o.destruction.destructor and object.name in o.destruction.destructorTargets:
                index = 0
                for ob in o.destruction.destructorTargets:
                    if ob.name == object.name:
                        break
                    index += 1
                o.destruction.destructorTargets.remove(index)
            
        for c in object.children:
            if c != backup: 
                c.select = True
                if c.name in bpy.context.scene.backups:
                    index = 0
                    for n in bpy.context.scene.backups:
                        if n == c.name:
                            break
                        index += 1
                        
                    bpy.context.scene.backups.remove(index)
            self.selectShards(c, backup)

class GameStart(types.Operator):
    bl_idname = "game.start"
    bl_label = "Start Game Engine"
    bl_description = "Start game engine with recording enabled by default"
    
    def execute(self, context):
  
        context.scene.game_settings.use_animation_record = True
        context.scene.game_settings.use_frame_rate = True
        context.scene.game_settings.restrict_animation_updates = True
        context.scene.game_settings.show_framerate_profile = True
        ops.view3d.game_start()
        
        return {'FINISHED'}
            