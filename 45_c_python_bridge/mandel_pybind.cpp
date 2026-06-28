// Bridge 3 (pybind11) — the kernel in C++, bound to Python with almost no boilerplate.
//
// Compare this file to mandelext.c: the CPython C-API version is ~60 lines of manual
// ref-counting and argument parsing. pybind11 (a header-only C++ library) does all of
// that for you — you write normal C++ and one PYBIND11_MODULE block. This is how modern
// native Python packages (incl. parts of PyTorch) are built. Ties to Module 44 (C++).
//
// Built via setup.py:  python setup.py build_ext --inplace

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>   // auto-converts std::vector <-> Python list
#include <vector>

namespace py = pybind11;

// Same kernel, idiomatic C++; returns a std::vector that pybind11 turns into a list.
std::vector<int> compute(int width, int height, int max_iter) {
    std::vector<int> out(static_cast<size_t>(width) * height);
    for (int py_ = 0; py_ < height; py_++) {
        double y0 = -1.25 + 2.5 * py_ / height;
        for (int px = 0; px < width; px++) {
            double x0 = -2.5 + 3.5 * px / width;
            double x = 0.0, y = 0.0;
            int it = 0;
            while (x * x + y * y <= 4.0 && it < max_iter) {
                double x_new = x * x - y * y + x0;
                y = 2.0 * x * y + y0;
                x = x_new;
                it++;
            }
            out[static_cast<size_t>(py_) * width + px] = it;
        }
    }
    return out;
}

PYBIND11_MODULE(mandelpy, m) {
    m.doc() = "Mandelbrot kernel in C++, bound with pybind11 (Module 45).";
    m.def("compute", &compute, "Mandelbrot escape counts -> list[int]",
          py::arg("width"), py::arg("height"), py::arg("max_iter"));
}
