# House Price Model API — capstone

Serve the Module 10 house-price model behind Module 19's JWT auth. The full
ML → API journey.

## Run

```bash
cd 20_capstone_model_api

# 1. train + persist the model (creates model.joblib) — do this once
python -m app.train_model

# 2. serve it
uvicorn app.main:app --reload
```

Docs at http://127.0.0.1:8000/docs.

## Flow (curl)

```bash
# health (no auth) — also reports whether the model is loaded
curl http://127.0.0.1:8000/health

# log in (demo account) to get a token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \
  -d "username=demo&password=demo-password-1" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# predict (protected) — JSON body of features
curl -X POST http://127.0.0.1:8000/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"square_feet": 2200, "bedrooms": 3, "bathrooms": 2, "age": 12,
       "garage_size": 2, "neighborhood_score": 7.5, "distance_to_city": 8}'

# predict without a token -> 401
curl -i -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{}'
```

## Layout

| File | Role |
|------|------|
| `train_model.py` | trains the GradientBoosting pipeline, saves `model.joblib` |
| `model.py` | loads the artifact once, `predict_price(features)` |
| `auth.py` | password hashing + JWT (reused from Module 19) |
| `main.py` | `/health`, `/token`, protected `/predict`, input validation |

Demo credentials: `demo` / `demo-password-1`. Set `JWT_SECRET` for real use.
