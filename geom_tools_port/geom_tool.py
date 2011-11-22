#!BPY
# -*- coding: latin-1 -*-


"""
Name: 'Geom Tool'
Blender: 248
Group: 'Mesh'
Tooltip: 'Geometric operations like projection or intersection.'
"""

#__author__  = "Guillaume 'GuieA_7' Englert"
#__version__ = "0.4 2009/01/26"
#__url__     = "Online doc , http://www.hybird.org/~guiea_7/"
#__email__   = "GuieA_7, genglert:hybird*org"
#__bpydoc__  = 

"""\
Do geometric operations:<br>
- projection (vertices-->face, vertices-->edge).<br>
- intersection(face/edges, faces/faces, edge/edge).<br>
- nearest plane.(be careful, slow algorithm)<br>
- distribute vertices regularly on a line, a curve or simply align them.<br>

Some tools have 'copy' and 'normal' versions.<br>
 eg: projection of a vertex on a face ; the 'normal' version moves the vertex,
  the 'copy' version create a new vertex (the projected point).

Some tools have 'cut' and 'normal' versions.<br>
 eg: intersection between an edge and a face; the normal version creates a new
  vertex (the intersection point), the 'cut' version cuts the edge into two new edges.
"""

################################################################################
#                                                                              #
#    GNU GPL LICENSE                                                           #
#    ---------------                                                           #
#                                                                              #
#    Copyright (C) 2006-2009: Guillaume Englert                                #
#                                                                              #
#    This program is free software; you can redistribute it and/or modify it   #
#    under the terms of the GNU General Public License as published by the     #
#    Free Software Foundation; either version 2 of the License, or (at your    #
#    option) any later version.                                                #
#                                                                              #
#    This program is distributed in the hope that it will be useful,           #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#    GNU General Public License for more details.                              #
#                                                                              #
#    You should have received a copy of the GNU General Public License         #
#    along with this program; if not, write to the Free Software Foundation,   #
#    Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.           #
#                                                                              #
################################################################################

################################################################################
# Thanks to :
# - Çetin Barkın Çelebican for the help on the new User Interface (see PanelUI)
################################################################################


################################################################################
# Importing modules
################################################################################

#from Blender import Redraw
#from Blender import Mesh, Redraw -> scene.update() ? Region/Area_tag.redraw()
#from Blender.Object import GetSelected -> object.select
#from Blender.Window import EditMode, GetAreaSize -> bpy.ops.editmode_toggle(), Area.width / height
#from Blender.Draw import Exit, Register, PupMenu, Label, PushButton, ESCKEY, QKEY  ->Operator invoke, event.ESCKEY, QKEY
#from Blender.Mathutils import Vector, DotVecs, CrossVecs, LineIntersect
#from Blender.Registry import GetKey, SetKey ?

from bpy.types import Region, Area, Object 
from bpy import ops, types, utils, data 
from mathutils import Vector
from mathutils.geometry import intersect_line_line, normal, area_tri
#from collections import OrderedDict
from . import geom_tool_math as gm
#from gm import EPSILON
#reload(gm) ###while coding/testing !!!

#from exceptions import Exception # ? Python 3.2 way ?

################################################################################
#                             CONSTANTS                                        #
################################################################################

#Masks
NOTHING    = 0
VERTS_FLAG = 1 #2**0
EDGES_FLAG = 2
FACES_FLAG = 4 #2**2

SCRIPTNAME    = 'GeomTool'
CONFKEY       = 'klass'
DEFAULT_CLASS = 'PopupUI'
EPSILON = gm.EPSILON

################################################################################
#                             GLOBALS                                          #
################################################################################

actions = []

################################################################################
#                              EXCEPTIONS                                      #
################################################################################

class GToolFatalError(Exception):
    """Fatal error, like no object selected."""
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg

class GToolGeomError(Exception):
    """Geometry error."""
    def __init__(self, msg, priority=0):
        Exception.__init__(self)
        self.msg      = msg
        self.priority = priority

    def __str__(self):
        return self.msg


################################################################################
#                              CLASS                                           #
################################################################################

class GToolAction(object):
    """Action that can do this module, like projection or intersection."""
    def __init__(self, function, label, tooltip, **kw):
        """Constructor.
        function: function object that do the action
        label: description of the action (for menu)
        tooltip: long description of the action (for tooltip)
        """
        self.function = function
        self.__label    = label
        self.__tooltip  = tooltip

        self.kwVals = []
        for key, val in kw.items():
            setattr(self, key, val)
            self.kwVals.append(val)

    def __call__(self, *args):
        return self.function(self, *args)

    label = property(lambda self: self.__label)
    tooltip = property(lambda self: self.__tooltip)
    

#-------------------------------------------------------------------------------

class UIInterface:
    """User interface base class"""
    klass_dict = {}

    def start(self):
        """Draw and start the User Interface."""
        pass

    def get_action(self):
        """Get the geometric action the user has chosen.
        return: a callable which take a Mesh object as argument.
        """
        raise NotImplementedError()

    def main(self):
        #init
       # is_editmode = EditMode()
        is_editmode = bpy.context.mode == 'EDIT_MESH'
        if is_editmode:
        #    EditMode(0)
            ops.object.mode_set(mode = 'OBJECT')

        try:
            #get selected object (or quit)
            #objs = GetSelected()
            objs = bpy.context.selected_objects
            if not objs:
                raise GToolFatalError("none selected object")

            if len(objs) > 1:
                raise GToolFatalError("only one object must be selected")

            obj = objs[0]
           # if obj.getType() != "Mesh":
            if obj.type != 'MESH':
                raise GToolFatalError("active object must be a mesh")

            #do the wanted action on the mesh
          #  mesh   = obj.getData(mesh=True)
            mesh = obj.data
            action = self.get_action()

            if action:
                action(mesh)

            ###########PROFILING#######
            #if action:
                #import hotshot, hotshot.stats
                #def foo():
                    #action(mesh)

                #filename = "geomtool.prof"
                #prof     = hotshot.Profile(filename)
                #prof.runcall(foo)
                #prof.close()

                #stats = hotshot.stats.load(filename)
                #stats.strip_dirs()
                #stats.sort_stats('time', 'calls')
                #stats.print_stats(30)
            ############################

        #Exceptions handlers
        except GToolFatalError as e:
            print(e)
            display_error(str(e))

        except GToolGeomError as e:
            print(e)

            if e.priority >= 1:
                display_error(str(e))

        except:
            import sys
            sys.excepthook(*sys.exc_info())
            display_error("An exception occured | (look at the terminal)")

        #finish
        if is_editmode:
            #EditMode(1)
            ops.object.mode_set(mode = 'EDIT')

#    @staticmethod
#    def get_UI_from_conf():
#        conf       = GetKey(SCRIPTNAME, True)
#        klass_name = DEFAULT_CLASS
#
#        if conf:
#            try:
#                klass_name = conf[CONFKEY]
#                assert isinstance(klass_name, str)
#            except Exception, e:
#                print "invalid registry??: ", e
#        else:
#            UIInterface.save_conf(DEFAULT_CLASS)
#
#        return UIInterface.klass_dict[klass_name]()
#
#    @staticmethod
#    def save_conf(ui_klass):
#        SetKey(SCRIPTNAME, {CONFKEY: ui_klass}, True)

#class PopupUI(UIInterface):
#    def start(self):
#        self.main()
#
#    def get_action(self):
#        """Ask to the user the action he wants.
#        return: None or a GToolAction object
#        """
#        menustr = "Geom tool%t"
#
#        for action in actions:
#            menustr += '|' + action.label
#
#        menustr += "|Use Panel UI (relaunch)"
#
#        ret = PupMenu(menustr)
#        if ret == -1: #Cancel
#            return None
#
#        if ret == len(actions) + 1: #Use Panel option
#            UIInterface.save_conf(PanelUI.__name__)
#            return None
#
#        return actions[ret-1]
#
#
#class PanelUI(UIInterface):
#    GEOM_EVENT_BASE = 1024
#    EVENT_EXIT = 10
#    EVENT_CHANGE_UI = 20
#
#    def start(self):
#        self._action = None
#        Register(self.draw, self.event, self.b_event)
#
#    def get_action(self):
#        return self._action
#
#    def draw(self):
#        #check to see if there's enough space for our buttons to fit and make sure they fit
#        #h for height, w for width, x for originx and y for originy
#        #this script uses a (7h+y) by (w+x) rectangle window in blender user space.
#
#        usage = ("Usage: to use this tool you must", "have the appropriate object(s)",
#                 "(vertex/edge/face) selected", "before pressing button.")
#
#        widgets_count = len(usage) + len(actions) + 2 #2 for 'stop' and 'change UI' buttons
#
#        h = 20; w = 180
#        x = 8;  y = 4
#
#        area_w, area_h = GetAreaSize()
#        if area_w < (x + w):
#            x = 0
#            w = area_w
#        if area_h < (y + h * widgets_count):
#            y = 0
#            h = area_h / widgets_count
#
#        y = y + h * (widgets_count - 1)
#
#        #usage help though there are tooltips in place
#        for text in usage:
#            Label(text, x, y, w, h)
#            y -= h
#
#        GEOM_EVENT_BASE = PanelUI.GEOM_EVENT_BASE
#        for offset, action in enumerate(actions):
#            #event id will be: GEOM_EVENT_BASE + offset
#            PushButton(action.label, GEOM_EVENT_BASE + offset, x, y, w, h, action.tooltip)
#            y -= h
#
#        PushButton("Use Popup UI (relaunch)", PanelUI.EVENT_CHANGE_UI, x, y,
#                   w, h, "Use the Popup menu interface (need relaunch)")
#
#        y -= h
#        PushButton("Exit", PanelUI.EVENT_EXIT, x, y, w, h, "Exit the script")
#
#    def event(self, event, value):
#        if event in (ESCKEY, QKEY) and not value:
#            Exit()
#
#    def b_event(self, event):
#        if event == PanelUI.EVENT_EXIT:
#            Exit()
#        elif event == PanelUI.EVENT_CHANGE_UI:
#            UIInterface.save_conf(PopupUI.__name__)
#            Exit()
#        else:
#            self._action = actions[event - PanelUI.GEOM_EVENT_BASE]
#            self.main()
#
#        Redraw()
#
##dammit I want class decorators (Python 2.6 inside) !!!
#UIInterface.klass_dict[PopupUI.__name__] = PopupUI
#UIInterface.klass_dict[PanelUI.__name__] = PanelUI
    
 

 
#bpy.utils.register_class(DialogOperator)
 
# Invoke the dialog when loading
#bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
 
#
#    Panel in tools region
#
#class DialogPanel(bpy.types.Panel):
#    bl_label = "Dialog"
#    bl_space_type = "VIEW_3D"
#    bl_region_type = "UI"
# 
#    def draw(self, context):
#        global theFloat, theBool, theString, theEnum
#        theFloat = 12.345
#        theBool = True
#        theString = "Code snippets"
#        theEnum = 'two'
#        self.layout.operator("object.dialog_operator")
    


################################################################################
#                             FUNCTIONS                                        #
################################################################################

##############
# DECORATORS #
##############

def actionfunc(label, tooltip, **kw):
    """Decorator that builds a GToolAction which have a method that corresponds
    to the decoated function, and adds the new action to the global actions list.
    label: label that describe the function (used in the popup menu).
    kw: keyword parameter will be added as members to the GToolAction object.
    Notice that decoracted function are on the model:
    def foobar(self, mesh):
        ...
    where self is the GToolAction object, and mesh the Blender.Mesh.Mesh concerned.
    """
    def _deco(func):
        global actions
        print("Adding action")
        actions.append(GToolAction(func, label, tooltip, **kw))
        return func
    return _deco


##################
# USER INTERFACE #
##################


def display_error(string):
   # PupMenu("Error !%t|" + string)
   pass


#########
# UTILS #
#########

#get_entities()-----------------------------------------------------------------

def selected_vertices(mesh):
    verts = mesh.vertices
    return dict((v.index, v) for v in verts if v.select)

def selected_edges(mesh):
   # SEL_E = Mesh.EdgeFlags['SELECT']
    return dict((e.index, e) for e in mesh.edges if e.select)#e.flag & SEL_E)

def selected_faces(mesh):
    faces = mesh.faces
    return [f for f in faces if f.select]#faces.selected()]

def verts_sub_verts_in_an_edge(verts, edges):
    """Remove vertices that belong to an (selected) edge."""
    for e in edges.values():
        for v in e.vertices:
            try:
                del verts[v]
            except KeyError:
                pass

def verts_sub_verts_in_a_face(verts, faces):
    """Remove vertices that belong to a (selected) face."""
    for f in faces:
        for v in f.vertices:
            try:
                del verts[v]
            except KeyError:
                pass

def edges_sub_edges_in_a_face(mesh, edges, faces):
    """Remove edges that belong to a (selected) face."""
    findEdges = mesh.findEdges
    for f in faces:
        vertsL = [[v for v in mesh.vertices if equals(v.index, i)] \
                   for i in f.vertices]
        verts = [v[0] for v in vertsL]
         
        v = verts
        if len(v) == 3:
            e_lst = [(v[0], v[1]), (v[1], v[2]), (v[2], v[0])]
        else: #len(v) == 4
            e_lst = [(v[0], v[1]), (v[1], v[2]), (v[2], v[3]), (v[3], v[0])]

        for i in findEdges(e_lst):
            try:
                del edges[i]
            except KeyError:
                pass

def get_entities(mesh, flag=NOTHING):
    """Determine the entities the user has selected.
    mesh: the selected Blender.Mesh.Mesh object.
    flag: indicates the kind of entities the caller wants.
          It's a combination of the following flags (with '|' operator): VERTS_FLAG, EDGES_FLAG, FACES_FLAG.
    return: - None if no flag(or NOTHING flag)
            - or if one kind of entity is wanted: vertices(in a dict), edges(in a dict), faces(in a list).
            - or a tuple depends on the flag that may contain vertices(dict), edges(dict), faces(list).
            Vertices, edges and faces are Blender.Mesh.MVert/MEdge/MFace objects.
            Dictionaries (verts and edges) are on the model : {obj_index:obj}.
    eg: a quad-face is selected (so 4 edges and 4 vertices too)
        - get_entities(mesh, FACES_FLAG) returns [the_face]
        - get_entities(mesh, VERTS_FLAG) returns {index0:vertex0, index1:vertex1,... }
    Notice that if flag is VERTS_FLAG|EDGES_FLAG for example, selected vertices that belong to
    a selected edge aren't returned.
    """
    res      = None
    vsel     = selected_vertices(mesh)
    esel     = None
    fsel_lst = None

    if flag & VERTS_FLAG:
        if flag & EDGES_FLAG:
            esel = selected_edges(mesh)
            verts_sub_verts_in_an_edge(vsel, esel)

            if flag & FACES_FLAG: #flag == VERTS_FLAG | EDGES_FLAG | FACES_FLAG
                fsel_lst = selected_faces(mesh)
                edges_sub_edges_in_a_face(mesh, esel, fsel_lst)
                res = (vsel, esel, fsel_lst)
            else: #flag == VERTS_FLAG | EDGES_FLAG
                res = (vsel, esel)
        else:
            if flag & FACES_FLAG: #flag == VERTS_FLAG | FACES_FLAG
                fsel_lst = selected_faces(mesh)
                verts_sub_verts_in_a_face(vsel, fsel_lst)
                res = (vsel, fsel_lst)
            else: #flag == VERTS_FLAG
                res = vsel
    else:
        if flag & EDGES_FLAG:
            esel = selected_edges(mesh)
            verts_sub_verts_in_an_edge(vsel, esel)

            if vsel:
                raise GToolFatalError("No alone vertex must be selected.")

            if flag & FACES_FLAG: #flag == EDGES_FLAG | FACES_FLAG
                fsel_lst = selected_faces(mesh)
                edges_sub_edges_in_a_face(mesh, esel, fsel_lst)
                res = (esel, fsel_lst)
            else: #flag == EDGES_FLAG
                res = esel
        else:
            if flag & FACES_FLAG: #flag == FACES_FLAG
                fsel_lst = selected_faces(mesh)
                verts_sub_verts_in_a_face(vsel, fsel_lst)
               # print ("VSEL: ", vsel)
               # print ("FSEL_LST: ", fsel_lst)
                if vsel:
                    raise GToolFatalError("Only faces must be selected.")

                res = fsel_lst
            else: #flag == NOTHING (very useless !! :)
                if vsel:
                    raise GToolFatalError("Nothing must be selected.")

    return res


#-------------------------------------------------------------------------------

def get_one_edge(esel):
    """
    esel: dictionary {index: edge} (see get_entities())
    """
    if len(esel) == 1:
        return esel.values()[0]
    else:
        raise GToolFatalError("need ONE edge")

def get_one_face(fsel_lst):
    """
    fsel_lst: face list (see get_entities())
    """
    if len(fsel_lst) == 1:
        return fsel_lst[0]
    else:
        raise GToolFatalError("need ONE face")


############
# GEOMETRY #
############

#project_vert_face()------------------------------------------------------------

@actionfunc("project: vert(s)->face (copy)", "Copy projection of vertex(ice) on face", make_copy=True)
@actionfunc("project: vert(s)->face",        "Project vertex(ice) on face",            make_copy=False)
def project_vert_face(self, mesh):
    """Project some vertices on a face."""
    vsel, fsel_lst = get_entities(mesh, VERTS_FLAG | FACES_FLAG)

    face = get_one_face(fsel_lst)
    if not vsel:
        raise GToolFatalError("need at least one vertex")

    projection = gm.project_vert_face

    if self.make_copy: #the projected vertices is are new points
        v_extend = mesh.verts.extend

        for vert in vsel.itervalues():
            h = projection(vert, face)

            if not h:
                raise GToolGeomError("Can't project (unvalid face ?!)")

            v_extend(h)
    else: #move the real vertices
        for vert in vsel.itervalues():
            h = projection(vert, face)

            if not h:
                raise GToolGeomError("Can't project (unvalid face ?!)")

            vect   = vert.co
            vect.x = h.x
            vect.y = h.y
            vect.z = h.z

    mesh.update()


#project_vert_edge()------------------------------------------------------------

@actionfunc("project: vert(s)->edge (copy)", "Copy projection of vertex(ice) on edge", make_copy=True)
@actionfunc("project: vert(s)->edge",        "Project vertex(ice) on edge",            make_copy=False)
def project_vert_edge(self, mesh):
    """Project some vertices on an edge."""
    vsel, esel = get_entities(mesh, VERTS_FLAG | EDGES_FLAG)
    edge = get_one_edge(esel)

    if not vsel:
        raise GToolFatalError("need at least one vertex")

    projection = gm.project_vert_edge

    if self.make_copy: #the projected vertices is are new points
        v_extend = mesh.verts.extend

        for vert in vsel.itervalues():
            h = projection(vert, edge)

            if not h:
                raise GToolGeomError("Can't project (unvalid edge ?!)")

            v_extend(h)
    else: #move the real vertices
        for vert in vsel.itervalues():
            h = projection(vert, edge)

            if not h:
                raise GToolGeomError("Can't project (unvalid edge ?!)")

            vect   = vert.co
            vect.x = h.x
            vect.y = h.y
            vect.z = h.z

    mesh.update()


#intersect_face_edge()----------------------------------------------------------

@actionfunc("intersect: face/edge(s) (cut)", "Intersect and cut face/edge",    cut=True)
@actionfunc("intersect: face/edge(s)",       "Draw intersection of face/edge", cut=False)
def intersect_face_edge(self, mesh):
    """Intersect a face and some edges."""
    from gm import intersect_face_edge

    esel, fsel_lst = get_entities(mesh, EDGES_FLAG | FACES_FLAG)

    face = get_one_face(fsel_lst)
    if not esel:
        raise GToolFatalError("need at least one edge")

    no_inters = 0

    if self.cut: #cut the edges in two edges, when it's possible
        medges = mesh.edges
        mverts = mesh.verts
        #edges are iterated in reversed order, because of the reorder of the
        # edges when one is deleted
        for i, edge in sorted(esel.items(), reverse=True):
            inters = intersect_face_edge(face, edge)

            if inters:
                mverts.extend(inters)
                v = mverts[-1]
                medges.extend(edge.v1, v)
                medges.extend(edge.v2, v)
                medges.delete(edge)
            else:
                no_inters += 1
    else: #just add new vertices as intersection points
        v_extend = mesh.verts.extend

        for edge in esel.itervalues():
            inters = intersect_face_edge(face, edge)

            if inters:
                v_extend(inters)
            else:
                no_inters += 1

    mesh.update()

    if no_inters:
        raise GToolGeomError("no intersection with %i edge(s)" % no_inters)


#intersect_edge_edge()----------------------------------------------------------

@actionfunc("intersect: edge/edge (cut)", "Intersect and cut edges",          cut=True)
@actionfunc("intersect: edge/edge",       "Draw intersection point of edges", cut=False)
def intersect_edge_edge(self, mesh):
    """Intersect two edges."""
    esel = get_entities(mesh, EDGES_FLAG)

    if len(esel) != 2:
        raise GToolFatalError("need exactly 2 edges")

    edge1 = esel.values()[0]
    edge2 = esel.values()[1]

    inters = gm.intersect_edge_edge(edge1, edge2)

    if not inters:
        raise GToolGeomError("no intersection")

    if self.cut: #cut the edges in two edges
        medges = mesh.edges
        mverts = mesh.verts

        mverts.extend(inters)

        medges.extend((edge1.v1, mverts[-2]), (edge1.v2, mverts[-2]),
                      (edge2.v1, mverts[-1]), (edge2.v2, mverts[-1]))

        ####BUG : medges.delete((edge1, edge2)) --> delete some faces too !! :(
        if edge1.index > edge2.index:
            medges.delete(edge1) ; medges.delete(edge2)
        else:
            medges.delete(edge2) ; medges.delete(edge1)

    else: #just add new vertices as intersection points
        if (inters[1]-inters[0]).length < EPSILON: #points are joined
            mesh.verts.extend(inters[0])
        else:
            mesh.verts.extend(inters)

    mesh.update()

def equals(a, b):
    return a == b

#intersect_face_face()----------------------------------------------------------

def intersectable_faces_pair_gen(faces, mesh):
    """Generator that produce pair of faces that can be intersect.
    faces: list of faces (Blender.Mesh.MFace objects).
    yield: a tuple of 2 faces (Blender.Mesh.MFace objects).
    """
    #from gm import intersect_face_face, EPSILON, Octree
    Octree = gm.Octree

    class _BoundingSphere:
        """A basic bouding sphere for a face (often too large but satisfactory)."""
        def __init__(self, face):
            """Constructor.
            face: the face to bound (Blender.Mesh.MFace object).
            """
            verts = [[v for v in mesh.vertices if equals(v.index, i)] for i in face.vertices]
         #   print(verts)
            self._center = sum([v[0].co for v in verts], Vector()) * (1.0/len(verts))
            self._ray    = max([(v[0].co - self._center).length for v in verts])

        def intersect(self, bs2):
            """Is there _BoundingSphere objects intersection ?
            bs2: a 2nd _BoundingSphere object.
            return: boolean (True if intersection).
            """
            return (self._center - bs2._center).length < (self._ray + bs2._ray)

    ### without Octree
    ##bs_faces = [(f, _BoundingSphere(f), set([v.index for v in f.verts])) for f in faces]
    ##for i, (face1, bs1, set1) in enumerate(islice(bs_faces, n-1)):
        ##for (face2, bs2, set2) in islice(bs_faces, i+1, n):
            ##if not bs1.intersect(bs2):
                ###the bounding spheres don't intersect --> no need to intersect faces
                ##continue
            ##if len(set1 & set2) != 0:
                ###face1 & face2 are neighbour ---> don't intersect them
                ##continue
            ##yield face1, face2

    bs_faces  = [_BoundingSphere(f) for f in faces]
    verts_set = [set([v for v in f.vertices]) for f in faces]

    octree         = Octree(faces, mesh, bs=bs_faces, vset=verts_set)
    aabb_faces_gen = octree.aabb_faces_gen

    for face1, face2 in aabb_faces_gen():
        if not face1.bs.intersect(face2.bs):
            #the bounding spheres don't intersect --> no need to intersect faces
            continue

        if face1.vset & face2.vset:
            #face1 & face2 are neighbour ---> don't intersect them
            continue

        yield face1.face, face2.face

class Face2Break(object):
    """A face which will be broken (and retriangulate later).
    self.face: the original face (Blender.Mesh.MFace object).
    self.inner_verts: list of verts which are inner face(Blender.Mesh.MVert object).
    self.border_verts: list of list of verts which are on an edge
    of the face(Blender.Mesh.MVert object).
    1rst list is for edge(face.verts[0] - face.verts[1]), etc...
    """
    __slots__ = ('face', 'inner_verts', 'border_verts')

    def __init__(self, face):
        self.face         = face
        self.inner_verts  = []
        self.border_verts = [[] for i in range(len(face.vertices))]

class Edge2Cut(object):
    """An edge that is cut by some faces.
    self.face_inters: dictionary with:
        -key   = face_index(the face that intersect)
        -value = MVert(result of the intersection)
    """
    __slots__ = 'face_inters'

    def __init__(self):
        self.face_inters = {}

class EdgeInFaceFinder(object):
    """Find if an edge belongs to a set of faces."""
    __slots__ = '_verts_sets'

    def __init__(self, faces):
        """
        faces: faces to examinate(Blender.Mesh.MFaceSeq object)
        """
        self._verts_sets = [(f.vertices, set(v for v in f.vertices)) for f in faces]

    def find(self, edge):
        """
        edge: Blender.Mesh.MEdge object
        return: True if the edge belongs to one face at least.
        """
        v1_ind = edge.vertices[0]
        v2_ind = edge.vertices[1]

        for fverts, vset in self._verts_sets:
            if v1_ind in vset and v2_ind in vset:
                #are the vertices consecutives (so the edge belong to the face)
                if len(fverts) == 3:
                    #in a triangle, all verts are consecutives...
                    return True

                #len(face) == 4
                for i, v in enumerate(fverts):
                    if   v == v1_ind: ind1 = i
                    elif v == v2_ind: ind2 = i

                if abs(ind1 - ind2) != 2: #can't be 0 (different verts)
                    return True
        return False
    
class MyVertex():
    
    lastIndex = 0 
    def __init__(self, co, index=-1, select=False):
        
        if index > -1:
            self.index = index
            MyVertex.lastIndex = index
        else:
            #new items get a new index assigned
            MyVertex.lastIndex += 1 
            self.index = MyVertex.lastIndex
            
        self.select = select
        self.co = co
        
    def __str__(self):
        return str(self.co) + " " + str(self.index)

class MyEdge():
     
     lastIndex = 0
     def __init__(self, vertices, index=-1, select=False):
        if index > -1:
            self.index = index
            MyEdge.lastIndex = index
        else:
            #new items get a new index assigned
           MyEdge.lastIndex += 1 
           self.index = MyEdge.lastIndex 
        self.select = select
        
        indexes = []
        vert = False
        for v in vertices:
            #new vertexes are from type MyVertex
            if isinstance(v, MyVertex):
                vert = True
                indexes.append(v.index)
        
        if vert:
            self.vertices = indexes
        else: 
            #take the existing values
            self.vertices = [vertices[0], vertices[1]]
            
     def __str__(self):
        return str(self.vertices) + " " + str(self.index)

class MyFace():
    
    lastIndex = 0
    def __init__(self, vertices, no=-1, index=-1, select=False):
        if index > -1:
            self.index = index
            MyFace.lastIndex = index
        else:
            #new items get a new index assigned
            MyFace.lastIndex += 1 
            self.index = MyFace.lastIndex 
        self.select = select
        
        indexes = []  
        vert = False  
        for v in vertices:
            if isinstance(v, MyVertex):
                vert = True
                indexes.append(v.index)        
        if vert:
            if no == -1:
               if len(vertices) == 3:
                   self.normal = normal(vertices[0].co, 
                                        vertices[1].co, 
                                        vertices[2].co)
               elif len(vertices) == 4:
                   self.normal = normal(vertices[0].co, 
                                        vertices[1].co, 
                                        vertices[2].co,
                                        vertices[3].co)
            else:
                self.normal = no
                
            self.vertices = indexes
        else:
            verts = []
            for i in range(0, len(vertices)):
                verts.append(vertices[i])
            self.vertices = verts
            self.normal = no
            
    def __str__(self):
        return str(self.vertices) + " " + str(self.normal) + " " + str(self.index)

class MyMesh():
    
    def __init__(self, mesh):
        self.vertices = [MyVertex(v.co, v.index, v.select) for v in mesh.vertices]
        self.edges = [MyEdge(e.vertices, e.index, e.select) for e in mesh.edges]
        self.faces = [MyFace(f.vertices, f.normal, f.index, f.select) for f in mesh.faces]
        self.mesh = mesh #for further data            
            
def retriangulate_mesh(mesh, faces2del, faces_dic, edges2del_ind):
    """retriangulate faces of a mesh, with the given new verts.
    faces2del: set which contains the faces to delete indices.
    faces_dic: dictionary with key=face_index, value=Face2Break object.
    edges2del_ind: list of the indices of the egdes that must be cut.
    """
    #-------------------------------------------------------------------
    def _add_no_UV_face(tri, old_face):
        #sort the verts in order to have a right oriented normal vector
        vec = tri.verts[1].co - tri.verts[0].co
        if old_face.normal.dot(vec.cross(tri.verts[-1].co - tri.verts[0].co)) > 0.0:
            mfaces.append(MyFace([tri.verts[0], tri.verts[1], tri.verts[2]]))
        else:
            mfaces.append(MyFace([tri.verts[0], tri.verts[2], tri.verts[1]]))

        new_face        = mfaces[-1]
        
        #TODO: irrelevant FOR NOW, because mesh gets rebuilt completely
        #so store that separately and re-apply it after new mesh is successfully
        #rebuilt
       # new_face.hide   = old_face.hide
       # new_face.material_index    = old_face.material_index
       # new_face.select    = old_face.select
       # new_face.use_smooth = old_face.use_smooth

    #-------------------------------------------------------------------
    def _complete_vcol_face(new_face, old_face):
        pass
      #  old_col = old_face.col
      #  new_face.col = (old_col[0], old_col[0], old_col[0])

    #-------------------------------------------------------------------
    def _complete_UV_face(new_face, old_face):
        pass
        ##new_face.flag   = old_face.flag ##BUG in API (sometimes there is an exception)
      #  new_face.image  = old_face.image
      #  new_face.mode   = old_face.mode
      #  new_face.transp = old_face.transp

        ##uv coords
#        for uv_layer_name in uv_layer_names:
#            mesh.activeUVLayer = uv_layer_name
#
#            origin   = old_face.verts[0].co
#
#            base_v1  = old_face.verts[1].co - origin
#            if base_v1.length < EPSILON: return
#
#            base_v2  = old_face.verts[-1].co - origin
#            if base_v2.length < EPSILON: return
#
#            base_uv1 = old_face.uv[ 1] - old_face.uv[0]
#            base_uv2 = old_face.uv[-1] - old_face.uv[0]
#
#            def _vert_uv(v):
#                i = LineIntersect(v, v - base_v2, origin, old_face.verts[1].co)
#                if not i: x = 0.0
#                else:     x = (i[0]-origin).length / base_v1.length
#
#                i = LineIntersect(v, v - base_v1, origin, old_face.verts[-1].co)
#                if not i: y = 0.0
#                else:     y = (i[0]-origin).length / base_v2.length
#
#                return old_face.uv[0] + x * base_uv1 + y * base_uv2
#
#            new_face.uv = [_vert_uv(vert.co) for vert in new_face.verts]

    #-------------------------------------------------------------------

    triangulate = gm.triangulate
    mfaces      = mesh.faces
    mverts      = mesh.vertices

    uv_layer_names  = None
    active_uv_layer = None

     #how to test that in Blender 2.5x upwards ?
     #there is always a uvtexture layer present AND a vertex color layer
     #TODO: assume using a texture layer here
    if True:#mesh.faceUV: 
              
        uv_layer_names  = mesh.mesh.uv_textures #mesh.getUVLayerNames()
        active_uv_layer = mesh.mesh.uv_textures.active #mesh.activeUVLayer

        if mesh.mesh.vertex_colors:# mesh.vertexColors:
            def _add_face(tri, old_face):
                _add_no_UV_face(tri, old_face)
                nface = mfaces[-1]
                _complete_vcol_face(nface, old_face)
                _complete_UV_face(nface, old_face)
        else:
            def _add_face(tri, old_face):
                _add_no_UV_face(tri, old_face)
                _complete_UV_face(mfaces[-1], old_face)
#    else:
#        if mesh.vertexColors:
#            def _add_face(tri, old_face):
#                _add_no_UV_face(tri, old_face)
#                _complete_vcol_face(mfaces[-1], old_face)
#        else:
#            _add_face = _add_no_UV_face
#

    for f_ind in faces2del:
        #retriangulate all the given faces
        f2break = faces_dic[f_ind]
    
        vertsL = [[v for v in mverts if equals(v.index, i)] \
                                 for i in f2break.face.vertices] 
        verts = [v[0] for v in vertsL]
       # [print("VERTS: ", v) for v in verts]
       # [print("INNER:", i) for i in f2break.inner_verts]
       # [print("BORDER: ", b) for b in f2break.border_verts]
        
        tris    = triangulate(verts, f2break.inner_verts, f2break.border_verts)

        if not tris: #shouldn't append...
            raise GToolGeomError("a vertex (at least) is out of the envelop")
        
        for tri in tris:
          #  print("TRIANGLE: ", tri)
            if not isInvalid(tri):
                _add_face(tri, f2break.face)

   # print("MFACES: ", mfaces)
    if active_uv_layer is not None:
        mesh.activeUVLayer = active_uv_layer

    if faces2del:
        #delete all the old faces
        #mfaces.delete(0, list(faces2del)) #0 is for delete only faces (don't reorder edges)
       # print(faces2del)
        faces = []
        for i in list(faces2del):
            for f in mfaces:
                if f.index == i:
                  #  print("INDEX: ",i) 
                    faces.append(f)
        for f in faces:
            mfaces.remove(f)

    #delete the edges than don't belong to a face
    medges     = mesh.edges
    edges2del_ind = sorted(edges2del_ind, reverse = True)
   # edges2del_ind.sort(reverse=True)

    is_edge_in_a_face = EdgeInFaceFinder(mfaces).find
   # print(edges2del_ind)

    for i in edges2del_ind:
        if not is_edge_in_a_face(medges[i]):
            ####BUG : medges.delete(edges2del_ind) --> delete some faces too !! :(
         #   medges.delete(i)
            for e in medges:
                if e.index == i:
                    #print("INDEX: ",i) 
                    medges.remove(e)
                    
   # print("MFACES: ", mfaces)               

#def checkSegment(point, first, second):
#    if first < second:
#        return gm.point_in_segment(point, first, second)
#    else:
#        return gm.point_in_segment(point, second, first)
#    

def isInvalid(tri):
#    return checkSegment(tri.verts[0].co, tri.verts[1].co, tri.verts[2].co) or \
#           checkSegment(tri.verts[1].co, tri.verts[0].co, tri.verts[2].co) or \
#           checkSegment(tri.verts[2].co, tri.verts[0].co, tri.verts[1].co)
     area = area_tri(tri.verts[0].co, tri.verts[1].co, tri.verts[2].co)
    # print("AREA: ", area)
     return area < gm.EPSILON 
    
    
def find_edges(v1, v2, mesh):
    #print("FIND:", v1, v2)
    for e in mesh.edges:
        if e.vertices[0] == v1.index and e.vertices[1] == v2.index or \
           e.vertices[1] == v1.index and e.vertices[0] == v2.index:
            return e.index
    return None

@actionfunc("intersect: face(s) (cut)", "Intersect and cut faces",            cut=True)
@actionfunc("intersect: face(s)",       "Draw line of intersection of faces", cut=False)
def intersect_face_face(self, mesh):
    """Intersection between some faces."""
    intersect_faces = gm.intersect_face_face

    mesh = MyMesh(mesh)
    fsel_lst = get_entities(mesh, FACES_FLAG)

    if len(fsel_lst) < 2:
        raise GToolFatalError("need at least two face")
    
    no_inters = True
    
    #tuples needed to rebuild the whole mesh, cant update it (yet) maybe with bmesh
    mverts = mesh.vertices
    medges = mesh.edges
    mfaces = mesh.faces
      
    if self.cut:
       # find_edges    = mesh.findEdges
        faces2del     = set() #contains the faces to delete indices
        faces_dic     = dict((f.index, Face2Break(f)) for f in fsel_lst)
        cut_edges_dic = {} #key = egde_index, value = Edge2Cut object

        for face1, face2 in intersectable_faces_pair_gen(fsel_lst, mesh):
            inters = intersect_faces(face1, face2, mesh)

            if inters:
                no_inters = False

                #here: we got 2 points
                if (inters[1].point - inters[0].point).length < EPSILON:
                    #points are joined
                    if face1.index == inters[0].face_index:
                        face = face2
                    else:
                        face = face1

                    mverts.append(MyVertex(inters[0].point))
                    faces_dic[face.index].inner_verts.append(mverts[-1])
                    faces2del.add(face.index)

                else:
                    #2 points points --> inner face or on an edge
                    for inter in inters:
                       # print("INTER: ", inter.point, inter.face_index)
                        if face1.index == inter.face_index:
                            face2edgecut  = face1
                            face2midpoint = face2
                        else:
                            face2edgecut  = face2
                            face2midpoint = face1
                        verts = [[v for v in mverts if equals(v.index, i)] \
                                 for i in face2edgecut.vertices]
                        edge2cut_ind = find_edges(verts[inter.e_ind][0],
                                                  verts[(inter.e_ind+1) % len(verts)][0],
                                                  mesh)
                      #  [print("VERTS2CUT", v) for v in verts] 
                     #   print(edge2cut_ind)                          

                        e2c = cut_edges_dic.get(edge2cut_ind) #edge to cut
                    #    print("E2C: ", e2c)

                        if e2c is None:
                            #1rst case: this edge has not yet been cut
                            # +edge is added to cut edge
                            # +a new MVert is added
                            mverts.append(MyVertex(inter.point))
                            
                          #  print("MVERTS: ", mverts)
                            
                            new_vert = mverts[-1]
                            e2c      = Edge2Cut()
                            e2c.face_inters[face2midpoint] = new_vert
                            cut_edges_dic[edge2cut_ind]    = e2c
                            faces_dic[face2midpoint.index].inner_verts.append(new_vert)
                            faces_dic[face2edgecut.index].border_verts[inter.e_ind].append(new_vert)

                        else:
                            new_vert = e2c.face_inters.get(face2midpoint)

                            if new_vert is None:
                                #2nd case: the edge has already been cut,
                                #but not by the same face
                                # +a new MVert is added
                                mverts.append(MyVertex(inter.point))
                                new_vert = mverts[-1]
                                e2c.face_inters[face2midpoint] = new_vert
                                faces_dic[face2midpoint.index].inner_verts.append(new_vert)
                                faces_dic[face2edgecut.index].border_verts[inter.e_ind].append(new_vert)

                            else:
                                #3rd case: the edge has already been cut by the face
                                faces_dic[face2edgecut.index].border_verts[inter.e_ind].append(new_vert)

                        faces2del.add(face1.index)
                        faces2del.add(face2.index)
                       # [print ("FACES_DIC:", val.inner_verts[0]) for val in faces_dic.values() 
                       #         if len(val.inner_verts)]

        retriangulate_mesh(mesh, faces2del, faces_dic, cut_edges_dic.keys())

    else: #don't cut
        for face1, face2 in intersectable_faces_pair_gen(fsel_lst, mesh):
            inters = intersect_faces(face1, face2, mesh)

            if inters:
                no_inters = False

                #here: we got 2 points
                p0 = inters[0].point
                p1 = inters[1].point

                if (p1 - p0).length < EPSILON:
                    #points are joined
                    #mverts.extend(p0)
                    mverts.append(MyVertex(p0))

                else: #2 points, plus 1 edge
                   # mverts.extend(p0) 
                   # mverts.extend(p1)
                    mverts.append(MyVertex(p0))
                    mverts.append(MyVertex(p1))
                    medges.append(MyEdge((mverts[-1].index, mverts[-2].index)))
                   # medges.extend()

   # mesh.update()
    
    if no_inters:
        raise GToolGeomError("no face intersection")
        return mesh

    verts = [v.co.to_tuple() for v in mesh.vertices]
    edges = [] #tuple(e.vertices) for e in mesh.edges]  
    faces = [tuple(f.vertices) for f in mesh.faces]
    
    [print(v) for v in verts]
    [print(e) for e in edges]
    [print(f) for f in faces]
   
    return verts, edges, faces
    
def facetuple(face):
    if len(face.vertices) == 3:
        return (face.vertices[0], face.vertices[1], face.vertices[2])
    elif len(face.vertices) == 4:
        return (face.vertices[0], face.vertices[1], face.vertices[2], face.vertices[3])

#flatten_vertices()-------------------------------------------------------------

@actionfunc("nearest plane: verts", "Pull vertices to nearest plane")
def flatten_vertices(self, mesh):
    """Flatten vertices (project them onto the nearest plane)."""
    vsel = get_entities(mesh, VERTS_FLAG)

    if len(vsel) < 3:
        raise GToolFatalError("need 3 vertices at least")

    point, norm = gm.nearest_plane(vsel)

    if not point:
        raise GToolGeomError("no satisfactory plane", 1)

    project = gm.project_point_plane

    for vert in vsel.itervalues():
        vect   = vert.co
        h      = project(vect, norm, point)
        vect.x = h.x
        vect.y = h.y
        vect.z = h.z

    mesh.update()


#align_vertices()---------------------------------------------------------------

#thanks to grafix from blenderartists.org for the idea.
@actionfunc("distribute & align: verts", "Distribute and align vertices", distr=True)
@actionfunc("align: verts",              "Align vertices",                distr=False)
def align_vertices(self, mesh):
    """Distribute vertices regularly or align them."""
    vsel = get_entities(mesh, VERTS_FLAG).values()

    if len(vsel) < 3:
        raise GToolFatalError("need 3 vertices at least")

    vsel  = gm.XYZvertexsort(vsel)
    point = vsel[0].co
    vect  = (vsel[-1].co - point) * (1.0/(len(vsel)-1))

    if vect.length < EPSILON: return

    from gm import islice

    if self.distr == True: #align & distribute
        for mult, vert in enumerate(islice(vsel, 1, len(vsel)-1)):
            v = vert.co
            finalv = (mult+1) * vect + point
            v.x = finalv.x
            v.y = finalv.y
            v.z = finalv.z

    else: #align only
        project = gm.project_point_vect

        for vert in islice(vsel, 1, len(vsel)-1):
            v = vert.co
            finalv = project(v, point, vect)
            v.x = finalv.x
            v.y = finalv.y
            v.z = finalv.z

    mesh.update()


#distribute_vertices()----------------------------------------------------------

class EdgeVert(object):
    """A vertex of an edge."""
    __slots__ = ('edge', 'vind')

    def __init__(self, edge, vind):
        self.edge = edge  #Blender.Mesh Edge object
        self.vind = vind  #index of vertex for the edge (1 or 2)

def vertex_string(edict, vert):
    """Build a list of edge-connected vertices.
    edict: dictionary {vextex_index, [list_of_EdgeVert_linked_to_this_vertex]}
    vert: the 1rst vertex of the vertex string.
    return: the list of vertices.
    """
    vlist = [vert]
    vind  = vert

    try:
        while True:
            convert = edict[vind].pop() #connected vertex
            edge    = convert.edge

            if convert.vind == 1: v2add = edge.vertices[1]
            else:                 v2add = edge.vertices[0]

            vind = v2add
            vlist.append(v2add)

            lst = edict[vind]

            for i, elt in enumerate(lst):
                if elt.edge.index == edge.index:
                    del lst[i]
                    break
    except KeyError:   pass #edict[vind] with vind not a valid key
    except IndexError: pass #pop() on an empty list

    return vlist

def get_loop(edges, verts):
    """Return a 'loop' of vertices edge-connected (loop[N] and loop[N+1] are edge-connected).
    edges: list of selected edges (Blender.Mesh.MEdge objects).
    verts: list of selected vertices (Blender.Mesh.MVert objects).
    return: a list of vertices (Blender.Mesh.MVert objects).
    NB: if the loop is a 'true loop' (and not a simple string), the first
    and the last vertex of the list are the same.
    """
    e = edges.popitem() #we need an edge to begin

    edict = dict((v.index, []) for v in verts)
    for edge in edges.values():
        edict[edge.vertices[0]].append(EdgeVert(edge, 0))
        edict[edge.vertices[1]].append(EdgeVert(edge, 1))

    looptmp = vertex_string(edict, e[1].vertices[0])
    loop    = vertex_string(edict, e[1].vertices[1])

    for val in edict.values():
        if val: raise GToolFatalError("need an edge loop")

    loop.reverse()
    loop.extend(looptmp)

    return loop

def loop_size(loop):
    """Get the length of a vertex loop.
    loop: vertex loop (Blender.Mesh.MVert objects).
    return: the length.
    """
    size  = 0.0
    vects = (v.co for v in loop)
    v1    = next(vects)

    for v2 in vects:
        size += (v2-v1).length
        v1 = v2

    return size

@actionfunc("distribute: verts", "Distribute vertices")
def distribute_vertices(self, mesh):
    """Distribute vertices regularly on a curve."""
    vsel = get_entities(mesh, VERTS_FLAG).values()

    if len(vsel) < 3:
        raise GToolFatalError("need 3 vertices at least")

    loopInd = get_loop(get_entities(mesh, EDGES_FLAG), vsel)
    loop = [v for v in mesh.vertices if v.index in loopInd]
    
    interp = gm.BezierInterpolator(loop)

    new_coords = []
    average    = loop_size(loop) / (len(loop)-1)

    vects = (v.co for v in loop)
    v1    = next(vects)
    v2    = next(vects)
    index = 0

    size_acc = 0.0             #size accumulator
    vec_len  = (v2-v1).length

    for coeff in (average*i for i in range(1, len(loop)-1)):
        while coeff > (size_acc+vec_len):
            size_acc += vec_len
            v1 = v2
            v2 = next(vects)
            index += 1
            vec_len = (v2-v1).length

        #here we have: size_acc < coeff < (size_acc+vec_len)
        # ~~> coeff 'between' v1 & v2
        new_coords.append(interp.interpolate((coeff-size_acc)/vec_len, index))


    it = iter(loop)
    next(it) #begin with the 2nd vertex
    for coord in new_coords:
        v   = next(it).co
        v.x = coord.x
        v.y = coord.y
        v.z = coord.z

    mesh.update()


#-------------------------------------------------------------------------------

#@actionfunc("Display infos", "Display infos")
#def display_infos_action(self, mesh):
    #vsel, esel, fsel_lst = get_entities(mesh, VERTS_FLAG|EDGES_FLAG|FACES_FLAG)

    #if vsel:
        #print "VERTS:"
        #print "------"
        #for v in vsel.itervalues():
            #print "  -", v

    #if esel:
        #print "EDGES:"
        #print "------"
        #for e in esel.itervalues():
            #print "  -", e

    #if fsel_lst:
        #print "FACES:"
        #print "------"
        #for f in fsel_lst:
            #print "  -", f
#@actionfunc("Display infos", "Display infos")


################################################################################
#                           MAIN FUNCTION                                      #
################################################################################
buttons = {}
#def main():
#    #"""Da main function ! :)"""
#    ui = UIInterface.get_UI_from_conf()
#    ui.start()
#   


def execute(self, context):
        #init
       # is_editmode = EditMode()
        is_editmode = context.mode == 'EDIT_MESH'
        if is_editmode:
        #    EditMode(0)
            ops.object.mode_set(mode = 'OBJECT')

        try:
            #get selected object (or quit)
            #objs = GetSelected()
            objs = context.selected_objects
            if not objs:
                raise GToolFatalError("none selected object")

            if len(objs) > 1:
                raise GToolFatalError("only one object must be selected")

            obj = objs[0]
           # if obj.getType() != "Mesh":
            if obj.type != 'MESH':
                raise GToolFatalError("active object must be a mesh")

            #do the wanted action on the mesh
          #  mesh   = obj.getData(mesh=True)
            mesh = obj.data
            action = buttons[self.bl_idname]

            if action:
                verts, edges, faces = action(mesh)
                if verts != None and edges != None and faces != None:
                    
                    print("Creating new mesh")
                    nmesh = data.meshes.new(name = mesh.name)
                    
                    print("Building new mesh")
                    nmesh.from_pydata(verts, edges, faces) #TODO: new Faces!
                   
                    print("Removing old mesh")    
                    obj.data = None
                    mesh.user_clear()
                    if (mesh.users == 0):
                        data.meshes.remove(mesh)
                   
                    print("Assigning new mesh")     
                    obj.data = nmesh 
                       

        #Exceptions handlers
        except GToolFatalError as e:
            print(e)
            display_error(str(e))

        except GToolGeomError as e:
            print(e)

            if e.priority >= 1:
                display_error(str(e))

        except:
            import sys
            sys.excepthook(*sys.exc_info())
            display_error("An exception occured | (look at the terminal)")

        #finish
        #if is_editmode:
            #EditMode(1)
            #ops.object.mode_set(mode = 'EDIT')
 

class DialogOperator(types.Operator):
    bl_idname = "object.geomtools"
    bl_label = "GeomTools Dialog"
  
    def draw(self, context):
        for b in buttonList:
            self.layout.operator(b)
         
    def execute(self, context):   
        return {'FINISHED'}
 
    def invoke(self, context, event):      
        return context.window_manager.invoke_props_dialog(self)

def kwVals(action):
    retVal = ""
    for k in action.kwVals:
        if k:
           retVal = retVal + "t"
        else:   
           retVal = retVal + "f"
    return retVal   

print("Actions: ", len(actions))
for action in actions:
    name  = "action." + action.function.__name__ + kwVals(action)
    opName = "ACTION_OT_" + action.function.__name__ + kwVals(action)
    buttons[opName] = action 
     
    class ActionOperator(types.Operator):
        bl_idname = name
        bl_label = action.label
        bl_description = action.tooltip
        
        def invoke(self, context, event):
            execute(self, context)       
            return{'FINISHED'}
        
buttonList = sorted(buttons.keys())

        
class GeomToolsPanel(types.Panel):
    bl_idname = "OBJECT_PT_geomTools"
    bl_label = "GeomTools"
    bl_context = "object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    
    def draw(self, context):
        self.layout.operator("object.geomtools")
        

################################################################################
#                           MAIN PROGRAM                                       #
################################################################################

#main()
#	Registration
if __name__ == "__main__":
    utils.register_module(__name__)