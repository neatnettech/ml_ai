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
# # Module 6.1 — Ensemble Methods
#
# So far we have trained individual models — a single decision tree, a single logistic
# regression, etc. But what if we could combine many models together to get a
# **better** result than any single model alone? That is exactly what **ensemble
# methods** do.
#
# **What you'll learn:**
# - What ensembles are and why they work
# - Bagging and Random Forests
# - Boosting and Gradient Boosting
# - A brief introduction to XGBoost
# - Hyperparameter tuning with GridSearchCV

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score

np.random.seed(42)
print("All imports loaded successfully!")

# %% [markdown]
# ---
# ## 1. What Are Ensembles?
#
# ### The Wisdom of Crowds
#
# Imagine you ask 100 people to guess the number of jelly beans in a jar. Most
# individual guesses will be off, but the **average** of all 100 guesses is
# usually remarkably close to the true answer. This is the *wisdom of crowds*
# effect.
#
# Ensemble methods apply the same idea to machine learning:
#
# 1. Train **multiple** models (often called "weak learners").
# 2. Combine their predictions — by **voting** (classification) or **averaging**
#    (regression).
# 3. The combined result is almost always **more accurate and more stable** than
#    any single model.
#
# ### Why does it work?
#
# Each individual model makes different errors. When you combine them, the errors
# tend to cancel out, while the correct predictions reinforce each other.
#
# There are two main families of ensemble methods:
#
# | Strategy | How it works | Key example |
# |----------|-------------|-------------|
# | **Bagging** | Train models in **parallel** on random subsets of data | Random Forest |
# | **Boosting** | Train models **sequentially**, each one fixing the previous one's errors | Gradient Boosting, XGBoost |

# %% [markdown]
# ---
# ## 2. Bagging — Random Forest
#
# ### How Bagging Works (Bootstrap Aggregating)
#
# Bagging follows a simple recipe:
#
# 1. **Bootstrap** — Create *N* random samples from the training data (sampling
#    *with replacement*, so some rows appear more than once and some are left out).
# 2. **Train** — Fit one model (typically a decision tree) on each bootstrap sample.
# 3. **Aggregate** — Combine predictions by majority vote (classification) or
#    average (regression).
#
# A **Random Forest** adds one more twist: at each split in a tree, it only
# considers a *random subset of features*. This makes the individual trees more
# diverse, which makes the ensemble even stronger.
#
# ```
# Training data
#      |
#      +---> Bootstrap sample 1  --->  Tree 1  ---\
#      +---> Bootstrap sample 2  --->  Tree 2  ----+---> Majority Vote = Final Prediction
#      +---> Bootstrap sample 3  --->  Tree 3  ---/
#      ...
# ```

# %% [markdown]
# ### Load the Wine Dataset
#
# We will use sklearn's built-in wine dataset. It has 13 chemical features
# measured on 178 wines from three different cultivars (classes 0, 1, 2).

# %%
wine = load_wine()
X = pd.DataFrame(wine.data, columns=wine.feature_names)
y = wine.target

print(f"Features: {X.shape[1]}")
print(f"Samples:  {X.shape[0]}")
print(f"Classes:  {np.unique(y)}")
X.head()

# %%
# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)
print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

# %% [markdown]
# ### Single Decision Tree vs. Random Forest

# %%
# --- Single Decision Tree ---
dt = DecisionTreeClassifier(random_state=42)
dt.fit(X_train, y_train)
dt_acc = accuracy_score(y_test, dt.predict(X_test))
print(f"Decision Tree accuracy: {dt_acc:.4f}")

# --- Random Forest ---
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_acc = accuracy_score(y_test, rf.predict(X_test))
print(f"Random Forest accuracy: {rf_acc:.4f}")

print(f"\nImprovement: {rf_acc - dt_acc:+.4f}")

# %% [markdown]
# The Random Forest almost always outperforms the single tree because it
# reduces **variance** — it is less likely to overfit to quirks in the training
# data.

# %% [markdown]
# ### Feature Importance
#
# Random Forests can tell us which features are most useful for making
# predictions. Each tree measures how much each feature reduces impurity
# (e.g., Gini impurity), and the forest averages these values across all trees.

# %%
importances = rf.feature_importances_
feature_names = X.columns

# Sort by importance
sorted_idx = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 5))
plt.bar(range(len(importances)), importances[sorted_idx], color="steelblue")
plt.xticks(range(len(importances)), feature_names[sorted_idx], rotation=45, ha="right")
plt.title("Random Forest — Feature Importances (Wine Dataset)")
plt.ylabel("Importance")
plt.tight_layout()
plt.show()

print("\nTop 5 features:")
for i in range(5):
    idx = sorted_idx[i]
    print(f"  {feature_names[idx]:30s} {importances[idx]:.4f}")

# %% [markdown]
# ---
# ## 3. Boosting — Gradient Boosting
#
# ### How Boosting Works
#
# While bagging trains trees **independently** in parallel, boosting trains them
# **sequentially**. Each new tree focuses on the mistakes the previous trees made:
#
# 1. Train a weak model (small tree) on the data.
# 2. Compute the **residual errors** — where the model was wrong.
# 3. Train the *next* tree to predict those residual errors.
# 4. Add the new tree's predictions (scaled by a learning rate) to the ensemble.
# 5. Repeat for *N* rounds.
#
# ```
# Step 1:   Tree 1  --->  predictions  --->  errors
# Step 2:   Tree 2  fits errors       --->  updated predictions  --->  new errors
# Step 3:   Tree 3  fits new errors   --->  updated predictions  --->  smaller errors
# ...
# Final:    Sum of all trees = strong prediction
# ```
#
# Because each tree corrects the previous one, boosting can achieve very high
# accuracy. The trade-off is that it is more prone to **overfitting** if not
# tuned carefully.

# %% [markdown]
# ### GradientBoostingClassifier
#
# Key hyperparameters:
#
# | Parameter | What it controls | Typical values |
# |-----------|-----------------|----------------|
# | `n_estimators` | Number of boosting rounds (trees) | 100 – 500 |
# | `learning_rate` | How much each tree contributes (lower = more conservative) | 0.01 – 0.3 |
# | `max_depth` | Depth of each individual tree (keep small!) | 2 – 5 |

# %%
gb = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    random_state=42
)
gb.fit(X_train, y_train)
gb_acc = accuracy_score(y_test, gb.predict(X_test))
print(f"Gradient Boosting accuracy: {gb_acc:.4f}")

# %%
# Compare all three models side by side
models = ["Decision Tree", "Random Forest", "Gradient Boosting"]
accuracies = [dt_acc, rf_acc, gb_acc]

plt.figure(figsize=(7, 4))
bars = plt.bar(models, accuracies, color=["#e74c3c", "#2ecc71", "#3498db"])
plt.ylim(0.7, 1.05)
plt.ylabel("Test Accuracy")
plt.title("Model Comparison on Wine Dataset")

# Add value labels on top of bars
for bar, acc in zip(bars, accuracies):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
             f"{acc:.3f}", ha="center", fontweight="bold")

plt.tight_layout()
plt.show()

# %% [markdown]
# ### Learning Rate Effect
#
# The `learning_rate` controls how aggressively boosting corrects errors.
# A smaller learning rate needs more trees but often generalizes better.

# %%
learning_rates = [0.01, 0.05, 0.1, 0.3, 0.5]
results = []

for lr in learning_rates:
    model = GradientBoostingClassifier(
        n_estimators=200, learning_rate=lr, max_depth=3, random_state=42
    )
    model.fit(X_train, y_train)
    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    results.append((lr, train_acc, test_acc))
    print(f"lr={lr:.2f}  train={train_acc:.4f}  test={test_acc:.4f}")

results_df = pd.DataFrame(results, columns=["learning_rate", "train_acc", "test_acc"])

plt.figure(figsize=(7, 4))
plt.plot(results_df["learning_rate"], results_df["train_acc"], "o-", label="Train")
plt.plot(results_df["learning_rate"], results_df["test_acc"], "s--", label="Test")
plt.xlabel("Learning Rate")
plt.ylabel("Accuracy")
plt.title("Gradient Boosting — Effect of Learning Rate")
plt.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## 4. XGBoost (Brief Intro)
#
# **XGBoost** (eXtreme Gradient Boosting) is one of the most popular ML libraries,
# especially for tabular/structured data. It won countless Kaggle competitions and
# is widely used in industry.
#
# ### Why XGBoost is popular
#
# - **Speed** — Highly optimized C++ backend, supports parallel tree construction.
# - **Regularization** — Built-in L1 and L2 regularization to reduce overfitting.
# - **Handling missing values** — Automatically learns the best direction for
#   missing data at each split.
# - **Sklearn-compatible API** — Drop-in replacement with `XGBClassifier`.
#
# Under the hood it is still gradient boosting, but with many engineering
# optimizations and algorithmic improvements.
#
# > **Note:** XGBoost is a separate package. Install it with:
# > ```
# > pip install xgboost
# > ```
# > The cell below will fall back to sklearn's `GradientBoostingClassifier`
# > if `xgboost` is not installed.

# %%
try:
    from xgboost import XGBClassifier
    print("xgboost is installed -- using XGBClassifier")

    xgb_model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42,
        use_label_encoder=False,
        eval_metric="mlogloss"
    )

except ImportError:
    print("xgboost not installed -- falling back to sklearn GradientBoostingClassifier")
    print("Install with: pip install xgboost")

    # Wrap sklearn's GradientBoosting so we can use the same variable name
    xgb_model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )

xgb_model.fit(X_train, y_train)
xgb_acc = accuracy_score(y_test, xgb_model.predict(X_test))
print(f"\nXGBoost / Gradient Boosting accuracy: {xgb_acc:.4f}")

# %% [markdown]
# ---
# ## 5. Hyperparameter Tuning with GridSearchCV
#
# Every ensemble model has hyperparameters that affect its performance. Choosing
# the right combination matters a lot, but trying every combination by hand is
# tedious.
#
# **GridSearchCV** automates this:
#
# 1. You define a **grid** of hyperparameter values to try.
# 2. It trains a model for every combination, using **cross-validation** to
#    estimate performance.
# 3. It returns the combination that scored best.
#
# Let's tune `n_estimators` and `max_depth` for a Random Forest.

# %%
param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [3, 5, 10, None]    # None = unlimited depth
}

grid_search = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_grid=param_grid,
    cv=5,                # 5-fold cross-validation
    scoring="accuracy",
    n_jobs=-1,           # use all CPU cores
    verbose=1
)

grid_search.fit(X_train, y_train)

print(f"\nBest parameters: {grid_search.best_params_}")
print(f"Best CV accuracy: {grid_search.best_score_:.4f}")
print(f"Test accuracy:    {grid_search.score(X_test, y_test):.4f}")

# %%
# Visualize grid search results
results = pd.DataFrame(grid_search.cv_results_)

# Pivot table: rows = max_depth, columns = n_estimators, values = mean test score
pivot = results.pivot_table(
    index="param_max_depth",
    columns="param_n_estimators",
    values="mean_test_score"
)

print("Mean CV Accuracy for each (max_depth, n_estimators) combination:\n")
print(pivot.round(4).to_string())

# %% [markdown]
# ---
# ## 6. Exercises
#
# Time to practice! Each exercise has a TODO cell for you to fill in,
# followed by a hidden solution cell.

# %% [markdown]
# ### Exercise 6.1 — Feature Importance Bar Chart
#
# Train a `RandomForestClassifier` (100 trees) on the wine dataset. Then:
#
# 1. Extract the feature importances.
# 2. Find the **top 5** most important features.
# 3. Plot them as a horizontal bar chart.

# %%
# TODO: Exercise 6.1
# 1. Train a RandomForestClassifier on X_train, y_train
rf_ex = ...

# 2. Get feature importances and find top 5 indices
#    Hint: use np.argsort and slice the last 5
importances_ex = ...
top5_idx = ...

# 3. Plot a horizontal bar chart of top 5 features
#    Hint: plt.barh(feature_names, importance_values)

print("Top 5 features:", list(feature_names[top5_idx]))

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION — Exercise 6.1
rf_ex = RandomForestClassifier(n_estimators=100, random_state=42)
rf_ex.fit(X_train, y_train)

importances_ex = rf_ex.feature_importances_
top5_idx = np.argsort(importances_ex)[-5:]  # indices of 5 largest

plt.figure(figsize=(8, 4))
plt.barh(feature_names[top5_idx], importances_ex[top5_idx], color="steelblue")
plt.xlabel("Importance")
plt.title("Top 5 Feature Importances — Random Forest")
plt.tight_layout()
plt.show()

print("Top 5 features:", list(feature_names[top5_idx]))

# %% [markdown]
# ### Exercise 6.2 — Model Comparison
#
# Compare three models on the wine dataset:
#
# 1. `DecisionTreeClassifier`
# 2. `RandomForestClassifier` (100 trees)
# 3. `GradientBoostingClassifier` (100 trees, learning_rate=0.1)
#
# Print each model's test accuracy and create a bar chart comparing them.

# %%
# TODO: Exercise 6.2
# 1. Create and train the three models
dt_ex = ...
rf_ex2 = ...
gb_ex = ...

# 2. Compute test accuracy for each
dt_ex_acc = ...
rf_ex2_acc = ...
gb_ex_acc = ...

# 3. Print accuracies
print(f"Decision Tree:      {dt_ex_acc:.4f}")
print(f"Random Forest:      {rf_ex2_acc:.4f}")
print(f"Gradient Boosting:  {gb_ex_acc:.4f}")

# 4. Create a bar chart comparing the three
# TODO: your plotting code here

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION — Exercise 6.2
dt_ex = DecisionTreeClassifier(random_state=42)
rf_ex2 = RandomForestClassifier(n_estimators=100, random_state=42)
gb_ex = GradientBoostingClassifier(
    n_estimators=100, learning_rate=0.1, random_state=42
)

dt_ex.fit(X_train, y_train)
rf_ex2.fit(X_train, y_train)
gb_ex.fit(X_train, y_train)

dt_ex_acc = accuracy_score(y_test, dt_ex.predict(X_test))
rf_ex2_acc = accuracy_score(y_test, rf_ex2.predict(X_test))
gb_ex_acc = accuracy_score(y_test, gb_ex.predict(X_test))

print(f"Decision Tree:      {dt_ex_acc:.4f}")
print(f"Random Forest:      {rf_ex2_acc:.4f}")
print(f"Gradient Boosting:  {gb_ex_acc:.4f}")

names = ["Decision Tree", "Random Forest", "Gradient Boosting"]
accs = [dt_ex_acc, rf_ex2_acc, gb_ex_acc]

plt.figure(figsize=(7, 4))
bars = plt.bar(names, accs, color=["#e74c3c", "#2ecc71", "#3498db"])
plt.ylim(0.7, 1.05)
plt.ylabel("Test Accuracy")
plt.title("Exercise 6.2 — Model Comparison")
for bar, acc in zip(bars, accs):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
             f"{acc:.3f}", ha="center", fontweight="bold")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Exercise 6.3 — GridSearchCV Tuning
#
# Use `GridSearchCV` to find the best hyperparameters for a
# `GradientBoostingClassifier` on the wine dataset.
#
# Search over:
# - `n_estimators`: [50, 100, 200]
# - `max_depth`: [2, 3, 5]
# - `learning_rate`: [0.05, 0.1, 0.2]
#
# Print the best parameters and the test accuracy of the best model.

# %%
# TODO: Exercise 6.3
# 1. Define the parameter grid
param_grid_ex = {
    # TODO: fill in the grid
}

# 2. Create a GridSearchCV with GradientBoostingClassifier
grid_ex = ...

# 3. Fit on training data
# TODO

# 4. Print best params and test accuracy
print(f"Best parameters: {grid_ex.best_params_}")
print(f"Best CV score:   {grid_ex.best_score_:.4f}")
print(f"Test accuracy:   {grid_ex.score(X_test, y_test):.4f}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION — Exercise 6.3
param_grid_ex = {
    "n_estimators": [50, 100, 200],
    "max_depth": [2, 3, 5],
    "learning_rate": [0.05, 0.1, 0.2]
}

grid_ex = GridSearchCV(
    estimator=GradientBoostingClassifier(random_state=42),
    param_grid=param_grid_ex,
    cv=5,
    scoring="accuracy",
    n_jobs=-1,
    verbose=1
)

grid_ex.fit(X_train, y_train)

print(f"\nBest parameters: {grid_ex.best_params_}")
print(f"Best CV score:   {grid_ex.best_score_:.4f}")
print(f"Test accuracy:   {grid_ex.score(X_test, y_test):.4f}")

# %% [markdown]
# ---
# ## Key Takeaways
#
# - **Ensembles** combine multiple models to produce better predictions than any
#   single model.
# - **Bagging** (Random Forest) trains trees in parallel on bootstrap samples and
#   reduces **variance** (overfitting).
# - **Boosting** (Gradient Boosting, XGBoost) trains trees sequentially, each one
#   correcting the previous one's errors. It reduces **bias** (underfitting).
# - **Feature importance** helps you understand which inputs matter most.
# - **GridSearchCV** automates hyperparameter tuning with cross-validation.
# - When in doubt, try a **Random Forest** first — it works well out of the box
#   with very little tuning.
#
# ---
# **Next:** [Intro to Neural Networks →](../07_neural_networks/01_intro_neural_nets.ipynb)
