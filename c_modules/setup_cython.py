from setuptools import setup
from Cython.Build import cythonize

setup(
    name="fuzzy_cython_ext",
    ext_modules=cythonize("fuzzy_cython.pyx"),
    libraries=[("fuzzy", {"sources": ["fuzzy/fuzzy_logic.c"]})],
)
