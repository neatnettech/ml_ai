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
# # Module 10 — Capstone Project: Predict House Prices
#
# **Purpose:** Run the complete ML workflow solo — EDA to tuned model — and produce
# the **capstone deliverable of the Pure ML track**: a house-price predictor built end
# to end. This is a self-directed capstone: by design there is no separate
# guided-exercise section — every step is a TODO you complete yourself, with hidden
# solutions if you get stuck.
#
# **Prerequisites:** Modules 1–6 (the full Pure ML track).
#
# Congratulations on making it to the final module! This capstone project ties
# together everything you have learned across all previous modules into one
# complete, end-to-end machine learning project.
#
# **Your mission:** Build a model that predicts house prices based on property
# features like square footage, number of bedrooms, age, and more.
#
# You will work through the full ML workflow:
#
# 1. **Generate & Load Data** — Create a synthetic housing dataset
# 2. **Exploratory Data Analysis** — Understand the data before modeling
# 3. **Data Preprocessing** — Clean, scale, and split the data
# 4. **Model Building** — Train and compare multiple models
# 5. **Model Evaluation** — Visualize and compare model performance
# 6. **Hyperparameter Tuning** — Squeeze out better performance
# 7. **Final Predictions & Conclusions** — Summarize your findings
#
# Each step has guidance, TODO exercises for you to complete, and hidden
# solutions you can reveal if you get stuck. Try to complete each exercise
# on your own first — that is where the real learning happens!
#
# Let's build something great.

# %%
# All imports for the project
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Plot settings
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 100
sns.set_style('whitegrid')

# Reproducibility
np.random.seed(42)

print("All imports loaded successfully. Let's go!")

# %% [markdown]
# ---
# ## Step 1: Generate & Load Data
#
# In real projects you would load data from a CSV, database, or API. Here we
# will generate a synthetic housing dataset so you do not need any external
# downloads. The dataset will have realistic relationships between features
# and the target price.
#
# **Features:**
# - `square_feet` — Total living area (800-4000 sq ft)
# - `bedrooms` — Number of bedrooms (1-6)
# - `bathrooms` — Number of bathrooms (1-4)
# - `age` — Age of the house in years (0-80)
# - `garage_size` — Number of garage spaces (0-3)
# - `neighborhood_score` — Quality of neighborhood (1-10)
# - `distance_to_city` — Distance to city center in miles (1-30)
#
# **Target:**
# - `price` — House sale price in dollars

# %%
# Generate synthetic housing data
n_samples = 1000

# Features
square_feet = np.random.uniform(800, 4000, n_samples)
bedrooms = np.random.randint(1, 7, n_samples)
bathrooms = np.random.randint(1, 5, n_samples)
age = np.random.uniform(0, 80, n_samples)
garage_size = np.random.randint(0, 4, n_samples)
neighborhood_score = np.random.uniform(1, 10, n_samples)
distance_to_city = np.random.uniform(1, 30, n_samples)

# Target: price is a function of features + noise
# This creates realistic, learnable relationships
price = (
    150 * square_feet
    + 15000 * bedrooms
    + 20000 * bathrooms
    - 2000 * age
    + 25000 * garage_size
    + 30000 * neighborhood_score
    - 5000 * distance_to_city
    + np.random.normal(0, 30000, n_samples)  # noise
)

# Ensure no negative prices
price = np.maximum(price, 50000)

# Build DataFrame
df = pd.DataFrame({
    'square_feet': square_feet,
    'bedrooms': bedrooms,
    'bathrooms': bathrooms,
    'age': age,
    'garage_size': garage_size,
    'neighborhood_score': neighborhood_score,
    'distance_to_city': distance_to_city,
    'price': price
})

# Introduce a few missing values (realistic!)
# Randomly set ~2% of values to NaN in some columns
for col in ['square_feet', 'age', 'neighborhood_score']:
    mask = np.random.random(n_samples) < 0.02
    df.loc[mask, col] = np.nan

print(f"Dataset shape: {df.shape}")
print(f"\nFirst 5 rows:")
df.head()

# %% [markdown]
# ---
# ## Step 2: Exploratory Data Analysis (EDA)
#
# Before building any model, you need to **understand your data**. EDA helps
# you spot patterns, outliers, missing values, and relationships that will
# guide your modeling decisions.
#
# Think of EDA as getting to know your data before asking it questions.

# %% [markdown]
# ### 2.1 Basic Statistics
#
# Start with `.info()` and `.describe()` to get a high-level overview.
# Check for missing values, data types, and basic statistics like mean,
# min, max, and standard deviation.

# %%
# TODO: Display basic info about the dataset
# Use df.info() to see column types and non-null counts
# Use df.describe() to see summary statistics
# Use df.isnull().sum() to count missing values per column


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
print("=== Dataset Info ===")
df.info()

print("\n=== Summary Statistics ===")
display(df.describe())

print("\n=== Missing Values ===")
print(df.isnull().sum())

# %% [markdown]
# ### 2.2 Target Variable Distribution
#
# Plot a histogram of the target variable (`price`). Understanding its
# distribution helps you choose the right model and evaluation metrics.
# Is it roughly normal? Skewed? Are there extreme outliers?

# %%
# TODO: Plot a histogram of the price column
# Include a title and axis labels
# Hint: plt.hist() or df['price'].hist()


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(df['price'], bins=40, edgecolor='black', alpha=0.7, color='steelblue')
ax.set_title('Distribution of House Prices', fontsize=14)
ax.set_xlabel('Price ($)', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.axvline(df['price'].mean(), color='red', linestyle='--', label=f"Mean: ${df['price'].mean():,.0f}")
ax.axvline(df['price'].median(), color='orange', linestyle='--', label=f"Median: ${df['price'].median():,.0f}")
ax.legend(fontsize=11)
plt.tight_layout()
plt.show()

print(f"Price range: ${df['price'].min():,.0f} - ${df['price'].max():,.0f}")
print(f"Mean price: ${df['price'].mean():,.0f}")
print(f"Median price: ${df['price'].median():,.0f}")

# %% [markdown]
# ### 2.3 Correlation Heatmap
#
# A correlation heatmap shows how strongly each pair of variables is
# linearly related. Values close to +1 or -1 indicate strong relationships.
# This helps you identify which features are most predictive of price.

# %%
# TODO: Create a correlation heatmap
# 1. Compute the correlation matrix with df.corr()
# 2. Plot it using sns.heatmap() with annotations
# Hint: sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm')


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
corr_matrix = df.corr(numeric_only=True)

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, square=True, linewidths=0.5, ax=ax)
ax.set_title('Feature Correlation Heatmap', fontsize=14)
plt.tight_layout()
plt.show()

print("\nCorrelation with price (sorted):")
print(corr_matrix['price'].drop('price').sort_values(ascending=False))

# %% [markdown]
# ### 2.4 Scatter Plots of Top Features vs Price
#
# Now visualize the relationship between the most correlated features and
# the target. Scatter plots let you see if the relationship is linear,
# non-linear, or noisy.

# %%
# TODO: Create scatter plots for the top 3 features most correlated with price
# Use subplots to show them side by side
# Hint: Look at the correlation values from the heatmap above
# The top features should be: square_feet, neighborhood_score, and one more


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# Get top 3 correlated features (by absolute correlation)
price_corr = corr_matrix['price'].drop('price').abs().sort_values(ascending=False)
top_3_features = price_corr.head(3).index.tolist()
print(f"Top 3 correlated features: {top_3_features}")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for i, feature in enumerate(top_3_features):
    axes[i].scatter(df[feature], df['price'], alpha=0.3, s=15, color='steelblue')
    axes[i].set_xlabel(feature, fontsize=12)
    axes[i].set_ylabel('Price ($)', fontsize=12)
    corr_val = corr_matrix.loc[feature, 'price']
    axes[i].set_title(f'{feature} vs Price (r={corr_val:.2f})', fontsize=12)

plt.tight_layout()
plt.show()

# %% [markdown]
# ### 2.5 Identify the Most Important Features
#
# Based on your EDA above, which 3 features do you think are the most
# important for predicting house prices? Write your answer below and
# explain why.

# %%
# TODO: List the 3 most important features and briefly explain why
# Replace the ... with your answers

most_important_features = [
    "...",  # Feature 1 — why?
    "...",  # Feature 2 — why?
    "...",  # Feature 3 — why?
]

print("My top 3 features:", most_important_features)

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
most_important_features = [
    "square_feet",          # Highest positive correlation with price
    "neighborhood_score",   # Second highest positive correlation
    "age",                  # Strong negative correlation (older = cheaper)
]

print("Top 3 features:", most_important_features)
print("\nReasoning:")
print("- square_feet has the strongest positive correlation with price.")
print("  Larger homes are worth more — this makes intuitive sense.")
print("- neighborhood_score is the second strongest predictor.")
print("  Location quality is a major driver of home value.")
print("- age has a strong negative correlation. Older homes lose value")
print("  due to wear, outdated features, and maintenance needs.")

# %% [markdown]
# ---
# ## Step 3: Data Preprocessing
#
# Raw data is rarely ready for modeling. You need to:
# 1. **Handle missing values** — Models cannot work with NaN
# 2. **Scale features** — Put all features on similar ranges so no single
#    feature dominates due to its scale
# 3. **Split the data** — Keep a test set that the model never sees during
#    training, so you can evaluate honestly
#
# This step uses skills from Modules 1-2 (Pandas, NumPy) and Module 3
# (train/test splits, preprocessing).

# %% [markdown]
# ### 3.1 Handle Missing Values
#
# Check how many missing values exist and decide on a strategy.
# Common approaches: drop rows, fill with mean/median, or use more
# sophisticated imputation. For small amounts of missing data, filling
# with the median is usually a safe choice.

# %%
# TODO: Handle missing values
# 1. Check how many missing values exist (df.isnull().sum())
# 2. Fill missing values with the median of each column
# Hint: df.fillna(df.median(numeric_only=True), inplace=True)
# 3. Verify there are no more missing values


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
print("Missing values BEFORE:")
print(df.isnull().sum())
print()

# Fill with median (robust to outliers)
df.fillna(df.median(numeric_only=True), inplace=True)

print("Missing values AFTER:")
print(df.isnull().sum())
print("\nAll missing values handled!")

# %% [markdown]
# ### 3.2 Feature Scaling and Train/Test Split
#
# Now prepare the data for modeling:
# 1. Separate features (X) from the target (y)
# 2. Split into training and test sets (80/20)
# 3. Scale features using `StandardScaler` (zero mean, unit variance)
#
# **Important:** Fit the scaler on training data only, then transform both
# train and test. This prevents data leakage.

# %%
# TODO: Write the complete preprocessing pipeline
# 1. Define X (features) and y (target)
#    X = df.drop('price', axis=1)
#    y = df['price']
#
# 2. Split into train/test (80/20, random_state=42)
#    Use train_test_split from sklearn
#
# 3. Scale features with StandardScaler
#    - Create the scaler
#    - Fit on X_train and transform X_train
#    - Only transform X_test (do NOT fit on test data!)
#
# 4. Print the shapes of X_train, X_test, y_train, y_test


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# 1. Separate features and target
X = df.drop('price', axis=1)
y = df['price']

feature_names = X.columns.tolist()
print(f"Features: {feature_names}")
print(f"Target: price")

# 2. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3. Feature scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # fit + transform on train
X_test_scaled = scaler.transform(X_test)         # only transform on test

# 4. Print shapes
print(f"\nTraining set: X={X_train_scaled.shape}, y={y_train.shape}")
print(f"Test set:     X={X_test_scaled.shape}, y={y_test.shape}")
print(f"\nScaling check (train means ~0): {X_train_scaled.mean(axis=0).round(2)}")
print(f"Scaling check (train stds ~1):  {X_train_scaled.std(axis=0).round(2)}")

# %% [markdown]
# ---
# ## Step 4: Model Building
#
# Now the fun part! You will train three different regression models and
# compare their performance:
#
# 1. **Linear Regression** — The simplest baseline. Assumes a linear
#    relationship between features and target. (Module 3)
# 2. **Random Forest** — An ensemble of decision trees that averages
#    their predictions. Handles non-linearity well. (Module 6)
# 3. **Gradient Boosting** — Builds trees sequentially, each one
#    correcting the errors of the previous. Often the strongest
#    performer. (Module 6)
#
# **Metrics we will use:**
# - **R-squared (R2)** — Proportion of variance explained (1.0 = perfect)
# - **MAE** — Mean Absolute Error (average dollar error)
# - **RMSE** — Root Mean Squared Error (penalizes large errors more)

# %% [markdown]
# ### 4.1 Train Linear Regression (Baseline)

# %%
# TODO: Train a Linear Regression model
# 1. Create a LinearRegression() model
# 2. Fit it on X_train_scaled, y_train
# 3. Make predictions on X_test_scaled
# 4. Calculate R2, MAE, and RMSE
# Hint: RMSE = np.sqrt(mean_squared_error(y_test, predictions))


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
lr_model = LinearRegression()
lr_model.fit(X_train_scaled, y_train)
lr_preds = lr_model.predict(X_test_scaled)

lr_r2 = r2_score(y_test, lr_preds)
lr_mae = mean_absolute_error(y_test, lr_preds)
lr_rmse = np.sqrt(mean_squared_error(y_test, lr_preds))

print("=== Linear Regression ===")
print(f"R2 Score: {lr_r2:.4f}")
print(f"MAE:      ${lr_mae:,.0f}")
print(f"RMSE:     ${lr_rmse:,.0f}")

# %% [markdown]
# ### 4.2 Train Random Forest

# %%
# TODO: Train a Random Forest model
# 1. Create a RandomForestRegressor(n_estimators=100, random_state=42)
# 2. Fit on X_train_scaled, y_train
# 3. Predict on X_test_scaled
# 4. Calculate R2, MAE, RMSE


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_scaled, y_train)
rf_preds = rf_model.predict(X_test_scaled)

rf_r2 = r2_score(y_test, rf_preds)
rf_mae = mean_absolute_error(y_test, rf_preds)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))

print("=== Random Forest ===")
print(f"R2 Score: {rf_r2:.4f}")
print(f"MAE:      ${rf_mae:,.0f}")
print(f"RMSE:     ${rf_rmse:,.0f}")

# %% [markdown]
# ### 4.3 Train Gradient Boosting

# %%
# TODO: Train a Gradient Boosting model
# 1. Create a GradientBoostingRegressor(n_estimators=100, random_state=42)
# 2. Fit on X_train_scaled, y_train
# 3. Predict on X_test_scaled
# 4. Calculate R2, MAE, RMSE


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
gb_model.fit(X_train_scaled, y_train)
gb_preds = gb_model.predict(X_test_scaled)

gb_r2 = r2_score(y_test, gb_preds)
gb_mae = mean_absolute_error(y_test, gb_preds)
gb_rmse = np.sqrt(mean_squared_error(y_test, gb_preds))

print("=== Gradient Boosting ===")
print(f"R2 Score: {gb_r2:.4f}")
print(f"MAE:      ${gb_mae:,.0f}")
print(f"RMSE:     ${gb_rmse:,.0f}")

# %% [markdown]
# ---
# ## Step 5: Model Evaluation & Comparison
#
# Numbers alone do not tell the full story. Visualizations help you
# understand *how* each model is performing — where it does well,
# where it struggles, and which features matter most.

# %% [markdown]
# ### 5.1 Comparison Table and Bar Chart
#
# Create a summary of all three models so you can compare them
# side by side. A bar chart makes the differences immediately visible.

# %%
# TODO: Create a comparison table and bar chart
# 1. Build a DataFrame with columns: Model, R2, MAE, RMSE
#    - One row per model (Linear Regression, Random Forest, Gradient Boosting)
# 2. Display the table
# 3. Create a bar chart comparing R2 scores across models


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
results = pd.DataFrame({
    'Model': ['Linear Regression', 'Random Forest', 'Gradient Boosting'],
    'R2': [lr_r2, rf_r2, gb_r2],
    'MAE': [lr_mae, rf_mae, gb_mae],
    'RMSE': [lr_rmse, rf_rmse, gb_rmse]
})

print("=== Model Comparison ===")
display(results.round(4))

# Bar chart
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

colors = ['#4C72B0', '#55A868', '#C44E52']

# R2 (higher is better)
axes[0].bar(results['Model'], results['R2'], color=colors)
axes[0].set_title('R-squared (higher = better)', fontsize=12)
axes[0].set_ylim(0, 1)
axes[0].tick_params(axis='x', rotation=15)

# MAE (lower is better)
axes[1].bar(results['Model'], results['MAE'], color=colors)
axes[1].set_title('MAE (lower = better)', fontsize=12)
axes[1].tick_params(axis='x', rotation=15)

# RMSE (lower is better)
axes[2].bar(results['Model'], results['RMSE'], color=colors)
axes[2].set_title('RMSE (lower = better)', fontsize=12)
axes[2].tick_params(axis='x', rotation=15)

plt.tight_layout()
plt.show()

# %% [markdown]
# ### 5.2 Actual vs Predicted Plot
#
# For the best model, plot actual prices against predicted prices.
# A perfect model would produce points along the diagonal line (y=x).
# Points far from the diagonal are large prediction errors.

# %%
# TODO: Plot actual vs predicted for the best model
# 1. Identify which model had the best R2 score
# 2. Create a scatter plot: x = actual prices, y = predicted prices
# 3. Add a diagonal reference line (y=x)
# 4. Add title, axis labels, and legend


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# Identify best model
best_idx = results['R2'].idxmax()
best_model_name = results.loc[best_idx, 'Model']
best_preds = [lr_preds, rf_preds, gb_preds][best_idx]
print(f"Best model: {best_model_name} (R2 = {results.loc[best_idx, 'R2']:.4f})")

fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(y_test, best_preds, alpha=0.4, s=20, color='steelblue', label='Predictions')

# Perfect prediction line
min_val = min(y_test.min(), best_preds.min())
max_val = max(y_test.max(), best_preds.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect prediction')

ax.set_xlabel('Actual Price ($)', fontsize=12)
ax.set_ylabel('Predicted Price ($)', fontsize=12)
ax.set_title(f'Actual vs Predicted — {best_model_name}', fontsize=14)
ax.legend(fontsize=11)
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 5.3 Residual Plot
#
# Residuals are the differences between actual and predicted values.
# A good model should have residuals randomly scattered around zero
# with no obvious patterns. Patterns in residuals suggest the model
# is missing something systematic.

# %%
# TODO: Plot residuals for the best model
# 1. Calculate residuals: actual - predicted
# 2. Create a scatter plot: x = predicted prices, y = residuals
# 3. Add a horizontal line at y=0
# 4. Add title and axis labels


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
residuals = y_test.values - best_preds

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Scatter plot of residuals
axes[0].scatter(best_preds, residuals, alpha=0.4, s=20, color='steelblue')
axes[0].axhline(y=0, color='red', linestyle='--', linewidth=2)
axes[0].set_xlabel('Predicted Price ($)', fontsize=12)
axes[0].set_ylabel('Residual ($)', fontsize=12)
axes[0].set_title(f'Residuals — {best_model_name}', fontsize=14)

# Histogram of residuals
axes[1].hist(residuals, bins=40, edgecolor='black', alpha=0.7, color='steelblue')
axes[1].axvline(x=0, color='red', linestyle='--', linewidth=2)
axes[1].set_xlabel('Residual ($)', fontsize=12)
axes[1].set_ylabel('Frequency', fontsize=12)
axes[1].set_title('Residual Distribution', fontsize=14)

plt.tight_layout()
plt.show()

print(f"Mean residual: ${residuals.mean():,.0f} (should be close to 0)")
print(f"Std of residuals: ${residuals.std():,.0f}")

# %% [markdown]
# ### 5.4 Feature Importance
#
# Tree-based models can tell you which features were most useful for
# making predictions. This is valuable for understanding the problem
# and for communicating results to stakeholders.

# %%
# Feature importance from the best tree-based model
# We'll use whichever tree model performed best
best_tree_model = gb_model if gb_r2 >= rf_r2 else rf_model
best_tree_name = 'Gradient Boosting' if gb_r2 >= rf_r2 else 'Random Forest'

importances = best_tree_model.feature_importances_
feat_imp = pd.Series(importances, index=feature_names).sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(8, 5))
feat_imp.plot(kind='barh', color='steelblue', edgecolor='black', ax=ax)
ax.set_xlabel('Feature Importance', fontsize=12)
ax.set_title(f'Feature Importance — {best_tree_name}', fontsize=14)
plt.tight_layout()
plt.show()

print("\nFeature importance ranking:")
for i, (feat, imp) in enumerate(feat_imp.sort_values(ascending=False).items(), 1):
    print(f"  {i}. {feat}: {imp:.4f}")

# %% [markdown]
# ---
# ## Step 6: Hyperparameter Tuning
#
# The default model settings are rarely optimal. **Hyperparameter tuning**
# systematically tries different configurations to find the best one.
#
# `GridSearchCV` tries every combination of parameters you specify and
# uses cross-validation to find the best set. This connects back to
# Module 3 (cross-validation) and Module 6 (ensemble methods).
#
# We will tune the best-performing model from Step 4.

# %%
# TODO: Use GridSearchCV to tune the best model
# If Gradient Boosting was best, tune these parameters:
#   param_grid = {
#       'n_estimators': [100, 200, 300],
#       'max_depth': [3, 5, 7],
#       'learning_rate': [0.05, 0.1, 0.2]
#   }
# If Random Forest was best, tune these:
#   param_grid = {
#       'n_estimators': [100, 200, 300],
#       'max_depth': [None, 10, 20],
#       'min_samples_split': [2, 5, 10]
#   }
#
# Steps:
# 1. Create a GridSearchCV with cv=5 and scoring='r2'
# 2. Fit on X_train_scaled, y_train
# 3. Print the best parameters and best CV score
# 4. Predict on X_test_scaled with the best estimator
# 5. Calculate and print R2, MAE, RMSE for the tuned model


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# Tune whichever tree model was best
if gb_r2 >= rf_r2:
    print("Tuning Gradient Boosting...")
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.05, 0.1, 0.2]
    }
    base_model = GradientBoostingRegressor(random_state=42)
else:
    print("Tuning Random Forest...")
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5, 10]
    }
    base_model = RandomForestRegressor(random_state=42)

grid_search = GridSearchCV(
    base_model, param_grid, cv=5, scoring='r2', n_jobs=-1, verbose=1
)
grid_search.fit(X_train_scaled, y_train)

print(f"\nBest parameters: {grid_search.best_params_}")
print(f"Best CV R2 score: {grid_search.best_score_:.4f}")

# Evaluate tuned model on test set
tuned_preds = grid_search.best_estimator_.predict(X_test_scaled)
tuned_r2 = r2_score(y_test, tuned_preds)
tuned_mae = mean_absolute_error(y_test, tuned_preds)
tuned_rmse = np.sqrt(mean_squared_error(y_test, tuned_preds))

print(f"\n=== Tuned Model on Test Set ===")
print(f"R2 Score: {tuned_r2:.4f}")
print(f"MAE:      ${tuned_mae:,.0f}")
print(f"RMSE:     ${tuned_rmse:,.0f}")

# %% [markdown]
# ### Tuned vs Default Comparison
#
# Let's see if tuning actually helped!

# %%
# Compare tuned vs default
default_r2 = gb_r2 if gb_r2 >= rf_r2 else rf_r2
default_mae = gb_mae if gb_r2 >= rf_r2 else rf_mae
default_rmse = gb_rmse if gb_r2 >= rf_r2 else rf_rmse
model_label = 'Gradient Boosting' if gb_r2 >= rf_r2 else 'Random Forest'

comparison = pd.DataFrame({
    'Version': [f'{model_label} (default)', f'{model_label} (tuned)'],
    'R2': [default_r2, tuned_r2],
    'MAE': [default_mae, tuned_mae],
    'RMSE': [default_rmse, tuned_rmse]
})

display(comparison.round(4))

improvement = tuned_r2 - default_r2
print(f"\nR2 improvement: {improvement:+.4f}")
if improvement > 0:
    print("Tuning improved the model!")
elif improvement == 0:
    print("Tuning found the same performance as default.")
else:
    print("Default was already near-optimal. Tuning made little difference.")

# %% [markdown]
# ---
# ## Step 7: Final Predictions & Conclusions
#
# You have built, evaluated, compared, and tuned your models. Now it is
# time to make final predictions and reflect on what you have learned.
#
# This is the most important step in any real project: communicating
# your results clearly and honestly.

# %%
# Final predictions with the best tuned model
final_model = grid_search.best_estimator_
final_preds = final_model.predict(X_test_scaled)

# Show some example predictions
results_df = pd.DataFrame({
    'Actual Price': y_test.values,
    'Predicted Price': final_preds,
    'Error': y_test.values - final_preds,
    'Error %': ((y_test.values - final_preds) / y_test.values * 100)
})

print("Sample predictions (first 10):")
display(results_df.head(10).round(2))

print(f"\nAverage absolute error: ${results_df['Error'].abs().mean():,.0f}")
print(f"Average percentage error: {results_df['Error %'].abs().mean():.1f}%")

# %% [markdown]
# ### Your Conclusions
#
# Write 3-5 bullet points summarizing what you found in this project.
# Think about:
# - Which model worked best and why?
# - Which features were most important?
# - Did hyperparameter tuning make a big difference?
# - What surprised you?
# - What would you do differently next time?

# %%
# TODO: Write your conclusions as a list of bullet points
# Replace each "..." with your own observations

conclusions = [
    "...",  # 1. Which model performed best and why?
    "...",  # 2. Which features mattered most?
    "...",  # 3. How much did tuning help?
    "...",  # 4. What surprised you?
    "...",  # 5. What would you do differently / next steps?
]

print("=== My Capstone Project Conclusions ===")
for i, point in enumerate(conclusions, 1):
    print(f"  {i}. {point}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION (example conclusions — yours may differ!)
conclusions = [
    "Gradient Boosting achieved the best performance with the highest R2 and "
    "lowest error metrics. Its sequential learning approach effectively captures "
    "the relationships in the data, correcting errors that simpler models miss.",

    "Square footage was by far the most important feature, followed by "
    "neighborhood score and house age. This aligns with real estate intuition: "
    "size, location quality, and condition drive home prices.",

    "Hyperparameter tuning provided a modest improvement over the defaults. "
    "The default settings in scikit-learn are already quite good, but tuning "
    "helps squeeze out the last bits of performance.",

    "Linear Regression performed surprisingly well as a baseline, likely because "
    "the synthetic data has mostly linear relationships between features and price.",

    "Next steps could include: trying more advanced models (XGBoost, LightGBM), "
    "engineering new features (e.g., price per square foot, bedrooms per bathroom), "
    "and using real-world data with more complex patterns and categorical features."
]

print("=== Capstone Project Conclusions ===")
for i, point in enumerate(conclusions, 1):
    print(f"  {i}. {point}")

# %% [markdown]
# ### Reflection
#
# Take a moment to think about the full journey:

# %%
print("""
========================================
  CAPSTONE PROJECT — COMPLETE!
========================================

You just completed a full end-to-end ML project:

  [1] Data Generation & Loading      (Module 1: NumPy, Pandas)
  [2] Exploratory Data Analysis       (Module 1: Pandas, Module 3: Visualization)
  [3] Data Preprocessing              (Module 2: Math, Module 3: Sklearn)
  [4] Model Building                  (Module 3-6: Regression, Trees, Ensembles)
  [5] Model Evaluation                (Module 3-6: Metrics, Visualization)
  [6] Hyperparameter Tuning           (Module 6: GridSearchCV)
  [7] Conclusions & Communication     (The most important skill of all)

What worked well:
  - Structured approach: EDA before modeling
  - Multiple model comparison: never rely on one model
  - Proper preprocessing: scaling, train/test split
  - Visualization: understanding results, not just numbers

What could be improved (in a real project):
  - Use real-world data with messier patterns
  - Add categorical features and proper encoding
  - Try more advanced models (XGBoost, neural networks)
  - Engineer domain-specific features
  - Deploy the model as an API or web app

You now have all the core skills to tackle real ML projects.
Keep building, keep learning, and keep experimenting!
""")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **EDA before modeling** | Histograms, correlation heatmaps, and scatter plots reveal patterns, outliers, and missing values before you commit to a model |
# | **Preprocessing without leakage** | Median imputation, an 80/20 split, and a scaler fit on training data only keep your evaluation honest |
# | **Model comparison** | Linear Regression baseline vs Random Forest vs Gradient Boosting — never rely on a single model |
# | **Evaluation** | R², MAE, and RMSE plus residual plots — numbers and pictures together tell the full story |
# | **Hyperparameter tuning** | GridSearchCV squeezes out extra performance once the big wins are banked |
# | **Communicating results** | Plain-language conclusions are part of the deliverable — a model nobody understands is a model nobody uses |
#
# ## Further reading
#
# - **scikit-learn — Choosing the right estimator** (the famous flowchart for picking
#   a model): https://scikit-learn.org/stable/machine_learning_map.html
# - **Google — Rules of Machine Learning** (hard-won engineering wisdom for real ML
#   systems): https://developers.google.com/machine-learning/guides/rules-of-ml
# - **Kaggle Learn** (free hands-on micro-courses to keep practicing):
#   https://www.kaggle.com/learn
#
# **Next:** [Module 11 — Segmentation & Face Parsing →](../11_segmentation_face_parsing/01_segmentation.ipynb)
# — the Advanced Image AI track begins: teach a network to label every pixel.
