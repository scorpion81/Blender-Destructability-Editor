from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import platform
import shutil

extname = "voronoi"

if platform.architecture()[0] == "64bit":
    if platform.architecture()[1] == "ELF":
        extname = "linux64/voronoi"
elif platform.architecture()[0] == "32bit":
    if platform.architecture()[1] == "ELF":
        extname = "linux32/voronoi"

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension(extname, [ "voro/src/voro++.cc", "voronoi.pyx"], language="c++")]
)

if platform.architecture()[0] == "64bit":
    if platform.architecture()[1] == "WindowsPE":
        dest = "win64/"+extname+".pyd"
        src = extname+".pyd"
    else:
        dest = "osx64/"+extname+".so"
        src = extname+".so"
elif platform.architecture()[0] == "32bit":
    if platform.architecture()[1] == "WindowsPE":
        dest = "win32/" + extname + ".pyd"
        src = extname + ".pyd"
    else:
        dest = "osx32/"+extname+".so"
        src = extname+".so"

if platform.architecture()[1] != 'ELF':
    shutil.copyfile(src, dest)
