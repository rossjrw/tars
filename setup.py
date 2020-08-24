from distutils.core import setup

from Cython.Build import cythonize

setup(name="tars", ext_modules=cythonize("helpers/build_chain.pyx"))
