## math module for mesh_geom_tool.py script
## version: 0.4

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
# Importing modules
################################################################################

#from Blender.Mathutils import Vector, Intersect, DotVecs, ProjectVecs, CrossVecs, LineIntersect
from mathutils import Vector
from mathutils.geometry import intersect_line_line, intersect_ray_tri 
from math import cos, acos, sin, degrees, radians, pi

try:
    import itertools
    islice = itertools.islice
   # izip   = itertools.izip
    izip = itertools.zip_longest

except ImportError as e:
    print (__name__, e)

    def islice(iterable, *args):
         s     = slice(*args)
         it    = iter(xrange(s.start or 0, s.stop or 2147483647, s.step or 1)) #sys.maxint
         nexti = it.next()
         for i, element in enumerate(iterable):
             if i == nexti:
                 yield element
                 nexti = it.next()

    def izip(*iterables):
        iterables = map(iter, iterables)
        while iterables:
            #yield tuple([i.next() for i in iterables]) #and NOT tuple(i.next() for i in iterables)
            yield [i.next() for i in iterables]

################################################################################
#                             CONSTANTS                                        #
################################################################################

EPSILON = 0.001


################################################################################
#                             FUNCTIONS                                        #
################################################################################

#########
# UTILS #
#########

def minmax(l):
    it = iter(l)
    mini = maxi = next(it)

    for val in it:
        mini = min(mini, val)
        maxi = max(maxi, val)

    return mini, maxi

#-------------------------------------------------------------------------------

def point_in_segment(p, a, b):
    """Is the point p between points a and b (a,b and p aligned)
    p, a, b: Blender.Mathutils.Vector objects.
    """
    vec = a - p
   # print(vec.dot(b-p))
    return vec.dot(b - p) < 0.0

#-------------------------------------------------------------------------------

def same_side(p1, p2, a, b):
    """Are points p1 and p2 in the same side of the ray(a, b).
    p1, p2, a, b: Blender.Mathutils.Vector objects, in the same plane.
    """
    a_b = b - a
    vec = a_b.cross(p1 - a)

    return (vec.dot(a_b.cross(p2 - a)) >= 0.0)

#-------------------------------------------------------------------------------

def point_in_triangle(p, a, b, c):
    """Is point p in the triangle with vertex(a, b, c).
    p, a, b, c: Blender.Mathutils.Vector objects, in the same plane.
    """
    return (same_side(p, a, b, c) and \
            same_side(p, b, a, c) and \
            same_side(p, c, a, b))

#triangulate()------------------------------------------------------------------

class Triangle(object):
    """A simple triangle class, with 3 vertices attibutes.
    (Blender.Mesh.MVert objects)
    """
    __slots__ = 'verts'

    def __init__(self, v1, v2, v3):
        self.verts = [v1, v2, v3]

    def own_edge(self, vert1, vert2):
        """Does the triangle own the edge (vert1, vert2).
        vert1, vert2: edge extremities(Blender.Mesh.MVert objects).
        return: a tuple with : a boolean (True if owned), the index of the third vertex.
        """
        ok1     = False
        ok2     = False
       # third_v = None # cant add ints to None, and there is no test for None 
       # afterwards, so assume None is 0 here
        third_v = None
        
        #[print("OWN_EDGE_VERTS: ", v ) for v in self.verts] 
        #print("OWN_EDGE_VERT1: ", vert1) 
        #print("OWN_EDGE_VERT2: ", vert2)
        for i, v in enumerate(self.verts):
            if v.index == vert1.index:
                ok1 = True
            elif v.index == vert2.index:
                ok2 = True
            else:
                third_v = i
      #  print(ok1, ok2, third_v)
        return (ok1 and ok2, third_v)

def _must_rotate_edge(v, v1, v2, v3):
    """(v1, v2, v3) and (v, v1, v2) are 2 triangles : must the edge(v1, v2)
    be rotated in order to have a beautiful fill ?
    v, v1, v2, v3 : Blender.Mathutils.Vector objects.
    return: boolean (True if must rotate).
    """
    #criteria : area divided by the sum of edge lengths
    e1 = v1 - v2
    e2 = v3 - v2
    e3 = v3 - v1
    e4 = v  - v1
    e5 = v  - v2
    e6 = v  - v3

    #NB: triangle_area(v1, v2, v3) ==> CrossVecs(v1-v2, v3-v2).length / 2.0
    ratio1 = e1.cross(e2).length / (e1.length + e2.length + e3.length) + \
             e1.cross(e5).length / (e1.length + e4.length + e5.length)

    ratio2 = e3.cross(e4).length / (e3.length + e4.length + e6.length) + \
             e2.cross(e5).length / (e2.length + e5.length + e6.length)

    return (ratio1 < ratio2)

def _add_beautiful_triangle(tris, vert, e_vert1, e_vert2):
    """Add a new triangle to a triangle list, and keep a beautiful fill
    (eventually remove one triangle and add two new triangles).
    tris: Triangle objects list.
    vert: new vertex to add as triangle vertex (Blender.Mesh.MVert object).
    e_vert1, e_vert2 : vertices that form an edge, belonging to an existing
    triangle. The edge will be use to build the new triangle, but can be
    eventually rotated.
    """
    #search the neighbour triangle (if it exists), to eventually rotate the shared edge
    sharing_edge_tri = None
    added_tri        = False

    for tri_ind, tri in enumerate(tris):
        own, third_v_ind = tri.own_edge(e_vert1, e_vert2)
        if own:
            sharing_edge_tri     = tri
            sharing_edge_tri_ind = tri_ind
            break

    if sharing_edge_tri:
        #there is a neighbour for this edge
        v1 = sharing_edge_tri.verts[(third_v_ind+1)%3]
        v2 = sharing_edge_tri.verts[(third_v_ind+2)%3]
        v3 = sharing_edge_tri.verts[third_v_ind]


        #inters <--- intersect(edge(vert-v3), edge(v1-v2))
        inters = intersect_line_line(vert.co, v3.co, v1.co, v2.co)
        #is there a concave problem ??
        if inters:
            inter = inters[0]
            if point_in_segment(inter, v1.co, v2.co) and point_in_segment(inter, vert.co, v3.co):
                #use the rotate criteria
                if _must_rotate_edge(vert.co, v1.co, v2.co, v3.co):
                    del tris[sharing_edge_tri_ind]
                    tris.append(Triangle(vert, v1, v3))
                    tris.append(Triangle(vert, v2, v3))
                    added_tri = True

    if not added_tri:
        tris.append(Triangle(vert, e_vert1, e_vert2))

def _triangulate_inner_envelop(tris, verts):
    """Triangulate in an envelop.
    tris: Triangle objects list.
    verts: list of vertices to use in the triangulation (Blender.Mesh.MVert objects).
    Beware, the verts must be IN the envelop, and not on the edges for example.
    """
    #add all vertices, one by one
    for vert in verts:
        #search in which triangle is the verts
        in_tri_ind = -1
        p          = vert.co

        for i, tri in enumerate(tris):
            t_verts = tri.verts
            if point_in_triangle(p, t_verts[0].co, t_verts[1].co, t_verts[2].co):
                in_tri_ind = i
                break

        if in_tri_ind == -1:
            #error, a vertex is out of all triangles
            return None

        in_tri = tris.pop(in_tri_ind)

        for i in range(3):#for the 3 edges of this triangle
            _add_beautiful_triangle(tris, vert, in_tri.verts[i], in_tri.verts[(i+1)%3])

def _get_cutting_verts(envelop, verts):
    """Get vertices which are on the edges on an envelop.
    envelop: list of 3 or 4 Blender.Mesh.MVert objects.
    verts: list of vertices to test (Blender.Mesh.MVert objects).
    return: list of vertices (Blender.Mesh.MVert objects) that are on an edge.
    Notice that vertices which are returned are removed from 'verts'.
    """
    #determine the verts that 'cut' an edge
    n             = len(envelop)
    edges         = [(envelop[i], envelop[(i+1)%n]) for i in xrange(n)]
    cutting_verts = [[] for i in xrange(n)]
    vert2del      = set()

    for i, (e1, e2) in enumerate(edges):
        e = e1.co - e2.co
        for vert_i, vert in enumerate(verts):
            if CrossVecs(e, vert.co - e1.co).length < EPSILON and vert_i not in vert2del:
                cutting_verts[i].append(vert)
                vert2del.add(vert_i)

    vert2del = list(vert2del)
    vert2del.sort(reverse=True)
    for i in vert2del:
        del verts[i]

    return cutting_verts

def _cut_edges(cutting_verts, envelop, tris):
    """Cut edges of a triangulated envelopp
    (indeed, we want to triangulate with vertices that are on the envelop borders).
    cutting_verts: list of list ofvertices that are used to cut (Blender.Mesh.MVert objects).
    envelop: list of 3 or 4 Blender.Mesh.MVert objects.
    tris: Triangle objects list (modified by this function).
    """
    for i, cverts in enumerate(cutting_verts):
        if cverts:
            #there are verts that cut this edge
            v1 = envelop[i]
            v2 = envelop[(i+1) % len(envelop)]

            #search the triangle that owns the edge
            for tri_ind, tri in enumerate(tris):
                own, third_v_ind = tri.own_edge(v1, v2)
                if own:
                    in_tri_ind = tri_ind
                    break
            in_tri = tris.pop(in_tri_ind)
            v3 = in_tri.verts[third_v_ind]

            cverts.sort(key = lambda v: (v.co-v1.co).length)

            cverts.insert(0, v1)
            cverts.append(v2)

            i = 0
            j = len(cverts) - 1

            while True:
                if i >= j: break

                _add_beautiful_triangle(tris, cverts[i+1], cverts[i], v3)
                i += 1

                if j <= i: break

                _add_beautiful_triangle(tris, cverts[j-1], cverts[j], v3)
                j -= 1

def triangulate(envelop, verts, cutting_verts=None, check_borders=False):
    """Triangulate an envelop that contains some others vertices.
    envelop: list of 3 or 4 Blender.Mesh.MVert objects.
    verts: list of vertices to use in the triangulation (Blender.Mesh.MVert objects).
    cutting_verts: list of list vertices (Blender.Mesh.MVert objects) that are
    on an edge of the envelop. These vertices must NOT belong to the 'verts' list.
    The first list correspond to the edge (envelop[0], envelop[1]), etc...
    check_borders: boolean. True = the 'cutting_verts' is build by the function.
    False = the arguments 'cutting_verts' is used (eventually None).
    Note that 'cutting_verts' can be modified (sorted) by the function.
    return: list of Triangle objects.
    """
    #manage the envelop (add one or 2 triangles)
    if len(envelop) == 3:
        tris = [Triangle(envelop[0], envelop[1], envelop[2])]
    else: #len(envelop) == 4
        if _must_rotate_edge(envelop[3].co, envelop[0].co, envelop[1].co, envelop[2].co):
            tris = [Triangle(envelop[0], envelop[1], envelop[3]),
                    Triangle(envelop[1], envelop[2], envelop[3])]
        else:
            tris = [Triangle(envelop[0], envelop[1], envelop[2]),
                    Triangle(envelop[0], envelop[2], envelop[3])]

    if check_borders:
        cutting_verts = _get_cutting_verts(envelop, verts)

   # print("CUTTING: ", cutting_verts)
    _triangulate_inner_envelop(tris, verts)

    if cutting_verts:
        _cut_edges(cutting_verts, envelop, tris)

    return tris

#-------------------------------------------------------------------------------

def XYZvertexsort(verts):
    """Sort a list of vertex with the most appropriate coodinate (x, y or z).
    verts: a list of vertices (Blender.Mesh.MVert objects).
    return: the sorted list.
    NB: verts is modified.
    """
    ##sort the vertices to get a list of aligned point (normally :)
    verts.sort(key=lambda v: v.co.x)    #X coord sort
    vertstmp = list(verts)
    vertstmp.sort(key=lambda v: v.co.y) #Y coord sort

    #compare the x diff and the y diff
    diff  = abs(verts[0].co.x - verts[-1].co.x)
    diffy = abs(vertstmp[0].co.y - vertstmp[-1].co.y)
    if diff < diffy:
        verts, vertstmp = vertstmp, verts
        diff = diffy

    vertstmp.sort(key=lambda v: v.co.z) #Z coord sort

    #compare the x|y diff and the z diff
    if diff < abs((vertstmp[0].co.z - vertstmp[-1].co.z)):
        verts = vertstmp

    return verts


###################
# DATA STRUCTURES #
###################
def equals(a, b):
    return a == b

class Octree:
    """Octree object. Currently used to contain faces in order to intersect them."""
    #---------------------------------------------------------------------------
    class _OctreeNode(object):
        """Inner class of octree node. Each node correspond to a 3D box, which
        contains bounding boxes.
        """
        __slots__ = ('_children', '_children_list', '_center', '_size', '_boxes')
        def __init__(self, center, size):
            """Constructor.
            center: center of the box (Blender.Mathutils.Vector object).
            size: size of the box, ie length of a side of the cubic box (float).
            """
            self._children      = None   #children nodes (_OctreeNode).--> list of list of list ([x][y][z])
            self._children_list = None   #   "       "         "      .--> list
            self._center        = center #center of the box.
            self._size          = size   #size of the box.
            self._boxes         = []     #contained bounding boxed object.

        def __str__(self):
            """To string method (useful to debug)."""
            def _aux(node):
                #recursive function
                s = "["
                for b in node._boxes:
                    s += str(b.face.index) + ','

                if node._children_list:
                    for child in node._children_list:
                        s += _aux(child)
                s += "]"
                return s

            return _aux(self)

        def __iter__(self):
            """Iteration over all children of this node.
            yield: Octree._OctreeNode object.
            """
            if self._children_list:
                #use a stack to avoid recursion (hard to deal with generator)
                stack = [iter(self._children_list)]

                while stack:
                    try:
                        node = next(stack[-1])
                    except StopIteration:
                        stack.pop()
                    else:
                        if node._children_list:
                            stack.append(iter(node._children_list))
                        yield node

        def add_box(self, box):
            """Add a bounding boxed object ; if it can be coutained by a child
            node, it is indeed added to this child (etc...).
            box: bounding box object (currently Octree._AAB_Boxed_Face).
            """
            center = self._center
            diff   = box._center - center  #difference vector between boxes centers.
            ok     = True                  #is the box in a child.
            coords = []                    #indices in the _children attribute.

            #try to put the box in a child
            for coord, size in izip(diff, box._sizes):
                if abs(coord) > size:
                    if coord >= 0.0:
                        coords.append(1)
                    else:
                        coords.append(0)
                else:
                    ok = False
                    break

            if ok: #the box is in a child.
                if not self._children:  #children not yet created.
                    n_size         = self._size * 0.5
                    children       = [[[None, None], [None, None]], [[None, None], [None, None]]]
                    self._children = children

                    Node = Octree._OctreeNode
                    self._children_list = \
                        [Node(center + Vector((-n_size, -n_size, -n_size)), n_size),
                         Node(center + Vector((-n_size, -n_size,  n_size)), n_size),
                         Node(center + Vector((-n_size,  n_size, -n_size)), n_size),
                         Node(center + Vector((-n_size,  n_size,  n_size)), n_size),
                         Node(center + Vector(( n_size, -n_size, -n_size)), n_size),
                         Node(center + Vector(( n_size, -n_size,  n_size)), n_size),
                         Node(center + Vector(( n_size,  n_size, -n_size)), n_size),
                         Node(center + Vector(( n_size,  n_size,  n_size)), n_size)]


                    it = iter(self._children_list)

                    children[0][0][0] = next(it) ; children[0][0][1] = next(it)
                    children[0][1][0] = next(it) ; children[0][1][1] = next(it)
                    children[1][0][0] = next(it) ; children[1][0][1] = next(it)
                    children[1][1][0] = next(it) ; children[1][1][1] = next(it)

                child = self._children[coords[0]][coords[1]][coords[2]]
                child.add_box(box)

            else: #the box isn't in a child --> put it in this node.
                self._boxes.append(box)

    #---------------------------------------------------------------------------
    class _AAB_Boxed_Face:
        """A face and his Axis Aligned Bounding Box."""
        def __init__(self, face, mesh, **kw):
            """Constructor.
            face: the face (Blender.Mesh.MFace object).
            kw: used to give additional data. 'kw[key] == val' becomes 'self.key == val'.
            """
            self.face = face
            
            verts = [[v for v in mesh.vertices if equals(v.index, i)] for i in face.vertices]
            min_x, max_x = minmax(v[0].co[0] for v in verts)
            min_y, max_y = minmax(v[0].co[1] for v in verts)
            min_z, max_z = minmax(v[0].co[2] for v in verts)

            self._vmax   = Vector((max_x, max_y, max_z))
            self._vmin   = Vector((min_x, min_y, min_z))
            self._center = Vector((max_x+min_x, max_y+min_y, max_z+min_z)) * 0.5
            self._sizes  = ((max_x-min_x)*0.5, (max_y-min_y)*0.5, (max_z-min_z)*0.5)

            for key, val in kw.items():
                setattr(self, key, val)

    #---------------------------------------------------------------------------
    def __init__(self, faces, mesh, **kw):
        """Constructor.
        faces: list of the faces to contain (Blender.Mesh.MFace objects).
        kw: used to give additional data. If given, it must be lists with the
        SAME SIZE than 'faces' (1rst element correspond to faces[0], etc...).
        """
        AABB_Face = Octree._AAB_Boxed_Face

        if not kw:
            aabb_faces = [AABB_Face(f) for f in faces]
        else:
            kwargs = [{} for f in faces]
            for key, values in kw.items():
                for value, arg in izip(values, kwargs):
                    arg[key] = value

            aabb_faces = [AABB_Face(f, mesh, **arg) for f, arg in izip(faces, kwargs)]


        max_x = max(f._vmax[0] for f in aabb_faces)
        min_x = min(f._vmin[0] for f in aabb_faces)
        max_y = max(f._vmax[1] for f in aabb_faces)
        min_y = min(f._vmin[1] for f in aabb_faces)
        max_z = max(f._vmax[2] for f in aabb_faces)
        min_z = min(f._vmin[2] for f in aabb_faces)

        center = Vector((max_x+min_x, max_y+min_y, max_z+min_z)) * 0.5
        _size  = max(max_x-min_x, max_y-min_y, max_z-min_z)

        node = Octree._OctreeNode(center, _size)
        for aabb_f in aabb_faces:
            node.add_box(aabb_f)

        self._rootnode = node

    def __str__(self):
        """To string method (useful to debug)."""
        return "(Octree" + str(self._rootnode) + ")"

    def __iter__(self):
        """Iteraton over all nodes of the octree."""
        yield self._rootnode
        for res in iter(self._rootnode):
            yield res

    def aabb_faces_gen(self):
        """Da useful method !! It's a generator that yield pairs of faces that
        can collide (for intersection).
        yield: tuple of 2 Octree._AAB_Boxed_Face objects, which have these
        public attributes:
         -face: Blender.Mesh.MFace object.
         -additionnal attributes given with 'kw' to the Octree constructor.
        """
        for node in iter(self):
            if node._boxes:
                #pair of face in the same node.
                boxes  = node._boxes
                n      = len(node._boxes)
                for i, face1 in enumerate(islice(boxes, n-1)):
                    for face2 in islice(boxes, i+1, n):
                        yield face1, face2

                #a face in the node, another in a child node.
                for node2 in iter(node):
                    boxes2 = node2._boxes
                    for face1 in boxes:
                        for face2 in boxes2:
                            yield face1, face2

#-------------------------------------------------------------------------------


class BezierInterpolator:
    """Interpolate a vertex loop/string with a bezier curve."""
    def __init__(self, vertloop):
        """Constructor.
        vertloop: the vertex loop a list of vertices (Blender.Mesh.MVert object).
        If it's a true loop (and not a simple string), the first and the last
        vertices are the same vertex.
        """
        nodes = [None, None] #2 first nodes

        it = (v.co for v in vertloop)
        p0 = next(it)
        p1 = next(it)

        for p2 in it:
            vect = p2 - p0
            vect.normalize()

            nodes.append(p1 - (abs(vect.dot(p1-p0)) / 3.0) * vect)
            nodes.append(Vector(p1))
            nodes.append(p1 + (abs(vect.dot(p2-p1)) / 3.0) * vect)

            p0 = p1
            p1 = p2


        if vertloop[0].index == vertloop[-1].index: #it's a true loop
            p0 = vertloop[-2].co
            p1 = vertloop[0].co
            p2 = vertloop[1].co

            vect = p2 - p0
            vect.normalize()

            nodes[1] =   p1 + (abs(vect.dot(p2-p1)) / 3.0) * vect
            nodes.append(p1 - (abs(vect.dot(p1-p0)) / 3.0) * vect)

            tmpvect  = Vector(p0)
            nodes[0] = tmpvect
            nodes.append(tmpvect)

        else: #it's a 'false' loop: a simple edge string
            #1rst intermediate node
            p0  = vertloop[0].co
            p1  = vertloop[1].co
            p01 = nodes[2]

            nodes[0] = Vector(p0)
            nodes[1] = p0 - 2.0*project_point_vect(p01, p1, p0-p1) + p1 + p01

            #last one
            p0  = vertloop[-1].co
            p1  = vertloop[-2].co
            p01 = nodes[-1]

            nodes.append(p0 - 2.0*project_point_vect(p01, p1, p0-p1) + p1 + p01)
            nodes.append(Vector(p0))

        self._nodes = nodes

    def interpolate(self, t, vind):
        """Interpolate 2 vertices of the original vertex loop.
        t: parameter for the bezier curve - between 0.0 and 1.0.
        vind: the index of the first vertex, in the original loop
        (==> interpolation between vertloop[vind] and vertloop[vind+1])
        """
        _1_t  = 1.0 - t
        i     = 3 * vind
        nodes = self._nodes

        return nodes[i]                * (_1_t**3) + \
               nodes[i+1] * 3 *  t     * (_1_t**2) + \
               nodes[i+2] * 3 * (t**2) *  _1_t     + \
               nodes[i+3] *     (t**3)


##############
# PROJECTION #
##############

def project_point_plane(point, norm, pop):
    """Give the projected point on the plane (norm, pop).
    point: point to project (Blender.Mathutils.Vector object).
    norm: normal vector of the plane (Blender.Mathutils.Vector object).
    pop: a point that belong to the plane (Blender.Mathutils.Vector object).
    return: the projected point (Blender.Mathutils.Vector object), or None if invalid norm.
    """
    if norm.length > EPSILON:
        return point - norm.project(point - pop)

def project_vert_face(vert, face):
    """Give the projected vertex on the face.
    vert: Blender.Mesh.MVert object.
    face:Blender.Mesh.MFace object.
    return: Blender.Mathutils.Vector object, or None if invalid face.
    """
    return project_point_plane(vert.co, face.no, face.verts[0].co)

#-------------------------------------------------------------------------------

def project_vert_edge(vert, edge):
    """Projection of a vertex on an edge.
    vert: Blender.Mesh.MVert object.
    edge: Blender.Mesh.MEdge object.
    return: the projected vertex (Blender.Mathutils.Vector object)
    or None (if the edge has a null length).
    """
    o = edge.v1.co
    v = edge.v2.co - o

    if v.length > EPSILON:
        return o + v.project(vert.co - o)

def project_point_vect(point, o, vect):
    """Projection of a point on an 'affine vector'.
    point: the point (Blender.Mathutils.Vector object).
    o: start extremity of the vector (Blender.Mathutils.Vector object).
    vect: direction vector (Blender.Mathutils.Vector object).
    return: the projected vector (Blender.Mathutils.Vector object)
    """
    return o + vect.project(point - o)
#-------------------------------------------------------------------------------


################
# INTERSECTION #
################


def intersect_face_edge(face, edge):
    """Intersection between a face and an edge.
    face: Blender.Mesh.MFace object.
    edge: Blender.Mesh.MEdge object.
    """
    vec1 = face.verts[0].co
    vec2 = face.verts[1].co
    vec3 = face.verts[2].co
    orig = edge.v2.co
    ray  = orig - edge.v1.co

    p = Intersect(vec1, vec2, vec3, ray, orig)

    if not p and len(face.verts) == 4:
        vec4 = face.verts[3].co
        p    = Intersect(vec1, vec4, vec3, ray, orig)

    return p

#-------------------------------------------------------------------------------

def intersect_edge_edge(edge1, edge2):
    """Get nearest point of two lines (if they intersect, the points are merged)
    edge1, edge2: Blender.Mesh.MEdges objects.
    return: list of two Blender.Mathutils.Vector objects, or None.
    """
    return LineIntersect(edge1.v1.co, edge1.v2.co, edge2.v1.co, edge2.v2.co)

#-------------------------------------------------------------------------------

class IntersPoint(object):
    """ Represents an intersection point between 2 faces.
    this class has following attributes:
    - point: intersection point (Blender.Mathutils.Vector object).
    - face_index: index of the face which the cut edge belong to.
    - e_ind: index (in the face: 0<index<3) of the 1rst vertex that belong to
             the cut egde (index of the second: (e_ind+1)%len(face.verts) ).
    """
    __slots__ = ('point', 'face_index', 'e_ind')

    def __init__(self, point, face_index, e_ind):
        self.point      = point
        self.face_index = face_index
        self.e_ind      = e_ind

    def __str__(self):
        return "IntersPoint(" + str(self.point) + ', ' + \
                str(self.face_index) + ', ' + \
                str(self.e_ind) + ')'

def _intersect_face_tri(face, tri, edges_ind, face_index):
    """Intersection between the edges of a face and a triangle face.
    face: list of 3 or 4 Blender.Mathutils.Vector objects (vertices).
    tri: list of 3 Blender.Mathutils.Vector objects (vertices).
    edges_ind: list of tuple with 2 integers: indices of edges vertices
               in the face. (i, j) WITH j = (i+1)%len(face).
    face_index: index of the face (to build an IntersPoint object)
    """
    res = []

    for ind0, ind1 in edges_ind:
        e = face[ind0] - face[ind1]
        p = intersect_ray_tri(tri[0], tri[1], tri[2], e, face[ind1])

        if p and point_in_segment(p, face[ind0], face[ind1]):
            res.append(IntersPoint(p, face_index, ind0))

    return res

def _intersect_face_face_aux(vertices1, vertices2, face_index):
    """Intersection between the edges of a face and another face.
    vertices1: the 1rst face -> list of 3 or 4 Blender.Mathutils.Vector objects.
    vertices1: the 2nd face  -> list of 3 or 4 Blender.Mathutils.Vector objects.
    face_index: index of the 1rst face.
    """
    if len(vertices1) == 3:
        edges = ((0, 1), (1, 2), (2, 0)) #(i, (i+1)%3)
    else: #len(vertices1) == 4
        edges = ((0, 1), (1, 2), (2, 3), (3, 0)) #(i, (i+1)%4)

    #_intersect_face_tri(vertices1, (vertices2[0], vertices2[1], vertices2[2]), edges, face_index)
    #if len(vertices2) == 4:
        #_intersect_face_tri(vertices1, (vertices2[0],vertices2[3],vertices2[2]), edges, face_index)
    res = _intersect_face_tri(vertices1, (vertices2[0], vertices2[1], vertices2[2]), edges, face_index)

    if len(vertices2) == 4:
        res += _intersect_face_tri(vertices1, (vertices2[0],vertices2[3],vertices2[2]), edges, face_index)

    return res

def intersect_face_face(face1, face2, mesh):
    """Intersection between 2 faces.
    face1, face2: Blender.Mesh.MFace objects
    return: list with 2 IntersPoint object, or 0 if no intersection.
    """
    #res    = []
    v1 = [[v for v in mesh.vertices if equals(v.index, i)] for i in face1.vertices]
    v2 = [[v for v in mesh.vertices if equals(v.index, i)] for i in face2.vertices]
    verts1 = [v[0].co for v in v1]
    verts2 = [v[0].co for v in v2]

    #_intersect_face_face_aux(verts1, verts2, face1.index)
    #_intersect_face_face_aux(verts2, verts1, face2.index)
    res  = _intersect_face_face_aux(verts1, verts2, face1.index)
    res += _intersect_face_face_aux(verts2, verts1, face2.index)

    #here, if we have 4 (aligned) points, we take the 2 at the extremities
    while len(res) > 2:
        if point_in_segment(res[2].point, res[0].point, res[1].point):
            del res[2]
        elif point_in_segment(res[1].point, res[0].point, res[2].point):
            del res[1]
        else:
            del res[0]

    if len(res) == 2:
        return res

#-------------------------------------------------------------------------------


#################
# NEAREST PLANE #
#################

def vec_from_azilati(azi, lati):
    """Build a Vector with azimuth & latitudes (in degrees)"""
    azimuth  = radians(azi)
    latitude = radians(lati)
    #formula : vector = RotMat(zaxis, azi) * Vector(sin(lat), 0., cos(lat))
    sinlat = sin(latitude)
    return Vector((cos(azimuth)*sinlat, sin(azimuth)*sinlat, cos(latitude)))

def make_triplet(lst):
    """Generate triplet of elements of a list. There are C(len(lst), 3) triplets.
    lst: the list
    return: the 2 first element of the triplet, and a generator for the 3rd.
    Use 2 'for' loops to get the triplets.
    """
    n = len(lst)
    for i, elt1 in enumerate(islice(lst, n-2)):
        for j, elt2 in enumerate(islice(lst, i+1, n-1)):
            def _gen():
                for elt3 in islice(lst, j+i+2, n):
                    yield elt3
            yield elt1, elt2, _gen

def nearest_plane(verts_dic):
    """Get the nearest plane from a group of vertices.
    verts_dic: a dic {id0:vertex0, ....}.
    return: a tuple (point, normal) vector, or None if no satisfactory plane.
    """
    vertices = [Vector(v.co) for v in verts_dic.itervalues()]
    avg_p    = sum(vertices, Vector()) * (1.0/len(vertices)) #average point
    norm     = None                                          #normal vector

    #accumulators array for azimuth/latitude angles
    # azimuth : angle with X axis, in XY plane (between -89 and 90 degrees)
    # latitude: angle with Z axis (between 0 and 179 degrees)
    azi_lati = [[0.0 for i in xrange(180)] for j in xrange(180)]

    rad2deg = 180.0/pi #radians to degrees coeff (seems to be faster than math.degrees)

    for vert1, vert2, vert3_gen in make_triplet(vertices):
        vert2 -= vert1

        for vert3 in vert3_gen():
            v = CrossVecs(vert2, vert3-vert1)
            if v.x < 0.:
                v = -v

            length = v.length

            v_xy    = Vector(v.x, v.y, 0.).normalize()
            azimuth = int(round(acos(v_xy.x)*rad2deg))
            if v_xy.y < 0. and azimuth != 90:
                    azimuth = -azimuth

            v.normalize()
            latitude = int(round(acos(v.z)*rad2deg))
            if latitude == 180:
                latitude = 0

            azi_lati[azimuth+89][latitude] += length

    #look for which azimuth/latitude normal vectors are the most numerous
    max_azi_ind  = None #index of the max azimuth value
    max_lati_ind = None #index of the max latitude value
    max_acc      = -1   #maximum value of the accumulators array
    max_count    =  0   #count the values near the max value
    treshold     =  0   #if value > treshold --> value is near max value
    for azi, latitudes in enumerate(azi_lati):
        for lati, acc in enumerate(latitudes):
            if acc > treshold:
                max_count += 1
            if acc > max_acc:
                max_acc      = acc
                max_azi_ind  = azi
                max_lati_ind = lati
                max_count    = 1
                treshold     = 0.9 * max_acc

    if max_acc > -1:
        norm = vec_from_azilati(max_azi_ind-89, max_lati_ind)

    if not norm:
        return None, None

    return avg_p, norm