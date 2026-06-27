# Track 6 — CS Foundations: x86-64 Linux lab box
#
# The gold-standard CS:APP labs (bomb, attack, cache — Modules 32-35) ship as
# x86-64 binaries and assume x86-64 disassembly. On Apple Silicon, run them here so
# the assembly matches the textbook verbatim.
#
# Build (emulated x86-64 on Apple Silicon via Rosetta/QEMU):
#   docker build --platform=linux/amd64 -t csfoundations setup/
# Run, with this track mounted at /work:
#   docker run --platform=linux/amd64 -it -v "$PWD":/work csfoundations
#
# Module 28 itself does NOT need this — it's portable C and runs natively. This box
# exists so the per-module template already points at a consistent x86-64 toolchain
# for the modules that do.

FROM --platform=linux/amd64 ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc gdb \
        valgrind \
        make \
        binutils \
        vim less \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
CMD ["/bin/bash"]
