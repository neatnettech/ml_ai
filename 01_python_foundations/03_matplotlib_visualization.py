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
# # Module 1.3 — Matplotlib & Visualization
#
# **Purpose:** You can't trust data or models you haven't plotted — visualization is
# ML's first debugging tool. A histogram catches a skewed feature, a scatter plot
# catches a broken label, a loss curve catches a diverging model. This notebook gives
# you the matplotlib core you'll reuse in every module of the **Pure ML track**.
#
# Visualization is how you *understand* your data before building models,
# and how you *communicate* results after.
#
# **What you'll learn:**
# - Line plots, scatter plots, bar charts, histograms
# - Customizing plots (labels, legends, colors)
# - Subplots
# - Plotting Pandas data directly

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# %matplotlib inline
plt.style.use('seaborn-v0_8-whitegrid')  # clean style

# %% [markdown]
# ## 1. Basic Plots

# %%
# Line plot
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 4))
plt.plot(x, y, label="sin(x)", color="blue")
plt.plot(x, np.cos(x), label="cos(x)", color="red", linestyle="--")
plt.xlabel("x")
plt.ylabel("y")
plt.title("Sine and Cosine")
plt.legend()
plt.show()

# %%
# Scatter plot
np.random.seed(42)
x = np.random.randn(100)
y = 2 * x + np.random.randn(100) * 0.5  # linear relationship + noise

plt.figure(figsize=(6, 6))
plt.scatter(x, y, alpha=0.6, c="steelblue", edgecolors="white")
plt.xlabel("Feature X")
plt.ylabel("Target Y")
plt.title("Scatter Plot — Linear Relationship")
plt.show()

# %%
# Histogram
data = np.random.randn(1000)

plt.figure(figsize=(8, 4))
plt.hist(data, bins=30, color="coral", edgecolor="black", alpha=0.7)
plt.xlabel("Value")
plt.ylabel("Frequency")
plt.title("Distribution of Random Data")
plt.axvline(data.mean(), color="black", linestyle="--", label=f"Mean: {data.mean():.2f}")
plt.legend()
plt.show()

# %%
# Bar chart
categories = ["Python", "R", "Julia", "MATLAB", "Scala"]
popularity = [85, 40, 15, 25, 10]

plt.figure(figsize=(8, 4))
plt.bar(categories, popularity, color=["#3776ab", "#276DC3", "#9558B2", "#e16737", "#DC322F"])
plt.ylabel("Popularity Score")
plt.title("ML Language Popularity")
plt.show()

# %% [markdown]
# ## 2. Subplots
#
# Show multiple plots side-by-side for comparison.

# %%
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

# Plot 1: Normal distribution
axes[0].hist(np.random.randn(500), bins=25, color="steelblue")
axes[0].set_title("Normal Distribution")

# Plot 2: Uniform distribution
axes[1].hist(np.random.uniform(0, 1, 500), bins=25, color="coral")
axes[1].set_title("Uniform Distribution")

# Plot 3: Exponential distribution
axes[2].hist(np.random.exponential(1, 500), bins=25, color="seagreen")
axes[2].set_title("Exponential Distribution")

plt.tight_layout()
plt.show()

# %% [markdown]
# ### Exercise 3.1
# Create a figure with 2 subplots (1 row, 2 columns):
# 1. Left: scatter plot of `height` vs `weight` (color by gender)
# 2. Right: histogram of `weight` distribution

# %%
np.random.seed(0)
n = 100
height_m = np.random.normal(175, 7, n // 2)
height_f = np.random.normal(162, 6, n // 2)
weight_m = height_m * 0.5 + np.random.normal(0, 5, n // 2)
weight_f = height_f * 0.45 + np.random.normal(0, 4, n // 2)

# TODO: Create a figure with 2 subplots
# Left: scatter plot, height vs weight, different colors for M/F
# Right: histogram of all weights combined
# Add labels, titles, and a legend to the scatter plot


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.scatter(height_m, weight_m, alpha=0.6, label="Male", color="steelblue")
ax1.scatter(height_f, weight_f, alpha=0.6, label="Female", color="coral")
ax1.set_xlabel("Height (cm)")
ax1.set_ylabel("Weight (kg)")
ax1.set_title("Height vs Weight")
ax1.legend()

all_weights = np.concatenate([weight_m, weight_f])
ax2.hist(all_weights, bins=20, color="mediumpurple", edgecolor="black")
ax2.set_xlabel("Weight (kg)")
ax2.set_ylabel("Frequency")
ax2.set_title("Weight Distribution")

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. Plotting Pandas Data Directly
#
# Pandas has built-in plotting that wraps Matplotlib — often the quickest way to visualize.

# %%
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=90)
ts = pd.DataFrame({
    "revenue": np.cumsum(np.random.randn(90) * 100 + 50),
    "costs": np.cumsum(np.random.randn(90) * 80 + 40)
}, index=dates)

ts.plot(figsize=(10, 4), title="Revenue vs Costs Over Time")
plt.ylabel("Amount ($)")
plt.show()

# %% [markdown]
# ### Exercise 3.2
# Using the `sales` DataFrame below, create:
# 1. A bar chart showing total revenue per region
# 2. A box plot of revenue distribution per product

# %%
np.random.seed(42)
sales = pd.DataFrame({
    "region": np.random.choice(["North", "South", "East", "West"], 200),
    "product": np.random.choice(["Widget", "Gadget", "Doohickey"], 200),
    "revenue": np.random.randint(100, 1000, 200)
})

# TODO: Create the two plots described above


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

sales.groupby("region")["revenue"].sum().plot(kind="bar", ax=ax1, color="steelblue")
ax1.set_title("Total Revenue by Region")
ax1.set_ylabel("Revenue ($)")

sales.boxplot(column="revenue", by="product", ax=ax2)
ax2.set_title("Revenue Distribution by Product")
ax2.set_ylabel("Revenue ($)")
plt.suptitle("")  # remove auto-title from boxplot

plt.tight_layout()
plt.show()

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Visualize first** | Plot before modeling — you'll catch issues early |
# | **Core plot types** | `plt.scatter`, `plt.hist`, `plt.bar` cover 80% of needs |
# | **Subplots** | Compare things side-by-side in one figure |
# | **Pandas `.plot()`** | Your quickest path from data to chart |
#
# ## Further reading
#
# - **Matplotlib quick start** (the official intro to figures, axes, and plotting):
#   https://matplotlib.org/stable/users/explain/quick_start.html
# - **Anatomy of a figure** (every named part of a matplotlib plot, annotated):
#   https://matplotlib.org/stable/gallery/showcase/anatomy.html
# - **pandas visualization** (plotting straight from DataFrames):
#   https://pandas.pydata.org/docs/user_guide/visualization.html
#
# **Next:** [Math Foundations →](../02_math_foundations/01_linear_algebra.ipynb) — the
# minimum linear algebra to read ML code: every model is matrix math underneath.
