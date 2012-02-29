# 1: // Voronoi calculation example code
# 2: //
# 3: // Author   : Chris H. Rycroft (LBL / UC Berkeley)
# 4: // Email    : chr@alum.mit.edu
# 5: // Date     : August 30th 2011
# 6: 
# 7: #include "voro++.hh"
# 8: using namespace voro;
# 9: 
#10: // Set up constants for the container geometry
#11: const double x_min=-1,x_max=1;
#12: const double y_min=-1,y_max=1;
#13: const double z_min=-1,z_max=1;
#14: const double cvol=(x_max-x_min)*(y_max-y_min)*(x_max-x_min);
#15: 
#16: // Set up the number of blocks that the container is divided into
#17: const int n_x=6,n_y=6,n_z=6;
#18: 
#19: // Set the number of particles that are going to be randomly introduced
#20: const int particles=20;
#21: 
#22: // This function returns a random double between 0 and 1
#23: double rnd() {return double(rand())/RAND_MAX;}
#24: 
#25: int main() {
#26:         int i;
#27:         double x,y,z;
#28: 
#29:         // Create a container with the geometry given above, and make it
#30:         // non-periodic in each of the three coordinates. Allocate space for
#31:         // eight particles within each computational block
#32:         container con(x_min,x_max,y_min,y_max,z_min,z_max,n_x,n_y,n_z,
#33:                         false,false,false,8);
#34: 
#35:         // Randomly add particles into the container
#36:         for(i=0;i<particles;i++) {
#37:                 x=x_min+rnd()*(x_max-x_min);
#38:                 y=y_min+rnd()*(y_max-y_min);
#39:                 z=z_min+rnd()*(z_max-z_min);
#40:                 con.put(i,x,y,z);
#41:         }
#42: 
#43:         // Sum up the volumes, and check that this matches the container volume
#44:         double vvol=con.sum_cell_volumes();
#45:         printf("Container volume : %g\n"
#46:                "Voronoi volume   : %g\n"
#47:                "Difference       : %g\n",cvol,vvol,vvol-cvol);
#48: 
#49:         // Output the particle positions in gnuplot format
#50:         con.draw_particles("random_points_p.gnu");
#51: 
#52:         // Output the Voronoi cells in gnuplot format
#53:         con.draw_cells_gnuplot("random_points_v.gnu");

from object_destruction.libvoro import voronoi
import random
from mathutils import Vector
import bpy
from bpy import ops
#import bmesh

def bracketPair(line, lastIndex):
    opening = line.index("(", lastIndex)
    closing = line.index(")", opening)
    
    print(opening, closing)
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
        
         print("VERTSFACES:", verts, faces) 
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
                faces.append([index, index1, index2])
                assert(len(set(faces[-1])) == 3)
                    
               
        ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.name = name
        
        mesh = obj.data
        print("Creating new mesh")
        nmesh = bpy.data.meshes.new(name = mesh.name)
        
        print("Building new mesh")
        print(edges, faces)
        nmesh.from_pydata(verts, edges, faces)
   
        print("Removing old mesh")    
        obj.data = None
       # mesh.user_clear()
        #if (mesh.users == 0):
        #    bpy.data.meshes.remove(mesh)
   
        print("Assigning new mesh")
        nmesh.update(calc_edges=True) 
        nmesh.validate()    
        obj.data = nmesh
        print("Mesh Done")
        
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
    
    print ("InVORONOICube")
    volume = None
    print("Volume", vol)
    if vol == None or vol == "":
        volume = obj
    else:
        volume = context.scene.objects[vol]
    
    xmin, xmax, ymin, ymax, zmin, zmax = corners(obj)   
     
    nx = 12
    ny = 12
    nz = 12
    particles = parts

    print(xmin, xmax, ymin, ymax, zmin, zmax)
    con = voronoi.domain(xmin,xmax,ymin,ymax,zmin,zmax,nx,ny,nz, False, False, False, particles)
    print("After")
    
    xmin, xmax, ymin, ymax, zmin, zmax = corners(volume)
    
    #add a wall object
  #  ops.object.mode_set(mode = 'EDIT')
 #   bm = bmesh.from_mesh(obj.data)
    bm = obj.data
#    ops.mesh.select_all(action = 'SELECT')
  #  ops.mesh.flip_normals()
    
 #   print("After bmesh")
    colist = []
    i = 0
    for poly in bm.polygons:
       # n = p.calc_center_median()
        n = poly.normal
        v = bm.vertices[poly.vertices[0]].co
        d = n.dot(v)
        print("Displacement: ", d)
        colist.append([n[0], n[1], n[2], d, i])
        i = i+1
    
#    ops.mesh.flip_normals()    
 #   ops.object.mode_set(mode = 'OBJECT')
    
    print("After colist")
   # print(colist)
    con.add_wall(colist)
  #  print("After wall")
    
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
        #if con.point_inside(x, y, z):
        con.put(i, x, y, z)
    
  #  d.add_wall(colist)
        
    name = "test.out"
    con.print_custom("%P v %t", name )
    
    
    records = parseFile(name)
    buildCellMesh(records, obj.name)   
    
    context.scene.objects.unlink(obj) 