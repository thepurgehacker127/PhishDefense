# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Phishing Defense Simulator (Training)")

@app.get("/")
def root():
    return {"ok": True, "message": "Training simulator scaffold ready."}

from app.routers import tracking, campaigns, reports
# ...
app.include_router(reports.router)