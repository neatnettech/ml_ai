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
# # Module 12.1 — Autoencoders & Variational Autoencoders
#
# In Module 11 we learned to find *where* the hair is. Now we start building a model that
# can *generate* image content — because a hairstyle swap ultimately has to **synthesize**
# new hair pixels, not just copy them.
#
# Every modern generator (GANs, diffusion, StyleGAN) rests on one idea: a **latent space**.
# Instead of working with raw pixels, the model learns a compact code — a short vector —
# that captures the *essence* of an image. Editing happens in that latent space. This module
# builds the simplest model that has one: the **autoencoder**, then upgrades it to a
# **variational autoencoder (VAE)** that can actually generate new images.
#
# **What you'll learn:**
# - What a latent space is and why generation needs one
# - Build a plain **autoencoder** from scratch and visualize its compressed codes
# - Why a plain AE *can't* generate, and how the **VAE** fixes it (the reparameterization trick + KL loss)
# - **Latent interpolation** — morph smoothly between two images (the core trick behind hair editing)
# - Sample brand-new images from the learned distribution

# %%
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader

import torchvision
import torchvision.transforms as transforms

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
# We use Fashion-MNIST (from Module 08) — small 28x28 grayscale images that train fast on a
# laptop. Everything here transfers directly to faces; we just keep the images small so the
# whole notebook runs on CPU/MPS in a couple of minutes. (A note at the end shows what
# changes for a face dataset like CelebA.)

# %%
transform = transforms.Compose([transforms.ToTensor()])  # keep pixels in [0, 1]

train_ds = torchvision.datasets.FashionMNIST(
    root='./data', train=True, download=True, transform=transform)
test_ds = torchvision.datasets.FashionMNIST(
    root='./data', train=False, download=True, transform=transform)

train_loader = DataLoader(train_ds, batch_size=128, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=128, shuffle=False)

class_names = ['T-shirt', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']
print(f"Train: {len(train_ds)}  Test: {len(test_ds)}  | image shape: {train_ds[0][0].shape}")

# %% [markdown]
# ## 2. The Plain Autoencoder
#
# An autoencoder has two halves joined at a bottleneck:
#
# ```
#   image (784) ──► ENCODER ──► z (latent, e.g. 16-d) ──► DECODER ──► reconstruction (784)
# ```
#
# - The **encoder** squeezes the image down to a tiny vector `z`.
# - The **decoder** tries to rebuild the original image from just `z`.
# - The loss is **reconstruction error** (how different is the output from the input).
#
# Because `z` is much smaller than the image, the network is forced to keep only the
# information that matters. That compressed `z` *is* the latent representation.

# %%
LATENT_DIM = 16


class Autoencoder(nn.Module):
    def __init__(self, latent_dim=LATENT_DIM):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Flatten(),                 # (B, 784)
            nn.Linear(784, 256), nn.ReLU(),
            nn.Linear(256, 64), nn.ReLU(),
            nn.Linear(64, latent_dim),    # bottleneck
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.ReLU(),
            nn.Linear(64, 256), nn.ReLU(),
            nn.Linear(256, 784), nn.Sigmoid(),  # back to [0, 1]
        )

    def forward(self, x):
        z = self.encoder(x)
        out = self.decoder(z)
        return out.view(-1, 1, 28, 28), z


ae = Autoencoder().to(device)
print(ae)
print(f"\nLatent dim: {LATENT_DIM}  (compressing 784 -> {LATENT_DIM} numbers)")

# %%
def train_ae(model, loader, epochs=8, lr=1e-3):
    opt = optim.Adam(model.parameters(), lr=lr)
    for epoch in range(epochs):
        model.train()
        running = 0.0
        for imgs, _ in loader:
            imgs = imgs.to(device)
            recon, _ = model(imgs)
            loss = F.mse_loss(recon, imgs)
            opt.zero_grad(); loss.backward(); opt.step()
            running += loss.item() * imgs.size(0)
        print(f"Epoch {epoch+1}/{epochs}  recon MSE: {running/len(loader.dataset):.5f}")


print("Training autoencoder...")
print("-" * 50)
train_ae(ae, train_loader, epochs=8)

# %%
# Reconstructions: top row = input, bottom row = AE output
ae.eval()
imgs, _ = next(iter(test_loader))
with torch.no_grad():
    recon, _ = ae(imgs.to(device))
recon = recon.cpu()

fig, axes = plt.subplots(2, 8, figsize=(14, 4))
for i in range(8):
    axes[0, i].imshow(imgs[i].squeeze(), cmap='gray'); axes[0, i].axis('off')
    axes[1, i].imshow(recon[i].squeeze(), cmap='gray'); axes[1, i].axis('off')
axes[0, 0].set_ylabel('input')
plt.suptitle('Autoencoder reconstructions (top: input, bottom: output)', fontsize=13)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. Why a Plain AE Can't *Generate*
#
# Reconstruction works. But suppose we want a **new** image — we'd sample a random `z` and
# decode it. With a plain AE this fails: the encoder is free to scatter codes anywhere it
# likes, so most of the latent space is "empty" (decodes to garbage). There's no structure
# saying *which* `z` values are valid.
#
# Let's prove it: sample random latents and decode them.

# %%
ae.eval()
with torch.no_grad():
    random_z = torch.randn(8, LATENT_DIM, device=device)  # random codes
    fake = ae.decoder(random_z).view(-1, 1, 28, 28).cpu()

fig, axes = plt.subplots(1, 8, figsize=(14, 2))
for i in range(8):
    axes[i].imshow(fake[i].squeeze(), cmap='gray'); axes[i].axis('off')
plt.suptitle('Plain AE: decoding random latents -> mostly garbage', fontsize=13)
plt.tight_layout()
plt.show()
print("The decoder never learned what an arbitrary z should look like.")
print("The VAE fixes this by forcing the latent space to be well-organized.")

# %% [markdown]
# ## 4. The Variational Autoencoder (VAE)
#
# The VAE (Kingma & Welling, 2013) makes the latent space **generatable** by adding two
# ingredients:
#
# **1. The encoder outputs a distribution, not a point.** Instead of a single `z`, it
# outputs a mean `μ` and a (log) variance `logσ²`. We then *sample* `z ~ N(μ, σ²)`.
#
# **2. A KL-divergence loss pulls every `μ, σ` toward the standard normal `N(0, 1)`.**
# This packs all the codes into one tidy, gap-free blob centered at the origin — so a
# random `z ~ N(0, 1)` now lands somewhere meaningful and decodes to a real-looking image.
#
# **The reparameterization trick.** Sampling is random, and you can't backprop through
# randomness. The fix: write `z = μ + σ · ε` where `ε ~ N(0, 1)`. The randomness lives in
# `ε` (no gradient needed), while `μ` and `σ` stay on the differentiable path.
#
# **Loss = reconstruction + β · KL.** Reconstruction keeps images sharp; KL keeps the space
# organized. They pull against each other — that tension is the whole game.

# %%
class VAE(nn.Module):
    def __init__(self, latent_dim=LATENT_DIM):
        super().__init__()
        self.latent_dim = latent_dim
        # Encoder body
        self.enc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(784, 256), nn.ReLU(),
            nn.Linear(256, 64), nn.ReLU(),
        )
        # Two heads: mean and log-variance
        self.fc_mu = nn.Linear(64, latent_dim)
        self.fc_logvar = nn.Linear(64, latent_dim)
        # Decoder
        self.dec = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.ReLU(),
            nn.Linear(64, 256), nn.ReLU(),
            nn.Linear(256, 784), nn.Sigmoid(),
        )

    def encode(self, x):
        h = self.enc(x)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        # z = mu + sigma * eps,  sigma = exp(0.5 * logvar)
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + std * eps

    def decode(self, z):
        return self.dec(z).view(-1, 1, 28, 28)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar


def vae_loss(recon, x, mu, logvar, beta=1.0):
    # Reconstruction: binary cross-entropy summed over pixels
    recon_loss = F.binary_cross_entropy(recon, x, reduction='sum') / x.size(0)
    # KL divergence between N(mu, sigma^2) and N(0, 1), closed form
    kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp()) / x.size(0)
    return recon_loss + beta * kl, recon_loss, kl


vae = VAE().to(device)
print(vae)

# %%
def train_vae(model, loader, epochs=10, lr=1e-3, beta=1.0):
    opt = optim.Adam(model.parameters(), lr=lr)
    for epoch in range(epochs):
        model.train()
        tot, rec, kld = 0.0, 0.0, 0.0
        for imgs, _ in loader:
            imgs = imgs.to(device)
            recon, mu, logvar = model(imgs)
            loss, r, k = vae_loss(recon, imgs, mu, logvar, beta=beta)
            opt.zero_grad(); loss.backward(); opt.step()
            tot += loss.item(); rec += r.item(); kld += k.item()
        n = len(loader)
        print(f"Epoch {epoch+1}/{epochs}  total: {tot/n:.2f}  "
              f"recon: {rec/n:.2f}  KL: {kld/n:.2f}")


print("Training VAE...")
print("-" * 50)
train_vae(vae, train_loader, epochs=10, beta=1.0)

# %% [markdown]
# ### Now sampling works
#
# Because the KL term organized the space, a random `z ~ N(0, 1)` decodes to a plausible
# (if blurry) clothing item. Blur is the VAE's known weakness — Module 13's GANs fix it.

# %%
vae.eval()
with torch.no_grad():
    z = torch.randn(16, LATENT_DIM, device=device)
    samples = vae.decode(z).cpu()

fig, axes = plt.subplots(2, 8, figsize=(14, 4))
for i, ax in enumerate(axes.flat):
    ax.imshow(samples[i].squeeze(), cmap='gray'); ax.axis('off')
plt.suptitle('VAE: brand-new images sampled from N(0, 1)', fontsize=13)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 5. Latent Interpolation — the heart of editing
#
# Here's the trick that hairstyle editing is built on. Encode two images to their latents
# `z_a` and `z_b`, then decode points *along the line between them*:
#
# ```
#   z(t) = (1 - t) · z_a + t · z_b,   t from 0 to 1
# ```
#
# A well-structured latent space gives a **smooth morph** from image A to image B. In
# Module 14 we do exactly this in StyleGAN's latent space — but blend only the *hair*
# layers, leaving the face identity untouched.

# %%
vae.eval()
# Grab two different items
img_a, _ = test_ds[1]
img_b, _ = test_ds[8]
with torch.no_grad():
    mu_a, _ = vae.encode(img_a.unsqueeze(0).to(device))
    mu_b, _ = vae.encode(img_b.unsqueeze(0).to(device))
    steps = torch.linspace(0, 1, 10, device=device)
    interp = torch.stack([(1 - t) * mu_a + t * mu_b for t in steps]).squeeze(1)
    morph = vae.decode(interp).cpu()

fig, axes = plt.subplots(1, 10, figsize=(16, 2))
for i in range(10):
    axes[i].imshow(morph[i].squeeze(), cmap='gray'); axes[i].axis('off')
    axes[i].set_title(f't={steps[i]:.1f}', fontsize=8)
plt.suptitle('Latent interpolation: smooth morph A -> B', fontsize=13)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6. Exercises
#
# ### Exercise 6.1 — Visualize the latent space in 2D
#
# Train a VAE with `latent_dim=2` so we can plot the whole latent space. Then:
# 1. Encode the test set, plot each point colored by its class label — see the clusters.
# 2. Walk a grid over the 2D latent plane and decode each point to build a "latent atlas".

# %%
# TODO: train a 2D VAE, scatter-plot encoded test points colored by class,
#       and decode a grid over the latent plane.
# Hint: reuse VAE(latent_dim=2) and train_vae. For the grid, use np.linspace
#       over roughly [-3, 3] in both dims (since the prior is N(0,1)).

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: 2D latent space

vae2 = VAE(latent_dim=2).to(device)
print("Training 2D VAE...")
train_vae(vae2, train_loader, epochs=10, beta=1.0)

# 1. Scatter encoded test points
vae2.eval()
zs, ys = [], []
with torch.no_grad():
    for imgs, labels in test_loader:
        mu, _ = vae2.encode(imgs.to(device))
        zs.append(mu.cpu().numpy()); ys.append(labels.numpy())
zs = np.concatenate(zs); ys = np.concatenate(ys)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
sc = axes[0].scatter(zs[:, 0], zs[:, 1], c=ys, cmap='tab10', s=4, alpha=0.5)
axes[0].set_title('Test set encoded into 2D latent space')
axes[0].set_xlabel('z[0]'); axes[0].set_ylabel('z[1]')
cbar = fig.colorbar(sc, ax=axes[0], ticks=range(10))
cbar.ax.set_yticklabels(class_names)

# 2. Decode a grid over the latent plane
n = 15
grid_x = np.linspace(-3, 3, n)
grid_y = np.linspace(-3, 3, n)
canvas = np.zeros((28 * n, 28 * n))
with torch.no_grad():
    for i, yi in enumerate(grid_y):
        for j, xi in enumerate(grid_x):
            z = torch.tensor([[xi, yi]], dtype=torch.float32, device=device)
            img = vae2.decode(z).cpu().squeeze().numpy()
            canvas[i*28:(i+1)*28, j*28:(j+1)*28] = img
axes[1].imshow(canvas, cmap='gray')
axes[1].set_title('Latent atlas: decode a grid over the 2D plane')
axes[1].axis('off')
plt.tight_layout()
plt.show()
print("Nearby points decode to similar images — that smoothness is what makes")
print("latent-space editing possible.")

# %% [markdown]
# ### Exercise 6.2 — The effect of β (beta-VAE)
#
# The `beta` weight on the KL term trades reconstruction sharpness against latent
# organization. Train two VAEs, `beta=0.5` and `beta=4.0`, and compare:
# - Reconstruction quality (sharper vs blurrier)
# - Sample quality (random `z ~ N(0,1)` decoded)
#
# Which makes sharper reconstructions? Which makes better random samples? Why the tradeoff?

# %%
# TODO: train VAE with beta=0.5 and beta=4.0, compare reconstructions and samples

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: beta comparison

def recon_and_sample(beta, epochs=8):
    m = VAE().to(device)
    train_vae(m, train_loader, epochs=epochs, beta=beta)
    m.eval()
    imgs, _ = next(iter(test_loader))
    with torch.no_grad():
        recon, _, _ = m(imgs.to(device))
        z = torch.randn(8, LATENT_DIM, device=device)
        samp = m.decode(z).cpu()
    return imgs.cpu(), recon.cpu(), samp


print("=== beta = 0.5 (favors reconstruction) ===")
imgs_lo, rec_lo, samp_lo = recon_and_sample(0.5)
print("=== beta = 4.0 (favors latent organization) ===")
imgs_hi, rec_hi, samp_hi = recon_and_sample(4.0)

fig, axes = plt.subplots(4, 8, figsize=(14, 7))
for i in range(8):
    axes[0, i].imshow(rec_lo[i].squeeze(), cmap='gray'); axes[0, i].axis('off')
    axes[1, i].imshow(samp_lo[i].squeeze(), cmap='gray'); axes[1, i].axis('off')
    axes[2, i].imshow(rec_hi[i].squeeze(), cmap='gray'); axes[2, i].axis('off')
    axes[3, i].imshow(samp_hi[i].squeeze(), cmap='gray'); axes[3, i].axis('off')
axes[0, 0].set_title('beta=0.5 recon', loc='left', fontsize=9)
axes[1, 0].set_title('beta=0.5 sample', loc='left', fontsize=9)
axes[2, 0].set_title('beta=4.0 recon', loc='left', fontsize=9)
axes[3, 0].set_title('beta=4.0 sample', loc='left', fontsize=9)
plt.suptitle('Low beta = sharper recon; high beta = better-organized space', fontsize=13)
plt.tight_layout()
plt.show()
print("Low beta: crisp reconstructions but a messier latent space (worse samples).")
print("High beta: smoother/disentangled latent (better samples) but blurrier recon.")

# %% [markdown]
# ## Scaling to faces
#
# Everything here works on faces — swap the dataset for CelebA (downscaled to e.g. 64x64)
# and make the encoder/decoder **convolutional** (Conv2d / ConvTranspose2d instead of
# Linear) so they handle RGB images efficiently. The latent interpolation you just saw is
# exactly how face-morphing demos work. But VAE faces come out blurry — to get *sharp*
# faces we need adversarial training, which is Module 13.

# %% [markdown]
# ## Key Takeaways
#
# - A **latent space** is a compact code capturing an image's essence; all generation and
#   editing happens there, not in raw pixels.
#
# - A **plain autoencoder** reconstructs well but its latent space has gaps — it can't
#   generate from random codes.
#
# - A **VAE** outputs a *distribution* (`μ`, `logσ²`), samples via the **reparameterization
#   trick** (`z = μ + σ·ε`), and uses a **KL loss** to pack codes into `N(0, 1)` — making
#   the space samplable.
#
# - **Latent interpolation** morphs smoothly between two images. Blending *selected* latent
#   dimensions is the foundation of targeted edits like hairstyle swapping (Module 14).
#
# - VAEs are blurry; **GANs** (next) trade the easy training for much sharper images.
#
# ---
# **Next:** [GANs from Scratch →](../13_gans/01_gans.ipynb) — adversarial training for
# sharp, realistic image generation, and the road to StyleGAN.
