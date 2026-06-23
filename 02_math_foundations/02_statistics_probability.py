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
# # Module 2.2 — Statistics & Probability for ML
#
# **Purpose:** Train/test splits, loss curves, evaluation metrics, regularization —
# all of it is applied statistics. Build the intuition for distributions, correlation,
# and Bayes' theorem here, before the **Pure ML track** starts leaning on those ideas
# in every evaluation step.
#
# Statistics and probability are the other half of ML's mathematical foundation.
# Every time you evaluate a model, analyze data, or make predictions with
# uncertainty, you're using these concepts.
#
# **What you'll learn:**
# - Descriptive statistics: mean, median, mode, variance, standard deviation
# - Distributions: normal and uniform, with visualizations
# - Correlation: Pearson coefficient and scatter plots
# - Probability basics: conditional probability and Bayes' theorem

# %%
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

np.random.seed(42)
np.set_printoptions(precision=3, suppress=True)
print("Ready to go!")

# %% [markdown]
# ## 1. Descriptive Statistics
#
# Before building any model, you need to **understand your data**. Descriptive
# statistics summarize what's going on in a dataset with just a few numbers.
#
# These are the first things you should calculate when you get a new dataset.

# %% [markdown]
# ### 1.1 Mean (Average)
#
# The **mean** is the sum of all values divided by the count.
# It tells you the "center" of your data, but is sensitive to outliers.

# %%
# Exam scores for a class
scores = np.array([72, 85, 90, 68, 95, 78, 82, 88, 76, 91])

# Manual calculation
mean_manual = np.sum(scores) / len(scores)
print(f"Manual mean: {mean_manual}")

# NumPy
mean_np = np.mean(scores)
print(f"NumPy mean:  {mean_np}")

# Why outliers matter:
scores_with_outlier = np.append(scores, 20)  # one student scored 20
print(f"\nMean without outlier: {np.mean(scores):.1f}")
print(f"Mean with outlier:    {np.mean(scores_with_outlier):.1f}")
print("One outlier pulled the mean down significantly!")

# %% [markdown]
# ### 1.2 Median
#
# The **median** is the middle value when data is sorted. It's robust to outliers,
# which makes it better than the mean for skewed data (like house prices or salaries).

# %%
scores = np.array([72, 85, 90, 68, 95, 78, 82, 88, 76, 91])

# Sort and find the middle
sorted_scores = np.sort(scores)
print(f"Sorted: {sorted_scores}")
print(f"Median: {np.median(scores)}")

# Compare with the outlier case
scores_with_outlier = np.append(scores, 20)
print(f"\nMedian without outlier: {np.median(scores):.1f}")
print(f"Median with outlier:    {np.median(scores_with_outlier):.1f}")
print("The median barely changed — it's robust to outliers!")

# %% [markdown]
# ### 1.3 Mode
#
# The **mode** is the most frequently occurring value. Most useful for categorical
# data, but can be used with numerical data too.

# %%
# Ratings from 1-5
ratings = np.array([5, 3, 4, 5, 5, 2, 4, 5, 3, 4, 5, 4, 3, 5, 4])

mode_result = stats.mode(ratings, keepdims=True)
print(f"Ratings: {ratings}")
print(f"Mode: {mode_result.mode[0]} (appears {mode_result.count[0]} times)")
print(f"Mean: {np.mean(ratings):.2f}")
print(f"Median: {np.median(ratings):.1f}")

# %% [markdown]
# ### 1.4 Variance and Standard Deviation
#
# These measure how **spread out** your data is.
#
# - **Variance** = average of squared differences from the mean
# - **Standard Deviation** = square root of variance (same units as the data)
#
# In ML, you'll use these for:
# - Feature scaling / standardization (`z = (x - mean) / std`)
# - Understanding model prediction uncertainty
# - Detecting outliers (values beyond 2-3 standard deviations)

# %%
scores = np.array([72, 85, 90, 68, 95, 78, 82, 88, 76, 91])

# Manual variance calculation
mean = np.mean(scores)
differences = scores - mean
squared_diffs = differences ** 2
variance_manual = np.mean(squared_diffs)

print(f"Mean: {mean}")
print(f"Differences from mean: {differences}")
print(f"Squared differences:   {squared_diffs}")
print(f"Variance (manual):     {variance_manual:.2f}")
print(f"Variance (numpy):      {np.var(scores):.2f}")
print(f"Std deviation:         {np.std(scores):.2f}")

# Visualize spread
tight = np.random.normal(50, 5, 1000)   # small std
wide = np.random.normal(50, 20, 1000)   # large std

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(tight, bins=30, color='steelblue', alpha=0.7)
axes[0].set_title(f'Small std = {np.std(tight):.1f}')
axes[0].set_xlim(-20, 120)
axes[1].hist(wide, bins=30, color='coral', alpha=0.7)
axes[1].set_title(f'Large std = {np.std(wide):.1f}')
axes[1].set_xlim(-20, 120)
plt.suptitle('Same Mean, Different Spread')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Exercise 2.1 — Calculate Statistics for a Dataset
#
# You have monthly sales data (in thousands of dollars) for a small business.
# Calculate the following:
# 1. Mean, median, and mode
# 2. Variance and standard deviation
# 3. Identify any months that are more than 2 standard deviations from the mean
#    (these are potential outliers)

# %%
sales = np.array([45, 52, 48, 61, 55, 49, 120, 53, 47, 58, 50, 54])
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# TODO: Calculate mean, median, mode
mean_sales = ...
median_sales = ...
mode_sales = ...  # hint: stats.mode(sales, keepdims=True).mode[0]

# TODO: Calculate variance and standard deviation
var_sales = ...
std_sales = ...

# TODO: Find outliers (values more than 2 std from the mean)
# hint: np.abs(sales - mean_sales) > 2 * std_sales
outlier_mask = ...

print(f"Mean:   ${mean_sales:.1f}k")
print(f"Median: ${median_sales:.1f}k")
print(f"Mode:   ${mode_sales}k")
print(f"Variance: {var_sales:.1f}")
print(f"Std Dev:  {std_sales:.1f}")
print(f"\nOutlier months: {[months[i] for i in range(len(months)) if outlier_mask[i]]}")
print(f"Outlier values:  {sales[outlier_mask]}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
sales = np.array([45, 52, 48, 61, 55, 49, 120, 53, 47, 58, 50, 54])
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

mean_sales = np.mean(sales)
median_sales = np.median(sales)
mode_sales = stats.mode(sales, keepdims=True).mode[0]

var_sales = np.var(sales)
std_sales = np.std(sales)

outlier_mask = np.abs(sales - mean_sales) > 2 * std_sales

print(f"Mean:   ${mean_sales:.1f}k")
print(f"Median: ${median_sales:.1f}k")
print(f"Mode:   ${mode_sales}k")
print(f"Variance: {var_sales:.1f}")
print(f"Std Dev:  {std_sales:.1f}")
print(f"\nOutlier months: {[months[i] for i in range(len(months)) if outlier_mask[i]]}")
print(f"Outlier values:  {sales[outlier_mask]}")
# July (120k) is the outlier — more than 2 std from the mean

# %% [markdown]
# ## 2. Distributions
#
# A **distribution** describes how values are spread across a range.
# Understanding distributions helps you:
# - Choose the right model
# - Detect data quality issues
# - Generate synthetic data for testing

# %% [markdown]
# ### 2.1 Normal (Gaussian) Distribution
#
# The **normal distribution** is the famous "bell curve." It shows up everywhere:
# - Heights, weights, test scores
# - Measurement errors
# - Many ML algorithms assume features are roughly normal
#
# Defined by two parameters: **mean** (center) and **std** (spread).
#
# The **68-95-99.7 rule**: ~68% of data falls within 1 std, ~95% within 2 std,
# ~99.7% within 3 std of the mean.

# %%
# Generate samples from normal distributions
normal_a = np.random.normal(loc=0, scale=1, size=10000)   # standard normal
normal_b = np.random.normal(loc=5, scale=2, size=10000)   # shifted and wider
normal_c = np.random.normal(loc=-2, scale=0.5, size=10000)  # shifted left, narrow

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot histograms
axes[0].hist(normal_a, bins=50, alpha=0.6, label='mean=0, std=1', density=True)
axes[0].hist(normal_b, bins=50, alpha=0.6, label='mean=5, std=2', density=True)
axes[0].hist(normal_c, bins=50, alpha=0.6, label='mean=-2, std=0.5', density=True)
axes[0].set_title('Normal Distributions')
axes[0].legend()
axes[0].set_xlabel('Value')
axes[0].set_ylabel('Density')

# Demonstrate the 68-95-99.7 rule
data = np.random.normal(100, 15, 100000)
within_1std = np.mean(np.abs(data - 100) <= 15) * 100
within_2std = np.mean(np.abs(data - 100) <= 30) * 100
within_3std = np.mean(np.abs(data - 100) <= 45) * 100

axes[1].hist(data, bins=80, density=True, alpha=0.7, color='steelblue')
axes[1].axvline(100, color='red', linestyle='--', label='mean')
axes[1].axvline(85, color='orange', linestyle=':', alpha=0.8)
axes[1].axvline(115, color='orange', linestyle=':', alpha=0.8, label=f'1 std ({within_1std:.1f}%)')
axes[1].axvline(70, color='green', linestyle=':', alpha=0.8)
axes[1].axvline(130, color='green', linestyle=':', alpha=0.8, label=f'2 std ({within_2std:.1f}%)')
axes[1].set_title('68-95-99.7 Rule (mean=100, std=15)')
axes[1].legend()

plt.tight_layout()
plt.show()

# %% [markdown]
# ### 2.2 Uniform Distribution
#
# In a **uniform distribution**, every value in the range is equally likely.
# Think of rolling a fair die — each outcome has the same probability.
#
# Used in ML for:
# - Random weight initialization (sometimes)
# - Random search in hyperparameter tuning
# - Generating random baseline data

# %%
# Uniform distribution: all values equally likely
uniform_data = np.random.uniform(low=0, high=10, size=10000)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Compare uniform vs normal
axes[0].hist(uniform_data, bins=50, alpha=0.7, color='coral', density=True)
axes[0].set_title('Uniform Distribution (0 to 10)')
axes[0].set_xlabel('Value')
axes[0].set_ylabel('Density')

normal_data = np.random.normal(loc=5, scale=1.5, size=10000)
axes[1].hist(normal_data, bins=50, alpha=0.7, color='steelblue', density=True)
axes[1].set_title('Normal Distribution (mean=5, std=1.5)')
axes[1].set_xlabel('Value')

# Both have similar range and mean, but very different shapes
print(f"Uniform — mean: {uniform_data.mean():.2f}, std: {uniform_data.std():.2f}")
print(f"Normal  — mean: {normal_data.mean():.2f}, std: {normal_data.std():.2f}")

plt.tight_layout()
plt.show()

# %% [markdown]
# ### Exercise 2.2 — Generate and Plot Distributions
#
# 1. Generate 5000 samples from a normal distribution with mean=70 and std=10
#    (think of it as exam scores)
# 2. Generate 5000 samples from a uniform distribution between 40 and 100
# 3. Plot both as histograms side by side
# 4. Print the mean, median, and std for each — how do they compare?

# %%
np.random.seed(42)

# TODO: Generate the samples
exam_normal = ...   # normal: mean=70, std=10, size=5000
exam_uniform = ...  # uniform: low=40, high=100, size=5000

# TODO: Create side-by-side histograms
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
# Plot exam_normal on axes[0]
# Plot exam_uniform on axes[1]
# ...

plt.tight_layout()
plt.show()

# TODO: Print statistics for both
print("Normal distribution:")
print(f"  Mean: ..., Median: ..., Std: ...")
print("\nUniform distribution:")
print(f"  Mean: ..., Median: ..., Std: ...")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
np.random.seed(42)

exam_normal = np.random.normal(loc=70, scale=10, size=5000)
exam_uniform = np.random.uniform(low=40, high=100, size=5000)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(exam_normal, bins=50, alpha=0.7, color='steelblue', density=True)
axes[0].set_title('Normal (mean=70, std=10)')
axes[0].set_xlabel('Score')
axes[0].set_ylabel('Density')
axes[0].axvline(np.mean(exam_normal), color='red', linestyle='--', label='mean')
axes[0].legend()

axes[1].hist(exam_uniform, bins=50, alpha=0.7, color='coral', density=True)
axes[1].set_title('Uniform (40 to 100)')
axes[1].set_xlabel('Score')
axes[1].axvline(np.mean(exam_uniform), color='red', linestyle='--', label='mean')
axes[1].legend()

plt.tight_layout()
plt.show()

print("Normal distribution:")
print(f"  Mean: {np.mean(exam_normal):.1f}, Median: {np.median(exam_normal):.1f}, Std: {np.std(exam_normal):.1f}")
print("\nUniform distribution:")
print(f"  Mean: {np.mean(exam_uniform):.1f}, Median: {np.median(exam_uniform):.1f}, Std: {np.std(exam_uniform):.1f}")
# Notice: similar means (~70), but uniform has higher std (more spread out)

# %% [markdown]
# ## 3. Correlation
#
# **Correlation** measures how two variables move together.
#
# **Pearson correlation coefficient (r)** ranges from -1 to +1:
# - **r = +1**: Perfect positive correlation (both increase together)
# - **r = 0**: No linear correlation
# - **r = -1**: Perfect negative correlation (one increases, the other decreases)
#
# In ML, correlation helps you:
# - Understand relationships between features
# - Identify redundant features (highly correlated = duplicate information)
# - Spot potential predictors for your target variable

# %%
np.random.seed(42)
n = 200

# Generate data with different correlations
x = np.random.normal(0, 1, n)

# Strong positive correlation (r ~ 0.95)
y_pos = 2 * x + np.random.normal(0, 0.5, n)

# No correlation (r ~ 0)
y_none = np.random.normal(0, 1, n)

# Strong negative correlation (r ~ -0.9)
y_neg = -1.5 * x + np.random.normal(0, 0.7, n)

# Non-linear relationship (low Pearson r, but clearly related)
y_nonlin = x**2 + np.random.normal(0, 0.3, n)

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
datasets = [
    (x, y_pos, 'Strong Positive'),
    (x, y_none, 'No Correlation'),
    (x, y_neg, 'Strong Negative'),
    (x, y_nonlin, 'Non-linear')
]

for ax, (xi, yi, title) in zip(axes, datasets):
    r = np.corrcoef(xi, yi)[0, 1]
    ax.scatter(xi, yi, alpha=0.4, s=10)
    ax.set_title(f'{title}\nr = {r:.2f}')
    ax.set_xlabel('x')

axes[0].set_ylabel('y')
plt.suptitle('Pearson Correlation Examples', fontsize=14)
plt.tight_layout()
plt.show()

print("Note: The non-linear case has a low r, but x and y are clearly related.")
print("Pearson correlation only measures LINEAR relationships!")

# %%
# Computing a correlation matrix
# This is what you'll do with a real dataset to see which features are related

np.random.seed(42)
n = 500

# Simulate features for a house price dataset
size = np.random.normal(150, 40, n)          # square meters
bedrooms = size / 40 + np.random.normal(0, 0.5, n)  # correlated with size
age = np.random.uniform(0, 50, n)             # years old
price = 2 * size - 0.5 * age + 10 * bedrooms + np.random.normal(0, 20, n)

# Stack into a matrix
data = np.column_stack([size, bedrooms, age, price])
labels = ['Size', 'Bedrooms', 'Age', 'Price']

# Correlation matrix
corr_matrix = np.corrcoef(data.T)
print("Correlation Matrix:")
for i, label in enumerate(labels):
    row = "  ".join(f"{corr_matrix[i,j]:+.2f}" for j in range(len(labels)))
    print(f"  {label:>8}: {row}")

# Visualize as a heatmap
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
ax.set_xticks(range(len(labels)))
ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45)
ax.set_yticklabels(labels)

# Add correlation values as text
for i in range(len(labels)):
    for j in range(len(labels)):
        ax.text(j, i, f'{corr_matrix[i,j]:.2f}', ha='center', va='center',
                color='white' if abs(corr_matrix[i,j]) > 0.5 else 'black')

plt.colorbar(im, label='Correlation')
plt.title('Feature Correlation Heatmap')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Exercise 2.3 — Correlation Matrix and Heatmap
#
# You have data for 100 students: hours studied, hours slept, and exam score.
#
# 1. Compute the correlation matrix using `np.corrcoef`
# 2. Visualize it as a heatmap
# 3. Which feature is most correlated with the exam score? Does that make sense?

# %%
np.random.seed(42)
n = 100

hours_studied = np.random.uniform(1, 10, n)
hours_slept = np.random.normal(7, 1.5, n)
exam_score = 5 * hours_studied + 3 * hours_slept + np.random.normal(0, 5, n)

data = np.column_stack([hours_studied, hours_slept, exam_score])
labels = ['Hours Studied', 'Hours Slept', 'Exam Score']

# TODO: Compute correlation matrix
corr = ...  # hint: np.corrcoef(data.T)

# TODO: Print the correlation matrix
print("Correlation Matrix:")
# ...

# TODO: Create heatmap visualization
fig, ax = plt.subplots(figsize=(7, 6))
# hint: use ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
# ...

plt.show()

# TODO: Which feature is most correlated with exam score?
# print("Most correlated with exam score: ...")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
np.random.seed(42)
n = 100

hours_studied = np.random.uniform(1, 10, n)
hours_slept = np.random.normal(7, 1.5, n)
exam_score = 5 * hours_studied + 3 * hours_slept + np.random.normal(0, 5, n)

data = np.column_stack([hours_studied, hours_slept, exam_score])
labels = ['Hours Studied', 'Hours Slept', 'Exam Score']

corr = np.corrcoef(data.T)

print("Correlation Matrix:")
for i, label in enumerate(labels):
    row = "  ".join(f"{corr[i,j]:+.2f}" for j in range(len(labels)))
    print(f"  {label:>14}: {row}")

fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
ax.set_xticks(range(len(labels)))
ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45)
ax.set_yticklabels(labels)

for i in range(len(labels)):
    for j in range(len(labels)):
        ax.text(j, i, f'{corr[i,j]:.2f}', ha='center', va='center',
                color='white' if abs(corr[i,j]) > 0.5 else 'black')

plt.colorbar(im, label='Correlation')
plt.title('Student Performance Correlation Heatmap')
plt.tight_layout()
plt.show()

# Hours studied is most correlated with exam score.
# This makes sense — we set the coefficient for hours_studied (5) higher
# than hours_slept (3), so studying has a stronger effect on the score.
print(f"\nMost correlated with exam score: Hours Studied (r = {corr[0, 2]:.2f})")

# %% [markdown]
# ## 4. Probability Basics
#
# Probability is the math of uncertainty. In ML, it powers:
# - Classification (what's the probability this email is spam?)
# - Bayesian methods
# - Generative models
# - Understanding model confidence

# %% [markdown]
# ### 4.1 Basic Probability
#
# **Probability** of an event = (favorable outcomes) / (total outcomes)
#
# Rules:
# - `0 <= P(A) <= 1` for any event A
# - `P(not A) = 1 - P(A)`
# - `P(A or B) = P(A) + P(B) - P(A and B)`

# %%
# Simulating probability with code
# Roll a die 100,000 times
np.random.seed(42)
rolls = np.random.randint(1, 7, size=100_000)

# Probability of rolling a 6
p_six = np.mean(rolls == 6)
print(f"P(rolling 6) = {p_six:.4f} (theoretical: {1/6:.4f})")

# Probability of rolling even
p_even = np.mean(rolls % 2 == 0)
print(f"P(rolling even) = {p_even:.4f} (theoretical: 0.5000)")

# Probability of rolling > 4
p_gt4 = np.mean(rolls > 4)
print(f"P(rolling > 4) = {p_gt4:.4f} (theoretical: {2/6:.4f})")

# %% [markdown]
# ### 4.2 Conditional Probability
#
# **P(A | B)** = "probability of A, given that B happened"
#
# Formula: `P(A | B) = P(A and B) / P(B)`
#
# Example: What's the probability a student passed the exam, given that they
# studied more than 5 hours?

# %%
np.random.seed(42)
n = 10000

# Simulate student data
hours_studied = np.random.uniform(0, 10, n)
# Probability of passing depends on hours studied
pass_prob = 1 / (1 + np.exp(-(hours_studied - 4)))  # sigmoid function
passed = np.random.random(n) < pass_prob

# Unconditional probability of passing
p_pass = np.mean(passed)
print(f"P(pass) = {p_pass:.3f}")

# Conditional: P(pass | studied > 5 hours)
studied_lots = hours_studied > 5
p_pass_given_studied = np.mean(passed[studied_lots])
print(f"P(pass | studied > 5h) = {p_pass_given_studied:.3f}")

# Conditional: P(pass | studied <= 2 hours)
studied_little = hours_studied <= 2
p_pass_given_little = np.mean(passed[studied_little])
print(f"P(pass | studied <= 2h) = {p_pass_given_little:.3f}")

print(f"\nStudying more than 5h increases pass rate from {p_pass:.1%} to {p_pass_given_studied:.1%}")

# %% [markdown]
# ### 4.3 Bayes' Theorem
#
# **Bayes' theorem** lets you flip conditional probabilities:
#
# ```
# P(A | B) = P(B | A) * P(A) / P(B)
# ```
#
# This is incredibly useful because often we know `P(B|A)` but want `P(A|B)`.
#
# **Classic example: Medical testing**
#
# A disease affects 1% of the population. A test for the disease:
# - Correctly detects the disease 95% of the time (sensitivity)
# - Correctly gives negative for healthy people 90% of the time (specificity)
#
# If you test positive, what's the actual probability you have the disease?

# %%
# Bayes' theorem: Medical test example
# P(disease)       = 0.01  (1% prevalence)
# P(positive|disease)  = 0.95 (sensitivity / true positive rate)
# P(positive|healthy)  = 0.10 (false positive rate = 1 - specificity)

p_disease = 0.01
p_healthy = 1 - p_disease
p_pos_given_disease = 0.95   # sensitivity
p_pos_given_healthy = 0.10   # false positive rate

# P(positive) = P(pos|disease)*P(disease) + P(pos|healthy)*P(healthy)
p_positive = p_pos_given_disease * p_disease + p_pos_given_healthy * p_healthy

# Bayes: P(disease|positive) = P(positive|disease) * P(disease) / P(positive)
p_disease_given_positive = (p_pos_given_disease * p_disease) / p_positive

print("Medical Test — Bayes' Theorem")
print("=" * 40)
print(f"Disease prevalence:      {p_disease:.1%}")
print(f"Test sensitivity:        {p_pos_given_disease:.1%}")
print(f"False positive rate:     {p_pos_given_healthy:.1%}")
print(f"P(test positive):        {p_positive:.3%}")
print(f"")
print(f"P(disease | positive):   {p_disease_given_positive:.1%}")
print(f"")
print(f"Surprise! Even with a positive test, there's only a")
print(f"{p_disease_given_positive:.1%} chance you actually have the disease.")
print(f"")
print(f"Why? Because the disease is rare (1%), so most positive")
print(f"tests come from the 99% of healthy people (false positives).")

# %%
# Let's verify with simulation
np.random.seed(42)
population = 1_000_000

# Simulate who has the disease
has_disease = np.random.random(population) < p_disease

# Simulate test results
test_positive = np.where(
    has_disease,
    np.random.random(population) < p_pos_given_disease,  # sick: 95% positive
    np.random.random(population) < p_pos_given_healthy   # healthy: 10% positive
)

# Among those who tested positive, how many actually have the disease?
true_positives = np.sum(has_disease & test_positive)
total_positives = np.sum(test_positive)

print(f"Simulation with {population:,} people:")
print(f"  People with disease:    {np.sum(has_disease):,}")
print(f"  Total positive tests:   {total_positives:,}")
print(f"  True positives:         {true_positives:,}")
print(f"  False positives:        {total_positives - true_positives:,}")
print(f"")
print(f"  P(disease | positive) = {true_positives/total_positives:.1%}")
print(f"  Bayes' formula gave:    {p_disease_given_positive:.1%}")

# %% [markdown]
# ### Why Bayes' Theorem Matters for ML
#
# - **Naive Bayes classifiers** directly use Bayes' theorem for text classification
# - **Bayesian inference** updates beliefs as you see more data
# - **Understanding false positives/negatives** — critical for evaluating classifiers
#   on imbalanced datasets (just like the rare disease example!)

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Mean vs median** | Mean gives the center but is outlier-sensitive — use median for skewed data |
# | **Standard deviation** | Measures spread — essential for feature scaling |
# | **Normal distribution** | The most common — many ML assumptions rely on it |
# | **Correlation** | Measures linear relationships — check it before modeling |
# | **Bayes' theorem** | Reason about probabilities with evidence |
# | **Visualize first** | Numbers alone can mislead — plot before computing statistics |
#
# ## Further reading
#
# - **Deep Learning book, ch. 3** (probability and information theory for ML):
#   https://www.deeplearningbook.org/contents/prob.html
# - **Seeing Theory** (interactive visual introduction to probability and statistics):
#   https://seeing-theory.brown.edu/
# - **scipy.stats** (the reference for every distribution and test used here):
#   https://docs.scipy.org/doc/scipy/reference/stats.html
#
# **Next:** [First ML Models →](../03_first_ml_models/01_linear_regression.ipynb) — put
# the math to work: train, evaluate, and understand your first real models.
