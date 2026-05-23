from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.models import ShipmentCheck
from app.services.shipment_checker import check_shipment

router = APIRouter(prefix="/shipments", tags=["shipments"])


class ShipmentCheckRequest(BaseModel):
    customer_id: Optional[str] = None
    hsn_code: str
    dest_country: str
    quantity: Optional[float] = None
    value_inr: Optional[float] = None


@router.post("/check")
async def run_shipment_check(
    payload: ShipmentCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await check_shipment(
        hsn_code=payload.hsn_code,
        dest_country=payload.dest_country,
        quantity=payload.quantity,
        value_inr=payload.value_inr,
        customer_id=payload.customer_id,
        db=db,
    )
    return result


@router.get("/history")
async def get_shipment_history(
    customer_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    query = select(ShipmentCheck).order_by(ShipmentCheck.checked_at.desc())
    if customer_id:
        query = query.where(ShipmentCheck.customer_id == customer_id)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    checks = result.scalars().all()

    return {
        "items": [
            {
                "id": c.id,
                "customer_id": c.customer_id,
                "hsn_code": c.hsn_code,
                "dest_country": c.dest_country,
                "quantity": c.quantity,
                "value_inr": c.value_inr,
                "response": c.response,
                "checked_at": c.checked_at.isoformat() if c.checked_at else None,
            }
            for c in checks
        ]
    }
