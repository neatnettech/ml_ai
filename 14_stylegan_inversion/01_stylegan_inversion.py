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
# **Purpose:** To edit a *real* photo with a GAN you must first find the latent code that
# reproduces it — that's **GAN inversion**, and together with StyleGAN's per-layer styles it
# is "Route A" of the **hairstyle-swap capstone** (Module 16). This module builds every idea
# locally on a tiny GAN first (directions, W-space, inversion-by-gradient-descent), then
# scales them up on a pretrained StyleGAN2 in Colab.
#
# **Prerequisites:** Module 13 (DCGAN, adversarial training, latent spaces).
#
# > ⚠️ **Hardware:** Sections **1–4 run locally** on your Mac (CPU/MPS) — they use a tiny
# > DCGAN and 2D toys. Sections **5–9 need a CUDA GPU**: StyleGAN2 inference is
# > slow-to-impractical on CPU/MPS, so run those on **Google Colab** (Runtime → Change
# > runtime type → **GPU**). The GPU cells are guarded — on a Mac they skip with a note.
#
# **What you'll learn:**
# - **Latent directions**: a direction in z-space = an attribute edit (the core mechanic)
# - **Z vs W**: why StyleGAN adds a mapping network, on a 2D toy you can fully see
# - **GAN inversion** as plain gradient descent on the latent — first tiny, then FFHQ-scale
# - **Style mixing**: coarse/mid/fine layers control pose/structure/color
# - A first **hairstyle blend** by grafting hair-controlling layers between two faces

# %%
import os
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

import torchvision
import torchvision.transforms as transforms
import torchvision.utils as vutils

# %matplotlib inline

torch.manual_seed(42)
np.random.seed(42)

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

ON_GPU = torch.cuda.is_available()   # StyleGAN2's custom ops need CUDA specifically
print(f"PyTorch {torch.__version__} | device: {device} | StyleGAN-ready (CUDA): {ON_GPU}")
if not ON_GPU:
    print("\nNo CUDA GPU: sections 1-4 (local lab) run fine here; sections 5-9 will skip.")

# %% [markdown]
# ---
# # Part A — Local Lab (runs on your Mac)
#
# Everything StyleGAN does at FFHQ scale has a small-scale analogue you can run in seconds
# to minutes locally. We rebuild Module 13's DCGAN as our sandbox, then practice the three
# core mechanics: **steering** the latent, **understanding W-space**, and **inverting**.
#
# ## 1. Warm-up: rebuild the Module 13 DCGAN
#
# Same architecture as Module 13 (Fashion-MNIST, 32x32, `LATENT_DIM=100`) — we re-train it
# here so this notebook is self-contained. Module 13 didn't save its weights, so the first
# run trains ~3 epochs (≈2–4 min on MPS) and **caches the generator** to
# `./data/dcgan_fmnist_G.pt`; later runs load instantly.

# %%
IMG_SIZE = 32
IMG_CHANNELS = 1
LATENT_DIM = 100


class Generator(nn.Module):
    def __init__(self, latent_dim=LATENT_DIM, channels=IMG_CHANNELS, feat=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.ConvTranspose2d(latent_dim, feat * 4, 4, 1, 0, bias=False),
            nn.BatchNorm2d(feat * 4), nn.ReLU(True),
            nn.ConvTranspose2d(feat * 4, feat * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat * 2), nn.ReLU(True),
            nn.ConvTranspose2d(feat * 2, feat, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat), nn.ReLU(True),
            nn.ConvTranspose2d(feat, channels, 4, 2, 1, bias=False),
            nn.Tanh(),
        )

    def forward(self, z):
        return self.net(z)


class Discriminator(nn.Module):
    def __init__(self, channels=IMG_CHANNELS, feat=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(channels, feat, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(feat, feat * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat * 2), nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(feat * 2, feat * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat * 4), nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(feat * 4, 1, 4, 1, 0, bias=False),
        )

    def forward(self, x):
        return self.net(x).view(-1)


def weights_init(m):
    if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d)):
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif isinstance(m, nn.BatchNorm2d):
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


# %%
G_PATH = "./data/dcgan_fmnist_G.pt"
os.makedirs("./data", exist_ok=True)

G_local = Generator().to(device)

if os.path.exists(G_PATH):
    G_local.load_state_dict(torch.load(G_PATH, map_location=device))
    print(f"Loaded cached generator from {G_PATH}")
else:
    print("No cached generator — training a quick DCGAN (~3 epochs)...")
    transform = transforms.Compose([
        transforms.Resize(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,)),
    ])
    dataset = torchvision.datasets.FashionMNIST(
        root='./data', train=True, download=True, transform=transform)
    loader = DataLoader(dataset, batch_size=128, shuffle=True, drop_last=True)

    D_local = Discriminator().to(device)
    G_local.apply(weights_init); D_local.apply(weights_init)
    criterion = nn.BCEWithLogitsLoss()
    opt_G = optim.Adam(G_local.parameters(), lr=2e-4, betas=(0.5, 0.999))
    opt_D = optim.Adam(D_local.parameters(), lr=2e-4, betas=(0.5, 0.999))
    REAL_LABEL, FAKE_LABEL = 0.9, 0.0

    for epoch in range(3):
        ld, lg, n = 0.0, 0.0, 0
        for real, _ in loader:
            real = real.to(device)
            b = real.size(0)
            opt_D.zero_grad()
            loss_real = criterion(D_local(real),
                                  torch.full((b,), REAL_LABEL, device=device))
            noise = torch.randn(b, LATENT_DIM, 1, 1, device=device)
            fake = G_local(noise)
            loss_fake = criterion(D_local(fake.detach()),
                                  torch.full((b,), FAKE_LABEL, device=device))
            (loss_real + loss_fake).backward(); opt_D.step()
            opt_G.zero_grad()
            loss_G = criterion(D_local(fake),
                               torch.full((b,), REAL_LABEL, device=device))
            loss_G.backward(); opt_G.step()
            ld += (loss_real + loss_fake).item(); lg += loss_G.item(); n += 1
        print(f"  epoch {epoch+1}/3  loss_D: {ld/n:.3f}  loss_G: {lg/n:.3f}")

    torch.save(G_local.state_dict(), G_PATH)
    print(f"Saved generator to {G_PATH}")

G_local.eval()
with torch.no_grad():
    sample = G_local(torch.randn(16, LATENT_DIM, 1, 1, device=device)).cpu()
grid = vutils.make_grid(sample, nrow=8, normalize=True, padding=1)
plt.figure(figsize=(10, 3))
plt.imshow(grid.permute(1, 2, 0).squeeze(), cmap='gray')
plt.title('Our local sandbox generator: 16 samples'); plt.axis('off')
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 2. Latent directions & arithmetic
#
# Module 13's exercise *interpolated* between two z's. Here we **steer** one z: a
# *direction* in latent space corresponds to an *attribute edit*. This is the core mechanic
# behind every "make the hair longer / face older" slider you've seen.
#
# The simplest way to find a direction (no labels needed): pick a measurable attribute,
# generate a lot of samples, and subtract the mean latent of the "low" group from the mean
# latent of the "high" group. We use **brightness** — trivially measurable — but with
# StyleGAN the same recipe with a hair-length classifier gives you a *hair-length* direction.

# %%
N = 2000
z_bank = torch.randn(N, LATENT_DIM, 1, 1, device=device)
brightness = torch.empty(N)
with torch.no_grad():
    for i in range(0, N, 250):
        imgs = G_local(z_bank[i:i + 250])
        brightness[i:i + 250] = imgs.mean(dim=(1, 2, 3)).cpu()

k = N // 10
order = brightness.argsort()
direction = (z_bank[order[-k:]].mean(0) - z_bank[order[:k]].mean(0))  # bright - dark

z0 = torch.randn(1, LATENT_DIM, 1, 1, device=device)
alphas = torch.linspace(-3, 3, 9)
fig, axes = plt.subplots(1, 9, figsize=(16, 2))
walk_brightness = []
with torch.no_grad():
    for ax, a in zip(axes, alphas):
        img = G_local(z0 + a.to(device) * direction)
        walk_brightness.append(img.mean().item())
        ax.imshow(img[0].cpu().squeeze(), cmap='gray', vmin=-1, vmax=1)
        ax.set_title(f'α={a:.1f}', fontsize=8); ax.axis('off')
plt.suptitle('Walking the "brightness" direction: z0 + α·dir', fontsize=13)
plt.tight_layout(); plt.show()
print("Mean brightness along the walk:",
      " ".join(f"{b:+.2f}" for b in walk_brightness))
print("Monotonic increase = the direction does what we asked, on ANY starting z.")

# %% [markdown]
# ### lerp vs slerp — how to interpolate in a Gaussian latent space
#
# A high-dimensional Gaussian has almost all its mass on a thin **shell** of radius
# `≈ sqrt(dim)` (for us, `sqrt(100) = 10`). A straight line (**lerp**) between two shell
# points cuts *through* the low-probability interior — the generator never saw latents
# there, so midpoints can look washed out. **slerp** (spherical lerp) walks along the
# shell instead. The same shell picture explains StyleGAN's **truncation trick** in §3.

# %%
def slerp(z_a, z_b, t):
    a, b = z_a.flatten(), z_b.flatten()
    omega = torch.acos((a @ b) / (a.norm() * b.norm()))
    return ((torch.sin((1 - t) * omega) * a + torch.sin(t * omega) * b)
            / torch.sin(omega)).view_as(z_a)


z_a = torch.randn(1, LATENT_DIM, 1, 1, device=device)
z_b = torch.randn(1, LATENT_DIM, 1, 1, device=device)
ts = torch.linspace(0, 1, 8)

fig, axes = plt.subplots(2, 8, figsize=(14, 4))
with torch.no_grad():
    for j, t in enumerate(ts):
        lerp_z = (1 - t.to(device)) * z_a + t.to(device) * z_b
        slerp_z = slerp(z_a, z_b, t.to(device))
        axes[0, j].imshow(G_local(lerp_z)[0].cpu().squeeze(), cmap='gray')
        axes[1, j].imshow(G_local(slerp_z)[0].cpu().squeeze(), cmap='gray')
        axes[0, j].axis('off'); axes[1, j].axis('off')
        axes[0, j].set_title(f'|z|={lerp_z.norm():.1f}', fontsize=7)
        axes[1, j].set_title(f'|z|={slerp_z.norm():.1f}', fontsize=7)
plt.suptitle('lerp dips inside the Gaussian shell (norm shrinks); slerp stays on it\n'
             'top row: lerp | bottom row: slerp', fontsize=12)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 3. Z-space vs W-space: a 2D toy you can see
#
# Why does StyleGAN bother with an 8-layer MLP mapping `z -> w` before generating?
# Because the Gaussian prior `z` is **warped** relative to the data's true factors of
# variation — straight lines in z change several attributes at once (**entanglement**).
# The mapping network learns to *un-warp* the space, so that in **W** straight lines
# change one attribute cleanly.
#
# We can build this exactly, in 2D, with no training:
# - True attributes `w = (w1, w2)`: position along a spiral, and offset from it.
# - An analytic **entangling warp** `z = warp(w)` plays the role of "the Gaussian prior
#   doesn't match the data manifold".
# - "Decoding" maps attributes to a 2D point on the spiral.
#
# Then we compare a straight line **in W** with a straight line **in Z** between the same
# two endpoints.

# %%
from scipy.stats import norm as scipy_norm


def decode(w1, w2):
    """Attributes -> 2D data point. w1 in (0,1): position along spiral; w2: offset."""
    theta = 1.5 * np.pi * w1
    r = 0.3 + 0.7 * w1
    x = r * np.cos(theta) - w2 * np.sin(theta)
    y = r * np.sin(theta) + w2 * np.cos(theta)
    return x, y


def warp(w1, w2):
    """W -> Z: an invertible, entangling warp (the 'inverse mapping network')."""
    z1 = scipy_norm.ppf(np.clip(w1, 1e-6, 1 - 1e-6))   # probit: uniform -> gaussian
    z2 = w2 * 8 - 1.5 * np.sin(2.5 * z1)               # shear that depends on z1
    return z1, z2


def unwarp(z1, z2):
    """Z -> W: exact inverse of warp."""
    w1 = scipy_norm.cdf(z1)
    w2 = (z2 + 1.5 * np.sin(2.5 * z1)) / 8
    return w1, w2


# The dataset, as seen through each space
w1_s = np.random.rand(1500)
w2_s = np.random.randn(1500) * 0.06
xs, ys = decode(w1_s, w2_s)

# Two endpoints, a straight path in W vs a straight path in Z
wA, wB = np.array([0.10, -0.05]), np.array([0.90, 0.05])
zA, zB = np.array(warp(*wA)), np.array(warp(*wB))
t = np.linspace(0, 1, 60)
w_path = wA[None] * (1 - t[:, None]) + wB[None] * t[:, None]          # line in W
z_line = zA[None] * (1 - t[:, None]) + zB[None] * t[:, None]          # line in Z
w_from_z = np.stack(unwarp(z_line[:, 0], z_line[:, 1]), axis=1)        # what Z-line means in W

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
axes[0].scatter(xs, ys, c=w1_s, s=4, cmap='viridis', alpha=0.5)
for path, c, lab in [(w_path, 'red', 'line in W'), (w_from_z, 'orange', 'line in Z')]:
    px, py = decode(path[:, 0], path[:, 1])
    axes[0].plot(px, py, c=c, lw=2.5, label=lab)
axes[0].set_title('Data (colored by attribute w1) + decoded paths')
axes[0].legend(); axes[0].set_aspect('equal')

axes[1].plot(t, w_path[:, 0], 'r-', label='w1, line in W')
axes[1].plot(t, w_from_z[:, 0], 'r--', label='w1, line in Z')
axes[1].set_xlabel('t'); axes[1].set_title('Attribute 1 along the path')
axes[1].legend(); axes[1].grid(alpha=0.3)

axes[2].plot(t, w_path[:, 1], 'b-', label='w2, line in W')
axes[2].plot(t, w_from_z[:, 1], 'b--', label='w2, line in Z')
axes[2].set_xlabel('t'); axes[2].set_title('Attribute 2 along the path')
axes[2].legend(); axes[2].grid(alpha=0.3)
plt.suptitle('W-space: straight line = clean attribute change. '
             'Z-space: both attributes wiggle (entangled).', fontsize=12)
plt.tight_layout(); plt.show()

# %% [markdown]
# ### The truncation trick
#
# StyleGAN samples better-looking (but less diverse) faces by pulling each `w` toward the
# **average** latent: `w' = w_avg + ψ·(w − w_avg)` with `ψ < 1`. Rare, poorly-modeled
# corners of the space get avoided. In our 2D toy that's literally a shrink toward the
# center of W:

# %%
w_samples = np.stack([np.random.rand(800), np.random.randn(800) * 0.06], axis=1)
w_avg = w_samples.mean(0)

fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
for ax, psi in zip(axes, [1.0, 0.7, 0.3]):
    w_trunc = w_avg + psi * (w_samples - w_avg)
    px, py = decode(w_trunc[:, 0], w_trunc[:, 1])
    ax.scatter(px, py, s=4, alpha=0.5, c='teal')
    ax.set_title(f'ψ = {psi}'); ax.set_aspect('equal')
    ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.3, 1.3)
plt.suptitle("Truncation: ψ→0 collapses samples toward the 'average' point — "
             "safer but less diverse", fontsize=12)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 4. GAN inversion on the tiny GAN
#
# Inversion sounds exotic but it's just **gradient descent on the latent**: freeze `G`,
# treat `z` as the parameter, minimize `||G(z) − target||`. We do it on our 32x32 sandbox
# where 300 steps take seconds — the FFHQ version in §8 is *the same loop* with a bigger
# generator and a perceptual loss added.

# %%
def invert_local(G, target, steps=300, lr=0.05, z_init=None):
    """Recover a latent z such that G(z) ≈ target. Returns (z, loss_history)."""
    z = (torch.randn(1, LATENT_DIM, 1, 1, device=device) if z_init is None
         else z_init.clone().to(device))
    z.requires_grad_(True)
    opt = torch.optim.Adam([z], lr=lr)
    losses = []
    for _ in range(steps):
        loss = F.mse_loss(G(z), target)
        opt.zero_grad(); loss.backward(); opt.step()
        losses.append(loss.item())
    return z.detach(), losses


# Invert an image the generator itself produced — best case: it IS on G's manifold
z_true = torch.randn(1, LATENT_DIM, 1, 1, device=device)
with torch.no_grad():
    x_target = G_local(z_true)

z_opt, losses = invert_local(G_local, x_target)
with torch.no_grad():
    x_recon = G_local(z_opt)

cos = F.cosine_similarity(z_opt.flatten(), z_true.flatten(), dim=0).item()
fig, axes = plt.subplots(1, 4, figsize=(13, 3))
axes[0].plot(losses); axes[0].set_title('Inversion loss'); axes[0].set_xlabel('step')
axes[0].grid(alpha=0.3)
for ax, img, title in [(axes[1], x_target, 'Target  G(z_true)'),
                       (axes[2], x_recon, 'Recon  G(z_opt)')]:
    ax.imshow(img[0].detach().cpu().squeeze(), cmap='gray', vmin=-1, vmax=1)
    ax.set_title(title); ax.axis('off')
diff = (x_target - x_recon).abs()
axes[3].imshow(diff[0].detach().cpu().squeeze(), cmap='hot')
axes[3].set_title('|difference|'); axes[3].axis('off')
plt.tight_layout(); plt.show()
print(f"cosine(z_opt, z_true) = {cos:+.3f}")
print("Often well below 1.0: we recover the IMAGE, not necessarily the same z.")
print("Many latents can render (nearly) the same picture — inversion is underdetermined.")

# %% [markdown]
# ### Inverting *real* images — and what happens out of domain
#
# Now invert images the generator did **not** produce: a real Fashion-MNIST photo (in
# domain — works decently) and an MNIST digit (out of domain — the optimizer can only
# *project it onto the clothing manifold*, producing the nearest garment-looking thing).
# This failure is exactly why FFHQ inversion needs **face alignment** (stay in domain),
# **w+** (more degrees of freedom), and a **perceptual loss** (match structure, not pixels).

# %%
fm_test = torchvision.datasets.FashionMNIST(
    root='./data', train=False, download=True,
    transform=transforms.Compose([transforms.Resize(IMG_SIZE), transforms.ToTensor(),
                                  transforms.Normalize((0.5,), (0.5,))]))
mn_test = torchvision.datasets.MNIST(
    root='./data', train=False, download=True,
    transform=transforms.Compose([transforms.Resize(IMG_SIZE), transforms.ToTensor(),
                                  transforms.Normalize((0.5,), (0.5,))]))

real_fm = fm_test[0][0].unsqueeze(0).to(device)    # a real ankle boot
real_mn = mn_test[0][0].unsqueeze(0).to(device)    # a real digit 7 — out of domain

fig, axes = plt.subplots(2, 2, figsize=(6, 6))
for row, (target, name) in enumerate([(real_fm, 'Fashion-MNIST (in domain)'),
                                      (real_mn, 'MNIST digit (OUT of domain)')]):
    z_inv, lo = invert_local(G_local, target, steps=400)
    with torch.no_grad():
        recon = G_local(z_inv)
    axes[row, 0].imshow(target[0].cpu().squeeze(), cmap='gray', vmin=-1, vmax=1)
    axes[row, 0].set_title(f'Target: {name}', fontsize=9); axes[row, 0].axis('off')
    axes[row, 1].imshow(recon[0].cpu().squeeze(), cmap='gray', vmin=-1, vmax=1)
    axes[row, 1].set_title(f'Inverted (final loss {lo[-1]:.3f})', fontsize=9)
    axes[row, 1].axis('off')
plt.suptitle('Inversion projects targets onto what G can draw', fontsize=12)
plt.tight_layout(); plt.show()
print("The digit comes back garment-shaped: G can only render its own manifold.")
print("Same reason a misaligned face inverts badly in StyleGAN — it's out of domain.")

# %% [markdown]
# ---
# # Part B — StyleGAN2 on Colab (GPU)
#
# Everything from Part A, at face scale. From here on the cells need a **CUDA GPU**.
#
# ## 5. Setup & load the pretrained generator
#
# We use NVIDIA's official **stylegan2-ada-pytorch** repo (it ships the network code and a
# loader for pretrained FFHQ weights). Run these once per Colab session:
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
#
# The generator splits into the two parts you met in §3, plus a per-layer latent:
#
# ```
#   z (512)                       w (512)                 w+ (num_ws x 512)
#  ───────► [ mapping: 8-layer MLP ] ───────► broadcast ─────────────────────┐
#                                                                            ▼
#                       [ synthesis network: 4x4 → 8x8 → ... → 1024x1024 ]──► image
#                         layers 0-3        4-9            10+
#                         "coarse"          "mid"          "fine"
#                         pose, face shape  features, hair color, texture
# ```
#
# (Each synthesis layer also receives a random **noise input** for stochastic detail —
# stubble, freckles — separate from the **style** `w` that controls structure.)
#
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
# ## 6. Sample faces
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
# ### The truncation trick, for real
#
# §3's toy showed truncation as a shrink toward the average attribute point. Here it is on
# faces: same z's, three values of ψ. Low ψ = safer, more "average" faces; ψ=1 = full
# diversity including odd artifacts.

# %%
if ON_GPU and G is not None:
    z_fix = torch.randn(4, G.z_dim, device=device)
    with torch.no_grad():
        w_avg_sg = G.mapping(torch.randn(5000, G.z_dim, device=device), None).mean(0, keepdim=True)
        fig, axes = plt.subplots(3, 4, figsize=(10, 8))
        for r, psi in enumerate([0.3, 0.7, 1.0]):
            w_psi = w_avg_sg + psi * (G.mapping(z_fix, None) - w_avg_sg)
            pics = to_image(G.synthesis(w_psi, noise_mode="const"))
            for c in range(4):
                axes[r, c].imshow(pics[c]); axes[r, c].axis('off')
            axes[r, 0].set_ylabel(f'ψ={psi}', fontsize=11)
    plt.suptitle('Truncation sweep: w_avg + ψ·(w − w_avg)', fontsize=13)
    plt.tight_layout(); plt.show()
else:
    print("[skipped] truncation sweep — GPU only.")
    print("Concept: pull w toward the average latent; ψ trades diversity for quality (§3 toy).")

# %% [markdown]
# ## 7. Style Mixing — proving layers control different scales
#
# This is §2's "directions" idea taken further: instead of steering one latent, we splice
# **two** latents at a chosen layer depth. `w+` has one `w` vector **per layer**
# (`num_ws ≈ 18` for 1024px). We build a "crossover": take the first `k` layers from face
# A's `w+` and the rest from face B's `w+`, synthesize, and see what transfers.
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
# ## 8. GAN Inversion — editing a *real* photo
#
# Style mixing edits generated faces. To edit a **real** person we must first find the
# latent that reproduces their photo. That's **GAN inversion**: solve for `w+` such that
# `G.synthesis(w+) ≈ target_photo`.
#
# **You already ran this loop in §4** — same algorithm, three upgrades:
#
# | | §4 tiny GAN | here (FFHQ) |
# |---|---|---|
# | latent optimized | `z` (100-d) | `w+` (num_ws × 512 — far more freedom) |
# | init | random | mean `w` over 10k samples (a good prior) |
# | loss | pixel MSE | MSE + **VGG perceptual** (match structure, not pixels) |
#
# Where you optimize matters: plain `w` (one vector for all layers) inverts worse but
# edits better; `w+` (per-layer) reconstructs almost perfectly but can drift off the
# manifold; some methods also optimize the per-layer **noise maps** for fine detail.
# We use `w+` — the standard for editing pipelines.
#
# Two families:
# - **Optimization-based** (shown below): start from the mean `w`, gradient-descend `w+` to
#   minimize a perceptual + pixel loss against the target. Slow (~1–2 min/image) but no extra
#   model. This is the most instructive, so we implement it.
# - **Encoder-based** (e4e, pSp, ReStyle): a network trained to predict `w+` in one forward
#   pass. Fast, better for editing; you'd load a pretrained encoder.
#
# **Aligning the face first matters.** FFHQ faces are centered/cropped a specific way.
# Real photos must be aligned the same (eyes on a fixed line) or inversion struggles —
# §4's out-of-domain MNIST digit showed exactly this failure mode. We handle alignment in
# the Module 16 capstone.

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
    print("Concept: §4's gradient-descent-on-the-latent, scaled up with w+ and a perceptual loss.")

# %% [markdown]
# ## 9. A First Hairstyle Blend ("Barbershop-lite")
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
# ## 10. Exercises
#
# > Exercises 10.1–10.2 run **locally** on the Part A sandbox. 10.3–10.4 need the Colab GPU
# > session from Part B.
#
# ### Exercise 10.1 — Find a different direction (local)
#
# §2 found a *brightness* direction. Find a **"trouser-likeness"** direction in the
# Fashion-MNIST GAN: use the mean intensity of the **bottom half** of the image as the
# attribute proxy (trousers fill the bottom; shoes/bags don't), build the direction from
# the top/bottom deciles of 2000 samples, and walk a random z along it. Show the strip.

# %%
# TODO: compute a bottom-half-intensity direction and walk z0 along it
# Hint: proxy = imgs[:, :, IMG_SIZE//2:, :].mean(dim=(1, 2, 3))
#       then reuse the §2 recipe: dir = z[top 10%].mean(0) - z[bottom 10%].mean(0)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: bottom-half-intensity ("trouser-likeness") direction
proxy = torch.empty(N)
with torch.no_grad():
    for i in range(0, N, 250):
        imgs = G_local(z_bank[i:i + 250])
        proxy[i:i + 250] = imgs[:, :, IMG_SIZE // 2:, :].mean(dim=(1, 2, 3)).cpu()

order_p = proxy.argsort()
dir_trouser = z_bank[order_p[-k:]].mean(0) - z_bank[order_p[:k]].mean(0)

z0_ex = torch.randn(1, LATENT_DIM, 1, 1, device=device)
fig, axes = plt.subplots(1, 9, figsize=(16, 2))
with torch.no_grad():
    for ax, a in zip(axes, torch.linspace(-3, 3, 9)):
        img = G_local(z0_ex + a.to(device) * dir_trouser)
        ax.imshow(img[0].cpu().squeeze(), cmap='gray', vmin=-1, vmax=1)
        ax.set_title(f'α={a:.1f}', fontsize=8); ax.axis('off')
plt.suptitle('Walking the "bottom-half mass" (trouser-likeness) direction', fontsize=13)
plt.tight_layout(); plt.show()
print("The garment elongates downward as α grows — a semantic edit from a dumb pixel proxy.")
print("With a real classifier as the proxy you get clean attribute sliders the same way.")

# %% [markdown]
# ### Exercise 10.2 — Inversion init matters (local)
#
# §8's FFHQ inversion initializes from the **mean latent**. Test why, on the sandbox:
# invert the same target three times, starting from (a) `z = 0`, (b) a random `z`,
# (c) the **mean of 100 random z's**. Plot the three loss curves on one figure.
# Which starts lower? Which converges fastest?

# %%
# TODO: run invert_local 3x with different z_init values and compare loss curves
# Hint: invert_local(G_local, x_target, z_init=...) — try torch.zeros, torch.randn,
#       and torch.randn(100, LATENT_DIM, 1, 1).mean(0, keepdim=True)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: compare inversion starting points
inits = {
    'z = 0': torch.zeros(1, LATENT_DIM, 1, 1),
    'random z': torch.randn(1, LATENT_DIM, 1, 1),
    'mean of 100 z': torch.randn(100, LATENT_DIM, 1, 1).mean(0, keepdim=True),
}
plt.figure(figsize=(8, 4))
for label, z_init in inits.items():
    _, lo = invert_local(G_local, x_target, steps=300, z_init=z_init)
    plt.plot(lo, label=f'{label} (final {lo[-1]:.4f})')
plt.xlabel('step'); plt.ylabel('MSE'); plt.yscale('log')
plt.legend(); plt.grid(alpha=0.3)
plt.title('Same target, three inversion starting points')
plt.tight_layout(); plt.show()
print("The averaged init starts near the 'typical' latent — usually lower initial loss")
print("and smoother descent. Same logic as StyleGAN's mean-w init in invert_image (§8).")

# %% [markdown]
# ### Exercise 10.3 — Find the hair layers (Colab)
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
# ### Exercise 10.4 — Invert a real photo of yourself (Colab)
#
# Load a real portrait (your own, or a public-domain one), align/crop it to a centered
# face, resize to `G.img_resolution`, scale to `[-1, 1]`, and run `invert_image`. Show
# target vs reconstruction. Then apply a hair blend with a generated target.
#
# Tip: face alignment matters a lot. You can borrow the FFHQ alignment helper
# (`face_alignment` / dlib 68-landmarks) — we set that up properly in Module 16. Save your
# aligned photo as `my_aligned_face.png` next to this notebook before running the solution.

# %%
# TODO: load + align a real photo, invert it, show reconstruction, then blend hair
# Hint: target = (TF.to_tensor(aligned_pil).to(device) * 2 - 1).unsqueeze(0)
#       then w = invert_image(G, target, steps=400)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: invert your own (aligned) photo, then blend in generated hair
if ON_GPU and G is not None and os.path.exists("my_aligned_face.png"):
    from PIL import Image
    import torchvision.transforms.functional as TF

    pil = Image.open("my_aligned_face.png").convert("RGB").resize(
        (G.img_resolution, G.img_resolution))
    target = (TF.to_tensor(pil).to(device) * 2 - 1).unsqueeze(0)

    print("Inverting your photo (~1-2 min)...")
    w_real = invert_image(G, target, steps=400, lr=0.05, device=device)
    with torch.no_grad():
        recon = G.synthesis(w_real, noise_mode="const")
        w_hair = G.mapping(torch.randn(1, G.z_dim, device=device), None)
        blended = G.synthesis(hair_blend(w_real, w_hair), noise_mode="const")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(to_image(target)[0]); axes[0].set_title('You (aligned)'); axes[0].axis('off')
    axes[1].imshow(to_image(recon)[0]); axes[1].set_title('Inverted'); axes[1].axis('off')
    axes[2].imshow(to_image(blended)[0]); axes[2].set_title('+ generated hair'); axes[2].axis('off')
    plt.tight_layout(); plt.show()
    print("Imperfect identity in the blend is expected — Module 16 adds masking to fix it.")
else:
    print("[skipped] Needs: Colab GPU, loaded G, and 'my_aligned_face.png' in the working dir.")
    print("To create one: take a portrait, align with the Module 16 aligner (eyes level,")
    print("face centered, square crop), save as my_aligned_face.png, re-run this cell.")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Latent direction** | A direction in latent space = an attribute edit; found by contrasting high/low attribute groups — works on any GAN |
# | **lerp vs slerp / Gaussian shell** | High-dim Gaussians live on a shell; interpolate along it, and truncation (ψ) trades diversity for quality |
# | **Z vs W space** | The mapping network un-warps the Gaussian prior so straight lines in W change one attribute cleanly (disentanglement) |
# | **GAN inversion** | Gradient descent on the latent recovers the *image*, not the z; out-of-domain targets only project onto G's manifold |
# | **StyleGAN2 structure** | `G.mapping` (z→w+) + `G.synthesis` (w+→image); one w per layer enables per-scale control |
# | **Style mixing** | Coarse layers = pose/shape, mid = features/hair structure, fine = color/texture |
# | **Hairstyle blend** | Copy the target's hair-controlling layers into the source's w+ — crude but real; the capstone adds masking |
#
# ## Further reading
#
# - **StyleGAN2 paper** (Analyzing and Improving the Image Quality of StyleGAN):
#   https://arxiv.org/abs/1912.04958
# - **Image2StyleGAN** (the original optimization-based inversion into w+):
#   https://arxiv.org/abs/1904.03189
# - **e4e — Designing an Encoder for StyleGAN Image Manipulation** (encoder-based inversion,
#   the editability/reconstruction trade-off): https://arxiv.org/abs/2102.02766
# - **pSp — Encoding in Style** (pixel2style2pixel encoder): https://arxiv.org/abs/2008.00951
# - **stylegan2-ada-pytorch** (NVIDIA's official repo used in Part B):
#   https://github.com/NVlabs/stylegan2-ada-pytorch
#
# **Next:** [Module 15 — Diffusion Models →](../15_diffusion/01_diffusion.ipynb) — the other
# (and now dominant) generative paradigm, plus mask-targeted **inpainting** for "Route B" of
# the swap.
