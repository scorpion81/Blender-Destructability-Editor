import bge
from bge import logic, constraints
from mathutils import Vector
import math
import random
# set hitpoints according to distance from ground and center
# the farther away from the center the more hitpoints
# map hitpointX, hitpointY to dimensionsX, dimensionsY (boundingbox of original) or set empty manually before

#create empty, store bbox dimensions as properties
#call fracture script

# for all shards (Name.xxx) 
# get dist to shard - center, get distY shard - center
# calc hitpointHorz: round(dist/maxDist + 0.1 * 100) (for instance, +0.x because shard at center might get 0 hitpoints)
# calc hitpointVert: distGround/bboxZ * 100 
# hitpoint = hpHorz * hpVert
# add all hitpoints, store as Prop in empty ? 

scene = logic.getCurrentScene()
center = scene.objects["Empty"]
ground = scene.objects["Ground"]
cellSize = 2
cells = []
center.suspendDynamics()
shards = [s for s in scene.objects if s.name.startswith("Cube")]
centers = [c for c in scene.objects if c.name.startswith("Center")]

class Cell:

    signs = { 0 : "--+",
              1 : "-++", 
              2 : "+++",
              3 : "+-+",
              4 : "---",
              5 : "-+-",
              6 : "++-",
              7 : "+--" }
              
    faceIndexes  = { 0: [0,1,2,3], 
                     1: [4,5,6,7],
                     2: [0,1,4,5],
                     3: [2,3,6,7],
                     4: [0,3,4,7],
                     5: [1,2,5,6] } 
    doReturn = False
    
    def __init__(self, center):
        self.faces = {}
        self.vertices = {}
        #have no faces to use, must define logical vertices/faces according to cell center/cell size
        # faces
        # 0 - top
        # 1 - bottom
        # 2 - left
        # 3 - right
        # 4 - front
        # 5 - back
        self.mid = center.worldPosition
        self.center = center
        self.children = []
        for o in shards:
            if o.worldPosition[0] >= self.mid[0] - 1 and o.worldPosition[0] <= self.mid[0] + 1 and \
               o.worldPosition[1] >= self.mid[1] - 1 and o.worldPosition[1] <= self.mid[1] + 1 and \
               o.worldPosition[2] >= self.mid[2] - 1 and o.worldPosition[2] <= self.mid[2] + 1:
                   self.children.append(o)
                   
        self.count = len(self.children) 
                   
        print("Center: ", self.mid)
        self.name = center.name
        half = cellSize / 2
        #eval "center[i]" + signs[j][i] + "half" 
        for i in range(0,8):
            vertex = []
            for j in range (0,3):
                strg = "self.mid[" + str(j)  + "] " + self.signs[i][j] + " half"
                #print(strg)
                vertex.append(eval(strg))
            self.vertices[i] = Vector(vertex)
        
        for i in range(0,6):
            vertList = []
            for j in range(0,4):
                vertList.append(self.vertices[self.faceIndexes[i][j]])
            face = sorted(vertList)
            self.faces[i] = face
        #print(len(self.faces))
        
    
    def getNeighbor(self, index):
        #test whether "opposite" face has same Vertex coordinates
        oppIndex = -1
        if (index % 2 == 0):
            oppIndex = index + 1
        else:
            oppIndex = index - 1
        
        face = self.faces[index]
        for cell in cells:
            oppFace = cell.faces[oppIndex]
            match = True
            for i in range(0,4):
               # print(face[i], " <==> ", oppFace[i])
                match = match and face[i] == oppFace[i]
            if match:
                return cell
            
        return None
    
    def isGroundCell(self):
        return round(self.mid[2]) == 1
    
    def integrity(self, intgr):
        return len(self.children) / self.count > intgr
        
    
    def destructionList(self, destList):
        
        if Cell.doReturn:
            return
        
        if self.isGroundCell():
            destList.append(self)
            Cell.doReturn = True
            return
        
        for i in range(0,6):
            neighbor = self.getNeighbor(i)
            if neighbor != None and not neighbor in destList:
                destList.append(neighbor)
                if neighbor.integrity(0.45):
                    neighbor.destructionList(destList)
                 
        destList.append(self)
    
    def destroyCells(self):
        
        destList = []
        self.destructionList(destList)
        
        Cell.doReturn = False
        
        for cell in destList:
            if cell.isGroundCell() and cell.integrity(0.45):
                return
            
        #destroy unconnected cells -> enable physics within radius -> fuzzy
        for cell in destList:
            if cell in cells:
                cells.remove(cell)
            
                print("Destroyed: ", cell.mid)
                for o in cell.children:
                    o.restoreDynamics()
                   
def setup():    
    for c in centers:
       c.suspendDynamics() 
       c["hit"] = True
       cells.append(Cell(c))
            
    for s in shards:
        s.suspendDynamics()
        
        
def collide():
    scene = logic.getCurrentScene()
    control = logic.getCurrentController()
    coll = control.sensors["Collision"]
    
    if coll.status == logic.KX_SENSOR_JUST_ACTIVATED:
        impact = coll.hitObject.worldPosition

        for o in shards:
          #  vec = impact - o.worldPosition
          #  dist = vec.length
            if o.getDistanceTo(impact) < 1.5:
                for cell in cells:
                    if o in cell.children:
                        cell.children.remove(o)
                o.restoreDynamics()
                
        cels = [d for d in cells]
        for c in cels:
            c.destroyCells()

def blow():
    ground = scene.objects["Ground"]
    
    tocollapse = [c for c in cells if c.mid[2] > 1]
    for c in tocollapse:
        for s in c.children:
            s.setParent(center, True, True)
            
   # center.applyRotation((0, math.radians(15), 0))
        
    toblow = [c for c in cells if c.mid[2] == 1]
    for b in toblow:
        for s in b.children:
            if not s.invalid:
                s.restoreDynamics()
            
    center.restoreDynamics()
    [c.restoreDynamics() for c in centers]
    
def collapse():
    control = logic.getCurrentController()
    coll = control.sensors["Touch"]
    cellC = [c for c in coll.hitObjectList if c.name.startswith("Center")]
    cell = [c for c in cells for ce in cellC if ce == c.center]
    print(len(cell))
    for c in cell:
        if "hit" in c.center:
            del c.center["hit"]
        for s in c.children:
           if not s.invalid:
                s.removeParent()
                randomDisplay(s)
                
   #     for x in shards:
   #         if not x.invalid:
   #             if x.getDistanceTo(cell) < 2:
   #                 x.removeParent()
   #                 randomDisplay(x)
                     

def randomDisplay(s):   
    rnd = random.random()
    if rnd < 0.65:
        s.endObject()
    else:
        s.restoreDynamics() 
    
         
 
    
    
              