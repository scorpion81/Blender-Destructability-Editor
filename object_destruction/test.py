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


def voronoiCube(context, objects, parts):
    obj = context.active_object
    
    print ("InVORONOICube")
    bbox = obj.bound_box.data 
    dims = bbox.dimensions
    loc = bbox.location
    
    lowCorner = (loc[0] - dims[0] / 2, loc[1] - dims[1] / 2, loc[2] - dims[2] / 2)
    values = []
    #verts = bbox.data.vertices
    #dims = [2, 2, 2]
    #lowCorner = [-1, -1, -1]
    xmin = lowCorner[0]
    xmax = lowCorner[0] + dims[0]
    ymin = lowCorner[1]
    ymax = lowCorner[1] + dims[1]
    zmin = lowCorner[2]
    zmax = lowCorner[2] + dims[2]
     
    nx = 6
    ny = 6
    nz = 6
    particles = parts

    d = voronoi.domain(xmin,xmax,ymin,ymax,zmin,zmax,nx,ny,nz, False, False, False, particles)
    
    for i in range(0, parts):# - len(verts)):
        randX = random.uniform(xmin, xmax)
        randY = random.uniform(ymin, ymax)
        randZ = random.uniform(zmin, zmax)
        values.append((randX, randY, randZ))
  
    for i in range(0, parts):
        x = values[i][0]
        y = values[i][1]
        z = values[i][2]
        d.put(i, x, y, z)

    d.print_custom("%P v %t f %f", "test.out")
    
def parseFile():
#    read array from file
     file = open("test.out")
     verts = []
#    #have a big string, need to parse ( and ), then split by ,
     #vertex part
     next = None
     lastIndex = 0
     while next != 'v':
        opening = file.index("(", lastIndex)
        closing = file.index(")", lastIndex)
        triplet = file[opening:closing]
        vals = triplet.split(",")
        x = float(vals[0])
        y = float(vals[1])
        z = float(vals[2])
        verts.append((x,y,z))
     
        lastIndex = closing
        next = file[closing+1]
    
     
     while next != 'f':
        opening = file.index("(", lastIndex)
        closing = file.index(")", lastIndex)
        triplet = file[opening:closing]
        vals = triplet.split(",")
        x = float(vals[0])
        y = float(vals[1])
        z = float(vals[2])
        verts.append((x,y,z))
     
        lastIndex = closing
        next = file[closing+1]
     
     
     
     
     
    
#def drawMesh():
#    
#    #
#    
#    
#    
#    verts = []
#    faces = []
#    for t in Side.__hull__:
#        length = len(verts)
#        print("Normal: ", t.n)
#        v1 = Vector((t.p1[0], t.p1[1], t.p1[2]))
#        v2 = Vector((t.p2[0], t.p2[1], t.p2[2]))
#        v3 = Vector((t.p3[0], t.p3[1], t.p3[2]))
#        
#        verts.append(v1)
#        verts.append(v2)
#        verts.append(v3)
#        rev = verts[::-1]
#        first = rev.index(v1) + length
#        second = rev.index(v2) + length
#        third = rev.index(v3) + length
#        faces.append([first, second, third])
#        print("Face: ", [first, second, third])#
#
#    obj = bpy.context.active_object
#    mesh = obj.data
#    print("Creating new mesh")
#    nmesh = bpy.data.meshes.new(name = mesh.name)

#    print("Building new mesh")
#    nmesh.from_pydata(verts, [], faces)
#   
#    print("Removing old mesh")    
#    obj.data = None
#    mesh.user_clear()
#    if (mesh.users == 0):
#        bpy.data.meshes.remove(mesh)
#   
#    print("Assigning new mesh")     
#    obj.data = nmesh 
    
#voronoiCube(20)