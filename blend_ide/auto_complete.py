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
#     handle imports, fill datastructure with all imported scopes
#     test unnamed scopes, maybe do not store them (unnecessary, maybe active scope only? for indentation bookkeeping)
#     make autocomplete info persisent, maybe pickle it, so it can be re-applied to the file (watch versions, if file has been changed
#     externally, continue using or discard or rebuild(!) by parsing the existing code
#     fix buffer behavior, must be cleared correctly, some state errors still
#     substitute operator, or function in autocomplete ? buffer is in op, hmm, shared between ops or via text.buffer stringprop
#     delete buffer content from text(select word, cut selected ?) and buffer itself and replace buffer content and insert into text
#     make new lookups on smaller buffers, on each time on initial buffer
#     if any keyword before variable, same line, do not accept declaration with = (would be wrong in python at all)

import bpy
#import re

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

class Function(Scope):
    
    paramlist = []
    
    def __init__(self, name, paramlist):
        super().__init__(name)
        self.paramlist = paramlist
        
    def declare(self, declaration):
        super().declare(declaration)
 
class Class(Function):
    
    def __init__(self, name, superclasses):
        super().__init__(name, superclasses)
    
    def declare(self, declaration):
        super().declare(declaration)
    

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
            
class SubstituteTextOperator(bpy.types.Operator):
    bl_idname = "text.substitute"
    bl_label = "Substitute Text"
    
    choice = bpy.props.StringProperty(name = "choice")
    
    def execute(self, context):
        #easy(?) way to delete entered word, but watch this for classes and functions (only select back to period), maybe this is done
        #already...
        
        isObject = False
        line = context.edit_text.current_line
        pos = context.edit_text.current_character
        print(line, pos)
        
        char = line.body[pos-1]
        if char != ".": #do not remove variable before . when choosing member after entering .
           bpy.ops.text.select_word()    
           #bpy.ops.text.cut()
           line = context.edit_text.current_line
           pos = context.edit_text.current_character
           char = line.body[pos]
           if char == ".":
               isObject = True
           
        
        context.edit_text.buffer = self.choice
        context.edit_text.bufferReset = True
        
        if isObject:
            insert = "." + self.choice 
        else:
            insert = self.choice
               
        bpy.ops.text.insert(text = insert)
        return {'FINISHED'}    
        
        
class AutoCompletePopup(bpy.types.Menu):
    bl_idname = "text.popup"
    bl_label = ""
       
    def draw(self, context):
        layout = self.layout
        entries = context.edit_text.suggestions
        
        for e in entries:
            layout.operator("text.substitute", text = e.name).choice = e.name
                                   
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
    oldbuffer = ""
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
        bpy.context.edit_text.buffer = "".join(str(i) for i in self.buflist).lstrip()
        print("BUFFER", bpy.context.edit_text.buffer)
        
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
        if "=" in bpy.context.edit_text.buffer:
            s = bpy.context.edit_text.buffer.split('=')
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
        elif bpy.context.edit_text.buffer.startswith("def") or bpy.context.edit_text.buffer.startswith("class"):
            name = ""
            params = []
            
            openbr = bpy.context.edit_text.buffer.split('(')
            name = openbr[0].split(' ')[1]
            
            closedbr = openbr[1].split(')')[0]
            psplit = closedbr.split(',')
            for p in psplit:
                #strip whitespace
                params.append(p.strip())
            
            if bpy.context.edit_text.buffer.startswith("def"):
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
        elif bpy.context.edit_text.buffer.endswith(":"):
            scope = Scope("")
            if scope.char_pos > self.activeScope.char_pos:
                self.activeScope.declare(scope)
                self.activeScope = scope 
        
     
        self.buflist = []
                     
    def lookupIdentifier(self, lastWords = None):
        
        bpy.context.edit_text.buffer = "".join(str(i) for i in self.buflist).lstrip()
        print("lookupbuf", bpy.context.edit_text.buffer)
        
        #if period/members: first show all members, then limit selection to members and so on
        #must pass/store lastWords selection, together with lastBuffer ?
        
        #only the NEW string compared to the last buffer is relevant
        #to look it up inside a subset/subdict of items
        words = []
        if lastWords == None:
            #if self.oldbuffer in self.lastLookups:
            #    lastWords = self.lastLookups[self.oldbuffer] #its a list only
            #    words = [it for it in lastWords if it.startswith(bpy.context.edit_text.buffer)]
            #else:
            lastWords = self.identifiers
            words = [it[0] for it in lastWords.items() if it[0].startswith(bpy.context.edit_text.buffer)]
        else:
            words = [it for it in lastWords if it.startswith(bpy.context.edit_text.buffer)]
            
        #print("WORDS", words)
        
        #display all looked up words
        self.displayPopup(words) # close after some time or selection/keypress
#        self.lastLookups[bpy.context.edit_text.buffer] = words #make copy of string for key ?
#        self.oldbuffer = str(bpy.context.edit_text.buffer)
    
    def lookupMembers(self):
        words = []
        #bpy.context.edit_text.buffer = "".join(str(i) for i in self.buflist).lstrip()
        
        if bpy.context.edit_text.buffer in self.identifiers:
            cl = self.identifiers[bpy.context.edit_text.buffer]
            if isinstance(cl, Class):
                [words.append(v) for v in cl.local_vars]
                [words.append(v) for v in cl.local_funcs]
                [words.append(v) for v in cl.local_classes]
        #bpy.context.edit_text.buffer = ""
        self.buflist = [] 
        
        print(words)           
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
            char = event.unicode
                   
#            text = context.edit_text #are we in the right context ?
#            line = text.current_line
#            pos = text.current_character
            #print(line, pos) 
            
            #char = line.body[pos]
            #watch copy and paste ! must add all pasted chars to buffer and separate by space TODO
            if context.edit_text.bufferReset: 
                self.buflist = []
                context.edit_text.bufferReset = False
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
    bpy.utils.register_class(SubstituteTextOperator)
    bpy.utils.register_class(AutoCompletePopup)
    bpy.utils.register_class(AutoCompleteOperator)
    bpy.types.Text.suggestions = bpy.props.CollectionProperty(
                            type = bpy.types.PropertyGroup, 
                            name = "suggestions")
    bpy.types.Text.buffer = bpy.props.StringProperty(name = "buffer")
    bpy.types.Text.bufferReset = bpy.props.BoolProperty(name = "bufferReset")


def unregister():
    bpy.utils.unregister_class(AutoCompleteOperator)
    bpy.utils.unregister_class(AutoCompletePopup)
    bpy.utils.unregister_class(SubstituteTextOperator)

if __name__ == "__main__":
    register()

#started by run script...
bpy.ops.text.autocomplete('INVOKE_DEFAULT')
    