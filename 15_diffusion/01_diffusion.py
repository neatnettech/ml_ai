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
# GANs are sharp but finicky (Module 13). **Diffusion models** are the paradigm that now
# powers Stable Diffusion, DALL·E, Midjourney — and they train with a *stable, simple*
# regression loss. For the hairstyle swap they give us "Route B": **inpainting** — regenerate
# only the masked hair region, conditioned on what we want.
#
# The core idea is almost suspiciously simple:
# 1. **Forward process:** gradually add Gaussian noise to an image over `T` steps until it's
#    pure noise. This is fixed math — no learning.
# 2. **Reverse process:** train a network to *predict the noise* that was added at each step.
#    To generate, start from pure noise and repeatedly subtract the predicted noise.
#
# **What you'll learn:**
# - The forward noising schedule and the closed-form "noise at step t" shortcut
# - Build a tiny **DDPM** from scratch (a small U-Net noise predictor) and train it on MNIST
# - Sample new digits by running the reverse denoising loop
# - Use a **pretrained Stable Diffusion inpainting** pipeline + **ControlNet** to regenerate
#   a masked region of a real photo — the hair-swap mechanism for Module 16

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
# ## 2. The Noise-Predictor Network
#
# The reverse process needs a network `ε_θ(x_t, t)` that predicts the noise in `x_t`. The
# standard choice is a **U-Net** (the same architecture from Module 11!) with the timestep
# `t` injected as an embedding so the network knows "how noisy" the input is.
#
# We build a compact U-Net with **sinusoidal time embeddings** (same positional-encoding
# trick used in transformers).

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
# ## 3. Training
#
# The whole loss is one line of intuition: **predict the noise you added**.
#
# ```
#   pick random t and random noise ε
#   x_t = q_sample(x_0, t, ε)
#   loss = MSE( ε_θ(x_t, t),  ε )
# ```
#
# That's it — a stable regression. No adversary, no KL balancing. (Training MNIST diffusion
# on a laptop is slow-ish; 2–3 epochs already produces recognizable digits. Reduce `epochs`
# if you're impatient, or run on Colab GPU.)

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
# ## 4. Sampling (the reverse process)
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
# ## 5. Inpainting intuition (why diffusion is perfect for hair swap)
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
# ## 6. Pretrained Stable Diffusion Inpainting (Colab GPU)
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
# reference image instead of text for tighter control).

# %%
ON_GPU = torch.cuda.is_available()
if ON_GPU:
    try:
        from diffusers import StableDiffusionInpaintPipeline
        from PIL import Image

        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting", torch_dtype=torch.float16
        ).to("cuda")

        # image = Image.open("face.png").convert("RGB").resize((512, 512))
        # mask  = Image.open("hair_mask.png").convert("L").resize((512, 512))  # white = hair
        # result = pipe(
        #     prompt="a person with short curly hair, photorealistic",
        #     image=image, mask_image=mask, num_inference_steps=30
        # ).images[0]
        # result.show()
        print("SD inpainting pipeline loaded. Provide image + hair mask + prompt to run.")
        print("Mask convention: WHITE = regenerate (hair), BLACK = keep (face/background).")
    except Exception as e:
        print(f"Could not load diffusers pipeline: {e}")
        print("Run `pip install diffusers transformers accelerate safetensors` on Colab.")
else:
    print("[skipped] Stable Diffusion inpainting — GPU only.")
    print("Mechanism is identical to the toy inpaint() above, at 512x512 with a")
    print("text/ControlNet condition instead of unconditional denoising.")

# %% [markdown]
# ## 7. Exercises
#
# ### Exercise 7.1 — The schedule matters
#
# Re-run the forward-process visualization with a **cosine** schedule instead of linear
# (it adds noise more gently early on and is widely used in practice). Implement
# `alpha_bars` from the cosine formula and compare how fast the image degrades vs the
# linear schedule.

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


ab_cos = cosine_alpha_bars(T)
sqrt_ab_c = torch.sqrt(ab_cos)
sqrt_1m_ab_c = torch.sqrt(1 - ab_cos)

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
# ### Exercise 7.2 — Inpaint an arbitrary mask
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
# ## Key Takeaways
#
# - **Forward process:** fixed math that noises an image to nothing; the closed form
#   `x_t = sqrt(ᾱ_t)·x_0 + sqrt(1-ᾱ_t)·ε` lets us jump to any step instantly.
#
# - **Reverse process:** train a (U-Net) network to **predict the added noise**; the loss is
#   plain MSE — stable, no adversary. Generate by denoising from pure noise step by step.
#
# - **Time conditioning** (sinusoidal embedding) tells the network the noise level.
#
# - **Inpainting** = re-impose the known region at every reverse step, let the model fill the
#   masked hole consistently with context. This is the hair-swap mechanism for Route B.
#
# - **Pretrained Stable Diffusion** inpainting + **ControlNet** does this at high resolution,
#   conditioned on a text prompt or a reference image.
#
# ---
# **Next:** [Capstone — Hairstyle Swap →](../16_capstone_hairstyle_swap/01_hairstyle_swap.ipynb)
# — assemble alignment + hair mask + (StyleGAN blend / diffusion inpaint) + blending into one
# working pipeline.
