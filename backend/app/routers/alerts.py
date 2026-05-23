from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.models import Alert, IntelligenceItem

router = APIRouter(prefix="/alerts", tags=["alerts"])


def alert_to_dict(alert: Alert, item: Optional[IntelligenceItem] = None) -> dict:
    result = {
        "id": alert.id,
        "customer_id": alert.customer_id,
        "item_id": alert.item_id,
        "urgency": alert.urgency,
        "sent_at": alert.sent_at.isoformat() if alert.sent_at else None,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "acknowledged": alert.acknowledged_at is not None,
    }
    if item:
        result["item"] = {
            "title": item.title,
            "summary": item.summary,
            "severity": item.severity,
            "hsn_codes": item.hsn_codes or [],
            "countries": item.countries or [],
            "action_text": item.action_text,
            "source_url": item.source_url,
        }
    return result


@router.get("")
async def list_alerts(
    customer_id: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert, IntelligenceItem).join(
        IntelligenceItem, Alert.item_id == IntelligenceItem.id
    ).order_by(Alert.sent_at.desc())

    if customer_id:
        query = query.where(Alert.customer_id == customer_id)
    if acknowledged is not None:
        if acknowledged:
            query = query.where(Alert.acknowledged_at.isnot(None))
        else:
            query = query.where(Alert.acknowledged_at.is_(None))

    count_q = select(func.count(Alert.id))
    if customer_id:
        count_q = count_q.where(Alert.customer_id == customer_id)
    total_result = await db.execute(count_q)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [alert_to_dict(alert, item) for alert, item in rows]
    }


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return alert_to_dict(alert)
