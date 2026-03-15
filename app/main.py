# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import tracking, campaigns, reports  # <-- import the modules

Base.metadata.create_all(bind=engine)  # safe during dev

app = FastAPI(title="Phishing Defense Simulator (Training)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

@app.get("/")
def root():
    return {"ok": True, "message": "Phase 3 ready: tracking + email"}

# <-- include the routers; these lines must execute at import time
app.include_router(tracking.router)
app.include_router(campaigns.router)
app.include_router(reports.router)