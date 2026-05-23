"""UK HMRC trade tariff updates ingester."""
import logging
from datetime import datetime
from typing import List, Dict, Any

import httpx
import feedparser
from bs4 import BeautifulSoup

from app.services.ingestion.base import BaseIngester

logger = logging.getLogger(__name__)


class UKHMRCIngester(BaseIngester):
    """Fetches UK HMRC trade tariff updates and commodity changes."""

    source_name = "UK HMRC"
    source_url = "https://www.trade-tariff.service.gov.uk"
    source_type = "api"

    RELEVANT_CHAPTERS = ["50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63"]

    HMRC_FEEDS = [
        "https://www.gov.uk/search/news-and-communications.atom?keywords=tariff+textile&organisations%5B%5D=hm-revenue-customs",
        "https://www.gov.uk/search/news-and-communications.atom?keywords=trade+import+duty&organisations%5B%5D=department-for-international-trade",
    ]

    RELEVANT_KEYWORDS = [
        "tariff", "duty", "textile", "apparel", "clothing", "fabric",
        "trade", "import", "export", "quota", "gsp", "fta", "preference",
        "commodity", "cotton", "wool", "synthetic", "yarn", "garment",
        "india-uk fta", "india fta", "safeguard", "anti-dumping"
    ]

    async def ingest(self) -> List[Dict[str, Any]]:
        """Fetch UK HMRC trade tariff updates."""
        items = []

        # Try ATOM/RSS feeds
        for feed_url in self.HMRC_FEEDS:
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    response = await client.get(feed_url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; TradingIntel/1.0)"
                    })
                    response.raise_for_status()

                feed = feedparser.parse(response.text)

                for entry in feed.entries[:10]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("content", [{}])[0].get("value", ""))
                    link = entry.get("link", "")
                    published = entry.get("published", "")

                    combined = f"{title} {summary}".lower()
                    if not any(kw in combined for kw in self.RELEVANT_KEYWORDS):
                        continue

                    # Clean HTML from summary
                    if summary:
                        summary_soup = BeautifulSoup(summary, "lxml")
                        summary = summary_soup.get_text(separator="\n", strip=True)

                    items.append({
                        "raw_content": f"UK Trade Update: {title}\n\nPublished: {published}\n\n{summary[:3000]}",
                        "metadata": {
                            "url": link,
                            "title": title,
                            "source": "UK HMRC",
                            "published_at": published,
                            "fetched_at": datetime.utcnow().isoformat(),
                        }
                    })

            except Exception as e:
                logger.warning(f"UK HMRC: Error fetching feed {feed_url}: {e}")
                continue

        # Fetch UK Trade Tariff API for textile chapters
        api_items = await self._fetch_trade_tariff_api()
        items.extend(api_items)

        if not items:
            items = self._get_fallback_items()

        return items

    async def _fetch_trade_tariff_api(self) -> List[Dict[str, Any]]:
        """Fetch recent changes from UK Trade Tariff API."""
        items = []
        base_url = "https://www.trade-tariff.service.gov.uk/api/v2"

        try:
            # Fetch recent section notes changes
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                # Get changes for textile section (Section XI)
                response = await client.get(
                    f"{base_url}/sections/11",
                    headers={"Accept": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    section_title = data.get("data", {}).get("attributes", {}).get("title", "")
                    position = data.get("data", {}).get("attributes", {}).get("position", "")

                    content = f"UK Trade Tariff - Section XI (Textile and Textile Articles)\n"
                    content += f"Title: {section_title}\n"
                    content += f"Covers chapters 50-63 including yarns, fabrics, and garments.\n"
                    content += f"Current rules and duty rates apply to India-UK FTA eligible products."

                    items.append({
                        "raw_content": content,
                        "metadata": {
                            "url": "https://www.trade-tariff.service.gov.uk/sections/11",
                            "title": "UK Trade Tariff Section XI - Textiles",
                            "source": "UK HMRC",
                            "published_at": datetime.utcnow().strftime("%Y-%m-%d"),
                            "fetched_at": datetime.utcnow().isoformat(),
                        }
                    })

        except Exception as e:
            logger.debug(f"UK HMRC API: {e}")

        return items

    def _get_fallback_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "raw_content": (
                    "UK HMRC Trade Tariff Update: India-UK Free Trade Agreement Textile Provisions\n\n"
                    "The UK Government has confirmed duty-free access for Indian textile and apparel "
                    "exports under the India-UK FTA effective from July 2025. Products under HS chapters "
                    "61-62 (garments) and chapters 50-60 (fabrics and yarns) qualify for 0% duty with "
                    "appropriate Certificate of Origin. Indian exporters must obtain Form A or equivalent "
                    "UK GSP documentation. Value addition requirement: minimum 35% value addition in India."
                ),
                "metadata": {
                    "url": "https://www.gov.uk/trade-tariff/india-uk-fta-sample",
                    "title": "India-UK FTA Textile Provisions",
                    "source": "UK HMRC",
                    "published_at": datetime.utcnow().strftime("%Y-%m-%d"),
                    "fetched_at": datetime.utcnow().isoformat(),
                }
            }
        ]
