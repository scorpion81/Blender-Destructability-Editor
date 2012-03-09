import platform

if platform.architecture()[0] == "64bit":
    if platform.architecture()[1] == "ELF":
        from object_destruction.libvoro.linux64 import voronoi
    elif platform.architecture()[1] == "WindowsPE":
        extname = "win64/voronoi"
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
#import bmesh

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
         
def buildCellMesh(cells, name):      
     
    for cell in cells:
        # for each face
        verts = []
        faces = []
        edges = []
        
        length = 0
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
                
               # edges.append([index, index1])
            #    edges.append([index1, index2])
             #   edges.append([index2, index])   
                if (index == index1) or (index == index2) or \
                (index2 == index1):
                    continue
                else: 
                    faces.append([index, index1, index2])
                #assert(len(set(faces[-1])) == 3)
                    
        ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.name = name
        obj.parent = bpy.context.scene.objects[name].parent
     #   obj.location += loc         
        
        mesh = obj.data
    #    print("Creating new mesh")
        nmesh = bpy.data.meshes.new(name = name)
        
   #     print("Building new mesh")
       # print(edges, faces)
        nmesh.from_pydata(verts, edges, faces)
   
   #     print("Removing old mesh")    
        obj.data = None
        #mesh.user_clear()
        #if (mesh.users == 0):
        #    bpy.data.meshes.remove(mesh)
   
       # print("Assigning new mesh")
        nmesh.update(calc_edges=True) 
        nmesh.validate()    
        obj.data = nmesh
      #  obj.name = nmesh.name
      #  print("Mesh Done")
        obj.select = True
        ops.object.origin_set(type='ORIGIN_GEOMETRY')
        ops.object.material_slot_copy()
        obj.select = False
        ops.object.mode_set(mode = 'EDIT')
        ops.mesh.normals_make_consistent(inside=False)
      #  ops.mesh.dissolve_limited()
        ops.object.mode_set(mode = 'OBJECT')

def corners(obj):
    
    bbox = obj.bound_box.data 
    dims = bbox.dimensions
    loc = bbox.location
    
    lowCorner = (loc[0] - dims[0] / 2, loc[1] - dims[1] / 2, loc[2] - dims[2] / 2)
    xmin = lowCorner[0]
    xmax = lowCorner[0] + dims[0]
    ymin = lowCorner[1]
    ymax = lowCorner[1] + dims[1]
    zmin = lowCorner[2]
    zmax = lowCorner[2] + dims[2]
    
    return xmin, xmax, ymin, ymax, zmin, zmax 

def voronoiCube(context, obj, parts, vol, walls):
    
    #applyscale before
    loc = Vector(obj.location)
    obj.destruction.tempLoc = loc
    context.scene.objects.active = obj
    obj.select = True
    ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')
    ops.object.transform_apply(scale=True, location = True, rotation=True)
    obj.select = False
   
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
    
    #enlarge container a bit, so parts near the border wont be cut off
    theta = 0.25
    if walls:
        theta = 10
    con = voronoi.domain(xmin-theta,xmax+theta,ymin-theta,ymax+theta,zmin-theta,zmax+theta,nx,ny,nz,False, False, False, particles)
    
    if vol == None or vol == "":
        pass
    else:
        volobj = context.scene.objects[vol]
        volobj.select = True
        ops.object.transform_apply(scale=True, location = True, rotation = True)
        volobj.select = False
        
        xmin, xmax, ymin, ymax, zmin, zmax = corners(volobj)
        xmin += loc[0]
        xmax += loc[0]
        ymin += loc[1]
        ymax += loc[1]
        zmin += loc[2]
        zmax += loc[2] 
    
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
#        volobj.select = True
#        ops.object.transform_apply(scale=True)
#        volobj.select = False
        
        for v in volobj.data.vertices:
            values.append((v.co[0], v.co[1], v.co[2]))
        
    else:    
        for i in range(0, particles):
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
    records = parseFile(name)
    
    context.scene.objects.active = obj
    buildCellMesh(records, obj.name)
    
    if not walls:
        
        if obj.destruction.remesh_depth > 0:
            rem = obj.modifiers.new("Remesh", 'REMESH')
            rem.mode = 'SHARP'
            rem.octree_depth = obj.destruction.remesh_depth
            rem.scale = 0.9
            rem.sharpness = 1.0
            rem.remove_disconnected_pieces = False
            #  rem.threshold = 1.0
       
            context.scene.objects.active = obj
            ctx = context.copy()
            ctx["object"] = obj
            ops.object.modifier_apply(ctx, apply_as='DATA', modifier="Remesh")
               
        for o in context.scene.objects:
            if o.name not in oldnames:
                context.scene.objects.active = o
                booleanIntersect(context, o, obj)
                if len(o.data.vertices) == 0:
                    context.scene.objects.unlink(o)
                else:
                    oldnames.append(o.name)
           
  #  context.scene.objects.unlink(obj) 
    
def booleanIntersect(context, o, obj):
    #rem = o.modifiers.new("Remesh", 'REMESH')    
    bool = o.modifiers.new("Boolean", 'BOOLEAN')
    bool.object = obj
    bool.operation = 'INTERSECT'
    
    mesh = o.to_mesh(context.scene, 
                    apply_modifiers=True, 
                    settings='PREVIEW')
                         
    old_mesh = o.data
    o.data = None
    old_mesh.user_clear()
        
    if (old_mesh.users == 0):
        bpy.data.meshes.remove(old_mesh)  
            
    o.data = mesh  
    o.modifiers.remove(bool)
    
    ops.object.mode_set(mode = 'EDIT')
    ops.mesh.separate(type = 'LOOSE')
    ops.object.mode_set(mode = 'OBJECT')
    
    o.select = True
    ops.object.origin_set(type='ORIGIN_GEOMETRY')
    o.select = False