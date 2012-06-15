import bpy
import os
from . import backend_git as b
from bpy.app.handlers import persistent

class GitLog(bpy.types.Operator):
    bl_idname = "git.log"
    bl_label = "Log"
    
    def populateLog(self, context, log):
        records = log.split("\n\n")
        commit = None
        author = None
        date = None
        
        #print("R:", records)
        for i in range(0, len(records)):
               
            if i % 2 == 0:
                lines = records[i].split("\n")
                #print("L:", lines)
                commit = lines[0].split(" ")[1]
                author = lines[1].split(": ")[1]
                date = lines[2].split(": ")[1]
            else:
                message = records[i].split("\n")[0] 
                    
                entry = context.scene.git.history.add()
                entry.message = message
                entry.commit = commit
                entry.author = author
                entry.date = date
                
                #the display name ?
                entry.name = message + " " + date + " " + commit
    
    def isRepo(self, context, g):
        s = g.status(context.scene.git.file)
        stat = s.decode("utf-8")
        if "fatal: Not a git repository" in stat: #very hackish
            return False
        return True    
    
    def execute(self, context):
        g = b.Git(context.scene.git.workdir)
        
        if self.isRepo(context, g):
            logRaw = g.log(context.scene.git.file)
            log = logRaw.decode("utf-8")
            context.scene.git.history.clear()
            
            #print("LOG", log)
            if log != "":
                self.populateLog(context, log)
        
        return {'FINISHED'}
    
class GitReset(bpy.types.Operator):
    bl_idname = "git.reset"
    bl_label = "Reset"
    
    def execute(self, context):
        g = b.Git(context.scene.git.workdir)
        g.reset(context.scene.git.file)
        return {'FINISHED'}

class GitCommit(bpy.types.Operator):
    bl_idname = "git.commit"
    bl_label = "Commit"
    
    def execute(self, context):
        g = b.Git(context.scene.git.workdir) 
        s = g.status(context.scene.git.file)
        status = s.decode("utf-8")
        print(status)
        
        if "fatal: Not a git repository" in status: #very hackish
            print("Init and Add")
            print(g.init().decode("utf-8"))
            print(g.add(context.scene.git.file).decode("utf-8"))
        elif "Untracked" in status:
            print("Add")
            print(g.add(context.scene.git.file).decode("utf-8"))
        
        print(g.commit(context.scene.git.file, context.scene.git.msg).decode("utf-8"))
        bpy.ops.git.log()
        return {'FINISHED'}
    
class GitUpdate(bpy.types.Operator):
    bl_idname = "git.update"
    bl_label = "Update"
    
    def execute(self, context):
        g = b.Git(context.scene.git.workdir) 
        index = context.scene.git.active_entry
        entry = context.scene.git.history[index]
        g.update(context.scene.git.file, context.scene.git.workdir, entry.commit)
        #load file here
        bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
         
        return {'FINISHED'}

class LogEntry(bpy.types.PropertyGroup):
    
    message = bpy.props.StringProperty(name = "message")
    author = bpy.props.StringProperty(name = "author")
    date = bpy.props.StringProperty(name = "date")
    commit = bpy.props.StringProperty(name = "commit")
    

class GitContext(bpy.types.PropertyGroup):
    
    workdir = bpy.props.StringProperty(name = "workdir")
    file = bpy.props.StringProperty(name = "file")
    msg = bpy.props.StringProperty(name = "msg")
    active_entry = bpy.props.IntProperty(name = "active_entry")
    history = bpy.props.CollectionProperty(type = LogEntry, name = "history")
    

class GitPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_git"
    bl_label = "Git"
    bl_context = "object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    
    def register():
        
        bpy.types.Scene.git = bpy.props.PointerProperty(type = GitContext, name = "GitContext")
        bpy.app.handlers.load_post.append(GitPanel.file_handler)
        bpy.app.handlers.save_post.append(GitPanel.file_handler)
    
    def unregister():
        del bpy.types.Scene.git
     
    def draw(self, context):
        
        layout = self.layout
        
#        row = layout.row(align=True)
#        row.prop(context.scene, "workdir", text = "Working Directory")
#        props = row.operator("buttons.directory_browse", text = "", icon = 'FILE_FOLDER')
#        props["filepath"] = context.scene.workdir
#        layout.operator("git.status")
#        
#        row = layout.row(align=True)
#        row.prop(context.scene, "repo", text = "Repository Path")
#        props = row.operator("buttons.directory_browse", text = "", icon = 'FILE_FOLDER')
#        props["filepath"] = context.scene.repo
#        layout.operator("git.init")
#        
#        row = layout.row(align=True)
#        row.prop(context.scene, "file", text = "File to add")
#        props = row.operator("buttons.file_browse", text = "", icon = 'FILESEL')
#        props["filepath"] = context.scene.file
#        layout.operator("git.add")
        
#        row = layout.row(align=True)
#        row.prop(context.scene, "file", text = "File to commit")
#        props = row.operator("buttons.file_browse", text = "", icon = 'FILESEL')
#        props["filepath"] = context.scene.file
        
        layout.label("History")
        layout.template_list(context.scene.git, "history", context.scene.git, "active_entry" , rows = 5)
        
        if context.scene.git.file != "": 
            layout.operator("git.update")
            
            layout.prop(context.scene.git, "msg", text = "Message")        
            layout.operator("git.commit")
            
            #layout.operator("git.reset") need to unload file first ?
        
    @persistent
    def file_handler(dummy):
        print("File Handler:", bpy.data.filepath)
        currentfile = bpy.path.basename(bpy.data.filepath)
        currentdir = bpy.path.abspath("//")
        
        bpy.context.scene.git.workdir = currentdir        
        bpy.context.scene.git.file = currentfile
        if currentdir != "" and currentfile != "":
            bpy.ops.git.log()