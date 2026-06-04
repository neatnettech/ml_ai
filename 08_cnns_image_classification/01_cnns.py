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
# # Module 8.1 — CNNs & Image Classification
#
# Convolutional Neural Networks (CNNs) are the workhorse of modern computer vision.
# They power everything from phone cameras that recognize faces to medical imaging
# systems that detect tumors.
#
# **What you'll learn:**
# - Why CNNs exist and what problem they solve
# - The key building blocks: convolutional layers, pooling, and fully connected layers
# - How to build and train a CNN on MNIST with PyTorch
# - Visualizing what the network learns
# - Data augmentation and transfer learning concepts

# %%
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader

import torchvision
import torchvision.transforms as transforms
import torchvision.models as models

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# %matplotlib inline

# For reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"PyTorch version: {torch.__version__}")
print(f"Using device: {device}")

# %% [markdown]
# ## 1. Why CNNs?
#
# ### Images Are Grids of Pixels
#
# A grayscale image is just a 2D grid of numbers (pixel intensities, usually 0-255).
# A color image has 3 such grids (Red, Green, Blue channels), making it a 3D tensor
# of shape `(channels, height, width)`.
#
# For example, MNIST digits are 28x28 grayscale images = 784 pixels each.
#
# ### The Problem with Fully Connected Networks
#
# In Module 7, we used fully connected (dense) layers where every neuron connects
# to every input. For a tiny 28x28 image, that's 784 inputs — manageable. But for
# a modest 224x224 color image:
#
# - Input size: 224 x 224 x 3 = **150,528** values
# - First hidden layer with 1000 neurons: 150,528 x 1000 = **150 million** parameters!
#
# That's way too many parameters. The model would overfit badly and train slowly.
#
# ### CNNs Use Local Patterns
#
# CNNs solve this by exploiting two key insights about images:
#
# 1. **Locality**: Nearby pixels are related. An edge or texture is a *local* pattern.
#    A small filter (e.g., 3x3) can detect it without looking at the whole image.
#
# 2. **Translation invariance**: A cat's ear looks the same whether it's in the top-left
#    or bottom-right of the image. The same filter can be reused everywhere.
#
# This means CNNs use far fewer parameters while being better at image tasks.

# %%
# Let's see what an image looks like as numbers
# Create a simple 8x8 "image" with a vertical edge
simple_image = np.zeros((8, 8))
simple_image[:, 4:] = 1.0  # right half is white

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

axes[0].imshow(simple_image, cmap='gray', vmin=0, vmax=1)
axes[0].set_title('Image (visual)')
axes[0].axis('off')

# Show the actual numbers
axes[1].imshow(simple_image, cmap='gray', vmin=0, vmax=1)
for i in range(8):
    for j in range(8):
        axes[1].text(j, i, f'{simple_image[i, j]:.0f}',
                     ha='center', va='center', color='red', fontsize=10)
axes[1].set_title('Image (as numbers)')
axes[1].axis('off')

plt.suptitle('An image is just a grid of numbers', fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 2. Key Building Blocks
#
# A CNN is built from three main types of layers:
#
# 1. **Convolutional layers** — detect local patterns (edges, textures, shapes)
# 2. **Pooling layers** — downsample to reduce size and add some translation invariance
# 3. **Fully connected layers** — combine detected features to make final predictions
#
# ### 2.1 Convolutional Layers
#
# A convolutional layer slides a small **filter** (also called a **kernel**) across
# the image. At each position, it computes the element-wise product between the filter
# and the image patch, then sums the result. This produces a single number in the
# output (called a **feature map**).
#
# Think of it like a magnifying glass scanning across the image, looking for a
# specific pattern at each location.

# %%
# Let's manually apply a 3x3 filter to see how convolution works

# A simple 6x6 image with a vertical edge
image = np.array([
    [0, 0, 0, 1, 1, 1],
    [0, 0, 0, 1, 1, 1],
    [0, 0, 0, 1, 1, 1],
    [0, 0, 0, 1, 1, 1],
    [0, 0, 0, 1, 1, 1],
    [0, 0, 0, 1, 1, 1]
], dtype=np.float32)

# A vertical edge detector filter
# This filter has negative values on the left and positive on the right.
# When placed over a vertical edge (dark-to-light transition), the products
# on the right side are positive and the left side are zero, giving a high sum.
vertical_edge_filter = np.array([
    [-1, 0, 1],
    [-1, 0, 1],
    [-1, 0, 1]
], dtype=np.float32)

# Manually compute convolution (no padding, stride=1)
output_h = image.shape[0] - vertical_edge_filter.shape[0] + 1  # 6 - 3 + 1 = 4
output_w = image.shape[1] - vertical_edge_filter.shape[1] + 1
output = np.zeros((output_h, output_w))

for i in range(output_h):
    for j in range(output_w):
        # Extract the patch under the filter
        patch = image[i:i+3, j:j+3]
        # Element-wise multiply and sum
        output[i, j] = np.sum(patch * vertical_edge_filter)

print("Input image (6x6):")
print(image)
print(f"\nFilter (3x3): vertical edge detector")
print(vertical_edge_filter)
print(f"\nOutput feature map ({output_h}x{output_w}):")
print(output)

# Visualize
fig, axes = plt.subplots(1, 3, figsize=(12, 3))
axes[0].imshow(image, cmap='gray')
axes[0].set_title('Input Image')
axes[1].imshow(vertical_edge_filter, cmap='RdBu', vmin=-1, vmax=1)
axes[1].set_title('Filter (edge detector)')
axes[2].imshow(output, cmap='gray')
axes[2].set_title('Output (detected edge)')
for ax in axes:
    ax.axis('off')
plt.tight_layout()
plt.show()

# %% [markdown]
# Notice how the output highlights *where* the vertical edge is. The column of 3s
# corresponds to the position where the filter found the dark-to-light transition.
#
# **Key parameters of a convolutional layer:**
# - **Number of filters** (e.g., 32): Each filter learns to detect a different pattern.
#   More filters = more patterns detected.
# - **Filter size** (e.g., 3x3): How large a patch each filter looks at.
#   3x3 is the most common choice.
# - **Stride**: How many pixels the filter moves at each step. Stride=1 means it
#   slides one pixel at a time. Stride=2 skips every other position (downsamples).
# - **Padding**: Adding zeros around the image border so the output keeps the same
#   spatial size as the input.
#
# In PyTorch: `nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding)`

# %% [markdown]
# ### 2.2 Pooling Layers
#
# After convolution, we often use **pooling** to reduce the spatial dimensions.
# The most common is **max pooling**: take the maximum value in each small window.
#
# Why pool?
# - **Reduces computation** — smaller feature maps mean fewer parameters downstream
# - **Adds translation invariance** — if the feature shifts by a pixel or two, the
#   max in the window stays roughly the same
#
# In PyTorch: `nn.MaxPool2d(kernel_size)` — typically `kernel_size=2` halves each dimension.

# %%
# Max pooling example
feature_map = np.array([
    [1, 3, 2, 4],
    [5, 6, 1, 2],
    [3, 2, 8, 1],
    [7, 4, 5, 3]
], dtype=np.float32)

# Max pooling with 2x2 window, stride 2
pooled = np.zeros((2, 2))
for i in range(2):
    for j in range(2):
        window = feature_map[i*2:i*2+2, j*2:j*2+2]
        pooled[i, j] = window.max()

print("Feature map (4x4):")
print(feature_map)
print("\nAfter 2x2 max pooling (2x2):")
print(pooled)
print("\nEach output is the max of its 2x2 window:")
print(f"  Top-left:  max(1,3,5,6) = {pooled[0,0]:.0f}")
print(f"  Top-right: max(2,4,1,2) = {pooled[0,1]:.0f}")
print(f"  Bot-left:  max(3,2,7,4) = {pooled[1,0]:.0f}")
print(f"  Bot-right: max(8,1,5,3) = {pooled[1,1]:.0f}")

# %% [markdown]
# ### 2.3 Flatten + Fully Connected Layers
#
# After several rounds of convolution and pooling, the feature maps are small but
# have many channels (e.g., 7x7 with 64 channels). We **flatten** them into a 1D
# vector and feed it into one or more **fully connected (linear) layers** to produce
# the final class predictions.
#
# ```
# Input Image (1x28x28)
#     |  Conv2d + ReLU
# Feature Maps (32x26x26)
#     |  MaxPool2d
# Feature Maps (32x13x13)
#     |  Conv2d + ReLU
# Feature Maps (64x11x11)
#     |  MaxPool2d
# Feature Maps (64x5x5)
#     |  Flatten
# Vector (1600)
#     |  Linear + ReLU
# Vector (128)
#     |  Linear
# Output (10 classes)
# ```
#
# This is the architecture we will build for MNIST.

# %% [markdown]
# ## 3. MNIST with PyTorch
#
# Let's put it all together and build a CNN to classify handwritten digits.
# MNIST has 60,000 training images and 10,000 test images, each 28x28 grayscale.
#
# ### 3.1 Load and Explore the Data

# %%
# Define transforms — convert images to tensors and normalize
# ToTensor() converts pixel values from [0, 255] to [0.0, 1.0]
# Normalize() then shifts to mean=0.5, std=0.5 so values are in [-1, 1]
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))  # MNIST mean and std
])

# Download MNIST
train_dataset = torchvision.datasets.MNIST(
    root='./data', train=True, download=True, transform=transform
)
test_dataset = torchvision.datasets.MNIST(
    root='./data', train=False, download=True, transform=transform
)

print(f"Training samples: {len(train_dataset)}")
print(f"Test samples:     {len(test_dataset)}")

# Look at one sample
image, label = train_dataset[0]
print(f"\nImage shape: {image.shape}")  # (1, 28, 28) — 1 channel, 28x28
print(f"Label: {label}")
print(f"Pixel value range: [{image.min():.2f}, {image.max():.2f}]")

# %%
# Visualize some sample digits
fig, axes = plt.subplots(2, 8, figsize=(14, 4))
for i, ax in enumerate(axes.flat):
    image, label = train_dataset[i]
    # image is (1, 28, 28), squeeze to (28, 28) for plotting
    ax.imshow(image.squeeze(), cmap='gray')
    ax.set_title(f'Label: {label}')
    ax.axis('off')
plt.suptitle('Sample MNIST Digits', fontsize=14)
plt.tight_layout()
plt.show()

# %%
# Create data loaders — these handle batching, shuffling, and parallel loading
BATCH_SIZE = 64

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

# Check a batch
images, labels = next(iter(train_loader))
print(f"Batch of images shape: {images.shape}")  # (64, 1, 28, 28)
print(f"Batch of labels shape: {labels.shape}")  # (64,)


# %% [markdown]
# ### 3.2 Build the CNN
#
# Our CNN architecture:
#
# | Layer | Input Shape | Output Shape | What it does |
# |-------|-------------|--------------|-------------|
# | Conv2d(1, 32, 3) | (1, 28, 28) | (32, 26, 26) | 32 filters detect basic patterns (edges, corners) |
# | ReLU | (32, 26, 26) | (32, 26, 26) | Non-linearity |
# | MaxPool2d(2) | (32, 26, 26) | (32, 13, 13) | Downsample by 2x |
# | Conv2d(32, 64, 3) | (32, 13, 13) | (64, 11, 11) | 64 filters detect higher-level patterns |
# | ReLU | (64, 11, 11) | (64, 11, 11) | Non-linearity |
# | MaxPool2d(2) | (64, 11, 11) | (64, 5, 5) | Downsample by 2x |
# | Flatten | (64, 5, 5) | (1600,) | Reshape to 1D |
# | Linear(1600, 128) | (1600,) | (128,) | Combine features |
# | ReLU | (128,) | (128,) | Non-linearity |
# | Linear(128, 10) | (128,) | (10,) | Output one score per digit class |

# %%
class MNISTNet(nn.Module):
    """A simple CNN for MNIST digit classification."""

    def __init__(self):
        super().__init__()
        # First convolutional block
        # in_channels=1 (grayscale), out_channels=32 (learn 32 filters)
        # kernel_size=3 (each filter is 3x3)
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3)
        self.pool = nn.MaxPool2d(kernel_size=2)  # halve spatial dims

        # Second convolutional block
        # in_channels=32 (from previous layer), out_channels=64
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)

        # Fully connected layers
        # After conv1 + pool: (32, 13, 13)
        # After conv2 + pool: (64, 5, 5) = 1600 values
        self.fc1 = nn.Linear(64 * 5 * 5, 128)
        self.fc2 = nn.Linear(128, 10)  # 10 digit classes

    def forward(self, x):
        # x shape: (batch_size, 1, 28, 28)
        x = self.pool(F.relu(self.conv1(x)))  # -> (batch, 32, 13, 13)
        x = self.pool(F.relu(self.conv2(x)))  # -> (batch, 64, 5, 5)
        x = x.view(x.size(0), -1)             # -> (batch, 1600)  (flatten)
        x = F.relu(self.fc1(x))               # -> (batch, 128)
        x = self.fc2(x)                       # -> (batch, 10)
        return x


# Create the model and move to device
model = MNISTNet().to(device)
print(model)

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
print(f"\nTotal parameters: {total_params:,}")
print("Compare this to a fully connected network with the same input:")
print(f"  FC first layer alone: {784 * 128:,} = {784*128:,} parameters")


# %% [markdown]
# ### 3.3 Training Loop
#
# We train using:
# - **CrossEntropyLoss**: Standard loss for multi-class classification.
#   It combines LogSoftmax + NLLLoss in one step.
# - **Adam optimizer**: An adaptive learning rate optimizer that works well out of
#   the box for most problems.

# %%
def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train the model for one epoch and return average loss and accuracy."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)

        # Backward pass and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Track statistics
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


def evaluate(model, loader, criterion, device):
    """Evaluate the model and return average loss and accuracy."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():  # no gradients needed for evaluation
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    return running_loss / total, correct / total


# %%
# Training configuration
NUM_EPOCHS = 5
LEARNING_RATE = 0.001

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# Training history
history = {
    'train_loss': [], 'train_acc': [],
    'val_loss': [], 'val_acc': []
}

print("Training CNN on MNIST...")
print("-" * 60)

for epoch in range(NUM_EPOCHS):
    train_loss, train_acc = train_one_epoch(
        model, train_loader, criterion, optimizer, device
    )
    val_loss, val_acc = evaluate(
        model, test_loader, criterion, device
    )

    history['train_loss'].append(train_loss)
    history['train_acc'].append(train_acc)
    history['val_loss'].append(val_loss)
    history['val_acc'].append(val_acc)

    print(f"Epoch {epoch+1}/{NUM_EPOCHS}  "
          f"Train Loss: {train_loss:.4f}  Train Acc: {train_acc:.4f}  "
          f"Val Loss: {val_loss:.4f}  Val Acc: {val_acc:.4f}")

print("-" * 60)
print(f"Final test accuracy: {history['val_acc'][-1]:.4f}")

# %%
# Plot training history
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

epochs = range(1, NUM_EPOCHS + 1)

# Loss
axes[0].plot(epochs, history['train_loss'], 'b-o', label='Train Loss')
axes[0].plot(epochs, history['val_loss'], 'r-o', label='Val Loss')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].set_title('Training & Validation Loss')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Accuracy
axes[1].plot(epochs, history['train_acc'], 'b-o', label='Train Acc')
axes[1].plot(epochs, history['val_acc'], 'r-o', label='Val Acc')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].set_title('Training & Validation Accuracy')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# %% [markdown]
# ### 3.4 Evaluate on Test Set — Confusion Matrix
#
# A confusion matrix shows which digits the model confuses with each other.
# The diagonal shows correct predictions; off-diagonal shows mistakes.

# %%
# Collect all predictions
model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for images, labels in test_loader:
        images = images.to(device)
        outputs = model(images)
        _, predicted = outputs.max(1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.numpy())

all_preds = np.array(all_preds)
all_labels = np.array(all_labels)

# Confusion matrix
cm = confusion_matrix(all_labels, all_preds)

fig, ax = plt.subplots(figsize=(8, 8))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=range(10))
disp.plot(ax=ax, cmap='Blues', values_format='d')
ax.set_title('MNIST Confusion Matrix')
plt.tight_layout()
plt.show()

# Per-class accuracy
print("Per-class accuracy:")
for digit in range(10):
    mask = all_labels == digit
    acc = (all_preds[mask] == digit).mean()
    print(f"  Digit {digit}: {acc:.4f} ({mask.sum()} samples)")

# %% [markdown]
# ### Exercise 3.1
#
# Show some **misclassified** examples. Find test images where the model's prediction
# differs from the true label, and display them with both the predicted and true labels.

# %%
# TODO: Find and display 10 misclassified images
# Hint:
#   1. Find indices where all_preds != all_labels
#   2. Use test_dataset[idx] to get the image
#   3. Plot with true label and predicted label as title

# Your code here
...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
misclassified = np.where(all_preds != all_labels)[0]
print(f"Total misclassified: {len(misclassified)} out of {len(all_labels)}")

fig, axes = plt.subplots(2, 5, figsize=(14, 6))
for i, ax in enumerate(axes.flat):
    idx = misclassified[i]
    image, true_label = test_dataset[idx]
    ax.imshow(image.squeeze(), cmap='gray')
    ax.set_title(f'True: {true_label}, Pred: {all_preds[idx]}', color='red')
    ax.axis('off')
plt.suptitle('Misclassified Examples', fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 4. Visualizing What the CNN Learns
#
# One way to peek inside a CNN is to look at the **learned filter weights** in the
# first convolutional layer. Since this layer operates directly on the input image,
# its filters are interpretable — they look for basic patterns like edges at various
# orientations, corners, and simple textures.

# %%
# Extract first-layer filter weights
# conv1 weight shape: (32, 1, 3, 3) — 32 filters, 1 input channel, 3x3 each
filters = model.conv1.weight.data.cpu().numpy()
print(f"Filter weights shape: {filters.shape}")

# Plot all 32 filters as small images
fig, axes = plt.subplots(4, 8, figsize=(12, 6))
for i, ax in enumerate(axes.flat):
    # Each filter is (1, 3, 3), squeeze to (3, 3)
    filt = filters[i, 0]
    ax.imshow(filt, cmap='RdBu', vmin=filt.min(), vmax=filt.max())
    ax.set_title(f'Filter {i}', fontsize=8)
    ax.axis('off')

plt.suptitle('First Convolutional Layer — Learned 3x3 Filters', fontsize=14)
plt.tight_layout()
plt.show()

print("\nRed = positive weight (excitatory), Blue = negative weight (inhibitory)")
print("These filters detect basic patterns like horizontal/vertical edges and corners.")

# %% [markdown]
# ## 5. Data Augmentation
#
# **Data augmentation** artificially increases the size and diversity of your training
# set by applying random transformations to each image during training. This helps the
# model generalize better because it sees more variation.
#
# Common augmentations for images:
# - **RandomRotation**: Rotate by a random angle
# - **RandomHorizontalFlip**: Mirror the image left-right (not for digits, but great for photos)
# - **RandomCrop**: Crop a random sub-region
# - **ColorJitter**: Randomly change brightness, contrast, etc.
#
# Important: Augmentation is applied **only during training**, never during evaluation.

# %%
# Define augmentation transforms
augmentation_transform = transforms.Compose([
    transforms.RandomRotation(15),            # rotate up to 15 degrees
    transforms.RandomAffine(
        degrees=0, translate=(0.1, 0.1)       # shift up to 10% in x/y
    ),
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

# Load one image without normalization to show augmented versions
show_transform = transforms.Compose([
    transforms.RandomRotation(15),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ToTensor()
])

# Get a raw MNIST image (without transforms)
raw_dataset = torchvision.datasets.MNIST(
    root='./data', train=True, download=True, transform=None
)
original_image, label = raw_dataset[0]  # PIL Image

# Show original and several augmented versions
fig, axes = plt.subplots(2, 5, figsize=(12, 5))
axes[0, 0].imshow(original_image, cmap='gray')
axes[0, 0].set_title(f'Original ({label})')
axes[0, 0].axis('off')

for i, ax in enumerate(axes.flat[1:]):
    augmented = show_transform(original_image)
    ax.imshow(augmented.squeeze(), cmap='gray')
    ax.set_title(f'Augmented {i+1}')
    ax.axis('off')

plt.suptitle('Data Augmentation: Same Image, Different Random Transforms', fontsize=14)
plt.tight_layout()
plt.show()

print("Each time we load this image during training, we get a slightly different")
print("version. This helps the model learn to be robust to small variations.")

# %%
# For photos (not digits), horizontal flipping is very useful
photo_transforms = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),   # 50% chance to flip
    transforms.RandomRotation(10),
    transforms.ColorJitter(
        brightness=0.2, contrast=0.2           # slight color changes
    ),
    transforms.ToTensor(),
])

print("Example photo augmentation pipeline:")
print(photo_transforms)
print("\nNote: We don't flip digits horizontally — a flipped '7' isn't a '7'!")
print("Always choose augmentations that make sense for your data.")

# %% [markdown]
# ## 6. Transfer Learning (Brief Intro)
#
# Training a CNN from scratch requires a lot of data. **Transfer learning** lets you
# reuse a model that was already trained on millions of images (like ImageNet) and
# adapt it to your specific task.
#
# The idea:
# 1. Take a pre-trained model (e.g., ResNet, trained on ImageNet with 1000 classes)
# 2. Remove the last classification layer
# 3. Add your own classification layer for your number of classes
# 4. Fine-tune — either train only the new layer, or slowly retrain the whole network
#
# Why it works: The early layers of a CNN learn generic features (edges, textures,
# colors) that are useful for *any* image task. Only the later layers are task-specific.

# %%
# Load a pretrained ResNet-18
# weights="IMAGENET1K_V1" loads weights trained on ImageNet (1.2M images, 1000 classes)
resnet = models.resnet18(weights="IMAGENET1K_V1")

# Look at the architecture
print("ResNet-18 final layers:")
print(f"  Average pool: {resnet.avgpool}")
print(f"  FC layer:     {resnet.fc}")
print(f"  (outputs {resnet.fc.out_features} classes for ImageNet)")

# To adapt for your task (e.g., 5 classes), replace the last layer:
num_your_classes = 5
num_features = resnet.fc.in_features  # 512 for ResNet-18
resnet.fc = nn.Linear(num_features, num_your_classes)

print(f"\nAfter modification:")
print(f"  FC layer: {resnet.fc}")
print(f"  (now outputs {num_your_classes} classes for your task)")

# Optionally freeze all layers except the new FC layer
# This means only the new layer's weights are updated during training
for param in resnet.parameters():
    param.requires_grad = False
# Unfreeze the new FC layer
for param in resnet.fc.parameters():
    param.requires_grad = True

trainable = sum(p.numel() for p in resnet.parameters() if p.requires_grad)
total = sum(p.numel() for p in resnet.parameters())
print(f"\nTrainable parameters: {trainable:,} / {total:,} total")
print("Only the new classification layer is being trained!")

# %% [markdown]
# ## 7. Exercises
#
# ### Exercise 7.1 — Build and Train a CNN on Fashion-MNIST
#
# Fashion-MNIST is a drop-in replacement for MNIST with 10 classes of clothing items
# instead of digits. It's harder than MNIST but uses the same 28x28 grayscale format.
#
# Classes: T-shirt/top, Trouser, Pullover, Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot
#
# Tasks:
# 1. Load Fashion-MNIST using `torchvision.datasets.FashionMNIST`
# 2. Build a CNN (you can start with the same architecture as MNISTNet)
# 3. Train for 5 epochs and plot the training curves
# 4. Show the confusion matrix — which clothing items does the model confuse?

# %%
# TODO: Build and train a CNN on Fashion-MNIST

# Class names for Fashion-MNIST
fashion_classes = [
    'T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
    'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot'
]

# Step 1: Load the dataset
# Hint: Use torchvision.datasets.FashionMNIST (same API as MNIST)
# fashion_train = ...
# fashion_test = ...

# Step 2: Create DataLoaders
# fashion_train_loader = ...
# fashion_test_loader = ...

# Step 3: Define your CNN model (can reuse MNISTNet or modify it)
# fashion_model = ...

# Step 4: Define loss and optimizer
# criterion = ...
# optimizer = ...

# Step 5: Train for 5 epochs, tracking loss and accuracy
# ...

# Step 6: Plot training curves
# ...

# Step 7: Show confusion matrix
# ...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Fashion-MNIST CNN

fashion_classes = [
    'T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
    'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot'
]

# Step 1: Load the dataset
fashion_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.2860,), (0.3530,))  # Fashion-MNIST mean/std
])

fashion_train = torchvision.datasets.FashionMNIST(
    root='./data', train=True, download=True, transform=fashion_transform
)
fashion_test = torchvision.datasets.FashionMNIST(
    root='./data', train=False, download=True, transform=fashion_transform
)

# Step 2: DataLoaders
fashion_train_loader = DataLoader(fashion_train, batch_size=64, shuffle=True)
fashion_test_loader = DataLoader(fashion_test, batch_size=64, shuffle=False)

# Step 3: Define the CNN (reuse MNISTNet — same input/output shape)
fashion_model = MNISTNet().to(device)

# Step 4: Loss and optimizer
fashion_criterion = nn.CrossEntropyLoss()
fashion_optimizer = optim.Adam(fashion_model.parameters(), lr=0.001)

# Step 5: Train
fashion_history = {
    'train_loss': [], 'train_acc': [],
    'val_loss': [], 'val_acc': []
}

print("Training CNN on Fashion-MNIST...")
print("-" * 60)

for epoch in range(5):
    train_loss, train_acc = train_one_epoch(
        fashion_model, fashion_train_loader,
        fashion_criterion, fashion_optimizer, device
    )
    val_loss, val_acc = evaluate(
        fashion_model, fashion_test_loader,
        fashion_criterion, device
    )

    fashion_history['train_loss'].append(train_loss)
    fashion_history['train_acc'].append(train_acc)
    fashion_history['val_loss'].append(val_loss)
    fashion_history['val_acc'].append(val_acc)

    print(f"Epoch {epoch+1}/5  "
          f"Train Loss: {train_loss:.4f}  Train Acc: {train_acc:.4f}  "
          f"Val Loss: {val_loss:.4f}  Val Acc: {val_acc:.4f}")

print("-" * 60)
print(f"Final test accuracy: {fashion_history['val_acc'][-1]:.4f}")

# Step 6: Plot training curves
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
epochs = range(1, 6)

axes[0].plot(epochs, fashion_history['train_loss'], 'b-o', label='Train Loss')
axes[0].plot(epochs, fashion_history['val_loss'], 'r-o', label='Val Loss')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].set_title('Fashion-MNIST: Loss')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(epochs, fashion_history['train_acc'], 'b-o', label='Train Acc')
axes[1].plot(epochs, fashion_history['val_acc'], 'r-o', label='Val Acc')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].set_title('Fashion-MNIST: Accuracy')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Step 7: Confusion matrix
fashion_model.eval()
f_preds = []
f_labels = []
with torch.no_grad():
    for images, labels in fashion_test_loader:
        images = images.to(device)
        outputs = fashion_model(images)
        _, predicted = outputs.max(1)
        f_preds.extend(predicted.cpu().numpy())
        f_labels.extend(labels.numpy())

f_cm = confusion_matrix(f_labels, f_preds)
fig, ax = plt.subplots(figsize=(10, 10))
disp = ConfusionMatrixDisplay(
    confusion_matrix=f_cm, display_labels=fashion_classes
)
disp.plot(ax=ax, cmap='Blues', values_format='d', xticks_rotation=45)
ax.set_title('Fashion-MNIST Confusion Matrix')
plt.tight_layout()
plt.show()


# %% [markdown]
# ### Exercise 7.2 — Experiment with Architecture
#
# Modify the CNN architecture and see how it affects performance.
# Try at least two of the following:
#
# 1. **Add a third convolutional layer** (Conv2d with 128 filters)
# 2. **Change filter sizes** from 3x3 to 5x5
# 3. **Add dropout** (`nn.Dropout(0.5)`) before the final linear layer
# 4. **Add batch normalization** (`nn.BatchNorm2d`) after each conv layer
#
# Train on Fashion-MNIST and compare the test accuracy.

# %%
# TODO: Define a modified CNN architecture
# Try adding layers, changing filter sizes, adding dropout or batch norm

class ImprovedCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # TODO: Define your layers here
        ...

    def forward(self, x):
        # TODO: Define the forward pass
        ...
        return x


# TODO: Train your improved model on Fashion-MNIST and compare accuracy
# ...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Improved CNN with batch norm, dropout, and an extra conv layer

class ImprovedCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # Block 1
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool = nn.MaxPool2d(2)

        # Block 2
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)

        # Block 3
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)

        # Classifier
        # After 3 pools: 28 -> 14 -> 7 -> 3 (floor division)
        self.fc1 = nn.Linear(128 * 3 * 3, 256)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))  # -> (32, 14, 14)
        x = self.pool(F.relu(self.bn2(self.conv2(x))))  # -> (64, 7, 7)
        x = self.pool(F.relu(self.bn3(self.conv3(x))))  # -> (128, 3, 3)
        x = x.view(x.size(0), -1)                      # -> (1152)
        x = F.relu(self.fc1(x))                         # -> (256)
        x = self.dropout(x)                             # regularization
        x = self.fc2(x)                                 # -> (10)
        return x


improved_model = ImprovedCNN().to(device)
print(improved_model)
print(f"\nParameters: {sum(p.numel() for p in improved_model.parameters()):,}")

# Train
imp_criterion = nn.CrossEntropyLoss()
imp_optimizer = optim.Adam(improved_model.parameters(), lr=0.001)

print("\nTraining improved CNN on Fashion-MNIST...")
print("-" * 60)
for epoch in range(5):
    train_loss, train_acc = train_one_epoch(
        improved_model, fashion_train_loader,
        imp_criterion, imp_optimizer, device
    )
    val_loss, val_acc = evaluate(
        improved_model, fashion_test_loader,
        imp_criterion, device
    )
    print(f"Epoch {epoch+1}/5  "
          f"Train Loss: {train_loss:.4f}  Train Acc: {train_acc:.4f}  "
          f"Val Loss: {val_loss:.4f}  Val Acc: {val_acc:.4f}")

print("-" * 60)
print(f"Improved model test accuracy: {val_acc:.4f}")
print(f"Basic model test accuracy:    {fashion_history['val_acc'][-1]:.4f}")

# %% [markdown]
# ### Exercise 7.3 — Apply Data Augmentation and Compare
#
# Train the same CNN architecture on Fashion-MNIST **with** data augmentation and
# compare the test accuracy to training **without** augmentation.
#
# Use augmentations that make sense for clothing images:
# - `RandomRotation(10)` — slight rotation
# - `RandomHorizontalFlip()` — flipping a shirt is still a shirt
# - `RandomAffine(degrees=0, translate=(0.1, 0.1))` — slight translation

# %%
# TODO: Train with data augmentation on Fashion-MNIST

# Step 1: Define an augmented transform for training
# aug_transform = transforms.Compose([
#     # TODO: Add augmentation transforms here
#     transforms.ToTensor(),
#     transforms.Normalize((0.2860,), (0.3530,))
# ])

# Step 2: Create augmented dataset and DataLoader
# aug_train_dataset = ...
# aug_train_loader = ...

# Step 3: Train a fresh MNISTNet on the augmented data for 5 epochs
# aug_model = ...

# Step 4: Compare test accuracy with and without augmentation
# ...

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Training with data augmentation

# Step 1: Augmented transform
aug_transform = transforms.Compose([
    transforms.RandomRotation(10),
    transforms.RandomHorizontalFlip(),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize((0.2860,), (0.3530,))
])

# Non-augmented transform for test set
plain_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.2860,), (0.3530,))
])

# Step 2: Datasets and loaders
aug_train_dataset = torchvision.datasets.FashionMNIST(
    root='./data', train=True, download=True, transform=aug_transform
)
aug_test_dataset = torchvision.datasets.FashionMNIST(
    root='./data', train=False, download=True, transform=plain_transform
)
aug_train_loader = DataLoader(aug_train_dataset, batch_size=64, shuffle=True)
aug_test_loader = DataLoader(aug_test_dataset, batch_size=64, shuffle=False)

# Step 3: Train a fresh model
aug_model = MNISTNet().to(device)
aug_criterion = nn.CrossEntropyLoss()
aug_optimizer = optim.Adam(aug_model.parameters(), lr=0.001)

aug_history = {'train_acc': [], 'val_acc': []}

print("Training with data augmentation...")
print("-" * 60)
for epoch in range(5):
    train_loss, train_acc = train_one_epoch(
        aug_model, aug_train_loader, aug_criterion, aug_optimizer, device
    )
    val_loss, val_acc = evaluate(
        aug_model, aug_test_loader, aug_criterion, device
    )
    aug_history['train_acc'].append(train_acc)
    aug_history['val_acc'].append(val_acc)
    print(f"Epoch {epoch+1}/5  "
          f"Train Acc: {train_acc:.4f}  Val Acc: {val_acc:.4f}")

# Step 4: Compare
print("-" * 60)
print(f"Without augmentation: {fashion_history['val_acc'][-1]:.4f}")
print(f"With augmentation:    {aug_history['val_acc'][-1]:.4f}")
print("\nNote: Augmentation often helps more with longer training (10+ epochs).")
print("Training accuracy may be lower (harder examples), but test accuracy")
print("tends to be higher — the model generalizes better.")

# %% [markdown]
# ## Key Takeaways
#
# - **CNNs exploit image structure** — local patterns, shared weights, and hierarchical features
#   make them far more efficient than fully connected networks for image tasks.
#
# - **Three building blocks** — Convolutional layers detect patterns, pooling layers
#   downsample, and fully connected layers combine features for classification.
#
# - **Training loop** — Forward pass, compute loss, backward pass, update weights.
#   Track both training and validation metrics to detect overfitting.
#
# - **Data augmentation** — Free extra training data through random transforms.
#   Always choose augmentations that preserve the label.
#
# - **Transfer learning** — Don't start from scratch when pre-trained models exist.
#   Fine-tuning a pre-trained model is faster and often more accurate.
#
# ---
# **Next:** [NLP & Text Processing →](../09_nlp_text_processing/01_nlp_basics.ipynb)
