#simple autocomplete:
# add each char typed into buffer, space empties buffer and insorts(insert sorted(?)) in a dict (because of types we need key and val)
# maybe keywords get the type "keyword", cant be overwritten, and all imported Types must be into dict too
# all others can be overwritten (when redeclared)
# declaration: key = name, value = type put into dict, empty buffer (after each space)
# if word is a type, put it as type into dict-> key = name, value = "Type"
# if word is unknown still, put as type "unknown" into dict
# fill in builtin types, and imported ones
# watch for def and class expressions, check if class or def is in buffer, then: till ( = func/classname, after (: params/subclass(1)

#TODO make addon out of this
#     make menu disappear when i continue typing (change focus)
#     correctly replace previously typed text by suggestion
#     handle class member display correctly after pushing "PERIOD"
#     categorize items: Class, Function, Variable at least

import bpy
import re

class Declaration:
    
    name = ""
    char_pos = 0
   
    def __init__(self, name):
        self.name = name
        self.char_pos = bpy.context.edit_text.current_character
    
class Scope(Declaration):

    local_funcs = {}
    local_vars = {}
    local_classes = {}
    local_unnamed_scopes = []
    parent = None
    
    def __init__(self, name): #indentation creates new scope too, name can be empty here
        super().__init__(name)
        
    def declare(self, declaration):
        #add a new declaration
        # if its a variable, add to localvars
        # if its a scope, add to scopes
        declaration.parent = self
        
        if isinstance(declaration, Class):
            self.local_classes[declaration.name] = declaration
        elif isinstance(declaration, Function):
            self.local_funcs[declaration.name] = declaration
        elif isinstance(declaration, Scope):
            self.local_unnamed_scopes.append(declaration)
        elif isinstance(declaration, Declaration):
            self.local_vars[declaration.name] = declaration
    
#    def copy(self):
#        s = None
#        
#        if parent != None:
#            s = Scope(self.name, self.parent)
#        else:
#            s = Scope(self.name, None)
#            
#        #copy Scope object only, need another reference in case activeScope is changed
#        s.local_funcs = self.local_funcs
#        s.local_vars = self.local_vars
#        s.local_classes = self.local_classes
#        return s

class Function(Scope):
    
    paramlist = []
    
    def __init__(self, name, paramlist):
        super().__init__(name)
        self.paramlist = paramlist
        
    def declare(self, declaration):
        super().declare(declaration)
        
#    def copy(self):
#        s = self.super.copy()
#        s.paramlist = paramlist
#        return s
 
class Class(Function):
    
    def __init__(self, name, superclasses):
        super().__init__(name, superclasses)
    
    def declare(self, declaration):
        super().declare(declaration)
    
#    def copy(self):
#        s = self.super.copy()
#        return s

#list of that (imported) modules must be generated, and active module (__module__)
class Module(Scope):
    
    submodules = []
    
    def __init__(self, name):
        super().__init__(name)
        self.char_pos = 0
        #print("PRINT", self.char_pos, super().char_pos)
    
    def declare(self, declaration):
        if isinstance(declaration, Module):
            submodules.append(declaration)
        else:
            super().declare(declaration)
        
        
class AutoCompletePopup(bpy.types.Menu):
    bl_idname = "text.popup"
    bl_label = ""
       
    def draw(self, context):
        layout = self.layout
        entries = context.edit_text.suggestions
        
        for e in entries:
            layout.operator("text.insert", text = e.name).text = e.name
                                   
class AutoCompleteOperator(bpy.types.Operator):
    bl_idname = "text.autocomplete"
    bl_label = "Auto Complete Text"
    
    identifiers = {'if': 'keyword', 
                   'else': 'keyword'}
                 #    ... 
                 #   'str' : 'type' # more accurate: class, function, builtin
                 #    ...}
                 #    #varname : typename , WHICH class
                    
    buflist = []
    buffer = ""
    oldbuffer = ""
#    lhs = "" # left hand side of =
#    lookupBuffer = ""
    lastLookups = {} #?, backspace must delete sub-buffers, that is 2 indexes on (sorted) list
    module = None
    activeScope = None
    
    def handleImport(self):
        #add all types of import to identifiers...
        #print out current module, after declaration change scope.... must parse the currently used code
        pass
    
    def isValid(self, identifier):
        return not identifier in self.identifiers or self.identifiers[identifier] != "keyword" 
    
    def parseIdentifier(self):
        
        #first check if we have a new identifier which mustnt be a keyword...
        self.buffer = "".join(str(i) for i in self.buflist).lstrip()
        print("BUFFER", self.buffer)
        
        #go to parent scope if new char_pos is smaller, "unindent"
        char_pos = bpy.context.edit_text.current_character
        while char_pos < self.activeScope.char_pos:
            if self.activeScope.parent != None:
                self.activeScope = self.activeScope.parent
            else:
                self.activeScope = self.module
                break
         
        #Case 1: Variable declaration: after SPACE/ENTER check for =
        #somewhere must be a single! "=" only !!, it must be the first one and no other = must follow, (split[1] is "" then)
        if "=" in self.buffer:
            s = self.buffer.split('=')
            s[0] = s[0].strip()
            print(s[0], s[1])
            if s[0] and s[1]: #maybe later get type of s[1] ??
                 v = Declaration(s[0])
                 #active module -> open file ? (important later, when treating different modules too)
                 #print(v.char_pos, self.activeScope.char_pos, self.isValid(s[0]))
                 if v.char_pos > self.activeScope.char_pos and self.isValid(s[0]):
                    self.activeScope.declare(v) 
                   # self.activeScope = v #variables build no scope
                    self.identifiers[s[0]] = v
                    print(self.identifiers)
                    
                 
        #Case 2: Function declaration: after SPACE/ENTER check for def and :
        #Case 3: Class declaration: after SPACE/ENTER check for class and :
        elif self.buffer.startswith("def") or self.buffer.startswith("class"):
            name = ""
            params = []
            
            openbr = self.buffer.split('(')
            name = openbr[0].split(' ')[1]
            
            closedbr = openbr[1].split(')')[0]
            psplit = closedbr.split(',')
            for p in psplit:
                #strip whitespace
                params.append(p.strip())
            
            if self.buffer.startswith("def"):
                f = Function(name, params)
                if f.char_pos > self.activeScope.char_pos and self.isValid(name):
                    self.activeScope.declare(f)
                    self.activeScope = f
                    self.identifiers[name] = f
            else:
                c = Class(name, params)
                if c.char_pos > self.activeScope.char_pos and self.isValid(name):
                    self.activeScope.declare(c)
                    self.activeScope = c
                    self.identifiers[name] = c
                    
            print(self.identifiers)    
                
        #Case 4: Anonymous scope declaration: after SPACE/ENTER check for :        
        elif self.buffer.endswith(":"):
            scope = Scope("")
            if scope.char_pos > self.activeScope.char_pos:
                self.activeScope.declare(scope)
                self.activeScope = scope 
        
     
        self.buflist = []
         
         #check identation level, if lower than current scope's one, go to parent scope(s)
         #compare how often indentation has taken place ?
         #if current_char < als scope.currentchar zu parent, while smaller, go to parent until parent = None      
                       
#        if self.isRhs: #rhs is type = var is declared here, rhs is expression/function = evaluate(?), rhs is var = reference
#            if self.lhs != "":
#                #check whether rhs is a type, -> compare with dict (all keys with value Type)
#               classes = [it[0] for it in identifiers.items() if isinstance(it[1], Class)]
#               funcs = [it[0] for it in identifiers.items() if is_instance(it[1], Function)]
##                if self.buffer in classes:
##                    self.identifiers[self.lhs] = self.buffer
##                elif if self.buffer in funcs:
##                    #must(?) eval the function, no just find its return type, by introspection
#                   
#        #put buffer content into dict (if not a keyword) or not there -> is var
#        if not self.identifiers[self.buffer] or self.identifiers[self.buffer] != "keyword":
#            self.identifiers[self.buffer] = "unknown"
#                
#            #empty buffer for next word, store potential lhs
#           # self.lhs = str(self.buffer) 
#            self.buffer = ""
            
            
    def lookupIdentifier(self, lastWords = None):
        
        self.buffer = "".join(str(i) for i in self.buflist).lstrip()
        print("lookupbuf", self.buffer)
        
        #only the NEW string compared to the last buffer is relevant
        #to look it up inside a subset/subdict of items
        words = []
        if lastWords == None:
            #if self.oldbuffer in self.lastLookups:
            #    lastWords = self.lastLookups[self.oldbuffer] #its a list only
            #    words = [it for it in lastWords if it.startswith(self.buffer)]
            #else:
            lastWords = self.identifiers
            words = [it[0] for it in lastWords.items() if it[0].startswith(self.buffer)]
        else:
            words = [it for it in lastWords if it.startswith(self.buffer)]
            
        #print("WORDS", words)
        
        #display all looked up words
        self.displayPopup(words) # close after some time or selection/keypress
#        self.lastLookups[self.buffer] = words #make copy of string for key ?
#        self.oldbuffer = str(self.buffer)
    
    def lookupMembers(self):
        words = []
        self.buffer = "".join(str(i) for i in self.buflist).lstrip()
        
        if self.buffer in self.identifiers:
            cl = self.identifiers[self.buffer]
            if isinstance(cl, Class):
                if self.buffer in cl.local_vars:
                    words.append(self.buffer)
                if self.buffer in cl.local_funcs:
                    words.append(self.buffer + "(")
                if self.buffer in cl.local_classes:
                    words.append(self.buffer + ".")
        self.buffer = ""
        self.buflist = []            
        return words   
                    
    def displayPopup(self, words):
        #sort it by category (class, function, var, constant, keyword....) first, then alpabetically
        #s = sorted(words, key=itemgetter(1))     # sort on value first
        #disp = sorted(s, key=itemgetter(0))      # now sort that on key
        if len(words) > 0:
            disp = sorted(words)
            #toPopup(disp)
            print("POPUP", disp)
            
            items = []
            bpy.context.edit_text.suggestions.clear()
            for d in disp:
                prop = bpy.context.edit_text.suggestions.add()
                prop.name = d
            
            bpy.ops.wm.call_menu(name = "text.popup")
        
       
    def modal(self, context, event):
        
        #add new entry to identifier list
        if 'MOUSE' not in event.type and event.value == 'PRESS':
            print(event.type, event.value)
        if event.shift:
            print("SHIFT")
        
        if event.type == 'RET' and event.value == 'PRESS':
            self.parseIdentifier()
            
        elif event.type == 'ESC':
            print("... autocompleter stopped")
            return {'CANCELLED'}
        
#        #detect variable declaration, add lhs to identifiers, look up rhs now  
#        elif event.type == '=':
#             self.isRhs = True
#             
#             if self.buffer != "": # if we didnt  press space before =, create lhs now
#                self.addIdentifier()
                
        #do lookups here
        elif event.type == 'PERIOD' and event.value == 'PRESS' and not event.shift:
            #look up all members of class/module of variable, depending on chars
            self.lookupIdentifier(self.lookupMembers())
#            
        elif event.type == '(':
            #look up parameters of function
            #self.lookupParameters()
            pass
#        
#        elif event.type == '[':
#            #look up keys in dictionary /indexable class ???            
#            #self.lookupDictKeys()
#            pass
#        
        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            #delete last lookup structure (sample, ...)
            #remove last char from buffer, do lookup again
            if len(self.buflist) > 0:
                self.buflist.pop()
                if len(self.buflist) > 0:
                    self.lookupIdentifier()
        
        #detect scope/function/class declaration, if not def and not class -> unnamed scope
#        elif event.type == ':':
#            #check for defs/classes in buffer
#            #remove leading whitespace...
#            if self.buffer.startswith("def") or self.buffer.startswith("class"):
#                #name = nonwhitespace until "("
#                #params = all until ")"
#                #split by comma, remove whitespace
#                #params (store with name, paramlist)
#                
#                decl = []
#                openbr = self.buffer.split('(')
#                name = openbr[0].split(' ')[1]
#                decl.append(name)
#                
#                closedbr = openbr.split(')')[0]
#                params = closedbr.split(',')
#                for p in params:
#                    #strip whitespace
#                    decl.append(p)
#                    #treat kwargs too !! and ctors are methods!! with classname -> __init__ must be checked
#                      
#                #same with class, here is superclass between ()
#               
#            #else do nothing, : is a delimiter and scope has no name, but look in active scope first
        
           
        elif ((event.type in ('A', 'B', 'C', 'D', 'E', 
                            'F', 'G', 'H', 'I', 'J',
                            'K', 'L', 'M', 'N', 'O',
                            'P', 'Q', 'R', 'S', 'T',
                            'U', 'V', 'W', 'X', 'Y',
                            'Z', 'ZERO','ONE', 'TWO',
                            'THREE', 'FOUR', 'FIVE',
                            'SIX', 'SEVEN','EIGHT', 
                            'NINE', 'MINUS',
                            'SPACE')) or \
                            (event.type == 'PERIOD' and \
                             event.shift)) and event.value == 'PRESS': 
            #catch all KEYBOARD events here....except (python) operators
            #maybe check whether we are run inside text editor
            
            #obviously this is called BEFORE the text editor receives the event. 
#            char = event.type #very hacky, better fetch it from the editor... ?
#            if not event.shift:
#                char = char.lower()
#            
#            #handle = and : and ( and ) and ., better read them AFTER typing from editor... or get it from locale at least
#            if event.shift:
#                if event.type == 'ZERO':
#                    char = '='
#                elif event.type == 'MINUS':
#                    char = '_'
#                elif event.type == 'EIGHT':
#                    char = '('
#                elif event.type == 'NINE':
#                    char = ')'
#                elif event.type == 'PERIOD':
#                    char = '
            char = event.unicode
#            print("CHAR", char)
                   
            text = context.edit_text #are we in the right context ?
            line = text.current_line
            pos = text.current_character
            #print(line, pos) 
            
            #char = line.body[pos]
            #watch copy and paste ! must add all pasted chars to buffer and separate by space TODO
            self.buflist.append(char)
            
            
            #also do word lookup, maybe triggered by a special key for now... 
            #start a timer, re-init it always, and accumulate a buffer
            #if timer expires, pass oldbuffer and buffer to lookup function, oldbuffer = buffer
            if len(self.buflist) > 0:
                self.lookupIdentifier()
            
            #how to end the op ?
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        
        text = context.edit_text
        self.module = Module(text.name.split(".")[0]) #better: filepath, if external
        print(self.module.name, self.module.char_pos)
        self.activeScope = self.module
        context.window_manager.modal_handler_add(self)
        print("autocompleter started...")
     
        return {'RUNNING_MODAL'}
       

def register():
    bpy.utils.register_class(AutoCompletePopup)
    bpy.utils.register_class(AutoCompleteOperator)
    bpy.types.Text.suggestions = bpy.props.CollectionProperty(
                            type = bpy.types.PropertyGroup, 
                            name = "suggestions")


def unregister():
    bpy.utils.unregister_class(AutoCompleteOperator)
    bpy.utils.unregister_class(AutoCompletePopup)


if __name__ == "__main__":
    register()

bpy.ops.text.autocomplete('INVOKE_DEFAULT')
    
#text = bpy.context.edit_text
#print(text.name) 
#print(__file__)
#currentDir = path.abspath(os.path.split(__file__)[0])  
#print(currentDir)
#line = text.current_line
#char = text.current_character
#print("char", line.body[char]) 

#strg = " a = b == c "
#print(strg.split("="))
#p = re.compile("=")
#m = p.search(strg, 0)
#print(m.start(0))



