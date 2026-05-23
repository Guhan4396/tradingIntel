import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey,
    Enum as SAEnum, Integer, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    type = Column(String(100), nullable=False)  # rss, scrape, api
    vertical_tags = Column(JSONB, default=list)
    refresh_cadence_hours = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ingested_items = relationship("IngestedItem", back_populates="source")


class IngestedItem(Base):
    __tablename__ = "ingested_items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    source_id = Column(UUID(as_uuid=False), ForeignKey("sources.id"), nullable=False)
    raw_content = Column(Text, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(
        SAEnum("pending", "processed", "failed", name="ingested_status"),
        default="pending"
    )
    extra_data = Column(JSONB, default=dict)

    source = relationship("Source", back_populates="ingested_items")
    intelligence_items = relationship("IntelligenceItem", back_populates="ingested_item")


class IntelligenceItem(Base):
    __tablename__ = "intelligence_items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    ingested_item_id = Column(UUID(as_uuid=False), ForeignKey("ingested_items.id"), nullable=True)
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=False)
    severity = Column(
        SAEnum("urgent", "watch", "opportunity", name="severity_type"),
        nullable=False,
        default="watch"
    )
    hsn_codes = Column(JSONB, default=list)
    countries = Column(JSONB, default=list)
    action_text = Column(Text)
    source_url = Column(String(1024))
    processed_at = Column(DateTime, default=datetime.utcnow)
    is_reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text)

    ingested_item = relationship("IngestedItem", back_populates="intelligence_items")
    deliveries = relationship("Delivery", back_populates="item")
    alerts = relationship("Alert", back_populates="item")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    whatsapp = Column(String(20))
    email = Column(String(255))
    vertical_tag = Column(String(100), default="textile_apparel")
    turnover_range = Column(String(50))
    status = Column(
        SAEnum("trial", "active", "paused", "churned", name="customer_status"),
        default="trial"
    )
    trial_started_at = Column(DateTime, default=datetime.utcnow)
    subscription_started_at = Column(DateTime)
    plan = Column(
        SAEnum("monthly", "annual", "pilot", name="plan_type"),
        default="pilot"
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    health_check_token = Column(String(100), unique=True, nullable=True)
    health_check_data = Column(JSONB, nullable=True)

    subscription = relationship("Subscription", back_populates="customer", uselist=False)
    deliveries = relationship("Delivery", back_populates="customer")
    shipment_checks = relationship("ShipmentCheck", back_populates="customer")
    alerts = relationship("Alert", back_populates="customer")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), unique=True, nullable=False)
    hsn_codes = Column(JSONB, default=list)
    dest_markets = Column(JSONB, default=list)
    source_markets = Column(JSONB, default=list)
    notification_prefs = Column(JSONB, default=dict)

    customer = relationship("Customer", back_populates="subscription")


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=False)
    item_id = Column(UUID(as_uuid=False), ForeignKey("intelligence_items.id"), nullable=False)
    channel = Column(
        SAEnum("whatsapp", "email", "dashboard", name="delivery_channel"),
        nullable=False
    )
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)
    action_taken = Column(String(255))
    extra_data = Column(JSONB, default=dict)

    customer = relationship("Customer", back_populates="deliveries")
    item = relationship("IntelligenceItem", back_populates="deliveries")


class ShipmentCheck(Base):
    __tablename__ = "shipment_checks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=True)
    hsn_code = Column(String(20), nullable=False)
    dest_country = Column(String(100), nullable=False)
    quantity = Column(Float)
    value_inr = Column(Float)
    response = Column(JSONB, default=dict)
    checked_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="shipment_checks")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=False)
    item_id = Column(UUID(as_uuid=False), ForeignKey("intelligence_items.id"), nullable=False)
    urgency = Column(String(50), default="watch")
    sent_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)

    customer = relationship("Customer", back_populates="alerts")
    item = relationship("IntelligenceItem", back_populates="alerts")
