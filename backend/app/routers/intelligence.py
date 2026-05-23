from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.models import IntelligenceItem, IngestedItem

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class ReviewPayload(BaseModel):
    reviewer_notes: Optional[str] = None
    is_reviewed: bool = True


def intel_to_dict(item: IntelligenceItem) -> dict:
    return {
        "id": item.id,
        "ingested_item_id": item.ingested_item_id,
        "title": item.title,
        "summary": item.summary,
        "severity": item.severity,
        "hsn_codes": item.hsn_codes or [],
        "countries": item.countries or [],
        "action_text": item.action_text,
        "source_url": item.source_url,
        "processed_at": item.processed_at.isoformat() if item.processed_at else None,
        "is_reviewed": item.is_reviewed,
        "reviewer_notes": item.reviewer_notes,
    }


@router.get("")
async def list_intelligence(
    severity: Optional[str] = Query(None),
    hsn_code: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(IntelligenceItem).order_by(IntelligenceItem.processed_at.desc())

    if severity:
        query = query.where(IntelligenceItem.severity == severity)
    if hsn_code:
        query = query.where(IntelligenceItem.hsn_codes.contains([hsn_code]))
    if country:
        query = query.where(IntelligenceItem.countries.contains([country]))
    if from_date:
        try:
            dt = datetime.fromisoformat(from_date)
            query = query.where(IntelligenceItem.processed_at >= dt)
        except ValueError:
            pass
    if to_date:
        try:
            dt = datetime.fromisoformat(to_date)
            query = query.where(IntelligenceItem.processed_at <= dt)
        except ValueError:
            pass

    count_query = select(func.count(IntelligenceItem.id))
    if severity:
        count_query = count_query.where(IntelligenceItem.severity == severity)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [intel_to_dict(i) for i in items]
    }


@router.post("/ingest")
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    from app.services.ingestion.registry import run_all_ingesters
    background_tasks.add_task(run_all_ingesters, db)
    return {"status": "ingestion_triggered", "message": "Ingestion started in background"}


@router.post("/{item_id}/review")
async def review_item(
    item_id: str,
    payload: ReviewPayload,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(IntelligenceItem).where(IntelligenceItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Intelligence item not found")

    item.is_reviewed = payload.is_reviewed
    item.reviewer_notes = payload.reviewer_notes
    await db.commit()
    await db.refresh(item)
    return intel_to_dict(item)


@router.get("/{item_id}")
async def get_intelligence_item(item_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IntelligenceItem).where(IntelligenceItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Intelligence item not found")
    return intel_to_dict(item)
