// Bridge 2 (CPython C-API) — a REAL Python extension module written in C.
//
// This is the literal meaning of "Python is C": CPython exposes a C API
// (<Python.h>) for defining modules, parsing arguments from Python objects, and
// building Python objects to return. After `make ext`, Python can `import mandelext`
// and call `mandelext.compute(...)` as if it were ordinary Python — but the body runs
// at C speed. No ctypes, no separate .dylib: this becomes part of the interpreter.
//
// Built via setup.py:  python setup.py build_ext --inplace

#define PY_SSIZE_T_CLEAN
#include <Python.h>

// The C kernel (same math as mandel.c / 01_pure_python.py).
static long mandel_escape(double x0, double y0, int max_iter) {
    double x = 0.0, y = 0.0;
    int it = 0;
    while (x * x + y * y <= 4.0 && it < max_iter) {
        double x_new = x * x - y * y + x0;
        y = 2.0 * x * y + y0;
        x = x_new;
        it++;
    }
    return it;
}

// Python-callable: mandelext.compute(width, height, max_iter) -> list[int]
static PyObject *mandelext_compute(PyObject *self, PyObject *args) {
    (void)self;
    int width, height, max_iter;
    // Parse three ints from the Python call; raises TypeError on mismatch.
    if (!PyArg_ParseTuple(args, "iii", &width, &height, &max_iter)) {
        return NULL;  // exception already set
    }

    PyObject *list = PyList_New((Py_ssize_t)width * height);
    if (!list) {
        return PyErr_NoMemory();
    }

    for (int py = 0; py < height; py++) {
        double y0 = -1.25 + 2.5 * py / height;
        for (int px = 0; px < width; px++) {
            double x0 = -2.5 + 3.5 * px / width;
            long it = mandel_escape(x0, y0, max_iter);
            // Build a Python int and store it; PyList_SET_ITEM steals the reference.
            PyObject *val = PyLong_FromLong(it);
            if (!val) {
                Py_DECREF(list);
                return PyErr_NoMemory();
            }
            PyList_SET_ITEM(list, (Py_ssize_t)py * width + px, val);
        }
    }
    return list;
}

// Method table: maps the Python name "compute" to our C function.
static PyMethodDef MandelMethods[] = {
    {"compute", mandelext_compute, METH_VARARGS,
     "compute(width, height, max_iter) -> list[int] of Mandelbrot escape counts"},
    {NULL, NULL, 0, NULL},  // sentinel
};

// Module definition.
static struct PyModuleDef mandelmodule = {
    PyModuleDef_HEAD_INIT,
    "mandelext",                  // module name (must match import name)
    "Mandelbrot kernel as a CPython C-API extension (Module 45).",
    -1,                            // per-interpreter state size; -1 = global
    MandelMethods,
    NULL, NULL, NULL, NULL,
};

// The ONE symbol CPython looks for when you `import mandelext`.
PyMODINIT_FUNC PyInit_mandelext(void) {
    return PyModule_Create(&mandelmodule);
}
