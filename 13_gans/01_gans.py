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
# # Module 13.1 — GANs from Scratch (and the road to StyleGAN)
#
# **Purpose:** VAEs sample but blur, and a convincing hairstyle swap needs **sharp**
# synthesis — which adversarial training delivers. In this **Advanced Image AI track**
# module you build a DCGAN from scratch, learn to diagnose its classic failure modes, and
# see how StyleGAN's per-layer styles become the editing handle the hairstyle-swap
# capstone (Module 16) ultimately exploits.
#
# **Prerequisites:** Module 12 (latent spaces).
#
# VAEs (Module 12) gave us a samplable latent space, but the images came out **blurry**.
# The reason: the VAE's pixel-wise reconstruction loss rewards "average" outputs. For a
# convincing hairstyle swap we need **sharp** synthesis. Enter the **GAN**.
#
# A Generative Adversarial Network (Goodfellow et al., 2014) trains two networks in a duel:
# - a **Generator** `G` that turns random noise `z` into a fake image
# - a **Discriminator** `D` that tries to tell real images from `G`'s fakes
#
# They improve by competing. `G` gets better at fooling `D`; `D` gets better at catching `G`.
# At equilibrium, `G`'s output is indistinguishable from real data. No blur-inducing pixel
# loss — `D` is the loss, and it cares about *realism*.
#
# **What you'll learn:**
# - The adversarial (minimax) training loop and its loss
# - Build a **DCGAN** (deep convolutional GAN) from scratch and train it on a laptop
# - Diagnose **mode collapse** and instability — the things that make GANs tricky
# - How **StyleGAN** restructures the generator to give *layer-by-layer control* — which is
#   exactly what lets us edit hair without touching identity (Module 14)

# %%
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

import torchvision
import torchvision.transforms as transforms
import torchvision.utils as vutils

import numpy as np
import matplotlib.pyplot as plt

# %matplotlib inline

torch.manual_seed(42)
np.random.seed(42)

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
print(f"PyTorch {torch.__version__} | device: {device}")

# %% [markdown]
# ## 1. The Data
#
# We train on Fashion-MNIST resized to **32x32** (a power of two, which DCGAN's strided
# convolutions like). Images are normalized to `[-1, 1]` to match the generator's `tanh`
# output. This trains in a few minutes on CPU/MPS and clearly shows the GAN learning.
#
# > Want faces? Swap in a 32x32 CelebA crop — the architecture below is unchanged except
# > `IMG_CHANNELS = 3`. We keep grayscale clothing here purely for laptop speed.

# %%
IMG_SIZE = 32
IMG_CHANNELS = 1
LATENT_DIM = 100   # size of the noise vector z

transform = transforms.Compose([
    transforms.Resize(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,)),  # [0,1] -> [-1,1]
])

dataset = torchvision.datasets.FashionMNIST(
    root='./data', train=True, download=True, transform=transform)
loader = DataLoader(dataset, batch_size=128, shuffle=True, drop_last=True)
print(f"Samples: {len(dataset)} | image: {dataset[0][0].shape} | pixel range ~[-1, 1]")

# %% [markdown]
# ## 2. The Generator
#
# `G` maps a noise vector `z` (shape `(LATENT_DIM, 1, 1)`) up to a full image. It uses
# **transposed convolutions** (`ConvTranspose2d`) to *upsample*: 1x1 -> 4x4 -> 8x8 -> 16x16
# -> 32x32. BatchNorm stabilizes training; `tanh` puts the output in `[-1, 1]`.

# %%
class Generator(nn.Module):
    def __init__(self, latent_dim=LATENT_DIM, channels=IMG_CHANNELS, feat=64):
        super().__init__()
        self.net = nn.Sequential(
            # z: (latent_dim, 1, 1) -> (feat*4, 4, 4)
            nn.ConvTranspose2d(latent_dim, feat * 4, 4, 1, 0, bias=False),
            nn.BatchNorm2d(feat * 4), nn.ReLU(True),
            # -> (feat*2, 8, 8)
            nn.ConvTranspose2d(feat * 4, feat * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat * 2), nn.ReLU(True),
            # -> (feat, 16, 16)
            nn.ConvTranspose2d(feat * 2, feat, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat), nn.ReLU(True),
            # -> (channels, 32, 32)
            nn.ConvTranspose2d(feat, channels, 4, 2, 1, bias=False),
            nn.Tanh(),
        )

    def forward(self, z):
        return self.net(z)


# %% [markdown]
# ## 3. The Discriminator
#
# `D` is a CNN classifier (like Module 08) that downsamples an image to a single
# real-vs-fake score. DCGAN uses **strided convolutions** (no pooling) and **LeakyReLU**.

# %%
class Discriminator(nn.Module):
    def __init__(self, channels=IMG_CHANNELS, feat=64):
        super().__init__()
        self.net = nn.Sequential(
            # (channels, 32, 32) -> (feat, 16, 16)
            nn.Conv2d(channels, feat, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            # -> (feat*2, 8, 8)
            nn.Conv2d(feat, feat * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat * 2), nn.LeakyReLU(0.2, inplace=True),
            # -> (feat*4, 4, 4)
            nn.Conv2d(feat * 2, feat * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feat * 4), nn.LeakyReLU(0.2, inplace=True),
            # -> (1, 1, 1)  single score
            nn.Conv2d(feat * 4, 1, 4, 1, 0, bias=False),
        )

    def forward(self, x):
        return self.net(x).view(-1)  # (B,) raw logits


def weights_init(m):
    """DCGAN paper init: conv weights ~ N(0, 0.02)."""
    if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d)):
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif isinstance(m, nn.BatchNorm2d):
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


G = Generator().to(device); G.apply(weights_init)
D = Discriminator().to(device); D.apply(weights_init)
print(f"G params: {sum(p.numel() for p in G.parameters()):,}")
print(f"D params: {sum(p.numel() for p in D.parameters()):,}")

# Confirm shapes line up
z = torch.randn(8, LATENT_DIM, 1, 1, device=device)
fake = G(z)
print(f"\nz {tuple(z.shape)} --G--> {tuple(fake.shape)} --D--> {tuple(D(fake).shape)}")

# %% [markdown]
# ## 4. The Adversarial Training Loop
#
# Each step has two updates:
#
# **Train D:** show it real images (label 1) and fake images (label 0). It learns to score
# reals high and fakes low. Loss = BCE on both.
#
# **Train G:** generate fakes and ask D to score them. G wants D to say "real" (label 1),
# so it's rewarded when it *fools* D. Crucially, we backprop *through* D into G but only
# update G's weights.
#
# We use `BCEWithLogitsLoss` (D outputs raw logits). A common stabilizer: use label `0.9`
# for "real" (one-sided label smoothing).

# %%
criterion = nn.BCEWithLogitsLoss()
opt_G = optim.Adam(G.parameters(), lr=2e-4, betas=(0.5, 0.999))
opt_D = optim.Adam(D.parameters(), lr=2e-4, betas=(0.5, 0.999))

# Fixed noise so we can watch the SAME latents improve across epochs
fixed_noise = torch.randn(32, LATENT_DIM, 1, 1, device=device)

REAL_LABEL = 0.9   # one-sided label smoothing
FAKE_LABEL = 0.0


def train_gan(epochs=5):
    history = {'loss_D': [], 'loss_G': []}
    snapshots = []
    for epoch in range(epochs):
        ld, lg, n = 0.0, 0.0, 0
        for real, _ in loader:
            real = real.to(device)
            b = real.size(0)

            # ---- Train D ----
            opt_D.zero_grad()
            # real batch
            out_real = D(real)
            loss_real = criterion(out_real, torch.full((b,), REAL_LABEL, device=device))
            # fake batch
            noise = torch.randn(b, LATENT_DIM, 1, 1, device=device)
            fake = G(noise)
            out_fake = D(fake.detach())  # detach: don't update G here
            loss_fake = criterion(out_fake, torch.full((b,), FAKE_LABEL, device=device))
            loss_D = loss_real + loss_fake
            loss_D.backward(); opt_D.step()

            # ---- Train G ----
            opt_G.zero_grad()
            out = D(fake)  # re-score the SAME fakes, now updating G
            # G wants D to output "real"
            loss_G = criterion(out, torch.full((b,), REAL_LABEL, device=device))
            loss_G.backward(); opt_G.step()

            ld += loss_D.item(); lg += loss_G.item(); n += 1

        history['loss_D'].append(ld / n)
        history['loss_G'].append(lg / n)
        print(f"Epoch {epoch+1}/{epochs}  loss_D: {ld/n:.3f}  loss_G: {lg/n:.3f}")

        # Snapshot fixed-noise outputs
        G.eval()
        with torch.no_grad():
            snap = G(fixed_noise).cpu()
        G.train()
        snapshots.append(snap)
    return history, snapshots


print("Training DCGAN (a few epochs is enough to see structure emerge)...")
print("-" * 60)
history, snapshots = train_gan(epochs=5)

# %% [markdown]
# ### Watch the generator learn
#
# The same fixed noise vectors, decoded after each epoch. Early epochs = noise; later
# epochs = recognizable clothing. (5 epochs on a laptop won't be photorealistic — that's
# expected. The point is to *see the mechanism work*.)

# %%
fig, axes = plt.subplots(1, len(snapshots), figsize=(16, 4))
for e, snap in enumerate(snapshots):
    grid = vutils.make_grid(snap[:16], nrow=4, normalize=True, padding=1)
    axes[e].imshow(grid.permute(1, 2, 0).squeeze(), cmap='gray')
    axes[e].set_title(f'Epoch {e+1}'); axes[e].axis('off')
plt.suptitle('DCGAN samples (fixed noise) improving over training', fontsize=13)
plt.tight_layout()
plt.show()

# %%
# Loss curves. Note: GAN losses DON'T converge to zero — they oscillate around an
# equilibrium. A flat-lined D loss (near 0) means D won and G stopped learning.
plt.figure(figsize=(9, 4))
plt.plot(history['loss_D'], 'b-o', label='Discriminator')
plt.plot(history['loss_G'], 'r-o', label='Generator')
plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.grid(True, alpha=0.3)
plt.title('Adversarial losses (oscillation is normal, not a bug)')
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 5. Failure Modes (why GANs are famously finicky)
#
# - **Mode collapse:** `G` discovers one (or few) images that reliably fool `D` and emits
#   only those — your samples all look identical. Fixes: more diverse minibatches,
#   different losses (WGAN-GP), spectral norm.
# - **Vanishing gradients:** if `D` gets too good too fast, `G` gets no useful signal
#   (`loss_D -> 0`, `loss_G` blows up). Balance the two (sometimes train `G` more often).
# - **Instability:** the two-player game can oscillate or diverge. Hence the careful tricks:
#   lr=2e-4, betas=(0.5, 0.999), BatchNorm, LeakyReLU, label smoothing.
#
# These headaches are a big reason **diffusion models** (Module 15) have largely overtaken
# GANs for general generation — they train with a stable, simple regression loss. But GANs
# still win on speed and on the *editable latent space* that StyleGAN provides.

# %% [markdown]
# ## 6. From DCGAN to StyleGAN (concept — no training here)
#
# Our DCGAN feeds noise `z` straight into the first layer. StyleGAN (Karras et al., 2019)
# rebuilds the generator so that **different layers control different visual scales**, which
# is *the* property that makes clean attribute editing — like swapping hair — possible.
#
# Key changes, conceptually:
#
# 1. **Mapping network.** Instead of using `z` directly, an 8-layer MLP maps `z` -> `w`.
#    This `w` lives in a "disentangled" space `W` where directions correspond to meaningful
#    attributes (pose, age, hair) instead of being tangled together.
#
# 2. **Per-layer style injection (AdaIN).** The *same* `w` (or a per-layer stack `w+`) is
#    fed into **every** layer of the generator via adaptive instance normalization. So `w`
#    sets the "style" at each resolution.
#
# 3. **Coarse-to-fine control.** Because layers run low-res -> high-res:
#    - **Coarse layers** (4x4–8x8) control pose, face shape, overall hair shape.
#    - **Middle layers** (16x16–32x32) control finer features, hairstyle structure.
#    - **Fine layers** (64x64+) control color and micro-texture (hair color, strands).
#
# 4. **Style mixing.** Feed `w_A` to the coarse layers and `w_B` to the fine layers and you
#    get person A's structure with person B's colors. **This is the seed of a hairstyle
#    swap**: take the hair-controlling layers from a target and graft them onto a source.
#
# ```
#   z --[mapping MLP]--> w  ──► injected into EVERY layer (AdaIN)
#                              coarse: pose/shape | mid: features/hairstyle | fine: color
# ```
#
# Training StyleGAN needs serious GPU time, so in Module 14 we load a **pretrained**
# StyleGAN2 and do the editing — including a first crude hairstyle blend.

# %% [markdown]
# ## 7. Exercises
#
# ### Exercise 7.1 — Latent walk
#
# With your trained `G`, generate a smooth **interpolation** between two random noise
# vectors `z_a` and `z_b` (decode points along the line between them) and display the strip.
# This is the GAN analogue of Module 12's VAE interpolation — and a sanity check that the
# latent space is smooth rather than collapsed.

# %%
# TODO: interpolate between two random z vectors and show the decoded strip
# Hint: zs = [(1-t)*z_a + t*z_b for t in torch.linspace(0,1,10)]
#       remember z has shape (1, LATENT_DIM, 1, 1)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: latent walk
G.eval()
z_a = torch.randn(1, LATENT_DIM, 1, 1, device=device)
z_b = torch.randn(1, LATENT_DIM, 1, 1, device=device)
ts = torch.linspace(0, 1, 10, device=device)
with torch.no_grad():
    walk = torch.cat([(1 - t) * z_a + t * z_b for t in ts], dim=0)
    imgs = G(walk).cpu()

fig, axes = plt.subplots(1, 10, figsize=(16, 2))
for i in range(10):
    axes[i].imshow(imgs[i].squeeze(), cmap='gray'); axes[i].axis('off')
    axes[i].set_title(f't={ts[i]:.1f}', fontsize=8)
plt.suptitle('GAN latent walk: z_a -> z_b', fontsize=13)
plt.tight_layout()
plt.show()
G.train()
print("Smooth morph = healthy latent space. Abrupt jumps / repeats = partial collapse.")

# %% [markdown]
# ### Exercise 7.2 — Detect mode collapse
#
# Generate 64 samples from random noise and measure their **diversity**. A simple proxy:
# the mean pairwise pixel distance between samples. Print it, and show the 64-sample grid.
# (Optionally, deliberately induce collapse by training G with a much higher lr, e.g. 1e-3,
# and compare the diversity number.)

# %%
# TODO: generate 64 samples, show the grid, and compute a diversity score
# Hint: diversity ~ mean std across the batch per pixel, or mean pairwise L2 distance.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: diversity check
G.eval()
with torch.no_grad():
    noise = torch.randn(64, LATENT_DIM, 1, 1, device=device)
    samples = G(noise).cpu()

# Diversity proxy 1: average per-pixel std across the 64 samples
per_pixel_std = samples.std(dim=0).mean().item()
# Diversity proxy 2: mean pairwise L2 distance on a subset (flattened)
flat = samples.view(64, -1)
dists = torch.cdist(flat, flat)
mean_pairwise = dists[dists > 0].mean().item()

print(f"Per-pixel std across samples: {per_pixel_std:.4f}  (higher = more diverse)")
print(f"Mean pairwise L2 distance:    {mean_pairwise:.4f}")
print("If these are near zero, G has collapsed to (nearly) one image.")

grid = vutils.make_grid(samples, nrow=8, normalize=True, padding=1)
plt.figure(figsize=(10, 10))
plt.imshow(grid.permute(1, 2, 0).squeeze(), cmap='gray')
plt.title('64 random samples — eyeball the diversity')
plt.axis('off')
plt.tight_layout()
plt.show()
G.train()

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **GAN** | Generator and discriminator train adversarially; `D` *is* the loss, and because it judges realism (not pixel error), outputs are **sharp** where VAEs blur |
# | **DCGAN** | Transposed-conv generator + strided-conv discriminator; the stabilizing recipe (BatchNorm, LeakyReLU, lr=2e-4, betas=(0.5,0.999), label smoothing) exists because training is delicate |
# | **Oscillating losses** | GAN losses don't go to zero — watch the *samples*, not just the loss |
# | **Mode collapse** | The classic failure mode (with instability) to recognize and diagnose |
# | **StyleGAN** | A mapping network (`z`→`w`) plus per-layer style injection gives coarse-to-fine control and **style mixing** — the mechanism we'll exploit to swap hair |
#
# ## Further reading
#
# - **GAN paper** (Goodfellow et al. — the original adversarial framework):
#   https://arxiv.org/abs/1406.2661
# - **DCGAN** (the convolutional architecture and training recipe used here):
#   https://arxiv.org/abs/1511.06434
# - **PyTorch DCGAN tutorial** (the same model on CelebA faces, official walkthrough):
#   https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html
# - **StyleGAN** (A Style-Based Generator Architecture — the mapping network and per-layer
#   styles): https://arxiv.org/abs/1812.04948
#
# **Next:** [StyleGAN & GAN Inversion →](../14_stylegan_inversion/01_stylegan_inversion.ipynb)
# — load a pretrained StyleGAN2, edit real photos via inversion, and attempt a first
# hairstyle blend.
