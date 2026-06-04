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
# # Module 1.1 — NumPy Basics
#
# NumPy is the foundation of almost all ML in Python. It gives you fast, vectorized
# operations on arrays of numbers — no slow Python loops needed.
#
# **What you'll learn:**
# - Creating arrays
# - Array shapes and reshaping
# - Indexing and slicing
# - Vectorized math operations
# - Broadcasting

# %%
import numpy as np
print(f"NumPy version: {np.__version__}")

# %% [markdown]
# ## 1. Creating Arrays
#
# A NumPy array is like a Python list, but every element must be the same type
# (usually numbers), and operations run *much* faster.

# %%
# From a Python list
a = np.array([1, 2, 3, 4, 5])
print("Array:", a)
print("Type:", type(a))
print("Dtype:", a.dtype)  # data type of elements
print("Shape:", a.shape)  # dimensions

# %%
# Common ways to create arrays
zeros = np.zeros(5)          # [0, 0, 0, 0, 0]
ones = np.ones((2, 3))       # 2x3 matrix of ones
rng = np.arange(0, 10, 2)    # [0, 2, 4, 6, 8] — like range()
lin = np.linspace(0, 1, 5)   # 5 evenly spaced values from 0 to 1
rand = np.random.randn(3, 3) # 3x3 matrix of random normal values

print("zeros:", zeros)
print("ones:\n", ones)
print("arange:", rng)
print("linspace:", lin)
print("random:\n", rand)

# %% [markdown]
# ### Exercise 1.1
# Create the following arrays:
# 1. A 1D array of integers from 10 to 50 (inclusive), stepping by 10
# 2. A 4x4 identity matrix (hint: `np.eye`)
# 3. A 2x5 array of random integers between 1 and 100 (hint: `np.random.randint`)

# %%
# TODO: Create the three arrays described above
arr1 = ...  # [10, 20, 30, 40, 50]
arr2 = ...  # 4x4 identity matrix
arr3 = ...  # 2x5 random integers 1-100

print("arr1:", arr1)
print("arr2:\n", arr2)
print("arr3:\n", arr3)

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
arr1 = np.arange(10, 51, 10)
arr2 = np.eye(4)
arr3 = np.random.randint(1, 101, size=(2, 5))

print("arr1:", arr1)
print("arr2:\n", arr2)
print("arr3:\n", arr3)

# %% [markdown]
# ## 2. Indexing and Slicing
#
# Works like Python lists, but extended to multiple dimensions.

# %%
# 1D indexing
a = np.array([10, 20, 30, 40, 50])
print("First element:", a[0])      # 10
print("Last element:", a[-1])      # 50
print("Slice [1:4]:", a[1:4])     # [20, 30, 40]

# 2D indexing
m = np.array([[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]])
print("\nRow 0:", m[0])            # [1, 2, 3]
print("Element [1,2]:", m[1, 2])  # 6
print("Column 1:", m[:, 1])       # [2, 5, 8]

# %%
# Boolean indexing — very powerful for filtering
a = np.array([3, 7, 2, 9, 1, 5, 8])
mask = a > 4
print("Mask:", mask)          # [False, True, False, True, False, True, True]
print("Filtered:", a[mask])   # [7, 9, 5, 8]

# %% [markdown]
# ### Exercise 1.2
# Given the matrix below:
# 1. Extract the second row
# 2. Extract the element at row 2, column 3
# 3. Extract all elements greater than 10
# 4. Replace all elements less than 5 with 0

# %%
m = np.array([[ 2,  8, 14,  3],
              [ 7, 11,  1, 16],
              [ 9,  4, 12,  6]])

# TODO: Complete the exercises
second_row = ...        # 1
element_2_3 = ...       # 2
greater_than_10 = ...   # 3

# 4: Replace elements < 5 with 0 (modify m in-place)
# TODO

print("Second row:", second_row)
print("Element [2,3]:", element_2_3)
print("Greater than 10:", greater_than_10)
print("Modified matrix:\n", m)

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
m = np.array([[ 2,  8, 14,  3],
              [ 7, 11,  1, 16],
              [ 9,  4, 12,  6]])

second_row = m[1]
element_2_3 = m[2, 3]
greater_than_10 = m[m > 10]
m[m < 5] = 0

print("Second row:", second_row)
print("Element [2,3]:", element_2_3)
print("Greater than 10:", greater_than_10)
print("Modified matrix:\n", m)

# %% [markdown]
# ## 3. Vectorized Operations
#
# The key idea: operate on entire arrays at once instead of looping.
# This is faster *and* more readable.

# %%
a = np.array([1, 2, 3, 4])
b = np.array([10, 20, 30, 40])

print("a + b:", a + b)       # element-wise addition
print("a * b:", a * b)       # element-wise multiplication
print("a ** 2:", a ** 2)     # square each element
print("np.sqrt(b):", np.sqrt(b))

# %%
# Aggregation functions
data = np.array([14, 23, 7, 31, 18, 9])
print("Sum:", data.sum())
print("Mean:", data.mean())
print("Std:", data.std())
print("Min:", data.min(), "at index", data.argmin())
print("Max:", data.max(), "at index", data.argmax())

# %% [markdown]
# ### Exercise 1.3
# You have exam scores for 5 students across 3 exams.
# 1. Calculate each student's average score (mean across columns)
# 2. Find the highest score in each exam (max across rows)
# 3. Normalize the scores to 0-1 range: `(x - min) / (max - min)`

# %%
scores = np.array([[85, 90, 78],
                    [92, 88, 95],
                    [70, 65, 80],
                    [88, 92, 87],
                    [76, 85, 72]])

# TODO: Calculate student averages (hint: use axis=1)
student_avg = ...

# TODO: Find highest score per exam (hint: use axis=0)
exam_max = ...

# TODO: Normalize to 0-1 range
normalized = ...

print("Student averages:", student_avg)
print("Exam maximums:", exam_max)
print("Normalized:\n", normalized)

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
student_avg = scores.mean(axis=1)
exam_max = scores.max(axis=0)
normalized = (scores - scores.min()) / (scores.max() - scores.min())

print("Student averages:", student_avg)
print("Exam maximums:", exam_max)
print("Normalized:\n", normalized)

# %% [markdown]
# ## 4. Reshaping
#
# ML models often need data in specific shapes. Reshaping lets you
# rearrange data without changing it.

# %%
a = np.arange(12)
print("Original:", a)
print("Shape:", a.shape)

# Reshape to 3x4
b = a.reshape(3, 4)
print("\nReshaped (3x4):\n", b)

# Use -1 to auto-calculate one dimension
c = a.reshape(2, -1)  # 2 rows, auto-calculate columns
print("\nReshaped (2x?):\n", c)

# Flatten back to 1D
print("\nFlattened:", c.flatten())

# %% [markdown]
# ### Exercise 1.4
# 1. Create an array of numbers 1 through 16
# 2. Reshape it into a 4x4 matrix
# 3. Transpose the matrix (hint: `.T`)
# 4. Flatten it back to 1D

# %%
# TODO
arr = ...          # 1-16
matrix = ...       # 4x4
transposed = ...   # transpose
flat = ...         # back to 1D

print("Array:", arr)
print("Matrix:\n", matrix)
print("Transposed:\n", transposed)
print("Flattened:", flat)

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
arr = np.arange(1, 17)
matrix = arr.reshape(4, 4)
transposed = matrix.T
flat = transposed.flatten()

print("Array:", arr)
print("Matrix:\n", matrix)
print("Transposed:\n", transposed)
print("Flattened:", flat)

# %% [markdown]
# ## 5. Broadcasting
#
# NumPy can operate on arrays with different shapes by "broadcasting"
# the smaller array across the larger one.

# %%
# Scalar broadcast: add 10 to every element
a = np.array([1, 2, 3])
print("a + 10:", a + 10)

# Row broadcast: subtract row means from each row
m = np.array([[10, 20, 30],
              [40, 50, 60]])
row_means = m.mean(axis=1, keepdims=True)  # shape (2,1)
centered = m - row_means
print("\nOriginal:\n", m)
print("Row means:", row_means.flatten())
print("Centered:\n", centered)

# %% [markdown]
# ## Key Takeaways
#
# - **Arrays** are the core data structure — fixed type, fast operations
# - **Vectorize** — avoid Python loops, use array operations
# - **Shape matters** — always be aware of your array dimensions
# - **Broadcasting** lets you combine arrays of different shapes
#
# ---
# **Next:** [Pandas Basics →](02_pandas_basics.ipynb)
