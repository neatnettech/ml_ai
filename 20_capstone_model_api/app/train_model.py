"""Train and persist the house-price model from Module 10.

Run once before serving:  python -m app.train_model   (from 20_capstone_model_api/)
Produces model.joblib, which app/model.py loads at startup.

This is the bridge from "ML in a notebook" to "a model you can ship": training and
serving are SEPARATE steps. You train occasionally and save the artifact; the API
just loads that artifact and predicts.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Feature order is the contract between training and serving — keep it in one place.
FEATURES = [
    "square_feet",
    "bedrooms",
    "bathrooms",
    "age",
    "garage_size",
    "neighborhood_score",
    "distance_to_city",
]
MODEL_PATH = Path(__file__).with_name("model.joblib")


def make_dataset(n_samples: int = 1000, seed: int = 42):
    """Same synthetic housing data as Module 10's capstone."""
    rng = np.random.default_rng(seed)
    square_feet = rng.uniform(800, 4000, n_samples)
    bedrooms = rng.integers(1, 7, n_samples)
    bathrooms = rng.integers(1, 5, n_samples)
    age = rng.uniform(0, 80, n_samples)
    garage_size = rng.integers(0, 4, n_samples)
    neighborhood_score = rng.uniform(1, 10, n_samples)
    distance_to_city = rng.uniform(1, 30, n_samples)

    price = (
        150 * square_feet
        + 15000 * bedrooms
        + 20000 * bathrooms
        - 2000 * age
        + 25000 * garage_size
        + 30000 * neighborhood_score
        - 5000 * distance_to_city
        + rng.normal(0, 30000, n_samples)
    )
    price = np.maximum(price, 50000)

    X = np.column_stack(
        [square_feet, bedrooms, bathrooms, age, garage_size, neighborhood_score, distance_to_city]
    )
    return X, price


def train_and_save(path: Path = MODEL_PATH) -> Pipeline:
    X, y = make_dataset()
    # Bundle scaler + model in one Pipeline so serving needs no separate scaler file.
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(n_estimators=200, random_state=42)),
        ]
    )
    pipeline.fit(X, y)
    joblib.dump({"pipeline": pipeline, "features": FEATURES}, path)
    print(f"Saved model -> {path}  (R^2 on train: {pipeline.score(X, y):.4f})")
    return pipeline


if __name__ == "__main__":
    train_and_save()
