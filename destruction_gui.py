from bpy import types, props, utils, ops, data, path
from bpy.types import Object, Scene
from . import destruction_proc as dp
from . import destruction_data as dd
import math
import os
import pickle
import inspect


class DestructabilityPanel(types.Panel):
    bl_idname = "OBJECT_PT_destructability"
    bl_label = "Destructability"
    bl_context = "object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
   # bl_options = {'UNDO'}
    
    def register():
        dp.initialize()
   
   # def execute(self, context):
   #     return {'FINISHED'}

    def unregister():
        del Object.destruction
        utils.unregister_class(DestructionContext)   
    
    def draw(self, context):
        layout = self.layout
      #  layout.active = context.object.useDestructability
        
        row = layout.row()
        row.label(text = "Apply this settings to:")
        row.prop(context.active_object.destruction, "transmitMode",  text = "")
        layout.separator()
        
        row = layout.row()
        row.prop(context.active_object.destruction, "destroyable", text = "Destroyable")

        col = row.column()
        col.prop(context.object.destruction, "partCount", text = "Parts")
        col.prop(context.object.destruction, "wallThickness", text = "Thickness")
        col.prop(context.object.destruction, "pieceGranularity", text = "Granularity")
        col.active = context.object.destruction.destroyable

        
        row = layout.row()
        row.prop(context.object.destruction, "destructionMode", text = "Destruction Mode")
        row.active = context.object.destruction.destroyable
        
        row = layout.row()
        row.operator("object.destroy")
        row.active = context.object.destruction.destroyable
        
        layout.separator()
       
        layout.prop(context.object.destruction, "isGround", text = "Is Connectivity Ground")
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
        row.label(text = "Select Ground:")
     #   row.prop(context.object.destruction, "groundSelector", text = "")
        row.prop_search(context.object.destruction, "groundSelector", 
                        context.scene, "objects", icon = 'OBJECT_DATA', text = "")
        row.operator("ground.add", icon = 'ZOOMIN', text = "")
        row.active = context.object.destruction.groundConnectivity
        
        row = layout.row()
        col = row.column()
        col.prop(context.object.destruction, "gridDim", text = "Connectivity Grid")
        col.active = context.object.destruction.groundConnectivity
        layout.separator()
         
        layout.prop(context.object.destruction, "destructor", text = "Destructor")
        
        row = layout.row()
        row.label(text = "Destructor Targets")
        row.active = context.object.destruction.destructor
        
        row = layout.row()
        row.template_list(context.object.destruction, "destructorTargets", 
                          context.object.destruction, "active_target" , rows = 2) 
        row.operator("target.remove", icon = 'ZOOMOUT', text = "") 
        row.active = context.object.destruction.destructor  
        
        row = layout.row()
        row.label(text = "Select Destroyable: ")
     #   row.prop(context.object.destruction, "targetSelector", text = "")
        row.prop_search(context.object.destruction, "targetSelector", context.scene, 
                       "objects", icon = 'OBJECT_DATA', text = "")
        row.operator("target.add", icon = 'ZOOMIN', text = "")
        row.active = context.object.destruction.destructor 
        
        row = layout.row()
        col = row.column() 
        
        col.operator("player.setup")
        col.active = not context.scene.player
        
        col = row.column()
        col.operator("player.clear")
        col.active = context.scene.player
        
        row = layout.row()
        
        txt = "To Editor Parenting"
        if not context.scene.converted:
            txt = "To Game Parenting"
       
        row.operator("parenting.convert", text = txt)
        
class AddGroundOperator(types.Operator):
    bl_idname = "ground.add"
    bl_label = "add ground"
    
    def execute(self, context):
        found = False
        for prop in context.object.destruction.grounds:
            if prop.name == context.object.destruction.groundSelector:
                found = True
                break
        if not found:
           propNew = context.object.destruction.grounds.add()
           propNew.name = context.object.destruction.groundSelector
               
        return {'FINISHED'}   
    
class RemoveGroundOperator(types.Operator):
    bl_idname = "ground.remove"
    bl_label = "remove ground"
    
    def execute(self, context):
        index = context.object.destruction.active_ground
        context.object.destruction.grounds.remove(index)
        return {'FINISHED'}
       
        
class AddTargetOperator(types.Operator):
    bl_idname = "target.add"
    bl_label = "add target"
    
    def execute(self, context):
        found = False
        for prop in context.object.destruction.destructorTargets:
            if prop.name == context.object.destruction.targetSelector:
                found = True
                break
        if not found:
            propNew = context.object.destruction.destructorTargets.add()
            propNew.name = context.object.destruction.targetSelector
        return {'FINISHED'}   
    
class RemoveTargetOperator(types.Operator):
    bl_idname = "target.remove"
    bl_label = "remove target"
    
    def execute(self, context):
        index = context.object.destruction.active_target
        context.object.destruction.destructorTargets.remove(index)
        return {'FINISHED'} 
    
class SetupPlayer(types.Operator):
    bl_idname = "player.setup"
    bl_label = "Setup Player"
    
    def execute(self, context):
        
        if context.scene.player:
            return
        
        context.scene.player = True
       
        
        ops.object.add()
        context.active_object.name = "Player"
       
        ops.object.add(type = 'CAMERA')
        context.active_object.name = "Eye"
         
        ops.object.add()
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
        
        ops.mesh.primitive_ico_sphere_add(layers = [False, True, False, False, False,
                                                    False, False, False, False, False,
                                                    False, False, False, False, False,
                                                    False, False, False, False, False])
        context.active_object.name = "Ball"   
        
        context.active_object.game.physics_type = 'RIGID_BODY'
        context.active_object.game.collision_bounds_type = 'SPHERE'                                          
        
        #internalize bge scripts
        print(__file__)
        currentDir = path.abspath(os.path.split(__file__)[0])
        
       # print(path.abspath(data.texts
        print(ops.text.open(filepath = currentDir + "\destruction_bge.py", internal = True))
        print(ops.text.open(filepath = currentDir + "\player.py", internal = True))
        print(ops.text.open(filepath = currentDir + "\destruction_data.py", internal = False))
        
        
        #setup logic bricks -player
        context.scene.objects.active = data.objects["Player"]
        
        ops.logic.controller_add(type = 'AND', object = "Player")
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
            
        #launcher
        context.scene.objects.active = data.objects["Launcher"]
        ops.logic.controller_add(type = 'PYTHON', object = "Launcher")
        
        context.active_object.game.controllers[0].mode = 'MODULE'
        context.active_object.game.controllers[0].module = "player.shoot"
        
        ops.logic.sensor_add(type = 'MOUSE', object = "Launcher")
        context.active_object.game.sensors[0].mouse_event = 'LEFTCLICK'
        
        ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Shoot", object = "Launcher")
        context.active_object.game.actuators[0].mode = 'ADDOBJECT'
        context.active_object.game.actuators[0].object = data.objects["Ball"]
        
        context.active_object.game.controllers[0].link(
            context.active_object.game.sensors[0],
            context.active_object.game.actuators[0])
        
        #ball
        context.scene.objects.active = data.objects["Ball"]
        ops.logic.controller_add(type = 'PYTHON', object = "Ball")
        ops.logic.sensor_add(type = 'COLLISION', object = "Ball")
        
        context.active_object.game.sensors[0].use_pulse_true_level = True
        
        context.active_object.game.controllers[0].mode = 'MODULE'
        context.active_object.game.controllers[0].module = "destruction_bge.collide"
        
        context.active_object.game.controllers[0].link(
            context.active_object.game.sensors[0])
        
        #by default destroy all destroyable objects
        context.active_object.destruction.destructor = True
        
        for o in data.objects:
            if o.destruction.destroyable:
                target = context.active_object.destruction.destructorTargets.add()
                target.name = o.name
                
        
        return {'FINISHED'}
    
class ClearPlayer(types.Operator):
    bl_idname = "player.clear"
    bl_label = "Clear Player"
    
    def execute(self, context):
        
        if not context.scene.player:
            return
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
        data.objects["Ball"].select = True
     
        ops.object.delete()
        
        context.scene.layers = [True, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False]
                                
        data.texts.remove(data.texts["destruction_bge.py"])
        data.texts.remove(data.texts["player.py"])                        
        
        return {'FINISHED'}
    
        
class ConvertParenting(types.Operator):
    bl_idname = "parenting.convert"
    bl_label = "Convert Parenting"
    
    def execute(self, context):
        if not context.scene.converted:
            self.convert(context)
        else:
            self.unconvert(context)
        context.scene.converted = not context.scene.converted
        return {'FINISHED'}
        
    
    def convert(self, context):
        for o in data.objects:
            
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher":
                       continue
            index = -1
            context.scene.objects.active = o
            ctx = dp.setObject(context, o)
            if o.parent != None:
                index = 0
                ops.object.game_property_new()
                o.game.properties[0].name = "myParent"
                o.game.properties[0].type = 'STRING'
                o.game.properties[0].value = o.parent.name
              #  o.parent = None
            
            ctx = dp.setObject(context, o)    
            ops.object.game_property_new(ctx)
            o.game.properties[index + 1].name = "destroyable"
            o.game.properties[index + 1].type = 'BOOL'
            o.game.properties[index + 1].value = o.destruction.destroyable
            
            ctx = dp.setObject(context, o)
            ops.object.game_property_new(ctx)
            o.game.properties[index + 2].name = "isGround"
            o.game.properties[index + 2].type = 'BOOL'
            o.game.properties[index + 2].value = o.destruction.isGround
            
            ctx = dp.setObject(context, o)
            ops.object.game_property_new(ctx)
            o.game.properties[index + 3].name = "groundConnectivity"
            o.game.properties[index + 3].type = 'BOOL'
            o.game.properties[index + 3].value = o.destruction.groundConnectivity
            
            ctx = dp.setObject(context, o)
            ops.object.game_property_new(ctx)
            o.game.properties[index + 4].name = "grounds"
            o.game.properties[index + 4].type = 'STRING'
            o.game.properties[index + 4].value = self.grounds(context)
            
            ctx = dp.setObject(context, o)
            ops.object.game_property_new(ctx)
            o.game.properties[index + 5].name = "destructor"
            o.game.properties[index + 5].type = 'BOOL'
            o.game.properties[index + 5].value = o.destruction.destructor
            
            ctx = dp.setObject(context, o)
            ops.object.game_property_new(ctx)
            o.game.properties[index + 6].name = "destructorTargets"
            o.game.properties[index + 6].type = 'STRING'
            o.game.properties[index + 6].value = self.targets(context)
            
#            ctx = dp.setObject(context, o)
#            ops.object.game_property_new(ctx)
#            o.game.properties[index + 7].name = "grid"
#            o.game.properties[index + 7].type = 'STRING'
#            o.game.properties[index + 7].value = self.pickleGrid(o.name)

            
            bbox = o.destruction.gridBBox
            dim  = o.destruction.gridDim

            ctx = dp.setObject(context, o)
            ops.object.game_property_new(ctx)
            o.game.properties[index + 7].name = "gridbbox"
            o.game.properties[index + 7].type = 'STRING'
            o.game.properties[index + 7].value = str(bbox[0]) + " " + str(bbox[1]) + " " + str(bbox[2])
            
            ctx = dp.setObject(context, o)
            ops.object.game_property_new(ctx)
            o.game.properties[index + 8].name = "griddim"
            o.game.properties[index + 8].type = 'STRING'
            o.game.properties[index + 8].value = str(dim[0]) + " " + str(dim[1]) + " " + str(dim[2])
            
  
        for o in data.objects: #restrict to P_ parents only ! no use all
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher":
                    continue
            o.parent = None
                       
    def unconvert(self, context):
        for o in data.objects:
            
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher":
                       continue
            
            context.scene.objects.active = o
            if len(o.game.properties) > 8:
                o.parent = data.objects[o.game.properties[0].value]
                
                while len(o.game.properties) > 0:
                    ctx = dp.setObject(context, o)
                    ops.object.game_property_remove(ctx)
    
    def grounds(self, context):
       retVal = ""
       for g in context.object.destruction.grounds:
           retVal = retVal + g.name + " "
       return retVal
   
   
    def targets(self, context):
       retVal = ""
       for t in context.object.destruction.destructorTargets:
           retVal = retVal + t.name + " "
       return retVal
   
    def pickleGrid(self, name):
        print(name, dd.DataStore.grids, name in dd.DataStore.grids.keys())
        if name not in dd.DataStore.grids.keys():
            return ""
        grid = dd.DataStore.grids[name]
        print(inspect.getmembers(grid.cells[(0,0,0)]))
        strObj = str(pickle.dumps(grid), 'ascii')
        print("Pickled: ", strObj)
        return strObj                 
   
class DestroyObject(types.Operator):
    bl_idname = "object.destroy"
    bl_label = "Destroy Object"
    
    def execute(self, context):
        dd.DataStore.proc.processDestruction(context)
        return {'FINISHED'}