# PhishDefense — Phishing Defense Simulator (Training Only)

Ethical, opt-in phishing simulation and awareness training tool.

## Quick Start
- Python FastAPI backend
- Postgres + Redis + MailHog via Docker (later phases)
- Do **not** store real credentials; training pages only

### Dev
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000