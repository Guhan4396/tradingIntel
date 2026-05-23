"""Abstract base ingester class with shared save logic and error handling."""
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import IngestedItem, Source

logger = logging.getLogger(__name__)


class BaseIngester(ABC):
    """Abstract base class for all data ingesters."""

    source_name: str = ""
    source_url: str = ""
    source_type: str = "scrape"  # rss, scrape, api

    def __init__(self, source: Optional[Source] = None):
        self.source = source
        self.source_id = source.id if source else None

    @abstractmethod
    async def ingest(self) -> List[Dict[str, Any]]:
        """
        Fetch raw content from the source.
        Returns a list of dicts with keys:
            - raw_content: str
            - metadata: dict (url, title, published_at, etc.)
        """
        raise NotImplementedError

    async def save_to_db(self, items: List[Dict[str, Any]], db: AsyncSession) -> List[IngestedItem]:
        """Save ingested items to the database. Deduplicates by checking existing content."""
        if not items:
            return []

        saved = []
        for item_data in items:
            raw_content = item_data.get("raw_content", "")
            if not raw_content or not raw_content.strip():
                continue

            # Check for duplicate by source_id + url in metadata
            metadata = item_data.get("metadata", {})
            source_url = metadata.get("url", "")

            if source_url and self.source_id:
                existing_query = select(IngestedItem).where(
                    IngestedItem.source_id == self.source_id,
                    IngestedItem.metadata["url"].astext == source_url
                )
                existing_result = await db.execute(existing_query)
                existing = existing_result.scalar_one_or_none()
                if existing:
                    logger.debug(f"Skipping duplicate item from {source_url}")
                    continue

            ingested_item = IngestedItem(
                id=str(uuid.uuid4()),
                source_id=self.source_id,
                raw_content=raw_content[:50000],  # Limit size
                ingested_at=datetime.utcnow(),
                status="pending",
                metadata=metadata,
            )
            db.add(ingested_item)
            saved.append(ingested_item)

        if saved:
            try:
                await db.commit()
                logger.info(f"{self.source_name}: saved {len(saved)} new items")
            except Exception as e:
                await db.rollback()
                logger.error(f"{self.source_name}: DB save failed: {e}")
                raise

        return saved

    async def run(self, db: AsyncSession) -> List[IngestedItem]:
        """Run ingestion with error handling and retry logic."""
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"{self.source_name}: ingestion attempt {attempt}/{max_retries}")
                items = await self.ingest()
                saved = await self.save_to_db(items, db)
                logger.info(f"{self.source_name}: completed, {len(saved)} items saved")
                return saved
            except Exception as e:
                last_error = e
                logger.warning(f"{self.source_name}: attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # exponential backoff

        logger.error(f"{self.source_name}: all {max_retries} attempts failed. Last error: {last_error}")
        return []
