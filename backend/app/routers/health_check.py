"""Health check router - export health check report generation."""
import uuid
import secrets
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.models import Customer, Subscription, ShipmentCheck

router = APIRouter(prefix="/health-check", tags=["health-check"])

# In-memory store for health check tokens (production: use Redis or DB column)
_health_check_store: dict = {}


class HealthCheckRequest(BaseModel):
    name: str
    company: str
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    products_exported: str
    top_markets: str
    turnover_range: str  # "<5 Cr", "5-50 Cr", "50-500 Cr", "500 Cr+"


class HealthCheckResponse(BaseModel):
    token: str
    message: str
    report_url: str


@router.post("/request", response_model=HealthCheckResponse, status_code=201)
async def request_health_check(
    payload: HealthCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit a health check request. Creates customer record and returns access token."""
    # Create customer record
    customer_id = str(uuid.uuid4())
    customer = Customer(
        id=customer_id,
        name=payload.name,
        company=payload.company,
        whatsapp=payload.whatsapp,
        email=payload.email,
        vertical_tag="textile_apparel",
        turnover_range=payload.turnover_range,
        status="trial",
        plan="pilot",
        trial_started_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(customer)

    # Create default subscription
    subscription = Subscription(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        hsn_codes=[],
        dest_markets=[m.strip() for m in payload.top_markets.split(",")][:5],
        source_markets=["India"],
        notification_prefs={
            "digest_frequency": "weekly",
            "alert_sensitivity": "high",
            "channels": ["whatsapp", "email"],
        }
    )
    db.add(subscription)

    # Generate secure token
    token = secrets.token_urlsafe(32)

    # Generate the health check report
    from app.services.health_check_generator import generate_health_check
    report_data = await generate_health_check(
        name=payload.name,
        company=payload.company,
        products_exported=payload.products_exported,
        top_markets=payload.top_markets,
        turnover_range=payload.turnover_range,
    )

    # Store report with token (in production: store in DB)
    _health_check_store[token] = {
        "customer_id": customer_id,
        "report": report_data,
        "created_at": datetime.utcnow().isoformat(),
        "products_exported": payload.products_exported,
        "top_markets": payload.top_markets,
        "turnover_range": payload.turnover_range,
    }

    await db.commit()

    from app.config import settings
    report_url = f"{settings.FRONTEND_URL}/health-check/{token}"

    return HealthCheckResponse(
        token=token,
        message="Your Export Health Check report is ready!",
        report_url=report_url,
    )


@router.get("/{token}")
async def get_health_check(token: str, db: AsyncSession = Depends(get_db)):
    """Get health check report by token."""
    data = _health_check_store.get(token)
    if not data:
        raise HTTPException(status_code=404, detail="Health check report not found or expired")

    # Get customer info
    result = await db.execute(
        select(Customer).where(Customer.id == data["customer_id"])
    )
    customer = result.scalar_one_or_none()

    return {
        "token": token,
        "customer": {
            "name": customer.name if customer else "",
            "company": customer.company if customer else "",
            "status": customer.status if customer else "trial",
        } if customer else None,
        "products_exported": data.get("products_exported"),
        "top_markets": data.get("top_markets"),
        "turnover_range": data.get("turnover_range"),
        "report": data["report"],
        "created_at": data["created_at"],
        "trial_signup_url": f"/dashboard",
    }
