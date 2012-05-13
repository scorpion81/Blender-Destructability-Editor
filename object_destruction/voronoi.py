import platform
from time import clock
#from concurrent.futures import ThreadPoolExecutor, wait
import threading
import math

if platform.architecture()[0] == "64bit":
    if platform.architecture()[1] == "ELF":
        from object_destruction.libvoro.linux64 import voronoi
    elif platform.architecture()[1] == "WindowsPE":
        from object_destruction.libvoro.win64 import voronoi
    else:
        from object_destruction.libvoro.osx64 import voronoi
elif platform.architecture()[0] == "32bit":
    if platform.architecture()[1] == "ELF":
        from object_destruction.libvoro.linux32 import voronoi
    elif platform.architecture()[1] == "WindowsPE":
        from object_destruction.libvoro.win32 import voronoi
    else:
        from object_destruction.libvoro.osx32 import voronoi

#from object_destruction.libvoro import voronoi
import random
from mathutils import Vector
import bpy
from bpy import ops
import bmesh

from . import destruction_data as dd

#start = 0

selected = {}
#

def bracketPair(line, lastIndex):
    opening = line.index("(", lastIndex)
    closing = line.index(")", opening)
    
   # print(opening, closing)
    values = line[opening+1:closing]
    vals = values.split(",")
    return vals, closing
    
def parseFile(name):
#    read array from file
     file = open(name)
     records = []
     for line in file:
         verts = []
         faces = []
         areas = []
    #    #have a big string, need to parse ( and ), then split by ,
         #vertex part
         next = None
         lastIndex = 0
         while next != 'v':
            vals, closing = bracketPair(line, lastIndex)
            x = float(vals[0])
            y = float(vals[1])
            z = float(vals[2])
            verts.append((x,y,z))
            lastIndex = closing
            next = line[closing+2]
        
         while True:
            facetuple = []
          #  print(lastIndex, len(line), next)
            try:
                vals, closing = bracketPair(line, lastIndex)
                for f in vals:
                    facetuple.append(int(f))
                faces.append(facetuple)
                lastIndex = closing
            except ValueError:
                break
        
       #  print("VERTSFACES:", verts, faces) 
         records.append({"v": verts, "f": faces})
     return records    

def buildCell(cell, name, walls):
 # for each face
    #global start
    
    verts = []
    faces = []
    edges = []
    
    for i in range(0, len(cell["f"])):
        v = []
        #get corresponding vertices
        for index in cell["f"][i]:
          #  print(index)
            vert = cell["v"][index]
            v.append(vert)
            if vert not in verts:
                verts.append(vert)
                    
        for j in range(1, len(v)-1):
            index = verts.index(v[0])
            index1 = verts.index(v[j])
            index2 = verts.index(v[j+1]) 
            
            if (index == index1) or (index == index2) or \
            (index2 == index1):
                continue
            else: 
                faces.append([index, index1, index2])
            #assert(len(set(faces[-1])) == 3)
            
  #  lock.acquire()
     
    nmesh = bpy.data.meshes.new(name = name)
    nmesh.from_pydata(verts, edges, faces)
    
    ops.mesh.primitive_cube_add()
    obj = bpy.context.active_object
    obj.name = name
    obj.parent = bpy.context.scene.objects[name].parent
   
    obj.data = None
 #  nmesh.update(calc_edges=True) 
 #   nmesh.validate()    
    obj.data = nmesh
    obj.select = True
    ops.object.origin_set(type='ORIGIN_GEOMETRY')
    ops.object.material_slot_copy()
    obj.select = False
    
    ops.object.mode_set(mode = 'EDIT')
    ops.mesh.normals_make_consistent(inside=False)
    
    if walls:
        ops.mesh.dissolve_limited(angle_limit = math.radians(2.5))
    ops.object.mode_set(mode = 'OBJECT')
    
#    lock.release()
    
   
    
    #print("Object assignment Time ", clock() - start)
   # start = clock()
    
         
def buildCellMesh(cells, name, walls):      
    

#     lock = threading.Lock()     
#     threads = [threading.Thread(target=buildCell, args=(cell, name, walls, lock)) for cell in cells]
#
#     print("Starting threads...")
#        
#     for t in threads:
#        t.start()
#        
#     print("Waiting for threads to finish...")
#        
#     for t in threads:
#        t.join()       
       
    for cell in cells: 
        buildCell(cell, name, walls)
        

def corners(obj, impactLoc = Vector((0,0,0))):
    
    bbox = obj.bound_box.data 
    dims = bbox.dimensions
    loc = bbox.location
    loc += impactLoc
    print("corners impact:", impactLoc)
    
    lowCorner = (loc[0] - dims[0] / 2, loc[1] - dims[1] / 2, loc[2] - dims[2] / 2)
    xmin = lowCorner[0]
    xmax = lowCorner[0] + dims[0]
    ymin = lowCorner[1]
    ymax = lowCorner[1] + dims[1]
    zmin = lowCorner[2]
    zmax = lowCorner[2] + dims[2]
    
    return xmin, xmax, ymin, ymax, zmin, zmax 

def deselect(obj):
    selected[obj] = obj.select
    obj.select = False

def select(obj):
    if obj in selected.keys():
        obj.select = selected[obj]    

def voronoiCube(context, obj, parts, vol, walls):
    
    #applyscale before
   # global start
    start = clock()
    loc = Vector(obj.location)
    obj.destruction.tempLoc = loc
    
    if vol != None and vol != "":
        print("USING VOL")
        volobj = context.scene.objects[vol]
        volobj.select = True
        ops.object.origin_set(type='GEOMETRY_ORIGIN')
        ops.object.transform_apply(scale=True, rotation = True)
        volobj.select = False
        
        print("I: ", dd.DataStore.impactLocation)
        vxmin, vxmax, vymin, vymax, vzmin, vzmax = corners(volobj, dd.DataStore.impactLocation - loc)
        vxmin += loc[0]
        vxmax += loc[0]
        vymin += loc[1]
        vymax += loc[1]
        vzmin += loc[2]
        vzmax += loc[2] 
        
    
    [deselect(o) for o in context.scene.objects]
      
    context.scene.objects.active = obj    
    obj.select = True
    if not walls:
        ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')
    else:
        ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        
    ops.object.transform_apply(scale=True, location = True, rotation=True)
    
    [select(o) for o in context.scene.objects]
  
    xmin, xmax, ymin, ymax, zmin, zmax = corners(obj)
          
    xmin += loc[0]
    xmax += loc[0]
    ymin += loc[1]
    ymax += loc[1]
    zmin += loc[2]
    zmax += loc[2] 
     
    nx = 12
    ny = 12
    nz = 12
    particles = parts

    print(xmin, xmax, ymin, ymax, zmin, zmax)
    
    if vol != None and vol != "" and context.object.destruction.voro_exact_shape:
        volobj = context.scene.objects[vol]
        particles = len(volobj.data.vertices)
    
    partsystem = None    
    if context.object.destruction.voro_particles != "":
        partsystemname = context.object.destruction.voro_particles
        volobj = context.scene.objects[vol]
        partsystem = volobj.particle_systems[partsystemname]
        particles = len(partsystem.particles)
    
    #enlarge container a bit, so parts near the border wont be cut off
    theta = 0.25
    if walls:
        theta = 10
    con = voronoi.domain(xmin-theta,xmax+theta,ymin-theta,ymax+theta,zmin-theta,zmax+theta,nx,ny,nz,False, False, False, particles)
    
    if vol != None and vol != "":
        xmin = vxmin
        xmax = vxmax
        ymin = vymin
        ymax = vymax
        zmin = vzmin
        zmax = vzmax
        print("VOL: ", xmin, xmax, ymin, ymax, zmin, zmax)
        
    
    bm = obj.data
    
    if walls:
        colist = []
        i = 0
        for poly in bm.polygons:
           # n = p.calc_center_median()
            n = poly.normal
            v = bm.vertices[poly.vertices[0]].co
            d = n.dot(v)
           # print("Displacement: ", d)
            colist.append([n[0], n[1], n[2], d, i])
            i = i+1
        
        #add a wall object per face    
        con.add_wall(colist)
    
    values = []
    
    if vol != None and vol != "" and context.object.destruction.voro_exact_shape:
        volobj = context.scene.objects[vol]
        context.scene.objects.active = volobj
        
        volobj.select = True
        ops.object.transform_apply(scale=True, location = True, rotation = True)
        volobj.select = False
                
        for v in volobj.data.vertices:
            values.append((v.co[0], v.co[1], v.co[2]))
            
    elif partsystem != None:
        for p in partsystem.particles:
            values.append((p.location[0] + dd.DataStore.impactLocation[0], 
                           p.location[1] + dd.DataStore.impactLocation[1], 
                           p.location[2] + dd.DataStore.impactLocation[2]))    
    else:    
        for i in range(0, particles):
            
            print (xmin, xmax, ymin, ymax, zmin, zmax)
            randX = random.uniform(xmin, xmax)
            randY = random.uniform(ymin, ymax)
            randZ = random.uniform(zmin, zmax)
            values.append((randX, randY, randZ))
  
    for i in range(0, particles):
        x = values[i][0]
        y = values[i][1]
        z = values[i][2]
        #if con.point_inside(x, y, z):
        print("Inserting", x, y, z)
        con.put(i, x, y, z)
    
  #  d.add_wall(colist)
        
    name = obj.destruction.voro_path
    con.print_custom("%P v %t", name )
    
    del con
    
    oldnames = [o.name for o in context.scene.objects]
   
    print("Library Time ", clock() - start)
    start = clock()
    
    records = parseFile(name)
    print("Parsing Time ", clock() - start)
    start = clock()
    
    
    context.scene.objects.active = obj
    buildCellMesh(records, obj.name, walls)
    
    print("Mesh Construction Time ", clock() - start)
    start = clock()
    
    if not walls:
        
        context.scene.objects.active = obj
        if obj.destruction.remesh_depth > 0:
            rem = obj.modifiers.new("Remesh", 'REMESH')
            rem.mode = 'SHARP'
            rem.octree_depth = obj.destruction.remesh_depth
            rem.scale = 0.9
            rem.sharpness = 1.0
            rem.remove_disconnected_pieces = False
            #  rem.threshold = 1.0
       
            #context.scene.objects.active = obj
            ctx = context.copy()
            ctx["object"] = obj
            ctx["modifier"] = rem
            ops.object.modifier_apply(ctx, apply_as='DATA', modifier = rem.name)
        
        [deselect(o) for o in context.scene.objects]
        
        #try to fix non-manifolds...
        ops.object.mode_set(mode = 'EDIT')
        ops.mesh.remove_doubles()
        ops.mesh.select_all(action = 'DESELECT')
        ops.mesh.select_non_manifold()
        #ops.mesh.edge_collapse()
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if len(v.link_edges) < 3 and v.select]
        for v in verts:
            print(len(v.link_edges))
            bm.verts.remove(v)
            
        ops.mesh.select_all(action = 'DESELECT')
        ops.mesh.select_non_manifold()
        ops.mesh.edge_collapse()   
        ops.object.mode_set(mode = 'OBJECT')
        
        newnames = []       
        for o in context.scene.objects:
            if o.name not in oldnames:
                context.scene.objects.active = o
                newnames.extend(booleanIntersect(context, o, obj, oldnames))
                if len(o.data.vertices) == 0:
                   context.scene.objects.unlink(o)
                else:
                    oldnames.append(o.name)
                    
        for n in newnames:
            if n not in oldnames and n in context.scene.objects:
                ob = context.scene.objects[n]
                context.scene.objects.active = ob
                ob.select = True
                ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                ob.select = False
                oldnames.append(ob.name)
                       
        [select(o) for o in context.scene.objects]
        print("Boolean Time ", clock() - start)      
  #  context.scene.objects.unlink(obj) 
    
def booleanIntersect(context, o, obj, oldnames):  
            
    bool = o.modifiers.new("Boolean", 'BOOLEAN')
    #use the original boolean object always, otherwise boolean op errors occur...
    bool.object = obj
 #    bool.object = bpy.data.objects[obj.destruction.boolean_original]
    bool.operation = 'INTERSECT'
    
    ctx = context.copy()
    ctx["object"] = o
    ctx["modifier"] = bool
    ops.object.modifier_apply(ctx, apply_as='DATA', modifier = bool.name)
    
    ops.object.mode_set(mode = 'EDIT')
    ops.mesh.dissolve_limited(angle_limit = math.radians(2.5))
    ops.mesh.separate(type = 'LOOSE')
    ops.object.mode_set(mode = 'OBJECT')
    
    newnames = []
    for ob in context.scene.objects:
        if ob.name not in oldnames and ob.name != o.name:
           newnames.append(ob.name)
    
    oldSel = o.select  
    o.select = True
    ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    o.select = oldSel
    
    return newnames    
   