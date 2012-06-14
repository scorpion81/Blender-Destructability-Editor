import bpy
import os
from . import backend_git as b
from bpy.app.handlers import persistent

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
        
        bpy.types.Scene.workdir = bpy.props.StringProperty(name = "workdir")
        bpy.types.Scene.repo = bpy.props.StringProperty(name = "repo") 
        bpy.types.Scene.file = bpy.props.StringProperty(name = "file")
        bpy.types.Scene.msg = bpy.props.StringProperty(name = "msg")
        bpy.app.handlers.load_post.append(GitPanel.file_handler)
        bpy.app.handlers.save_post.append(GitPanel.file_handler)
    
    def unregister():
        del bpy.types.Scene.workdir
        del bpy.types.Scene.repo
        del bpy.types.Scene.file
        del bpy.types.Scene.msg
     
    def draw(self, context):
        
        layout = self.layout
        
        row = layout.row(align=True)
        row.prop(context.scene, "workdir", text = "Working Directory")
        props = row.operator("buttons.directory_browse", text = "", icon = 'FILE_FOLDER')
        props["filepath"] = context.scene.workdir
        layout.operator("git.status")
        
        row = layout.row(align=True)
        row.prop(context.scene, "repo", text = "Repository Path")
        props = row.operator("buttons.directory_browse", text = "", icon = 'FILE_FOLDER')
        props["filepath"] = context.scene.repo
        layout.operator("git.init")
        
        row = layout.row(align=True)
        row.prop(context.scene, "file", text = "File to add")
        props = row.operator("buttons.file_browse", text = "", icon = 'FILESEL')
        props["filepath"] = context.scene.file
        layout.operator("git.add")
        
        row = layout.row(align=True)
        row.prop(context.scene, "file", text = "File to commit")
        props = row.operator("buttons.file_browse", text = "", icon = 'FILESEL')
        props["filepath"] = context.scene.file
        layout.prop(context.scene, "msg", text = "Commit Message")
        layout.operator("git.commit")
        
    @persistent
    def file_handler(dummy):
        print("Load Handler:", bpy.data.filepath)
        currentfile = bpy.path.basename(bpy.data.filepath)
        currentdir = bpy.path.abspath("//")
        
        bpy.context.scene.workdir = currentdir        
        bpy.context.scene.repo = currentdir
        bpy.context.scene.file = currentfile