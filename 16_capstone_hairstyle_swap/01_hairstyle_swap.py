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
# This is it — the goal of the whole Advanced Image AI track. We take **person A** (keep
# their identity) and give them **person B's hairstyle**, then blend it so it looks real.
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
# > **Steps 1, 2, and 4 (alignment, masking, blending) run locally on your Mac.** The
# > heavy cells are guarded and will skip with notes if no GPU/weights are present, so the
# > notebook always runs top-to-bottom. The local **compositing demo** at the end works
# > fully offline and is the piece that makes any swap look seamless.

# %%
import os
import numpy as np
import matplotlib.pyplot as plt

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
    print("Local mode: alignment + masking + compositing run; Routes A/B skip (need GPU).")

# %% [markdown]
# ## 1. Face Alignment
#
# Both StyleGAN inversion and clean masking assume a **centered, consistently-cropped** face
# (the FFHQ convention: eyes on a fixed horizontal line, fixed inter-ocular distance). Real
# photos vary wildly, so we align first.
#
# The standard approach: detect **facial landmarks** (68 points: eye corners, nose, jaw),
# then compute a similarity transform (rotate + scale + crop) that maps the eyes/mouth to
# canonical positions. The `face_alignment` library (or dlib's 68-point predictor) gives the
# landmarks.
#
# ```python
# !pip install face-alignment    # one-time
# ```

# %%
def align_face(pil_img, output_size=256):
    """Detect landmarks and return an FFHQ-style aligned, centered face crop.

    Uses `face_alignment` if available. Falls back to a plain center-crop+resize so the
    rest of the notebook still runs (alignment quality just won't be as good).
    """
    from PIL import Image
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


print("align_face() ready. Feed it source and target portraits.")
print("It aligns to the FFHQ convention so StyleGAN inversion and masking behave.")

# %% [markdown]
# ## 2. The Hair Mask (from Module 11)
#
# We reuse the face-parsing approach from Module 11 — BiSeNet labels 19 face regions and
# **class 17 is hair**. We wrap it with the `clean_mask` post-processing (largest component,
# fill holes, feather) so the composite has a soft, natural edge.
#
# Setup (one-time, same as Module 11):
# ```bash
# git clone https://github.com/zllrunning/face-parsing.PyTorch.git
# # download 79999_iter.pth into face-parsing.PyTorch/res/cp/
# ```

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


from PIL import Image
print("hair_mask() ready (Module 11's parser + clean_mask).")

# %% [markdown]
# ## 3a. Route A — StyleGAN latent blend
#
# (Module 14 mechanics.) Invert source and target into `w+`, copy the target's
# hair-controlling layers into the source, synthesize. Pros: globally coherent, handles
# lighting/3D well. Cons: needs inversion (can lose identity detail), GPU-only.

# %%
def route_a_stylegan(G, w_source, w_target, hair_layers=range(4, 11)):
    """Copy target's hair layers into source w+ and synthesize. (See Module 14.)"""
    w = w_source.clone()
    for layer in hair_layers:
        w[:, layer] = w_target[:, layer]
    with torch.no_grad():
        img = G.synthesis(w, noise_mode="const")
    return img


if ON_GPU:
    print("Route A: load StyleGAN2 (Module 14), invert both faces, call route_a_stylegan().")
    print("  pipeline: align -> invert(source) -> invert(target) -> blend hair layers")
    print("  then mask-composite the StyleGAN hair onto the original source (step 4).")
    # See Module 14 for invert_image() and the full StyleGAN2 loading code.
else:
    print("[skipped] Route A — needs StyleGAN2 on a GPU. Mechanism shown above.")

# %% [markdown]
# ## 3b. Route B — Diffusion inpainting
#
# (Module 15 mechanics.) Mask the source's hair region, inpaint it conditioned on the desired
# hairstyle — via a **text prompt** ("long wavy blonde hair") or, for tighter control, a
# **ControlNet** conditioned on the target's hair edges/structure. Pros: photorealistic, edits
# only the masked pixels, keeps identity perfectly. Cons: GPU, prompt/Control tuning.

# %%
def route_b_inpaint(pipe, source_img, hair_alpha, prompt, steps=30):
    """Stable Diffusion inpainting over the hair region. (See Module 15.)

    source_img: PIL RGB (512x512). hair_alpha: (H,W) float mask, 1=hair.
    """
    mask_img = Image.fromarray((hair_alpha * 255).astype(np.uint8)).resize((512, 512))
    src = source_img.resize((512, 512))
    result = pipe(prompt=prompt, image=src, mask_image=mask_img,
                  num_inference_steps=steps).images[0]
    return result


if ON_GPU:
    print("Route B: load SD inpainting (Module 15), build hair mask (step 2), call route_b_inpaint().")
    print('  e.g. prompt="a person with a sleek bob haircut, photorealistic, studio lighting"')
    print("  ControlNet variant: condition on target hair edges for shape fidelity.")
else:
    print("[skipped] Route B — needs Stable Diffusion on a GPU. Mechanism shown above.")

# %% [markdown]
# ## 4. Compositing & Seam Blending  (runs locally!)
#
# Whichever route generated new hair, the final step is to **paste it onto the original
# source face** using the hair mask — and make the seam invisible. Two techniques:
#
# - **Alpha (feathered) blending:** `out = α·hair + (1-α)·face`, with a feathered `α` so the
#   boundary is soft. Simple, fast, what we used in Module 11.
# - **Poisson / seamless cloning** (`cv2.seamlessClone`): blends *gradients* instead of
#   colors, so the inserted region adopts the surrounding lighting/skin tone. This is what
#   makes a swap stop looking pasted-on.
#
# This whole section runs on your Mac — let's demonstrate it on a synthetic example so you
# can see the difference without any GPU model.

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


# --- Synthetic demo: a "face" (blue-ish) gets "hair" (orange) composited on top ---
SZ = 256
rng = np.random.default_rng(0)
face = np.zeros((SZ, SZ, 3), np.uint8)
face[:] = (180, 150, 130)                            # skin-ish base
yy, xx = np.ogrid[:SZ, :SZ]
face_oval = ((xx - SZ/2)/(SZ*0.3))**2 + ((yy - SZ*0.55)/(SZ*0.4))**2 <= 1
face[~face_oval] = (60, 70, 90)                      # background

hair_src = np.zeros((SZ, SZ, 3), np.uint8)
hair_src[:] = (200, 120, 40)                         # the new "hair" color/texture
hair_src += (rng.normal(0, 12, hair_src.shape)).astype(np.int16).clip(-40, 40).astype(np.uint8)

# Hair region: a band across the top of the head
hair_alpha = (((xx - SZ/2)/(SZ*0.34))**2 + ((yy - SZ*0.30)/(SZ*0.26))**2 <= 1).astype(np.uint8)
hair_alpha = clean_mask(hair_alpha, feather_sigma=6.0)   # feather the edge (Module 11)

alpha_out = alpha_composite(face, hair_src, hair_alpha)
try:
    poisson_out = poisson_composite(face, hair_src, hair_alpha)
    have_cv2 = True
except Exception as e:
    poisson_out = alpha_out
    have_cv2 = False
    print(f"OpenCV not available ({e}) — install opencv-python to try Poisson blending.")

fig, axes = plt.subplots(1, 5, figsize=(18, 4))
axes[0].imshow(face); axes[0].set_title('Source face'); axes[0].axis('off')
axes[1].imshow(hair_src); axes[1].set_title('New hair (from route A/B)'); axes[1].axis('off')
axes[2].imshow(hair_alpha, cmap='gray'); axes[2].set_title('Feathered hair mask'); axes[2].axis('off')
axes[3].imshow(alpha_out); axes[3].set_title('Alpha blend'); axes[3].axis('off')
axes[4].imshow(poisson_out); axes[4].set_title('Poisson blend' + ('' if have_cv2 else ' (n/a)')); axes[4].axis('off')
plt.suptitle('Compositing the swapped hair onto the source face', fontsize=14)
plt.tight_layout(); plt.show()
print("Alpha blend keeps the hair's own color; Poisson adapts it to the face's lighting.")
print("In a real swap, 'New hair' is the StyleGAN/diffusion output and the mask comes from")
print("face parsing — but the compositing math is exactly what you see here.")

# %% [markdown]
# ## 5. The Full Pipeline (putting it together)
#
# Here's the end-to-end orchestration. On a GPU with the weights in place it produces a real
# swap; locally it walks the steps and uses the fallbacks so you can read the control flow.

# %%
def hairstyle_swap(source_path, target_path, route="B", prompt=None):
    """End-to-end swap. route 'A' = StyleGAN, 'B' = diffusion inpaint.

    Returns the final composited image (or None if heavy models are unavailable).
    """
    # 1. Align both faces
    src_pil = align_face(Image.open(source_path).convert("RGB"), output_size=512)
    tgt_pil = align_face(Image.open(target_path).convert("RGB"), output_size=512)

    # 2. Hair masks
    src_hair_alpha = hair_mask(src_pil, device)   # where to remove/replace on the source

    if not ON_GPU:
        print("Local mode: aligned faces + masks computed; generation step needs a GPU.")
        return None

    # 3. Generate new hair (one of the two routes)
    if route == "A":
        # ... load StyleGAN2 (Module 14), invert src & tgt, route_a_stylegan(...)
        raise NotImplementedError("Wire up Module 14's StyleGAN load + invert here.")
    else:
        # ... load SD inpainting pipe (Module 15)
        from diffusers import StableDiffusionInpaintPipeline
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting", torch_dtype=torch.float16).to("cuda")
        prompt = prompt or "a person with a stylish haircut, photorealistic, detailed hair"
        generated = route_b_inpaint(pipe, src_pil, src_hair_alpha, prompt)
        new_hair = np.array(generated.resize((512, 512)))

    # 4. Composite onto the original source with the hair mask
    src_rgb = np.array(src_pil)
    final = poisson_composite(src_rgb, new_hair, src_hair_alpha)
    return Image.fromarray(final)


print("hairstyle_swap() defined. On Colab:")
print('  out = hairstyle_swap("alice.jpg", "bob.jpg", route="B",')
print('                       prompt="long curly hair, photorealistic")')
print("  out.show()")

# %% [markdown]
# ## 6. Exercises
#
# ### Exercise 6.1 — Compare alpha vs Poisson on a real photo
#
# Take a real portrait, compute its hair mask (Module 11 parser), recolor the hair region
# (e.g. shift hue), then composite it back with **both** `alpha_composite` and
# `poisson_composite`. Which looks more natural? Where does each break (wispy hair edges,
# strong lighting)? Write 3 sentences on what you observe.

# %%
# TODO: load a real aligned portrait, get hair mask, recolor hair, compare both composites
# Hint: recolor by converting to HSV (cv2.cvtColor), shifting the H channel inside the mask.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: recolor-and-recomposite on the synthetic face (swap to a real one on Colab)
try:
    import cv2
    hsv = cv2.cvtColor(face, cv2.COLOR_RGB2HSV).astype(np.int16)
    # Recolor only inside the hair region
    region = hair_alpha > 0.3
    hsv[region, 0] = (hsv[region, 0] + 60) % 180     # hue shift
    recolored = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    a_out = alpha_composite(face, recolored, hair_alpha)
    p_out = poisson_composite(face, recolored, hair_alpha)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(face); axes[0].set_title('Original'); axes[0].axis('off')
    axes[1].imshow(a_out); axes[1].set_title('Alpha (keeps new hue)'); axes[1].axis('off')
    axes[2].imshow(p_out); axes[2].set_title('Poisson (blends to lighting)'); axes[2].axis('off')
    plt.suptitle('Recolor hair, then composite two ways', fontsize=13)
    plt.tight_layout(); plt.show()
    print("Alpha preserves the exact new color; Poisson can wash strong recolors toward the")
    print("surrounding tone — choose per use-case (color change -> alpha; texture/style -> Poisson).")
except Exception as e:
    print(f"Install opencv-python to run this exercise ({e}).")

# %% [markdown]
# ### Exercise 6.2 — Mask dilation and its effect
#
# The hair mask boundary controls how much of the original is replaced. Experiment with
# **dilating** vs **eroding** the mask (e.g. `ndimage.binary_dilation`) before feathering.
# Composite each and observe: too tight leaves a halo of old hair; too loose eats into the
# face/background. Find a good amount for the synthetic demo and note why this matters more
# for diffusion (Route B) than for StyleGAN (Route A).

# %%
# TODO: dilate/erode the hair mask by a few pixels, feather, composite, compare
# Hint: ndimage.binary_dilation(mask, iterations=k) / binary_erosion(...)

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: mask dilation sweep
base_mask = (((xx - SZ/2)/(SZ*0.34))**2 + ((yy - SZ*0.30)/(SZ*0.26))**2 <= 1)

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for ax, k in zip(axes, [-6, 0, 6, 14]):
    if k < 0:
        m = ndimage.binary_erosion(base_mask, iterations=-k)
    elif k > 0:
        m = ndimage.binary_dilation(base_mask, iterations=k)
    else:
        m = base_mask
    a = clean_mask(m.astype(np.uint8), feather_sigma=5.0)
    comp = alpha_composite(face, hair_src, a)
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
# ## Key Takeaways & Where to Go Next
#
# - A hairstyle swap is a **pipeline**, not one model: **align -> mask -> generate -> blend**.
#   Each stage is a skill from earlier modules.
#
# - **Route A (StyleGAN latent blend):** globally coherent, great lighting/3D, but inversion
#   can soften identity and it regenerates the whole face.
#
# - **Route B (diffusion inpainting):** edits only the masked region so identity is preserved
#   perfectly; quality depends on the mask and the prompt/ControlNet condition. This is the
#   approach most modern tools use.
#
# - **The hair mask and the composite make or break realism** — feathering and Poisson
#   blending are what turn a "pasted wig" into a believable result. These run on your laptop.
#
# - **Out of scope (your next steps):** robustness to profile views and occluding hair,
#   explicit lighting/color transfer, temporal consistency for video, and dedicated methods
#   (Barbershop, HairCLIP, StyleYourHair, Stable-Hair) that combine these ideas with
#   purpose-built losses. You now have the foundation to read and reimplement those papers.
#
# ---
# 🎉 **You finished the Advanced Image AI track.** From "what is a pixel" (Module 11) to a
# full generative hairstyle-swap pipeline. The same four-skill template — locate, model,
# invert/condition, composite — underlies most image-editing AI.
