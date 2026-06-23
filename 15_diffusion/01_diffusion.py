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
# # Module 15.1 — Diffusion Models
#
# **Purpose:** Diffusion is the paradigm behind Stable Diffusion, DALL·E, and Midjourney —
# and it is "Route B" of the **hairstyle-swap capstone** (Module 16): mask the hair,
# regenerate just that region with **inpainting**. You build a DDPM from scratch twice —
# first on 2D points where you can *watch every trajectory*, then on MNIST images — and
# learn the two knobs every Stable Diffusion user turns: **guidance scale** and
# **step count (DDIM)**.
#
# **Prerequisites:** Modules 12–13 (latent spaces; the U-Net from Module 11 reappears here).
#
# GANs are sharp but finicky (Module 13). Diffusion models train with a *stable, simple*
# regression loss. The core idea is almost suspiciously simple:
# 1. **Forward process:** gradually add Gaussian noise to an image over `T` steps until it's
#    pure noise. This is fixed math — no learning.
# 2. **Reverse process:** train a network to *predict the noise* that was added at each step.
#    To generate, start from pure noise and repeatedly subtract the predicted noise.
#
# **What you'll learn:**
# - The forward noising schedule and the closed-form "noise at step t" shortcut
# - A complete DDPM on **2D point clouds** — watch individual points denoise (runs in seconds)
# - Build a tiny image **DDPM** from scratch (a small U-Net noise predictor) on MNIST
# - **Classifier-free guidance** — what `guidance_scale` actually does
# - How **latent diffusion** (Stable Diffusion) reuses your Module 11/12 building blocks
# - Use a **pretrained Stable Diffusion inpainting** pipeline — the hair-swap mechanism
#
# > Everything here runs **locally** on CPU/MPS except §9 (Stable Diffusion itself), which
# > is Colab/GPU and guarded to skip elsewhere. MNIST training (§4) is the slowest local
# > part: ~2–3 min on MPS; set `epochs=1` on plain CPU.

# %%
import torch
import torch.nn as nn
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
# ## 1. The Forward Process (adding noise)
#
# We define a **variance schedule** `β_1 ... β_T` (small, increasing). At each step we add a
# little noise. The magic: there's a **closed form** for jumping straight to step `t` without
# looping. With `α_t = 1 - β_t` and `ᾱ_t = ∏ α_s`:
#
# ```
#   x_t = sqrt(ᾱ_t) · x_0 + sqrt(1 - ᾱ_t) · ε,    ε ~ N(0, 1)
# ```
#
# So a noisy image at any `t` is just a weighted mix of the clean image and pure noise. This
# is what makes training cheap: pick a random `t`, make `x_t` in one shot, ask the network to
# recover `ε`.

# %%
T = 200  # number of diffusion steps (small, for laptop speed)

# Linear beta schedule
betas = torch.linspace(1e-4, 0.02, T)
alphas = 1.0 - betas
alpha_bars = torch.cumprod(alphas, dim=0)          # ᾱ_t
sqrt_ab = torch.sqrt(alpha_bars)
sqrt_1m_ab = torch.sqrt(1 - alpha_bars)


def q_sample(x0, t, noise):
    """Forward: produce x_t from x_0 in one step (closed form)."""
    # gather schedule values for each t in the batch, reshape to broadcast over (C,H,W)
    # (move the schedule to t's device first so MPS/CUDA index tensors work)
    a = sqrt_ab.to(x0.device)[t].view(-1, 1, 1, 1)
    b = sqrt_1m_ab.to(x0.device)[t].view(-1, 1, 1, 1)
    return a * x0 + b * noise


# Visualize the forward process on one image
transform = transforms.Compose([transforms.ToTensor(),
                                 transforms.Normalize((0.5,), (0.5,))])  # [-1,1]
mnist = torchvision.datasets.MNIST(root='./data', train=True, download=True, transform=transform)
x0 = mnist[7][0].unsqueeze(0)  # (1,1,28,28)

fig, axes = plt.subplots(1, 6, figsize=(13, 2.5))
for i, t in enumerate([0, 20, 50, 100, 150, 199]):
    noise = torch.randn_like(x0)
    xt = q_sample(x0, torch.tensor([t]), noise)
    axes[i].imshow(xt.squeeze().clamp(-1, 1) * 0.5 + 0.5, cmap='gray')
    axes[i].set_title(f't={t}'); axes[i].axis('off')
plt.suptitle('Forward process: clean image -> pure noise', fontsize=13)
plt.tight_layout(); plt.show()

# %% [markdown]
# ### The schedule, as math (not just pictures)
#
# `ᾱ_t` is *the* quantity to watch: it's the fraction of original signal surviving at step
# `t`. Its log-SNR, `log(ᾱ_t / (1−ᾱ_t))`, tells you what the model is asked to do at each
# step: high SNR (early t) = polish fine details; low SNR (late t) = invent coarse
# structure. Different schedules spend the model's capacity differently — compare linear
# with the **cosine** schedule (you'll implement it in Exercise 10.1):

# %%
def cosine_ab(T, s=0.008):
    steps = torch.arange(T + 1)
    f = torch.cos(((steps / T + s) / (1 + s)) * np.pi / 2) ** 2
    return (f / f[0])[1:].clamp(1e-5, 0.9999)


ab_lin, ab_cos = alpha_bars, cosine_ab(T)
fig, axes = plt.subplots(1, 2, figsize=(11, 3.5))
axes[0].plot(ab_lin, label='linear'); axes[0].plot(ab_cos, label='cosine')
axes[0].set_xlabel('t'); axes[0].set_ylabel(r'$\bar{\alpha}_t$  (signal fraction)')
axes[0].legend(); axes[0].grid(alpha=0.3); axes[0].set_title('Signal surviving at step t')
for ab, lab in [(ab_lin, 'linear'), (ab_cos, 'cosine')]:
    axes[1].plot(torch.log(ab / (1 - ab)), label=lab)
axes[1].set_xlabel('t'); axes[1].set_ylabel('log SNR')
axes[1].legend(); axes[1].grid(alpha=0.3); axes[1].set_title('Log signal-to-noise ratio')
plt.suptitle('Linear destroys signal early; cosine spreads the work more evenly', fontsize=12)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 2. Diffusion you can watch: 2D point clouds
#
# Images hide what diffusion actually does — you can't see a pixel's "path" from noise to
# data. **2D points can be watched.** Same equations, same training loop, but the "image"
# is a single (x, y) point and the dataset is the two-moons shape. The whole thing trains
# in ~10–20 s on CPU.
#
# This is the single best mental model to carry into Stable Diffusion: every generated
# image is one of these trajectories, in ~16k dimensions instead of 2.

# %%
from sklearn.datasets import make_moons

pts_np, moon_labels = make_moons(n_samples=2000, noise=0.05, random_state=42)
pts = torch.tensor((pts_np - pts_np.mean(0)) / pts_np.std(0), dtype=torch.float32)
labels_t = torch.tensor(moon_labels, dtype=torch.long)


def q_sample_pts(x0, t, noise):
    """Forward process for 2D points: same closed form, (B,2) shapes."""
    a = sqrt_ab.to(x0.device)[t].view(-1, 1)
    b = sqrt_1m_ab.to(x0.device)[t].view(-1, 1)
    return a * x0 + b * noise


# Watch the forward process scatter the moons into a Gaussian blob
fig, axes = plt.subplots(1, 5, figsize=(15, 3))
for ax, t in zip(axes, [0, 20, 50, 100, 199]):
    noisy = q_sample_pts(pts, torch.full((len(pts),), t), torch.randn_like(pts))
    ax.scatter(noisy[:, 0], noisy[:, 1], s=2, alpha=0.4, c='steelblue')
    ax.set_title(f't={t}'); ax.set_xlim(-3.5, 3.5); ax.set_ylim(-3.5, 3.5)
plt.suptitle('Forward process on 2D points: two moons -> Gaussian blob', fontsize=13)
plt.tight_layout(); plt.show()

# %% [markdown]
# ### A tiny noise predictor for points
#
# The "U-Net" for a 2D point is just an MLP: input = the noisy point plus a **sinusoidal
# time embedding** (so the net knows the noise level — same trick, fancier, in the image
# U-Net below). Output = the predicted 2D noise.

# %%
def time_features(t, dim=16):
    """Sinusoidal features of the integer timestep t: (B,) -> (B, dim)."""
    half = dim // 2
    freqs = torch.exp(-np.log(1000) * torch.arange(half, device=t.device) / (half - 1))
    args = t[:, None].float() * freqs[None]
    return torch.cat([torch.sin(args), torch.cos(args)], dim=-1)


class PointDenoiser(nn.Module):
    def __init__(self, tdim=16, hidden=128):
        super().__init__()
        self.tdim = tdim
        self.net = nn.Sequential(
            nn.Linear(2 + tdim, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, 2),
        )

    def forward(self, x, t):
        return self.net(torch.cat([x, time_features(t, self.tdim)], dim=-1))


pt_net = PointDenoiser().to(device)
pts_dev = pts.to(device)
opt = torch.optim.Adam(pt_net.parameters(), lr=1e-3)

losses_pt = []
for step in range(3000):
    idx = torch.randint(0, len(pts_dev), (256,), device=device)
    x0_b = pts_dev[idx]
    t = torch.randint(0, T, (256,), device=device)
    noise = torch.randn_like(x0_b)
    xt = q_sample_pts(x0_b, t, noise)
    loss = F.mse_loss(pt_net(xt, t), noise)
    opt.zero_grad(); loss.backward(); opt.step()
    losses_pt.append(loss.item())

plt.figure(figsize=(8, 3))
plt.plot(losses_pt, alpha=0.6)
plt.xlabel('step'); plt.ylabel('noise MSE'); plt.grid(alpha=0.3)
plt.title('2D DDPM training: a plain regression loss, quietly going down')
plt.tight_layout(); plt.show()

# %% [markdown]
# ### Reverse process — and the trajectories
#
# Now sample: start 1000 points at pure noise, run the DDPM update backwards, and — the
# payoff images can't give you — **plot the path of individual points** as they travel
# from the Gaussian blob onto the moons.

# %%
@torch.no_grad()
def sample_points(net, n=1000, track=20):
    """Reverse-sample n points. Returns (final points, snapshots, tracked trajectories)."""
    x = torch.randn(n, 2, device=device)
    snaps, traj = {}, [x[:track].cpu().clone()]
    for t in reversed(range(T)):
        tb = torch.full((n,), t, device=device, dtype=torch.long)
        eps = net(x, tb)
        a = alphas[t].to(device); ab = alpha_bars[t].to(device); beta = betas[t].to(device)
        mean = (x - (beta / torch.sqrt(1 - ab)) * eps) / torch.sqrt(a)
        x = mean + (torch.sqrt(beta) * torch.randn_like(x) if t > 0 else 0)
        if t in (150, 100, 50, 20, 0):
            snaps[t] = x.cpu().clone()
        traj.append(x[:track].cpu().clone())
    return x.cpu(), snaps, torch.stack(traj)   # traj: (T+1, track, 2)


final, snaps, traj = sample_points(pt_net)

fig, axes = plt.subplots(1, 6, figsize=(17, 3))
axes[0].scatter(torch.randn(1000), torch.randn(1000), s=2, alpha=0.4, c='gray')
axes[0].set_title('start: pure noise')
for ax, t in zip(axes[1:], [150, 100, 50, 20, 0]):
    ax.scatter(snaps[t][:, 0], snaps[t][:, 1], s=2, alpha=0.4, c='steelblue')
    ax.set_title(f'after denoising to t={t}')
for ax in axes:
    ax.set_xlim(-3.5, 3.5); ax.set_ylim(-3.5, 3.5)
plt.suptitle('Reverse process: noise condenses onto the data manifold', fontsize=13)
plt.tight_layout(); plt.show()

# Trajectories of 20 individual points
plt.figure(figsize=(7, 6))
plt.scatter(pts[:, 0], pts[:, 1], s=3, alpha=0.15, c='gray', label='data')
for i in range(traj.shape[1]):
    path = traj[:, i, :]
    plt.plot(path[:, 0], path[:, 1], lw=0.8, alpha=0.7)
    plt.scatter(path[-1, 0], path[-1, 1], s=25, zorder=3)
plt.title('20 individual denoising trajectories: noise -> moons\n'
          '(every Stable Diffusion image is one of these, in ~16k dimensions)')
plt.legend(); plt.grid(alpha=0.2)
plt.tight_layout(); plt.show()
print("Early steps (outer ends of the paths) make big coarse moves; final steps barely nudge.")
print("That asymmetry is the schedule curve from §1 in action.")

# %% [markdown]
# ## 3. The Noise-Predictor Network (images)
#
# Back to images. The reverse process needs a network `ε_θ(x_t, t)` that predicts the noise
# in `x_t`. The standard choice is a **U-Net** (the same architecture from Module 11!) with
# the timestep `t` injected as an embedding so the network knows "how noisy" the input is —
# exactly the `time_features` trick from §2, with conv blocks instead of an MLP.

# %%
class TimeEmbedding(nn.Module):
    """Sinusoidal embedding of the integer timestep, then a small MLP."""
    def __init__(self, dim):
        super().__init__()
        self.dim = dim
        self.mlp = nn.Sequential(nn.Linear(dim, dim), nn.SiLU(), nn.Linear(dim, dim))

    def forward(self, t):
        half = self.dim // 2
        freqs = torch.exp(-np.log(10000) * torch.arange(half, device=t.device) / (half - 1))
        args = t[:, None].float() * freqs[None]
        emb = torch.cat([torch.sin(args), torch.cos(args)], dim=-1)
        return self.mlp(emb)


class Block(nn.Module):
    """Conv block that adds a projected time embedding."""
    def __init__(self, in_ch, out_ch, tdim):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, padding=1)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1)
        self.time = nn.Linear(tdim, out_ch)
        self.norm1 = nn.GroupNorm(8, out_ch)
        self.norm2 = nn.GroupNorm(8, out_ch)
        self.act = nn.SiLU()

    def forward(self, x, t):
        h = self.act(self.norm1(self.conv1(x)))
        h = h + self.time(t)[:, :, None, None]   # inject time
        h = self.act(self.norm2(self.conv2(h)))
        return h


class TinyUNet(nn.Module):
    """Small time-conditioned U-Net noise predictor for 28x28 images."""
    def __init__(self, tdim=128, base=32):
        super().__init__()
        self.time_emb = TimeEmbedding(tdim)
        self.down1 = Block(1, base, tdim)
        self.down2 = Block(base, base * 2, tdim)
        self.pool = nn.MaxPool2d(2)
        self.mid = Block(base * 2, base * 2, tdim)
        self.up2 = nn.ConvTranspose2d(base * 2, base * 2, 2, 2)
        self.dec2 = Block(base * 4, base, tdim)
        self.up1 = nn.ConvTranspose2d(base, base, 2, 2)
        self.dec1 = Block(base * 2, base, tdim)
        self.out = nn.Conv2d(base, 1, 1)

    def forward(self, x, t):
        temb = self.time_emb(t)
        s1 = self.down1(x, temb)                 # (B, base, 28, 28)
        s2 = self.down2(self.pool(s1), temb)     # (B, 2base, 14, 14)
        m = self.mid(self.pool(s2), temb)        # (B, 2base, 7, 7)
        d2 = self.up2(m)                         # (B, 2base, 14, 14)
        d2 = self.dec2(torch.cat([d2, s2], 1), temb)  # (B, base, 14, 14)
        d1 = self.up1(d2)                        # (B, base, 28, 28)
        d1 = self.dec1(torch.cat([d1, s1], 1), temb)
        return self.out(d1)                      # predicted noise (B,1,28,28)


net = TinyUNet().to(device)
print(f"Noise predictor params: {sum(p.numel() for p in net.parameters()):,}")
# sanity check
xt = torch.randn(4, 1, 28, 28, device=device)
tt = torch.randint(0, T, (4,), device=device)
print(f"forward: x_t {tuple(xt.shape)}, t {tuple(tt.shape)} -> eps {tuple(net(xt, tt).shape)}")

# %% [markdown]
# ## 4. Training
#
# The whole loss is one line of intuition: **predict the noise you added**.
#
# ```
#   pick random t and random noise ε
#   x_t = q_sample(x_0, t, ε)
#   loss = MSE( ε_θ(x_t, t),  ε )
# ```
#
# That's it — a stable regression. No adversary, no KL balancing. Identical to §2's point
# loop, just with conv shapes.
#
# > **Timing:** ~2–3 minutes on Apple Silicon (MPS), longer on plain CPU — set `epochs=1`
# > there; even one epoch produces recognizable digits. On Colab GPU it's <1 min.

# %%
loader = DataLoader(mnist, batch_size=128, shuffle=True)


def train_diffusion(net, loader, epochs=3, lr=2e-4):
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    for epoch in range(epochs):
        net.train()
        running, n = 0.0, 0
        for x0, _ in loader:
            x0 = x0.to(device)
            b = x0.size(0)
            t = torch.randint(0, T, (b,), device=device)
            noise = torch.randn_like(x0)
            xt = q_sample(x0, t, noise)
            pred = net(xt, t)
            loss = F.mse_loss(pred, noise)
            opt.zero_grad(); loss.backward(); opt.step()
            running += loss.item() * b; n += b
        print(f"Epoch {epoch+1}/{epochs}  noise-MSE: {running/n:.4f}")


print("Training tiny DDPM on MNIST (this is the slow part on CPU/MPS)...")
print("-" * 55)
train_diffusion(net, loader, epochs=3)

# %% [markdown]
# ## 5. Sampling (the reverse process)
#
# To generate: start from pure noise `x_T ~ N(0,1)` and step backward `t = T-1 ... 0`. At
# each step, use the predicted noise to estimate a slightly-less-noisy image (DDPM update):
#
# ```
#   x_{t-1} = 1/sqrt(α_t) · ( x_t - (β_t / sqrt(1-ᾱ_t)) · ε_θ(x_t, t) ) + sqrt(β_t) · z
# ```
#
# (the last term `z` is fresh noise, dropped at `t=0`).

# %%
@torch.no_grad()
def sample(net, n=16):
    net.eval()
    x = torch.randn(n, 1, 28, 28, device=device)  # x_T
    for t in reversed(range(T)):
        tb = torch.full((n,), t, device=device, dtype=torch.long)
        eps = net(x, tb)
        a = alphas[t].to(device)
        ab = alpha_bars[t].to(device)
        beta = betas[t].to(device)
        coef = beta / torch.sqrt(1 - ab)
        mean = (x - coef * eps) / torch.sqrt(a)
        if t > 0:
            x = mean + torch.sqrt(beta) * torch.randn_like(x)
        else:
            x = mean
    return x.clamp(-1, 1)


samples = sample(net, n=16).cpu()
fig, axes = plt.subplots(2, 8, figsize=(14, 4))
for i, ax in enumerate(axes.flat):
    ax.imshow(samples[i].squeeze() * 0.5 + 0.5, cmap='gray'); ax.axis('off')
plt.suptitle('DDPM samples: generated from pure noise by reverse denoising', fontsize=13)
plt.tight_layout(); plt.show()
print("Recognizable digits from noise — with a model that only ever learned to denoise.")

# %% [markdown]
# ## 6. Inpainting intuition (why diffusion is perfect for hair swap)
#
# Diffusion shines at **inpainting**: regenerate only a masked region while keeping the rest.
# The trick during sampling — at every reverse step, *force* the known (unmasked) pixels back
# to the real image's (noised) values, and only let the model freely denoise inside the mask:
#
# ```
#   x_{t-1} = mask * (model's denoised x_{t-1}) + (1 - mask) * (noised real image at t-1)
# ```
#
# So the model "hallucinates" content that's consistent with the surrounding context — exactly
# what we want for hair: keep the face, regenerate the hair region. Below is a toy demo on
# MNIST (mask out the bottom half and let the model fill it in).

# %%
@torch.no_grad()
def inpaint(net, x0, mask, n_show=8):
    """mask: 1 where we KEEP the original, 0 where the model should fill in."""
    net.eval()
    x0 = x0.to(device); mask = mask.to(device)
    x = torch.randn_like(x0)
    for t in reversed(range(T)):
        tb = torch.full((x0.size(0),), t, device=device, dtype=torch.long)
        eps = net(x, tb)
        a, ab, beta = alphas[t].to(device), alpha_bars[t].to(device), betas[t].to(device)
        mean = (x - (beta / torch.sqrt(1 - ab)) * eps) / torch.sqrt(a)
        x = mean + (torch.sqrt(beta) * torch.randn_like(x) if t > 0 else 0)
        # Re-impose the known region (noised to the right level)
        if t > 0:
            known = q_sample(x0, torch.full((x0.size(0),), t - 1, device=device), torch.randn_like(x0))
            x = mask * known + (1 - mask) * x
    return x.clamp(-1, 1)


# Keep top half, regenerate bottom half
batch = torch.stack([mnist[i][0] for i in range(8)])  # (8,1,28,28)
mask = torch.ones_like(batch); mask[:, :, 14:, :] = 0  # 0 = fill bottom half
filled = inpaint(net, batch, mask).cpu()

fig, axes = plt.subplots(3, 8, figsize=(14, 5.5))
for i in range(8):
    axes[0, i].imshow(batch[i].squeeze() * 0.5 + 0.5, cmap='gray'); axes[0, i].axis('off')
    masked_vis = (batch[i] * mask[i]).squeeze() * 0.5 + 0.5
    axes[1, i].imshow(masked_vis, cmap='gray'); axes[1, i].axis('off')
    axes[2, i].imshow(filled[i].squeeze() * 0.5 + 0.5, cmap='gray'); axes[2, i].axis('off')
axes[0, 0].set_title('original', loc='left', fontsize=9)
axes[1, 0].set_title('masked input', loc='left', fontsize=9)
axes[2, 0].set_title('inpainted', loc='left', fontsize=9)
plt.suptitle('Diffusion inpainting (toy): fill the masked bottom half', fontsize=13)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 7. Classifier-free guidance — what `guidance_scale` actually does
#
# Everything above is **unconditional** — the model draws *some* digit, *some* point. Real
# use is conditional: "a person with short curly hair". How does a prompt steer sampling?
#
# **Classifier-free guidance (CFG)**, the trick used by Stable Diffusion:
# 1. Train ONE model that accepts a condition `c` (here: which moon, 0 or 1), but **drop
#    the condition ~10% of the time** during training, replacing it with a special null
#    token. The model learns conditional *and* unconditional denoising simultaneously.
# 2. At sampling time, run both and extrapolate **past** the conditional prediction:
#
# ```
#   ε̂ = (1 + w) · ε(x_t, c)  −  w · ε(x_t, ∅)        # w = guidance strength
# ```
#
# `w = 0` is plain conditional sampling; bigger `w` pushes samples harder toward "what
# makes this look like `c`" — at the cost of diversity, and eventually quality. That's the
# `guidance_scale` slider (SD default ≈ 7.5). We can see all of this on the moons in
# seconds.

# %%
NULL_CLASS = 2   # embedding index for "no condition"


class CondPointDenoiser(nn.Module):
    def __init__(self, tdim=16, cdim=16, hidden=128):
        super().__init__()
        self.tdim = tdim
        self.cond = nn.Embedding(3, cdim)   # class 0, class 1, null
        self.net = nn.Sequential(
            nn.Linear(2 + tdim + cdim, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, 2),
        )

    def forward(self, x, t, c):
        return self.net(torch.cat(
            [x, time_features(t, self.tdim), self.cond(c)], dim=-1))


cond_net = CondPointDenoiser().to(device)
labels_dev = labels_t.to(device)
opt = torch.optim.Adam(cond_net.parameters(), lr=1e-3)

for step in range(3000):
    idx = torch.randint(0, len(pts_dev), (256,), device=device)
    x0_b, c_b = pts_dev[idx], labels_dev[idx].clone()
    # CFG trick: drop the condition 10% of the time -> model also learns unconditional
    drop = torch.rand(256, device=device) < 0.10
    c_b[drop] = NULL_CLASS
    t = torch.randint(0, T, (256,), device=device)
    noise = torch.randn_like(x0_b)
    loss = F.mse_loss(cond_net(q_sample_pts(x0_b, t, noise), t, c_b), noise)
    opt.zero_grad(); loss.backward(); opt.step()
print(f"Conditional model trained (final loss {loss.item():.4f})")


@torch.no_grad()
def sample_guided(net, target_class, w, n=600):
    """CFG sampling: eps = (1+w)*eps_cond - w*eps_uncond."""
    x = torch.randn(n, 2, device=device)
    c = torch.full((n,), target_class, device=device, dtype=torch.long)
    c_null = torch.full((n,), NULL_CLASS, device=device, dtype=torch.long)
    for t in reversed(range(T)):
        tb = torch.full((n,), t, device=device, dtype=torch.long)
        eps = (1 + w) * net(x, tb, c) - w * net(x, tb, c_null)
        a = alphas[t].to(device); ab = alpha_bars[t].to(device); beta = betas[t].to(device)
        mean = (x - (beta / torch.sqrt(1 - ab)) * eps) / torch.sqrt(a)
        x = mean + (torch.sqrt(beta) * torch.randn_like(x) if t > 0 else 0)
    return x.cpu()


fig, axes = plt.subplots(2, 4, figsize=(15, 7))
for row, cls in enumerate([0, 1]):
    for col, w in enumerate([0.0, 1.0, 3.0, 8.0]):
        out = sample_guided(cond_net, cls, w)
        ax = axes[row, col]
        ax.scatter(pts[:, 0], pts[:, 1], s=2, alpha=0.08, c='gray')
        ax.scatter(out[:, 0], out[:, 1], s=3, alpha=0.5,
                   c=('crimson' if cls == 0 else 'royalblue'))
        ax.set_title(f'class {cls}, w={w}')
        ax.set_xlim(-2.8, 2.8); ax.set_ylim(-2.8, 2.8)
plt.suptitle('Classifier-free guidance: w=0 leaks onto both moons; w=3 selects cleanly;\n'
             'w=8 over-concentrates (the 2D analogue of "fried" over-guided images)',
             fontsize=12)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 8. From pixels to latents: how Stable Diffusion scales
#
# Our MNIST model denoises 28×28 pixels. Doing that at 512×512×3 is brutally expensive —
# so **latent diffusion** (= Stable Diffusion) runs the whole noise/denoise game in the
# compressed latent space of an autoencoder. Every component is a scaled-up version of
# something you've already built:
#
# ```
#   "short curly hair" ──[ CLIP text encoder ]──► text embedding
#                                                      │ (cross-attention)
#                                                      ▼
#   noise (64x64x4) ──► [ U-Net denoiser, run T times, CFG w/ guidance_scale ] ──► clean latent
#                                                      │
#   pixel image (512x512x3) ◄──[ VAE decoder ]─────────┘
#                       (and VAE encoder for img2img / inpainting)
# ```
#
# | Stable Diffusion component | Where you built the small version |
# |---|---|
# | VAE encoder/decoder (pixels ↔ latents) | Module 12 (autoencoders & VAE) |
# | U-Net noise predictor with time embedding | Module 11 (U-Net) + §3 here |
# | DDPM forward/reverse process | §1–§5 here |
# | Classifier-free guidance / `guidance_scale` | §7 here |
# | Inpainting by mask re-imposition | §6 here |
# | Fewer-step sampling (`num_inference_steps`) | DDIM — Exercise 10.2 |
#
# The only genuinely new part is the **text conditioning** (CLIP embeddings injected via
# cross-attention) — conceptually the same role as §7's class embedding, just richer.

# %% [markdown]
# ## 9. Pretrained Stable Diffusion Inpainting (Colab GPU)
#
# > ⚠️ **GPU recommended.** Stable Diffusion is far too slow on CPU/MPS for interactive use.
# > Run this section on **Colab (GPU runtime)**. It's guarded to skip otherwise.
#
# The real swap uses a pretrained SD inpainting model via HuggingFace `diffusers`. Setup:
#
# ```python
# !pip install diffusers transformers accelerate safetensors
# ```
#
# The pipeline takes an image, a **mask** (white = regenerate), and a **text prompt**
# describing the desired content. For hair: mask = the hair region (from Module 11's face
# parsing), prompt = the hairstyle you want (or, with **ControlNet**, condition on a
# reference image instead of text for tighter control). On a GPU, the cell below downloads
# the Module 11 sample portrait, masks the top-of-head region, and actually generates.

# %%
ON_GPU = torch.cuda.is_available()
if ON_GPU:
    try:
        import io
        import urllib.request
        from diffusers import StableDiffusionInpaintPipeline
        from PIL import Image

        def load_image_from_url(url, size=512):
            """Fetch an image and return it as a PIL RGB image (resized)."""
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                img = Image.open(io.BytesIO(resp.read())).convert("RGB")
            return img.resize((size, size))

        # Same public-domain Wikimedia portrait as Module 11 (Marie Curie, 1920)
        PORTRAIT_URL = (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "7/7e/Marie_Curie_c1920.jpg/500px-Marie_Curie_c1920.jpg"
        )
        image = load_image_from_url(PORTRAIT_URL)

        # Crude top-of-head ellipse mask (white = regenerate). The real pipeline uses
        # the Module 11 hair parser instead — this is just to see the mechanism work.
        yy, xx = np.mgrid[0:512, 0:512]
        ellipse = (((xx - 256) / 190) ** 2 + ((yy - 150) / 150) ** 2) <= 1.0
        mask = Image.fromarray((ellipse * 255).astype(np.uint8))

        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting", torch_dtype=torch.float16
        ).to("cuda")

        result = pipe(
            prompt="a person with short curly red hair, photorealistic portrait",
            image=image, mask_image=mask,
            num_inference_steps=30, guidance_scale=7.5,
        ).images[0]

        fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
        for ax, im, title in [(axes[0], image, 'input'),
                              (axes[1], mask, 'mask (white = regenerate)'),
                              (axes[2], result, 'inpainted result')]:
            ax.imshow(im, cmap='gray' if title.startswith('mask') else None)
            ax.set_title(title); ax.axis('off')
        plt.suptitle('Stable Diffusion inpainting: §6\'s trick at 512px with a text prompt',
                     fontsize=12)
        plt.tight_layout(); plt.show()
        print("Try different prompts and guidance_scale values (1, 7.5, 15) — §7 predicts")
        print("what you'll see. Module 16 replaces the ellipse with a real hair mask.")
    except Exception as e:
        print(f"Could not run diffusers pipeline: {e}")
        print("Run `pip install diffusers transformers accelerate safetensors` on Colab.")
else:
    print("[skipped] Stable Diffusion inpainting — GPU only.")
    print("Mechanism is identical to the toy inpaint() above, at 512x512 in VAE-latent")
    print("space, with a text/ControlNet condition and CFG (§7) instead of unconditional.")

# %% [markdown]
# ## 10. Exercises
#
# > All four run locally. 10.2 and 10.3 reuse the models you trained above.
#
# ### Exercise 10.1 — The schedule matters
#
# Re-run the forward-process visualization with a **cosine** schedule instead of linear
# (it adds noise more gently early on and is widely used in practice). Implement
# `alpha_bars` from the cosine formula and compare how fast the image degrades vs the
# linear schedule. (§1's curve plot showed the math; this shows it in pixels.)

# %%
# TODO: build a cosine alpha_bar schedule and visualize the forward process
# Hint (Nichol & Dhariwal): f(t) = cos((t/T + s)/(1+s) * pi/2)^2, alpha_bar = f(t)/f(0), s=0.008

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: cosine schedule
def cosine_alpha_bars(T, s=0.008):
    steps = torch.arange(T + 1)
    f = torch.cos(((steps / T + s) / (1 + s)) * np.pi / 2) ** 2
    ab = f / f[0]
    return ab[1:].clamp(1e-5, 0.9999)


ab_cos_ex = cosine_alpha_bars(T)
sqrt_ab_c = torch.sqrt(ab_cos_ex)
sqrt_1m_ab_c = torch.sqrt(1 - ab_cos_ex)

fig, axes = plt.subplots(2, 6, figsize=(13, 5))
for i, t in enumerate([0, 20, 50, 100, 150, 199]):
    noise = torch.randn_like(x0)
    # linear
    xt_lin = sqrt_ab[t] * x0 + sqrt_1m_ab[t] * noise
    axes[0, i].imshow(xt_lin.squeeze().clamp(-1, 1) * 0.5 + 0.5, cmap='gray')
    axes[0, i].set_title(f'linear t={t}', fontsize=8); axes[0, i].axis('off')
    # cosine
    xt_cos = sqrt_ab_c[t] * x0 + sqrt_1m_ab_c[t] * noise
    axes[1, i].imshow(xt_cos.squeeze().clamp(-1, 1) * 0.5 + 0.5, cmap='gray')
    axes[1, i].set_title(f'cosine t={t}', fontsize=8); axes[1, i].axis('off')
plt.suptitle('Linear (top) vs cosine (bottom) noise schedule', fontsize=13)
plt.tight_layout(); plt.show()
print("Cosine keeps the image recognizable longer, giving the model more useful")
print("signal in the mid-range timesteps — often improves sample quality.")

# %% [markdown]
# ### Exercise 10.2 — DDIM: why Stable Diffusion samples in 30 steps, not 1000
#
# Our DDPM sampler takes all `T=200` steps and injects fresh noise at each one. **DDIM**
# makes the reverse process *deterministic* and lets you skip steps: pick a subsequence of
# timesteps (say 20 of the 200) and update with
#
# ```
#   x̂_0  = (x_t − sqrt(1−ᾱ_t)·ε̂) / sqrt(ᾱ_t)           # model's guess of the clean data
#   x_(t') = sqrt(ᾱ_t')·x̂_0 + sqrt(1−ᾱ_t')·ε̂            # jump straight to the next kept step
# ```
#
# Implement DDIM for the **2D point model** (`pt_net`) with 20 steps and compare the result
# scatter against the 200-step DDPM sample. This is the `num_inference_steps` knob in
# `diffusers`.

# %%
# TODO: implement ddim_sample_points(net, n_steps=20) and compare with sample_points()
# Hint: timesteps = torch.linspace(T-1, 0, n_steps).long(); loop pairs (t, t_next),
#       compute x0_hat from eps, then re-noise deterministically to t_next.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: DDIM on the 2D toy
@torch.no_grad()
def ddim_sample_points(net, n=1000, n_steps=20):
    x = torch.randn(n, 2, device=device)
    timesteps = torch.linspace(T - 1, 0, n_steps).long()
    for i in range(len(timesteps)):
        t = timesteps[i].item()
        tb = torch.full((n,), t, device=device, dtype=torch.long)
        eps = net(x, tb)
        ab_t = alpha_bars[t].to(device)
        x0_hat = (x - torch.sqrt(1 - ab_t) * eps) / torch.sqrt(ab_t)
        if i + 1 < len(timesteps):
            ab_next = alpha_bars[timesteps[i + 1].item()].to(device)
            x = torch.sqrt(ab_next) * x0_hat + torch.sqrt(1 - ab_next) * eps  # deterministic
        else:
            x = x0_hat
    return x.cpu()


ddim_out = ddim_sample_points(pt_net, n_steps=20)
ddpm_out, _, _ = sample_points(pt_net)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, out, title in [(axes[0], ddpm_out, 'DDPM — 200 stochastic steps'),
                       (axes[1], ddim_out, 'DDIM — 20 deterministic steps')]:
    ax.scatter(pts[:, 0], pts[:, 1], s=2, alpha=0.08, c='gray')
    ax.scatter(out[:, 0], out[:, 1], s=3, alpha=0.5, c='seagreen')
    ax.set_title(title); ax.set_xlim(-2.8, 2.8); ax.set_ylim(-2.8, 2.8)
plt.suptitle('10x fewer steps, nearly the same distribution — the num_inference_steps knob',
             fontsize=12)
plt.tight_layout(); plt.show()
print("DDIM treats the model's x0-estimate as trustworthy and jumps between kept steps.")
print("Stable Diffusion's default of ~30 steps is exactly this idea (plus better solvers).")

# %% [markdown]
# ### Exercise 10.3 — What does the model think x₀ is?
#
# At every step, the noise prediction implies a guess of the **clean image**:
# `x̂_0 = (x_t − sqrt(1−ᾱ_t)·ε̂) / sqrt(ᾱ_t)` — the same quantity DDIM (10.2) jumps with.
# Using the trained MNIST model: take one digit, noise it to
# `t ∈ {25, 50, 100, 150, 199}`, and show the model's `x̂_0` at each. At which noise level
# does the model stop recovering *this* digit and start inventing *a* digit?

# %%
# TODO: visualize x0_hat at several t for one MNIST digit
# Hint: xt = q_sample(x0, t, noise); eps_hat = net(xt, t); apply the x0_hat formula.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: the implied x0_hat across noise levels
net.eval()
digit = mnist[7][0].unsqueeze(0).to(device)
t_show = [25, 50, 100, 150, 199]

fig, axes = plt.subplots(2, len(t_show), figsize=(13, 5))
with torch.no_grad():
    for i, t in enumerate(t_show):
        tb = torch.tensor([t], device=device)
        xt = q_sample(digit, tb, torch.randn_like(digit))
        eps_hat = net(xt, tb)
        ab_t = alpha_bars[t].to(device)
        x0_hat = (xt - torch.sqrt(1 - ab_t) * eps_hat) / torch.sqrt(ab_t)
        axes[0, i].imshow(xt[0].cpu().squeeze().clamp(-1, 1) * 0.5 + 0.5, cmap='gray')
        axes[0, i].set_title(f'x_t at t={t}', fontsize=9); axes[0, i].axis('off')
        axes[1, i].imshow(x0_hat[0].cpu().squeeze().clamp(-1, 1) * 0.5 + 0.5, cmap='gray')
        axes[1, i].set_title('implied x̂₀', fontsize=9); axes[1, i].axis('off')
plt.suptitle('Top: noisy input. Bottom: the model\'s one-shot guess of the clean image.',
             fontsize=12)
plt.tight_layout(); plt.show()
print("Low t: x̂₀ matches the true digit. High t: the input is ~pure noise, so x̂₀ is a")
print("blurry 'average digit' — predicting eps and predicting x0 are two views of one model.")

# %% [markdown]
# ### Exercise 10.4 — Inpaint an arbitrary mask
#
# Modify the toy `inpaint` demo to fill a **center square** hole (instead of the bottom
# half), then a **random** mask. Does the model produce coherent digits? Where does it
# struggle? This builds intuition for why a *clean, well-shaped* hair mask (Module 11)
# matters for the real swap.

# %%
# TODO: create a center-square mask and a random mask, run inpaint(), compare results

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: different masks
batch = torch.stack([mnist[i][0] for i in range(8)])

# Center square hole
mask_sq = torch.ones_like(batch); mask_sq[:, :, 9:19, 9:19] = 0
filled_sq = inpaint(net, batch, mask_sq).cpu()

# Random mask (per-pixel)
mask_rand = (torch.rand_like(batch) > 0.4).float()
filled_rand = inpaint(net, batch, mask_rand).cpu()

fig, axes = plt.subplots(2, 8, figsize=(14, 4))
for i in range(8):
    axes[0, i].imshow(filled_sq[i].squeeze() * 0.5 + 0.5, cmap='gray'); axes[0, i].axis('off')
    axes[1, i].imshow(filled_rand[i].squeeze() * 0.5 + 0.5, cmap='gray'); axes[1, i].axis('off')
axes[0, 0].set_title('center-square fill', loc='left', fontsize=9)
axes[1, 0].set_title('random-mask fill', loc='left', fontsize=9)
plt.suptitle('Inpainting different mask shapes', fontsize=13)
plt.tight_layout(); plt.show()
print("Contiguous, well-shaped masks inpaint more coherently than scattered ones —")
print("hence the mask cleanup (largest component, fill holes, feather) from Module 11.")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Forward process** | Fixed math noising data to nothing; `x_t = √ᾱ_t·x_0 + √(1−ᾱ_t)·ε` jumps to any step instantly |
# | **Noise schedules** | ᾱ_t / log-SNR curves decide where the model spends its capacity; cosine spreads work more evenly than linear |
# | **Reverse process** | A U-Net trained with plain MSE to predict the added noise; generation = iterative denoising from pure noise |
# | **Trajectories (2D toy)** | Each sample is a path from the Gaussian onto the data manifold — coarse moves early, fine moves late |
# | **Classifier-free guidance** | One model trained with condition-dropout; `ε̂ = (1+w)·ε_cond − w·ε_uncond` is the `guidance_scale` knob |
# | **DDIM** | Deterministic skipping via the implied x̂₀ — why 20–30 inference steps suffice |
# | **Inpainting** | Re-impose known pixels at every reverse step; the model fills the mask consistently — Route B of the hair swap |
# | **Latent diffusion** | Stable Diffusion = your VAE (M12) + your U-Net (M11) + this DDPM + CFG, run in latent space with text conditioning |
#
# ## Further reading
#
# - **DDPM — Denoising Diffusion Probabilistic Models** (Ho et al., the paper behind §1–§5):
#   https://arxiv.org/abs/2006.11239
# - **DDIM — Denoising Diffusion Implicit Models** (deterministic, few-step sampling):
#   https://arxiv.org/abs/2010.02502
# - **Classifier-Free Diffusion Guidance** (Ho & Salimans): https://arxiv.org/abs/2207.12598
# - **Latent Diffusion / Stable Diffusion** (Rombach et al.): https://arxiv.org/abs/2112.10752
# - **Lilian Weng — What are Diffusion Models?** (the best single derivation write-up):
#   https://lilianweng.github.io/posts/2021-07-11-diffusion-models/
# - **HuggingFace diffusers docs** (the library used in §9):
#   https://huggingface.co/docs/diffusers
#
# **Next:** [Module 16 — Capstone: Hairstyle Swap →](../16_capstone_hairstyle_swap/01_hairstyle_swap.ipynb)
# — assemble alignment + hair mask + (StyleGAN blend / diffusion inpaint) + blending into one
# working pipeline.
