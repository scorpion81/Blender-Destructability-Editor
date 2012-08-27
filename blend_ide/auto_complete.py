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
#     make addon out of this (partially done)

#     integrate nicely: create datastructures automatically (on text open), enable/disable via checkbox (maybe
#     then load datastructures), end modal operator with other operator/gui event ?

#     make menu disappear when i continue typing (change focus) (done)

#     correctly replace previously typed text by suggestion (partially done)

#     handle class member display correctly after pushing "PERIOD" (done)

#     categorize items: Class, Function, Variable at least

#     handle imports, fill datastructure with all imported scopes (classes, functions, modules and vars visible, local vars relevant 
#     for own code only - need to parse imports AND importable stuff (module handling, parse dir for that ?), importable as new
#     datastructure

#     test unnamed scopes, maybe do not store them (unnecessary, maybe active scope only? for indentation bookkeeping) (partially done)

#     make autocomplete info persisent, maybe pickle it, so it can be re-applied to the file (watch versions, 
#     if file has been changed (not necessary, will be parsed in dynamically, but maybe for big files ?)

#     externally, continue using or discard or rebuild(!) by parsing the existing code (partially done) automate this

#     fix buffer behavior, must be cleared correctly, some state errors still (partially done)

#     substitute operator, or function in autocomplete ? buffer is in op, hmm, shared between ops or via text.buffer stringprop
#     delete buffer content from text(select word, cut selected ?) and buffer itself and replace buffer content and insert into 
#     text (done)

#     make new lookups on smaller buffers, on each time on initial buffer

#     if any keyword before variable, same line, do not accept declaration with = (would be wrong in python at all)
#     hmm are those keyword scopes ?, no unnamed... and type = scope

#     parse existing code line by line after loading(all) or backspace (current line) (partially done)

#    BIG todo: make usable for any type of text / code   

#    parseLine benutzen dort wird der indent gemessen! evtl bei parseIdentifier keinen buffer benutzen sondern die Zeile
#    buffer nur für den Lookup benutzen !! auch nicht indent auf -1 setzen und dann current char ermitteln... (done)
 
#    scope parsing: check for \ as last char in previous lines, if there, prepend it to buffer !!!
#    substitution, preserve whitespaces before inserted text 

#    scope, special cases: higher class, function(?) names not usable as lhs ! only rhs (its usable both!)
#                          higher declaration: if isinstance(parent, Class) prepend self in choice ! (or check for it)
#                          or if startswith(__) static vars, usable with className only (check it, both lhs and rhs)
#    evaluate self, and dotted stuff, or simply create entry for it ?, dot -> if available, find object

#    exclude those entries from suggestions, which match completely with the buffer entry. 
#    watch for comma separated assignments, those are multiple identifiers, which need to be assigned separately !!

#    if only one matching entry in autocomplete suggestions, then substitute automatically !!
#    first restore menu functionality  with self drawn menu!! (done)  
#    lookup with dots, commas: always get the last element in sequence only after detecting . or , (when typing)
#    when parsing, evaluate dotted or take last part always (or leave it as is ?) and with comma watch whether ret type count
#    types match and assign one after other

#    take special care with lambdas, generators, list comprehensions ? or simply eval them

#    parenthesis: open parameter sequences in menu, and close sucessively entered params (highlight them separately,
#    do similar with brackets ([]), eval indexing or show possible keys (dicts) or range of indexes (list)

#    caution with re-setting/deleting(!!) variables, exec / eval must re-parse the variables too, and delete identifier
#    list before

#    manage fully qualified variable names internally, but cut all off whats already before the last dot
#    do not let fully qualified names pop up, prepend dotted types in internal rep, and at lookup check 
#    activeScope.type as well, if . occurs


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
import bgl
import blf


#encapsulate drawing and functionality of a menu
#select callback with parameter tuple
class Menu:
    
    color = (0.2, 0.2, 0.2, 1.0)
    hColor = (0.02, 0.4, 0.7, 1.0)
    textColor = (1.0, 1.0, 1.0, 1.0)
    width = 6 # get that from font object ?
    height = 11
    margin = 10
    pos_x = 0
    pos_y = 0
    max = 0
    highlighted = ""
    shift = int(margin / 2)
    index = -1
    
    def __init__(self, items):
        self.items = items
        self.itemRects = {}
    
    def highlightItem(self, x, y):
        #self.open(self.pos_x, self.pos_y)
        self.highlighted = ""
        for it in self.itemRects.items():
            ir = it[1] 
            if x >= ir[0] and x <= ir[2] and \
               y >= ir[1] and y <= ir[3]:
                #print(x, y, ir)
                self.highlighted = it[0]
                self.index = self.items.index(it[0])
                break
                    
        
    def pickItem(self):
        
        if self.highlighted != "":
            bpy.ops.text.substitute(choice = self.highlighted)
            
    def previousItem(self):
        if self.index > 0:
            self.index -= 1
            self.highlighted = self.items[self.index]
    
    def nextItem(self):
        
        if self.index < len(self.items) - 1:
            self.index += 1
            self.highlighted = self.items[self.index]
       
    def draw(self, x, y):
         
        #memorize position once
        if self.pos_x == 0:
            self.pos_x = x
        
        if self.pos_y == 0:
            self.pos_y = y
        
        #store rect of each item    
        if len(self.itemRects) == 0:
            self.max = 0
            i = 0
            for it in self.items:
                if len(it) > self.max:
                    self.max = len(it)
            
            width = self.max * self.width
            
            for it in self.items:
                rect_x = x - self.margin
                rect_y = y - i * (self.height + self.margin) 
                     
                self.itemRects[it] = (rect_x, rect_y, 
                                      rect_x + width + 2*self.margin, 
                                      rect_y + self.height + self.margin)
                i += 1
            
        self.open(self.pos_x, self.pos_y)     
    
    def open(self, x, y):
        
        if len(self.items) == 0:
            return
         
        width = self.max * self.width        
        
        #menu background
        bgl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        bgl.glRecti(x - self.margin, y - (self.height + self.margin) * (len(self.items)-1) - self.margin , 
                    x + width + self.margin, y + self.height + self.margin - self.shift)
        
        if self.highlighted != "":
            ir = self.itemRects[self.highlighted]    
            bgl.glColor4f(self.hColor[0], self.hColor[1], self.hColor[2], self.hColor[3])
            bgl.glRecti(ir[0], ir[1] - self.shift, ir[2], ir[3] - 2 * self.shift)
            #bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        
        font_id = 0  # XXX, need to find out how best to get this.        
        bgl.glColor4f(self.textColor[0], self.textColor[1], self.textColor[2], self.textColor[3])
        
        for it in self.items:
            rect = self.itemRects[it]
            
            #if it == self.highlighted:
            #    bgl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
              
            blf.position(font_id, float(rect[0] + self.margin), float(rect[1]), 0) # check for boundaries ?
            blf.size(font_id, self.height, 72)
            blf.draw(font_id, it)
            
            #if it == self.highlighted:
            #   bgl.glColor4f(self.textColor[0], self.textColor[1], self.textColor[2], self.textColor[3])
            
        # restore opengl defaults
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        
         
class Declaration:
   
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.indent = 0
        self.parent = None
       
    def __str__(self):
        return self.type 
    
    @staticmethod
    def createDecl(name, typename, opdata):
        
        #if "." in name:
        #    name = opdata.parseDotted(name)
            #name = name.split(".")[-1].strip()
            
        v = Declaration(name, typename)
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
        
    
    @staticmethod
    def create(name, typename, opdata):
        
        #exec/compile: necessary to "create" live objects from source ?
        #code = bpy.types.Text.as_string(bpy.context.edit_text)
        code = bpy.context.edit_text.as_string()
        #print(code)
        exec(compile(code, '<string>', 'exec'))
        
        #g = globals()
        #l = locals()
        
        #print("LOCALS", l)
        
        ret = eval(typename)         
        typ = type(ret).__name__
        print("TYPE", typ)
        
        if typ == "tuple" and isinstance(name, list):
            for i in range(0, len(name)): #name list can be shorter, might not be interested in all ret vals
                Declaration.createDecl(name[i].strip(), type(ret[i]).__name__, opdata)
        elif isinstance(name, str):
            Declaration.createDecl(name, typ, opdata)        
        
        
  
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
    
    @staticmethod
    def create(opdata):
        #Case 4: Anonymous scope declaration: after SPACE/ENTER check for :        
        s = Scope("", "scope")
        if opdata.indent >= opdata.activeScope.indent:
            opdata.activeScope.declare(s)
            s.indent = opdata.indent + 4 
            opdata.activeScope = s
            print("scope created") 
        

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
            #cant support classes in unnamed scopes and functions this way (makes this sense?)
            parent = c
            pstr = ""
            while parent.parent != None and isinstance(parent.parent, Class):
                parent = parent.parent
                pstr = parent.name + pstr
            
            if pstr != "":
                print("PSTR", pstr)
                code = bpy.context.edit_text.as_string()
                exec(compile(code, '<string>', 'exec'))     
                opdata.globals[name] = eval(pstr) 
                #print(opdata.activeScope)
                    
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
   # type = bpy.props.StringProperty(name = "type")
   # indent = bpy.props.IntProperty(name = "indent")
    
    def execute(self, context):
        #easy(?) way to delete entered word, but watch this for classes and functions (only select back to period), maybe this is done
        #already...
        
        isObject = False
        line = context.edit_text.current_line
        pos = context.edit_text.current_character
        print("LINEPOS", line, pos)
        
        char = line.body[pos-1]
        if char not in (".", " "): #do not remove variable before . when choosing member after entering .
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
        
        
#class AutoCompletePopup(bpy.types.Menu):
#    bl_idname = "text.popup"
#    bl_label = ""
#       
#    def draw(self, context):
#        layout = self.layout
#        entries = context.edit_text.suggestions
#        
#        for e in entries:
#            layout.operator("text.substitute", text = e.name).choice = e.name
                                   
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
    mouse_x = 0
    mouse_y = 0
    menu = None
    caret_x = 0
    caret_y = 0
    globals = None
    
    def draw_popup_callback_px(self, context):
        
        if self.menu != None:
            self.menu.draw(self.mouse_x, self.mouse_y)
        
    def cleanup(self):
        self.typedChar = []
        self.module = None
        self.activeScope = None
        self.lhs = ""
        self.identifiers = {}
        self.indent = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.menu = None
        self.caret_x = 0
        self.caret_y = 0
        self.globals = None
        
        #TODO remove this from context
        bpy.context.edit_text.suggestions.clear()
        bpy.context.edit_text.buffer = ""
        bpy.context.region.callback_remove(self._handle)
    
    def trackScope(self):
        print("TRACKSCOPE", self.indent, self.activeScope.indent)
        while self.indent < self.activeScope.indent:
            if self.activeScope.parent != None:
                self.activeScope = self.activeScope.parent
            else:
                self.activeScope = self.module
                break
        
    
    def parseCode(self, codetxt): 
        for l in codetxt.lines:
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
        if "," in lhs:
            lhs = line.split(",")
            
        rhs = line[index+1:].strip()
        return lhs, rhs    
    
    def parseLine(self, line):
        # ignore comments, do that at typing too!!
        self.indent = 0 
        
        if "#" in line:
            line = line.split("#")[0]
        
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
            
        elif line.endswith(":"):
            Scope.create(self)
    
    def parseDotted(self, buffer):
        
        ri = buffer.rindex(".")
        dotted = buffer[:ri]
        buffer = buffer[ri+1:]
    
        try: 
            code = bpy.context.edit_text.as_string()
            #print(code)
            exec(compile(code, '<string>', 'exec'))
    
            print("LOCALS", locals()) 
            #print("GLOBALS", globals())    
            typename = type(eval(dotted)).__name__
            print("TYPENAME", typename)
            if typename in self.identifiers:
                self.activeScope = self.identifiers[typename]
        except NameError:
            raise
        except KeyError:
            raise
        except Exception:
            pass
        finally:
            return buffer
            
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
        
        bpy.context.edit_text.buffer = ""
    
    def testScope(self, declaration):
        print("TESTSCOPE", self.activeScope.name, declaration.name)
        
        if self.activeScope != None:
            return declaration.name in self.activeScope.local_funcs or \
                   declaration.name in self.activeScope.local_vars or \
                   declaration.name in self.activeScope.local_classes
        else:
            return False    
    
    def testIndent(self, declaration):
  
        if isinstance(declaration, Function) or isinstance(declaration, Class) or \
        isinstance(declaration, Scope):
            print("TESTINDENT", self.indent, declaration.indent)
            return self.indent >= (declaration.indent - 4) and self.testScope(declaration)# the "outer" indent
        elif isinstance(declaration, Declaration): 
            print("TESTINDENT", self.indent, declaration.indent)   
            return self.indent >= declaration.indent and self.testScope(declaration)
        else:
            return False
                    
    def lookupIdentifier(self, lastWords = None):
        
        #self.lhs = ""
           
        if len(self.typedChar) > 0:
            char = self.typedChar[0]
        else:
            char = ""
        
        if self.lhs == "" and "." not in bpy.context.edit_text.buffer and "." != char:    
            bpy.context.edit_text.buffer = bpy.context.edit_text.current_line.body
            l1 = len(bpy.context.edit_text.buffer)
            bpy.context.edit_text.buffer = bpy.context.edit_text.buffer.lstrip()
            l2 = len(bpy.context.edit_text.buffer)
            self.indent = l1-l2
            print("INDENT SET", self.indent, self.lhs, bpy.context.edit_text.buffer)
        
        #add char later...
        #if char != ".":
        bpy.context.edit_text.buffer += char
        bpy.context.edit_text.buffer = bpy.context.edit_text.buffer.lstrip()
        
        print("lookupbuf", bpy.context.edit_text.buffer)
        
        if bpy.context.edit_text.buffer == "" and lastWords == None:
            return
        
        #if period/members: first show all members, then limit selection to members and so on
        #must pass/store lastWords selection, together with lastBuffer ?
        
        #dynamically get the last of . and , lists on lhs of =
        buffer = bpy.context.edit_text.buffer
        
        if "," in buffer and self.lhs == "":
            sp = buffer.split(",")
            buffer = sp[-1]
        #if "." in buffer and self.lhs == "":
        #    buffer = self.parseDotted(buffer)
                 
        #    if char == ".":
        #        bpy.context.edit_text.buffer += char
        #        buffer += char
            
        #only the NEW string compared to the last buffer is relevant
        #to look it up inside a subset/subdict of items
        words = []
        if lastWords == None:
            #if self.oldbuffer in self.lastLookups:
            #    lastWords = self.lastLookups[self.oldbuffer] #its a list only
            #    words = [it for it in lastWords if it.startswith(bpy.context.edit_text.buffer)]
            #else:
            lastWords = self.identifiers
            words = [it[0] for it in lastWords.items() if it[0].startswith(buffer) and \
                    (it[1] == 'keyword' or self.testIndent(it[1])) and it[0] != buffer]
        else:
            #print("OKKK")
            #words = [it for it in lastWords if it.startswith(bpy.context.edit_text.buffer)]
            words = lastWords
            
        #print("WORDS", words)
        
        #display all looked up words
        self.displayPopup(words) # close after some time or selection/keypress
#        self.lastLookups[bpy.context.edit_text.buffer] = words #make copy of string for key ?
#        self.oldbuffer = str(bpy.context.edit_text.buffer)
        self.activeScope = self.module
        
    def lookupMembers(self):
        words = []
       # self.tempBuffer = "".join(str(i) for i in self.buflist).lstrip()
        #print("TEMP", self.tempBuffer)
        
        buffer = bpy.context.edit_text.buffer
        #if "." in buffer:
        #    buffer = self.parseDotted(buffer)
        
        if buffer in self.identifiers:
            cl = self.identifiers[buffer]
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
            self.menu = Menu(sorted(words))
            #toPopup(disp)
            print("POPUP", self.menu.items)
            
            
            
            #items = []
            #bpy.context.edit_text.suggestions.clear()
            #for d in disp:
            #    prop = bpy.context.edit_text.suggestions.add()
            #    prop.name = d
                
           # bpy.ops.wm.call_menu(name = "text.popup")
    
                 
    def modal(self, context, event):
        
        try:
            
            context.area.tag_redraw()
            self.mouse_x = event.mouse_region_x
            self.mouse_y = event.mouse_region_y
            
            #doesnt work because i cant find out which line is the topmost in the display
            #line_index = context.edit_text.lines.values().index(context.edit_text.current_line)
            #self.caret_x = context.region.x + context.edit_text.current_character * 6
            #self.caret_y = context.region.y + line_index * 11
            
            if event.type == 'MOUSEMOVE':
                if self.menu != None:
                    self.menu.highlightItem(self.mouse_x, self.mouse_y)
            
            if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
                self.menu = None
                return {'RUNNING_MODAL'}
                
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                if self.menu != None:
                    self.menu.pickItem()
                    self.menu = None
                    return {'RUNNING_MODAL'} #do not pass the event ?
            
            if event.type == 'DOWN_ARROW' and event.value == 'PRESS':
                if self.menu != None:
                    self.menu.nextItem()
                    return {'RUNNING_MODAL'}
                    
            
            if event.type == 'UP_ARROW' and event.value == 'PRESS':
                if self.menu != None:
                    self.menu.previousItem()
                    return {'RUNNING_MODAL'}        
                
            #add new entry to identifier list
            if 'MOUSE' not in event.type and event.value == 'PRESS':
                print(event.type, event.value)
            
           
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
                if self.menu != None:
                    self.menu.pickItem()
                    self.menu = None
                    return {'RUNNING_MODAL'}
                
                self.parseIdentifier()
                self.indent = 0
                
            elif event.type == 'ESC':
                
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
                if event.unicode == ".":
                    self.indent += 4
                    
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
                #if event.type in ('BACK_SPACE', 'LEFT_ARROW', 'RIGHT_ARROW'): 
                    self.indent = 0
                    self.menu = None
                       
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
                #self.indent = 0
                self.menu = None
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
            self.cleanup() # maybe to finally ?
            #self.report({'ERROR'}, "Autocompleter stopped because of exception: " + str(e))
            raise
    
    def invoke(self, context, event):
        
        text = context.edit_text
        self.module = Module(text.name.split(".")[0]) #better: filepath, if external
        print(self.module.name, self.module.indent)
        self.activeScope = self.module
        context.window_manager.modal_handler_add(self)
        self._handle = context.region.callback_add(self.draw_popup_callback_px, (context,), 'POST_PIXEL')
        self.globals = globals()
       
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
    #bpy.utils.register_class(AutoCompletePopup)
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
   # bpy.utils.unregister_class(AutoCompletePopup)
    bpy.utils.unregister_class(SubstituteTextOperator)
    
    del bpy.types.Text.suggestions
    del bpy.types.Text.buffer
    del bpy.types.Text.bufferReset
    del bpy.types.Text.autocomplete_enabled 

if __name__ == "__main__":
    register()
    #started by run script...
    bpy.ops.text.autocomplete('INVOKE_DEFAULT')
    