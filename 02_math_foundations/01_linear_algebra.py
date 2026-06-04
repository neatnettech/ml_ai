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
# # Module 2.1 — Linear Algebra for ML
#
# Linear algebra is the language of machine learning. Every dataset is a matrix,
# every feature vector is... a vector, and most ML algorithms boil down to
# matrix operations under the hood.
#
# **What you'll learn:**
# - Vectors: creation, addition, scalar multiplication, dot product, magnitude
# - Matrices: creation, multiplication, transpose, inverse
# - Why this matters: linear regression is just matrix math
# - Solving systems of linear equations

# %%
import numpy as np
import matplotlib.pyplot as plt

np.set_printoptions(precision=3, suppress=True)
print("Ready to go!")

# %% [markdown]
# ## 1. Vectors
#
# A **vector** is just an ordered list of numbers. In ML, vectors show up everywhere:
# - A single data point (row) in your dataset is a vector of features
# - The weights of a model are a vector
# - Word embeddings represent words as vectors
#
# In NumPy, a vector is simply a 1D array.

# %% [markdown]
# ### 1.1 Creating Vectors

# %%
# A vector is just a 1D array
v = np.array([3, 5, 2])
print("Vector v:", v)
print("Shape:", v.shape)    # (3,) — a 3-dimensional vector
print("Length:", len(v))     # 3 elements

# Think of it as a point in 3D space, or a data point with 3 features
# e.g., [height_cm, weight_kg, age_years]

# %% [markdown]
# ### 1.2 Vector Addition
#
# Adding two vectors means adding their corresponding elements.
# Both vectors must have the same length.

# %%
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# Element-wise addition
c = a + b
print(f"{a} + {b} = {c}")  # [5, 7, 9]

# Visualize 2D vector addition
v1 = np.array([2, 1])
v2 = np.array([1, 3])
v_sum = v1 + v2

plt.figure(figsize=(6, 5))
origin = np.array([0, 0])
plt.quiver(*origin, *v1, angles='xy', scale_units='xy', scale=1, color='blue', label=f'v1 = {v1}')
plt.quiver(*origin, *v2, angles='xy', scale_units='xy', scale=1, color='red', label=f'v2 = {v2}')
plt.quiver(*origin, *v_sum, angles='xy', scale_units='xy', scale=1, color='green', label=f'v1+v2 = {v_sum}')
# Show the parallelogram
plt.quiver(*v1, *v2, angles='xy', scale_units='xy', scale=1, color='red', alpha=0.3, linestyle='--')
plt.quiver(*v2, *v1, angles='xy', scale_units='xy', scale=1, color='blue', alpha=0.3, linestyle='--')
plt.xlim(-0.5, 5)
plt.ylim(-0.5, 5)
plt.grid(True, alpha=0.3)
plt.legend()
plt.title('Vector Addition')
plt.gca().set_aspect('equal')
plt.show()

# %% [markdown]
# ### 1.3 Scalar Multiplication
#
# Multiplying a vector by a scalar (a single number) scales every element.
# This stretches or shrinks the vector.

# %%
v = np.array([2, 3])

print(f"v = {v}")
print(f"2 * v = {2 * v}")    # doubles the vector
print(f"0.5 * v = {0.5 * v}")  # halves the vector
print(f"-1 * v = {-1 * v}")  # reverses direction

# Visualize
plt.figure(figsize=(6, 5))
origin = np.array([0, 0])
for scalar, color in [(1, 'blue'), (2, 'green'), (0.5, 'orange'), (-1, 'red')]:
    scaled = scalar * v
    plt.quiver(*origin, *scaled, angles='xy', scale_units='xy', scale=1,
               color=color, label=f'{scalar} * v = {scaled}')
plt.xlim(-4, 6)
plt.ylim(-4, 8)
plt.grid(True, alpha=0.3)
plt.legend()
plt.title('Scalar Multiplication')
plt.gca().set_aspect('equal')
plt.show()

# %% [markdown]
# ### 1.4 Dot Product
#
# The **dot product** of two vectors multiplies corresponding elements and sums them up.
# It tells you how much two vectors "agree" — how much they point in the same direction.
#
# Formula: `a . b = a[0]*b[0] + a[1]*b[1] + ... + a[n]*b[n]`
#
# In ML, the dot product is everywhere:
# - Predictions in linear models: `y = w . x + b`
# - Similarity between embeddings
# - Attention mechanisms in transformers

# %%
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# Manual calculation
dot_manual = a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
print(f"Manual: {a[0]}*{b[0]} + {a[1]}*{b[1]} + {a[2]}*{b[2]} = {dot_manual}")

# NumPy ways to compute dot product
dot1 = np.dot(a, b)
dot2 = a @ b          # @ is the matrix multiplication operator
dot3 = (a * b).sum()  # element-wise multiply, then sum

print(f"np.dot:  {dot1}")
print(f"a @ b:   {dot2}")
print(f"sum(a*b): {dot3}")
print(f"All equal: {dot1 == dot2 == dot3}")

# %% [markdown]
# ### 1.5 Vector Magnitude (Length / Norm)
#
# The **magnitude** (or **L2 norm**) of a vector is its length.
#
# Formula: `||v|| = sqrt(v[0]^2 + v[1]^2 + ... + v[n]^2)`
#
# This is just the Pythagorean theorem extended to N dimensions.
# In ML, we use norms for regularization, distance calculations, and normalization.

# %%
v = np.array([3, 4])

# Manual: sqrt(3^2 + 4^2) = sqrt(9 + 16) = sqrt(25) = 5
magnitude_manual = np.sqrt(np.sum(v**2))
print(f"Manual: sqrt({v[0]}^2 + {v[1]}^2) = sqrt({v[0]**2} + {v[1]**2}) = {magnitude_manual}")

# NumPy way
magnitude = np.linalg.norm(v)
print(f"np.linalg.norm: {magnitude}")

# Unit vector — same direction, length = 1
unit_v = v / np.linalg.norm(v)
print(f"Unit vector: {unit_v}")
print(f"Its length: {np.linalg.norm(unit_v):.4f}")  # should be 1.0

# %% [markdown]
# ### Exercise 2.1 — Dot Product by Hand
#
# Given vectors `u = [2, 7, 1]` and `w = [8, 2, 8]`:
# 1. Calculate their dot product **manually** (write out each multiplication and sum)
# 2. Verify your answer using `np.dot`
# 3. Calculate the magnitude of each vector

# %%
u = np.array([2, 7, 1])
w = np.array([8, 2, 8])

# TODO: Step 1 — Calculate dot product manually
# dot_manual = u[0]*w[0] + ...
dot_manual = ...

# TODO: Step 2 — Verify with numpy
dot_numpy = ...

# TODO: Step 3 — Calculate magnitudes
mag_u = ...
mag_w = ...

print(f"Manual dot product: {dot_manual}")
print(f"NumPy dot product: {dot_numpy}")
print(f"Match: {dot_manual == dot_numpy}")
print(f"|u| = {mag_u:.3f}")
print(f"|w| = {mag_w:.3f}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
u = np.array([2, 7, 1])
w = np.array([8, 2, 8])

# Step 1 — Manual: 2*8 + 7*2 + 1*8 = 16 + 14 + 8 = 38
dot_manual = u[0]*w[0] + u[1]*w[1] + u[2]*w[2]

# Step 2 — NumPy
dot_numpy = np.dot(u, w)

# Step 3 — Magnitudes
mag_u = np.linalg.norm(u)
mag_w = np.linalg.norm(w)

print(f"Manual dot product: {dot_manual}")
print(f"NumPy dot product: {dot_numpy}")
print(f"Match: {dot_manual == dot_numpy}")
print(f"|u| = {mag_u:.3f}")
print(f"|w| = {mag_w:.3f}")

# %% [markdown]
# ## 2. Matrices
#
# A **matrix** is a 2D array of numbers — rows and columns. In ML:
# - Your dataset is a matrix: rows = samples, columns = features
# - Weight matrices connect layers in neural networks
# - Transformations (rotation, scaling) are matrix operations

# %% [markdown]
# ### 2.1 Creating Matrices

# %%
# From nested lists
A = np.array([[1, 2, 3],
              [4, 5, 6]])
print("Matrix A:")
print(A)
print(f"Shape: {A.shape}")  # (2, 3) — 2 rows, 3 columns

# Special matrices
I = np.eye(3)           # 3x3 identity matrix
Z = np.zeros((2, 4))    # 2x4 zeros

print("\nIdentity matrix:")
print(I)
print("\nZeros matrix:")
print(Z)

# %% [markdown]
# ### 2.2 Matrix Multiplication
#
# Matrix multiplication is NOT element-wise. For `C = A @ B`:
# - Each element `C[i,j]` is the dot product of row `i` of A with column `j` of B
# - The inner dimensions must match: `(m x n) @ (n x p)` = `(m x p)`
#
# This is the most important operation in ML. Neural networks are basically
# a series of matrix multiplications with non-linear functions in between.

# %%
A = np.array([[1, 2],
              [3, 4],
              [5, 6]])  # 3x2

B = np.array([[7, 8, 9],
              [10, 11, 12]])  # 2x3

C = A @ B  # (3x2) @ (2x3) = (3x3)
print(f"A shape: {A.shape}")
print(f"B shape: {B.shape}")
print(f"C = A @ B shape: {C.shape}")
print(f"\nC = A @ B:")
print(C)

# Let's verify C[0,0] manually:
# Row 0 of A = [1, 2], Column 0 of B = [7, 10]
# Dot product = 1*7 + 2*10 = 7 + 20 = 27
print(f"\nVerify C[0,0]: 1*7 + 2*10 = {1*7 + 2*10}")

# %% [markdown]
# ### 2.3 Transpose
#
# The **transpose** flips a matrix — rows become columns and columns become rows.
# If A is `(m x n)`, then A.T is `(n x m)`.
#
# You'll use transpose constantly to make matrix dimensions line up for multiplication.

# %%
A = np.array([[1, 2, 3],
              [4, 5, 6]])

print("A (2x3):")
print(A)
print(f"\nA transposed (3x2):")
print(A.T)

# Common pattern: A^T @ A always gives a square, symmetric matrix
# This shows up in the normal equation for linear regression
ATA = A.T @ A
print(f"\nA^T @ A (3x3):")
print(ATA)
print(f"Is symmetric: {np.allclose(ATA, ATA.T)}")

# %% [markdown]
# ### 2.4 Matrix Inverse
#
# The **inverse** of a matrix A (written A^-1) is the matrix such that:
# `A @ A^-1 = I` (the identity matrix)
#
# Not all matrices have an inverse — only square matrices with non-zero determinant.
# The inverse is used in solving linear equations and in the closed-form solution
# of linear regression.

# %%
A = np.array([[4, 7],
              [2, 6]])

# Compute inverse
A_inv = np.linalg.inv(A)

print("A:")
print(A)
print("\nA inverse:")
print(A_inv)

# Verify: A @ A_inv should equal the identity matrix
product = A @ A_inv
print("\nA @ A_inv (should be identity):")
print(product)
print(f"Is identity: {np.allclose(product, np.eye(2))}")

# Determinant — if this is 0, the matrix has no inverse
det = np.linalg.det(A)
print(f"\nDeterminant of A: {det:.1f}")

# %% [markdown]
# ### Exercise 2.2 — Matrix Multiplication
#
# Given:
# ```
# P = [[1, 2],        Q = [[5, 6],
#      [3, 4]]             [7, 8]]
# ```
#
# 1. Compute `P @ Q` by hand (write out the dot products for each element)
# 2. Verify with NumPy
# 3. Is `P @ Q` the same as `Q @ P`? (Matrix multiplication is NOT commutative!)

# %%
P = np.array([[1, 2],
              [3, 4]])
Q = np.array([[5, 6],
              [7, 8]])

# TODO: Step 1 — Compute P @ Q by hand
# PQ[0,0] = 1*5 + 2*7 = ?
# PQ[0,1] = 1*6 + 2*8 = ?
# PQ[1,0] = 3*5 + 4*7 = ?
# PQ[1,1] = 3*6 + 4*8 = ?
PQ_manual = np.array([[..., ...],
                      [..., ...]])

# TODO: Step 2 — Verify with NumPy
PQ_numpy = ...

# TODO: Step 3 — Compute Q @ P and compare
QP = ...

print("P @ Q (manual):")
print(PQ_manual)
print("\nP @ Q (numpy):")
print(PQ_numpy)
print("\nQ @ P:")
print(QP)
print(f"\nP@Q == Q@P? {np.array_equal(PQ_numpy, QP)}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
P = np.array([[1, 2],
              [3, 4]])
Q = np.array([[5, 6],
              [7, 8]])

# Step 1 — By hand
# PQ[0,0] = 1*5 + 2*7 = 5 + 14 = 19
# PQ[0,1] = 1*6 + 2*8 = 6 + 16 = 22
# PQ[1,0] = 3*5 + 4*7 = 15 + 28 = 43
# PQ[1,1] = 3*6 + 4*8 = 18 + 32 = 50
PQ_manual = np.array([[19, 22],
                      [43, 50]])

# Step 2 — NumPy
PQ_numpy = P @ Q

# Step 3 — Q @ P
QP = Q @ P

print("P @ Q (manual):")
print(PQ_manual)
print("\nP @ Q (numpy):")
print(PQ_numpy)
print("\nQ @ P:")
print(QP)
print(f"\nP@Q == Q@P? {np.array_equal(PQ_numpy, QP)}")
# Answer: No! Matrix multiplication is not commutative.

# %% [markdown]
# ## 3. Why This Matters for ML
#
# ### Linear Regression is Just Matrix Math
#
# The equation for linear regression is:
#
# **y = Xw + b**
#
# Where:
# - `X` is your data matrix (n_samples x n_features)
# - `w` is the weight vector (n_features x 1)
# - `b` is the bias (scalar)
# - `y` is the prediction vector (n_samples x 1)
#
# If we add a column of ones to X (for the bias), it simplifies to: **y = Xw**
#
# The optimal weights can be found with the **normal equation**:
#
# **w = (X^T X)^-1 X^T y**
#
# Let's see this in action!

# %%
# Generate some fake data: house size -> price
np.random.seed(42)
n_samples = 50

# True relationship: price = 3 * size + 50 + noise
sizes = np.random.uniform(30, 150, n_samples)   # house sizes (m^2)
prices = 3 * sizes + 50 + np.random.randn(n_samples) * 20  # prices (thousands)

# Step 1: Set up the X matrix (add column of ones for the bias)
X = np.column_stack([sizes, np.ones(n_samples)])  # (50, 2)
y = prices  # (50,)

print(f"X shape: {X.shape}  (samples x features+bias)")
print(f"y shape: {y.shape}  (samples)")
print(f"\nFirst 5 rows of X:")
print(X[:5])

# %%
# Step 2: Solve for weights using the normal equation
# w = (X^T X)^-1 X^T y
XTX = X.T @ X              # (2x50) @ (50x2) = (2x2)
XTX_inv = np.linalg.inv(XTX)  # (2x2)
XTy = X.T @ y              # (2x50) @ (50,) = (2,)
w = XTX_inv @ XTy          # (2x2) @ (2,) = (2,)

print(f"Learned weights: slope = {w[0]:.2f}, intercept = {w[1]:.2f}")
print(f"True values:     slope = 3.00, intercept = 50.00")

# Step 3: Make predictions
y_pred = X @ w  # Matrix multiplication gives all predictions at once!

# Visualize
plt.figure(figsize=(8, 5))
plt.scatter(sizes, prices, alpha=0.5, label='Data')
sorted_idx = np.argsort(sizes)
plt.plot(sizes[sorted_idx], y_pred[sorted_idx], 'r-', linewidth=2,
         label=f'Fit: y = {w[0]:.1f}x + {w[1]:.1f}')
plt.xlabel('House Size (m²)')
plt.ylabel('Price (thousands)')
plt.title('Linear Regression = Matrix Math')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# %% [markdown]
# **Key insight:** Everything scikit-learn's `LinearRegression` does under the hood
# is the matrix math we just did. Understanding this gives you intuition for why
# things work (and why they sometimes don't).

# %% [markdown]
# ### Exercise 2.3 — Solve a System of Linear Equations
#
# Solving a system of equations is another core application of linear algebra.
#
# Given this system:
# ```
# 2x + 3y = 8
# 4x +  y = 2
# ```
#
# This can be written as: **Aw = b** where:
# - `A` is the coefficient matrix
# - `w` is the vector of unknowns `[x, y]`
# - `b` is the right-hand side
#
# 1. Set up the matrices A and b
# 2. Solve using `np.linalg.solve(A, b)` (more numerically stable than using the inverse)
# 3. Verify your solution by computing `A @ w` and checking it equals `b`

# %%
# TODO: Step 1 — Set up the coefficient matrix and right-hand side
# 2x + 3y = 8
# 4x +  y = 2
A = ...  # 2x2 matrix of coefficients
b = ...  # vector of right-hand side values

# TODO: Step 2 — Solve the system
w = ...  # hint: np.linalg.solve(A, b)

# TODO: Step 3 — Verify
check = ...  # should equal b

print(f"Solution: x = {w[0]:.2f}, y = {w[1]:.2f}")
print(f"Verification A @ w = {check}")
print(f"Original b = {b}")
print(f"Match: {np.allclose(check, b)}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# 2x + 3y = 8
# 4x +  y = 2
A = np.array([[2, 3],
              [4, 1]])
b = np.array([8, 2])

# Solve
w = np.linalg.solve(A, b)

# Verify
check = A @ w

print(f"Solution: x = {w[0]:.2f}, y = {w[1]:.2f}")
print(f"Verification A @ w = {check}")
print(f"Original b = {b}")
print(f"Match: {np.allclose(check, b)}")
# Answer: x = -0.60, y = 3.07 (approximately)

# %% [markdown]
# ## Key Takeaways
#
# - **Vectors** are 1D arrays — they represent data points, weights, features
# - **Dot product** measures similarity and is the core of linear predictions
# - **Matrices** are 2D arrays — datasets, weight layers, transformations
# - **Matrix multiplication** is the workhorse of ML (not element-wise!)
# - **Transpose** flips rows/columns — used everywhere to align dimensions
# - **Inverse** solves equations — the normal equation for linear regression
# - Use `np.linalg.solve` instead of computing the inverse directly (more stable)
#
# ---
# **Next:** [Statistics & Probability →](02_statistics_probability.ipynb)
