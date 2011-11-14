#cell contains: pieces of parent in range of cell size
# a cell size, a cell location(x,y,z), neighbors for quick access, retrieved from grid

#grid provides access to cells via x,y,z indexing, has a size and cell count to calculate cell sizes
#

#each object has a destruction dataset in context, to get it to game engine store it externally or maybe all custom properties will be converted ? could even work like that
#but for standalone mode no bpy may be used !
#and here no bge may be used, need to be clean data objects
from mathutils import geometry, Vector

class Cell:
    
    def __init__(self, gridPos, grid):
        self.gridPos = gridPos
        self.grid = grid
        cellDim = grid.cellDim
        self.center = ((gridPos[0] + 0.5) * cellDim[0] + grid.pos[0], 
                       (gridPos[1] + 0.5) * cellDim[1] + grid.pos[1], 
                       (gridPos[2] + 0.5) * cellDim[2] + grid.pos[2]) 
                       
        self.range = [(self.center[0] - cellDim[0] / 2, self.center[0] + cellDim[0] / 2),
                      (self.center[1] - cellDim[1] / 2, self.center[1] + cellDim[1] / 2),
                      (self.center[2] - cellDim[2] / 2, self.center[2] + cellDim[2] / 2)] 
                                         
        self.children = [c.name for c in grid.children if self.isInside(c.worldPosition)]
        self.count = len(self.children)
        print("Cell created: ", self.center, self.count)
        self.isGroundCell = False
    
    def integrity(self, intgr):
        if self.count == 0:
            return False
        return len(self.children) / self.count > intgr     
            
    def isInside(self, pos):
       # print("Child: ", c, c.worldPosition, self.range) 
        
        if pos[0] >= self.range[0][0] and pos[0] <= self.range[0][1] and \
           pos[1] >= self.range[1][0] and pos[1] <= self.range[1][1] and \
           pos[2] >= self.range[2][0] and pos[2] <= self.range[2][1]:
               return True
           
        return False
    
    def findNeighbors(self):
    
        back = None
        if self.gridPos[1] < self.grid.cellCounts[1] - 1:
            back = self.grid.cells[(self.gridPos[0], self.gridPos[1] + 1, self.gridPos[2])]
         
        front = None
        if self.gridPos[1] > 0:
            front = self.grid.cells[(self.gridPos[0], self.gridPos[1] - 1, self.gridPos[2])]
            
        left = None
        if self.gridPos[0] < self.grid.cellCounts[0] - 1:
            left = self.grid.cells[(self.gridPos[0] + 1, self.gridPos[1], self.gridPos[2])]
         
        right = None
        if self.gridPos[0] > 0:
            bottom = self.grid.cells[(self.gridPos[0] - 1, self.gridPos[1], self.gridPos[2])]
            
        top  = None
        if self.gridPos[2] < self.grid.cellCounts[2] - 1:
            top = self.grid.cells[(self.gridPos[0], self.gridPos[1], self.gridPos[2] + 1)]
         
        bottom = None
        if self.gridPos[2] > 0:
            bottom = self.grid.cells[(self.gridPos[0], self.gridPos[1], self.gridPos[2] - 1)]
            
        self.neighbors = [back, front, left, right, top, bottom]
        
    def testGroundCell(self):   
        #test distance of closest point on poly to cell center,
        #if it is in range, cell becomes groundcell
        #if neighbors opposite to each other both are groundcells, cell itself
        #becomes groundcell too
        
        #insert more complex checking logic here->what if is only one neighbor there...
#        if self.neighbors[0] != None and self.neighbors[1] != None:
#        if (self.neighbors[0].isGroundCell and self.neighbors[1].isGroundCell) or \
#           (self.neighbors[2].isGroundCell and self.neighbors[3].isGroundCell) or \
#           (self.neighbors[4].isGroundCell and self.neighbors[5].isGroundCell):
#               self.isGroundCell = True
#               return
#        
        if self.grid.grounds == None:
            return
               
        for ground in self.grid.grounds:
            for edge in ground.edges:
                closest = geometry.intersect_point_line(Vector(self.center), Vector(edge[0]), Vector(edge[1]))
                vec = closest[0] + ground.pos
                if self.isInside(vec.to_tuple()):
                    print("Found Ground Cell: ", self.center, closest[0].to_tuple(), closest[1])
                    self.isGroundCell = True
                    return
                   
class Grid:
    
    def __init__(self, cellCounts, pos, dim, children, grounds):
        self.cells = {}
        self.grounds = grounds
        #must start at upper left corner of bbox, that is the "origin" of the grid
        self.pos = (pos[0] - dim[0] / 2, pos[1] - dim[1] / 2, pos[2] - dim[2] / 2)
        self.dim = dim #from objects bbox
        self.children = children
        self.cellCounts = cellCounts
    
        self.cellDim = [ dim[0] / cellCounts[0], dim[1] / cellCounts[1], 
                         dim[2] / cellCounts[2]]
                         
        print("cell/grid dimension: ", self.cellDim, self.dim)
        
        #build cells
        for x in range(0, cellCounts[0]):
            for y in range(0, cellCounts[1]):
                for z in range(0, cellCounts[2]):
                   self.cells[(x,y,z)] = Cell((x,y,z), self)
                   
    #   self.buildNeighborhood()
        self.children = None
    #    self.pos = None
    #    self.dim =  None
    
    def buildNeighborhood(self):
        [c.findNeighbors() for c in self.cells.values()]
        #delete possible refs to bpy objects
    #    for c in self.cells.values():
    #        c.cellDim = None
    #        c.gridPos = None
    #        c.grid = None
        
    def findGroundCells(self):
        [c.testGroundCell() for c in self.cells.values()]    
        
            
    def __str__(self):
        return str(self.pos) + " " + str(self.dim) + " " + str(len(self.children))

class DataStore:
    backups = {}
    grids = {}

class Ground:
    edges = []
#def register():
#   pass

#def unregister():
#   pass
    