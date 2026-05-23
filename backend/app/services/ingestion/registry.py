"""Source registry - maps sources to ingester classes and runs them."""
import logging
from datetime import datetime, timedelta
from typing import List, Type, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Source, IngestedItem
from app.services.ingestion.base import BaseIngester
from app.services.ingestion.ingesters.ustr import USTRIngester
from app.services.ingestion.ingesters.eu_taric import EUTaricIngester
from app.services.ingestion.ingesters.uk_hmrc import UKHMRCIngester
from app.services.ingestion.ingesters.dgft import DGFTIngester
from app.services.ingestion.ingesters.cbic import CBICIngester

logger = logging.getLogger(__name__)

# Mapping from source name to ingester class
SOURCE_INGESTER_MAP: Dict[str, Type[BaseIngester]] = {
    "USTR": USTRIngester,
    "EU TARIC": EUTaricIngester,
    "UK HMRC": UKHMRCIngester,
    "DGFT": DGFTIngester,
    "CBIC": CBICIngester,
}

# Default sources to seed in the database
DEFAULT_SOURCES = [
    {
        "name": "USTR",
        "url": "https://ustr.gov/about-us/policy-offices/press-office/press-releases",
        "type": "scrape",
        "vertical_tags": ["trade_policy", "tariff", "us_market"],
        "refresh_cadence_hours": 12,
    },
    {
        "name": "EU TARIC",
        "url": "https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp",
        "type": "rss",
        "vertical_tags": ["trade_policy", "tariff", "eu_market"],
        "refresh_cadence_hours": 24,
    },
    {
        "name": "UK HMRC",
        "url": "https://www.trade-tariff.service.gov.uk",
        "type": "api",
        "vertical_tags": ["trade_policy", "tariff", "uk_market"],
        "refresh_cadence_hours": 24,
    },
    {
        "name": "DGFT",
        "url": "https://www.dgft.gov.in",
        "type": "scrape",
        "vertical_tags": ["export_policy", "incentives", "india"],
        "refresh_cadence_hours": 12,
    },
    {
        "name": "CBIC",
        "url": "https://cbic.gov.in",
        "type": "scrape",
        "vertical_tags": ["customs", "duty", "classification", "india"],
        "refresh_cadence_hours": 24,
    },
    {
        "name": "WTO Trade Policy Review",
        "url": "https://www.wto.org/english/tratop_e/tpr_e/tpr_e.htm",
        "type": "scrape",
        "vertical_tags": ["trade_policy", "global", "multilateral"],
        "refresh_cadence_hours": 72,
    },
    {
        "name": "India Ministry of Commerce",
        "url": "https://commerce.gov.in/press-releases/",
        "type": "scrape",
        "vertical_tags": ["trade_policy", "export_policy", "india"],
        "refresh_cadence_hours": 24,
    },
    {
        "name": "AEPC",
        "url": "https://www.aepc.in/",
        "type": "scrape",
        "vertical_tags": ["apparel", "export", "industry", "india"],
        "refresh_cadence_hours": 48,
    },
    {
        "name": "Textiles Committee India",
        "url": "https://textilescommittee.nic.in/",
        "type": "scrape",
        "vertical_tags": ["textile", "quality", "certification", "india"],
        "refresh_cadence_hours": 48,
    },
    {
        "name": "US Federal Register Trade",
        "url": "https://www.federalregister.gov/documents/search?conditions%5Bagencies%5D%5B%5D=international-trade-administration",
        "type": "api",
        "vertical_tags": ["trade_policy", "tariff", "us_market", "anti_dumping"],
        "refresh_cadence_hours": 24,
    },
]


async def seed_default_sources(db: AsyncSession) -> None:
    """Seed default sources into the database if they don't exist."""
    import uuid

    for source_data in DEFAULT_SOURCES:
        result = await db.execute(
            select(Source).where(Source.name == source_data["name"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            source = Source(
                id=str(uuid.uuid4()),
                name=source_data["name"],
                url=source_data["url"],
                type=source_data["type"],
                vertical_tags=source_data["vertical_tags"],
                refresh_cadence_hours=source_data["refresh_cadence_hours"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(source)
            logger.info(f"Seeded source: {source_data['name']}")

    await db.commit()


async def run_all_ingesters(db: AsyncSession) -> None:
    """Run all active ingesters that are due for refresh."""
    result = await db.execute(
        select(Source).where(Source.is_active == True)
    )
    sources = result.scalars().all()

    for source in sources:
        try:
            ingester_class = SOURCE_INGESTER_MAP.get(source.name)
            if not ingester_class:
                logger.debug(f"No ingester found for source: {source.name}")
                continue

            # Check if refresh is due
            last_ingested_result = await db.execute(
                select(IngestedItem.ingested_at)
                .where(IngestedItem.source_id == source.id)
                .order_by(IngestedItem.ingested_at.desc())
                .limit(1)
            )
            last_ingested = last_ingested_result.scalar_one_or_none()

            cadence_hours = source.refresh_cadence_hours or 24
            if last_ingested:
                next_run = last_ingested + timedelta(hours=cadence_hours)
                if datetime.utcnow() < next_run:
                    logger.debug(f"Skipping {source.name}: next run at {next_run}")
                    continue

            ingester = ingester_class(source=source)
            await ingester.run(db)

        except Exception as e:
            logger.error(f"Error running ingester for {source.name}: {e}")
            continue


async def run_ingester_by_name(source_name: str, db: AsyncSession) -> List[IngestedItem]:
    """Run a specific ingester by source name."""
    result = await db.execute(
        select(Source).where(Source.name == source_name, Source.is_active == True)
    )
    source = result.scalar_one_or_none()

    if not source:
        logger.warning(f"Source not found or inactive: {source_name}")
        return []

    ingester_class = SOURCE_INGESTER_MAP.get(source_name)
    if not ingester_class:
        logger.warning(f"No ingester class for: {source_name}")
        return []

    ingester = ingester_class(source=source)
    return await ingester.run(db)
