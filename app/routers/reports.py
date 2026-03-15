from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from statistics import median
from typing import Dict, Any, List
from app.database import get_db
from app import models
from jinja2 import Template
from pathlib import Path

router = APIRouter(prefix="/admin/reports", tags=["reports"])

def _dur_secs(start: datetime | None, end: datetime | None) -> float | None:
    if not start or not end:
        return None
    return max(0.0, (end - start).total_seconds())

def _median(values: List[float | None]) -> float | None:
    cleaned = [v for v in values if v is not None]
    return median(cleaned) if cleaned else None

def _render_template(name: str, **ctx):
    tpl = Path(__file__).parent.parent / "templates" / name
    html = tpl.read_text(encoding="utf-8")
    return Template(html).render(**ctx)

def compute_campaign_stats(db: Session, campaign_id: int) -> Dict[str, Any]:
    c = db.query(models.Campaign).get(campaign_id)
    if not c:
        raise HTTPException(404, "campaign not found")
    q = db.query(models.CampaignRecipient).filter(models.CampaignRecipient.campaign_id == campaign_id)
    rows: List[models.CampaignRecipient] = q.all()

    total = len(rows)
    sent = sum(1 for r in rows if r.sent_at)
    opened = sum(1 for r in rows if r.opened_at)
    clicked = sum(1 for r in rows if r.clicked_at)
    landed = sum(1 for r in rows if r.landed_at)
    submitted = sum(1 for r in rows if r.submitted_at)
    reported = sum(1 for r in rows if r.reported_at)

    ttc = _median([_dur_secs(r.sent_at, r.clicked_at) for r in rows])
    ttr = _median([_dur_secs(r.sent_at, r.reported_at) for r in rows])

    by_outcome: Dict[str, int] = {}
    for r in rows:
        k = r.outcome or "unknown"
        by_outcome[k] = by_outcome.get(k, 0) + 1

    def rate(n: int, d: int) -> float:
        return round((n / d) * 100.0, 2) if d else 0.0

    return {
        "campaign": {"id": c.id, "name": c.name, "status": c.status},
        "counts": {
            "total": total,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "landed": landed,
            "submitted": submitted,
            "reported": reported,
        },
        "rates": {
            "open_rate_pct": rate(opened, sent),
            "click_rate_pct": rate(clicked, sent),
            "report_rate_pct": rate(reported, sent),
        },
        "timings_seconds": {
            "median_time_to_click": ttc,
            "median_time_to_report": ttr,
        },
        "outcomes": by_outcome,
    }

@router.get("/campaign/{campaign_id}")
def campaign_report(campaign_id: int, db: Session = Depends(get_db)):
    return compute_campaign_stats(db, campaign_id)

@router.get("/campaign/{campaign_id}/html", response_model=None)
def campaign_report_html(campaign_id: int, db: Session = Depends(get_db)):
    data = compute_campaign_stats(db, campaign_id)
    html = _render_template("admin_report.html", data=data)
    from fastapi.responses import HTMLResponse
    return HTMLResponse(html)

@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    campaigns = db.query(models.Campaign).all()
    return {
        "campaigns": [
            compute_campaign_stats(db, c.id)
            for c in campaigns
        ]
    }

# CSV export for a single campaign's recipients + events
@router.get("/campaign/{campaign_id}/export.csv")
def campaign_export_csv(campaign_id: int, db: Session = Depends(get_db)):
    import io, csv
    crs = db.query(models.CampaignRecipient).filter_by(campaign_id=campaign_id).all()
    if not crs:
        raise HTTPException(404, "No data for campaign")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "recipient_email","first_name","department","sent_at",
        "opened_at","clicked_at","landed_at","submitted_at","reported_at",
        "ip_open","ip_click","ua_open","ua_click","outcome"
    ])
    for r in crs:
        writer.writerow([
            r.recipient.email, r.recipient.first_name, r.recipient.department, r.sent_at,
            r.opened_at, r.clicked_at, r.landed_at, r.submitted_at, r.reported_at,
            r.ip_open, r.ip_click, r.ua_open, r.ua_click, r.outcome
        ])
    from fastapi.responses import Response
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="campaign_{campaign_id}.csv"'}
    )
