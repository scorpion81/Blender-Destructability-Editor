import subprocess
import os
import shutil


#find/set path to git
#error feedback -> process show stdout
#class structure:
#GitRepo, Git, 
#current file committen, current file updaten

#git command class
class Git():
    def __init__(self, work):
        self.git = '/usr/bin/git'
        self.work = work
        os.chdir(self.work)
          
    def init(self, repo):
        self.command("init", ["--separate-git-dir=" + repo, self.work])
        
    def add(self, file):
        #filename = os.path.basename(file)
        self.command("add", [file])
    
    def commit(self, file, message):
        self.command("commit", ['-m', message, file])
    
    def status(self):
        self.command("status", [])
    
    def ignore(self, file, asPattern):
        os.chdir(self.work)
        ig = open(".gitignore", "a+")
        if asPattern:
            ig.write(file + "\n")
        else:
            ig.write("!" + file + "\n")
        ig.close()
        
#    def checkout(self, path):
#        pass
#    
#    def clone(self, target):
#        pass
#    
#    def log(self):
#        pass 
#    
#    def pull(self):
#        pass
#    
#    def push(self):
#        pass
#    
#    def rebase(self):
#        pass
#    
#    def reset(self):
#        pass
#    
#    def rm(self):
#        pass
#    
#    def show(self):
#        pass
#    
#    def tag(self):
#        pass
#        
    #generic Git command with textual feedback        
    def command(self, cmd, args): 
        p = subprocess.Popen([self.git, cmd] + args,
            stdout = subprocess.PIPE, 
            stderr = subprocess.STDOUT)
        out = p.stdout.read().decode("utf-8") # convert bytes to string
        print(out)

#def test():
#    repo = '/home/xxx/TestRepo/'
#    file = '/home/xxx/Dokumente/blender/TEST/GitWork/macroTest.blend'  
#    work = '/home/xxx/Dokumente/blender/TEST/GitWork/'     
#    g = Git(repo, work)
#   # g.init()
#   # g.add(file)
#  #  g.ignore("*.blend1", True)
##    g.ignore("*.blend2", True)
#  #  g.commit(file, "MacroTest Initial Commit")
#    g.status()
#
##test() 