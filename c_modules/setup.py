from setuptools import setup, Extension
from Cython.Build import cythonize

ext_modules = [
    Extension(
        "c_modules.fuzzy_cython",
        ["fuzzy_cython.pyx", "fuzzy_logic.c"],
        extra_compile_args=["-O3"],
    )
]

setup(
    name="vexus_c_modules",
    version="0.1.0",
    description="Extensões C para Vexus Service",
    ext_modules=cythonize(ext_modules),
    zip_safe=False,
)
