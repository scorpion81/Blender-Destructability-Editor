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
        
    # Getting and Creating Projects 
    #def init(self, quiet=False, bare=False, template ="", separate = "", shared = "")
    def init(self):
        self.command("init", [self.work])
        
#    def clone(self, template = "", local = False, shared = False, no_hardlinks = False, 
#              quiet = False, n = False, bare = False, mirror = False, origin = "", 
#              branch = "", upload_pack = "", reference = "", separate_git_dir = "", 
#              depth = 0, recursive = False, repository)       
#        pass

    # Basic Snapshotting
        
#    def add(self, n = False, v = False, force = False, interactive = False, patch = False,
#            edit = False, all = False, update = False, intent_to_add = False, refresh = False,
#            ignore_errors = False, ignore_missing = False, filepattern)
    def add(self, file):
        self.command("add", [file])
        
#    def status(self, short = False, branch = False, porcelain = False, untracked_files = "", 
#              ignore_submodules = "", ignored = False, z = False, pathspec) 
#        #self.command("status", [])
#        pass
    
    def status(self, file):
        return self.command("status", [file])
    
    #def diff(self):
    #    pass    
    
#    def commit(self, interactive = False, all = False, patch = False, s = False, v = False,
#               u = "", amend = False, dry_run = False, c = "", C = "", fixup = "",
#               squash = "", F = "",  message = "", reset_author = False, allow_empty = False,
#               allow_empty_message = False, no_verify = False, e = False, author = ""
#               date = "", cleanup = "", status = False, no_status = False, i = False, o = False)
    def commit(self, file, message):           
        self.command("commit", ['-m', message, file])
    
    def reset(self, file):
        self.command("reset", ['--hard', file])
    
    def rm(self, file):
        self.command("rm", [file])
    
#    def mv(self):
#        pass
    


    #Branching and Merging 
#    def branch(self):
#        pass   
#    
#    def checkout(self):
#        pass
    
    def log(self, file):
        return self.command("log", [file]) 
    
    def update(self, file, commit):
        outRaw = self.command("ls-tree", [commit])
        out = outRaw.stdout.read().decode("utf-8")
        blobnr = self.blobnr(out, file)
        if blobnr != None:
            blob = self.command("cat-file", ["blob", blobnr])
            tmp = open("tmp.blend", "wb+")
            tmp.write(blob.stdout.read())
            tmp.close()
        
    
    def blobnr(self, commitdata, file):
        lines = commitdata.split("\n")
        print("L", lines)
        for l in lines:
            tab = l.split("\t")
            name = tab[1]
            blob = tab[0].split(" ")[1]
            blobnr = tab[0].split(" ")[2]
            #print("R", records)
            
            if "blob" == blob and file == name:
                return blobnr
        return None
                    
        
    
#    def merge(self):
#        pass
#
#    def tag(self):
#        pass

    # Sharing and Updating Projects
#    
#    def fetch(self):
#        pass
#    
#    def push(self):
#        pass
#    
#    def pull(self):
#        pass
#   
#    def remote(self):
#        pass
        
    # Miscellaneous
    
    def ignore(self, file, asPattern):
        os.chdir(self.work)
        ig = open(".gitignore", "a+")
        if asPattern:
            ig.write(file + "\n")
        else:
            ig.write("!" + file + "\n")
        ig.close()
#        
#    def show(self)
#        pass
#    
#    def rebase(self)
#        pass
#    
#    def grep(self)
#        pass
#    
#    def bisect(self)
#        pass
    
    #generic Git command with textual feedback  
          
    def command(self, cmd, args): 
        p = subprocess.Popen([self.git, cmd] + args,
            stdout = subprocess.PIPE, 
            stderr = subprocess.STDOUT)
        #out = p.stdout.read().decode("utf-8") # convert bytes to string
        #print(out)
        return p