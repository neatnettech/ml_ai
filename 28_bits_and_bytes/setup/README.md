# Track 6 setup — toolchain

One-time setup for the whole CS Foundations track. Module 28 needs only the native
toolchain; later modules add the container and emulator.

## Native (macOS, Apple Silicon) — needed for Module 28

```bash
brew bundle --file=28_bits_and_bytes/setup/Brewfile
```

Or, minimally, the Xcode Command Line Tools already give you `clang` and `make`:

```bash
xcode-select --install
```

Verify:

```bash
cd 28_bits_and_bytes
make run        # builds and runs all four demos
```

## x86-64 lab box — needed from Module 32 (CS:APP bomb/attack/cache labs)

These labs are x86-64 and assume x86-64 disassembly. On Apple Silicon, run them in a
container so the bytes match the textbook:

```bash
docker build --platform=linux/amd64 -t csfoundations 28_bits_and_bytes/setup/
docker run  --platform=linux/amd64 -it -v "$PWD":/work csfoundations
# inside: cd /work/32_assembly && make ...
```

This box also has `valgrind` (Linux-only), used for the leak-checking in Module 31.

## RISC-V + qemu — needed for Module 36 (xv6)

`qemu` is in the Brewfile. The RISC-V cross-toolchain is installed when you reach
Module 36 (the xv6 lab pins a specific version); instructions live in that module.

## Why this split

- **Native arm64** — fast, zero friction, fine for portable C (28, 30, 31, 37, 38).
- **x86-64 container** — matches CS:APP's x86-64 ABI/disassembly exactly (32–35).
- **RISC-V/qemu** — xv6's target; cross-platform either way (36).
