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
# # Module 3.1 — First ML Models
#
# In this notebook we go from zero to training real machine learning models.
# We will cover linear regression (predicting numbers) and logistic regression
# (predicting categories), both from scratch and with scikit-learn.
#
# **What you'll learn:**
# - What machine learning actually is
# - The standard ML workflow
# - Train/test splits and why they matter
# - Linear regression from scratch (gradient descent)
# - Linear regression with scikit-learn
# - Logistic regression for classification
# - Evaluation metrics: MSE, R², accuracy

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.datasets import make_regression, make_classification
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

# Reproducibility
np.random.seed(42)

# Plot style
plt.rcParams['figure.figsize'] = (8, 5)
plt.rcParams['figure.dpi'] = 100

print("All imports loaded successfully!")

# %% [markdown]
# ---
# ## 1. What Is Machine Learning?
#
# Traditional programming: you write **rules** that transform input into output.
#
# ```
# Input + Rules  -->  Output
# ```
#
# Machine learning flips this: you give the computer **examples** of inputs and
# outputs, and it **learns the rules** automatically.
#
# ```
# Input + Output  -->  Rules (model)
# ```
#
# **Why is this useful?** Some problems are too complex to program by hand:
# - Recognizing faces in photos
# - Predicting house prices from dozens of features
# - Detecting spam emails
#
# Instead of writing thousands of if/else statements, we let the algorithm
# discover the patterns in the data.
#
# ### Types of ML
#
# | Type | What it does | Example |
# |------|-------------|--------|
# | **Supervised** | Learn from labeled data (input -> known output) | Predict house price |
# | **Unsupervised** | Find structure in unlabeled data | Customer segmentation |
# | **Reinforcement** | Learn by trial and error with rewards | Game-playing AI |
#
# This notebook focuses on **supervised learning** — the most common type.

# %% [markdown]
# ---
# ## 2. The ML Workflow
#
# Every ML project follows roughly the same steps:
#
# ```
# 1. Load data
# 2. Explore & clean data
# 3. Split into train/test sets
# 4. Train a model
# 5. Evaluate the model
# 6. Make predictions on new data
# ```
#
# Let's walk through each step with a concrete example.

# %%
# Step 1: Load data — we'll create a simple synthetic dataset
# Imagine: predicting exam score from hours studied
np.random.seed(42)
hours_studied = np.random.uniform(1, 10, 50)   # 50 students, 1-10 hours
exam_score = 5 * hours_studied + 20 + np.random.normal(0, 5, 50)  # true relationship + noise

data = pd.DataFrame({'hours': hours_studied, 'score': exam_score})
print(data.head(10))
print(f"\nDataset shape: {data.shape}")

# %%
# Step 2: Explore — visualize the relationship
plt.scatter(data['hours'], data['score'], alpha=0.7, edgecolors='k', linewidth=0.5)
plt.xlabel('Hours Studied')
plt.ylabel('Exam Score')
plt.title('Hours Studied vs Exam Score')
plt.grid(True, alpha=0.3)
plt.show()

print(f"Correlation: {data['hours'].corr(data['score']):.3f}")

# %% [markdown]
# There is a clear positive trend: more hours studied tends to mean higher scores.
# A linear model should capture this pattern well.

# %% [markdown]
# ---
# ## 3. Train/Test Split
#
# **The golden rule of ML:** never evaluate your model on the same data you
# trained it on.
#
# Why? Because a model can *memorize* the training data (overfitting) and look
# great on it but fail on new, unseen data. That is useless.
#
# **Solution:** split your data into two parts:
# - **Training set** (typically 70-80%): used to train the model
# - **Test set** (typically 20-30%): held back, only used to evaluate
#
# ```
# All data
# ├── Training set (80%)  --> model learns from this
# └── Test set (20%)      --> model is evaluated on this
# ```

# %%
# Prepare features (X) and target (y)
X = data[['hours']].values   # 2D array, shape (50, 1) — sklearn needs 2D
y = data['score'].values     # 1D array, shape (50,)

# Split: 80% train, 20% test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set: {X_train.shape[0]} samples")
print(f"Test set:     {X_test.shape[0]} samples")
print(f"\nX_train shape: {X_train.shape}")
print(f"y_train shape: {y_train.shape}")

# %%
# Visualize the split
plt.scatter(X_train, y_train, alpha=0.7, label='Train', edgecolors='k', linewidth=0.5)
plt.scatter(X_test, y_test, alpha=0.7, label='Test', marker='s', edgecolors='k', linewidth=0.5)
plt.xlabel('Hours Studied')
plt.ylabel('Exam Score')
plt.title('Train/Test Split')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# %% [markdown]
# > **Key points about `train_test_split`:**
# > - `test_size=0.2` means 20% of data goes to the test set
# > - `random_state=42` makes the split reproducible
# > - The function shuffles the data by default (important for non-random orderings)

# %% [markdown]
# ---
# ## 4. Linear Regression from Scratch
#
# Before using a library, let's understand what a linear regression model
# actually does under the hood.
#
# ### The equation
#
# A linear model predicts the output as a straight line:
#
# $$\hat{y} = w \cdot x + b$$
#
# - $x$ = input feature (hours studied)
# - $\hat{y}$ = predicted output (exam score)
# - $w$ = **weight** (slope) — how much $x$ affects $\hat{y}$
# - $b$ = **bias** (intercept) — the baseline value when $x = 0$
#
# **Goal:** find the values of $w$ and $b$ that make the line fit the data best.

# %%
# Let's visualize what different w and b values look like
x_line = np.linspace(0, 11, 100)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

params = [(2, 30, 'w=2, b=30 (too flat)'),
          (5, 20, 'w=5, b=20 (good fit)'),
          (8, 10, 'w=8, b=10 (too steep)')]

for ax, (w, b, title) in zip(axes, params):
    ax.scatter(X_train, y_train, alpha=0.5, s=20)
    ax.plot(x_line, w * x_line + b, 'r-', linewidth=2)
    ax.set_title(title)
    ax.set_xlabel('Hours')
    ax.set_ylabel('Score')
    ax.set_ylim(10, 80)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()


# %% [markdown]
# ### The cost function (MSE)
#
# How do we measure how "good" a line is? We use a **cost function** that
# measures the error between our predictions and the actual values.
#
# The most common one is **Mean Squared Error (MSE)**:
#
# $$\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2$$
#
# - Small MSE = predictions are close to actual values (good)
# - Large MSE = predictions are far off (bad)
#
# Our goal is to **minimize** the MSE by finding the best $w$ and $b$.

# %%
def compute_mse(X, y, w, b):
    """Compute Mean Squared Error for given parameters."""
    y_pred = w * X + b
    mse = np.mean((y - y_pred) ** 2)
    return mse

# Calculate MSE for our three parameter choices
X_flat = X_train.flatten()
for w, b, label in params:
    mse = compute_mse(X_flat, y_train, w, b)
    print(f"{label:30s} --> MSE = {mse:.2f}")

# %%
# Let's visualize how MSE changes as we vary the weight w
# (keeping b fixed at 20 for simplicity)
w_values = np.linspace(-5, 15, 200)
mse_values = [compute_mse(X_flat, y_train, w, 20) for w in w_values]

plt.plot(w_values, mse_values, linewidth=2)
plt.xlabel('Weight (w)')
plt.ylabel('MSE')
plt.title('Cost Function: MSE vs Weight')
plt.grid(True, alpha=0.3)

# Mark the minimum
best_w_idx = np.argmin(mse_values)
plt.scatter(w_values[best_w_idx], mse_values[best_w_idx],
            color='red', s=100, zorder=5, label=f'Minimum at w={w_values[best_w_idx]:.2f}')
plt.legend()
plt.show()

print(f"Best weight (with b=20): w = {w_values[best_w_idx]:.2f}")


# %% [markdown]
# The cost curve is a smooth "bowl" shape. The bottom of the bowl is where
# the model fits best. We can find this minimum using **gradient descent**.
#
# ### Gradient descent — finding the minimum
#
# Gradient descent is an algorithm that iteratively adjusts $w$ and $b$ to
# reduce the cost:
#
# 1. Start with random values of $w$ and $b$
# 2. Compute the gradient (slope of the cost function)
# 3. Update the parameters in the direction that reduces cost
# 4. Repeat until convergence
#
# The update rules are:
#
# $$w = w - \alpha \cdot \frac{\partial \text{MSE}}{\partial w}$$
# $$b = b - \alpha \cdot \frac{\partial \text{MSE}}{\partial b}$$
#
# Where $\alpha$ is the **learning rate** — how big a step we take each time.
#
# The partial derivatives are:
#
# $$\frac{\partial \text{MSE}}{\partial w} = \frac{-2}{n} \sum (y_i - \hat{y}_i) \cdot x_i$$
# $$\frac{\partial \text{MSE}}{\partial b} = \frac{-2}{n} \sum (y_i - \hat{y}_i)$$

# %%
def gradient_descent(X, y, learning_rate=0.01, n_iterations=1000):
    """Simple gradient descent for linear regression."""
    n = len(X)
    w = 0.0  # start with zero
    b = 0.0
    history = []  # track cost over iterations

    for i in range(n_iterations):
        # Predictions with current parameters
        y_pred = w * X + b

        # Compute gradients
        dw = (-2 / n) * np.sum((y - y_pred) * X)
        db = (-2 / n) * np.sum(y - y_pred)

        # Update parameters
        w = w - learning_rate * dw
        b = b - learning_rate * db

        # Track cost
        cost = np.mean((y - y_pred) ** 2)
        history.append(cost)

    return w, b, history

# Run gradient descent on our training data
w_gd, b_gd, cost_history = gradient_descent(X_flat, y_train, learning_rate=0.01, n_iterations=500)

print(f"Learned parameters: w = {w_gd:.4f}, b = {b_gd:.4f}")
print(f"(True values: w = 5, b = 20)")
print(f"Final MSE: {cost_history[-1]:.4f}")

# %%
# Visualize gradient descent convergence
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: cost over iterations
axes[0].plot(cost_history, linewidth=2)
axes[0].set_xlabel('Iteration')
axes[0].set_ylabel('MSE')
axes[0].set_title('Gradient Descent Convergence')
axes[0].grid(True, alpha=0.3)

# Right: the learned line on the data
axes[1].scatter(X_train, y_train, alpha=0.7, edgecolors='k', linewidth=0.5, label='Training data')
x_line = np.linspace(0, 11, 100)
axes[1].plot(x_line, w_gd * x_line + b_gd, 'r-', linewidth=2,
             label=f'Learned: y = {w_gd:.1f}x + {b_gd:.1f}')
axes[1].set_xlabel('Hours Studied')
axes[1].set_ylabel('Exam Score')
axes[1].set_title('Learned Linear Model')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# %% [markdown]
# The cost drops quickly and then levels off — the model has converged.
# Our learned line fits the data well, close to the true relationship
# (y = 5x + 20).

# %% [markdown]
# ---
# ## 5. Linear Regression with scikit-learn
#
# In practice, you rarely implement gradient descent yourself. scikit-learn
# provides `LinearRegression` that handles everything for you.
#
# ### 5a. Using our hours-studied dataset

# %%
# Step 4: Train the model
model = LinearRegression()
model.fit(X_train, y_train)

print(f"sklearn learned:  w = {model.coef_[0]:.4f}, b = {model.intercept_:.4f}")
print(f"Our GD learned:   w = {w_gd:.4f}, b = {b_gd:.4f}")
print(f"True values:      w = 5.0000, b = 20.0000")

# %%
# Step 5: Evaluate on the TEST set (never on training set!)
y_pred = model.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Test MSE: {mse:.4f}")
print(f"Test R^2: {r2:.4f}")
print(f"\nR^2 interpretation: the model explains {r2*100:.1f}% of the variance in scores")

# %% [markdown]
# > **R-squared (R²)** ranges from 0 to 1:
# > - **R² = 1.0** means the model perfectly explains the data
# > - **R² = 0.0** means the model is no better than predicting the mean
# > - **R² < 0** is possible — the model is *worse* than the mean

# %%
# Plot predictions vs actual
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: predictions vs actual
axes[0].scatter(y_test, y_pred, alpha=0.7, edgecolors='k', linewidth=0.5)
# Perfect prediction line
min_val = min(y_test.min(), y_pred.min())
max_val = max(y_test.max(), y_pred.max())
axes[0].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect prediction')
axes[0].set_xlabel('Actual Score')
axes[0].set_ylabel('Predicted Score')
axes[0].set_title('Predictions vs Actual')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Right: residuals (errors)
residuals = y_test - y_pred
axes[1].scatter(y_pred, residuals, alpha=0.7, edgecolors='k', linewidth=0.5)
axes[1].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[1].set_xlabel('Predicted Score')
axes[1].set_ylabel('Residual (Actual - Predicted)')
axes[1].set_title('Residual Plot')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print(f"Mean residual: {residuals.mean():.4f} (should be close to 0)")
print(f"Std of residuals: {residuals.std():.4f}")

# %% [markdown]
# **How to read these plots:**
# - **Predictions vs Actual:** points close to the red dashed line = good predictions
# - **Residual plot:** points should be randomly scattered around zero with no pattern.
#   If you see a curve or funnel shape, the model is missing something.

# %% [markdown]
# ### 5b. Using `make_regression` — synthetic multi-feature data

# %%
# Generate a more complex dataset with multiple features
X_reg, y_reg = make_regression(n_samples=200, n_features=3, noise=15, random_state=42)

print(f"Features shape: {X_reg.shape}")
print(f"Target shape: {y_reg.shape}")
print(f"\nFirst 5 rows of features:")
print(X_reg[:5])

# %%
# Train/test split
X_r_train, X_r_test, y_r_train, y_r_test = train_test_split(
    X_reg, y_reg, test_size=0.2, random_state=42
)

# Train
model_reg = LinearRegression()
model_reg.fit(X_r_train, y_r_train)

# Evaluate
y_r_pred = model_reg.predict(X_r_test)
print(f"R^2 score: {r2_score(y_r_test, y_r_pred):.4f}")
print(f"MSE:       {mean_squared_error(y_r_test, y_r_pred):.4f}")
print(f"\nCoefficients: {model_reg.coef_}")
print(f"Intercept:    {model_reg.intercept_:.4f}")

# %% [markdown]
# ### 5c. Synthetic housing dataset
#
# The classic Boston housing dataset is deprecated due to ethical concerns.
# Let's create our own simple housing dataset to practice on.

# %%
# Create a synthetic housing dataset
np.random.seed(42)
n_houses = 300

sqft = np.random.uniform(600, 4000, n_houses)         # square footage
bedrooms = np.random.randint(1, 6, n_houses)           # number of bedrooms
age = np.random.uniform(0, 50, n_houses)               # age of house in years
distance_city = np.random.uniform(1, 30, n_houses)     # distance to city center (miles)

# Price formula: larger, newer, closer to city = more expensive
price = (
    80 * sqft
    + 15000 * bedrooms
    - 2000 * age
    - 5000 * distance_city
    + 50000
    + np.random.normal(0, 30000, n_houses)  # noise
)

housing = pd.DataFrame({
    'sqft': sqft,
    'bedrooms': bedrooms,
    'age': age,
    'distance_city': distance_city,
    'price': price
})

print(housing.head())
print(f"\n{housing.describe().round(1)}")

# %%
# Explore the relationships
fig, axes = plt.subplots(1, 4, figsize=(18, 4))

for ax, col in zip(axes, ['sqft', 'bedrooms', 'age', 'distance_city']):
    ax.scatter(housing[col], housing['price'], alpha=0.3, s=10)
    ax.set_xlabel(col)
    ax.set_ylabel('Price ($)')
    ax.set_title(f'Price vs {col}')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# %%
# Train a linear regression model on the housing data
X_house = housing[['sqft', 'bedrooms', 'age', 'distance_city']].values
y_house = housing['price'].values

X_h_train, X_h_test, y_h_train, y_h_test = train_test_split(
    X_house, y_house, test_size=0.2, random_state=42
)

model_house = LinearRegression()
model_house.fit(X_h_train, y_h_train)

y_h_pred = model_house.predict(X_h_test)

print(f"R^2: {r2_score(y_h_test, y_h_pred):.4f}")
print(f"MSE: {mean_squared_error(y_h_test, y_h_pred):.2f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_h_test, y_h_pred)):.2f}")
print(f"\nCoefficients:")
for name, coef in zip(['sqft', 'bedrooms', 'age', 'distance_city'], model_house.coef_):
    print(f"  {name:15s}: {coef:>10.2f}")
print(f"  {'intercept':15s}: {model_house.intercept_:>10.2f}")

# %%
# Plot predictions vs actual for housing data
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].scatter(y_h_test, y_h_pred, alpha=0.5, s=15, edgecolors='k', linewidth=0.3)
lims = [min(y_h_test.min(), y_h_pred.min()), max(y_h_test.max(), y_h_pred.max())]
axes[0].plot(lims, lims, 'r--', linewidth=2, label='Perfect prediction')
axes[0].set_xlabel('Actual Price ($)')
axes[0].set_ylabel('Predicted Price ($)')
axes[0].set_title('Housing: Predictions vs Actual')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

h_residuals = y_h_test - y_h_pred
axes[1].scatter(y_h_pred, h_residuals, alpha=0.5, s=15, edgecolors='k', linewidth=0.3)
axes[1].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[1].set_xlabel('Predicted Price ($)')
axes[1].set_ylabel('Residual ($)')
axes[1].set_title('Housing: Residual Plot')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()


# %% [markdown]
# The learned coefficients are close to our true values (80 for sqft, 15000 for
# bedrooms, -2000 for age, -5000 for distance). The model recovers the underlying
# relationships from the noisy data.

# %% [markdown]
# ---
# ## 6. Logistic Regression
#
# Linear regression predicts **continuous** values (prices, scores, temperatures).
# But what if we want to predict **categories** — yes/no, spam/not-spam,
# pass/fail?
#
# That is **classification**, and **logistic regression** is the simplest
# classification algorithm.
#
# ### The key idea
#
# Instead of predicting a number directly, logistic regression predicts the
# **probability** that an example belongs to class 1 (the positive class).
# It does this by passing the linear output through a **sigmoid function**:
#
# $$P(y=1) = \sigma(w \cdot x + b) = \frac{1}{1 + e^{-(wx+b)}}$$

# %%
# The sigmoid function
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

# Plot it
z = np.linspace(-8, 8, 200)

plt.figure(figsize=(8, 5))
plt.plot(z, sigmoid(z), linewidth=2.5, color='blue')
plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Decision boundary (0.5)')
plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
plt.axhline(y=1, color='gray', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='gray', linestyle='-', alpha=0.3)
plt.xlabel('z = wx + b')
plt.ylabel('sigmoid(z) = probability')
plt.title('The Sigmoid Function')
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(-0.05, 1.05)
plt.show()

print("Key properties:")
print(f"  sigmoid(-10) = {sigmoid(-10):.6f}  (very negative -> close to 0)")
print(f"  sigmoid(0)   = {sigmoid(0):.6f}  (zero -> exactly 0.5)")
print(f"  sigmoid(10)  = {sigmoid(10):.6f}  (very positive -> close to 1)")

# %% [markdown]
# **How the sigmoid works:**
# - It squashes any number into the range (0, 1) — perfect for probabilities
# - Large positive inputs -> probability close to 1 (class 1)
# - Large negative inputs -> probability close to 0 (class 0)
# - Input of 0 -> probability of exactly 0.5 (uncertain)
#
# **Decision rule:** if probability >= 0.5, predict class 1; else predict class 0.

# %% [markdown]
# ### Logistic regression with scikit-learn

# %%
# Generate a binary classification dataset
X_clf, y_clf = make_classification(
    n_samples=300,
    n_features=2,         # 2 features so we can visualize
    n_informative=2,
    n_redundant=0,
    n_clusters_per_class=1,
    random_state=42
)

print(f"Features shape: {X_clf.shape}")
print(f"Target shape: {y_clf.shape}")
print(f"Classes: {np.unique(y_clf)} (counts: {np.bincount(y_clf)})")

# %%
# Visualize the data
plt.figure(figsize=(8, 6))
scatter = plt.scatter(X_clf[:, 0], X_clf[:, 1], c=y_clf, cmap='RdYlBu',
                      alpha=0.7, edgecolors='k', linewidth=0.5)
plt.colorbar(scatter, label='Class')
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.title('Binary Classification Dataset')
plt.grid(True, alpha=0.3)
plt.show()

# %%
# Split, train, evaluate
X_c_train, X_c_test, y_c_train, y_c_test = train_test_split(
    X_clf, y_clf, test_size=0.2, random_state=42
)

clf = LogisticRegression(random_state=42)
clf.fit(X_c_train, y_c_train)

# Predictions
y_c_pred = clf.predict(X_c_test)
y_c_proba = clf.predict_proba(X_c_test)  # probabilities for each class

acc = accuracy_score(y_c_test, y_c_pred)
print(f"Accuracy: {acc:.4f} ({acc*100:.1f}%)")
print(f"\nFirst 10 predictions vs actual:")
print(f"  Predicted:    {y_c_pred[:10]}")
print(f"  Actual:       {y_c_test[:10]}")
print(f"  Probabilities (class 1): {y_c_proba[:10, 1].round(3)}")

# %%
# Visualize the decision boundary
fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# Left: decision boundary
x_min, x_max = X_clf[:, 0].min() - 1, X_clf[:, 0].max() + 1
y_min, y_max = X_clf[:, 1].min() - 1, X_clf[:, 1].max() + 1
xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200),
                      np.linspace(y_min, y_max, 200))
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

axes[0].contourf(xx, yy, Z, alpha=0.3, cmap='RdYlBu')
axes[0].scatter(X_c_test[:, 0], X_c_test[:, 1], c=y_c_test, cmap='RdYlBu',
                edgecolors='k', linewidth=0.5)
axes[0].set_xlabel('Feature 1')
axes[0].set_ylabel('Feature 2')
axes[0].set_title('Decision Boundary (Test Data)')

# Right: predicted probabilities
axes[1].scatter(X_c_test[:, 0], X_c_test[:, 1], c=y_c_proba[:, 1],
                cmap='RdYlBu', edgecolors='k', linewidth=0.5)
axes[1].set_xlabel('Feature 1')
axes[1].set_ylabel('Feature 2')
axes[1].set_title('Predicted Probabilities')

plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## 7. Exercises
#
# Now it's your turn! Complete the exercises below to solidify your
# understanding of linear and logistic regression.

# %% [markdown]
# ### Exercise 3.1 — Implement gradient descent
#
# Complete the `my_gradient_descent` function below. It should:
# 1. Initialize `w` and `b` to 0
# 2. For each iteration, compute predictions, gradients, and update `w` and `b`
# 3. Return the learned `w`, `b`, and the cost history
#
# Then run it on the provided data and print the learned parameters.

# %%
# Exercise data
np.random.seed(99)
ex_X = np.random.uniform(0, 10, 80)
ex_y = 3 * ex_X + 7 + np.random.normal(0, 3, 80)  # true: w=3, b=7

# TODO: Complete this function
def my_gradient_descent(X, y, learning_rate=0.01, n_iterations=500):
    n = len(X)
    w = 0.0
    b = 0.0
    history = []

    for i in range(n_iterations):
        # TODO: Compute predictions
        y_pred = ...

        # TODO: Compute gradients dw and db
        dw = ...
        db = ...

        # TODO: Update w and b
        w = ...
        b = ...

        # Track cost
        cost = np.mean((y - y_pred) ** 2)
        history.append(cost)

    return w, b, history

# TODO: Run gradient descent and print results
# w, b, history = my_gradient_descent(...)
# print(f"Learned: w = {w:.4f}, b = {b:.4f}")
# print(f"True:    w = 3.0000, b = 7.0000")


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
np.random.seed(99)
ex_X = np.random.uniform(0, 10, 80)
ex_y = 3 * ex_X + 7 + np.random.normal(0, 3, 80)

def my_gradient_descent(X, y, learning_rate=0.01, n_iterations=500):
    n = len(X)
    w = 0.0
    b = 0.0
    history = []

    for i in range(n_iterations):
        y_pred = w * X + b
        dw = (-2 / n) * np.sum((y - y_pred) * X)
        db = (-2 / n) * np.sum(y - y_pred)
        w = w - learning_rate * dw
        b = b - learning_rate * db

        cost = np.mean((y - y_pred) ** 2)
        history.append(cost)

    return w, b, history

w, b, history = my_gradient_descent(ex_X, ex_y, learning_rate=0.01, n_iterations=500)
print(f"Learned: w = {w:.4f}, b = {b:.4f}")
print(f"True:    w = 3.0000, b = 7.0000")
print(f"Final MSE: {history[-1]:.4f}")

# Plot convergence
plt.plot(history)
plt.xlabel('Iteration')
plt.ylabel('MSE')
plt.title('Exercise 3.1: Gradient Descent Convergence')
plt.grid(True, alpha=0.3)
plt.show()

# %% [markdown]
# ### Exercise 3.2 — Train a linear regression model and compute R²
#
# Using scikit-learn's `LinearRegression`:
# 1. Generate a dataset with `make_regression(n_samples=150, n_features=5, noise=20, random_state=7)`
# 2. Split it 80/20 with `random_state=7`
# 3. Train a `LinearRegression` model
# 4. Compute and print the R² score and MSE on the test set
# 5. Print the model's coefficients

# %%
# TODO: Generate data
# X_ex2, y_ex2 = ...

# TODO: Train/test split
# X_ex2_train, X_ex2_test, y_ex2_train, y_ex2_test = ...

# TODO: Train model
# model_ex2 = ...

# TODO: Evaluate
# print(f"R^2: {...}")
# print(f"MSE: {...}")
# print(f"Coefficients: {...}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
X_ex2, y_ex2 = make_regression(n_samples=150, n_features=5, noise=20, random_state=7)

X_ex2_train, X_ex2_test, y_ex2_train, y_ex2_test = train_test_split(
    X_ex2, y_ex2, test_size=0.2, random_state=7
)

model_ex2 = LinearRegression()
model_ex2.fit(X_ex2_train, y_ex2_train)

y_ex2_pred = model_ex2.predict(X_ex2_test)

print(f"R^2: {r2_score(y_ex2_test, y_ex2_pred):.4f}")
print(f"MSE: {mean_squared_error(y_ex2_test, y_ex2_pred):.4f}")
print(f"Coefficients: {model_ex2.coef_.round(4)}")
print(f"Intercept: {model_ex2.intercept_:.4f}")

# %% [markdown]
# ### Exercise 3.3 — Train logistic regression and compute accuracy
#
# 1. Generate a classification dataset with `make_classification(n_samples=400, n_features=4, n_informative=3, n_redundant=1, random_state=21)`
# 2. Split 75/25 with `random_state=21`
# 3. Train a `LogisticRegression` model
# 4. Print accuracy on the test set
# 5. Print the first 15 predictions vs actual values

# %%
# TODO: Generate classification data
# X_ex3, y_ex3 = ...

# TODO: Split
# X_ex3_train, X_ex3_test, y_ex3_train, y_ex3_test = ...

# TODO: Train logistic regression
# clf_ex3 = ...

# TODO: Evaluate
# print(f"Accuracy: {...}")
# print(f"First 15 predicted: {...}")
# print(f"First 15 actual:    {...}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
X_ex3, y_ex3 = make_classification(
    n_samples=400, n_features=4, n_informative=3,
    n_redundant=1, random_state=21
)

X_ex3_train, X_ex3_test, y_ex3_train, y_ex3_test = train_test_split(
    X_ex3, y_ex3, test_size=0.25, random_state=21
)

clf_ex3 = LogisticRegression(random_state=21)
clf_ex3.fit(X_ex3_train, y_ex3_train)

y_ex3_pred = clf_ex3.predict(X_ex3_test)
acc_ex3 = accuracy_score(y_ex3_test, y_ex3_pred)

print(f"Accuracy: {acc_ex3:.4f} ({acc_ex3*100:.1f}%)")
print(f"First 15 predicted: {y_ex3_pred[:15]}")
print(f"First 15 actual:    {y_ex3_test[:15]}")

# %% [markdown]
# ### Exercise 3.4 — Compare predictions with different features
#
# Using the synthetic housing dataset from Section 5c:
# 1. Train a model using **only** `sqft` as the feature
# 2. Train another model using **all 4** features
# 3. Compare their R² scores on the test set
# 4. Which model is better, and why?

# %%
# TODO: Model A — only sqft
# X_sqft = housing[['sqft']].values
# X_sqft_train, X_sqft_test, y_sqft_train, y_sqft_test = ...
# model_a = ...
# r2_a = ...

# TODO: Model B — all features (already trained above, but do it fresh)
# X_all = housing[['sqft', 'bedrooms', 'age', 'distance_city']].values
# X_all_train, X_all_test, y_all_train, y_all_test = ...
# model_b = ...
# r2_b = ...

# TODO: Print comparison
# print(f"Model A (sqft only) R^2: {...}")
# print(f"Model B (all features) R^2: {...}")
# print(f"Which is better and why?")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION

# Model A: sqft only
X_sqft = housing[['sqft']].values
y_price = housing['price'].values
X_sqft_train, X_sqft_test, y_sqft_train, y_sqft_test = train_test_split(
    X_sqft, y_price, test_size=0.2, random_state=42
)
model_a = LinearRegression()
model_a.fit(X_sqft_train, y_sqft_train)
r2_a = r2_score(y_sqft_test, model_a.predict(X_sqft_test))

# Model B: all features
X_all = housing[['sqft', 'bedrooms', 'age', 'distance_city']].values
X_all_train, X_all_test, y_all_train, y_all_test = train_test_split(
    X_all, y_price, test_size=0.2, random_state=42
)
model_b = LinearRegression()
model_b.fit(X_all_train, y_all_train)
r2_b = r2_score(y_all_test, model_b.predict(X_all_test))

print(f"Model A (sqft only)    R^2: {r2_a:.4f}")
print(f"Model B (all features) R^2: {r2_b:.4f}")
print(f"\nModel B is better because it uses more information.")
print(f"Bedrooms, age, and distance all contribute to the price.")
print(f"Using only sqft ignores these factors, so the model explains")
print(f"less of the variance in prices.")

# %% [markdown]
# ## Key Takeaways
#
# - **Machine learning** learns patterns from data instead of explicit programming
# - The **ML workflow** is: load -> explore -> split -> train -> evaluate -> predict
# - Always use a **train/test split** to evaluate honestly
# - **Linear regression** fits a line to predict continuous values (y = wx + b)
# - **Gradient descent** finds the best parameters by minimizing the cost function
# - **Logistic regression** uses the sigmoid function for binary classification
# - **R²** measures regression quality; **accuracy** measures classification quality
# - More relevant features generally improve model performance
#
# ---
# **Next:** [Decision Trees ->](../04_classification_and_trees/01_decision_trees.ipynb)
