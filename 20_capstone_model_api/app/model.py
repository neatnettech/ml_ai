"""Load the persisted model once and predict from it.

Loading happens at import (startup), not per request — deserializing on every call
would be slow. The loaded pipeline is reused for the life of the process.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

MODEL_PATH = Path(__file__).with_name("model.joblib")

_bundle: dict | None = None


def load_model() -> dict:
    """Load the {pipeline, features} bundle, caching it after the first call."""
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"{MODEL_PATH.name} not found. Train it first: python -m app.train_model"
            )
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def predict_price(features: dict[str, float]) -> float:
    """Map a feature dict to a single price prediction, in the trained order."""
    bundle = load_model()
    row = np.array([[features[name] for name in bundle["features"]]])
    return float(bundle["pipeline"].predict(row)[0])
