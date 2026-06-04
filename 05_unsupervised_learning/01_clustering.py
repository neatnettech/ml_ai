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
# # Module 5.1 — Unsupervised Learning
#
# So far every model we have trained has had **labels** — a target column that tells
# the algorithm what the right answer is.  That is *supervised* learning.  In this
# module we drop the labels and let the algorithm discover structure on its own.
#
# **What you will learn:**
# - Supervised vs unsupervised learning
# - K-Means clustering (from scratch and with scikit-learn)
# - Choosing K with the Elbow Method
# - DBSCAN — density-based clustering
# - PCA — Principal Component Analysis for dimensionality reduction

# %%
import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import make_blobs, make_moons, load_iris
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Reproducibility
np.random.seed(42)

# Nicer plots
plt.rcParams["figure.figsize"] = (8, 5)
plt.rcParams["axes.grid"] = True
print("All imports ready.")

# %% [markdown]
# ## 1. Supervised vs Unsupervised Learning
#
# | Aspect | Supervised | Unsupervised |
# |---|---|---|
# | **Labels** | Every sample has a known target (y) | No labels at all |
# | **Goal** | Predict the target for new data | Discover hidden patterns or groupings |
# | **Examples** | Linear regression, decision trees, SVM | K-Means, DBSCAN, PCA |
# | **Evaluation** | Compare predictions to ground truth | Internal metrics (inertia, silhouette) or visual inspection |
#
# **Key idea:** In unsupervised learning the algorithm receives only the input
# features X.  It must find meaningful structure — clusters, lower-dimensional
# representations, anomalies — without being told what to look for.

# %% [markdown]
# ---
# ## 2. K-Means Clustering
#
# ### How it works
#
# K-Means partitions data into **K** clusters by repeating two simple steps:
#
# 1. **Assign** — label each point with the index of its nearest centroid.
# 2. **Update** — move each centroid to the mean of the points assigned to it.
#
# Repeat until the centroids stop moving (or a maximum number of iterations is
# reached).  The algorithm minimizes **inertia** — the total squared distance from
# each point to its assigned centroid.

# %% [markdown]
# ### 2.1  Step-by-step K-Means from scratch
#
# Let us implement the algorithm by hand so we can visualize every iteration.

# %%
# Generate simple blob data
X, y_true = make_blobs(n_samples=200, centers=3, cluster_std=1.0,
                       random_state=42)

plt.scatter(X[:, 0], X[:, 1], s=20, alpha=0.7)
plt.title("Raw data — no labels")
plt.xlabel("Feature 1")
plt.ylabel("Feature 2")
plt.show()


# %%
def simple_kmeans(X, K, max_iters=6, seed=0):
    """A minimal K-Means implementation that records every iteration."""
    rng = np.random.RandomState(seed)
    # Step 0 — pick K random points as initial centroids
    indices = rng.choice(len(X), size=K, replace=False)
    centroids = X[indices].copy()

    history = []  # store (centroids, labels) at each step

    for i in range(max_iters):
        # --- Assign step ---
        # Compute distance from every point to every centroid
        dists = np.linalg.norm(X[:, np.newaxis] - centroids[np.newaxis, :],
                               axis=2)  # shape (n_samples, K)
        labels = dists.argmin(axis=1)

        history.append((centroids.copy(), labels.copy()))

        # --- Update step ---
        new_centroids = np.array([X[labels == k].mean(axis=0)
                                  for k in range(K)])

        # Check for convergence
        if np.allclose(centroids, new_centroids):
            print(f"Converged at iteration {i + 1}")
            break
        centroids = new_centroids

    return history


history = simple_kmeans(X, K=3)

# %%
# Visualize each iteration
colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
n_iters = len(history)
fig, axes = plt.subplots(1, n_iters, figsize=(5 * n_iters, 4))
if n_iters == 1:
    axes = [axes]

for idx, (centroids, labels) in enumerate(history):
    ax = axes[idx]
    for k in range(3):
        mask = labels == k
        ax.scatter(X[mask, 0], X[mask, 1], c=colors[k], s=15, alpha=0.6)
    ax.scatter(centroids[:, 0], centroids[:, 1],
               c="red", marker="X", s=200, edgecolors="black", linewidths=1.5)
    ax.set_title(f"Iteration {idx + 1}")
    ax.set_xlabel("Feature 1")
    ax.set_ylabel("Feature 2")

plt.suptitle("K-Means — step by step", fontsize=14, y=1.02)
plt.tight_layout()
plt.show()

# %% [markdown]
# Notice how the centroids (red **X** markers) shift toward the center of their
# cluster with each iteration.  After just a few rounds the assignments stabilize.

# %% [markdown]
# ### 2.2  K-Means with scikit-learn
#
# In practice you will use `sklearn.cluster.KMeans` which handles edge cases,
# runs multiple random initializations, and is heavily optimized.

# %%
km = KMeans(n_clusters=3, random_state=42, n_init=10)
km.fit(X)

print("Cluster labels (first 10):", km.labels_[:10])
print("Centroids:\n", km.cluster_centers_)
print("Inertia:", round(km.inertia_, 2))

# %%
# Visualize the sklearn result
plt.scatter(X[:, 0], X[:, 1], c=km.labels_, cmap="viridis", s=20, alpha=0.7)
plt.scatter(km.cluster_centers_[:, 0], km.cluster_centers_[:, 1],
            c="red", marker="X", s=200, edgecolors="black", linewidths=1.5,
            label="Centroids")
plt.title("K-Means (sklearn) — 3 clusters")
plt.xlabel("Feature 1")
plt.ylabel("Feature 2")
plt.legend()
plt.show()

# %% [markdown]
# ---
# ## 3. Choosing K — the Elbow Method
#
# K-Means requires you to specify the number of clusters **K** up front.  How do
# you pick a good value?
#
# The **Elbow Method** works as follows:
# 1. Run K-Means for K = 1, 2, 3, ..., K_max.
# 2. Record the **inertia** (sum of squared distances to the nearest centroid) for
#    each K.
# 3. Plot inertia vs K.  The curve drops steeply at first, then levels off.  The
#    point where it bends — the "elbow" — is usually a good choice for K.

# %%
K_range = range(1, 10)
inertias = []

for k in K_range:
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    model.fit(X)
    inertias.append(model.inertia_)

plt.plot(K_range, inertias, "o-", linewidth=2)
plt.xlabel("Number of clusters (K)")
plt.ylabel("Inertia")
plt.title("Elbow Method")
plt.xticks(list(K_range))
plt.annotate("Elbow", xy=(3, inertias[2]), fontsize=13,
             arrowprops=dict(arrowstyle="->"), xytext=(5, inertias[2] + 400))
plt.show()

# %% [markdown]
# The inertia drops sharply from K=1 to K=3 and then flattens.  This confirms
# that **K = 3** is the natural number of clusters in this dataset.

# %% [markdown]
# ---
# ## 4. DBSCAN — Density-Based Clustering
#
# K-Means assumes clusters are roughly spherical (round blobs).  Real data often
# has irregular shapes.  **DBSCAN** (Density-Based Spatial Clustering of
# Applications with Noise) groups together points that are packed closely and
# marks sparse regions as noise.
#
# Key parameters:
# - `eps` — the maximum distance between two points to be considered neighbors.
# - `min_samples` — the minimum number of neighbors a point must have to be a
#   *core* point (otherwise it is noise, labeled -1).
#
# DBSCAN does **not** require you to specify the number of clusters beforehand.

# %%
# Generate moon-shaped data — K-Means will struggle here
X_moons, y_moons = make_moons(n_samples=300, noise=0.08, random_state=42)

plt.scatter(X_moons[:, 0], X_moons[:, 1], s=15, alpha=0.7)
plt.title("Moon-shaped data")
plt.xlabel("Feature 1")
plt.ylabel("Feature 2")
plt.show()

# %%
# K-Means on moons — it splits along a straight boundary
km_moons = KMeans(n_clusters=2, random_state=42, n_init=10)
km_moons.fit(X_moons)

# DBSCAN on moons — it follows the density contour
db_moons = DBSCAN(eps=0.2, min_samples=5)
db_moons.fit(X_moons)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].scatter(X_moons[:, 0], X_moons[:, 1], c=km_moons.labels_,
                cmap="viridis", s=15, alpha=0.7)
axes[0].set_title("K-Means (K=2) on moons")
axes[0].set_xlabel("Feature 1")
axes[0].set_ylabel("Feature 2")

axes[1].scatter(X_moons[:, 0], X_moons[:, 1], c=db_moons.labels_,
                cmap="viridis", s=15, alpha=0.7)
axes[1].set_title("DBSCAN on moons")
axes[1].set_xlabel("Feature 1")
axes[1].set_ylabel("Feature 2")

plt.tight_layout()
plt.show()

print(f"DBSCAN found {len(set(db_moons.labels_) - {-1})} clusters "
      f"and {(db_moons.labels_ == -1).sum()} noise points.")

# %% [markdown]
# DBSCAN correctly separates the two crescents, while K-Means draws a straight
# line that cuts through both shapes.
#
# **When to use which?**
# - **K-Means** — fast, easy to interpret, good when clusters are roughly round
#   and similar in size.
# - **DBSCAN** — no need to choose K, handles arbitrary shapes, can identify
#   noise.  Sensitive to `eps` and `min_samples`.

# %% [markdown]
# ---
# ## 5. PCA — Principal Component Analysis
#
# ### Why reduce dimensions?
#
# Many real datasets have tens, hundreds, or thousands of features.  High
# dimensionality causes several problems:
# - Hard to **visualize** (you can only plot 2D or 3D).
# - **Curse of dimensionality** — distances become less meaningful.
# - Slower training and risk of **overfitting**.
#
# **PCA** finds new axes (called *principal components*) that capture the most
# variance in the data.  By keeping only the top 2 or 3 components you get a
# low-dimensional summary that preserves as much information as possible.

# %% [markdown]
# ### 5.1  PCA on the Iris dataset (4D to 2D)

# %%
# Load the Iris dataset — 4 features, 3 species
iris = load_iris()
X_iris = iris.data       # shape (150, 4)
y_iris = iris.target      # 0, 1, 2
feature_names = iris.feature_names
target_names = iris.target_names

print("Features:", feature_names)
print("Species:", target_names)
print("Shape:", X_iris.shape)

# %%
# Step 1 — standardize (PCA is sensitive to feature scales)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_iris)

# Step 2 — fit PCA with 2 components
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

print("Original shape:", X_scaled.shape)
print("Reduced shape: ", X_pca.shape)

# %%
# Visualize the 2D projection colored by species
for i, name in enumerate(target_names):
    mask = y_iris == i
    plt.scatter(X_pca[mask, 0], X_pca[mask, 1], label=name, s=30, alpha=0.7)

plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("Iris dataset — PCA projection (4D to 2D)")
plt.legend()
plt.show()

# %% [markdown]
# Even though we went from 4 dimensions down to 2, the three species are still
# clearly separated.  PCA kept the directions of maximum variance, which happen to
# align well with the species labels.

# %% [markdown]
# ### 5.2  Explained variance ratio
#
# How much information did each component capture?

# %%
print("Explained variance per component:", pca.explained_variance_ratio_)
print("Total explained variance:        ",
      round(pca.explained_variance_ratio_.sum() * 100, 1), "%")

# %%
# Bar chart of explained variance for all 4 possible components
pca_full = PCA().fit(X_scaled)
var = pca_full.explained_variance_ratio_

plt.bar(range(1, len(var) + 1), var, alpha=0.7, label="Individual")
plt.step(range(1, len(var) + 1), np.cumsum(var), where="mid",
         label="Cumulative", color="red")
plt.xlabel("Principal Component")
plt.ylabel("Explained Variance Ratio")
plt.title("Explained Variance by Component")
plt.xticks(range(1, len(var) + 1))
plt.legend()
plt.show()

# %% [markdown]
# The first two components together explain the vast majority of the variance.
# Adding more components gives diminishing returns, so 2D is a great summary.

# %% [markdown]
# ---
# ## 6. Exercises

# %% [markdown]
# ### Exercise 5.1 — Find the best K for a mystery dataset
#
# A synthetic dataset is created below with an unknown number of clusters.
# 1. Use the Elbow Method to determine the best K.
# 2. Fit K-Means with that K.
# 3. Plot the resulting clusters.

# %%
# Mystery dataset — do NOT peek at the centers parameter!
X_mystery, _ = make_blobs(n_samples=400, centers=5, cluster_std=0.9,
                          random_state=7)

# TODO: 1) Plot inertia vs K for K = 1..10 to find the elbow
# TODO: 2) Fit KMeans with the best K
# TODO: 3) Scatter plot colored by cluster label

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION — Exercise 5.1

# 1) Elbow Method
K_range = range(1, 11)
inertias = []
for k in K_range:
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    model.fit(X_mystery)
    inertias.append(model.inertia_)

plt.plot(K_range, inertias, "o-", linewidth=2)
plt.xlabel("K")
plt.ylabel("Inertia")
plt.title("Elbow Method — mystery dataset")
plt.xticks(list(K_range))
plt.show()

# 2) Best K is 5 (elbow is at K=5)
best_k = 5
km_mystery = KMeans(n_clusters=best_k, random_state=42, n_init=10)
km_mystery.fit(X_mystery)

# 3) Scatter plot
plt.scatter(X_mystery[:, 0], X_mystery[:, 1], c=km_mystery.labels_,
            cmap="viridis", s=15, alpha=0.7)
plt.scatter(km_mystery.cluster_centers_[:, 0],
            km_mystery.cluster_centers_[:, 1],
            c="red", marker="X", s=200, edgecolors="black", linewidths=1.5)
plt.title(f"K-Means with K={best_k}")
plt.xlabel("Feature 1")
plt.ylabel("Feature 2")
plt.show()

# %% [markdown]
# ### Exercise 5.2 — PCA on a higher-dimensional dataset
#
# The Wine dataset in scikit-learn has 13 features.  Reduce it to 2D with PCA
# and visualize the projection colored by wine class.
#
# Steps:
# 1. Load the dataset with `sklearn.datasets.load_wine()`.
# 2. Standardize the features.
# 3. Apply PCA (2 components).
# 4. Plot the 2D projection with colors for each class.
# 5. Print the explained variance ratio.

# %%
from sklearn.datasets import load_wine

# TODO: Load wine data
# TODO: Standardize features
# TODO: Fit PCA with 2 components
# TODO: Scatter plot colored by class
# TODO: Print explained variance ratio

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION — Exercise 5.2
from sklearn.datasets import load_wine

wine = load_wine()
X_wine = wine.data
y_wine = wine.target

# Standardize
scaler_w = StandardScaler()
X_wine_scaled = scaler_w.fit_transform(X_wine)

# PCA
pca_w = PCA(n_components=2)
X_wine_pca = pca_w.fit_transform(X_wine_scaled)

# Plot
for i, name in enumerate(wine.target_names):
    mask = y_wine == i
    plt.scatter(X_wine_pca[mask, 0], X_wine_pca[mask, 1],
                label=name, s=30, alpha=0.7)

plt.xlabel("PC 1")
plt.ylabel("PC 2")
plt.title("Wine dataset — PCA (13D to 2D)")
plt.legend()
plt.show()

print("Explained variance per component:", pca_w.explained_variance_ratio_)
print("Total explained variance:        ",
      round(pca_w.explained_variance_ratio_.sum() * 100, 1), "%")

# %% [markdown]
# ### Exercise 5.3 — K-Means vs DBSCAN on different data shapes
#
# Compare K-Means (K=2) and DBSCAN on three datasets:
# 1. `make_blobs` with 2 centers
# 2. `make_moons` (noise=0.07)
# 3. `make_circles` (noise=0.05, factor=0.5) — import from `sklearn.datasets`
#
# Create a 3x2 grid of scatter plots (rows = datasets, columns = algorithms).
# Title each subplot with the algorithm name.  Use appropriate `eps` values for
# DBSCAN on each dataset.

# %%
from sklearn.datasets import make_circles

# TODO: Generate three datasets
#   X_blobs2, _ = make_blobs(...)
#   X_moons2, _ = make_moons(...)
#   X_circles, _ = make_circles(...)

# TODO: For each dataset, fit KMeans(n_clusters=2) and DBSCAN
# TODO: Create a 3x2 subplot grid showing the results

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION — Exercise 5.3
from sklearn.datasets import make_circles

# Generate datasets
X_blobs2, _ = make_blobs(n_samples=300, centers=2, cluster_std=0.8,
                         random_state=42)
X_moons2, _ = make_moons(n_samples=300, noise=0.07, random_state=42)
X_circles, _ = make_circles(n_samples=300, noise=0.05, factor=0.5,
                            random_state=42)

datasets = [
    ("Blobs",   X_blobs2,  0.7),
    ("Moons",   X_moons2,  0.2),
    ("Circles", X_circles, 0.2),
]

fig, axes = plt.subplots(3, 2, figsize=(12, 14))

for row, (name, X_data, eps_val) in enumerate(datasets):
    # K-Means
    km_tmp = KMeans(n_clusters=2, random_state=42, n_init=10)
    km_labels = km_tmp.fit_predict(X_data)
    axes[row, 0].scatter(X_data[:, 0], X_data[:, 1], c=km_labels,
                         cmap="viridis", s=15, alpha=0.7)
    axes[row, 0].set_title(f"{name} — K-Means (K=2)")
    axes[row, 0].set_xlabel("Feature 1")
    axes[row, 0].set_ylabel("Feature 2")

    # DBSCAN
    db_tmp = DBSCAN(eps=eps_val, min_samples=5)
    db_labels = db_tmp.fit_predict(X_data)
    axes[row, 1].scatter(X_data[:, 0], X_data[:, 1], c=db_labels,
                         cmap="viridis", s=15, alpha=0.7)
    n_clusters = len(set(db_labels) - {-1})
    n_noise = (db_labels == -1).sum()
    axes[row, 1].set_title(f"{name} — DBSCAN (clusters={n_clusters}, "
                           f"noise={n_noise})")
    axes[row, 1].set_xlabel("Feature 1")
    axes[row, 1].set_ylabel("Feature 2")

plt.suptitle("K-Means vs DBSCAN on different shapes", fontsize=14, y=1.01)
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## Key Takeaways
#
# - **Unsupervised learning** works without labels — the algorithm discovers
#   structure on its own.
# - **K-Means** is fast and intuitive but assumes spherical clusters and needs
#   you to pick K.  Use the **Elbow Method** to choose K.
# - **DBSCAN** handles arbitrary cluster shapes and detects noise, but you need
#   to tune `eps` and `min_samples`.
# - **PCA** reduces dimensionality while preserving the most important variation.
#   Great for visualization and as a preprocessing step before other algorithms.
#
# ---
# **Next:** [Ensemble Methods →](../06_ensemble_methods/01_ensembles.ipynb)
