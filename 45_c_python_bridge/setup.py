# Build script for the two COMPILED Python extensions in this module:
#   - mandelext : CPython C-API extension   (mandelext.c)
#   - mandelpy  : pybind11 / C++ extension  (mandel_pybind.cpp)
#
# Build both in place (so `import mandelext` / `import mandelpy` work from here):
#   python setup.py build_ext --inplace
# (the Makefile's `make ext` and `make pybind` targets call exactly this).
#
# The ctypes bridge (mandel.c -> libmandel.dylib) is NOT built here — it's a plain
# shared library built directly by the Makefile, because ctypes needs no Python build.

from setuptools import setup, Extension

ext_modules = [
    Extension(
        "mandelext",
        sources=["mandelext.c"],
        extra_compile_args=["-O3"],
    ),
]

# pybind11 is optional: only add the C++ extension if pybind11 is importable, so
# `make ext` still works on a machine without pybind11 installed.
try:
    import pybind11

    ext_modules.append(
        Extension(
            "mandelpy",
            sources=["mandel_pybind.cpp"],
            include_dirs=[pybind11.get_include()],
            extra_compile_args=["-O3", "-std=c++17"],
            language="c++",
        )
    )
except ImportError:
    print("[setup] pybind11 not found — skipping the C++ (mandelpy) extension. "
          "Install it with: pip install pybind11")

setup(
    name="mandel_bridges",
    version="0.1",
    description="Module 45 — C/C++ <-> Python bridges (Mandelbrot kernel)",
    ext_modules=ext_modules,
)
