# simple autocomplete:
#
# 1) run this file via runscript
# 
# 2) type code in another empty text
# 
# 3) try declaring variables, classes, functions
#
# 4) during typing, if you retype parts of known identifiers, a popup should open
#
# 5) choose option and it will be inserted into text
#
# 6) after object variables, enter . and member popup should open
# 
# 7) its all very alpha, in case of error: rerun auto_complete.py and in text to edited, 
#    press SHIFT+CTRL to load existing code and create autocomplete datastructures

#TODO 
#     make addon out of this

#     integrate nicely: create datastructures automatically (on text open), enable/disable via checkbox (maybe
#     then load datastructures), end modal operator with other operator/gui event ?

#     make menu disappear when i continue typing (change focus)

#     correctly replace previously typed text by suggestion (partially done)

#     handle class member display correctly after pushing "PERIOD" (done)

#     categorize items: Class, Function, Variable at least

#     handle imports, fill datastructure with all imported scopes (classes, functions, modules and vars visible, local vars relevant 
#     for own code only

#     test unnamed scopes, maybe do not store them (unnecessary, maybe active scope only? for indentation bookkeeping)

#     make autocomplete info persisent, maybe pickle it, so it can be re-applied to the file (watch versions, if file has been changed

#     externally, continue using or discard or rebuild(!) by parsing the existing code (partially done)

#     fix buffer behavior, must be cleared correctly, some state errors still (partially done)

#     substitute operator, or function in autocomplete ? buffer is in op, hmm, shared between ops or via text.buffer stringprop
#     delete buffer content from text(select word, cut selected ?) and buffer itself and replace buffer content and insert into text (done)

#     make new lookups on smaller buffers, on each time on initial buffer

#     if any keyword before variable, same line, do not accept declaration with = (would be wrong in python at all)

#     parse existing code line by line after loading(all) or backspace (current line) (partially done)

#    BIG todo: make usable for any type of text / code   

#    parseLine benutzen dort wird der indent gemessen! evtl bei parseIdentifier keinen buffer benutzen sondern die Zeile
#    buffer nur für den Lookup benutzen !! auch nicht indent auf -1 setzen und dann current char ermitteln...  

bl_info = {
    "name": "Python Editor Autocomplete",
    "author": "scorpion81",
    "version": (0, 1),
    "blender": (2, 6, 3),
    "api": 50083,
    "location": "Text Editor > Left Panel > Autocomplete",
    "description": "Simple autocompletion for Blender Text Editor (for Python only currently)",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development" } 

import bpy

class Declaration:
   
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.indent = 0
        self.parent = None
       
    def __str__(self):
        return self.type 
    
    @staticmethod
    def create(name, typename, opdata):
        
        #exec/compile: necessary to "create" live objects from source ?
        code = bpy.types.Text.as_string(bpy.context.edit_text)
        print(code)
        exec(compile(code, '<string>', 'exec'))
                 
        typ = type(eval(typename)).__name__
        print("TYPE", typ)
        v = Declaration(name, typ)
        #active module -> open file ? (important later, when treating different modules too)
        print("INDENT", opdata.indent, opdata.activeScope.indent, opdata.isValid(name))
        if opdata.indent >= opdata.activeScope.indent and opdata.isValid(name):
            print("SCOPE", opdata.activeScope)
            opdata.activeScope.declare(v) 
           # self.activeScope = v #variables build no scope
            v.indent = opdata.indent
            opdata.identifiers[name] = v
            opdata.lhs = ""
            [print(it[0], ":", it[1]) for it in opdata.identifiers.items()]
        
          
class Scope(Declaration):

    
    def __init__(self, name, type): #indentation creates new scope too, name can be empty here
        super().__init__(name, type)
        self.local_funcs = {}
        self.local_vars = {}
        self.local_classes = {}
        self.local_unnamed_scopes = []
        
    def declare(self, declaration):
        #add a new declaration
        # if its a variable, add to localvars
        # if its a scope, add to scopes
        
        declaration.parent = self
        #declaration.indent = self.indent + 4
        
        if isinstance(declaration, Class):
            self.local_classes[declaration.name] = declaration
        elif isinstance(declaration, Function):
            self.local_funcs[declaration.name] = declaration
        elif isinstance(declaration, Scope):
            self.local_unnamed_scopes.append(declaration)
        elif isinstance(declaration, Declaration):
            self.local_vars[declaration.name] = declaration
    
    def __str__(self):
        f = ""
        v = ""
        c = ""
        
        if len(self.local_funcs) > 0:
            #f = "".join(it[0] + ":" + str(it[1]) for it in self.local_funcs.items())
            f = "F " + str(len(self.local_funcs))
        if len(self.local_vars) > 0:    
            #v = "".join(it[0] + ":" + str(it[1]) for it in self.local_vars.items())
            v = "V " + str(len(self.local_vars))
        if len(self.local_classes) > 0:
            #print("LEN", len(self.local_classes))
            c = "C " + str(len(self.local_classes))    
            #c = "".join(it[0] + ":" + str(it[1]) for it in self.local_classes.items())
        
        return self.type + " " + f + " " + v + " " + c

class Function(Scope):
    
    def __init__(self, name, paramlist):
        super().__init__(name, "function") #must be evaluated to find out return type...
        self.paramlist = paramlist
        
    def declare(self, declaration):
        super().declare(declaration)
    
    def __str__(self):
        return super().__str__()
    
    @staticmethod
    def create(name, params, opdata):
        f = Function(name, params)
        if opdata.indent >= opdata.activeScope.indent and opdata.isValid(name):
            print("SCOPE", opdata.activeScope)
            opdata.activeScope.declare(f)
            f.indent = opdata.indent + 4
            opdata.activeScope = f
            opdata.identifiers[name] = f
            [print(it[0], ":", it[1]) for it in opdata.identifiers.items()]
            
        
 
class Class(Scope):
        
    def __init__(self, name, superclasses):
        super().__init__(name, "class")
        self.superclasses = superclasses
    
    def declare(self, declaration):
        super().declare(declaration)
    
    def __str__(self):
        return super().__str__()
    
    @staticmethod
    def create(name, superclasses, opdata):
        c = Class(name, superclasses)
        if opdata.indent >= opdata.activeScope.indent and opdata.isValid(name):
            print("SCOPE", opdata.activeScope)
            opdata.activeScope.declare(c)
            c.indent = opdata.indent + 4
            opdata.activeScope = c
            opdata.identifiers[name] = c
            [print(it[0], ":", it[1]) for it in opdata.identifiers.items()]

#list of that (imported) modules must be generated, and active module (__module__)
class Module(Scope):
    
    def __init__(self, name):
        super().__init__(name, "module")
        self.indent = 0
        #print("PRINT", self.indent, super().indent)
    
    def declare(self, declaration):
        if isinstance(declaration, Module):
            submodules.append(declaration) # make dict ?
        else:
            super().declare(declaration)
    
    def __str__(self):
        return super().__str__()
            
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
        print("LINEPOS", line, pos)
        
        char = line.body[pos-1]
        if char != ".": #do not remove variable before . when choosing member after entering .
           bpy.ops.text.select_word()    
           #bpy.ops.text.cut()
           line = context.edit_text.current_line
           pos = context.edit_text.current_character
           char = line.body[pos]
           if char in (".", " "):
               isObject = True
           
        
        context.edit_text.buffer = self.choice
        context.edit_text.bufferReset = True
        
        if isObject:
            insert = char + self.choice 
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
    bl_label = "Autocomplete"
    
    identifiers = {'if': 'keyword', 
                   'else': 'keyword'}
                 #    ... 
                 #   'str' : 'type' # more accurate: class, function, builtin
                 #    ...}
                 #    #varname : typename , WHICH class
                    
    typedChar = []
    oldbuffer = ""
    lastLookups = {} #?, backspace must delete sub-buffers, that is 2 indexes on (sorted) list
    module = None
    activeScope = None
    lhs = ""
    tempBuffer = ""
    indent = 0
    
    def cleanup(self):
        self.typedChar = []
        self.module = None
        self.activeScope = None
        self.lhs = ""
        self.identifiers = {}
        self.indent = 0
    
    def trackScope(self):
        print("TRACKSCOPE", self.indent, self.activeScope.indent)
        while self.indent < self.activeScope.indent:
            if self.activeScope.parent != None:
                self.activeScope = self.activeScope.parent
            else:
                self.activeScope = self.module
                break
        
    
    def parseCode(self, code):
        for l in code.lines:
            self.parseLine(l.body)
    
    
    def parseClass(self, line):
        beforeColon = line.split(":")
        name = beforeColon[0].split(' ')[1]
        return name
    
    def parseFunction(self, line):
        params = []
        openbr = line.split('(')
        name = openbr[0].split(' ')[1]
                
        closedbr = openbr[1].split(')')[0]
        psplit = closedbr.split(',')
        for p in psplit:
            #strip whitespace
            params.append(p.strip())
        
        return name, params
    
    def parseDeclaration(self, line):
        index = line.index("=")
        lhs = line[:index-1].strip()
        rhs = line[index+1:].strip()
        return lhs, rhs    
    
    def parseLine(self, line):
        # variable:
        l1 = len(line)
        line = line.lstrip()
        l2 = len(line)
        spaces = l1-l2
        self.indent = spaces
        self.trackScope()
        
        print(line)
        if "=" in line:
            lhs, rhs = self.parseDeclaration(line)
            Declaration.create(lhs, rhs, self)
        elif line.startswith("def"):
            name, params = self.parseFunction(line)
            Function.create(name, params, self)
        elif line.startswith("class"):
            if "(" not in line:
                name = self.parseClass(line)
                params = []
            else:
                name, params = self.parseFunction(line)
            
            Class.create(name, params, self)
            
        self.indent = 0    
            
    
    def handleImport(self):
        #add all types of import to identifiers...
        #print out current module, after declaration change scope.... must parse the currently used code
        pass
    
    def isValid(self, identifier):
        return not identifier in self.identifiers or self.identifiers[identifier] != "keyword" 
    
    def parseIdentifier(self):
        
        self.lhs = ""
        
        #first check if we have a new identifier which mustnt be a keyword...
        bpy.context.edit_text.buffer = bpy.context.edit_text.current_line.body
        print("BUFFER", bpy.context.edit_text.buffer)
        
        #go to parent scope if new indent is smaller, "unindent"
        #indent = bpy.context.edit_text.current_character
        self.parseLine(bpy.context.edit_text.buffer)
        
                          
        #Case 4: Anonymous scope declaration: after SPACE/ENTER check for :        
        #elif bpy.context.edit_text.buffer.endswith(":"):
        #    scope = Scope("", "")
        #    if scope.indent > self.activeScope.indent:
        #        self.activeScope.declare(scope)
        #        self.activeScope = scope 
        
    
    def testIndent(self, declaration):
        if isinstance(declaration, Declaration):
            print("TESTINDENT", self.indent, declaration.indent)
            if isinstance(declaration, Function) or isinstance(declaration, Class):
                return self.indent == (declaration.indent - 4) # the "outer" indent
            return self.indent == declaration.indent
        else:
            return False
                    
    def lookupIdentifier(self, lastWords = None):
        
        #self.lhs = ""
           
        if len(self.typedChar) > 0:
            char = self.typedChar[0]
        else:
            char = ""
        
        if self.lhs == "":    
            bpy.context.edit_text.buffer = bpy.context.edit_text.current_line.body
            l1 = len(bpy.context.edit_text.buffer)
            bpy.context.edit_text.buffer = bpy.context.edit_text.buffer.lstrip()
            l2 = len(bpy.context.edit_text.buffer)
            self.indent = l1-l2
        
        bpy.context.edit_text.buffer += char
        bpy.context.edit_text.buffer = bpy.context.edit_text.buffer.lstrip()
        
        print("lookupbuf", bpy.context.edit_text.buffer)
        
        if bpy.context.edit_text.buffer == "" and lastWords == None:
            return
        
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
            words = [it[0] for it in lastWords.items() if it[0].startswith(bpy.context.edit_text.buffer) and \
                    (it[1] == 'keyword' or self.testIndent(it[1]))]
        else:
            #print("OKKK")
            #words = [it for it in lastWords if it.startswith(bpy.context.edit_text.buffer)]
            words = lastWords
            
        #print("WORDS", words)
        
        #display all looked up words
        self.displayPopup(words) # close after some time or selection/keypress
#        self.lastLookups[bpy.context.edit_text.buffer] = words #make copy of string for key ?
#        self.oldbuffer = str(bpy.context.edit_text.buffer)
    
    def lookupMembers(self):
        words = []
       # self.tempBuffer = "".join(str(i) for i in self.buflist).lstrip()
        #print("TEMP", self.tempBuffer)
        
        if bpy.context.edit_text.buffer in self.identifiers:
            cl = self.identifiers[bpy.context.edit_text.buffer]
            if isinstance(cl, Class):
                [words.append(v) for v in cl.local_vars]
                [words.append(v) for v in cl.local_funcs]
                [words.append(v) for v in cl.local_classes]
            elif isinstance(cl, Declaration):
                typ = cl.type
                cl = self.identifiers[typ]
                [words.append(v) for v in cl.local_vars]
                [words.append(v) for v in cl.local_funcs]
                [words.append(v) for v in cl.local_classes]
                    
        #bpy.context.edit_text.buffer = ""
        #self.buflist = [] 
        
        print("MEMBERZ", words)           
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
        
        try:
            #add new entry to identifier list
            if 'MOUSE' not in event.type and event.value == 'PRESS':
                print(event.type, event.value)
            
            #if event.type == 'LEFT_MOUSE' and event.value == 'PRESS':
                
            if event.shift:
                print("SHIFT")
            
            #hack, trigger parse manually, must be done with bpy.app. handler somehow (on change of text block)
            if event.shift and event.ctrl:
                #parse existing code to buildup data structure, what to do when code has syntax errors (it is execed to get types)
                #maybe avoid unnecessary compile steps
                print("Reading file...")
                self.parseCode(context.edit_text)
                print("... file read")
            
            elif event.type == 'RET' and event.value == 'PRESS':
                self.parseIdentifier()
                
            elif event.type == 'ESC':
                context.edit_text.suggestions.clear()
                context.edit_text.buffer = ""
                self.cleanup()
                
                print("... autocompleter stopped")
                return {'CANCELLED'}
            
            elif event.unicode == "=" and self.lhs == "" and event.value == 'PRESS':
                
                print("ASSIGN")
                context.edit_text.buffer += event.unicode 
                lhs, rhs = self.parseDeclaration(context.edit_text.buffer)
                self.lhs = lhs
                context.edit_text.buffer = ""
                    
            #do lookups here
            elif event.type == 'PERIOD' and event.value == 'PRESS' and not event.shift:
                #look up all members of class/module of variable, depending on chars
                self.typedChar.append(event.unicode) # . is part of name
                self.lookupIdentifier(self.lookupMembers())
                
                if len(self.typedChar) > 0:
                    self.typedChar.pop()
    #            
            #elif event.type == '(':
                #look up parameters of function
                #self.lookupParameters()
             #   pass
    #        
    #        elif event.type == '[':
    #            #look up keys in dictionary /indexable class ???            
    #            #self.lookupDictKeys()
    #            pass
    #        
            elif event.type in ('BACK_SPACE', 'LEFT_ARROW', 'RIGHT_ARROW', 'UP_ARROW', 'DOWN_ARROW') and event.value == 'PRESS':
                #delete last lookup structure (sample, ...)
                #remove last char from buffer, do lookup again
                if len(self.typedChar) > 0:
                    self.typedChar.pop()
                    
                #self.lookupIdentifier()
                       
            elif (((event.type in ('A', 'B', 'C', 'D', 'E',
                                'F', 'G', 'H', 'I', 'J',
                                'K', 'L', 'M', 'N', 'O',
                                'P', 'Q', 'R', 'S', 'T',
                                'U', 'V', 'W', 'X', 'Y',
                                'Z', 'ZERO','ONE', 'TWO',
                                'THREE', 'FOUR', 'FIVE',
                                'SIX', 'SEVEN','EIGHT', 
                                'NINE', 'MINUS', 'PLUS',
                                'SPACE', 'COMMA')) or \
                                (event.type == 'PERIOD' and \
                                 event.shift)) or (event.unicode in ["'", "#", "?", "+" ,"*"])) and event.value == 'PRESS': 
                #catch all KEYBOARD events here...
                #maybe check whether we are run inside text editor
                
                #obviously this is called BEFORE the text editor receives the event. so we need to store the typed char too.
                self.typedChar.append(event.unicode)
            
                #watch copy and paste ! must add all pasted chars to buffer and separate by space TODO
                #via MOUSE events and is_dirty/is_modified
                
                if context.edit_text.bufferReset:
                    #self.typedChar.pop()
                    self.tempBuffer += context.edit_text.buffer
                    context.edit_text.bufferReset = False
                #self.buflist.append(char)
                
                #also do word lookup, maybe triggered by a special key for now... 
                #start a timer, re-init it always, and accumulate a buffer
                #if timer expires, pass oldbuffer and buffer to lookup function, oldbuffer = buffer
                
                self.lookupIdentifier()
                
                if len(self.typedChar) > 0:
                    self.typedChar.pop()
                
                #how to end the op ?
            return {'PASS_THROUGH'}
        
        except Exception as e:
            # clean up after error
            print("Exception", e)
            context.edit_text.suggestions.clear()
            context.edit_text.buffer = ""
            self.cleanup()
            self.report({'ERROR'}, "Autocompleter stopped because of exception: " + str(e))
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        
        text = context.edit_text
        self.module = Module(text.name.split(".")[0]) #better: filepath, if external
        print(self.module.name, self.module.indent)
        self.activeScope = self.module
       # self.identifiers = {}
        context.window_manager.modal_handler_add(self)
       
        print("autocompleter started...")
     
        return {'RUNNING_MODAL'}

class AutoCompletePanel(bpy.types.Panel):
    bl_idname = 'auto_complete'
    bl_label = 'Autocomplete'
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
       # layout.prop(context.edit_text, "autocomplete_enabled", text = "Enabled",  event = True)
        layout.operator("text.autocomplete", text = "Enable")
        layout.label("disable with ESC")

def enablerUpdate(self, context):
    pass
               

def register():
    bpy.utils.register_class(SubstituteTextOperator)
    bpy.utils.register_class(AutoCompletePopup)
    bpy.utils.register_class(AutoCompleteOperator)
    
    bpy.types.Text.suggestions = bpy.props.CollectionProperty(
                            type = bpy.types.PropertyGroup, 
                            name = "suggestions")
    bpy.types.Text.buffer = bpy.props.StringProperty(name = "buffer")
    bpy.types.Text.bufferReset = bpy.props.BoolProperty(name = "bufferReset")
    bpy.types.Text.autocomplete_enabled = bpy.props.BoolProperty(name = "autocomplete_enabled")
    
    bpy.utils.register_class(AutoCompletePanel)


def unregister():
    bpy.utils.unregister_class(AutoCompletePanel)
    bpy.utils.unregister_class(AutoCompleteOperator)
    bpy.utils.unregister_class(AutoCompletePopup)
    bpy.utils.unregister_class(SubstituteTextOperator)
    
    del bpy.types.Text.suggestions
    del bpy.types.Text.buffer
    del bpy.types.Text.bufferReset
    del bpy.types.Text.autocomplete_enabled 

if __name__ == "__main__":
    register()
    #started by run script...
    bpy.ops.text.autocomplete('INVOKE_DEFAULT')
    