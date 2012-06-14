import bpy
import os
from . import backend_git as b

class GitInit(bpy.types.Operator):
    bl_idname = "git.init"
    bl_label = "Init"
    
    def execute(self, context):
        g = b.Git(context.scene.workdir)
        g.init(context.scene.repo)
        return {'FINISHED'}

class GitStatus(bpy.types.Operator):
    bl_idname = "git.status"
    bl_label = "Status"
   
    def execute(self, context):
        g = b.Git(context.scene.workdir)
        g.status()
        return {'FINISHED'}
    
class GitAdd(bpy.types.Operator):
    bl_idname = "git.add"
    bl_label = "Add"
    
    def execute(self, context):
        g = b.Git(context.scene.workdir)
        g.add(context.scene.file)
        return {'FINISHED'}

class GitCommit(bpy.types.Operator):
    bl_idname = "git.commit"
    bl_label = "Commit"
    
    def execute(self, context):
        g = b.Git(context.scene.workdir)
        g.commit(context.scene.filename, context.scene.message)
        return {'FINISHED'}

class GitPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_git"
    bl_label = "Git"
    bl_context = "object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    
    def register():
        currentfile = "" # need to obtain current blend file path/name  
        currentdir = "" # thats the addon directory -> bpy.path.abspath(os.path.split(__file__)[0])
     
        bpy.types.Scene.workdir = bpy.props.StringProperty(name = "workdir", default = currentdir)
        bpy.types.Scene.repo = bpy.props.StringProperty(name = "repo", default = currentdir) 
        bpy.types.Scene.file = bpy.props.StringProperty(name = "file", default = currentfile)
        bpy.types.Scene.msg = bpy.props.StringProperty(name = "msg")
    
    def unregister():
        del bpy.types.Scene.workdir
        del bpy.types.Scene.repo
        del bpy.types.Scene.file
        del bpy.types.Scene.msg
     
    def draw(self, context):
        
        layout = self.layout
        
        layout.prop(context.scene, "workdir", text = "Working Directory")
        layout.operator("git.status")
        
        layout.prop(context.scene, "repo", text = "Repository Path")
        layout.operator("git.init")
        
        layout.prop(context.scene, "file", text = "File/Directory to add")
        layout.operator("git.add")
        
        layout.prop(context.scene, "file", text = "File/Directory to commit")
        layout.prop(context.scene, "msg", text = "Commit Message")
        layout.operator("git.commit")
        