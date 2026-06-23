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
# # Module 7.1 — Introduction to Neural Networks
#
# **Purpose:** The start of the **AI & Deep Learning track** — the jump from classical ML
# to deep learning. You build a neural network twice: first by hand in NumPy so the math
# (weighted sums, activations, backpropagation) is demystified, then in PyTorch to learn
# the training loop that every later deep-learning module in this repo reuses verbatim.
#
# **Prerequisites:** Modules 2–3 (linear algebra, gradient descent).
#
# Neural networks are the foundation of modern deep learning. They power everything
# from image recognition to language translation. In this notebook, you will learn
# how neural networks work from the ground up — starting with the math behind a
# single neuron, building networks by hand with NumPy, and then using PyTorch to
# train real models.
#
# **What you'll learn:**
# - What a neural network is (neurons, layers, weights, biases)
# - Activation functions: ReLU, sigmoid, tanh
# - Building a neural network from scratch with NumPy
# - Forward pass, loss functions, and backpropagation intuition
# - PyTorch basics: tensors and autograd
# - Training your first neural network with PyTorch

# %%
# All imports for this notebook
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.datasets import make_moons, load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Reproducibility
np.random.seed(42)
torch.manual_seed(42)

# Plot settings
plt.rcParams['figure.figsize'] = (8, 5)
plt.rcParams['figure.dpi'] = 100

print(f"NumPy version:   {np.__version__}")
print(f"PyTorch version: {torch.__version__}")


# %% [markdown]
# ---
# ## 1. What is a Neural Network?
#
# A **neural network** is a machine learning model inspired (loosely) by how the brain
# works. It is made up of simple building blocks called **neurons** organized into
# **layers**.
#
# ### The Single Neuron (Perceptron)
#
# A single neuron does three things:
#
# 1. Takes **inputs** (numbers) and multiplies each by a **weight**
# 2. Adds a **bias** term
# 3. Passes the result through an **activation function**
#
# ```
#   Inputs      Weights
#   x1 -----(w1)----\
#                     \
#   x2 -----(w2)------[SUM + bias] --> activation(z) --> output
#                     /
#   x3 -----(w3)----/
#
#   z = w1*x1 + w2*x2 + w3*x3 + bias
#   output = activation(z)
# ```
#
# In math: **z = w . x + b**, then **output = f(z)** where f is the activation function.
#
# ### Layers and Networks
#
# A neural network stacks neurons into layers:
#
# ```
#   Input Layer      Hidden Layer 1     Hidden Layer 2     Output Layer
#   (features)       (learned repr.)    (learned repr.)    (prediction)
#
#     [x1] -------\      [h1] -------\      [h3] -------\      [y1]
#                  \-->               \-->               \-->
#     [x2] -------\--->  [h2] -------\--->  [h4] -------\--->  [y2]
#                  /-->               /-->               /-->
#     [x3] -------/      [  ] -------/      [  ] -------/
# ```
#
# Key vocabulary:
# - **Input layer**: your raw features (no computation happens here)
# - **Hidden layers**: where the network learns internal representations
# - **Output layer**: produces the final prediction
# - **Weights**: numbers the network *learns* that determine how inputs combine
# - **Biases**: extra learned numbers that shift the output of each neuron
# - **Deep learning**: a neural network with 2 or more hidden layers

# %% [markdown]
# ### Activation Functions
#
# Without activation functions, a neural network would just be a linear model
# (no matter how many layers you stack). Activation functions add **non-linearity**,
# which lets the network learn complex patterns.
#
# The three most common activation functions:
#
# | Function | Formula | Range | When to use |
# |----------|---------|-------|-------------|
# | **Sigmoid** | 1 / (1 + e^(-z)) | (0, 1) | Output layer for binary classification |
# | **Tanh** | (e^z - e^(-z)) / (e^z + e^(-z)) | (-1, 1) | Hidden layers (centered around 0) |
# | **ReLU** | max(0, z) | [0, inf) | Default choice for hidden layers |

# %%
# Define activation functions
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def tanh(z):
    return np.tanh(z)

def relu(z):
    return np.maximum(0, z)

# Plot all three
z = np.linspace(-5, 5, 200)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Sigmoid
axes[0].plot(z, sigmoid(z), color='blue', linewidth=2)
axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[0].axhline(y=0.5, color='gray', linestyle=':', alpha=0.5)
axes[0].axhline(y=1, color='gray', linestyle='--', alpha=0.5)
axes[0].axvline(x=0, color='gray', linestyle='--', alpha=0.5)
axes[0].set_title('Sigmoid', fontsize=14)
axes[0].set_xlabel('z')
axes[0].set_ylabel('sigmoid(z)')
axes[0].set_ylim(-0.1, 1.1)
axes[0].grid(True, alpha=0.3)

# Tanh
axes[1].plot(z, tanh(z), color='green', linewidth=2)
axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[1].axvline(x=0, color='gray', linestyle='--', alpha=0.5)
axes[1].set_title('Tanh', fontsize=14)
axes[1].set_xlabel('z')
axes[1].set_ylabel('tanh(z)')
axes[1].set_ylim(-1.3, 1.3)
axes[1].grid(True, alpha=0.3)

# ReLU
axes[2].plot(z, relu(z), color='red', linewidth=2)
axes[2].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[2].axvline(x=0, color='gray', linestyle='--', alpha=0.5)
axes[2].set_title('ReLU', fontsize=14)
axes[2].set_xlabel('z')
axes[2].set_ylabel('relu(z)')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("Sigmoid(0) =", sigmoid(0))   # 0.5
print("Tanh(0)    =", tanh(0))      # 0.0
print("ReLU(-2)   =", relu(-2))     # 0
print("ReLU(3)    =", relu(3))      # 3

# %% [markdown]
# **Why ReLU is the default for hidden layers:**
# - Very fast to compute (just a comparison)
# - Doesn't suffer from the "vanishing gradient" problem as badly as sigmoid/tanh
# - Works well in practice for most problems
#
# **Sigmoid** is still used at the output layer when you need a probability (0 to 1).

# %% [markdown]
# ---
# ## 2. Building from Scratch (NumPy Only)
#
# Before using any frameworks, let's build neural network components by hand.
# This will give you a deep understanding of what's happening under the hood.
#
# ### 2.1 Forward Pass for a Single Neuron
#
# A single neuron computes: **output = activation(w . x + b)**

# %%
# A single neuron with 3 inputs
# Imagine this neuron receives 3 features from one data point

inputs = np.array([1.0, 2.0, 3.0])     # 3 input features
weights = np.array([0.2, 0.8, -0.5])   # learned weights
bias = 0.1                              # learned bias

# Step 1: weighted sum
z = np.dot(weights, inputs) + bias
print(f"Weighted sum (z): {z}")
print(f"  = (0.2*1.0) + (0.8*2.0) + (-0.5*3.0) + 0.1")
print(f"  = 0.2 + 1.6 - 1.5 + 0.1 = {z}")

# Step 2: apply activation function
output_sigmoid = sigmoid(z)
output_relu = relu(z)

print(f"\nWith sigmoid activation: {output_sigmoid:.4f}")
print(f"With ReLU activation:    {output_relu:.4f}")

# %% [markdown]
# ### 2.2 Forward Pass for a 2-Layer Network (XOR Problem)
#
# The **XOR problem** is a classic test for neural networks. A single neuron
# (perceptron) cannot solve XOR because the data is not linearly separable.
# But a network with a hidden layer can!
#
# XOR truth table:
# | x1 | x2 | XOR |
# |----|----| ----|
# | 0  | 0  |  0  |
# | 0  | 1  |  1  |
# | 1  | 0  |  1  |
# | 1  | 1  |  0  |
#
# We'll build a network with:
# - Input layer: 2 neurons (x1, x2)
# - Hidden layer: 2 neurons (with tanh activation)
# - Output layer: 1 neuron (with sigmoid activation)

# %%
# XOR dataset
X_xor = np.array([[0, 0],
                   [0, 1],
                   [1, 0],
                   [1, 1]])
y_xor = np.array([[0], [1], [1], [0]])

# Manually set weights that solve XOR
# (Normally these are learned, but let's see the solution)

# Hidden layer: 2 inputs -> 2 neurons
W1 = np.array([[ 20.0, -20.0],
               [ 20.0, -20.0]])   # shape: (2, 2)
b1 = np.array([-10.0, 30.0])      # shape: (2,)

# Output layer: 2 inputs -> 1 neuron
W2 = np.array([[20.0],
               [20.0]])            # shape: (2, 1)
b2 = np.array([-30.0])            # shape: (1,)

def forward_pass(X):
    """Forward pass through the 2-layer network."""
    # Hidden layer
    z1 = X @ W1 + b1          # linear transformation
    a1 = sigmoid(z1)          # activation
    
    # Output layer
    z2 = a1 @ W2 + b2         # linear transformation
    a2 = sigmoid(z2)          # activation (output probability)
    
    return a2, a1  # return output and hidden activations

# Test on all XOR inputs
output, hidden = forward_pass(X_xor)

print("XOR Network Results:")
print("-" * 40)
for i in range(4):
    print(f"Input: {X_xor[i]}  Hidden: [{hidden[i,0]:.3f}, {hidden[i,1]:.3f}]  "
          f"Output: {output[i,0]:.4f}  Expected: {y_xor[i,0]}")


# %% [markdown]
# Notice how the hidden layer transforms the inputs into a representation where
# the output neuron can separate the two classes. This is the key insight of
# neural networks: **hidden layers learn useful representations of the data**.

# %% [markdown]
# ### 2.3 Loss Functions
#
# A **loss function** measures how wrong the network's predictions are. During
# training, we try to minimize this number.
#
# Two common loss functions:
#
# - **Mean Squared Error (MSE)**: Good for regression. Measures average squared
#   difference between predictions and targets.
#   
#   `MSE = (1/n) * sum((y_pred - y_true)^2)`
#
# - **Binary Cross-Entropy (BCE)**: Good for binary classification. Measures how
#   well predicted probabilities match actual labels.
#   
#   `BCE = -(1/n) * sum(y*log(p) + (1-y)*log(1-p))`

# %%
def mse_loss(y_pred, y_true):
    """Mean Squared Error loss."""
    return np.mean((y_pred - y_true) ** 2)

def binary_cross_entropy(y_pred, y_true, eps=1e-15):
    """Binary Cross-Entropy loss.
    eps prevents log(0) which is undefined."""
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))

# Example: compare good vs bad predictions
y_true = np.array([1.0, 0.0, 1.0, 0.0])
y_good = np.array([0.9, 0.1, 0.8, 0.2])  # pretty good predictions
y_bad  = np.array([0.3, 0.7, 0.4, 0.6])  # pretty bad predictions

print("Good predictions:")
print(f"  MSE:  {mse_loss(y_good, y_true):.4f}")
print(f"  BCE:  {binary_cross_entropy(y_good, y_true):.4f}")

print("\nBad predictions:")
print(f"  MSE:  {mse_loss(y_bad, y_true):.4f}")
print(f"  BCE:  {binary_cross_entropy(y_bad, y_true):.4f}")

print("\nNotice: both loss functions are higher (worse) for bad predictions.")

# %% [markdown]
# ### 2.4 Backpropagation Intuition
#
# **Backpropagation** is the algorithm that trains neural networks. The core idea
# is surprisingly simple:
#
# 1. **Forward pass**: Push data through the network to get predictions
# 2. **Compute loss**: Measure how wrong the predictions are
# 3. **Backward pass**: Calculate how much each weight contributed to the error
#    (using the chain rule from calculus)
# 4. **Update weights**: Nudge each weight in the direction that reduces the loss
#
# This is **gradient descent** applied to neural networks.
#
# ```
# Forward:   inputs --> layer 1 --> layer 2 --> prediction --> loss
# Backward:  inputs <-- layer 1 <-- layer 2 <-- prediction <-- loss
#                        dW1         dW2        (gradients flow backward)
# ```
#
# **The chain rule** tells us: to find how a weight in layer 1 affects the loss,
# multiply together the local gradients along the path from that weight to the loss.
#
# Think of it like a pipeline: if you want to know how turning a knob at the
# beginning affects the output at the end, you trace the signal through each
# stage and multiply the sensitivities together.
#
# **Key insight**: We don't need to understand all the calculus right now.
# PyTorch computes all gradients automatically. But knowing that backpropagation
# exists and uses the chain rule will help you debug and understand your models.

# %%
# Quick demo: gradient of sigmoid
# The derivative of sigmoid(z) is sigmoid(z) * (1 - sigmoid(z))

z = np.linspace(-5, 5, 200)
sig = sigmoid(z)
sig_gradient = sig * (1 - sig)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(z, sig, label='sigmoid(z)', linewidth=2)
ax.plot(z, sig_gradient, label='gradient (derivative)', linewidth=2, linestyle='--')
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
ax.axvline(x=0, color='gray', linestyle='--', alpha=0.3)
ax.set_xlabel('z')
ax.set_title('Sigmoid and Its Gradient')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("Notice: the gradient is largest around z=0 and nearly zero far from 0.")
print("This is the 'vanishing gradient' problem — very large or very small")
print("values of z produce almost zero gradient, so learning slows down.")

# %% [markdown]
# ---
# ## 3. PyTorch Basics
#
# **PyTorch** is the most popular deep learning framework. It provides:
# - **Tensors**: like NumPy arrays, but they can run on GPUs and track gradients
# - **Autograd**: automatic differentiation — no manual gradient math needed
# - **nn.Module**: building blocks for neural network layers
#
# ### 3.1 Tensors
#
# A PyTorch tensor is very similar to a NumPy array. If you know NumPy, you
# already know most of PyTorch's tensor operations.

# %%
# Creating tensors (very similar to NumPy)
a = torch.tensor([1.0, 2.0, 3.0])
print(f"Tensor: {a}")
print(f"Shape:  {a.shape}")
print(f"Dtype:  {a.dtype}")

# Common creation functions
zeros = torch.zeros(3, 4)
ones = torch.ones(2, 3)
rand = torch.randn(3, 3)  # random normal

print(f"\nZeros (3x4):\n{zeros}")
print(f"\nOnes (2x3):\n{ones}")
print(f"\nRandom (3x3):\n{rand}")

# %%
# Basic operations — same as NumPy
a = torch.tensor([1.0, 2.0, 3.0])
b = torch.tensor([4.0, 5.0, 6.0])

print("a + b:", a + b)
print("a * b:", a * b)        # element-wise
print("a @ b:", a @ b)        # dot product
print("a.sum():", a.sum())
print("a.mean():", a.mean())

# Convert between NumPy and PyTorch
np_array = np.array([7.0, 8.0, 9.0])
tensor_from_np = torch.from_numpy(np_array)
back_to_np = tensor_from_np.numpy()

print(f"\nNumPy -> Tensor: {tensor_from_np}")
print(f"Tensor -> NumPy: {back_to_np}")

# %% [markdown]
# ### 3.2 Autograd — Automatic Differentiation
#
# This is PyTorch's superpower. When you set `requires_grad=True` on a tensor,
# PyTorch tracks every operation on it so it can compute gradients automatically.
#
# This replaces all the manual calculus we would need for backpropagation.

# %%
# Simple autograd example: y = x^2 + 3x + 1
# The derivative dy/dx = 2x + 3

x = torch.tensor(2.0, requires_grad=True)  # tell PyTorch to track gradients
y = x**2 + 3*x + 1

print(f"x = {x.item()}")
print(f"y = x^2 + 3x + 1 = {y.item()}")

# Compute gradients (backpropagation)
y.backward()

print(f"dy/dx = 2x + 3 = {x.grad.item()}")
print(f"Expected: 2*2 + 3 = 7")

# %%
# Autograd with vectors — this is what happens inside neural networks
w = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
x = torch.tensor([4.0, 5.0, 6.0])

# Simulate: prediction = w . x, loss = (prediction - target)^2
target = 20.0
prediction = torch.dot(w, x)           # w1*x1 + w2*x2 + w3*x3
loss = (prediction - target) ** 2      # squared error

print(f"Prediction: {prediction.item():.1f}")
print(f"Target:     {target}")
print(f"Loss:       {loss.item():.1f}")

# Compute gradients of loss with respect to w
loss.backward()

print(f"\nGradients dL/dw: {w.grad}")
print("These tell us: to reduce the loss, should we increase or decrease each weight?")
print("Negative gradient means 'increase this weight', positive means 'decrease it'.")

# %% [markdown]
# ---
# ## 4. First Neural Network with PyTorch
#
# Now let's put it all together and train a real neural network on a real
# (synthetic) dataset.
#
# ### 4.1 The Dataset: make_moons
#
# `make_moons` generates two interleaving half-circles — a classic non-linear
# classification problem that a simple linear model cannot solve.

# %%
# Generate the dataset
X, y = make_moons(n_samples=500, noise=0.2, random_state=42)

# Visualize it
plt.figure(figsize=(8, 5))
plt.scatter(X[y == 0, 0], X[y == 0, 1], c='blue', label='Class 0', alpha=0.6, s=30)
plt.scatter(X[y == 1, 0], X[y == 1, 1], c='red', label='Class 1', alpha=0.6, s=30)
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.title('make_moons Dataset')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print(f"X shape: {X.shape}  (500 samples, 2 features)")
print(f"y shape: {y.shape}  (500 labels: 0 or 1)")

# %%
# Prepare data for PyTorch
X_tensor = torch.FloatTensor(X)              # shape: (500, 2)
y_tensor = torch.FloatTensor(y).unsqueeze(1)  # shape: (500, 1) — needs to be 2D

print(f"X_tensor shape: {X_tensor.shape}")
print(f"y_tensor shape: {y_tensor.shape}")


# %% [markdown]
# ### 4.2 Define the Neural Network
#
# In PyTorch, you define a neural network as a class that inherits from `nn.Module`.
# You need to:
# 1. Define the layers in `__init__`
# 2. Define the forward pass in `forward`
#
# PyTorch handles the backward pass (backpropagation) automatically.

# %%
class SimpleNet(nn.Module):
    """A simple neural network with 2 hidden layers.
    
    Architecture:
        Input (2) -> Hidden1 (16) -> ReLU -> Hidden2 (8) -> ReLU -> Output (1) -> Sigmoid
    """
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(2, 16)    # 2 inputs -> 16 hidden neurons
        self.layer2 = nn.Linear(16, 8)    # 16 -> 8 hidden neurons
        self.layer3 = nn.Linear(8, 1)     # 8 -> 1 output
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        x = self.relu(self.layer1(x))     # hidden layer 1 + ReLU
        x = self.relu(self.layer2(x))     # hidden layer 2 + ReLU
        x = self.sigmoid(self.layer3(x))  # output + sigmoid (probability)
        return x

# Create the model
model = SimpleNet()
print(model)

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
print(f"\nTotal trainable parameters: {total_params}")
print("\nParameter breakdown:")
for name, param in model.named_parameters():
    print(f"  {name}: {param.shape} ({param.numel()} params)")

# %% [markdown]
# ### 4.3 Training Loop
#
# Training a neural network follows this pattern every epoch (one pass through data):
#
# 1. **Forward pass**: compute predictions
# 2. **Compute loss**: measure error
# 3. **Backward pass**: compute gradients (`loss.backward()`)
# 4. **Update weights**: optimizer adjusts weights (`optimizer.step()`)
# 5. **Zero gradients**: reset for next iteration (`optimizer.zero_grad()`)

# %%
# Set up training
model = SimpleNet()                                   # fresh model
criterion = nn.BCELoss()                              # binary cross-entropy
optimizer = optim.Adam(model.parameters(), lr=0.01)   # Adam optimizer

# Training loop
num_epochs = 200
losses = []  # track loss over time

for epoch in range(num_epochs):
    # --- Forward pass ---
    predictions = model(X_tensor)            # run data through network
    loss = criterion(predictions, y_tensor)  # compute loss
    
    # --- Backward pass ---
    optimizer.zero_grad()  # clear old gradients
    loss.backward()        # compute new gradients
    optimizer.step()       # update weights
    
    # Track loss
    losses.append(loss.item())
    
    # Print progress every 25 epochs
    if (epoch + 1) % 25 == 0:
        # Calculate accuracy
        with torch.no_grad():  # don't track gradients for evaluation
            predicted_labels = (predictions > 0.5).float()
            accuracy = (predicted_labels == y_tensor).float().mean()
        print(f"Epoch {epoch+1:3d}/{num_epochs}  "
              f"Loss: {loss.item():.4f}  Accuracy: {accuracy.item():.4f}")

print("\nTraining complete!")

# %% [markdown]
# ### 4.4 Plot Training Loss

# %%
plt.figure(figsize=(8, 4))
plt.plot(losses, linewidth=1.5)
plt.xlabel('Epoch')
plt.ylabel('Loss (Binary Cross-Entropy)')
plt.title('Training Loss Over Time')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print(f"Initial loss: {losses[0]:.4f}")
print(f"Final loss:   {losses[-1]:.4f}")
print(f"Improvement:  {((losses[0] - losses[-1]) / losses[0] * 100):.1f}%")


# %% [markdown]
# ### 4.5 Visualize Decision Boundary
#
# Let's see what region of the 2D space the network assigns to each class.
# We create a fine grid of points and run each one through the network.

# %%
def plot_decision_boundary(model, X, y, title="Decision Boundary"):
    """Plot the decision boundary of a trained model."""
    # Create a mesh grid
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200),
                         np.linspace(y_min, y_max, 200))
    
    # Get predictions for every point in the grid
    grid = torch.FloatTensor(np.c_[xx.ravel(), yy.ravel()])
    with torch.no_grad():
        probs = model(grid).numpy().reshape(xx.shape)
    
    # Plot
    plt.figure(figsize=(8, 6))
    plt.contourf(xx, yy, probs, levels=50, cmap='RdBu_r', alpha=0.8)
    plt.colorbar(label='Predicted Probability (Class 1)')
    plt.contour(xx, yy, probs, levels=[0.5], colors='black', linewidths=2)
    plt.scatter(X[y == 0, 0], X[y == 0, 1], c='blue', label='Class 0',
                edgecolors='white', s=30, alpha=0.7)
    plt.scatter(X[y == 1, 0], X[y == 1, 1], c='red', label='Class 1',
                edgecolors='white', s=30, alpha=0.7)
    plt.xlabel('Feature 1')
    plt.ylabel('Feature 2')
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()

plot_decision_boundary(model, X, y, "Neural Network Decision Boundary (make_moons)")

# %% [markdown]
# The neural network has learned a smooth, non-linear decision boundary that
# separates the two crescent shapes. A linear model (like logistic regression)
# could only draw a straight line, which would fail badly on this dataset.
#
# This is the power of neural networks: they can learn **any** decision boundary,
# given enough neurons and training data.

# %% [markdown]
# ---
# ## 5. Exercises
#
# ### Exercise 5.1 — Implement a Single Neuron (Perceptron) from Scratch
#
# Implement a single neuron that can learn the AND gate using NumPy.
#
# AND truth table:
# | x1 | x2 | AND |
# |----|----| ----|
# | 0  | 0  |  0  |
# | 0  | 1  |  0  |
# | 1  | 0  |  0  |
# | 1  | 1  |  1  |
#
# Steps:
# 1. Initialize weights and bias to small random values
# 2. For each epoch:
#    - Forward pass: compute `sigmoid(w . x + b)` for each input
#    - Compute MSE loss
#    - Compute gradients manually (or use simple update rule)
#    - Update weights: `w = w - lr * gradient`
# 3. Print predictions before and after training

# %%
# TODO: Implement a single neuron (perceptron) that learns the AND gate

# Dataset
X_and = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y_and = np.array([[0], [0], [0], [1]])

# Initialize weights and bias
np.random.seed(42)
w = ...  # TODO: shape (2, 1), small random values
b = ...  # TODO: scalar, start at 0
lr = ... # TODO: learning rate (try 0.5 to 2.0)

# Training loop
for epoch in range(1000):
    # TODO: Forward pass
    z = ...       # X_and @ w + b
    a = ...       # sigmoid(z)
    
    # TODO: Compute loss (MSE)
    loss = ...
    
    # TODO: Backward pass (gradient computation)
    # dL/da = 2 * (a - y_and) / n_samples
    # da/dz = a * (1 - a)   (sigmoid derivative)
    # dz/dw = X_and.T
    dz = ...  # dL/dz = dL/da * da/dz
    dw = ...  # dL/dw = X_and.T @ dz / n_samples
    db = ...  # dL/db = mean of dz
    
    # TODO: Update weights
    # w = w - lr * dw
    # b = b - lr * db
    pass

# Print final predictions
print("AND Gate Results:")
for i in range(4):
    print(f"  Input: {X_and[i]}  Predicted: {a[i,0]:.4f}  Expected: {y_and[i,0]}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Single neuron learning the AND gate

X_and = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y_and = np.array([[0], [0], [0], [1]])

np.random.seed(42)
w = np.random.randn(2, 1) * 0.1
b = 0.0
lr = 2.0
n = len(X_and)

losses = []
for epoch in range(1000):
    # Forward pass
    z = X_and @ w + b
    a = 1 / (1 + np.exp(-z))  # sigmoid
    
    # Loss (MSE)
    loss = np.mean((a - y_and) ** 2)
    losses.append(loss)
    
    # Backward pass
    dL_da = 2 * (a - y_and) / n
    da_dz = a * (1 - a)
    dz = dL_da * da_dz
    dw = X_and.T @ dz
    db = np.mean(dz)
    
    # Update
    w -= lr * dw
    b -= lr * db

print("AND Gate Results:")
for i in range(4):
    print(f"  Input: {X_and[i]}  Predicted: {a[i,0]:.4f}  Expected: {y_and[i,0]}")
print(f"\nFinal loss: {losses[-1]:.6f}")

# %% [markdown]
# ### Exercise 5.2 — Build and Train a PyTorch Network on the Iris Dataset
#
# The Iris dataset has 4 features and 3 classes (species of iris flowers).
# Build a neural network that classifies iris flowers.
#
# Requirements:
# 1. Load the Iris dataset and split into train/test
# 2. Standardize the features (use `StandardScaler`)
# 3. Define a network with at least 1 hidden layer
# 4. Use `nn.CrossEntropyLoss` (for multi-class classification)
# 5. Train for at least 100 epochs
# 6. Print final train and test accuracy

# %%
# TODO: Build and train a PyTorch network to classify the Iris dataset

# Step 1: Load data
iris = load_iris()
X_iris, y_iris = iris.data, iris.target
print(f"Features: {iris.feature_names}")
print(f"Classes:  {iris.target_names}")
print(f"X shape:  {X_iris.shape}")

# Step 2: Split and scale
# TODO: use train_test_split and StandardScaler

# Step 3: Convert to tensors
# TODO: convert to torch.FloatTensor (X) and torch.LongTensor (y)
# Note: CrossEntropyLoss expects y as LongTensor (class indices), not one-hot

# Step 4: Define the network
# TODO: create an nn.Module subclass
# Hint: output layer should have 3 neurons (one per class)
# Hint: do NOT put softmax in forward() — CrossEntropyLoss includes it

# Step 5: Training loop
# TODO: criterion = nn.CrossEntropyLoss()
# TODO: optimizer = optim.Adam(model.parameters(), lr=0.01)
# TODO: train for 200 epochs, print loss every 25 epochs

# Step 6: Evaluate
# TODO: compute train and test accuracy
pass

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Iris classification with PyTorch

# Step 1: Load data
iris = load_iris()
X_iris, y_iris = iris.data, iris.target

# Step 2: Split and scale
X_train, X_test, y_train, y_test = train_test_split(
    X_iris, y_iris, test_size=0.2, random_state=42, stratify=y_iris
)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Step 3: Convert to tensors
X_train_t = torch.FloatTensor(X_train)
X_test_t = torch.FloatTensor(X_test)
y_train_t = torch.LongTensor(y_train)
y_test_t = torch.LongTensor(y_test)

# Step 4: Define the network
class IrisNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(4, 16)
        self.layer2 = nn.Linear(16, 8)
        self.layer3 = nn.Linear(8, 3)  # 3 classes
        self.relu = nn.ReLU()
    
    def forward(self, x):
        x = self.relu(self.layer1(x))
        x = self.relu(self.layer2(x))
        x = self.layer3(x)  # no softmax — CrossEntropyLoss handles it
        return x

# Step 5: Training
torch.manual_seed(42)
iris_model = IrisNet()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(iris_model.parameters(), lr=0.01)

iris_losses = []
for epoch in range(200):
    # Forward
    outputs = iris_model(X_train_t)
    loss = criterion(outputs, y_train_t)
    
    # Backward
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    iris_losses.append(loss.item())
    if (epoch + 1) % 25 == 0:
        print(f"Epoch {epoch+1:3d}/200  Loss: {loss.item():.4f}")

# Step 6: Evaluate
with torch.no_grad():
    train_preds = iris_model(X_train_t).argmax(dim=1)
    test_preds = iris_model(X_test_t).argmax(dim=1)
    train_acc = (train_preds == y_train_t).float().mean()
    test_acc = (test_preds == y_test_t).float().mean()

print(f"\nTrain accuracy: {train_acc.item():.4f}")
print(f"Test accuracy:  {test_acc.item():.4f}")

# %% [markdown]
# ### Exercise 5.3 — Experiment with Activations and Hidden Layer Sizes
#
# Go back to the make_moons dataset. Train multiple networks with different
# configurations and compare their accuracy and decision boundaries.
#
# Try these configurations:
# 1. Small network: 1 hidden layer with 4 neurons, ReLU
# 2. Medium network: 2 hidden layers with 16, 8 neurons, ReLU (the one we used above)
# 3. Tanh network: 2 hidden layers with 16, 8 neurons, Tanh instead of ReLU
#
# For each configuration:
# - Train for 300 epochs
# - Record the final loss and accuracy
# - Plot the decision boundary
#
# Which configuration works best? Which is fastest to train?

# %%
# TODO: Experiment with different network configurations

# Hint: Create a flexible network class that accepts configuration parameters
# class FlexNet(nn.Module):
#     def __init__(self, hidden_sizes, activation='relu'):
#         ...

# Configurations to try:
configs = [
    {"name": "Small (4) ReLU",      "hidden_sizes": [4],    "activation": "relu"},
    {"name": "Medium (16,8) ReLU",   "hidden_sizes": [16,8], "activation": "relu"},
    {"name": "Medium (16,8) Tanh",   "hidden_sizes": [16,8], "activation": "tanh"},
]

# TODO: Train each configuration and compare results
# TODO: Plot decision boundaries side by side
pass


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Experimenting with different configurations

class FlexNet(nn.Module):
    """Flexible neural network with configurable layers and activation."""
    def __init__(self, input_size, hidden_sizes, output_size, activation='relu'):
        super().__init__()
        self.layers = nn.ModuleList()
        
        # Build hidden layers
        prev_size = input_size
        for h in hidden_sizes:
            self.layers.append(nn.Linear(prev_size, h))
            prev_size = h
        
        # Output layer
        self.output_layer = nn.Linear(prev_size, output_size)
        
        # Activation
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        else:
            self.activation = nn.Sigmoid()
        
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        for layer in self.layers:
            x = self.activation(layer(x))
        x = self.sigmoid(self.output_layer(x))
        return x

# Prepare data
X_moons, y_moons = make_moons(n_samples=500, noise=0.2, random_state=42)
X_t = torch.FloatTensor(X_moons)
y_t = torch.FloatTensor(y_moons).unsqueeze(1)

configs = [
    {"name": "Small (4) ReLU",      "hidden_sizes": [4],     "activation": "relu"},
    {"name": "Medium (16,8) ReLU",   "hidden_sizes": [16, 8], "activation": "relu"},
    {"name": "Medium (16,8) Tanh",   "hidden_sizes": [16, 8], "activation": "tanh"},
]

results = []
trained_models = []

for cfg in configs:
    torch.manual_seed(42)
    net = FlexNet(2, cfg["hidden_sizes"], 1, cfg["activation"])
    criterion = nn.BCELoss()
    optimizer = optim.Adam(net.parameters(), lr=0.01)
    
    config_losses = []
    for epoch in range(300):
        preds = net(X_t)
        loss = criterion(preds, y_t)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        config_losses.append(loss.item())
    
    # Final accuracy
    with torch.no_grad():
        final_preds = (net(X_t) > 0.5).float()
        acc = (final_preds == y_t).float().mean().item()
    
    results.append({
        "name": cfg["name"],
        "final_loss": config_losses[-1],
        "accuracy": acc,
        "losses": config_losses
    })
    trained_models.append(net)
    print(f"{cfg['name']:25s}  Loss: {config_losses[-1]:.4f}  Accuracy: {acc:.4f}")

# Plot loss curves
plt.figure(figsize=(10, 4))
for r in results:
    plt.plot(r["losses"], label=f"{r['name']} (acc={r['accuracy']:.3f})")
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss Comparison')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Plot decision boundaries side by side
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for idx, (net, r) in enumerate(zip(trained_models, results)):
    ax = axes[idx]
    x_min, x_max = X_moons[:, 0].min() - 0.5, X_moons[:, 0].max() + 0.5
    y_min, y_max = X_moons[:, 1].min() - 0.5, X_moons[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200),
                         np.linspace(y_min, y_max, 200))
    grid = torch.FloatTensor(np.c_[xx.ravel(), yy.ravel()])
    with torch.no_grad():
        probs = net(grid).numpy().reshape(xx.shape)
    ax.contourf(xx, yy, probs, levels=50, cmap='RdBu_r', alpha=0.8)
    ax.contour(xx, yy, probs, levels=[0.5], colors='black', linewidths=2)
    ax.scatter(X_moons[y_moons == 0, 0], X_moons[y_moons == 0, 1],
               c='blue', s=15, alpha=0.6)
    ax.scatter(X_moons[y_moons == 1, 0], X_moons[y_moons == 1, 1],
               c='red', s=15, alpha=0.6)
    ax.set_title(f"{r['name']}\nAcc: {r['accuracy']:.3f}")
    ax.set_xlabel('Feature 1')
    ax.set_ylabel('Feature 2')

plt.tight_layout()
plt.show()

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Neural network** | A stack of layers, each made of neurons computing weighted sums followed by activations |
# | **Activation functions** | ReLU, sigmoid, tanh add the non-linearity that lets networks learn complex patterns |
# | **Forward pass** | Data flows through the network to produce predictions |
# | **Loss functions** | MSE and cross-entropy measure prediction error |
# | **Backpropagation** | Computes gradients via the chain rule; gradient descent updates weights to minimize loss |
# | **PyTorch** | Autograd automates gradients; `nn.Module` and optimizers are the building blocks for training |
# | **Training loop** | forward → loss → backward → update → repeat — the rhythm of all deep learning |
#
# ## Further reading
#
# - **PyTorch — Learn the Basics** (official tutorial: tensors, autograd, and the training
#   loop): https://pytorch.org/tutorials/beginner/basics/intro.html
# - **3Blue1Brown — Neural networks** (the best visual intuition for backpropagation):
#   https://www.3blue1brown.com/topics/neural-networks
# - **Deep Learning book, ch. 6** (feedforward networks in mathematical depth):
#   https://www.deeplearningbook.org/contents/mlp.html
# - **Karpathy — Neural Networks: Zero to Hero** (build networks from scratch, in code, on
#   video): https://karpathy.ai/zero-to-hero.html
#
# **Next:** [Convolutional Neural Networks for Image Classification →](../08_cnns_image_classification/01_cnns.ipynb)
