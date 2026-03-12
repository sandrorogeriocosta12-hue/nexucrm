"""
setup.py - Build script para os módulos C/Cython do Nexus Service

Compila:
1. weight_adjustment.c + weight_adjustment.pyx (novo!)
2. fuzzy_logic.c + fuzzy_cython.pyx (existente)

Uso:
    python setup.py build_ext --inplace
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import sys
import os

# Detecta se está em 64 bits
is_64bit = sys.maxsize > 2**32

ext_modules = [
    # Novo módulo: Weight Adjustment (Neural Learning)
    Extension(
        "c_modules.weight_adjustment",
        sources=["c_modules/weight_adjustment.pyx", "c_modules/weight_adjustment.c"],
        extra_compile_args=[
            "-O3",  # Otimização agressiva
            "-march=native",  # Usa instruções de CPU
            "-ffast-math",  # Operações de ponto flutuante rápidas
        ],
        language="c",
    ),
    # Módulo existente: Fuzzy Logic (Cython)
    Extension(
        "c_modules.fuzzy_cython",
        sources=["c_modules/fuzzy_cython.pyx", "c_modules/fuzzy_logic.c"],
        extra_compile_args=[
            "-O3",
            "-march=native",
            "-ffast-math",
        ],
        language="c",
    ),
]

setup(
    name="nexus-c-modules",
    version="1.0.0",
    description="Módulos C de alto desempenho para Nexus Service",
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "language_level": "3",
            "profile": False,
        },
    ),
    include_dirs=[
        np.get_include(),
        "c_modules/",
    ],
    zip_safe=False,
)
