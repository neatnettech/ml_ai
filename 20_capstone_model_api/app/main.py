"""Capstone API: serve the house-price model behind JWT auth.

End-to-end: train (train_model.py) -> persist (model.joblib) -> load (model.py)
-> validate input (Pydantic) -> predict -> protect with auth (Module 19).

Run:
  python -m app.train_model          # once, to create model.joblib
  uvicorn app.main:app --reload
"""
from __future__ import annotations

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from . import auth, model

app = FastAPI(title="House Price Model API", version="1.0.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Tiny in-memory user store. In a real service this is the SQLAlchemy users table
# from Module 19. One demo account, hashed at startup.
_USERS = {"demo": auth.hash_password("demo-password-1")}


# ---- Schemas: the prediction contract -------------------------------------
class HouseFeatures(BaseModel):
    """Validated input. Bounds catch nonsense (negative area, 99 bedrooms) early."""

    square_feet: float = Field(gt=0, le=20000)
    bedrooms: int = Field(ge=0, le=20)
    bathrooms: int = Field(ge=0, le=20)
    age: float = Field(ge=0, le=200)
    garage_size: int = Field(ge=0, le=10)
    neighborhood_score: float = Field(ge=1, le=10)
    distance_to_city: float = Field(ge=0, le=200)


class Prediction(BaseModel):
    predicted_price: float


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Auth dependency ------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        username = auth.decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_error
    if username not in _USERS:
        raise credentials_error
    return username


# ---- Lifecycle ------------------------------------------------------------
@app.on_event("startup")
def _warm_model() -> None:
    # Load the model once at startup so the first request is not slow.
    # If the artifact is missing we keep serving /health and surface a clear
    # error on /predict instead of crashing the whole app.
    try:
        model.load_model()
    except FileNotFoundError as exc:
        print(f"[startup] {exc}")


# ---- Routes ---------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "model_loaded": model.MODEL_PATH.exists()}


@app.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    hashed = _USERS.get(form.username)
    if hashed is None or not auth.verify_password(form.password, hashed):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=auth.create_access_token(subject=form.username))


@app.post("/predict", response_model=Prediction)
def predict(features: HouseFeatures, current_user: str = Depends(get_current_user)):
    """Protected: predict a house price from validated features."""
    try:
        price = model.predict_price(features.model_dump())
    except FileNotFoundError as exc:
        # Model artifact missing — operator error, not the client's fault.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return Prediction(predicted_price=round(price, 2))
