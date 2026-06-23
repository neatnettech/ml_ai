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
# # Module 16.1 — Capstone: Hairstyle Swap
#
# **Purpose:** This is the goal of the whole **Advanced Image AI track**: take **person A**
# (keep their identity) and give them **person B's hairstyle**, blended so it looks real.
# You run the full pipeline — align → mask → generate → blend — end-to-end on your Mac with
# a naive generator first, score the result with real metrics, then upgrade the generation
# step to StyleGAN (Route A) or Stable Diffusion inpainting (Route B) on Colab.
#
# **Prerequisites:** Modules 11–15 (segmentation, VAE, GANs, StyleGAN inversion, diffusion).
#
# We assemble everything you built:
#
# | Step | Skill | Module |
# |------|-------|--------|
# | 1. **Align** the faces (FFHQ-style crop) | landmarks | (new here) |
# | 2. **Mask** the hair region | face parsing / segmentation | 11 |
# | 3a. **Route A**: blend hair in StyleGAN latent space | GAN inversion + style mixing | 12–14 |
# | 3b. **Route B**: inpaint the hair region with diffusion | DDPM / SD inpainting | 15 |
# | 4. **Composite & blend** the seam | masks + Poisson blending | 11 + (new) |
#
# > ⚠️ **Routes A and B need a GPU** (StyleGAN2 / Stable Diffusion) — run them on **Colab**.
# > Everything else — **alignment, masking, the naive end-to-end swap, compositing, and the
# > quality metrics — runs locally on your Mac.** The heavy cells are guarded and will skip
# > with notes if no GPU/weights are present, so the notebook always runs top-to-bottom.

# %%
import io
import os
import urllib.request

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import torch
import torch.nn.functional as F

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

ON_GPU = torch.cuda.is_available()
print(f"device: {device} | heavy-model-ready (CUDA): {ON_GPU}")
if not ON_GPU:
    print("Local mode: align + mask + naive swap + metrics run; Routes A/B skip (need GPU).")

# %% [markdown]
# ## 0. Sample assets
#
# A capstone needs inputs. We download two public-domain portraits from Wikimedia Commons —
# a **source** (whose identity we keep; same portrait as Module 11) and a **hair target**
# (whose hair we want — chosen for very different hair). If you're offline, the cell falls
# back to a synthetic face pair so every later cell still runs; swap in your own photos any
# time by replacing `portrait_src` / `portrait_tgt`.

# %%
def load_image_from_url(url, size=512):
    """Fetch an image and return it as a PIL RGB image (resized)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        img = Image.open(io.BytesIO(resp.read())).convert("RGB")
    return img.resize((size, size))


# Source: the Module 11 portrait (Marie Curie, 1920). Target: Einstein — very different hair.
SRC_URL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/"
           "7/7e/Marie_Curie_c1920.jpg/500px-Marie_Curie_c1920.jpg")
TGT_URL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/"
           "d/d3/Albert_Einstein_Head.jpg/500px-Albert_Einstein_Head.jpg")


def synthetic_portrait(skin, hair_color, hair_cy=0.28, hair_rx=0.36, hair_ry=0.27, seed=0):
    """Offline fallback: a cartoon head (oval face + noisy hair band) as a PIL image."""
    SZ = 512
    rng = np.random.default_rng(seed)
    img = np.zeros((SZ, SZ, 3), np.uint8)
    img[:] = (60, 70, 90)                                          # background
    yy, xx = np.ogrid[:SZ, :SZ]
    oval = ((xx - SZ / 2) / (SZ * 0.30)) ** 2 + ((yy - SZ * 0.55) / (SZ * 0.40)) ** 2 <= 1
    img[oval] = skin
    band = ((xx - SZ / 2) / (SZ * hair_rx)) ** 2 + ((yy - SZ * hair_cy) / (SZ * hair_ry)) ** 2 <= 1
    noise = rng.normal(0, 12, (SZ, SZ, 3)).clip(-40, 40)
    img[band] = np.clip(np.array(hair_color) + noise[band], 0, 255).astype(np.uint8)
    return Image.fromarray(img)


try:
    portrait_src = load_image_from_url(SRC_URL)
    portrait_tgt = load_image_from_url(TGT_URL)
    have_photos = True
    print("Downloaded both sample portraits (512x512).")
except Exception as e:
    print(f"Could not download sample images ({e}) — using synthetic fallback faces.")
    portrait_src = synthetic_portrait((180, 150, 130), (90, 60, 30), hair_ry=0.22, seed=0)
    portrait_tgt = synthetic_portrait((200, 170, 150), (210, 210, 215), hair_ry=0.33, seed=1)
    have_photos = False

fig, axes = plt.subplots(1, 2, figsize=(8, 4))
axes[0].imshow(portrait_src); axes[0].set_title('Source (keep identity)'); axes[0].axis('off')
axes[1].imshow(portrait_tgt); axes[1].set_title('Target (want this hair)'); axes[1].axis('off')
plt.suptitle('Capstone inputs' + ('' if have_photos else ' (synthetic fallback)'), fontsize=13)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 1. Face Alignment
#
# Both StyleGAN inversion and clean masking assume a **centered, consistently-cropped** face
# (the FFHQ convention: eyes on a fixed horizontal line, fixed inter-ocular distance). Real
# photos vary wildly, so we align first.
#
# Why this exact convention? Because the generators were *trained* on FFHQ-aligned faces —
# a photo cropped any other way is **out of domain**, and Module 14's MNIST-digit inversion
# showed what happens then: the model projects it onto whatever it knows, badly. Alignment
# is how we stay on the manifold.
#
# The standard approach: detect **facial landmarks** (68 points: eye corners, nose, jaw),
# then compute a similarity transform (rotate + scale + crop) that maps the eyes/mouth to
# canonical positions. The `face_alignment` library (or dlib's 68-point predictor) gives the
# landmarks — it runs fine on CPU for single images.
#
# ```python
# !pip install face-alignment    # one-time (works locally too)
# ```

# %%
def align_face(pil_img, output_size=256):
    """Detect landmarks and return an FFHQ-style aligned, centered face crop.

    Uses `face_alignment` if available. Falls back to a plain center-crop+resize so the
    rest of the notebook still runs (alignment quality just won't be as good).
    """
    try:
        import face_alignment
        fa = face_alignment.FaceAlignment(
            face_alignment.LandmarksType.TWO_D, flip_input=False,
            device="cuda" if torch.cuda.is_available() else "cpu")
        lms = fa.get_landmarks(np.array(pil_img))
        if not lms:
            raise RuntimeError("no face detected")
        lm = lms[0]  # (68, 2)

        # Canonical FFHQ alignment (simplified version of the official recipe):
        # build a quad from eye + mouth landmarks and crop/resize to it.
        eye_left = lm[36:42].mean(0)
        eye_right = lm[42:48].mean(0)
        mouth = (lm[48] + lm[54]) / 2
        eye_avg = (eye_left + eye_right) / 2
        eye_to_eye = eye_right - eye_left
        eye_to_mouth = mouth - eye_avg

        x = eye_to_eye.copy()
        x /= np.hypot(*x)
        x *= max(np.hypot(*eye_to_eye) * 2.0, np.hypot(*eye_to_mouth) * 1.8)
        y = np.flipud(x) * [-1, 1]
        c = eye_avg + eye_to_mouth * 0.1
        quad = np.stack([c - x - y, c - x + y, c + x + y, c + x - y])

        img = pil_img.transform(
            (output_size, output_size), Image.QUAD,
            (quad + 0.5).flatten(), Image.BILINEAR)
        return img.convert("RGB")
    except Exception as e:
        print(f"  [align] face_alignment unavailable or failed ({e}); using center crop.")
        w, h = pil_img.size
        s = min(w, h)
        img = pil_img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
        return img.resize((output_size, output_size)).convert("RGB")


# Run it on both inputs — this is step 1 of the actual pipeline, live.
aligned_src = align_face(portrait_src, output_size=512)
aligned_tgt = align_face(portrait_tgt, output_size=512)

fig, axes = plt.subplots(2, 2, figsize=(8, 8))
for row, (orig, aligned, name) in enumerate([(portrait_src, aligned_src, 'source'),
                                             (portrait_tgt, aligned_tgt, 'target')]):
    axes[row, 0].imshow(orig); axes[row, 0].set_title(f'{name}: original', fontsize=10)
    axes[row, 1].imshow(aligned); axes[row, 1].set_title(f'{name}: aligned 512px', fontsize=10)
    axes[row, 0].axis('off'); axes[row, 1].axis('off')
plt.suptitle('Step 1 — alignment (with face_alignment installed: eyes level, face centered)',
             fontsize=12)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 2. The Hair Mask (from Module 11)
#
# We reuse the face-parsing approach from Module 11 — BiSeNet labels 19 face regions and
# **class 17 is hair**. We wrap it with the `clean_mask` post-processing (largest component,
# fill holes, feather) so the composite has a soft, natural edge.
#
# > BiSeNet inference runs fine on **CPU/MPS** (~50 MB checkpoint, a second per image) —
# > this step does not need Colab. Setup (one-time, same as Module 11):
# ```bash
# git clone https://github.com/zllrunning/face-parsing.PyTorch.git
# # download 79999_iter.pth into face-parsing.PyTorch/res/cp/
# ```
# Without the checkpoint the function falls back to a top-of-head ellipse so everything
# downstream still runs (you'll see the difference in mask quality, which is itself
# instructive).

# %%
from scipy import ndimage
import torchvision.transforms.functional as TF


def clean_mask(mask, feather_sigma=3.0):
    """Largest connected component, fill holes, feather edge -> float alpha in [0,1]."""
    m = mask.astype(bool)
    labels, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, labels, range(1, n + 1))
        m = labels == (np.argmax(sizes) + 1)
    m = ndimage.binary_fill_holes(m)
    soft = ndimage.gaussian_filter(m.astype(float), sigma=feather_sigma)
    return np.clip(soft, 0, 1)


def hair_mask(pil_img, device):
    """Return a feathered hair-alpha mask (H,W) in [0,1] for an aligned face image.

    Requires face-parsing.PyTorch + checkpoint. Falls back to a top-of-head ellipse so the
    compositing demo still runs without the weights.
    """
    import sys
    FP_DIR = "face-parsing.PyTorch"
    CKPT = os.path.join(FP_DIR, "res", "cp", "79999_iter.pth")
    HAIR_CLASS = 17
    size = pil_img.size[0]
    if os.path.exists(CKPT):
        sys.path.insert(0, FP_DIR)
        from model import BiSeNet
        net = BiSeNet(n_classes=19).to(device).eval()
        net.load_state_dict(torch.load(CKPT, map_location=device))
        img = pil_img.resize((512, 512))
        x = TF.normalize(TF.to_tensor(img), (0.485, 0.456, 0.406),
                         (0.229, 0.224, 0.225)).unsqueeze(0).to(device)
        with torch.no_grad():
            parsing = net(x)[0].argmax(1).squeeze().cpu().numpy()
        raw = (parsing == HAIR_CLASS).astype(np.uint8)
        raw = np.array(Image.fromarray(raw * 255).resize((size, size))) > 127
        return clean_mask(raw.astype(np.uint8))
    else:
        print("  [hair_mask] no face-parsing checkpoint; using a placeholder ellipse.")
        yy, xx = np.ogrid[:size, :size]
        ell = ((xx - size / 2) / (size * 0.42)) ** 2 + ((yy - size * 0.32) / (size * 0.34)) ** 2 <= 1
        return clean_mask(ell.astype(np.uint8))


# Run it on both aligned faces — step 2 of the pipeline, live.
alpha_src = hair_mask(aligned_src, device)
alpha_tgt = hair_mask(aligned_tgt, device)

fig, axes = plt.subplots(2, 3, figsize=(12, 8))
for row, (img, alpha, name) in enumerate([(aligned_src, alpha_src, 'source'),
                                          (aligned_tgt, alpha_tgt, 'target')]):
    rgb = np.array(img)
    overlay = rgb.copy()
    overlay[..., 0] = np.clip(rgb[..., 0] + alpha * 120, 0, 255)
    axes[row, 0].imshow(rgb); axes[row, 0].set_title(f'{name}: aligned', fontsize=10)
    axes[row, 1].imshow(alpha, cmap='gray')
    axes[row, 1].set_title('feathered hair alpha', fontsize=10)
    axes[row, 2].imshow(overlay.astype(np.uint8))
    axes[row, 2].set_title('overlay (red = hair region)', fontsize=10)
    for ax in axes[row]:
        ax.axis('off')
plt.suptitle('Step 2 — hair masks (BiSeNet if checkpoint present, ellipse fallback otherwise)',
             fontsize=12)
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 3. The pipeline at a glance
#
# ```
#  photo (any size)        512x512 RGB           (512,512) float alpha
#  ┌────────────┐  align   ┌────────────┐ parse  ┌────────────┐
#  │ portrait   │ ───────► │ aligned    │ ─────► │ hair mask  │
#  └────────────┘          └────────────┘        └────────────┘
#                                │                     │
#                                ▼                     ▼
#                  ┌─────────────────────────────────────────────┐
#                  │ GENERATE new-hair pixels — pick a route:    │
#                  │  naive : transplant target's hair pixels    │
#                  │  A     : StyleGAN w+ blend (Module 14)      │
#                  │  B     : SD inpainting     (Module 15)      │
#                  └─────────────────────────────────────────────┘
#                                │  new-hair RGB (512x512)
#                                ▼
#                  ┌─────────────────────────────┐
#                  │ COMPOSITE onto source face  │ ──► final image
#                  │ (alpha or Poisson, step 5)  │
#                  └─────────────────────────────┘
# ```
#
# | Route | How | Pros | Cons / failure modes | Hardware |
# |---|---|---|---|---|
# | **naive** | copy target's hair pixels into source's hair box | runs anywhere, instant, shows the pipeline | lighting mismatch, geometry ignores head shape, leftover old hair | **your Mac** |
# | **A — StyleGAN** | invert both to w+, copy hair layers | globally coherent lighting/3D | inversion softens identity; regenerates whole face | Colab GPU |
# | **B — diffusion** | inpaint inside mask with a prompt | identity outside mask untouched; photoreal | needs good mask + prompt; can drift from target's exact hair | Colab GPU |
#
# The naive route exists *because* its failures are the curriculum: every artifact you see
# in §4 is something Route A or B was invented to fix.

# %% [markdown]
# ## 4. A naive swap, end-to-end, on your Mac
#
# No neural generator at all: crop the **target's hair pixels**, resize them to the
# **source's hair region**, paste, composite. Crude on purpose — but it is the *complete
# pipeline* (align → mask → generate → blend) running locally, and it produces a baseline
# we can measure (§7) and beat.

# %%
def naive_hair_transplant(src_rgb, src_alpha, tgt_rgb, tgt_alpha):
    """Transplant target hair pixels into the source's hair bounding box.

    Returns (new_hair_rgb, new_hair_alpha) sized like the source — ready to composite.
    """
    def bbox(alpha):
        ys, xs = np.where(alpha > 0.3)
        return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

    sy0, sy1, sx0, sx1 = bbox(src_alpha)
    ty0, ty1, tx0, tx1 = bbox(tgt_alpha)

    hair_crop = tgt_rgb[ty0:ty1, tx0:tx1]
    alpha_crop = tgt_alpha[ty0:ty1, tx0:tx1]

    h, w = sy1 - sy0, sx1 - sx0
    hair_rs = np.array(Image.fromarray(hair_crop).resize((w, h)))
    alpha_rs = np.array(
        Image.fromarray((alpha_crop * 255).astype(np.uint8)).resize((w, h))) / 255.0

    new_hair = np.zeros_like(src_rgb)
    new_alpha = np.zeros(src_rgb.shape[:2])
    new_hair[sy0:sy1, sx0:sx1] = hair_rs
    new_alpha[sy0:sy1, sx0:sx1] = alpha_rs
    return new_hair, new_alpha


src_rgb = np.array(aligned_src)
tgt_rgb = np.array(aligned_tgt)

naive_hair, naive_alpha = naive_hair_transplant(src_rgb, alpha_src, tgt_rgb, alpha_tgt)
print("Naive transplant computed: target hair pixels, resized into the source's hair box.")

# %% [markdown]
# ## 5. Compositing & Seam Blending  (runs locally!)
#
# Whichever route generated new hair, the final step is to **paste it onto the original
# source face** using the hair mask — and make the seam invisible. Two techniques:
#
# - **Alpha (feathered) blending:** `out = α·hair + (1-α)·face`, with a feathered `α` so the
#   boundary is soft. Simple, fast, what we used in Module 11.
# - **Poisson / seamless cloning** (`cv2.seamlessClone`): blends *gradients* instead of
#   colors, so the inserted region adopts the surrounding lighting/skin tone. This is what
#   makes a swap stop looking pasted-on.

# %%
def alpha_composite(face_rgb, hair_rgb, alpha):
    """Feathered alpha blend. Inputs: (H,W,3) uint8, alpha (H,W) in [0,1]."""
    a = alpha[..., None]
    return (a * hair_rgb + (1 - a) * face_rgb).astype(np.uint8)


def poisson_composite(face_rgb, hair_rgb, alpha):
    """Seamless (Poisson) clone of the hair region onto the face. Needs OpenCV."""
    import cv2
    mask = (alpha > 0.5).astype(np.uint8) * 255
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return face_rgb
    center = (int((xs.min() + xs.max()) / 2), int((ys.min() + ys.max()) / 2))
    # cv2 uses BGR; convert in/out
    out = cv2.seamlessClone(
        cv2.cvtColor(hair_rgb, cv2.COLOR_RGB2BGR),
        cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR),
        mask, center, cv2.NORMAL_CLONE)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)


# Composite the naive transplant both ways — the END of the local end-to-end run.
naive_alpha_out = alpha_composite(src_rgb, naive_hair, naive_alpha)
try:
    naive_poisson_out = poisson_composite(src_rgb, naive_hair, naive_alpha)
    have_cv2 = True
except Exception as e:
    naive_poisson_out = naive_alpha_out
    have_cv2 = False
    print(f"OpenCV not available ({e}) — install opencv-python to try Poisson blending.")

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
axes[0].imshow(src_rgb); axes[0].set_title('Source'); axes[0].axis('off')
axes[1].imshow(tgt_rgb); axes[1].set_title('Hair target'); axes[1].axis('off')
axes[2].imshow(naive_alpha_out); axes[2].set_title('Naive swap — alpha blend'); axes[2].axis('off')
axes[3].imshow(naive_poisson_out)
axes[3].set_title('Naive swap — Poisson' + ('' if have_cv2 else ' (n/a)')); axes[3].axis('off')
plt.suptitle('The complete pipeline, locally, with a dumb generator', fontsize=13)
plt.tight_layout(); plt.show()
print("Look closely at the failures — each one motivates a real route:")
print("  * lighting/color mismatch on the transplanted hair  -> Route A fixes globally")
print("  * old hair peeking outside the new mask             -> Route B regenerates the region")
print("  * geometry that ignores the head's shape            -> both routes model the head")

# %% [markdown]
# ## 6a. Route A — StyleGAN latent blend (Colab GPU)
#
# (Module 14 mechanics.) Invert source and target into `w+`, copy the target's
# hair-controlling layers into the source, synthesize. Pros: globally coherent, handles
# lighting/3D well. Cons: needs inversion (can lose identity detail), GPU-only.
#
# The cell below is real, runnable code on a Colab session where you've done the Module 14
# setup (stylegan2-ada-pytorch cloned, `ffhq.pkl` downloaded). It uses a compact MSE-only
# inversion; Module 14's `invert_image` adds the VGG perceptual loss for better quality.

# %%
def route_a_stylegan(G, w_source, w_target, hair_layers=range(4, 11)):
    """Copy target's hair layers into source w+ and synthesize. (See Module 14.)"""
    w = w_source.clone()
    for layer in hair_layers:
        w[:, layer] = w_target[:, layer]
    with torch.no_grad():
        img = G.synthesis(w, noise_mode="const")
    return img


if ON_GPU and os.path.exists("ffhq.pkl"):
    import pickle

    with open("ffhq.pkl", "rb") as f:
        G_sg = pickle.load(f)["G_ema"].to(device).eval()
    res = G_sg.img_resolution

    def pil_to_target(pil):
        return (TF.to_tensor(pil.resize((res, res))).to(device) * 2 - 1).unsqueeze(0)

    def invert_w_plus(G, target, steps=250, lr=0.05):
        """Compact optimization-based inversion (MSE only — see Module 14 for the full one)."""
        with torch.no_grad():
            w_avg = G.mapping(torch.randn(10000, G.z_dim, device=device), None).mean(0, keepdim=True)
        w_opt = w_avg.clone().requires_grad_(True)
        opt = torch.optim.Adam([w_opt], lr=lr)
        for _ in range(steps):
            loss = F.mse_loss(G.synthesis(w_opt, noise_mode="const"), target)
            opt.zero_grad(); loss.backward(); opt.step()
        return w_opt.detach()

    print("Inverting source and target (~2-4 min total)...")
    w_src = invert_w_plus(G_sg, pil_to_target(aligned_src))
    w_tgt = invert_w_plus(G_sg, pil_to_target(aligned_tgt))
    out_a = route_a_stylegan(G_sg, w_src, w_tgt)
    out_a_rgb = np.array(Image.fromarray(
        ((out_a.clamp(-1, 1) + 1) * 127.5)[0].permute(1, 2, 0).to(torch.uint8).cpu().numpy()
    ).resize((512, 512)))
    # Composite the StyleGAN hair back onto the REAL source pixels (identity preserved)
    route_a_final = poisson_composite(src_rgb, out_a_rgb, alpha_src) if have_cv2 \
        else alpha_composite(src_rgb, out_a_rgb, alpha_src)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(src_rgb); axes[0].set_title('Source'); axes[0].axis('off')
    axes[1].imshow(out_a_rgb); axes[1].set_title('StyleGAN blend (whole frame)'); axes[1].axis('off')
    axes[2].imshow(route_a_final); axes[2].set_title('Composited (mask = hair only)'); axes[2].axis('off')
    plt.suptitle('Route A: invert -> blend hair layers -> composite', fontsize=13)
    plt.tight_layout(); plt.show()
else:
    print("[skipped] Route A — needs a CUDA GPU + ffhq.pkl (Module 14 setup).")
    print("  pipeline: align -> invert(source) -> invert(target) -> blend hair layers")
    print("  then mask-composite the StyleGAN hair onto the original source (step 5).")

# %% [markdown]
# ## 6b. Route B — Diffusion inpainting (Colab GPU)
#
# (Module 15 mechanics.) Mask the source's hair region, inpaint it conditioned on the desired
# hairstyle — via a **text prompt** ("long wavy blonde hair") or, for tighter control, a
# **ControlNet** conditioned on the target's hair edges/structure. Pros: photorealistic, edits
# only the masked pixels, keeps identity perfectly. Cons: GPU, prompt/Control tuning.

# %%
_PIPE = None   # cache: loading SD takes ~30 s — do it once per session, not per call


def get_inpaint_pipe():
    global _PIPE
    if _PIPE is None:
        from diffusers import StableDiffusionInpaintPipeline
        _PIPE = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting", torch_dtype=torch.float16).to("cuda")
    return _PIPE


def route_b_inpaint(source_img, hair_alpha, prompt, steps=30):
    """Stable Diffusion inpainting over the hair region. (See Module 15.)

    source_img: PIL RGB (512x512). hair_alpha: (H,W) float mask, 1=hair.
    """
    pipe = get_inpaint_pipe()
    mask_img = Image.fromarray((hair_alpha * 255).astype(np.uint8)).resize((512, 512))
    src = source_img.resize((512, 512))
    result = pipe(prompt=prompt, image=src, mask_image=mask_img,
                  num_inference_steps=steps).images[0]
    return result


if ON_GPU:
    try:
        gen = route_b_inpaint(
            aligned_src, alpha_src,
            prompt="a person with long wavy gray hair, photorealistic, studio lighting")
        route_b_final = np.array(gen.resize((512, 512)))
        fig, axes = plt.subplots(1, 2, figsize=(9, 4.5))
        axes[0].imshow(src_rgb); axes[0].set_title('Source'); axes[0].axis('off')
        axes[1].imshow(route_b_final); axes[1].set_title('Route B inpaint'); axes[1].axis('off')
        plt.suptitle('Route B: SD inpainting inside the hair mask', fontsize=13)
        plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"Route B failed ({e}) — pip install diffusers transformers accelerate safetensors")
else:
    print("[skipped] Route B — needs Stable Diffusion on a GPU.")
    print('  route_b_inpaint(aligned_src, alpha_src, prompt="a sleek bob haircut, photorealistic")')
    print("  ControlNet variant: condition on target hair edges for shape fidelity.")

# %% [markdown]
# ## 7. Scoring your swap (runs locally)
#
# A capstone needs a rubric, not vibes. Two cheap, useful proxies:
#
# - **`keep_region_error`** — mean squared difference between output and source *outside*
#   the (dilated) hair mask. Measures **identity preservation**: a perfect swap changes
#   nothing but hair. Lower = better.
# - **`seam_score`** — mean gradient magnitude inside the mask's boundary band
#   (`0.05 < α < 0.95`). Sharp pasted edges create strong gradients exactly there.
#   Lower = smoother seam.
#
# The real literature uses **ArcFace identity similarity** (face-recognition embeddings)
# and **FID** (distribution realism) — same ideas, heavier models.

# %%
def keep_region_error(src_rgb, out_rgb, alpha, dilate_iters=8):
    """MSE outside the dilated hair region — identity-preservation proxy (lower = better)."""
    hair = ndimage.binary_dilation(alpha > 0.3, iterations=dilate_iters)
    keep = ~hair
    diff = (src_rgb.astype(float) - out_rgb.astype(float)) ** 2
    return float(diff[keep].mean())


def seam_score(out_rgb, alpha):
    """Mean gradient magnitude in the mask's boundary band — seam-visibility proxy."""
    band = (alpha > 0.05) & (alpha < 0.95)
    if not band.any():
        return 0.0
    gray = out_rgb.mean(axis=2)
    gy, gx = np.gradient(gray)
    return float(np.sqrt(gx ** 2 + gy ** 2)[band].mean())


print(f"{'composite':<22} {'keep_region_error':>18} {'seam_score':>12}")
for name, out in [('naive + alpha', naive_alpha_out),
                  ('naive + Poisson', naive_poisson_out)]:
    print(f"{name:<22} {keep_region_error(src_rgb, out, naive_alpha):>18.2f} "
          f"{seam_score(out, naive_alpha):>12.2f}")
print("\nPoisson usually wins seam_score (gradient blending) but can bleed color, which")
print("keep_region_error picks up. Exercise 10.4 asks you to optimize this trade-off.")

# %% [markdown]
# ## 8. The Full Pipeline (putting it together)
#
# One function, three routes. `route="naive"` runs **fully locally** and returns a real
# image; `"A"`/`"B"` use the GPU sections above when available.

# %%
def hairstyle_swap(source, target, route="naive", prompt=None):
    """End-to-end swap. source/target: PIL images or file paths.

    route: 'naive' (local), 'A' (StyleGAN, GPU), 'B' (diffusion inpaint, GPU).
    Returns the final composited PIL image, or None if the route's models are unavailable.
    """
    if isinstance(source, str):
        source = Image.open(source).convert("RGB")
    if isinstance(target, str):
        target = Image.open(target).convert("RGB")

    # 1. Align both faces
    src_pil = align_face(source, output_size=512)
    tgt_pil = align_face(target, output_size=512)
    src_arr = np.array(src_pil)

    # 2. Hair masks
    a_src = hair_mask(src_pil, device)
    a_tgt = hair_mask(tgt_pil, device)

    # 3. Generate new hair
    if route == "naive":
        new_hair, new_alpha = naive_hair_transplant(src_arr, a_src, np.array(tgt_pil), a_tgt)
    elif route == "A":
        if not (ON_GPU and os.path.exists("ffhq.pkl")):
            print("Route A needs a CUDA GPU + ffhq.pkl (see §6a / Module 14).")
            return None
        w_s = invert_w_plus(G_sg, pil_to_target(src_pil))
        w_t = invert_w_plus(G_sg, pil_to_target(tgt_pil))
        out = route_a_stylegan(G_sg, w_s, w_t)
        new_hair = np.array(Image.fromarray(
            ((out.clamp(-1, 1) + 1) * 127.5)[0].permute(1, 2, 0).to(torch.uint8).cpu().numpy()
        ).resize((512, 512)))
        new_alpha = a_src
    else:  # route == "B"
        if not ON_GPU:
            print("Route B needs Stable Diffusion on a GPU (see §6b / Module 15).")
            return None
        prompt = prompt or "a person with a stylish haircut, photorealistic, detailed hair"
        generated = route_b_inpaint(src_pil, a_src, prompt)
        new_hair = np.array(generated.resize((512, 512)))
        new_alpha = a_src

    # 4. Composite onto the original source with the hair mask
    try:
        final = poisson_composite(src_arr, new_hair, new_alpha)
    except Exception:
        final = alpha_composite(src_arr, new_hair, new_alpha)
    return Image.fromarray(final)


# The capstone moment: a complete swap, locally.
result = hairstyle_swap(portrait_src, portrait_tgt, route="naive")
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
axes[0].imshow(portrait_src); axes[0].set_title('Source'); axes[0].axis('off')
axes[1].imshow(portrait_tgt); axes[1].set_title('Target hair'); axes[1].axis('off')
axes[2].imshow(result); axes[2].set_title('hairstyle_swap(..., route="naive")'); axes[2].axis('off')
plt.suptitle('One call, whole pipeline', fontsize=13)
plt.tight_layout(); plt.show()
print('On Colab, upgrade the generator: hairstyle_swap(a, b, route="B",')
print('                                  prompt="long curly hair, photorealistic")')

# %% [markdown]
# ## 9. Capstone checklist — definition of done
#
# Work through this before calling the capstone complete:
#
# - [ ] **Both faces aligned** (eyes level, centered — `face_alignment` installed, not the
#       center-crop fallback)
# - [ ] **Real hair masks** from the BiSeNet parser (not the ellipse fallback), cleaned
#       and feathered
# - [ ] **Naive swap runs locally** and you can explain each visible artifact
# - [ ] **Metrics computed**: `keep_region_error` and `seam_score` for alpha vs Poisson
# - [ ] **One GPU route** (A or B) produces a swap on Colab with your own photo pair
# - [ ] **3-sentence failure analysis**: where does your best result still look wrong, and
#       which paper in Further reading addresses exactly that?

# %% [markdown]
# ## 10. Exercises
#
# > 10.1–10.4 run locally; 10.5 is the Colab capstone proper.
#
# ### Exercise 10.1 — Compare alpha vs Poisson on a recolor
#
# Take the source portrait, recolor its hair region (shift the hue inside the mask), then
# composite it back with **both** `alpha_composite` and `poisson_composite`. Which looks
# more natural? Where does each break (wispy hair edges, strong lighting)? Write 3
# sentences on what you observe.

# %%
# TODO: recolor the hair region of src_rgb, compare both composites
# Hint: recolor by converting to HSV (cv2.cvtColor), shifting the H channel inside the mask.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: recolor-and-recomposite on the source portrait
try:
    import cv2
    hsv = cv2.cvtColor(src_rgb, cv2.COLOR_RGB2HSV).astype(np.int16)
    # Recolor only inside the hair region
    region = alpha_src > 0.3
    hsv[region, 0] = (hsv[region, 0] + 60) % 180     # hue shift
    recolored = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    a_out = alpha_composite(src_rgb, recolored, alpha_src)
    p_out = poisson_composite(src_rgb, recolored, alpha_src)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(src_rgb); axes[0].set_title('Original'); axes[0].axis('off')
    axes[1].imshow(a_out); axes[1].set_title('Alpha (keeps new hue)'); axes[1].axis('off')
    axes[2].imshow(p_out); axes[2].set_title('Poisson (blends to lighting)'); axes[2].axis('off')
    plt.suptitle('Recolor hair, then composite two ways', fontsize=13)
    plt.tight_layout(); plt.show()
    print("Alpha preserves the exact new color; Poisson can wash strong recolors toward the")
    print("surrounding tone — choose per use-case (color change -> alpha; texture/style -> Poisson).")
except Exception as e:
    print(f"Install opencv-python to run this exercise ({e}).")

# %% [markdown]
# ### Exercise 10.2 — Mask dilation and its effect
#
# The hair mask boundary controls how much of the original is replaced. Experiment with
# **dilating** vs **eroding** the mask (e.g. `ndimage.binary_dilation`) before feathering.
# Composite each and observe: too tight leaves a halo of old hair; too loose eats into the
# face/background. Find a good amount, and note why this matters more for diffusion
# (Route B) than for StyleGAN (Route A).

# %%
# TODO: dilate/erode the source hair mask by a few pixels, feather, composite, compare
# Hint: ndimage.binary_dilation(mask, iterations=k) / binary_erosion(...)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: mask dilation sweep on the naive transplant
base_mask = naive_alpha > 0.5

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for ax, k in zip(axes, [-6, 0, 6, 14]):
    if k < 0:
        m = ndimage.binary_erosion(base_mask, iterations=-k)
    elif k > 0:
        m = ndimage.binary_dilation(base_mask, iterations=k)
    else:
        m = base_mask
    a = clean_mask(m.astype(np.uint8), feather_sigma=5.0)
    comp = alpha_composite(src_rgb, naive_hair, a)
    ax.imshow(comp)
    ax.set_title({-6: 'eroded (halo of old hair)', 0: 'original',
                  6: 'dilated +6', 14: 'too dilated (eats face)'}[k], fontsize=9)
    ax.axis('off')
plt.suptitle('Mask dilation/erosion changes how much gets replaced', fontsize=13)
plt.tight_layout(); plt.show()
print("Diffusion (Route B) only edits inside the mask, so a slightly DILATED mask gives it")
print("room to grow longer/different hair. StyleGAN (Route A) regenerates the whole head, so")
print("the mask there is only for the final composite, not for generation.")

# %% [markdown]
# ### Exercise 10.3 — Swap the other way
#
# Run the naive transplant in **both directions**: target's hair onto the source (done in
# §4) and source's hair onto the target. The two directions fail differently — going from
# *more* hair to *less* hair exposes regions the transplant has nothing to fill (old hair
# and background that should be revealed). Show both results and explain the asymmetry.

# %%
# TODO: naive_hair_transplant in both directions, composite, compare
# Hint: just swap the (rgb, alpha) argument pairs.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: both directions
fwd_hair, fwd_alpha = naive_hair_transplant(src_rgb, alpha_src, tgt_rgb, alpha_tgt)
rev_hair, rev_alpha = naive_hair_transplant(tgt_rgb, alpha_tgt, src_rgb, alpha_src)

fwd_out = alpha_composite(src_rgb, fwd_hair, fwd_alpha)
rev_out = alpha_composite(tgt_rgb, rev_hair, rev_alpha)

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
axes[0].imshow(src_rgb); axes[0].set_title('A (source)'); axes[0].axis('off')
axes[1].imshow(fwd_out); axes[1].set_title("A with B's hair"); axes[1].axis('off')
axes[2].imshow(tgt_rgb); axes[2].set_title('B (target)'); axes[2].axis('off')
axes[3].imshow(rev_out); axes[3].set_title("B with A's hair"); axes[3].axis('off')
plt.suptitle('The swap is asymmetric', fontsize=13)
plt.tight_layout(); plt.show()
print("Going big->small hair: the new mask doesn't cover all the OLD hair, which stays")
print("visible outside it — a transplant can only ADD pixels, never reveal what was behind")
print("the original hair. That 'reveal the hidden background' problem is exactly what")
print("inpainting (Route B) solves: the model HALLUCINATES plausible background there.")

# %% [markdown]
# ### Exercise 10.4 — Beat the seam score
#
# §7 gave you two metrics in tension: heavier feathering smooths the seam (`seam_score`
# down) but smears more of the surrounding face (`keep_region_error` up). Sweep
# `feather_sigma` over ~6 values (e.g. 1, 2, 4, 6, 10, 16) on the naive swap, compute both
# metrics for each, and plot the trade-off curve. Where would you operate?

# %%
# TODO: for each feather_sigma, rebuild the feathered alpha, composite, compute both
#       metrics, then plot seam_score vs keep_region_error.
# Hint: a = clean_mask((naive_alpha > 0.5).astype(np.uint8), feather_sigma=s)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: feathering trade-off sweep
sigmas = [1, 2, 4, 6, 10, 16]
kre, ss = [], []
for s in sigmas:
    a = clean_mask((naive_alpha > 0.5).astype(np.uint8), feather_sigma=s)
    out = alpha_composite(src_rgb, naive_hair, a)
    kre.append(keep_region_error(src_rgb, out, a))
    ss.append(seam_score(out, a))

fig, ax1 = plt.subplots(figsize=(8, 4))
ax1.plot(sigmas, ss, 'b-o', label='seam_score')
ax1.set_xlabel('feather_sigma'); ax1.set_ylabel('seam_score', color='b')
ax2 = ax1.twinx()
ax2.plot(sigmas, kre, 'r-s', label='keep_region_error')
ax2.set_ylabel('keep_region_error', color='r')
plt.title('Feathering trade-off: smoother seam vs more face smearing')
fig.tight_layout(); plt.show()
for s, a_, b_ in zip(sigmas, ss, kre):
    print(f"  sigma={s:<3} seam={a_:7.2f}  keep_err={b_:7.2f}")
print("Typical sweet spot: sigma 4-6 — most of the seam improvement, little identity cost.")
print("Past that you pay identity for diminishing seam returns. (Your numbers may differ.)")

# %% [markdown]
# ### Exercise 10.5 — The capstone proper (Colab)
#
# On a Colab GPU, run the **full Route B swap on your own photo pair**:
# 1. Upload two portraits (you + a hairstyle you want, or any consenting pair).
# 2. Align both, build real BiSeNet masks (checklist §9 items 1–2).
# 3. Inpaint with **two different prompts** and compare.
# 4. Compute `keep_region_error` and `seam_score` for both results.
# 5. Write your 3-sentence failure analysis (checklist item 6).

# %%
# TODO: full Route B run on your own photos, two prompts, metrics + analysis
# Hint: result = hairstyle_swap("me.jpg", "style.jpg", route="B", prompt=...)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: the full Colab run (executable on GPU; prints the recipe otherwise)
if ON_GPU:
    prompts = [
        "a person with short curly hair, photorealistic, natural lighting",
        "a person with long straight platinum hair, photorealistic, natural lighting",
    ]
    results = []
    for p in prompts:
        r = hairstyle_swap(portrait_src, portrait_tgt, route="B", prompt=p)
        results.append((p, r))

    fig, axes = plt.subplots(1, 1 + len(results), figsize=(5 * (1 + len(results)), 5))
    axes[0].imshow(portrait_src); axes[0].set_title('Source'); axes[0].axis('off')
    for ax, (p, r) in zip(axes[1:], results):
        ax.imshow(r); ax.set_title(p[:38] + '...', fontsize=8); ax.axis('off')
    plt.tight_layout(); plt.show()

    a_src_m = hair_mask(align_face(portrait_src, 512), device)
    src_arr = np.array(align_face(portrait_src, 512))
    for p, r in results:
        out = np.array(r.resize((512, 512)))
        print(f"  '{p[:40]}...' keep_err={keep_region_error(src_arr, out, a_src_m):.2f} "
              f"seam={seam_score(out, a_src_m):.2f}")
    print("Swap portrait_src/portrait_tgt for your own uploaded photos to make it yours.")
else:
    print("[skipped] Needs a Colab GPU. Recipe:")
    print("  1. upload me.jpg + style.jpg;  2. ensure BiSeNet checkpoint is in place")
    print('  3. r = hairstyle_swap("me.jpg", "style.jpg", route="B", prompt="...")')
    print("  4. repeat with a second prompt;  5. score both with §7's metrics")
    print("  6. write the 3-sentence failure analysis (checklist §9)")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Pipeline thinking** | A swap is align → mask → generate → blend; each stage is a separate skill, separately debuggable |
# | **FFHQ alignment** | Keeps real photos on the generators' training manifold — the out-of-domain lesson from Module 14, applied |
# | **Hair masking** | Module 11's parser + clean/feather post-processing decide exactly which pixels may change |
# | **Naive baseline** | A dumb generator runs the whole pipeline locally; its artifacts are the *reason* Routes A/B exist |
# | **Route A (StyleGAN)** | Globally coherent lighting/3D via w+ blending, but inversion can soften identity |
# | **Route B (diffusion)** | Edits only masked pixels — identity preserved; the approach modern tools use |
# | **Compositing** | Feathered alpha vs Poisson (gradient) blending — what turns "pasted wig" into believable |
# | **Evaluation** | `keep_region_error` + `seam_score` (cheap proxies for ArcFace-ID and FID) make quality measurable |
#
# **Out of scope (your next steps):** robustness to profile views and occluding hair,
# explicit lighting/color transfer, temporal consistency for video — the papers below
# combine these ideas with purpose-built losses. You now have the foundation to read and
# reimplement them.
#
# ## Further reading
#
# - **Barbershop** (GAN-based hairstyle transfer via aligned latent blending — Route A,
#   done properly): https://arxiv.org/abs/2106.01505
# - **HairCLIP** (text- and reference-driven hair editing): https://arxiv.org/abs/2112.05142
# - **Style Your Hair** (pose-invariant hairstyle transfer): https://arxiv.org/abs/2208.07765
# - **diffusers inpainting guide** (the Route B toolchain):
#   https://huggingface.co/docs/diffusers/using-diffusers/inpaint
# - **ControlNet** (structure-conditioned diffusion — tighter hair-shape control):
#   https://arxiv.org/abs/2302.05543
#
# ---
# 🎉 **You finished the Advanced Image AI track.** From "what is a pixel" (Module 11) to a
# full generative hairstyle-swap pipeline. The same four-skill template — locate, model,
# invert/condition, composite — underlies most image-editing AI.
#
# **Next:** [Module 17 — FastAPI CRUD →](../17_fastapi_crud/01_fastapi_crud.ipynb) — the
# **Backend track**: learn to ship models like these behind a real, authenticated API.
