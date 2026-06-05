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
# # Module 20 — Capstone: Serve an ML Model
#
# This is where the whole catalog comes together. You will take the **house-price
# model** from Module 10 and turn it into a **production-shaped web service** using
# everything from the backend track:
#
# - **Module 17** — FastAPI endpoints + Pydantic validation
# - **Module 18** — the crypto under the hood
# - **Module 19** — JWT auth to protect the endpoint
#
# The end-to-end pipeline:
#
# ```
# train  ->  persist (joblib)  ->  load at startup  ->  validate input
#        ->  predict  ->  return JSON  ->  behind auth
# ```
#
# The runnable service is in `app/`. This notebook walks the key ideas and
# exercises the API with `TestClient`.

# %%
import numpy as np
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

print("Ready — sklearn for the model, FastAPI to serve it.")

# %% [markdown]
# ## Step 1: Train ≠ Serve — persist the artifact
#
# The single most important idea in ML deployment: **training and serving are
# separate**. You train occasionally (slow, needs data), save the result, and the
# API just **loads that artifact and predicts** (fast, stateless).
#
# We wrap the scaler + model in one **`Pipeline`** so a single saved object handles
# preprocessing *and* prediction — no risk of train/serve scaling mismatch.

# %%
FEATURES = [
    "square_feet", "bedrooms", "bathrooms", "age",
    "garage_size", "neighborhood_score", "distance_to_city",
]


def make_dataset(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    cols = [
        rng.uniform(800, 4000, n),      # square_feet
        rng.integers(1, 7, n),          # bedrooms
        rng.integers(1, 5, n),          # bathrooms
        rng.uniform(0, 80, n),          # age
        rng.integers(0, 4, n),          # garage_size
        rng.uniform(1, 10, n),          # neighborhood_score
        rng.uniform(1, 30, n),          # distance_to_city
    ]
    X = np.column_stack(cols)
    price = (150*cols[0] + 15000*cols[1] + 20000*cols[2] - 2000*cols[3]
             + 25000*cols[4] + 30000*cols[5] - 5000*cols[6]
             + rng.normal(0, 30000, n))
    return X, np.maximum(price, 50000)


X, y = make_dataset()
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", GradientBoostingRegressor(n_estimators=200, random_state=42)),
])
pipeline.fit(X, y)
print(f"Trained. R^2 on training data: {pipeline.score(X, y):.4f}")

# %% [markdown]
# ### Persisting with joblib
#
# `joblib` serializes the fitted pipeline to disk. We bundle it with the feature
# order so the server always feeds inputs in the order the model was trained on.
# (In `app/`, `train_model.py` does this and writes `model.joblib`.)

# %%
import joblib
import tempfile
from pathlib import Path

# Save to a temp file just for this notebook demo.
tmp = Path(tempfile.gettempdir()) / "house_model_demo.joblib"
joblib.dump({"pipeline": pipeline, "features": FEATURES}, tmp)
print("Saved:", tmp)

# Loading is what the API does at startup:
bundle = joblib.load(tmp)
print("Loaded bundle keys:", list(bundle.keys()))


def predict_price(features: dict) -> float:
    row = np.array([[features[name] for name in bundle["features"]]])
    return float(bundle["pipeline"].predict(row)[0])


example = {"square_feet": 2200, "bedrooms": 3, "bathrooms": 2, "age": 12,
           "garage_size": 2, "neighborhood_score": 7.5, "distance_to_city": 8}
print(f"\nPredicted price: ${predict_price(example):,.0f}")

# %% [markdown]
# ## Step 2: Validate the input
#
# Never feed raw client JSON straight to a model. A **Pydantic schema** with field
# bounds rejects nonsense (negative square footage, 99 bedrooms) with a clear `422`
# *before* it reaches the model — garbage in is caught at the door.

# %%
class HouseFeatures(BaseModel):
    square_feet: float = Field(gt=0, le=20000)
    bedrooms: int = Field(ge=0, le=20)
    bathrooms: int = Field(ge=0, le=20)
    age: float = Field(ge=0, le=200)
    garage_size: int = Field(ge=0, le=10)
    neighborhood_score: float = Field(ge=1, le=10)
    distance_to_city: float = Field(ge=0, le=200)


print("Valid:", HouseFeatures(**example).model_dump())

try:
    HouseFeatures(**{**example, "square_feet": -5})  # impossible house
except Exception as e:
    print("\nRejected negative square_feet (422-worthy):", type(e).__name__)

# %% [markdown]
# ## Step 3: Serve it behind auth
#
# Now assemble the service: a protected `/predict` route. We reuse the JWT pieces
# from Module 19 (abbreviated here) so only authenticated callers can spend your
# compute. Build it and drive it with `TestClient`.

# %%
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "dev-only-secret-change-me-in-production-32b"
ALGORITHM = "HS256"

app = FastAPI(title="House Price API (notebook demo)")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def make_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": sub, "exp": now + timedelta(minutes=30)}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    except jwt.PyJWTError:
        raise err


class Prediction(BaseModel):
    predicted_price: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(features: HouseFeatures, user: str = Depends(get_current_user)):
    return Prediction(predicted_price=round(predict_price(features.model_dump()), 2))


client = TestClient(app)

# Unauthenticated -> 401
print("POST /predict (no token) ->", client.post("/predict", json=example).status_code)

# With a token -> a prediction
token = make_token("demo")
r = client.post("/predict", json=example, headers={"Authorization": f"Bearer {token}"})
print("POST /predict (with token) ->", r.status_code, r.json())

# %% [markdown]
# ### Exercise 3.1 — Add a `/health` check and reject bad input
#
# Two production must-haves:
#
# 1. A **`/health`** route (already above) — load balancers ping it; it must need
#    **no auth**. Confirm it returns `200` without a token.
# 2. **Input validation** — confirm a request with an out-of-range field is rejected
#    with `422` *before* hitting the model.
#
# Write the two assertions.

# %%
# TODO:
# 1. Call GET /health WITHOUT a token; assert status_code == 200.
# 2. POST /predict with bedrooms=999 AND a valid token; assert status_code == 422
#    (Pydantic rejects it before the model runs).


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# 1. health needs no auth
h = client.get("/health")
assert h.status_code == 200, h.status_code
print("GET /health (no token) ->", h.status_code, h.json())

# 2. invalid input is rejected with 422 even with a valid token
bad = client.post(
    "/predict",
    json={**example, "bedrooms": 999},
    headers={"Authorization": f"Bearer {token}"},
)
assert bad.status_code == 422, bad.status_code
print("POST /predict (bedrooms=999) ->", bad.status_code, "(validation caught it)")
print("\nBoth checks pass.")

# %% [markdown]
# ## Step 4: Run the real service
#
# The `app/` folder is the full version:
#
# ```bash
# cd 20_capstone_model_api
# python -m app.train_model        # creates model.joblib
# uvicorn app.main:app --reload
# ```
#
# Then (see `app/README.md`): `GET /health` → `POST /token` (demo / demo-password-1)
# → `POST /predict` with a Bearer token. It loads the model once at startup, reuses
# the real `auth.py` from Module 19, and returns a `503` (not a crash) if the model
# artifact is missing.

# %% [markdown]
# ## You did it — the whole journey
#
# ```
# Pure ML            ->  train a model            (Modules 01–10)
# AI & Deep Learning ->  build neural / generative nets (07–16)
# Backend            ->  FastAPI + DB (17), crypto (18), auth (19)
# Capstone           ->  ship the model as an authenticated API (20)
# ```
#
# You can now go from a dataset to a deployed, secured prediction service. That is
# the full arc from *"it works in my notebook"* to *"it's running for users."*
#
# **Where to go next:**
# - Containerize with Docker, deploy to a cloud host
# - Add request logging, metrics, and model-version tracking (MLOps)
# - Batch predictions, caching, and rate limiting
# - Swap the in-memory users for the SQLAlchemy table from Module 19
#
# Congratulations on finishing the catalog. Keep shipping.
