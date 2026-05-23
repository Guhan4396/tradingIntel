from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.database import get_db
from app.models.models import Customer, Subscription

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str
    company: str
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    vertical_tag: Optional[str] = "textile_apparel"
    turnover_range: Optional[str] = None
    plan: Optional[str] = "pilot"


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    vertical_tag: Optional[str] = None
    turnover_range: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    hsn_codes: Optional[List[str]] = None
    dest_markets: Optional[List[str]] = None
    source_markets: Optional[List[str]] = None
    notification_prefs: Optional[dict] = None


def customer_to_dict(c: Customer) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "company": c.company,
        "whatsapp": c.whatsapp,
        "email": c.email,
        "vertical_tag": c.vertical_tag,
        "turnover_range": c.turnover_range,
        "status": c.status,
        "trial_started_at": c.trial_started_at.isoformat() if c.trial_started_at else None,
        "subscription_started_at": c.subscription_started_at.isoformat() if c.subscription_started_at else None,
        "plan": c.plan,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("")
async def list_customers(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    query = select(Customer)
    if status:
        query = query.where(Customer.status == status)
    query = query.offset(skip).limit(limit).order_by(Customer.created_at.desc())
    result = await db.execute(query)
    customers = result.scalars().all()

    count_query = select(func.count(Customer.id))
    if status:
        count_query = count_query.where(Customer.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [customer_to_dict(c) for c in customers]
    }


@router.post("", status_code=201)
async def create_customer(payload: CustomerCreate, db: AsyncSession = Depends(get_db)):
    customer = Customer(
        id=str(uuid.uuid4()),
        name=payload.name,
        company=payload.company,
        whatsapp=payload.whatsapp,
        email=payload.email,
        vertical_tag=payload.vertical_tag or "textile_apparel",
        turnover_range=payload.turnover_range,
        plan=payload.plan or "pilot",
        status="trial",
        trial_started_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(customer)

    # Create default subscription
    subscription = Subscription(
        id=str(uuid.uuid4()),
        customer_id=customer.id,
        hsn_codes=[],
        dest_markets=[],
        source_markets=["India"],
        notification_prefs={
            "digest_frequency": "weekly",
            "alert_sensitivity": "high",
            "channels": ["whatsapp", "email"]
        }
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(customer)
    return customer_to_dict(customer)


@router.get("/{customer_id}")
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_to_dict(customer)


@router.patch("/{customer_id}")
async def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(customer, key, value)

    if payload.status == "active" and not customer.subscription_started_at:
        customer.subscription_started_at = datetime.utcnow()

    await db.commit()
    await db.refresh(customer)
    return customer_to_dict(customer)


@router.get("/{customer_id}/subscription")
async def get_subscription(customer_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.customer_id == customer_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {
        "id": sub.id,
        "customer_id": sub.customer_id,
        "hsn_codes": sub.hsn_codes or [],
        "dest_markets": sub.dest_markets or [],
        "source_markets": sub.source_markets or [],
        "notification_prefs": sub.notification_prefs or {},
    }


@router.put("/{customer_id}/subscription")
async def update_subscription(
    customer_id: str,
    payload: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(Subscription.customer_id == customer_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        # Create if missing
        sub = Subscription(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            hsn_codes=[],
            dest_markets=[],
            source_markets=["India"],
            notification_prefs={}
        )
        db.add(sub)

    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(sub, key, value)

    await db.commit()
    await db.refresh(sub)
    return {
        "id": sub.id,
        "customer_id": sub.customer_id,
        "hsn_codes": sub.hsn_codes or [],
        "dest_markets": sub.dest_markets or [],
        "source_markets": sub.source_markets or [],
        "notification_prefs": sub.notification_prefs or {},
    }
