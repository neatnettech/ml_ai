# AI & Machine Learning — From Zero to Neural Networks

A hands-on, exercise-driven learning path. Each module builds on the previous one.
Work through the notebooks in order — every concept is introduced with examples,
then you practice with exercises marked with `# TODO`.

Every notebook follows the same shape: a **Purpose** statement and **Prerequisites**
up top, a **What you learned** table, a **Further reading** list (papers, docs, RFCs),
and a **Next** link at the end — so you always know why a module exists, what it
assumes, and where to go next.

## Prerequisites

- Python 3.10+
- Basic programming knowledge (variables, loops, functions)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

## Run in Zed (REPL)

Every notebook has a paired `.py` twin (same name, percent format) for [Zed's REPL](https://zed.dev/docs/repl):

1. Open the module's `.py` file in Zed (e.g. `01_python_foundations/01_numpy_basics.py`)
2. Put the cursor in a `# %%` cell, press `ctrl-shift-enter` to run it — output & plots render inline
3. The `.py` and `.ipynb` stay paired; sync edits with `jupytext --sync <file>`

> The `.ipynb` files keep saved outputs; the `.py` twins do not (output is live-only in Zed).

## Learning Path

The catalog is grouped into four categories by the *kind of skill* each module
builds. Work top to bottom — each category builds on the one before it.

### 1. Pure ML — classic machine learning, the math, and scikit-learn

Tabular data, the core ML workflow, and the algorithms you reach for first.

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 01 | [Python Foundations](01_python_foundations/) | NumPy, Pandas, Matplotlib — the ML toolkit |
| 02 | [Math Foundations](02_math_foundations/) | Linear algebra & statistics you actually need |
| 03 | [First ML Models](03_first_ml_models/) | Linear & logistic regression from scratch and with scikit-learn |
| 04 | [Classification & Trees](04_classification_and_trees/) | Decision trees, model evaluation, confusion matrices |
| 05 | [Unsupervised Learning](05_unsupervised_learning/) | K-Means clustering, PCA, dimensionality reduction |
| 06 | [Ensemble Methods](06_ensemble_methods/) | Random Forest, Gradient Boosting, XGBoost |

### 2. AI & Deep Learning — neural nets and generative vision

Neural networks with PyTorch, then a deep-dive that builds, step by step, toward a
**working hairstyle swap** (take person A's face, give them person B's hair). Each
generative module first builds the idea *from scratch*, then uses pretrained SOTA models.

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 07 | [Neural Networks](07_neural_networks/) | Build your first neural net with PyTorch |
| 08 | [CNNs & Images](08_cnns_image_classification/) | Convolutional neural networks, image classification |
| 09 | [NLP & Text](09_nlp_text_processing/) | Text processing, embeddings, intro to transformers |
| 11 | [Segmentation & Face Parsing](11_segmentation_face_parsing/) | U-Net from scratch, pixel-wise labels, hair masks |
| 12 | [Autoencoders & VAEs](12_autoencoders_vae/) | Latent spaces, the reparameterization trick, interpolation |
| 13 | [GANs from Scratch](13_gans/) | DCGAN, adversarial training, the road to StyleGAN |
| 14 | [StyleGAN & GAN Inversion](14_stylegan_inversion/) | Local lab: latent directions, W-space, toy inversion; then StyleGAN2 style mixing & real-photo inversion *(GPU part)* |
| 15 | [Diffusion Models](15_diffusion/) | DDPM from scratch (2D + MNIST), classifier-free guidance, DDIM; Stable Diffusion inpainting *(GPU part)* |

> **Hardware:** Modules 11–13 and the local labs in 14–16 run on a Mac (CPU/MPS) —
> every module gives you hands-on practice without a GPU. The heavy models (StyleGAN2,
> Stable Diffusion) need a GPU — run those sections on **Google Colab** (Runtime → GPU).
> Every notebook is guarded so it runs top-to-bottom either way; GPU-only cells skip
> with notes when no GPU is present.

### 3. Practical End-to-End — ship something complete

Tie it all together. Two ML capstones, then a backend track that takes you from
"train a model in a notebook" to "ship that model behind an authenticated REST API."

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 10 | [ML Capstone](10_capstone_project/) | End-to-end ML project pulling the Pure ML track together |
| 16 | [Capstone — Hairstyle Swap](16_capstone_hairstyle_swap/) | Align → mask → generate → blend, end to end — naive route + quality metrics run locally; StyleGAN/diffusion routes on Colab |
| 17 | [FastAPI + SQLAlchemy CRUD](17_fastapi_crud/) | REST APIs, Pydantic schemas, SQLAlchemy 2.0 ORM, migrations |
| 18 | [Cryptography Deep-Dive](18_cryptography/) | Hashing vs encryption, HMAC, symmetric/asymmetric, JWT signatures |
| 19 | [Auth: JWT + Password Security](19_auth_jwt/) | Password hashing, OAuth2 flow, JWT, protected routes |
| 20 | [Capstone — Serve an ML Model](20_capstone_model_api/) | Wrap the Module 10 model in an authenticated FastAPI service |

> **Backend track (17–20)** runs anywhere — pure CPU, no GPU needed. Each module pairs
> a teaching notebook (run it like any other) with a runnable `app/` project you launch
> with `uvicorn`. See each module's `app/README.md` for run commands and example calls.

### 4. Offensive & Defensive Security (White-Hat)

White-hat hacking from the network up. Each module follows one loop — **attack →
understand → defend**: you exploit a real flaw, learn its root cause, then build the
fix. The web modules attack a bundled, intentionally-vulnerable lab app
([`vulnlab`](23_web_app_security/vulnlab/)) you run on localhost. As everywhere in the
catalog, each module lists its **purpose**, hands-on **exercises**, and a **Further
reading** section — here linking the canonical security references (OWASP, RFCs,
PortSwigger, NIST).

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 21 | [Networking & Packets](21_networking_and_packets/) | TCP/IP, sockets, build a port scanner, scapy, nmap concepts |
| 22 | [Recon & Scanning](22_recon_and_scanning/) | Passive/active recon, banner grabbing, service/version fingerprinting, DNS enum |
| 23 | [Web App Security](23_web_app_security/) | OWASP Top 10 on `vulnlab` — SQLi, XSS, IDOR, SSRF, command injection |
| 24 | [Auth Attacks & Defense](24_auth_attacks_and_defense/) | Brute force, credential stuffing, hash cracking → bcrypt, rate limit, lockout, TOTP MFA |
| 25 | [Traffic & Crypto Attacks](25_traffic_and_crypto_attacks/) | Sniffing, HTTP vs TLS, ECB leakage, weak hashes, timing attacks |
| 26 | [Capstone — Pentest](26_capstone_pentest/) | Full engagement: recon → exploit chain → CVSS report → remediation → re-test |
| 46 | [Pentest Tooling](46_pentest_tooling/) | Drive the real tools — Nmap, Nikto, SQLmap, John, Hashcat (+ Metasploit/Maltego/Recon-ng) — against `vulnlab`, mapped to the by-hand attacks of 22–24 |

> ⚖️ **Ethics & the law — read [Module 21](21_networking_and_packets/) first.** This
> track teaches *authorized, defensive* security. Only test systems you own or have
> **written permission** to test (unauthorized access violates the CFAA and equivalents).
> Every lab here targets `127.0.0.1` or the bundled `vulnlab` — **never** a third party.
> Practice further on legal ranges: TryHackMe, Hack The Box, PortSwigger Web Security
> Academy, OverTheWire.
>
> **Runs anywhere — pure CPU, no GPU.** A few raw-socket cells (scapy sniffing) need
> `sudo`; they're guarded with a no-privilege fallback so notebooks always run clean.

### 5. Agents & Tooling — give an LLM hands

You've shipped models behind APIs for *people*. Now expose capabilities to a *model*
via the **Model Context Protocol (MCP)** — the open standard that lets Claude discover
and call your tools, read your data, and reuse your prompts.

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 27 | [Model Context Protocol](27_mcp/) | Build an MCP server (tools/resources/prompts) + client over stdio, then register it with Claude |

> **Runs anywhere — pure CPU, stdio transport, no GPU and no network.** Reuses the
> FastAPI/Pydantic mental model from Module 17; pairs a teaching notebook with a runnable
> `app/` (server + client) you wire into Claude per `app/README.md`.

### 6. CS Foundations — from bits to systems (the bytes-up track)

Everything above stands on Python and high-level libraries. This track goes the other
way: **down to the metal and back up**, MIT-EECS style — single bits → logic gates → a
CPU → C and pointers → assembly → caches → the operating system → algorithms →
compilers → distributed systems → security. It can be taken **first** (it's
foundational) despite the high numbers. See [the track plan](cs-foundations-track.md)
for the full curriculum and source mapping (CS:APP, Nand2Tetris, MIT 6.191/6.1210/
6.1800/6.1810, xv6).

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 28 | [Bits, Bytes & Number Representation](28_bits_and_bytes/) | Binary/hex, two's complement, IEEE-754, bitwise tricks |
| 29 | [Digital Logic & the CPU](29_digital_logic/) | NAND → gates → mux → adders → an 8-bit ALU |
| 30 | [C Programming I](30_c_programming_i/) | Pointers & memory, stack vs heap, strings, structs, a dynamic array |
| 31 | [C Programming II](31_c_programming_ii/) | Multi-file builds, function pointers, the preprocessor, UB, gdb/valgrind |
| 32 | [Assembly & the ISA](32_assembly/) | Reading compiler output, registers, calling conventions (x86-64 + native AArch64) |
| 33 | [Computer Architecture](33_architecture/) | Cache locality, branch prediction, the memory hierarchy — measured |
| 34 | [Linking, Loading & Processes](34_linking_loading/) | Compile→link→load, static/dynamic libraries, symbols |
| 35 | [Virtual Memory & Allocation](35_virtual_memory/) | Address space, mmap, write your own malloc |
| 36 | [Operating Systems with xv6](36_xv6_os/) | fork/exec/pipes/a tiny shell; the xv6 kernel labs (qemu/RISC-V) |
| 37 | [Concurrency](37_concurrency/) | Threads, races, mutexes, condition vars, atomics, deadlock |
| 38 | [Algorithms & Data Structures](38_algorithms/) | Sorting, hashing, trees/heaps, graphs, dynamic programming |
| 39 | [Advanced Algorithms](39_advanced_algorithms/) | Greedy, divide & conquer, Dijkstra, MST, max-flow, NP-hardness |
| 40 | [Compilers & Language Engineering](40_compilers/) | Lexer → parser → evaluator → bytecode VM for a small language |
| 41 | [Networking Deep-Dive](41_networking/) | Sockets, TCP/UDP, a request/response protocol, a concurrent server |
| 42 | [Distributed Systems](42_distributed/) | RPC, logical clocks, replication/quorums, a Raft-lite consensus sim |
| 43 | [Security & Cryptography Foundations](43_security/) | Memory-safety bugs (explain-and-fix), constant-time compare, crypto primitives |
| 44 | [C++ for Systems](44_cpp_for_systems/) *(optional)* | RAII, smart pointers, templates, the STL |
| 45 | [C/C++ ↔ Python (FFI & Extensions)](45_c_python_bridge/) | Call C/C++ from Python (ctypes, C-API, pybind11) vs NumPy — the bridge back to the ML tracks |

> **Format differs from the rest of the catalog:** this track is real C/C++ + a
> `Makefile` per module (not jupyter). Build with `make`, run a demo with `make run1`,
> attempt `exercises/`, check against `solutions/`. The native parts run on Apple
> Silicon; the x86-64 (CS:APP bomb/attack) and RISC-V (xv6) labs use the toolchain in
> [`28_bits_and_bytes/setup/`](28_bits_and_bytes/setup/) (Docker + qemu).

## How to Use

1. Open the notebook for each module in Jupyter
2. Read through the explanations and run the example cells
3. Complete the `# TODO` exercises — solutions are in separate cells you can reveal
4. Move to the next module when you're comfortable

## Tips

- **Don't skip the exercises** — reading is not learning, doing is
- **Experiment** — change parameters, break things, see what happens
- **Re-run from scratch** — use "Restart & Run All" to make sure your code works end-to-end
