"""Customer-intelligence matching service."""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.models import Subscription, Customer, Delivery, Alert, IntelligenceItem

logger = logging.getLogger(__name__)


async def find_matching_customers(
    intelligence_item: IntelligenceItem,
    db: AsyncSession,
) -> List[str]:
    """
    Find customers whose subscriptions match a given intelligence item.
    Matches based on:
    - HSN code overlap between item's hsn_codes and subscription's hsn_codes
    - Country overlap between item's countries and subscription's dest_markets OR source_markets
    - Deduplication: skip customers who already received this item
    Returns list of matching customer_ids.
    """
    item_hsn_codes = set(intelligence_item.hsn_codes or [])
    item_countries = set(intelligence_item.countries or [])
    item_id = intelligence_item.id

    # Get all active/trial customer subscriptions
    result = await db.execute(
        select(Subscription, Customer)
        .join(Customer, Subscription.customer_id == Customer.id)
        .where(Customer.status.in_(["trial", "active"]))
    )
    rows = result.all()

    # Get customers who already received this item
    already_delivered_result = await db.execute(
        select(Delivery.customer_id)
        .where(Delivery.item_id == item_id)
    )
    already_delivered = set(row[0] for row in already_delivered_result.all())

    matching_customer_ids = []

    for subscription, customer in rows:
        customer_id = customer.id

        # Skip if already delivered
        if customer_id in already_delivered:
            continue

        sub_hsn_codes = set(subscription.hsn_codes or [])
        sub_dest_markets = set(subscription.dest_markets or [])
        sub_source_markets = set(subscription.source_markets or [])

        # Check for HSN overlap (if both have codes specified)
        hsn_match = True
        if item_hsn_codes and sub_hsn_codes:
            # Check if any HSN codes overlap (including prefix matching)
            hsn_match = False
            for item_code in item_hsn_codes:
                for sub_code in sub_hsn_codes:
                    # Match if either is a prefix of the other
                    if item_code.startswith(sub_code[:4]) or sub_code.startswith(item_code[:4]):
                        hsn_match = True
                        break
                if hsn_match:
                    break

        # Check for country overlap
        country_match = True
        if item_countries and (sub_dest_markets or sub_source_markets):
            all_sub_markets = sub_dest_markets | sub_source_markets
            country_match = bool(item_countries & all_sub_markets)
            # Also match on broad regions
            if not country_match:
                eu_countries = {"EU", "Germany", "France", "Italy", "Spain", "Netherlands",
                                "Belgium", "Poland", "Sweden", "Austria"}
                if item_countries & eu_countries and sub_dest_markets & eu_countries:
                    country_match = True

        if hsn_match and country_match:
            matching_customer_ids.append(customer_id)

    logger.info(f"Intelligence item {item_id}: matched {len(matching_customer_ids)} customers")
    return matching_customer_ids


async def create_alerts_for_urgent_items(db: AsyncSession) -> int:
    """
    Find unalerted urgent intelligence items and create alerts for matching customers.
    Returns number of alerts created.
    """
    # Find urgent items that haven't been fully alerted yet
    # (items with no deliveries, or items recent enough to re-check)
    result = await db.execute(
        select(IntelligenceItem)
        .where(IntelligenceItem.severity == "urgent")
        .order_by(IntelligenceItem.processed_at.desc())
        .limit(10)
    )
    urgent_items = result.scalars().all()

    alerts_created = 0

    for item in urgent_items:
        matching_customers = await find_matching_customers(item, db)

        for customer_id in matching_customers:
            # Check if alert already exists
            existing_alert = await db.execute(
                select(Alert).where(
                    and_(Alert.item_id == item.id, Alert.customer_id == customer_id)
                )
            )
            if existing_alert.scalar_one_or_none():
                continue

            # Create alert
            alert = Alert(
                id=str(uuid.uuid4()),
                customer_id=customer_id,
                item_id=item.id,
                urgency=item.severity,
                sent_at=datetime.utcnow(),
            )
            db.add(alert)

            # Create delivery record
            delivery = Delivery(
                id=str(uuid.uuid4()),
                customer_id=customer_id,
                item_id=item.id,
                channel="dashboard",
                sent_at=datetime.utcnow(),
                extra_data={"triggered_by": "matcher", "urgency": item.severity},
            )
            db.add(delivery)
            alerts_created += 1

    if alerts_created > 0:
        await db.commit()
        logger.info(f"Created {alerts_created} new alerts")

    return alerts_created


async def prepare_weekly_digest(customer_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Prepare weekly digest of intelligence items for a customer.
    Returns items not yet delivered to this customer, sorted by severity.
    """
    result = await db.execute(
        select(Subscription).where(Subscription.customer_id == customer_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        return []

    # Get undelivered intelligence items from the last 7 days
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)

    # Items not yet delivered to this customer
    delivered_item_ids_result = await db.execute(
        select(Delivery.item_id).where(Delivery.customer_id == customer_id)
    )
    delivered_item_ids = set(row[0] for row in delivered_item_ids_result.all())

    items_result = await db.execute(
        select(IntelligenceItem)
        .where(IntelligenceItem.processed_at >= week_ago)
        .order_by(
            IntelligenceItem.severity.desc(),
            IntelligenceItem.processed_at.desc()
        )
        .limit(20)
    )
    all_items = items_result.scalars().all()

    digest_items = []
    for item in all_items:
        if item.id in delivered_item_ids:
            continue

        # Check relevance to this customer's subscription
        item_hsn = set(item.hsn_codes or [])
        item_countries = set(item.countries or [])
        sub_hsn = set(subscription.hsn_codes or [])
        sub_markets = set(subscription.dest_markets or []) | set(subscription.source_markets or [])

        # Include if relevant or if no filters set
        is_relevant = True
        if sub_hsn and item_hsn:
            is_relevant = bool(item_hsn & sub_hsn) or any(
                ic[:4] in sc[:4] or sc[:4] in ic[:4]
                for ic in item_hsn for sc in sub_hsn
            )
        if sub_markets and item_countries and is_relevant:
            is_relevant = bool(item_countries & sub_markets)

        if is_relevant:
            digest_items.append({
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "severity": item.severity,
                "hsn_codes": item.hsn_codes or [],
                "countries": item.countries or [],
                "action_text": item.action_text,
                "source_url": item.source_url,
            })

    return digest_items[:10]  # Max 10 items per digest
