"""Auth API: register, get a token, and a protected /me route.

Run:  cd 19_auth_jwt && uvicorn app.main:app --reload
Flow: POST /register -> POST /token -> GET /me (with Bearer token)
"""
from __future__ import annotations

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import auth, models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth API", version="1.0.0")

# Tells FastAPI/Swagger where clients exchange credentials for a token, and to
# read the "Authorization: Bearer <token>" header on protected routes.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """Dependency that turns a Bearer token into the logged-in User, or 401s."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        username = auth.decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_error

    user = db.scalar(select(models.User).where(models.User.username == username))
    if user is None:
        raise credentials_error
    return user


@app.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(models.User).where(models.User.username == data.username))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
    user = models.User(
        username=data.username,
        hashed_password=auth.hash_password(data.password),  # hash, never store plaintext
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/token", response_model=schemas.Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """OAuth2 password flow: verify username+password, issue a JWT."""
    user = db.scalar(select(models.User).where(models.User.username == form.username))
    if user is None or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return schemas.Token(access_token=auth.create_access_token(subject=user.username))


@app.get("/me", response_model=schemas.UserRead)
def read_me(current_user: models.User = Depends(get_current_user)):
    """Protected: only reachable with a valid Bearer token."""
    return current_user
