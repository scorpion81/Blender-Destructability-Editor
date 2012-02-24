from libcpp cimport bool
from libc.stdio cimport FILE

cdef extern from "stdio.h":
    cdef FILE* fopen(char* path, char* mode)
    cdef int fclose(FILE*)

cdef extern from "voro/src/voro++.hh" namespace "voro":
    cdef cppclass container:
        container(int xmin, int xmax, int ymin, int ymax, int zmin, int zmax,
                    int nx, int ny, int nz, bool xp, bool yp, bool zp, int p)
        void put(int i, double x, double y, double z)
        void print_custom(char *format, FILE *fp)

cdef class domain:
    cdef container *thisptr
    def __cinit__(self, int xmin, int xmax, int ymin, int ymax, int zmin, int zmax, \
    int nx, int ny, int nz, bool xp, bool yp, bool zp, int p):
        self.thisptr = new container(xmin, xmax, ymin, ymax, zmin, zmax, nx, ny,
                    nz, xp, yp, zp, p)

    def __dealloc__(self):
        del self.thisptr

    def put(self, i, x, y, z):
        self.thisptr.put(i, x, y, z)

    def print_custom(self, format, fp):
        fpc = fp.encode('UTF-8')
        r = "w+".encode('UTF-8')
        cdef char* path = fpc
        cdef char* mode = r
        cdef FILE* fil = fopen(path, mode)

        if (fil == NULL):
            print("Couldnt open file!", fp)
            return

        f = format.encode('UTF-8')
        cdef char * formatstr = f
        self.thisptr.print_custom(formatstr, fil)
        cdef int ret = fclose(fil)
      
        if (ret != 0):
            print("Closing file error!", fp)


