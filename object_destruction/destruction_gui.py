from bpy import types, props, utils, ops, data, path
from bpy.types import Object, Scene
from . import destruction_proc as dp
from . import destruction_data as dd
import math
import os
import bpy
from mathutils import Vector
from time import clock

#import threading
#from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
#from xmlrpc.client import ServerProxy

#from object_destruction.unittest import destruction_bpy_test as test

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
    
    
    def isMesh(self, context):
        return context.object.type == 'MESH'
    
    def isParent(self, context):
        meshChild = False
        for o in context.object.children:
            if o.type == 'MESH':
                meshChild = True
                break;
        return context.object.type == 'EMPTY' and meshChild
    
    def draw_basic_fracture(self, context):
        
        layout = self.layout
         
        if self.isParent(context):
            row = layout.row()
            row.prop(context.object.destruction, "destroyable", text = "Destroyable")
        
        if self.isMesh(context):
            box = layout.box()
            row = box.row()
            row.prop(context.object.destruction, "destructionMode", text = "Mode")

            col = box.column()
            if context.object.destruction.destructionMode != 'DESTROY_L' and \
               context.object.destruction.destructionMode != 'DESTROY_C':
                if not context.object.destruction.voro_exact_shape and context.object.destruction.voro_particles == "":
                    col.prop(context.object.destruction, "partCount", text = "Parts")
            
            
            #gui parts from ideasman42
            if context.object.destruction.destructionMode == 'DESTROY_C':
        
                box = layout.box()
                col = box.column()
                col.label("Point Source")
                #rowsub = col.row()
                col.prop(context.object.destruction.cell_fracture, "source")
                col.prop(context.object.destruction.cell_fracture, "source_limit")
                col.prop(context.object.destruction.cell_fracture, "source_noise")
                rowsub = col.row(align = True)
                rowsub.prop(context.object.destruction.cell_fracture, "cell_scale")                
                
                box = layout.box()
                col = box.column()
                col.label("Mesh Data")
                rowsub = col.row(align=True)
                rowsub.prop(context.object.destruction.cell_fracture, "use_smooth_faces")
                rowsub.prop(context.object.destruction.cell_fracture, "use_sharp_edges")
                rowsub.prop(context.object.destruction.cell_fracture, "use_sharp_edges_apply")
                rowsub.prop(context.object.destruction.cell_fracture, "use_data_match")
                rowsub.prop(context.object.destruction.cell_fracture, "use_interior_vgroup")
                rowsub = col.row(align=True)
                rowsub.prop(context.object.destruction.cell_fracture, "margin")
                rowsub.prop(context.object.destruction.cell_fracture, "use_island_split")
                
                box = layout.box()
                col = box.column()    
                col.label("Object")
                rowsub = col.row(align=True)
                rowsub.prop(context.object.destruction.cell_fracture, "use_recenter")
                
                box = layout.box()
                col = box.column()
                col.label("Scene")
                rowsub = col.row(align=True)
                rowsub.prop(context.object.destruction.cell_fracture, "group_name")
        
                box = layout.box()
                col = box.column()
                col.label("Debug")
                rowsub = col.row(align=True)
                rowsub.prop(context.object.destruction.cell_fracture, "use_debug_points")
                rowsub.prop(context.object.destruction.cell_fracture, "use_debug_bool")
                    
            if context.object.destruction.destructionMode == 'DESTROY_F':
                col.prop(context.object.destruction, "crack_type", text = "Crack Type")
                if context.object.destruction.crack_type == 'FLAT_ROUGH' or \
                context.object.destruction.crack_type == 'SPHERE_ROUGH':
                    col.prop(context.object.destruction, "roughness", text = "Roughness")
                    
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
                if context.object.destruction.voro_particles == "":
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
                row = col.row()
                row.prop(context.object.destruction, "dissolve_angle", text="Limited Dissolve Angle")
            
        
    def draw_advanced_fracture(self, context):
        
        layout = self.layout
        if self.isMesh(context):    
            box = layout.box()   
            
            row = box.row(align=True)
            row.prop(context.object.destruction.cell_fracture, "mass_mode")
            row = box.row(align=True)
            row.prop(context.object.destruction.cell_fracture, "mass")
                    
            if context.object.destruction.destructionMode != 'DESTROY_L':        
                row = box.row()
                row.prop(context.object.destruction, "cubify", text = "Intersect with Grid")
            
            if context.object.destruction.destructionMode != 'DESTROY_L' and \
            context.object.destruction.cubify:
                row = box.row()
                col = row.column()
                col.prop(context.object.destruction, "cubifyDim", text = "Intersection Grid")
        
            if context.object.destruction.destructionMode != 'DESTROY_L':
                row = box.row()
                row.prop_search(context.object.destruction, "inner_material", data, 
                    "materials", icon = 'MATERIAL', text = "Inner Material:")    
            
            if context.object.destruction.destructionMode != 'DESTROY_L' and \
            context.object.destruction.destructionMode != 'DESTROY_V':
                row = box.row()
                row.prop(context.object.destruction, "re_unwrap", text = "Smart Project Shard UVs")
                if context.object.destruction.re_unwrap:
                    row = box.row()
                    row.prop(context.object.destruction, "smart_angle", text = "Angle limit")
            
            row = box.row()
            row.prop(context.object.destruction, "dynamic_mode", expand = True)
            
            if (context.object.destruction.dynamic_mode == "D_PRECALCULATED"):
                
                if self.isMesh(context) or self.isParent(context):
                    row = box.row()
                    row.prop(context.object.destruction, "cluster", text = "Use Clusters")
                    if context.object.destruction.cluster:
                        row = box.row()
                        col = row.column()
                        col.prop(context.object.destruction, "cluster_dist", text = "Cluster Distance in %")
            
                row = box.row()
                row.prop(context.object.destruction, "flatten_hierarchy", text = "Flatten Hierarchy")
            
                if not context.object.destruction.flatten_hierarchy:    
                    row = box.row()
                    row.prop(context.scene, "hideLayer", text = "Hierarchy Layer")
                
                row = box.row()
                row.prop(context.object.destruction, "use_debug_redraw")
                    
            else:
                row = box.row()
                row.prop(context.scene, "dummyPoolSize", text = "Dummy Object Pool Size")
            
            row = box.row()
            row.prop(context.object.destruction, "glue_threshold", text = "Glue Threshold")

    
    def draw_recursion(self, context):
        
        layout = self.layout
        #use recursion for all methods
        if context.object.destruction.destructionMode != 'DESTROY_L' and self.isMesh(context):     
            box = layout.box()
            col = box.column()
            col.label("Recursive Shatter")
            rowsub = col.row(align=True)
            rowsub.prop(context.object.destruction.cell_fracture, "recursion")
            #rowsub.prop(context.object.destruction.cell_fracture, "recursion_source_limit")
            rowsub.prop(context.object.destruction.cell_fracture, "recursion_clamp")
            rowsub = col.row()
            rowsub.prop(context.object.destruction.cell_fracture, "recursion_chance")
            col.prop(context.object.destruction.cell_fracture, "recursion_chance_select", expand=True)
        
    def draw_gameengine_setup(self, context):
        
        layout = self.layout
        layout.separator()
        box = layout.box() 
        row = box.row()
        row.label("Game Engine Settings: ")
        row.scale_x = 1.5
        row.scale_y = 1.5
        
        #does not work correctly
        #if isMesh or isParent:
        #    layout.prop(context.object.destruction, "deform", text = "Enable Deformation")
        
        
       
        if self.isMesh(context) or self.isParent(context):       
            box.prop(context.object.destruction, "isGround", text = "Is Connectivity Ground")
        
        if self.isParent(context):
            box.prop(context.object.destruction, "groundConnectivity", text = "Calculate Ground Connectivity")
            
            if context.object.destruction.groundConnectivity:
                row = box.row()
                row.label(text = "Connected Grounds")
                row.active = context.object.destruction.groundConnectivity
        
                row = box.row()       
                row.template_list(context.object.destruction, "grounds", 
                          context.object.destruction, "active_ground", rows = 2)
                row.operator("ground.remove", icon = 'ZOOMOUT', text = "")
                row.active = context.object.destruction.groundConnectivity
        
                row = box.row()   
                row.prop_search(context.object.destruction, "groundSelector", 
                        context.scene, "objects", icon = 'OBJECT_DATA', text = "Ground:")
                        
                row.operator("ground.add", icon = 'ZOOMIN', text = "")
                row.active = context.object.destruction.groundConnectivity
            
                row = box.row()
                col = row.column()
                col.prop(context.object.destruction, "gridDim", text = "Connectivity Grid")
                #col.active = context.object.destruction.groundConnectivity
                
                row = box.row()
                row.prop(context.scene, "useGravityCollapse", text = "Use Gravity Collapse")
                
                if context.scene.useGravityCollapse:
                    row.prop(context.scene, "collapse_delay", text = "Collapse Delay")
       
        if self.isMesh(context) or self.isParent(context): #if destroyables were able to be dynamic....
            box.prop(context.object.destruction, "destructor", text = "Destructor")
            
            if context.object.destruction.destructor:
                row = box.row()
                row.prop(context.object.destruction, "hierarchy_depth", text = "Hierarchy Depth")
                row.active = context.object.destruction.destructor
                
                row = box.row()
                row.prop(context.object.destruction, "dead_delay", text = "Object Death Delay")
                row.active = context.object.destruction.destructor
                
                row = box.row()
                row.prop(context.object.destruction, "radius", text = "Radius")
                row.active = context.object.destruction.destructor
                
                row = box.row()
                row.prop(context.object.destruction, "modifier", text = "Speed Modifier")
                row.active = context.object.destruction.destructor
                
            
                row = box.row()
                row.label(text = "Destructor Targets")
                row.active = context.object.destruction.destructor
            
                row = box.row()
            
                row.template_list(context.object.destruction, "destructorTargets", 
                              context.object.destruction, "active_target" , rows = 2) 
                            
                row.operator("target.remove", icon = 'ZOOMOUT', text = "") 
                row.active = context.object.destruction.destructor  
            
                row = box.row()
                
                row.prop_search(context.object.destruction, "targetSelector", context.scene, 
                           "objects", icon = 'OBJECT_DATA', text = "Destroyable:")
                                        
                row.operator("target.add", icon = 'ZOOMIN', text = "")
            #row.active = context.object.destruction.destructor 
        
        row = box.row()
        row.prop_search(context.scene, "custom_ball", context.scene, 
                    "objects", icon = 'OBJECT_DATA', text = "Custom Ball:")
        
        row = box.row()
        row.prop(context.scene, "use_player_cam", text = "Use Player Camera")
        
        row = box.row()
        col = row.column() 
    
        col.operator("player.setup")
        col.active = not context.scene.player
    
        col = row.column()
        col.operator("player.clear")
        col.active = context.scene.player
    
        row = box.row()
    
        txt = "To Game Parenting"
   
        row.operator("parenting.convert", text = txt)
        row.active = not context.scene.converted
        row = box.row()
        row.operator("game.start")
        
#        layout.separator()
#        row = layout.row()
#        row.label("Unit Tests: ")
#        row.scale_x = 1.5
#        row.scale_y = 1.5
#        
#        row = layout.row()
#        row.operator("test.run")
#        
#        if context.scene.player:
#            
#            if context.scene.runBGETests:
#                txt = "Disable BGE Tests"
#            else:
#                txt = "Enable BGE Tests"
#                
#            row.operator("bge_test.run", text = txt) 
        
    
    def draw_the_button(self, context):
        
        layout = self.layout
        box = layout.box() 
        row = box.row()
        row.operator("object.destroy")
        
    def draw_the_undo_button(self, context):
        
        layout = self.layout
        names = []
        for o in data.objects:
            if o.destruction != None:
                if o.destruction.is_backup_for != None:
                    names.append(o.destruction.is_backup_for)
        if context.object.name in names:
            box = layout.box()
            row = box.row()
            row.operator("object.undestroy")
                    
    
    def draw(self, context):        
        
        layout = self.layout
        self.draw_basic_fracture(context)
        
        if self.isMesh(context):
            layout.prop(context.object.destruction, "advanced_fracture", text = "Advanced Fracture Options")
            if context.object.destruction.advanced_fracture:
                self.draw_advanced_fracture(context)
        
            layout.prop(context.object.destruction, "auto_recursion", text = "Automatic Recursion Options")
            if context.object.destruction.auto_recursion:
                self.draw_recursion(context)
                
        
        if self.isMesh(context) and context.object.destruction.dynamic_mode == "D_PRECALCULATED":
            self.draw_the_button(context)
        
        if self.isParent(context):
            self.draw_the_undo_button(context)
        
        layout.prop(context.object.destruction, "setup_gameengine", text = "Game Engine Setup Options")
        if context.object.destruction.setup_gameengine:
            self.draw_gameengine_setup(context)
        
        layout.operator("active.to_selected")
        
       # row = layout.row()
        #row.label("Progress")
        #row.label(context.scene.fracture_progress) 
        
               
class AddGroundOperator(types.Operator):
    bl_idname = "ground.add"
    bl_label = "add ground"
    bl_description = "Add the selected ground to ground list"
    bl_options = {'UNDO'}
    
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
    bl_options = {'UNDO'}
    
    def execute(self, context):
        
        if len(context.object.destruction.grounds) == 0:
            return {'CANCELLED'}
        
        index = context.object.destruction.active_ground
        name = context.object.destruction.grounds[index].name 
        context.object.destruction.grounds.remove(index)
        context.object.destruction.active_ground = len(context.object.destruction.grounds) - 1
        
       # if name not in context.scene.validGrounds:
        #    propNew = context.scene.validGrounds.add()
        #    propNew.name = name
        
        return {'FINISHED'}
       
        
class AddTargetOperator(types.Operator):
    bl_idname = "target.add"
    bl_label = "add target"
    bl_description = "Add the selected target to target list"
    bl_options = {'UNDO'}
    
    def isParent(self, obj):
        return obj.type == 'EMPTY' and obj.name.startswith("P_")
    
    def execute(self, context):
        
        #entered name has priority over selected objects
        name = context.object.destruction.targetSelector
        prop =[p.name for p in context.object.destruction.destructorTargets]
        sel = [o.name for o in context.selected_objects if self.isParent(o) and o.name not in prop and o != context.object]
        
        found = False
        for prop in context.object.destruction.destructorTargets:
            if prop.name == name:
                found = True
                break
        if not found:
            #name = context.object.destruction.targetSelector
            if (name == None or name == "") and len(sel) == 0:
                self.report({'ERROR_INVALID_INPUT'}, "Please select an object first")
                return {'CANCELLED'}  
            elif name != "":     
                objs = [context.scene.objects[name]]
            else:
                objs = [o for o in bpy.data.objects if o.name in sel]
                
            context.object.destruction.targetSelector = ""
            
            for obj in objs:
                if obj != context.object and obj.type == 'EMPTY' and \
                obj.name.startswith("P_") and obj.destruction.destroyable:
                    propNew = context.object.destruction.destructorTargets.add()
                    propNew.name = obj.name
                else:
                    self.report({'ERROR_INVALID_INPUT'}, "Object must be another destroyable empty with children")
                    return {'CANCELLED'}  
            
        return {'FINISHED'}   
    
class RemoveTargetOperator(types.Operator):
    bl_idname = "target.remove"
    bl_label = "remove target"
    bl_description = "Remove the selected target from target list"
    bl_options = {'UNDO'}
    
    def isParent(self, obj):
        return obj.type == 'EMPTY' and obj.name.startswith("P_")
    
    def findIndex(self, context, name):
        i = 0
        ret = -1
        for p in context.object.destruction.destructorTargets:
            if p.name == name:
                ret = i 
            i += 1
        
        return ret
            
    def execute(self, context):
        
        if len(context.object.destruction.destructorTargets) == 0:
            return {'CANCELLED'}
        
        prop =[p.name for p in context.object.destruction.destructorTargets]
        sel = [o.name for o in context.selected_objects if self.isParent(o) and o.name in prop]
        
        if len(sel) > 0: 
            for s in sel:
                index = self.findIndex(context, s)
                if index != -1:
                    name = context.object.destruction.destructorTargets[index].name 
                    context.object.destruction.destructorTargets.remove(index)
                    context.object.destruction.active_target = len(context.object.destruction.destructorTargets) - 1
        else:
            index = context.object.destruction.active_target
            name = context.object.destruction.destructorTargets[index].name 
            context.object.destruction.destructorTargets.remove(index)
            context.object.destruction.active_target = len(context.object.destruction.destructorTargets) - 1
            
        return {'FINISHED'} 
    
class SetupPlayer(types.Operator):
    bl_idname = "player.setup"
    bl_label = "Setup Player"
    bl_description = "Create Player, default Ground and default Ball (or custom ball) object"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        
        if context.scene.player:
             return {'CANCELLED'}
        
        context.scene.player = True
        
        #transfer settings to all selected objects if NOT precalculated(done via destroy if precalculated)
        if context.object.destruction.dynamic_mode == "D_DYNAMIC":
            dd.DataStore.proc.copySettings(context, None)
        
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
       
        ballname = context.scene.custom_ball
        if ballname == None or ballname == "":
            ops.mesh.primitive_ico_sphere_add(layers = [False, True, False, False, False,
                                                        False, False, False, False, False,
                                                        False, False, False, False, False,
                                                        False, False, False, False, False])
            context.active_object.name = "Ball"
            ball = context.active_object 
            ball.game.physics_type = 'RIGID_BODY'
            #ball.game.collision_bounds_type = 'SPHERE'
            ball.game.mass = 100.0
              
        else:
            ball = context.scene.objects[ballname] 
            if ball.type == 'MESH':
                context.scene.objects.active = ball
                context.active_object.game.physics_type = 'RIGID_BODY'
                #context.active_object.game.collision_bounds_type = 'SPHERE' #what about non-spheres ?
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
        ops.logic.controller_add(type = 'PYTHON', object = "Player", name = "PythonAim")
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        
        context.active_object.game.controllers[1].mode = 'MODULE'
        context.active_object.game.controllers[1].module = "player.aim"
        
        context.active_object.game.controllers[2].mode = 'MODULE'
        context.active_object.game.controllers[2].module = "destruction_bge.setup"
        
        ops.logic.sensor_add(type = 'ALWAYS', object = "Player")
        ops.logic.sensor_add(type = 'MOUSE', object = "Player")
        context.active_object.game.sensors[1].mouse_event = 'MOVEMENT'
        
        #detonator lock on
        ops.logic.sensor_add(type = 'MOUSE', object = "Player", name = "LockOn")
        context.active_object.game.sensors[2].mouse_event = 'MOUSEOVERANY'
        
        
        ops.logic.actuator_add(type = 'SCENE', object = "Player")
        context.active_object.game.actuators[0].mode = 'CAMERA'
        context.active_object.game.actuators[0].camera = data.objects["Eye"]
        
        if context.scene.use_player_cam:
            context.active_object.game.controllers[0].link(
                context.active_object.game.sensors[0],
                context.active_object.game.actuators[0])
        
        context.active_object.game.controllers[1].link(
            context.active_object.game.sensors[1])
            
        context.active_object.game.controllers[1].link(
            context.active_object.game.sensors[2])
            
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
            
            context.active_object.game.sensors[i+3].key = motionkeys[i]
            context.active_object.game.actuators[i+1].offset_location = offsets[i]
            
            context.active_object.game.controllers[i+3].link(
            context.active_object.game.sensors[i+3],
            context.active_object.game.actuators[i+1])
        
        #make screenshots
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        context.active_object.game.controllers[9].mode = 'MODULE'
        context.active_object.game.controllers[9].module = "player.screenshot" 
        
        ops.logic.sensor_add(type = 'KEYBOARD', object = "Player")
        context.active_object.game.sensors[9].key = 'C'
        
        context.active_object.game.controllers[9].link(
            context.active_object.game.sensors[9])
            
        
        #gravity collapse check timer brick
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        context.active_object.game.controllers[10].mode = 'MODULE'
        context.active_object.game.controllers[10].module = "destruction_bge.checkGravityCollapse"
        
        ops.logic.sensor_add(type = 'ALWAYS', object = "Player")
        context.active_object.game.sensors[10].use_pulse_true_level = True
        context.active_object.game.sensors[10].frequency = 100
        
        context.active_object.game.controllers[10].link(
            context.active_object.game.sensors[10])
        
        
              
            
        #launcher
        context.scene.objects.active = data.objects["Launcher"]
        ops.logic.controller_add(type = 'PYTHON', object = "Launcher", name = "PythonShoot")
        ops.logic.controller_add(type = 'PYTHON', object = "Launcher", name = "PythonDetonate")
        
        context.active_object.game.controllers[0].mode = 'MODULE'
        context.active_object.game.controllers[0].module = "player.shoot"
        
        ops.logic.sensor_add(type = 'MOUSE', object = "Launcher")
        context.active_object.game.sensors[0].mouse_event = 'LEFTCLICK'
        
        context.active_object.game.controllers[0].link(
                context.active_object.game.sensors[0])
                
        context.active_object.game.controllers[1].mode = 'MODULE'
        context.active_object.game.controllers[1].module = "player.detonate"
        
        ops.logic.sensor_add(type = 'MOUSE', object = "Launcher")
        context.active_object.game.sensors[1].mouse_event = 'RIGHTCLICK'
        
        context.active_object.game.controllers[1].link(
                context.active_object.game.sensors[1])
        
        
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
               # ops.object.origin_set(type = 'ORIGIN_GEOMETRY', center = 'BOUNDS')
                ops.object.transform_apply(location = True, scale = True, rotation = True)
                #ops.object.transform_apply(scale = True, rotation = True)
                  
                controllers = len(context.active_object.game.controllers)
                sensors = len(context.active_object.game.sensors)
        
                sensornames = [s.name for s in context.active_object.game.sensors]
                if not "Collision" in sensornames:
                    
                    ops.logic.controller_add(type = 'PYTHON', object = b.name)
                    ops.logic.sensor_add(type = 'COLLISION', object = b.name)
                    context.active_object.game.sensors[sensors].name = "Collision"
        
                    context.active_object.game.sensors[sensors].use_tap = True
                    context.active_object.game.sensors[sensors].use_pulse_true_level = True
                    context.active_object.game.sensors[sensors].frequency = 100
     
                    context.active_object.game.controllers[controllers].mode = 'MODULE'
                    context.active_object.game.controllers[controllers].module = "destruction_bge.collide"
        
                    context.active_object.game.controllers[controllers].link(
                    context.active_object.game.sensors[sensors])
               
                ops.object.game_property_new()
                b.game.properties[0].name = "myParent"
                b.game.properties[0].type = 'STRING'
                b.game.properties[0].value = ball.name
                
                b.select = False
                
                context.scene.objects.active = launcher
                ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Shoot", object = "Launcher")
                context.active_object.game.actuators[i].mode = 'ADDOBJECT'
                context.active_object.game.actuators[i].object = b
                
                ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Detonate", object = "Launcher")
                context.active_object.game.actuators[i+1].mode = 'ADDOBJECT'
                context.active_object.game.actuators[i+1].object = ball
                
                context.active_object.game.controllers[0].link(
                    actuator = context.active_object.game.actuators[i])
                
                context.active_object.game.controllers[1].link(
                    actuator = context.active_object.game.actuators[i+1])
                
                i += 2
            context.scene.layers = [True, False, False, False, False,
                                    False, False, False, False, False,
                                    False, False, False, False, False,
                                    False, False, False, False, False]
            
        ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Shoot", object = "Launcher")
        context.active_object.game.actuators[i].mode = 'ADDOBJECT'
        context.active_object.game.actuators[i].object = ball
        
        ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Detonate", object = "Launcher")
        context.active_object.game.actuators[i+1].mode = 'ADDOBJECT'
        context.active_object.game.actuators[i+1].object = ball
            
        context.active_object.game.controllers[0].link(
                actuator = context.active_object.game.actuators[i])
        
        context.active_object.game.controllers[1].link(
                actuator = context.active_object.game.actuators[i+1])
        
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
    bl_options = {'UNDO'}
    
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
        if "Player" in data.objects:
            data.objects["Player"].select = True
        if "Eye" in data.objects:
            data.objects["Eye"].select = True
        if "Launcher" in data.objects:
            data.objects["Launcher"].select = True
        
        ballname = context.scene.custom_ball
        if ballname != None and ballname != "":
            data.objects[ballname].select = True
            for o in data.objects:
                if "myParent" in o.game.properties:
                    #it is always the first by now
                    if ballname == o.game.properties[0].value:
                        o.select = True
        else:
            ballname = "Ball"
            if "Ball" in data.objects:
                data.objects["Ball"].select = True
        
        if "Ground" in data.objects:
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
    bl_options = {'UNDO'}
    
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
    
    def setDestructor(self, context, o):
    
        context.scene.objects.active = o        
        controllers = len(context.active_object.game.controllers)
        sensors = len(context.active_object.game.sensors)
        
        sensornames = [s.name for s in context.active_object.game.sensors]
        if "Collision" in sensornames:
            return
            
        ops.logic.controller_add(type = 'PYTHON', object = o.name)
        ops.logic.sensor_add(type = 'COLLISION', object = o.name)
        context.active_object.game.sensors[sensors].name = "Collision"
        
        context.active_object.game.sensors[sensors].use_tap = True
        
        if o.name != "Ball":
            context.active_object.game.sensors[sensors].use_pulse_true_level = True
            context.active_object.game.sensors[sensors].frequency = 100
     
        context.active_object.game.controllers[controllers].mode = 'MODULE'
        context.active_object.game.controllers[controllers].module = "destruction_bge.collide"
        
        context.active_object.game.controllers[controllers].link(
        context.active_object.game.sensors[sensors])
        
        for c in o.children:
            self.setDestructor(context, c)
                    
    
    def convert(self, context):
        
        
        #temporarily parent all grounds to the parent object
        #rotate back, unparent with keep transform
        parent = None
        groundNames = None
        oldRot = None
      #  grounds = []
        
        #copy ground/destructor settings over to children
        for o in context.scene.objects:
            if o.name.startswith("P_") and not o.destruction.converted:
                for c in o.children:
                    c.destruction.flatten_hierarchy = o.destruction.flatten_hierarchy 
                    c.destruction.isGround = o.destruction.isGround
                    c.destruction.destructor = o.destruction.destructor
                    for p in o.destruction.destructorTargets:
                        prop = c.destruction.destructorTargets.add()
                        prop.name = p.name
      
        for o in context.scene.objects:
            
            if o.destruction.converted:
                continue
            
            if o.destruction.destructor and o.destruction.isGround:
                o.select = True
                print("Applying Destr Transform", o)
                ops.object.transform_apply(location = True, scale = True, rotation = True)
                o.select = False
           
            if o.name.startswith("P_0"):
                
                parent = o
                groundNames = o.destruction.grounds #self.grounds(context, o, True)
                #gNames = groundNames.split(" ")
                #grounds = [g for g in gNames if g != ""]
                for g in groundNames:
                    if g != "":
                        ground = context.scene.objects[g.name]
                        
                        ground.select = True
                        ctx = context.copy()
                        ctx["object"] = parent
                        ops.object.parent_set(ctx)
                        ground.select = False
               
                #clear rotation and drag ground with me
                oldRot = tuple(parent.rotation_euler)    
                parent.rotation_euler = (0, 0, 0)  
                
                for g in groundNames:
                    if g != "":
                        ground = context.scene.objects[g.name]
                    
                        ground.select = True
                        ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
                        ops.object.transform_apply(rotation = True)
                    
                        #apply scale and location also, AFTER rotation
                        ops.object.transform_apply(scale = True, location = True)
                     
                        ground.select = False
                break
            
        
        #for o in context.scene.objects:    
            #poll speed of ANY destroyable object's child
        #    if o.parent != None:
#                if o.parent.name.startswith("P_") and o.parent.name != "Player":             #regexp PNumber !!
#                    context.scene.objects.active = o
#                    
#                    controllers = len(context.active_object.game.controllers)
#                    sensors = len(context.active_object.game.sensors)
#                    
#                    ops.logic.controller_add(type = 'PYTHON', object = o.name)
#                    ops.logic.sensor_add(type = 'ALWAYS', object = o.name)
#                    context.active_object.game.sensors[sensors].name = "Always"
#                    context.active_object.game.sensors[sensors].use_pulse_true_level = True
#                    context.active_object.game.sensors[sensors].frequency = 100
#            
#            
#                    context.active_object.game.controllers[controllers].mode = 'MODULE'
#                    context.active_object.game.controllers[controllers].module = "destruction_bge.checkSpeed"
#            
#                    context.active_object.game.controllers[controllers].link(
#                    context.active_object.game.sensors[sensors])    
        
#        dp.updateIsGround(context)
        dp.updateDestructor(context)          
        for o in context.scene.objects: #data.objects
            
            if o.destruction.converted:
                continue
            
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
          
        #parent again , rotate to rotation, clear parent with keeptransform    
        #for g in grounds:
            for g in o.destruction.grounds: #names
                if g != "":
                    ground = context.scene.objects[g.name]
            
                    if parent == None:
                        continue
            
            #ground = context.scene.objects[g]
            
                    ground.select = True
                    ctx = context.copy()
                    ctx["object"] = parent
                    ops.object.parent_set(ctx)
                    ground.select = False
       
                #restore rotation
                if parent != None:
                    parent.rotation_euler = oldRot  
        
            for g in o.destruction.grounds: #names
                if g != "":
                    ground = context.scene.objects[g.name]
                
                    if parent == None:
                        continue
                
                    #ground = context.scene.objects[g]
                    print("Rotating back")
                    ground.select = True
                    ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
                    ops.object.transform_apply(rotation = True)
                    ground.select = False
        
        for o in data.objects: #context.scene.objects misses objects on deselected layers
            #destructors
            if o.destruction.destructor:
                self.setDestructor(context, o)
        
        for o in data.objects: #restrict to P_ parents only ! no use all
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher" or o.name == "Ground":
                    continue
            if o.destruction.converted:
                continue
            
            if o.parent != None and o.name in context.scene.objects:
                #if not o.destruction.destructor:
                o.destruction.converted = True
                
                if o.parent.name.startswith("P_"):    
                    o.select = True
                    context.scene.objects.active = o
                    print("Clearing parent: ", o)
                    o.hide = False
                   # propNew = o.parent.destruction.children.add()
                    #propNew.name = o.name
                    ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
                    o.select = False
        
                                                      
    
    
    
                       
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


#class MyServer(SimpleXMLRPCServer):
#    running = False
#    server = None
#    
#    class MyHandler(SimpleXMLRPCRequestHandler):
#        rpc_paths = ('/RPC2', )
#   
#       
#    def start():
#        if MyServer.server == None:
#            MyServer.server = MyServer(("localhost", 8999), 
#                                requestHandler=MyServer.MyHandler, 
#                                allow_none=True)
#        
#            MyServer.server.register_function(MyServer.execute)
#            MyServer.server.register_function(MyServer.stop)
#            MyServer.server.register_instance(bpy)
#            MyServer.running = True
#        
#            while MyServer.running:
#                print("Running")
#                MyServer.server.handle_request()
#                
#            del MyServer.server
#     
#    def execute(cmd):
#        exec(cmd)
#    
#    def stop():
#        if MyServer.server != None:
#            MyServer.running = False
#    
#    def proxy(cmd):
#        p = ServerProxy('http://localhost:8999')
#        p.execute(cmd)
#        p.stop() 
            
        
     


class DestroyObject(types.Operator):
    bl_idname = "object.destroy"
    bl_label = "Destroy Object"
    bl_description = "Start fracturing process"
    bl_options = {'UNDO'}
    
    impactLoc = bpy.props.FloatVectorProperty(default = (0, 0, 0))
    proc = None
    lock = None
    
    def execute(self, context):
        
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        
        #print(event.type)
       # if event.type == 'ESC':
        #    context.user_preferences.edit.use_global_undo = undo 
            
            #if c != None:# and s != None:
                #MyServer.stop()
             #   c.join()
                #s.join()
        #    return {'CANCELLED'}
        
        #set a heavy mass as workaround, until mass update works correctly...
        #context.active_object.game.mass = 1000
        
        if context.active_object.destruction.destructionMode == 'DESTROY_V' or \
        context.active_object.destruction.destructionMode == 'DESTROY_VB':
            vol = context.active_object.destruction.voro_volume
            if vol != None and vol != "":
                obj = context.scene.objects[vol]
                if obj.type != "MESH" or obj == context.active_object:
                   self.report({'ERROR_INVALID_INPUT'},"Object must be a mesh other than the original object")
                   return {'CANCELLED'}
        
        if context.active_object.destruction.destructionMode == 'DESTROY_L':        
            if context.active_object.parent == None or context.active_object.parent.type != "EMPTY":
                self.report({'ERROR_INVALID_INPUT'},"Object must be parented to an empty before")
                return {'CANCELLED'}
                
        start = clock()   
        #s = threading.Thread(target=MyServer.start)
        #func = dd.DataStore.proc.processDestruction
        #args = (context, Vector(self.impactLoc))
        #c = threading.Thread(target=func, args=args)
               
        #s.start()
        #c.start()
        #v = Vector(self.impactLoc)
        
       # c.join()
        #s.join()
                      
        dd.DataStore.proc.processDestruction(context, Vector((self.impactLoc)))
        print("Decomposition Time:" , clock() - start) 
        context.user_preferences.edit.use_global_undo = undo
        
       # lock.release()     
        return {'FINISHED'}
    
    #def invoke(self, context, event):
    #    if context.active_object:
    #        context.window_manager.modal_handler_add(self)
    #        return {'RUNNING_MODAL'}
    #    else:
    #        self.report({'WARNING'}, "No active object, could not finish")
    #        return {'CANCELLED'}

class UndestroyObject(types.Operator):
    bl_idname = "object.undestroy"
    bl_label = "Undestroy Object"
    bl_description = "Manually undo object destruction, alternatively use regular undo"
    bl_options = {'UNDO'}
    
    
    def execute(self, context):
        
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        
        for o in context.selected_objects:
            if o.name.startswith("P_"):
                backup = data.objects[o.destruction.backup]
                self.selectShards(o, backup)
                ops.object.delete()
                
                if context.scene.hideLayer == 1:
                    context.scene.objects.link(backup)
                    backup.use_fake_user = False
        
                backup.location = Vector((0,0,0))
                backup.select = True
                ops.object.origin_set(type='ORIGIN_GEOMETRY')
                backup.select = False
                backup.destruction.is_backup_for = ""
            
        context.user_preferences.edit.use_global_undo = undo     
        return {'FINISHED'}
            
           
#        volobj = None
#        for o in data.objects:
#            if o.destruction != None:
#                if o.destruction.is_backup_for == context.active_object.name:
#                    backup = o
#                    vol = o.destruction.voro_volume 
#                    if vol != "":
#                        volobj = context.scene.objects[vol]
#                        #print("VOL", volobj.name) 
#        
#        for o in data.objects:
#            if o.destruction != None:
#                if o.destruction.is_backup_for == context.active_object.name:
#                    backup = o    
#                    if context.scene.hideLayer == 1 and o != volobj:
#                       # print("LINK", o.name) 
#                        context.scene.objects.link(o)
#                    #o.select = True
#                   # ops.object.origin_set(type='ORIGIN_GEOMETRY')
#                    #o.select = False      
#                    o.destruction.is_backup_for = ""
#                    o.use_fake_user = False
#        
#        for o in data.objects:
#            o.select = False
#            
#        context.active_object.select = True
#        self.selectShards(context.active_object, backup)
#        ops.object.delete()
#        
#        backup.location = Vector((0,0,0))
#        backup.select = True
#        ops.object.origin_set(type='ORIGIN_GEOMETRY')
#        backup.select = False
#        
#        backup.destruction.is_backup_for = ""
#        context.user_preferences.edit.use_global_undo = undo     
#        return {'FINISHED'}
    
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
            #self.selectShards(c, backup)

class GameStart(types.Operator):
    bl_idname = "game.start"
    bl_label = "Start Game Engine"
    bl_description = "Start game engine with recording enabled by default"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        
        names = []
        #isDynamic = False
        if context.object.destruction.dynamic_mode == "D_DYNAMIC":
            #isDynamic = True
            for i in range(0, context.scene.dummyPoolSize):
                ops.mesh.primitive_cube_add(layers = [False, True, False, False, False,
                                                   False, False, False, False, False,
                                                   False, False, False, False, False,
                                                   False, False, False, False, False])
                                   
                context.active_object.name = "Dummy" #rely on blender automatic unique naming here...
                names.append(context.active_object.name)
                
                context.active_object.game.physics_type = 'RIGID_BODY'
                context.active_object.game.radius = 0.01
                context.active_object.game.use_collision_bounds = True
                context.active_object.game.collision_bounds_type = 'TRIANGLE_MESH'
                context.active_object.game.collision_margin = 0.0
                context.active_object.game.mass = 100.0
        
        if context.object.destruction.dynamic_mode == "D_PRECALCULATED":  
            context.scene.game_settings.use_animation_record = True
            context.scene.game_settings.use_frame_rate = True
            context.scene.game_settings.restrict_animation_updates = True
        context.scene.game_settings.show_framerate_profile = True
        ops.view3d.game_start()
        
        #if isDynamic:
        #    context.scene.converted = False
        
        context.scene.layers = [False, True, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False]
        for n in names:
            o = bpy.data.objects[n]
            context.scene.objects.unlink(o)
            bpy.data.objects.remove(o)
        
        context.scene.layers = [True, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False] 
        #undestroy all P_0 parents
        #for o in context.scene.objects:
        #    if o.name.startswith("P_0_"):
        #        context.scene.objects.active = o
        #        bpy.ops.object.undestroy() 
        
        return {'FINISHED'}

class ActiveToSelected(types.Operator):
    bl_idname = "active.to_selected"
    bl_label = "Copy From Active To Selected"
    bl_description = "Copy Properties from Active to Selected Objects"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        active = context.active_object
        selected = context.selected_objects
        
        if active and selected:
            for prop in active.destruction.items():
                for s in selected:
                    if prop[0] not in ('wasCompound', 'backup', 'children', 'ascendants', 'converted', 'is_backup_for', 'destroyable', 
                                        'tempLoc', 'origLoc', 'restoreLoc', 'restore'):
                        print("Copying:", prop[0])
                        s.destruction[prop[0]] = prop[1]
                 
            return {'FINISHED'}
        
        return {'CANCELLED'}

#class RunUnitTest(types.Operator):
#    bl_idname = "test.run"
#    bl_label = "Run Unit Tests"
#    bl_description = "Run the destruction unit tests not related to bge"
#    
#    def execute(self, context):
#        test.run() #module test
#        return {'FINISHED'}
#
#class RunBGETest(types.Operator):
#    bl_idname = "bge_test.run"
#    bl_label = "Run BGE Unit Tests"
#    bl_description = "Enable or disable the bge related destruction unit tests"
#    
#    def execute(self, context):
#        
#        context.scene.objects.active = data.objects["Player"]
#        
#        if not context.scene.runBGETests:
#            
#            currentDir = path.abspath(os.path.split(__file__)[0])
#            print(ops.text.open(filepath = currentDir + "\\unittest\\destruction_bge_test.py", internal = False))
#            #setup logic bricks -player
#              
#            #run unit tests with key "T"
#            ops.logic.controller_add(type = 'PYTHON', object = "Player", name = "UnitTest")
#        
#            context.active_object.game.controllers[11].mode = 'MODULE'
#            context.active_object.game.controllers[11].module = "destruction_bge_test.run"
#         
#            ops.logic.sensor_add(type = 'KEYBOARD', object = "Player", name = "TestKey")
#            context.active_object.game.sensors[11].key = 'T'
#        
#            context.active_object.game.controllers[11].link(
#            context.active_object.game.sensors[11])
#            context.scene.runBGETests = True
#        
#        else:
#            
#            ops.logic.controller_remove(controller = "UnitTest", object = "Player")
#            ops.logic.sensor_remove(sensor = "TestKey", object = "Player")
#            data.texts.remove(data.texts["destruction_bge_test.py"])
#            context.scene.runBGETests = False
#            
#        return {'FINISHED'}
        
            