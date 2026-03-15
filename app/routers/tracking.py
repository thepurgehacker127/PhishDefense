# app/routers/tracking.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import Response, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from jinja2 import Template
from pathlib import Path
from app.database import get_db
from app import models

router = APIRouter()  # <-- MUST be named exactly `router`

def _render_template(name: str, **ctx):
    tpl = Path(__file__).parent.parent / "templates" / name
    html = tpl.read_text(encoding="utf-8")
    return Template(html).render(**ctx)

@router.get("/t/{token}.png")
def track_open(token: str, request: Request, db: Session = Depends(get_db)):
    cr = db.query(models.CampaignRecipient).filter_by(token=token).first()
    pixel = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C6360000002000100FFFF03000006000557BF0000000049454E44AE426082"
    )
    if cr and not cr.opened_at:
        cr.opened_at = datetime.utcnow()
        cr.ip_open = request.client.host
        cr.ua_open = request.headers.get("user-agent", "")
        db.commit()
    return Response(content=pixel, media_type="image/png")

@router.get("/o/{token}")
def track_click(token: str, request: Request, db: Session = Depends(get_db)):
    cr = db.query(models.CampaignRecipient).filter_by(token=token).first()
    if not cr:
        raise HTTPException(status_code=404)
    if not cr.clicked_at:
        cr.clicked_at = datetime.utcnow()
        cr.ip_click = request.client.host
        cr.ua_click = request.headers.get("user-agent", "")
        db.commit()
    return RedirectResponse(url=f"/landing/{token}")

@router.get("/landing/{token}", response_class=HTMLResponse)
def landing(token: str, db: Session = Depends(get_db)):
    cr = db.query(models.CampaignRecipient).filter_by(token=token).first()
    if not cr:
        raise HTTPException(status_code=404)
    if not cr.landed_at:
        cr.landed_at = datetime.utcnow()
        db.commit()
    return HTMLResponse(_render_template("landing.html", token=token))

@router.post("/submit/{token}", response_class=HTMLResponse)
def submit(token: str, db: Session = Depends(get_db)):
    cr = db.query(models.CampaignRecipient).filter_by(token=token).first()
    if cr and not cr.submitted_at:
        cr.submitted_at = datetime.utcnow()
        cr.outcome = "submitted"
        db.commit()
    return HTMLResponse(_render_template("training.html"))

@router.get("/report/{token}")
def report(token: str, db: Session = Depends(get_db)):
    cr = db.query(models.CampaignRecipient).filter_by(token=token).first()
    if cr and not cr.reported_at:
        cr.reported_at = datetime.utcnow()
        cr.outcome = "reported"
        db.commit()
    return {"status": "reported"}