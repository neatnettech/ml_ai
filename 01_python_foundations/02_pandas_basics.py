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
# # Module 1.2 — Pandas Basics
#
# Pandas is the go-to library for working with tabular data (think spreadsheets, CSV files, databases).
# Almost every ML project starts with loading and exploring data in Pandas.
#
# **What you'll learn:**
# - Series and DataFrames
# - Loading and exploring data
# - Selecting, filtering, and sorting
# - Handling missing values
# - Grouping and aggregation

# %%
import pandas as pd
import numpy as np
print(f"Pandas version: {pd.__version__}")

# %% [markdown]
# ## 1. Series and DataFrames
#
# - **Series**: a 1D labeled array (like a column)
# - **DataFrame**: a 2D labeled table (like a spreadsheet)

# %%
# Series
s = pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"])
print("Series:")
print(s)
print("\nValue at 'b':", s["b"])

# %%
# DataFrame from a dictionary
df = pd.DataFrame({
    "name":   ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "age":    [25, 30, 35, 28, 22],
    "salary": [50000, 60000, 75000, 55000, 45000],
    "dept":   ["Engineering", "Marketing", "Engineering", "Marketing", "Engineering"]
})
print(df)

# %% [markdown]
# ## 2. Exploring Data
#
# First thing you do with any dataset: look at it.

# %%
print("Shape:", df.shape)             # (rows, columns)
print("\nColumn types:")
print(df.dtypes)
print("\nFirst 3 rows:")
print(df.head(3))
print("\nBasic statistics:")
print(df.describe())

# %% [markdown]
# ## 3. Selecting and Filtering

# %%
# Select a single column (returns Series)
print(df["name"])

# Select multiple columns (returns DataFrame)
print(df[["name", "salary"]])

# %%
# Filter rows with boolean conditions
high_salary = df[df["salary"] > 50000]
print("Salary > 50k:")
print(high_salary)

# Multiple conditions (use & for AND, | for OR)
eng_high = df[(df["dept"] == "Engineering") & (df["salary"] > 50000)]
print("\nEngineering + salary > 50k:")
print(eng_high)

# %%
# .loc — select by label; .iloc — select by position
print("Row 0 (iloc):", df.iloc[0].values)
print("Rows 1-3, columns name+age (loc):")
print(df.loc[1:3, ["name", "age"]])

# %% [markdown]
# ### Exercise 2.1
# Using the `df` DataFrame above:
# 1. Select all people younger than 30
# 2. Get the names and departments of people in Marketing
# 3. Sort the DataFrame by salary (descending)
# 4. Add a new column `bonus` that is 10% of salary

# %%
# TODO
young = ...          # 1
marketing = ...      # 2
sorted_df = ...      # 3
# 4: add bonus column

print("Young (<30):\n", young)
print("\nMarketing names+dept:\n", marketing)
print("\nSorted by salary:\n", sorted_df)

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
young = df[df["age"] < 30]
marketing = df[df["dept"] == "Marketing"][["name", "dept"]]
sorted_df = df.sort_values("salary", ascending=False)
df["bonus"] = df["salary"] * 0.10

print("Young (<30):\n", young)
print("\nMarketing names+dept:\n", marketing)
print("\nSorted by salary:\n", sorted_df)
print("\nWith bonus:\n", df)

# %% [markdown]
# ## 4. Handling Missing Data
#
# Real-world data almost always has missing values. Pandas represents them as `NaN`.

# %%
dirty = pd.DataFrame({
    "A": [1, 2, np.nan, 4],
    "B": [np.nan, 5, 6, np.nan],
    "C": [7, 8, 9, 10]
})
print("Data with NaN:")
print(dirty)
print("\nMissing values per column:")
print(dirty.isnull().sum())

# %%
# Strategy 1: Drop rows with any NaN
print("Drop NaN rows:")
print(dirty.dropna())

# Strategy 2: Fill with a value (e.g. column mean)
print("\nFill with column mean:")
print(dirty.fillna(dirty.mean()))

# %% [markdown]
# ## 5. Grouping and Aggregation
#
# `groupby` is Pandas' most powerful feature — split data into groups,
# apply a function to each group, combine results.

# %%
# Average salary by department
print(df.groupby("dept")["salary"].mean())

# Multiple aggregations
print("\nMultiple stats:")
print(df.groupby("dept").agg({
    "salary": ["mean", "max"],
    "age": "mean"
}))

# %% [markdown]
# ### Exercise 2.2
# Let's work with a slightly bigger dataset.

# %%
np.random.seed(42)
n = 100
sales = pd.DataFrame({
    "region": np.random.choice(["North", "South", "East", "West"], n),
    "product": np.random.choice(["Widget", "Gadget", "Doohickey"], n),
    "revenue": np.random.randint(100, 1000, n),
    "quantity": np.random.randint(1, 50, n)
})
sales.head()

# %%
# TODO:
# 1. What is the total revenue per region?
revenue_by_region = ...

# 2. What is the average quantity sold per product?
avg_qty_by_product = ...

# 3. Which region+product combo has the highest total revenue?
# Hint: groupby two columns, then use idxmax()
best_combo = ...

print("Revenue by region:\n", revenue_by_region)
print("\nAvg quantity by product:\n", avg_qty_by_product)
print("\nBest combo:", best_combo)

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
revenue_by_region = sales.groupby("region")["revenue"].sum()
avg_qty_by_product = sales.groupby("product")["quantity"].mean()
combo = sales.groupby(["region", "product"])["revenue"].sum()
best_combo = combo.idxmax()

print("Revenue by region:\n", revenue_by_region)
print("\nAvg quantity by product:\n", avg_qty_by_product)
print("\nBest combo:", best_combo, "with revenue", combo.max())

# %% [markdown]
# ## Key Takeaways
#
# - **DataFrame** = your main data structure for tabular data
# - **Explore first**: `.head()`, `.shape`, `.describe()`, `.dtypes`
# - **Filter** with boolean indexing: `df[df["col"] > value]`
# - **Handle NaNs** before feeding data to ML models
# - **groupby** is essential for understanding your data
#
# ---
# **Next:** [Matplotlib Visualization →](03_matplotlib_visualization.ipynb)
