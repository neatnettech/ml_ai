# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 14.1 — StyleGAN & GAN Inversion
#
# > ⚠️ **This module needs a GPU.** StyleGAN2 inference is slow-to-impractical on CPU/MPS.
# > Run it on **Google Colab** (Runtime → Change runtime type → **GPU**) or any CUDA machine.
# > The code is written to run top-to-bottom on a Colab GPU. On your Mac, read it as a
# > walkthrough — the cells are guarded so they won't crash, they'll just skip.
#
# This is where hairstyle editing gets real. In Module 13 we saw *why* StyleGAN's layered
# design enables attribute control. Now we:
#
# 1. Load a **pretrained StyleGAN2** trained on **FFHQ** (70k high-quality faces).
# 2. Use **style mixing** to see coarse/mid/fine layers control pose/structure/color.
# 3. **Invert** a real photo — find the latent `w+` that reproduces it (so we can edit *real*
#    people, not just generated ones).
# 4. Attempt a first **hairstyle blend** by mixing the hair-controlling layers of two faces.
#
# This is "Route A" of the capstone (Module 16): edit hair entirely in StyleGAN's latent space.

# %% [markdown]
# ## 0. Setup (Colab)
#
# We use NVIDIA's official **stylegan2-ada-pytorch** repo (it ships the network code and a
# loader for pretrained FFHQ weights). Run these once per Colab session.
#
# ```python
# # --- run in a Colab cell ---
# !git clone https://github.com/NVlabs/stylegan2-ada-pytorch.git
# !pip install ninja                     # for the custom CUDA ops
# import sys; sys.path.append('stylegan2-ada-pytorch')
# ```
#
# Pretrained FFHQ weights (config-f, 1024x1024) are distributed by NVIDIA as a `.pkl`:
# `https://nvlabs-fi-cdn.nvidia.com/stylegan2-ada-pytorch/pretrained/ffhq.pkl`

# %%
import os
import numpy as np
import matplotlib.pyplot as plt

try:
    import torch
    import torch.nn.functional as F
    HAVE_TORCH = True
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
except Exception:
    HAVE_TORCH = False
    device = None

ON_GPU = HAVE_TORCH and torch.cuda.is_available()
print(f"torch available: {HAVE_TORCH} | device: {device} | StyleGAN-ready (CUDA): {ON_GPU}")
if not ON_GPU:
    print("\nNo CUDA GPU detected. The StyleGAN cells below will SKIP and print notes.")
    print("Open this notebook in Colab with a GPU runtime to run them live.")

# %% [markdown]
# ## 1. Load the Pretrained Generator
#
# StyleGAN2's generator exposes two entry points we care about:
# - `G.mapping(z, c)` -> `w`  (the disentangled latent, broadcast to all layers as `w+`)
# - `G.synthesis(w)` -> image  (the actual image generator)
#
# Splitting them lets us manipulate `w` directly — which is the whole point.

# %%
G = None
if ON_GPU:
    import pickle
    import urllib.request

    URL = ("https://nvlabs-fi-cdn.nvidia.com/stylegan2-ada-pytorch/"
           "pretrained/ffhq.pkl")
    if not os.path.exists("ffhq.pkl"):
        print("Downloading FFHQ weights (~350 MB)...")
        urllib.request.urlretrieve(URL, "ffhq.pkl")

    with open("ffhq.pkl", "rb") as f:
        G = pickle.load(f)["G_ema"].to(device).eval()
    print(f"Loaded StyleGAN2-FFHQ.")
    print(f"  z dim:       {G.z_dim}")
    print(f"  w dim:       {G.w_dim}")
    print(f"  num layers:  {G.num_ws}  (this is the depth of w+)")
    print(f"  resolution:  {G.img_resolution}x{G.img_resolution}")
else:
    print("[skipped] StyleGAN2 load — needs a CUDA GPU.")


def to_image(tensor):
    """StyleGAN output (B,3,H,W) in ~[-1,1] -> uint8 HWC numpy for plotting."""
    img = (tensor.clamp(-1, 1) + 1) * 127.5
    return img.permute(0, 2, 3, 1).to(torch.uint8).cpu().numpy()

# %% [markdown]
# ## 2. Sample Faces
#
# Map random `z` -> `w`, synthesize, and look. Each face is fully synthetic — none of these
# people exist.

# %%
if ON_GPU and G is not None:
    z = torch.randn(8, G.z_dim, device=device)
    w = G.mapping(z, None)                 # (8, num_ws, w_dim)  <- this is w+
    with torch.no_grad():
        imgs = G.synthesis(w, noise_mode="const")
    pics = to_image(imgs)

    fig, axes = plt.subplots(1, 8, figsize=(16, 3))
    for i in range(8):
        axes[i].imshow(pics[i]); axes[i].axis('off')
    plt.suptitle('StyleGAN2-FFHQ: 8 synthetic faces', fontsize=13)
    plt.tight_layout(); plt.show()
else:
    print("[skipped] face sampling — GPU only.")

# %% [markdown]
# ## 3. Style Mixing — proving layers control different scales
#
# `w+` has one `w` vector **per layer** (`num_ws ≈ 18` for 1024px). We build a "crossover":
# take the first `k` layers from face A's `w+` and the rest from face B's `w+`, synthesize,
# and see what transfers.
#
# - **Small `k` (mix at coarse layers):** A's pose/face-shape with B's everything-else.
# - **Large `k` (mix at fine layers):** mostly A, with B's color/texture grafted on.
#
# **Hair lives across the coarse-to-mid layers (shape) and fine layers (color).** Finding
# *which* layers move hair is exactly how we target a swap.

# %%
if ON_GPU and G is not None:
    z_a = torch.randn(1, G.z_dim, device=device)
    z_b = torch.randn(1, G.z_dim, device=device)
    w_a = G.mapping(z_a, None)   # (1, num_ws, w_dim)
    w_b = G.mapping(z_b, None)
    num_ws = G.num_ws

    def synth(w):
        with torch.no_grad():
            return to_image(G.synthesis(w, noise_mode="const"))[0]

    crossovers = [0, 4, 8, 12, num_ws]  # how many leading layers come from A
    fig, axes = plt.subplots(1, len(crossovers) + 2, figsize=(18, 3))
    axes[0].imshow(synth(w_a)); axes[0].set_title('Face A'); axes[0].axis('off')
    for idx, k in enumerate(crossovers):
        w_mix = w_b.clone()
        w_mix[:, :k] = w_a[:, :k]   # first k layers from A, rest from B
        axes[idx + 1].imshow(synth(w_mix))
        axes[idx + 1].set_title(f'A[:{k}] + B[{k}:]', fontsize=9)
        axes[idx + 1].axis('off')
    axes[-1].imshow(synth(w_b)); axes[-1].set_title('Face B'); axes[-1].axis('off')
    plt.suptitle('Style mixing: leading layers from A, trailing from B', fontsize=13)
    plt.tight_layout(); plt.show()
else:
    print("[skipped] style mixing — GPU only.")
    print("Concept: w+ holds one w per layer; swapping a layer range swaps a visual scale.")

# %% [markdown]
# ## 4. GAN Inversion — editing a *real* photo
#
# Style mixing edits generated faces. To edit a **real** person we must first find the
# latent that reproduces their photo. That's **GAN inversion**: solve for `w+` such that
# `G.synthesis(w+) ≈ target_photo`.
#
# Two families:
# - **Optimization-based** (shown below): start from the mean `w`, gradient-descend `w+` to
#   minimize a perceptual + pixel loss against the target. Slow (~1–2 min/image) but no extra
#   model. This is the most instructive, so we implement it.
# - **Encoder-based** (e4e, pSp, ReStyle): a network trained to predict `w+` in one forward
#   pass. Fast, better for editing; you'd load a pretrained encoder.
#
# **Aligning the face first matters.** FFHQ faces are centered/cropped a specific way.
# Real photos must be aligned the same (eyes on a fixed line) or inversion struggles — we
# handle alignment in the Module 16 capstone.

# %%
def invert_image(G, target, steps=300, lr=0.05, device="cuda"):
    """Optimization-based inversion. target: (1,3,H,W) in [-1,1] at G's resolution.

    Returns the optimized w+ latent. Uses VGG perceptual loss if torchvision is present,
    else falls back to L2. (Educational version — encoder inversion is faster in practice.)
    """
    # Initialize from the mean latent (w averaged over many z) — a good starting point
    with torch.no_grad():
        z_samples = torch.randn(10000, G.z_dim, device=device)
        w_avg = G.mapping(z_samples, None).mean(0, keepdim=True)  # (1, num_ws, w_dim)
    w_opt = w_avg.clone().requires_grad_(True)
    optimizer = torch.optim.Adam([w_opt], lr=lr)

    # Optional perceptual loss via a pretrained VGG
    try:
        import torchvision
        vgg = torchvision.models.vgg16(weights="IMAGENET1K_V1").features[:16].eval().to(device)
        for p in vgg.parameters():
            p.requires_grad_(False)

        def perceptual(a, b):
            a = F.interpolate((a + 1) / 2, size=224, mode="area")
            b = F.interpolate((b + 1) / 2, size=224, mode="area")
            return F.mse_loss(vgg(a), vgg(b))
    except Exception:
        perceptual = None

    for step in range(steps):
        synth = G.synthesis(w_opt, noise_mode="const")
        loss = F.mse_loss(synth, target)
        if perceptual is not None:
            loss = loss + perceptual(synth, target)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        if step % 50 == 0:
            print(f"  step {step:4d}  loss {loss.item():.4f}")
    return w_opt.detach()


if ON_GPU and G is not None:
    # For a self-contained demo we "invert" a StyleGAN-generated face (we know it's invertible).
    # For a real photo: load it, align it, resize to G.img_resolution, scale to [-1, 1].
    with torch.no_grad():
        target_w = G.mapping(torch.randn(1, G.z_dim, device=device), None)
        target = G.synthesis(target_w, noise_mode="const")

    print("Inverting target face...")
    w_found = invert_image(G, target, steps=200, lr=0.05, device=device)

    with torch.no_grad():
        recon = G.synthesis(w_found, noise_mode="const")
    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    axes[0].imshow(to_image(target)[0]); axes[0].set_title('Target'); axes[0].axis('off')
    axes[1].imshow(to_image(recon)[0]); axes[1].set_title('Inverted (reconstructed)'); axes[1].axis('off')
    plt.tight_layout(); plt.show()
else:
    print("[skipped] inversion — GPU only.")

# %% [markdown]
# ## 5. A First Hairstyle Blend ("Barbershop-lite")
#
# Now the payoff. Given two inverted faces — **source** (whose identity we keep) and
# **target** (whose hair we want) — we copy the target's hair-controlling layers into the
# source's `w+`.
#
# Which layers? Empirically, in FFHQ StyleGAN2 the **coarse-to-mid layers (~4–10)** carry
# hair *shape*, and **finer layers** carry hair *color*. We expose the range as a parameter
# so you can sweep it. This is crude — it also drags some face structure along, and there's
# no masking yet — but it's a real latent-space edit and a baseline the capstone improves on.

# %%
def hair_blend(w_source, w_target, hair_layers=range(4, 10)):
    """Copy hair-controlling layers from target into source's w+."""
    w = w_source.clone()
    for layer in hair_layers:
        w[:, layer] = w_target[:, layer]
    return w


if ON_GPU and G is not None:
    w_source = G.mapping(torch.randn(1, G.z_dim, device=device), None)
    w_target = G.mapping(torch.randn(1, G.z_dim, device=device), None)
    w_swapped = hair_blend(w_source, w_target, hair_layers=range(4, 10))

    with torch.no_grad():
        src = to_image(G.synthesis(w_source, noise_mode="const"))[0]
        tgt = to_image(G.synthesis(w_target, noise_mode="const"))[0]
        out = to_image(G.synthesis(w_swapped, noise_mode="const"))[0]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(src); axes[0].set_title('Source (keep identity)'); axes[0].axis('off')
    axes[1].imshow(tgt); axes[1].set_title('Target (want this hair)'); axes[1].axis('off')
    axes[2].imshow(out); axes[2].set_title('Blend (source + target hair layers)'); axes[2].axis('off')
    plt.suptitle('Latent-space hairstyle blend — crude first attempt', fontsize=13)
    plt.tight_layout(); plt.show()
    print("Notice the leakage: copying whole layers also shifts some face structure.")
    print("The capstone (Module 16) adds a hair MASK so only hair pixels change.")
else:
    print("[skipped] hair blend — GPU only.")
    print("Mechanism: w_swapped[:, hair_layers] = w_target[:, hair_layers].")

# %% [markdown]
# ## 6. Exercises
#
# > These run on the same Colab GPU session as above. On a Mac they'll skip.
#
# ### Exercise 6.1 — Find the hair layers
#
# Sweep the `hair_layers` range. For a fixed source and target, render the blend for
# several ranges: `range(0,4)`, `range(4,8)`, `range(8,12)`, `range(12, num_ws)`. Which
# range changes hair the most while disturbing identity the least? Make a labeled grid.

# %%
# TODO: render hair_blend for several layer ranges and compare
# Hint: reuse hair_blend(w_source, w_target, hair_layers=...) in a loop.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: layer sweep
if ON_GPU and G is not None:
    ranges = [range(0, 4), range(4, 8), range(8, 12), range(12, G.num_ws)]
    labels = ['layers 0-3 (pose)', 'layers 4-7 (shape/hair)',
              'layers 8-11 (hair/features)', 'layers 12+ (color/texture)']
    fig, axes = plt.subplots(1, len(ranges) + 1, figsize=(16, 3))
    with torch.no_grad():
        axes[0].imshow(to_image(G.synthesis(w_source, noise_mode="const"))[0])
        axes[0].set_title('Source'); axes[0].axis('off')
        for i, (rng, lab) in enumerate(zip(ranges, labels)):
            w = hair_blend(w_source, w_target, hair_layers=rng)
            axes[i + 1].imshow(to_image(G.synthesis(w, noise_mode="const"))[0])
            axes[i + 1].set_title(lab, fontsize=8); axes[i + 1].axis('off')
    plt.suptitle('Which layers move the hair?', fontsize=13)
    plt.tight_layout(); plt.show()
    print("Typically the 4-11 band moves hairstyle most; 12+ shifts color.")
else:
    print("[skipped] — GPU only.")

# %% [markdown]
# ### Exercise 6.2 — Invert a real photo of yourself
#
# Load a real portrait (your own, or a public-domain one), align/crop it to a centered
# face, resize to `G.img_resolution`, scale to `[-1, 1]`, and run `invert_image`. Show
# target vs reconstruction. Then apply a hair blend with a generated target.
#
# Tip: face alignment matters a lot. You can borrow the FFHQ alignment helper
# (`face_alignment` / dlib 68-landmarks) — we set that up properly in Module 16.

# %%
# TODO: load + align a real photo, invert it, show reconstruction, then blend hair
# Hint: target = (TF.to_tensor(aligned_pil).to(device) * 2 - 1).unsqueeze(0)
#       then w = invert_image(G, target, steps=400)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION (template — fill in your image path on Colab):
#
# from PIL import Image
# import torchvision.transforms.functional as TF
# if ON_GPU and G is not None:
#     pil = Image.open("my_aligned_face.png").convert("RGB").resize(
#         (G.img_resolution, G.img_resolution))
#     target = (TF.to_tensor(pil).to(device) * 2 - 1).unsqueeze(0)
#     w_real = invert_image(G, target, steps=400, lr=0.05, device=device)
#     recon = G.synthesis(w_real, noise_mode="const")
#     # ... show target vs recon, then hair_blend(w_real, w_generated_target)
print("Run on Colab with a real, FFHQ-aligned face. See Module 16 for the aligner.")

# %% [markdown]
# ## Key Takeaways
#
# - **StyleGAN2** separates `G.mapping` (`z`->`w+`) from `G.synthesis` (`w+`->image), so we
#   can manipulate the latent directly. `w+` has **one `w` per layer**.
#
# - **Style mixing** proves layers control scales: coarse = pose/shape, mid = features/hair
#   structure, fine = color/texture. Swapping a layer range swaps that visual scale.
#
# - **GAN inversion** finds the `w+` that reproduces a *real* photo — the prerequisite for
#   editing real people. Optimization-based is instructive; encoder-based (e4e/pSp) is fast.
#
# - A **hairstyle blend** = copy the target's hair-controlling layers into the source's `w+`.
#   Crude alone (it leaks identity); the capstone adds a **hair mask** to localize the change.
#
# - **Alignment is essential** — real photos must match FFHQ's crop convention.
#
# ---
# **Next:** [Diffusion Models →](../15_diffusion/01_diffusion.ipynb) — the other (and now
# dominant) generative paradigm, plus mask-targeted **inpainting** for "Route B" of the swap.
