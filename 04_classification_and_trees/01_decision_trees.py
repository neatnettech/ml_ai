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
# # Module 4.1 — Classification & Decision Trees
#
# **Purpose:** Your first non-linear model. Decision trees split data with simple
# yes/no questions yet capture patterns no straight line can — and along the way you
# build the evaluation toolkit (confusion matrices, precision/recall, ROC/AUC) that
# every later module in the **Pure ML track** uses forever.
#
# **Prerequisites:** Module 3 (the ML workflow, train/test splits).
#
# Decision trees are one of the most intuitive and powerful machine learning
# algorithms. They work for both classification and regression, and they form the
# foundation for ensemble methods like Random Forests and Gradient Boosting.
#
# **What you'll learn:**
# - How decision trees split data (information gain, Gini impurity)
# - Training a Decision Tree Classifier with scikit-learn
# - Decision Tree Regression
# - Evaluating classifiers: confusion matrix, precision, recall, F1, ROC/AUC
# - Overfitting, underfitting, and cross-validation
# - Hands-on exercises

# %%
# All imports for this notebook
import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import load_iris, load_wine, make_classification, make_regression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, plot_tree
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    confusion_matrix, ConfusionMatrixDisplay,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, roc_curve, auc,
    mean_squared_error
)
from sklearn.preprocessing import label_binarize

np.random.seed(42)
print("Imports loaded successfully!")


# %% [markdown]
# ## 1. Decision Trees — The Concept
#
# A decision tree makes predictions by asking a series of yes/no questions about
# the features. Think of it like a flowchart:
#
# ```
#                Is petal_length < 2.5?
#               /                      \
#            Yes                        No
#             |                          |
#          Setosa              Is petal_width < 1.75?
#                             /                      \
#                          Yes                        No
#                           |                          |
#                      Versicolor                  Virginica
# ```
#
# At each **node**, the algorithm picks the feature and threshold that best
# separates the data into purer groups. But how does it measure "purity"?

# %% [markdown]
# ### Gini Impurity
#
# Gini impurity measures how "mixed" a group is. If a node contains only one
# class, Gini = 0 (perfectly pure). If classes are equally mixed, Gini is high.
#
# **Formula:** Gini = 1 - sum(p_i^2) for each class i
#
# - If a node has 100% class A: Gini = 1 - 1.0^2 = 0 (pure)
# - If a node has 50% class A, 50% class B: Gini = 1 - (0.5^2 + 0.5^2) = 0.5 (impure)
#
# ### Information Gain (Entropy-based)
#
# Entropy is another way to measure impurity, borrowed from information theory.
#
# **Formula:** Entropy = -sum(p_i * log2(p_i)) for each class i
#
# - Pure node: Entropy = 0
# - Maximally mixed (50/50 binary): Entropy = 1
#
# **Information Gain** = Entropy(parent) - weighted average of Entropy(children)
#
# The tree picks the split that maximizes information gain (or minimizes Gini).
#
# Let's see this with a concrete example.

# %%
# Concrete example: should we play tennis?
# Imagine 10 days: 6 we played (Yes), 4 we didn't (No)

def gini_impurity(class_counts):
    """Calculate Gini impurity from a list of class counts."""
    total = sum(class_counts)
    if total == 0:
        return 0
    proportions = [c / total for c in class_counts]
    return 1 - sum(p ** 2 for p in proportions)

def entropy(class_counts):
    """Calculate entropy from a list of class counts."""
    total = sum(class_counts)
    if total == 0:
        return 0
    proportions = [c / total for c in class_counts if c > 0]
    return -sum(p * np.log2(p) for p in proportions)

# Parent node: 6 Yes, 4 No
parent_gini = gini_impurity([6, 4])
parent_entropy = entropy([6, 4])
print(f"Parent — Gini: {parent_gini:.4f}, Entropy: {parent_entropy:.4f}")

# Suppose we split on "Is it sunny?":
#   Sunny (5 samples): 3 Yes, 2 No
#   Not Sunny (5 samples): 3 Yes, 1 No  (wait, that's only 4...)
# Let's fix: Sunny: 3 Yes, 2 No | Not Sunny: 3 Yes, 2 No
# This is a bad split — both sides look the same!
left_gini = gini_impurity([3, 2])   # sunny
right_gini = gini_impurity([3, 2])  # not sunny
weighted_gini_bad = (5/10) * left_gini + (5/10) * right_gini
print(f"\nBad split (Sunny?) — Weighted Gini: {weighted_gini_bad:.4f}")
print(f"  Improvement: {parent_gini - weighted_gini_bad:.4f}")

# Better split on "Is it windy?":
#   Windy (4 samples): 1 Yes, 3 No
#   Not Windy (6 samples): 5 Yes, 1 No
left_gini = gini_impurity([1, 3])   # windy
right_gini = gini_impurity([5, 1])  # not windy
weighted_gini_good = (4/10) * left_gini + (6/10) * right_gini
print(f"\nGood split (Windy?) — Weighted Gini: {weighted_gini_good:.4f}")
print(f"  Improvement: {parent_gini - weighted_gini_good:.4f}")

print(f"\nThe 'Windy?' split is better because it reduces impurity more!")

# %%
# Visualize Gini and Entropy as a function of class proportion
p = np.linspace(0.01, 0.99, 100)
gini_values = 1 - p**2 - (1-p)**2
entropy_values = -p * np.log2(p) - (1-p) * np.log2(1-p)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(p, gini_values, label="Gini Impurity", linewidth=2)
ax.plot(p, entropy_values, label="Entropy", linewidth=2)
ax.set_xlabel("Proportion of Class 1 (binary case)")
ax.set_ylabel("Impurity")
ax.set_title("Gini Impurity vs Entropy")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("Both measures peak at p=0.5 (maximum uncertainty) and are 0 at p=0 or p=1 (pure).")
print("Gini is slightly faster to compute; Entropy can be more sensitive to changes.")
print("In practice, they usually produce very similar trees.")

# %% [markdown]
# ## 2. Decision Tree Classifier with scikit-learn
#
# Let's train a real decision tree on the **Iris dataset** — a classic beginner
# dataset with 150 flowers from 3 species, described by 4 measurements
# (sepal length, sepal width, petal length, petal width).

# %%
# Load the Iris dataset
iris = load_iris()
X, y = iris.data, iris.target

print(f"Features: {iris.feature_names}")
print(f"Classes: {iris.target_names}")
print(f"Dataset shape: {X.shape}  (150 samples, 4 features)")
print(f"Class distribution: {np.bincount(y)}  (50 of each)")

# %%
# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
print(f"Train: {X_train.shape[0]} samples")
print(f"Test:  {X_test.shape[0]} samples")

# %%
# Train a Decision Tree Classifier
clf = DecisionTreeClassifier(random_state=42)
clf.fit(X_train, y_train)

# Make predictions
y_pred = clf.predict(X_test)

# Check accuracy
acc = accuracy_score(y_test, y_pred)
print(f"Accuracy: {acc:.4f}")
print(f"\nTree depth: {clf.get_depth()}")
print(f"Number of leaves: {clf.get_n_leaves()}")

# %%
# Visualize the full decision tree
fig, ax = plt.subplots(figsize=(20, 10))
plot_tree(
    clf,
    feature_names=iris.feature_names,
    class_names=iris.target_names,
    filled=True,           # color nodes by majority class
    rounded=True,          # round box corners
    fontsize=10,
    ax=ax
)
ax.set_title("Decision Tree trained on Iris dataset", fontsize=14)
plt.tight_layout()
plt.show()

print("Reading the tree: each node shows the split condition, Gini impurity,")
print("number of samples, and class distribution. Darker color = more pure.")

# %%
# Feature importance — how much each feature contributed to splits
importances = clf.feature_importances_

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(iris.feature_names, importances)
ax.set_xlabel("Importance")
ax.set_title("Feature Importance in the Decision Tree")
for bar, imp in zip(bars, importances):
    ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
            f"{imp:.3f}", va="center")
plt.tight_layout()
plt.show()

print("Petal measurements are far more important than sepal measurements")
print("for distinguishing Iris species — as we saw in the tree structure.")

# %% [markdown]
# ## 3. Decision Tree Regressor
#
# Decision trees can also handle regression (predicting continuous values).
# Instead of Gini impurity, the splits minimize **mean squared error (MSE)**
# within each leaf. The prediction for a leaf is the **mean** of the training
# samples that fell into it.

# %%
# Create synthetic regression data
np.random.seed(42)
X_reg = np.sort(5 * np.random.rand(200, 1), axis=0)
y_reg = np.sin(X_reg).ravel() + 0.2 * np.random.randn(200)

# Train two regressors with different depths
reg_shallow = DecisionTreeRegressor(max_depth=3, random_state=42)
reg_deep = DecisionTreeRegressor(max_depth=10, random_state=42)

reg_shallow.fit(X_reg, y_reg)
reg_deep.fit(X_reg, y_reg)

# Predict on a fine grid for smooth plotting
X_plot = np.linspace(0, 5, 500).reshape(-1, 1)
y_shallow = reg_shallow.predict(X_plot)
y_deep = reg_deep.predict(X_plot)

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

for ax, y_hat, depth, title in zip(
    axes,
    [y_shallow, y_deep],
    [3, 10],
    ["max_depth=3 (underfitting?)", "max_depth=10 (overfitting?)"]
):
    ax.scatter(X_reg, y_reg, s=10, alpha=0.5, label="Training data")
    ax.plot(X_plot, y_hat, color="red", linewidth=2, label=f"Tree (depth={depth})")
    ax.set_xlabel("X")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

axes[0].set_ylabel("y")
plt.suptitle("Decision Tree Regression: Depth Comparison", fontsize=14)
plt.tight_layout()
plt.show()

print(f"Shallow tree MSE (train): {mean_squared_error(y_reg, reg_shallow.predict(X_reg)):.4f}")
print(f"Deep tree MSE (train):    {mean_squared_error(y_reg, reg_deep.predict(X_reg)):.4f}")
print("\nThe deep tree fits the training data almost perfectly, but notice")
print("the staircase pattern — it is memorizing noise (overfitting).")

# %% [markdown]
# ## 4. Model Evaluation for Classification
#
# Accuracy alone can be misleading, especially with imbalanced classes. Let's
# learn the full toolkit for evaluating classifiers.

# %% [markdown]
# ### Confusion Matrix
#
# A confusion matrix shows what the model got right and wrong. For binary
# classification:
#
# ```
#                     Predicted
#                  Positive  Negative
# Actual Positive    TP        FN
# Actual Negative    FP        TN
# ```
#
# - **TP (True Positive):** Model said positive, and it was actually positive. (Correct!)
# - **TN (True Negative):** Model said negative, and it was actually negative. (Correct!)
# - **FP (False Positive):** Model said positive, but it was actually negative. (Type I error — "false alarm")
# - **FN (False Negative):** Model said negative, but it was actually positive. (Type II error — "missed detection")
#
# **Real-world examples of why FP vs FN matters:**
# - Spam filter: FP = legitimate email goes to spam (annoying). FN = spam reaches inbox (annoying but less harmful).
# - Cancer screening: FP = healthy person told they might have cancer (stressful, more tests). FN = cancer missed (dangerous!).
# - Fraud detection: FP = legitimate transaction blocked (bad customer experience). FN = fraud goes through (financial loss).

# %%
# Confusion matrix for our Iris classifier
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix (raw):\n", cm)
print("\nRows = actual class, Columns = predicted class")
print("Diagonal = correct predictions, off-diagonal = errors")

# Visual confusion matrix
fig, ax = plt.subplots(figsize=(7, 6))
disp = ConfusionMatrixDisplay(cm, display_labels=iris.target_names)
disp.plot(cmap="Blues", ax=ax)
ax.set_title("Confusion Matrix — Iris Decision Tree")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Accuracy, Precision, Recall, and F1 Score
#
# These are the four most common classification metrics. Here is what each one
# measures:
#
# | Metric | Formula | Question it answers |
# |--------|---------|--------------------|
# | **Accuracy** | (TP + TN) / Total | What fraction of all predictions were correct? |
# | **Precision** | TP / (TP + FP) | When the model says "positive", how often is it right? |
# | **Recall** | TP / (TP + FN) | Out of all actual positives, how many did we catch? |
# | **F1 Score** | 2 * (Prec * Rec) / (Prec + Rec) | Harmonic mean of precision and recall |
#
# **When to care about which:**
# - **Accuracy:** Good default when classes are balanced.
# - **Precision:** When false positives are costly (e.g., spam filter — don't block real emails).
# - **Recall:** When false negatives are costly (e.g., cancer screening — don't miss a diagnosis).
# - **F1 Score:** When you need a balance between precision and recall, or when classes are imbalanced.

# %%
# Calculate metrics for the Iris model
acc  = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, average="macro")  # macro = average across classes
rec  = recall_score(y_test, y_pred, average="macro")
f1   = f1_score(y_test, y_pred, average="macro")

print(f"Accuracy:  {acc:.4f}")
print(f"Precision: {prec:.4f}  (macro-averaged across 3 classes)")
print(f"Recall:    {rec:.4f}")
print(f"F1 Score:  {f1:.4f}")
print("\nNote: For multi-class problems, 'macro' averages the metric")
print("computed independently for each class (treats all classes equally).")

# %%
# Classification report — all metrics at once, per class
print("Classification Report:\n")
print(classification_report(y_test, y_pred, target_names=iris.target_names))

print("This report shows precision, recall, and F1 for EACH class individually,")
print("plus micro/macro/weighted averages at the bottom.")

# %% [markdown]
# ### ROC Curve and AUC
#
# The **ROC curve** (Receiver Operating Characteristic) plots the trade-off
# between the True Positive Rate (recall) and the False Positive Rate at
# various classification thresholds.
#
# **AUC** (Area Under the Curve) summarizes the ROC curve as a single number:
# - AUC = 1.0: perfect classifier
# - AUC = 0.5: random guessing (the diagonal line)
# - AUC < 0.5: worse than random (something is backwards)
#
# For multi-class problems, we compute ROC/AUC per class using a one-vs-rest
# approach.

# %%
# ROC Curve for multi-class (one-vs-rest)
# We need probability scores, not just predictions
y_proba = clf.predict_proba(X_test)

# Binarize the true labels for one-vs-rest ROC
y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
n_classes = 3

fig, ax = plt.subplots(figsize=(8, 6))

colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
for i, (cls_name, color) in enumerate(zip(iris.target_names, colors)):
    fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, color=color, linewidth=2,
            label=f"{cls_name} (AUC = {roc_auc:.2f})")

ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random (AUC = 0.50)")
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate (Recall)")
ax.set_title("ROC Curves — Iris Decision Tree (One-vs-Rest)")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("Each curve shows how well the model separates one class from the rest.")
print("AUC close to 1.0 means excellent discrimination for that class.")

# %% [markdown]
# ## 5. Overfitting and Underfitting
#
# This is one of the most important concepts in machine learning:
#
# - **Overfitting:** The model learns the training data *too well*, including
#   noise and quirks. It performs great on training data but poorly on new data.
# - **Underfitting:** The model is too simple to capture the real patterns.
#   It performs poorly on both training and test data.
#
# For decision trees, **max_depth** is the key knob:
# - Very deep tree = overfitting (memorizes training data)
# - Very shallow tree = underfitting (too simple to learn patterns)

# %%
# Show how max_depth affects train vs test accuracy
depths = range(1, 16)
train_scores = []
test_scores = []

for depth in depths:
    tree = DecisionTreeClassifier(max_depth=depth, random_state=42)
    tree.fit(X_train, y_train)
    train_scores.append(tree.score(X_train, y_train))
    test_scores.append(tree.score(X_test, y_test))

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(depths, train_scores, "o-", label="Train Accuracy", linewidth=2)
ax.plot(depths, test_scores, "s-", label="Test Accuracy", linewidth=2)
ax.set_xlabel("max_depth")
ax.set_ylabel("Accuracy")
ax.set_title("Train vs Test Accuracy at Different Tree Depths")
ax.legend()
ax.set_xticks(list(depths))
ax.grid(True, alpha=0.3)

# Mark the best test depth
best_depth = list(depths)[np.argmax(test_scores)]
best_test = max(test_scores)
ax.axvline(x=best_depth, color="gray", linestyle="--", alpha=0.5)
ax.annotate(f"Best test depth = {best_depth}",
            xy=(best_depth, best_test),
            xytext=(best_depth + 2, best_test - 0.05),
            arrowprops=dict(arrowstyle="->"),
            fontsize=11)

plt.tight_layout()
plt.show()

print("Key observations:")
print("- Training accuracy keeps increasing (or stays at 100%) as depth grows.")
print("- Test accuracy peaks at some depth and may drop after — that is overfitting.")
print("- The gap between train and test accuracy is a sign of overfitting.")
print(f"- Best max_depth for test performance: {best_depth}")

# %% [markdown]
# ### Cross-Validation
#
# Using a single train/test split can be unreliable — you might get lucky or
# unlucky with the split. **Cross-validation** gives a more robust estimate.
#
# With **k-fold cross-validation** (commonly k=5):
# 1. Split data into 5 equal folds
# 2. Train on 4 folds, test on the 1 held-out fold
# 3. Repeat 5 times (each fold is the test set once)
# 4. Report the mean and standard deviation of the scores
#
# This gives you 5 accuracy estimates instead of just 1, so you can see how
# stable the model is.

# %%
# Cross-validation with different depths
print("Cross-validation scores at different max_depth values:\n")
print(f"{'Depth':>6}  {'Mean CV Acc':>12}  {'Std':>8}  {'Individual Fold Scores'}")
print("-" * 70)

cv_means = []
cv_stds = []

for depth in range(1, 11):
    tree = DecisionTreeClassifier(max_depth=depth, random_state=42)
    scores = cross_val_score(tree, X, y, cv=5, scoring="accuracy")
    cv_means.append(scores.mean())
    cv_stds.append(scores.std())
    print(f"{depth:>6}  {scores.mean():>12.4f}  {scores.std():>8.4f}  {scores.round(3)}")

best_cv_depth = np.argmax(cv_means) + 1
print(f"\nBest depth by cross-validation: {best_cv_depth}")
print(f"CV accuracy at that depth: {cv_means[best_cv_depth-1]:.4f} +/- {cv_stds[best_cv_depth-1]:.4f}")

# %%
# Visualize cross-validation results
depths_range = list(range(1, 11))
cv_means = np.array(cv_means)
cv_stds = np.array(cv_stds)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(depths_range, cv_means, "o-", linewidth=2, label="Mean CV Accuracy")
ax.fill_between(depths_range,
                cv_means - cv_stds,
                cv_means + cv_stds,
                alpha=0.2, label="+/- 1 Std Dev")
ax.set_xlabel("max_depth")
ax.set_ylabel("Accuracy")
ax.set_title("Cross-Validation Accuracy vs Tree Depth")
ax.set_xticks(depths_range)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("The shaded band shows the variability across folds.")
print("A wide band means the model's performance is unstable.")
print("Choose the simplest model (smallest depth) within the top-performing range.")

# %% [markdown]
# ## 6. Exercises
#
# Time to practice! Each exercise has a TODO cell for you to fill in,
# followed by a hidden solution cell.

# %% [markdown]
# ### Exercise 4.1 — Wine Dataset Classification
#
# Train a decision tree on the **Wine dataset** (`sklearn.datasets.load_wine`).
# This dataset has 13 chemical features describing 178 wines from 3 cultivars.
#
# Steps:
# 1. Load the wine dataset
# 2. Split into train (70%) and test (30%) with `random_state=42` and `stratify=y`
# 3. Train a `DecisionTreeClassifier` with `random_state=42`
# 4. Print the accuracy
# 5. Display the confusion matrix using `ConfusionMatrixDisplay`

# %%
# TODO: Exercise 4.1 — Wine Dataset Classification

# 1. Load the wine dataset
wine = ...  # hint: load_wine()
X_wine, y_wine = ..., ...

# 2. Train/test split (70/30, random_state=42, stratify)
X_train_w, X_test_w, y_train_w, y_test_w = ...

# 3. Train a DecisionTreeClassifier
clf_wine = ...

# 4. Predict and print accuracy
y_pred_w = ...
# print(f"Accuracy: {accuracy_score(y_test_w, y_pred_w):.4f}")

# 5. Plot confusion matrix
# hint: ConfusionMatrixDisplay.from_estimator(clf_wine, X_test_w, y_test_w, ...)
pass

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Exercise 4.1 — Wine Dataset Classification

# 1. Load the wine dataset
wine = load_wine()
X_wine, y_wine = wine.data, wine.target

# 2. Train/test split
X_train_w, X_test_w, y_train_w, y_test_w = train_test_split(
    X_wine, y_wine, test_size=0.3, random_state=42, stratify=y_wine
)

# 3. Train a DecisionTreeClassifier
clf_wine = DecisionTreeClassifier(random_state=42)
clf_wine.fit(X_train_w, y_train_w)

# 4. Predict and print accuracy
y_pred_w = clf_wine.predict(X_test_w)
print(f"Accuracy: {accuracy_score(y_test_w, y_pred_w):.4f}")

# 5. Plot confusion matrix
fig, ax = plt.subplots(figsize=(7, 6))
ConfusionMatrixDisplay.from_estimator(
    clf_wine, X_test_w, y_test_w,
    display_labels=wine.target_names,
    cmap="Blues", ax=ax
)
ax.set_title("Confusion Matrix — Wine Decision Tree")
plt.tight_layout()
plt.show()

print("\nClassification Report:")
print(classification_report(y_test_w, y_pred_w, target_names=wine.target_names))

# %% [markdown]
# ### Exercise 4.2 — Best max_depth via Cross-Validation
#
# Using the Wine dataset, find the best `max_depth` for a decision tree
# using 5-fold cross-validation.
#
# Steps:
# 1. Try `max_depth` from 1 to 15
# 2. For each depth, compute the mean cross-validation accuracy
# 3. Print the best depth and its CV score
# 4. Plot the CV accuracy vs depth (with error bands)

# %%
# TODO: Exercise 4.2 — Best max_depth via Cross-Validation

depths_to_try = range(1, 16)
cv_results = []  # store (depth, mean_score, std_score)

for depth in depths_to_try:
    # Create tree with this depth
    tree = ...
    # Run 5-fold cross-validation on the FULL wine dataset (X_wine, y_wine)
    scores = ...
    cv_results.append((depth, scores.mean(), scores.std()))

# Find the best depth
# best = max(cv_results, key=lambda x: x[1])
# print(f"Best depth: {best[0]}, CV Accuracy: {best[1]:.4f} +/- {best[2]:.4f}")

# Plot CV accuracy vs depth
# hint: use plt.plot and plt.fill_between
pass

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Exercise 4.2 — Best max_depth via Cross-Validation

depths_to_try = range(1, 16)
cv_results = []

for depth in depths_to_try:
    tree = DecisionTreeClassifier(max_depth=depth, random_state=42)
    scores = cross_val_score(tree, X_wine, y_wine, cv=5, scoring="accuracy")
    cv_results.append((depth, scores.mean(), scores.std()))

# Find the best depth
best = max(cv_results, key=lambda x: x[1])
print(f"Best depth: {best[0]}, CV Accuracy: {best[1]:.4f} +/- {best[2]:.4f}")

# Plot
depths_list = [r[0] for r in cv_results]
means = np.array([r[1] for r in cv_results])
stds = np.array([r[2] for r in cv_results])

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(depths_list, means, "o-", linewidth=2, label="Mean CV Accuracy")
ax.fill_between(depths_list, means - stds, means + stds, alpha=0.2, label="+/- 1 Std Dev")
ax.axvline(x=best[0], color="red", linestyle="--", alpha=0.5, label=f"Best depth = {best[0]}")
ax.set_xlabel("max_depth")
ax.set_ylabel("CV Accuracy")
ax.set_title("Cross-Validation: Finding the Best Tree Depth (Wine Dataset)")
ax.set_xticks(depths_list)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("\nAll results:")
for d, m, s in cv_results:
    marker = " <-- best" if d == best[0] else ""
    print(f"  depth={d:2d}:  {m:.4f} +/- {s:.4f}{marker}")

# %% [markdown]
# ### Exercise 4.3 — Precision vs Recall on an Imbalanced Dataset
#
# In many real-world problems, classes are imbalanced (e.g., 95% negative, 5%
# positive). This makes accuracy misleading — a model that always predicts
# "negative" gets 95% accuracy but is useless!
#
# Steps:
# 1. Generate an imbalanced binary dataset using `make_classification` with
#    `weights=[0.9, 0.1]` (90% class 0, 10% class 1)
# 2. Split into train/test
# 3. Train a decision tree and make predictions
# 4. Print accuracy, precision, recall, and F1
# 5. Display the confusion matrix
# 6. Discuss: Is accuracy a good metric here? Which matters more, precision or recall?

# %%
# TODO: Exercise 4.3 — Precision vs Recall on Imbalanced Data

# 1. Generate imbalanced dataset
X_imb, y_imb = make_classification(
    n_samples=1000,
    n_features=10,
    n_informative=5,
    n_redundant=2,
    weights=[0.9, 0.1],   # 90% class 0, 10% class 1
    random_state=42
)
print(f"Class distribution: {np.bincount(y_imb)}")

# 2. Train/test split
X_train_i, X_test_i, y_train_i, y_test_i = ...

# 3. Train a decision tree
clf_imb = ...
y_pred_i = ...

# 4. Print accuracy, precision, recall, F1
# hint: use average="binary" for binary classification
# print(f"Accuracy:  {accuracy_score(y_test_i, y_pred_i):.4f}")
# print(f"Precision: {precision_score(y_test_i, y_pred_i):.4f}")
# print(f"Recall:    {recall_score(y_test_i, y_pred_i):.4f}")
# print(f"F1 Score:  {f1_score(y_test_i, y_pred_i):.4f}")

# 5. Confusion matrix
pass

# 6. Discussion: print your observations
# Which metric matters more here?

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION: Exercise 4.3 — Precision vs Recall on Imbalanced Data

# 1. Generate imbalanced dataset
X_imb, y_imb = make_classification(
    n_samples=1000,
    n_features=10,
    n_informative=5,
    n_redundant=2,
    weights=[0.9, 0.1],
    random_state=42
)
print(f"Class distribution: {np.bincount(y_imb)}")
print(f"Class 0: {np.sum(y_imb == 0)/len(y_imb)*100:.1f}%, "
      f"Class 1: {np.sum(y_imb == 1)/len(y_imb)*100:.1f}%")

# 2. Train/test split
X_train_i, X_test_i, y_train_i, y_test_i = train_test_split(
    X_imb, y_imb, test_size=0.3, random_state=42, stratify=y_imb
)

# 3. Train a decision tree
clf_imb = DecisionTreeClassifier(random_state=42)
clf_imb.fit(X_train_i, y_train_i)
y_pred_i = clf_imb.predict(X_test_i)

# 4. Print metrics
print(f"\nAccuracy:  {accuracy_score(y_test_i, y_pred_i):.4f}")
print(f"Precision: {precision_score(y_test_i, y_pred_i):.4f}")
print(f"Recall:    {recall_score(y_test_i, y_pred_i):.4f}")
print(f"F1 Score:  {f1_score(y_test_i, y_pred_i):.4f}")

# 5. Confusion matrix
fig, ax = plt.subplots(figsize=(7, 6))
ConfusionMatrixDisplay.from_estimator(
    clf_imb, X_test_i, y_test_i,
    display_labels=["Negative (0)", "Positive (1)"],
    cmap="Blues", ax=ax
)
ax.set_title("Confusion Matrix — Imbalanced Dataset")
plt.tight_layout()
plt.show()

# 6. Discussion
print("\nDiscussion:")
print("- Accuracy looks high, but it is misleading! A model predicting all 0s")
print("  would get ~90% accuracy and catch zero positive cases.")
print("- Precision tells us: of the samples we flagged as positive, how many")
print("  actually were? (Are we raising false alarms?)")
print("- Recall tells us: of all actual positives, how many did we detect?")
print("  (Are we missing real cases?)")
print("- F1 Score balances both — it is the best single metric here.")
print("- In domains like fraud or disease detection, RECALL is usually more")
print("  important — missing a real case is worse than a false alarm.")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Decision trees** | Split data by asking yes/no questions, picking splits that maximize purity (minimize Gini impurity or entropy) |
# | **Visualization** | A big advantage of trees — you can see exactly how the model makes decisions |
# | **Evaluation beyond accuracy** | Precision, recall, F1, and ROC/AUC reveal what accuracy hides, especially with imbalanced data |
# | **Overfitting** | The main risk with decision trees — control it with `max_depth` and other hyperparameters |
# | **Cross-validation** | A more reliable performance estimate than a single train/test split |
#
# ## Further reading
#
# - **scikit-learn — Decision trees** (the canonical reference for tree models):
#   https://scikit-learn.org/stable/modules/tree.html
# - **scikit-learn — Model evaluation** (every metric in this notebook, and many more):
#   https://scikit-learn.org/stable/modules/model_evaluation.html
# - **An Introduction to Statistical Learning, ch. 8** (free book; tree-based methods
#   in depth): https://www.statlearning.com/
#
# **Next:** [Module 5 — Unsupervised Learning →](../05_unsupervised_learning/01_clustering.ipynb)
# — what happens when you don't have labels at all.
