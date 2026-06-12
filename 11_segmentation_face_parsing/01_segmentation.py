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
# # Module 11.1 — Segmentation & Face Parsing
#
# **Purpose:** The first skill of the **Advanced Image AI track**: before you can change
# someone's hair you must know *which pixels are hair*. You build a U-Net from scratch,
# train it on a toy dataset, then run a real face parser — producing the **hair mask** that
# every later module, all the way to the hairstyle-swap capstone (Module 16), depends on.
#
# **Prerequisites:** Module 8 (CNNs).
#
# Welcome to the **Advanced Image AI** track. Modules 01–10 took you from NumPy to
# classifying images with CNNs. This track has one north star: **swap a person's hairstyle**
# — take person A's face and give them person B's hair, convincingly.
#
# That turns out to need four new skills, and this module builds the first one:
#
# 1. **Where is the hair / face?** ← *this module: segmentation & face parsing*
# 2. A generative model of faces (autoencoders → VAEs → GANs → StyleGAN) — Modules 12–14
# 3. Editing a *real* photo (GAN inversion) — Module 14
# 4. Region-targeted synthesis (diffusion inpainting) — Module 15
#
# Before you can change someone's hair you have to know **which pixels are hair**.
# Classification answers "what is in this image?". **Segmentation** answers a much finer
# question: "what is *this pixel*?" — every single pixel gets a label.
#
# **What you'll learn:**
# - The difference between classification, detection, and segmentation
# - The **U-Net** architecture (encoder–decoder with skip connections) — and build one from scratch
# - Train it on a synthetic shapes dataset (runs on a Mac in seconds)
# - Run a **pretrained** semantic segmentation model (DeepLabV3) on a real photo
# - **Face parsing**: how a model labels hair / skin / eyes / background, and how we turn
#   that into the **hair mask** the rest of this track depends on

# %%
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

import numpy as np
import matplotlib.pyplot as plt

# %matplotlib inline

torch.manual_seed(42)
np.random.seed(42)

# Use the best device available. On a Mac, "mps" is Apple's GPU backend (Metal).
# On a CUDA machine it picks the NVIDIA GPU. Otherwise CPU.
if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

print(f"PyTorch version: {torch.__version__}")
print(f"Using device: {device}")

# %% [markdown]
# ## 1. Classification vs. Segmentation
#
# Three levels of "understanding" an image, from coarse to fine:
#
# | Task | Question | Output |
# |------|----------|--------|
# | **Classification** (Module 08) | What's in this image? | one label per image (`"cat"`) |
# | **Object detection** | Where are the objects? | boxes + labels |
# | **Semantic segmentation** | What is *each pixel*? | a label per pixel (a "mask") |
#
# A segmentation model outputs an image-shaped grid of class scores. For an input of
# shape `(3, H, W)` and `C` classes, the output is `(C, H, W)` — at every pixel a vector
# of `C` scores. Take the `argmax` over classes and you get the **segmentation mask**:
# an `(H, W)` grid where each entry is the predicted class.
#
# **Face parsing** is just segmentation with face-specific classes: `background`, `skin`,
# `hair`, `left_eye`, `nose`, `upper_lip`, ... For us the prize is the `hair` class.

# %% [markdown]
# ## 2. A Synthetic Segmentation Dataset
#
# To learn the mechanics we don't need faces yet — we need a task where we *know* the
# correct mask. So we generate images on the fly: a random circle (the "object", class 1)
# on a noisy background (class 0). The mask is whatever pixels fall inside the circle.
#
# This trains in seconds on a laptop and makes the U-Net's job easy to verify by eye.

# %%
class ShapesDataset(Dataset):
    """Random circles on noisy backgrounds. Returns (image, mask).

    image: (1, H, W) float in [0, 1]
    mask:  (H, W) long, 0 = background, 1 = circle
    """

    def __init__(self, n_samples=512, size=64, seed=0):
        self.n_samples = n_samples
        self.size = size
        self.rng = np.random.default_rng(seed)
        # Pre-generate so __getitem__ is deterministic and fast
        self.images = []
        self.masks = []
        for _ in range(n_samples):
            img, msk = self._make_one()
            self.images.append(img)
            self.masks.append(msk)

    def _make_one(self):
        s = self.size
        # Noisy gray background
        img = self.rng.uniform(0.0, 0.3, size=(s, s)).astype(np.float32)

        # Random circle
        radius = self.rng.integers(s // 8, s // 4)
        cx = self.rng.integers(radius, s - radius)
        cy = self.rng.integers(radius, s - radius)
        yy, xx = np.ogrid[:s, :s]
        circle = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2

        # Circle is brighter than background
        img[circle] = self.rng.uniform(0.7, 1.0)
        mask = circle.astype(np.int64)
        return img, mask

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        img = torch.from_numpy(self.images[idx]).unsqueeze(0)  # (1, H, W)
        mask = torch.from_numpy(self.masks[idx])               # (H, W)
        return img, mask


# Build train / val sets
IMG_SIZE = 64
train_ds = ShapesDataset(n_samples=512, size=IMG_SIZE, seed=1)
val_ds = ShapesDataset(n_samples=128, size=IMG_SIZE, seed=2)

train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=16, shuffle=False)

# Peek at a few samples: image + its ground-truth mask
fig, axes = plt.subplots(2, 5, figsize=(12, 5))
for i in range(5):
    img, mask = train_ds[i]
    axes[0, i].imshow(img.squeeze(), cmap='gray', vmin=0, vmax=1)
    axes[0, i].set_title('Image')
    axes[0, i].axis('off')
    axes[1, i].imshow(mask, cmap='viridis', vmin=0, vmax=1)
    axes[1, i].set_title('Mask (target)')
    axes[1, i].axis('off')
plt.suptitle('Synthetic segmentation data: find the circle', fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. The U-Net Architecture
#
# Why not just stack conv layers like in Module 08? Two reasons segmentation is different:
#
# 1. **Output must be image-shaped.** Classification collapses everything to one vector.
#    Segmentation must produce a full-resolution `(C, H, W)` map.
# 2. **You need both context and precision.** To label a pixel you need the *big picture*
#    (is this region a face?) AND *fine detail* (exactly where the hair edge is).
#
# The **U-Net** (Ronneberger et al., 2015) solves both with a U-shaped design:
#
# ```
#   input ─► [down1] ─────────────skip─────────────► [up1] ─► output
#              │                                       ▲
#              ▼                                       │
#           [down2] ───────────skip───────────────► [up2]
#              │                                       ▲
#              ▼                                       │
#                          [bottleneck]
# ```
#
# - **Encoder (contracting path):** conv + downsample, repeatedly. Captures *context* but
#   loses spatial detail (gets smaller).
# - **Decoder (expanding path):** upsample + conv, back to full size.
# - **Skip connections:** the magic. Each decoder stage is handed the matching encoder
#   feature map (the "skip"), restoring the fine detail that downsampling threw away.
#
# Those skips are exactly why U-Nets give crisp edges — and crisp edges are what we need
# for a clean hair boundary later. (Fun fact: the U-Net's denoising descendant is the
# backbone of the diffusion models in Module 15.)

# %%
class DoubleConv(nn.Module):
    """(conv -> BN -> ReLU) x 2 — the basic U-Net block."""

    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNet(nn.Module):
    """A small U-Net for segmentation.

    in_channels: 1 for grayscale, 3 for RGB
    num_classes: number of output classes (2 here: background, circle)
    """

    def __init__(self, in_channels=1, num_classes=2, base=16):
        super().__init__()
        # --- Encoder ---
        self.down1 = DoubleConv(in_channels, base)        # 64x64
        self.down2 = DoubleConv(base, base * 2)           # 32x32
        self.pool = nn.MaxPool2d(2)

        # --- Bottleneck ---
        self.bottleneck = DoubleConv(base * 2, base * 4)  # 16x16

        # --- Decoder (upsample, then double-conv on concatenated skip) ---
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, kernel_size=2, stride=2)
        self.dec2 = DoubleConv(base * 4, base * 2)        # in = up2 + skip(down2)

        self.up1 = nn.ConvTranspose2d(base * 2, base, kernel_size=2, stride=2)
        self.dec1 = DoubleConv(base * 2, base)            # in = up1 + skip(down1)

        # 1x1 conv maps features -> per-pixel class scores
        self.head = nn.Conv2d(base, num_classes, kernel_size=1)

    def forward(self, x):
        # Encoder, keeping the skip outputs
        s1 = self.down1(x)               # (B, base,   64, 64)
        s2 = self.down2(self.pool(s1))   # (B, base*2, 32, 32)

        # Bottleneck
        b = self.bottleneck(self.pool(s2))  # (B, base*4, 16, 16)

        # Decoder: upsample, concatenate the matching skip, then conv
        d2 = self.up2(b)                       # (B, base*2, 32, 32)
        d2 = self.dec2(torch.cat([d2, s2], 1)) # concat along channels
        d1 = self.up1(d2)                      # (B, base, 64, 64)
        d1 = self.dec1(torch.cat([d1, s1], 1))

        return self.head(d1)             # (B, num_classes, 64, 64)


model = UNet(in_channels=1, num_classes=2, base=16).to(device)
total_params = sum(p.numel() for p in model.parameters())
print(model)
print(f"\nTotal parameters: {total_params:,}")

# Sanity check: feed a dummy batch and confirm the output shape is image-shaped
dummy = torch.randn(4, 1, IMG_SIZE, IMG_SIZE, device=device)
with torch.no_grad():
    out = model(dummy)
print(f"\nInput:  {tuple(dummy.shape)}")
print(f"Output: {tuple(out.shape)}  <- (batch, classes, H, W), same H,W as input")

# %% [markdown]
# ## 4. Training the U-Net
#
# Segmentation is **per-pixel classification**, so the loss is the same `CrossEntropyLoss`
# from Module 08 — PyTorch just applies it across every pixel automatically when the
# target is `(B, H, W)` and the prediction is `(B, C, H, W)`.
#
# We also track a second metric, **IoU** (Intersection over Union) — the standard
# segmentation score. For the object class: `IoU = overlap / union` between the predicted
# and true masks. 1.0 = perfect, 0 = no overlap.

# %%
def iou_score(preds, targets, cls=1):
    """Intersection-over-Union for a single class. preds/targets are (B, H, W) long."""
    pred_c = (preds == cls)
    targ_c = (targets == cls)
    inter = (pred_c & targ_c).sum().float()
    union = (pred_c | targ_c).sum().float()
    return (inter / union).item() if union > 0 else 1.0


def train_seg(model, train_loader, val_loader, epochs=8, lr=1e-3):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    history = {'train_loss': [], 'val_loss': [], 'val_iou': []}

    for epoch in range(epochs):
        # --- train ---
        model.train()
        running = 0.0
        for imgs, masks in train_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            logits = model(imgs)                 # (B, C, H, W)
            loss = criterion(logits, masks)      # masks: (B, H, W)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            running += loss.item() * imgs.size(0)
        train_loss = running / len(train_loader.dataset)

        # --- validate ---
        model.eval()
        v_running, v_iou, n = 0.0, 0.0, 0
        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                logits = model(imgs)
                v_running += criterion(logits, masks).item() * imgs.size(0)
                preds = logits.argmax(1)         # (B, H, W)
                v_iou += iou_score(preds, masks) * imgs.size(0)
                n += imgs.size(0)
        val_loss = v_running / n
        val_iou = v_iou / n

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_iou'].append(val_iou)
        print(f"Epoch {epoch+1}/{epochs}  "
              f"Train Loss: {train_loss:.4f}  Val Loss: {val_loss:.4f}  "
              f"Val IoU: {val_iou:.4f}")
    return history


print("Training U-Net on synthetic shapes...")
print("-" * 60)
history = train_seg(model, train_loader, val_loader, epochs=8)
print("-" * 60)
print(f"Final val IoU: {history['val_iou'][-1]:.4f} (1.0 = perfect overlap)")

# %%
# Plot the learning curves
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
epochs_range = range(1, len(history['train_loss']) + 1)
axes[0].plot(epochs_range, history['train_loss'], 'b-o', label='Train Loss')
axes[0].plot(epochs_range, history['val_loss'], 'r-o', label='Val Loss')
axes[0].set_xlabel('Epoch'); axes[0].set_ylabel('Loss')
axes[0].set_title('Loss'); axes[0].legend(); axes[0].grid(True, alpha=0.3)

axes[1].plot(epochs_range, history['val_iou'], 'g-o', label='Val IoU')
axes[1].set_xlabel('Epoch'); axes[1].set_ylabel('IoU')
axes[1].set_title('Validation IoU'); axes[1].legend(); axes[1].grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Look at the predictions
#
# The real test of a segmentation model is visual. We show, for a few validation images:
# the input, the ground-truth mask, and the model's predicted mask.

# %%
model.eval()
fig, axes = plt.subplots(3, 5, figsize=(13, 8))
with torch.no_grad():
    for i in range(5):
        img, mask = val_ds[i]
        logits = model(img.unsqueeze(0).to(device))
        pred = logits.argmax(1).squeeze().cpu()

        axes[0, i].imshow(img.squeeze(), cmap='gray', vmin=0, vmax=1)
        axes[0, i].set_title('Input'); axes[0, i].axis('off')
        axes[1, i].imshow(mask, cmap='viridis', vmin=0, vmax=1)
        axes[1, i].set_title('True mask'); axes[1, i].axis('off')
        axes[2, i].imshow(pred, cmap='viridis', vmin=0, vmax=1)
        axes[2, i].set_title('Predicted'); axes[2, i].axis('off')
plt.suptitle('U-Net predictions on validation set', fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# That's the entire mechanism behind face parsing — only the data and the number of
# classes change. Real face-parsing models are bigger U-Net-like networks trained on
# datasets like **CelebAMask-HQ** (30,000 faces, each hand-labeled into 19 regions).
# Training one from scratch needs a GPU and hours, so next we use a **pretrained** model.

# %% [markdown]
# ## 5. A Pretrained Segmentation Model (real photos)
#
# `torchvision` ships pretrained segmentation models. **DeepLabV3** trained on COCO/VOC
# can segment 21 classes including `person`. It's not hair-specific, but it's a one-liner
# to download and it shows the exact same `argmax` over `(C, H, W)` logits on a *real* image.
#
# > **Note:** the first run downloads ~160 MB of weights. Works on CPU/MPS (inference only).

# %%
import torchvision
from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights
import torchvision.transforms.functional as TF
from PIL import Image
import urllib.request
import io

# Load pretrained DeepLabV3 (downloads weights on first run)
weights = DeepLabV3_ResNet50_Weights.DEFAULT
seg_model = deeplabv3_resnet50(weights=weights).eval().to(device)
preprocess = weights.transforms()
voc_classes = weights.meta["categories"]  # index -> class name
PERSON_IDX = voc_classes.index("person")
print(f"Loaded DeepLabV3. 'person' is class index {PERSON_IDX} of {len(voc_classes)}.")


def load_image_from_url(url, size=384):
    """Fetch an image and return it as a PIL RGB image (resized)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        img = Image.open(io.BytesIO(resp.read())).convert("RGB")
    return img.resize((size, size))


# A public-domain portrait from Wikimedia Commons (Marie Curie, 1920).
# (If you're offline, replace this with: Image.open("your_photo.jpg").convert("RGB"))
PORTRAIT_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/"
    "7/7e/Marie_Curie_c1920.jpg/500px-Marie_Curie_c1920.jpg"
)

try:
    portrait = load_image_from_url(PORTRAIT_URL)
    have_image = True
except Exception as e:
    print(f"Could not download the sample image ({e}).")
    print("Replace PORTRAIT_URL or load a local file to run this section.")
    have_image = False

# %%
if have_image:
    # Preprocess -> run model -> argmax over classes
    x = preprocess(portrait).unsqueeze(0).to(device)
    with torch.no_grad():
        out = seg_model(x)["out"][0]          # (num_classes, H, W)
    seg = out.argmax(0).cpu().numpy()         # (H, W) class indices

    # Person mask = pixels labelled "person"
    person_mask = (seg == PERSON_IDX).astype(np.uint8)

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    axes[0].imshow(portrait); axes[0].set_title('Input photo'); axes[0].axis('off')
    axes[1].imshow(seg, cmap='tab20'); axes[1].set_title('Semantic segmentation'); axes[1].axis('off')
    # Overlay the person mask in red on top of the photo
    overlay = np.array(portrait.resize(person_mask.shape[::-1])).copy()
    overlay[person_mask == 1] = (0.5 * overlay[person_mask == 1] +
                                 0.5 * np.array([255, 0, 0])).astype(np.uint8)
    axes[2].imshow(overlay); axes[2].set_title('Person mask (red)'); axes[2].axis('off')
    plt.suptitle('Pretrained DeepLabV3 on a real photo', fontsize=14)
    plt.tight_layout()
    plt.show()

# %% [markdown]
# ## 6. Face Parsing — getting the *hair* mask
#
# DeepLabV3 gives us `person`, but for a hairstyle swap we need the **hair** region alone.
# That requires a model trained specifically on face regions. The standard choice is
# **BiSeNet** trained on **CelebAMask-HQ**, which labels 19 classes:
#
# ```
#  0 background   1 skin      2 l_brow    3 r_brow    4 l_eye     5 r_eye
#  6 eye_glasses  7 l_ear     8 r_ear     9 ear_ring  10 nose     11 mouth
#  12 u_lip       13 l_lip    14 neck     15 neck_l   16 cloth    17 HAIR
#  18 hat
# ```
#
# Class **17 = hair**. The model is the same idea you just built — an encoder–decoder that
# outputs `(19, H, W)` logits — only larger and trained on real faces. It isn't packaged in
# `torchvision`, so you grab the public weights once:
#
# ```bash
# # In the repo root (one-time setup for this section):
# git clone https://github.com/zllrunning/face-parsing.PyTorch.git
# # Download the pretrained checkpoint (79999_iter.pth, ~50 MB) from the repo's
# # README link into face-parsing.PyTorch/res/cp/
# ```
#
# The code below shows exactly how you'd use it. It's wrapped in a guard so the notebook
# still runs end-to-end if the weights aren't present yet.

# %%
import os, sys

FACE_PARSING_DIR = "face-parsing.PyTorch"
CHECKPOINT = os.path.join(FACE_PARSING_DIR, "res", "cp", "79999_iter.pth")
HAIR_CLASS = 17


def face_parse(pil_img, device):
    """Run BiSeNet face parsing. Returns an (H, W) array of class indices (0..18).

    Requires the face-parsing.PyTorch repo + checkpoint (see the markdown above).
    """
    sys.path.insert(0, FACE_PARSING_DIR)
    from model import BiSeNet  # provided by the cloned repo

    net = BiSeNet(n_classes=19).to(device)
    net.load_state_dict(torch.load(CHECKPOINT, map_location=device))
    net.eval()

    img = pil_img.resize((512, 512))
    x = TF.to_tensor(img)
    x = TF.normalize(x, (0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
    x = x.unsqueeze(0).to(device)
    with torch.no_grad():
        parsing = net(x)[0].argmax(1).squeeze().cpu().numpy()  # (512, 512)
    return parsing


if have_image and os.path.exists(CHECKPOINT):
    parsing = face_parse(portrait, device)
    hair_mask = (parsing == HAIR_CLASS).astype(np.uint8)

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    axes[0].imshow(portrait.resize((512, 512))); axes[0].set_title('Input'); axes[0].axis('off')
    axes[1].imshow(parsing, cmap='tab20'); axes[1].set_title('Face parsing (19 classes)'); axes[1].axis('off')
    axes[2].imshow(hair_mask, cmap='gray'); axes[2].set_title('Hair mask (class 17)'); axes[2].axis('off')
    plt.suptitle('Face parsing -> hair mask', fontsize=14)
    plt.tight_layout()
    plt.show()
else:
    print("Face-parsing checkpoint not found — skipping the live hair-mask demo.")
    print(f"Expected at: {CHECKPOINT}")
    print("Follow the setup in the markdown cell above to enable this section.")
    print("\nThe synthetic U-Net you trained above already shows the full mechanism;")
    print("BiSeNet is the same idea scaled up to 19 face classes.")

# %% [markdown]
# ## 7. Exercises
#
# ### Exercise 7.1 — Two shapes, three classes
#
# Extend `ShapesDataset` to draw **both** a circle (class 1) and a square (class 2) on each
# image. Retrain the U-Net with `num_classes=3` and report the per-class IoU. You'll need to:
# 1. Add a square to `_make_one` (carve out a rectangular region in the mask = class 2)
# 2. Build the model with `UNet(in_channels=1, num_classes=3)`
# 3. Generalize `iou_score` to average over classes 1 and 2

# %%
# TODO: build a 3-class dataset and retrain the U-Net
# Hint: a square mask is `mask[y0:y1, x0:x1] = 2` for a random box that doesn't
#       overlap the circle. Keep IMG_SIZE small (64) so it stays fast.

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: three-class segmentation (background / circle / square)

class TwoShapesDataset(Dataset):
    def __init__(self, n_samples=512, size=64, seed=0):
        self.n_samples = n_samples
        self.size = size
        self.rng = np.random.default_rng(seed)
        self.images, self.masks = [], []
        for _ in range(n_samples):
            img, msk = self._make_one()
            self.images.append(img)
            self.masks.append(msk)

    def _make_one(self):
        s = self.size
        img = self.rng.uniform(0.0, 0.3, size=(s, s)).astype(np.float32)
        mask = np.zeros((s, s), dtype=np.int64)

        # Circle (class 1) in the left half
        r = self.rng.integers(s // 10, s // 6)
        cx = self.rng.integers(r, s // 2 - r)
        cy = self.rng.integers(r, s - r)
        yy, xx = np.ogrid[:s, :s]
        circle = (xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2
        img[circle] = self.rng.uniform(0.7, 1.0)
        mask[circle] = 1

        # Square (class 2) in the right half
        side = self.rng.integers(s // 8, s // 5)
        x0 = self.rng.integers(s // 2, s - side)
        y0 = self.rng.integers(0, s - side)
        img[y0:y0 + side, x0:x0 + side] = self.rng.uniform(0.7, 1.0)
        mask[y0:y0 + side, x0:x0 + side] = 2
        return img, mask

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        return (torch.from_numpy(self.images[idx]).unsqueeze(0),
                torch.from_numpy(self.masks[idx]))


def mean_iou(preds, targets, classes=(1, 2)):
    return float(np.mean([iou_score(preds, targets, cls=c) for c in classes]))


tr = DataLoader(TwoShapesDataset(512, IMG_SIZE, seed=1), batch_size=16, shuffle=True)
va_ds = TwoShapesDataset(128, IMG_SIZE, seed=2)
va = DataLoader(va_ds, batch_size=16, shuffle=False)

model3 = UNet(in_channels=1, num_classes=3, base=16).to(device)
crit = nn.CrossEntropyLoss()
opt = optim.Adam(model3.parameters(), lr=1e-3)

print("Training 3-class U-Net...")
for epoch in range(8):
    model3.train()
    for imgs, masks in tr:
        imgs, masks = imgs.to(device), masks.to(device)
        loss = crit(model3(imgs), masks)
        opt.zero_grad(); loss.backward(); opt.step()

# Per-class IoU on validation
model3.eval()
ious = {1: [], 2: []}
with torch.no_grad():
    for imgs, masks in va:
        imgs, masks = imgs.to(device), masks.to(device)
        preds = model3(imgs).argmax(1)
        for c in (1, 2):
            ious[c].append(iou_score(preds, masks, cls=c))
print(f"Circle (class 1) IoU: {np.mean(ious[1]):.4f}")
print(f"Square (class 2) IoU: {np.mean(ious[2]):.4f}")

# Visualize
fig, axes = plt.subplots(3, 5, figsize=(13, 8))
with torch.no_grad():
    for i in range(5):
        img, mask = va_ds[i]
        pred = model3(img.unsqueeze(0).to(device)).argmax(1).squeeze().cpu()
        axes[0, i].imshow(img.squeeze(), cmap='gray'); axes[0, i].set_title('Input'); axes[0, i].axis('off')
        axes[1, i].imshow(mask, cmap='viridis', vmin=0, vmax=2); axes[1, i].set_title('True'); axes[1, i].axis('off')
        axes[2, i].imshow(pred, cmap='viridis', vmin=0, vmax=2); axes[2, i].set_title('Pred'); axes[2, i].axis('off')
plt.suptitle('3-class segmentation: circle + square', fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Exercise 7.2 — Clean up a mask (post-processing)
#
# Raw masks are often jagged or have stray pixels. For the hairstyle swap we'll want a
# **smooth, hole-free** hair mask. Write a function that takes a binary mask and:
# 1. Removes small isolated blobs (keep only the largest connected component)
# 2. Fills internal holes
# 3. Slightly **feathers** (blurs) the edge so compositing later looks natural
#
# Use `scipy.ndimage` (label, binary_fill_holes) and a Gaussian blur. Apply it to the
# circle mask predicted by your trained `model` and show before/after.

# %%
# TODO: write clean_mask(mask) and show before/after on a predicted circle mask
# Hint: from scipy import ndimage
#       - ndimage.label(mask) gives connected components
#       - ndimage.binary_fill_holes(mask) fills holes
#       - ndimage.gaussian_filter(mask.astype(float), sigma) feathers the edge

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: mask cleanup
from scipy import ndimage


def clean_mask(mask, feather_sigma=1.5):
    """Keep largest component, fill holes, feather the edge.

    Returns a float mask in [0, 1] (feathered alpha)."""
    m = mask.astype(bool)

    # 1. Largest connected component
    labels, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, labels, range(1, n + 1))
        m = labels == (np.argmax(sizes) + 1)

    # 2. Fill internal holes
    m = ndimage.binary_fill_holes(m)

    # 3. Feather the edge for soft compositing
    soft = ndimage.gaussian_filter(m.astype(float), sigma=feather_sigma)
    return np.clip(soft, 0, 1)


# Predict a circle mask, add some synthetic noise, then clean it
model.eval()
img, _ = val_ds[3]
with torch.no_grad():
    raw = model(img.unsqueeze(0).to(device)).argmax(1).squeeze().cpu().numpy()

# Inject stray pixels to simulate a messy real-world mask
noisy = raw.copy()
ys = np.random.randint(0, IMG_SIZE, 20)
xs = np.random.randint(0, IMG_SIZE, 20)
noisy[ys, xs] = 1

cleaned = clean_mask(noisy)

fig, axes = plt.subplots(1, 3, figsize=(12, 4))
axes[0].imshow(noisy, cmap='gray'); axes[0].set_title('Raw (with stray pixels)'); axes[0].axis('off')
axes[1].imshow(cleaned, cmap='gray'); axes[1].set_title('Cleaned + feathered'); axes[1].axis('off')
axes[2].imshow(img.squeeze(), cmap='gray'); axes[2].imshow(cleaned, cmap='Reds', alpha=0.4)
axes[2].set_title('Overlay'); axes[2].axis('off')
plt.tight_layout()
plt.show()
print("This clean_mask() is exactly the kind of post-processing we'll reuse on the")
print("hair mask in the Module 16 capstone for a seamless composite.")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Segmentation = per-pixel classification** | Output is `(C, H, W)` logits; `argmax` over the class dim gives the mask; loss is plain per-pixel `CrossEntropyLoss` |
# | **U-Net** | The workhorse: encoder for context, decoder for resolution, **skip connections** to recover the fine detail lost during downsampling |
# | **IoU** | The standard metric — accuracy alone is misleading when one class dominates the image |
# | **Face parsing** | Segmentation with face-specific classes; BiSeNet on CelebAMask-HQ labels 19 regions, and **class 17 is hair** — the mask this track is built on |
# | **Mask post-processing** | Largest component, fill holes, feather — turns a raw prediction into something you can composite cleanly; reused in the capstone |
#
# ## Further reading
#
# - **U-Net paper** (Convolutional Networks for Biomedical Image Segmentation — the
#   original encoder–decoder with skips): https://arxiv.org/abs/1505.04597
# - **CelebAMask-HQ** (the face-parsing dataset and its 19 classes):
#   https://github.com/switchablenorms/CelebAMask-HQ
# - **CS231n** (Stanford's computer vision course; detection & segmentation lectures):
#   https://cs231n.stanford.edu/
#
# **Next:** [Autoencoders & VAEs →](../12_autoencoders_vae/01_autoencoders_vae.ipynb) —
# build a generative model of images and meet the *latent space* where hair editing happens.
