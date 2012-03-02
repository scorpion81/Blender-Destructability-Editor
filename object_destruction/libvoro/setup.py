from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import platform

extname = "voronoi"
if platform.architecture()[0] == "64bit":
    if platform.architecture()[1] == "ELF":
        extname = "linux64/voronoi"
    elif platform.architecture()[1] == "WindowsPE":
        extname = "win64/voronoi"
elif platform.architecture()[0] == "32bit":
    if platform.architecture()[1] == "ELF":
        extname = "linux32/voronoi"
    elif platform.architecture()[1] == "WindowsPE":
        extname = "win32/voronoi"

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension(extname, [ "voro/src/voro++.cc", "voronoi.pyx"], language="c++")]
)
