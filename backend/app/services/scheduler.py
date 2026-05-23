"""APScheduler background jobs for TradingIntel."""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def _run_ingestion():
    """Scheduled job: run ingestion for all due sources."""
    logger.info("Scheduler: Starting scheduled ingestion")
    try:
        from app.services.ingestion.registry import run_all_ingesters
        async with AsyncSessionLocal() as db:
            await run_all_ingesters(db)
    except Exception as e:
        logger.error(f"Scheduler: Ingestion job failed: {e}")


async def _process_intelligence():
    """Scheduled job: process pending ingested items through AI."""
    logger.info("Scheduler: Processing pending intelligence items")
    try:
        from app.services.intelligence.processor import process_pending_items
        async with AsyncSessionLocal() as db:
            count = await process_pending_items(db)
            if count > 0:
                logger.info(f"Scheduler: Processed {count} intelligence items")
    except Exception as e:
        logger.error(f"Scheduler: Intelligence processing failed: {e}")


async def _run_matcher_and_alerts():
    """Scheduled job: run matcher and create alerts for urgent items."""
    logger.info("Scheduler: Running matcher for urgent alerts")
    try:
        from app.services.matching.matcher import create_alerts_for_urgent_items
        async with AsyncSessionLocal() as db:
            count = await create_alerts_for_urgent_items(db)
            if count > 0:
                logger.info(f"Scheduler: Created {count} new alerts")
    except Exception as e:
        logger.error(f"Scheduler: Matcher job failed: {e}")


async def _send_weekly_digests():
    """Scheduled job: send weekly digests to all active customers (Monday 9 AM IST)."""
    logger.info("Scheduler: Sending weekly digests")
    try:
        from sqlalchemy import select
        from app.models.models import Customer, Delivery
        from app.services.matching.matcher import prepare_weekly_digest
        from app.services.delivery.whatsapp import send_message, format_weekly_digest
        from app.services.delivery.email_service import send_digest_email

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Customer).where(Customer.status.in_(["trial", "active"]))
            )
            customers = result.scalars().all()

            sent_count = 0
            for customer in customers:
                try:
                    digest_items = await prepare_weekly_digest(customer.id, db)

                    if not digest_items:
                        logger.debug(f"No digest items for customer {customer.id}")
                        continue

                    # Send via WhatsApp if available
                    if customer.whatsapp:
                        msg = format_weekly_digest(customer.name, digest_items)
                        await send_message(customer.whatsapp, msg)

                    # Send via email if available
                    if customer.email:
                        await send_digest_email(customer, digest_items)

                    # Mark items as delivered
                    import uuid
                    from datetime import datetime
                    for item in digest_items:
                        delivery = Delivery(
                            id=str(uuid.uuid4()),
                            customer_id=customer.id,
                            item_id=item["id"],
                            channel="email" if customer.email else "whatsapp",
                            sent_at=datetime.utcnow(),
                            extra_data={"digest_type": "weekly"},
                        )
                        db.add(delivery)

                    await db.commit()
                    sent_count += 1

                except Exception as e:
                    logger.error(f"Scheduler: Error sending digest to customer {customer.id}: {e}")
                    await db.rollback()

            logger.info(f"Scheduler: Weekly digests sent to {sent_count}/{len(customers)} customers")

    except Exception as e:
        logger.error(f"Scheduler: Weekly digest job failed: {e}")


def start_scheduler():
    """Initialize and start all scheduled jobs."""
    # Ingestion: every hour
    scheduler.add_job(
        _run_ingestion,
        trigger=IntervalTrigger(hours=1),
        id="ingestion",
        name="Source Ingestion",
        replace_existing=True,
        misfire_grace_time=300,  # 5 minute grace
    )

    # Intelligence processing: every 15 minutes
    scheduler.add_job(
        _process_intelligence,
        trigger=IntervalTrigger(minutes=15),
        id="intelligence_processing",
        name="Intelligence Processing",
        replace_existing=True,
        misfire_grace_time=120,
    )

    # Alert matching: every 5 minutes
    scheduler.add_job(
        _run_matcher_and_alerts,
        trigger=IntervalTrigger(minutes=5),
        id="matcher_alerts",
        name="Matcher & Alerts",
        replace_existing=True,
        misfire_grace_time=60,
    )

    # Weekly digest: every Monday at 9:00 AM IST
    scheduler.add_job(
        _send_weekly_digests,
        trigger=CronTrigger(
            day_of_week="mon",
            hour=9,
            minute=0,
            timezone="Asia/Kolkata"
        ),
        id="weekly_digest",
        name="Weekly Digest",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with jobs: ingestion(1h), processing(15m), alerts(5m), digest(Mon 9AM IST)")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
