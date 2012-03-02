

import platform

if platform.architecture()[0] == "64bit":
    if platform.architecture()[1] == "ELF":
        from object_destruction.libvoro.linux64 import voronoi
    elif platform.architecture()[1] == "WindowsPE":
        extname = "win64/voronoi"
        from object_destruction.libvoro.win64 import voronoi
elif platform.architecture[0]() == "32bit":
    if platform.architecture[1]() == "ELF":
        from object_destruction.libvoro.linux32 import voronoi
    elif platform.architecture()[1] == "WindowsPE":
       from object_destruction.libvoro.win32 import voronoi

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
        
        ops.object.origin_set(type='ORIGIN_GEOMETRY')
        ops.object.mode_set(mode = 'EDIT')
        ops.mesh.normals_make_consistent(inside=False)
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

def voronoiCube(context, obj, parts, vol):
    
    #applyscale before
    loc = Vector(obj.location)
    ops.object.transform_apply(scale=True, location = True)
   
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
    
    #enlarge container a bit, so parts near the border wont be cut off
    theta = 10
    con = voronoi.domain(xmin-theta,xmax+theta,ymin-theta,ymax+theta,zmin-theta,zmax+theta,nx,ny,nz,False, False, False, particles)
    
    if vol == None or vol == "":
        pass
    else:
        xmin, xmax, ymin, ymax, zmin, zmax = corners(context.scene.objects[vol])
        xmin += loc[0]
        xmax += loc[0]
        ymin += loc[1]
        ymax += loc[1]
        zmin += loc[2]
        zmax += loc[2] 
    
    bm = obj.data
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
    for i in range(0, particles):# - len(verts)):
        randX = random.uniform(xmin, xmax)
        randY = random.uniform(ymin, ymax)
        randZ = random.uniform(zmin, zmax)
        values.append((randX, randY, randZ))
  
    for i in range(0, particles):
        x = values[i][0]
        y = values[i][1]
        z = values[i][2]
       # if con.point_inside(x, y, z):
        print("Inserting", x, y, z)
        con.put(i, x, y, z)
    
  #  d.add_wall(colist)
        
    name = "test.out"
    con.print_custom("%P v %t", name )
    
    del con
    records = parseFile(name)
    buildCellMesh(records, obj.name)   
    
    context.scene.objects.unlink(obj) 