# app/routers/campaigns.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models
from app.emailing import gen_token, render_email, send_training_email

router = APIRouter(prefix="/admin", tags=["admin"])  # <-- MUST be named `router`

@router.post("/templates")
def create_template(data: dict, db: Session = Depends(get_db)):
    name = data.get("name")
    subject = data.get("subject")
    html_body = data.get("html_body")
    if not name or not subject or not html_body:
        raise HTTPException(400, "name, subject, and html_body are required")
    exists = db.query(models.Template).filter(models.Template.name == name).first()
    if exists:
        raise HTTPException(409, f"Template '{name}' already exists")
    t = models.Template(
        name=name, subject=subject, html_body=html_body,
        landing_html=data.get("landing_html"),
        difficulty=data.get("difficulty"),
        category=data.get("category"),
    )
    db.add(t); db.commit(); db.refresh(t)
    return {"id": t.id, "name": t.name}

@router.post("/recipients")
def create_recipient(data: dict, db: Session = Depends(get_db)):
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(400, "email is required")
    exists = db.query(models.Recipient).filter(models.Recipient.email == email).first()
    if exists:
        return {"id": exists.id}
    r = models.Recipient(
        email=email,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        department=data.get("department"),
    )
    db.add(r); db.commit(); db.refresh(r)
    return {"id": r.id}

@router.post("/campaigns")
def create_campaign(data: dict, db: Session = Depends(get_db)):
    name = data.get("name")
    template_id = data.get("template_id")
    from_name = data.get("from_name")
    from_email = data.get("from_email")
    if not all([name, template_id, from_name, from_email]):
        raise HTTPException(400, "name, template_id, from_name, from_email are required")
    t = db.get(models.Template, template_id)
    if not t:
        raise HTTPException(404, "template not found")
    exists = db.query(models.Campaign).filter(models.Campaign.name == name).first()
    if exists:
        raise HTTPException(409, f"Campaign '{name}' already exists")
    c = models.Campaign(
        name=name, template_id=template_id,
        from_name=from_name, from_email=from_email,
        start_at=datetime.utcnow(), status="scheduled"
    )
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id, "name": c.name}

@router.post("/campaigns/{campaign_id}/enqueue_one/{recipient_id}")
def send_one(campaign_id: int, recipient_id: int, db: Session = Depends(get_db)):
    c = db.get(models.Campaign, campaign_id)
    r = db.get(models.Recipient, recipient_id)
    if not c or not r:
        raise HTTPException(404, "campaign or recipient not found")
    t = c.template
    if not t:
        raise HTTPException(500, "campaign template missing")
    token = gen_token()
    cr = models.CampaignRecipient(
        campaign_id=c.id, recipient_id=r.id, token=token,
        sent_at=datetime.utcnow(), delivered=True
    )
    db.add(cr); db.commit(); db.refresh(cr)
    subject, html = render_email(t.subject, t.html_body, r.first_name, token)
    send_training_email(r.email, subject, html)
    return {"status": "sent", "campaign_id": c.id, "recipient_id": r.id, "token": token}