# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    subject = Column(String(255), nullable=False)
    html_body = Column(Text, nullable=False)
    landing_html = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=True)
    category = Column(String(50), nullable=True)

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    from_name = Column(String(120), nullable=False)
    from_email = Column(String(255), nullable=False)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="draft")

    template = relationship("Template")
    recipients = relationship("CampaignRecipient", back_populates="campaign")

class Recipient(Base):
    __tablename__ = "recipients"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(120), nullable=True)
    last_name = Column(String(120), nullable=True)
    department = Column(String(120), nullable=True)

class CampaignRecipient(Base):
    __tablename__ = "campaign_recipients"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("recipients.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered = Column(Boolean, default=False)
    bounced_reason = Column(String(255), nullable=True)

    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    landed_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    reported_at = Column(DateTime, nullable=True)

    ip_open = Column(String(64), nullable=True)
    ip_click = Column(String(64), nullable=True)
    ua_open = Column(String(255), nullable=True)
    ua_click = Column(String(255), nullable=True)
    outcome = Column(String(40), nullable=True)  # ignored/reported/clicked/submitted

    campaign = relationship("Campaign", back_populates="recipients")
    recipient = relationship("Recipient")