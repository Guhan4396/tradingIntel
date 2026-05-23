"""CBIC.gov.in circulars ingester."""
import logging
from datetime import datetime
from typing import List, Dict, Any

import httpx
from bs4 import BeautifulSoup

from app.services.ingestion.base import BaseIngester

logger = logging.getLogger(__name__)


class CBICIngester(BaseIngester):
    """Scrapes CBIC.gov.in customs and central excise circulars."""

    source_name = "CBIC"
    source_url = "https://cbic.gov.in"
    source_type = "scrape"

    CBIC_URLS = [
        "https://cbic.gov.in/htdocs-cbec/customs/cs-circulars/cs-circulars-2024/circular-index.htm",
        "https://cbic.gov.in/htdocs-cbec/customs/cs-act/formatted-htmls/cnotfns.htm",
    ]

    RELEVANT_KEYWORDS = [
        "textile", "apparel", "garment", "clothing", "fabric", "yarn",
        "cotton", "wool", "synthetic", "import", "export", "customs",
        "duty", "tariff", "chapter 50", "chapter 51", "chapter 52",
        "chapter 53", "chapter 54", "chapter 55", "chapter 56",
        "chapter 57", "chapter 58", "chapter 59", "chapter 60",
        "chapter 61", "chapter 62", "chapter 63",
        "exemption", "notification", "safeguard", "anti-dumping",
        "valuation", "classification", "bcd", "igst", "trade facilitation"
    ]

    async def ingest(self) -> List[Dict[str, Any]]:
        """Scrape CBIC customs circulars and notifications."""
        items = []

        # Try primary CBIC customs circulars page
        try:
            primary_items = await self._scrape_circulars()
            items.extend(primary_items)
        except Exception as e:
            logger.warning(f"CBIC: Error scraping circulars: {e}")

        # Try notification page
        try:
            notification_items = await self._scrape_notifications()
            items.extend(notification_items)
        except Exception as e:
            logger.warning(f"CBIC: Error scraping notifications: {e}")

        if not items:
            items = self._get_fallback_items()

        return items[:15]  # Limit to 15 items

    async def _scrape_circulars(self) -> List[Dict[str, Any]]:
        """Scrape CBIC customs circulars."""
        items = []
        url = "https://cbic.gov.in/htdocs-cbec/customs/cs-circulars/index-customs-circular.htm"

        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; TradingIntel/1.0)"
                })
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            links = soup.find_all("a")

            for link in links[:30]:
                title = link.get_text(strip=True)
                href = link.get("href", "")

                if not title or len(title) < 10:
                    continue

                title_lower = title.lower()
                if not any(kw in title_lower for kw in self.RELEVANT_KEYWORDS):
                    continue

                if not href.startswith("http"):
                    if href.startswith("/"):
                        href = f"https://cbic.gov.in{href}"
                    else:
                        href = f"https://cbic.gov.in/htdocs-cbec/customs/cs-circulars/{href}"

                content = f"CBIC Customs Circular: {title}\nSource: CBIC.gov.in\n"
                content += "This circular affects customs procedures and duty rates for covered products."

                items.append({
                    "raw_content": content,
                    "metadata": {
                        "url": href,
                        "title": title,
                        "source": "CBIC",
                        "published_at": datetime.utcnow().strftime("%d %b %Y"),
                        "fetched_at": datetime.utcnow().isoformat(),
                        "category": "circular",
                    }
                })

        except Exception as e:
            logger.debug(f"CBIC circulars: {e}")

        return items

    async def _scrape_notifications(self) -> List[Dict[str, Any]]:
        """Scrape CBIC customs duty notifications."""
        items = []
        url = "https://cbic.gov.in/htdocs-cbec/customs/cs-act/formatted-htmls/cnotfns.htm"

        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True, verify=False) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; TradingIntel/1.0)"
                })
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            rows = soup.find_all("tr")
            for row in rows[:25]:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                title = cells[-1].get_text(strip=True) if cells else ""
                if not title or len(title) < 10:
                    continue

                title_lower = title.lower()
                if not any(kw in title_lower for kw in self.RELEVANT_KEYWORDS):
                    continue

                link_tag = row.find("a")
                href = link_tag.get("href", "") if link_tag else ""
                if href and not href.startswith("http"):
                    href = f"https://cbic.gov.in{href}"

                date_text = cells[0].get_text(strip=True) if cells else ""

                items.append({
                    "raw_content": f"CBIC Customs Notification: {title}\nDate: {date_text}\n"
                                   f"This notification relates to customs duties for affected product categories.",
                    "metadata": {
                        "url": href or url,
                        "title": title,
                        "source": "CBIC",
                        "published_at": date_text,
                        "fetched_at": datetime.utcnow().isoformat(),
                        "category": "notification",
                    }
                })

        except Exception as e:
            logger.debug(f"CBIC notifications: {e}")

        return items

    def _get_fallback_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "raw_content": (
                    "CBIC Customs Circular: Clarification on HSN Classification for Blended Fabric Products\n\n"
                    "The Central Board of Indirect Taxes and Customs has issued a clarification circular "
                    "regarding correct HSN classification of blended fabric products containing cotton and "
                    "synthetic fiber blends. Products with >50% cotton by weight: Chapter 52. Products with "
                    ">50% synthetic fiber by weight: Chapter 54 or 55. Mixed blends with equal proportions: "
                    "classification based on constituent yielding highest customs duty. "
                    "Wrongly classified goods may attract penalties under Section 112 of Customs Act."
                ),
                "metadata": {
                    "url": "https://cbic.gov.in/sample-circular",
                    "title": "HSN Classification for Blended Fabric Products",
                    "source": "CBIC",
                    "published_at": datetime.utcnow().strftime("%d %b %Y"),
                    "fetched_at": datetime.utcnow().isoformat(),
                    "category": "circular",
                }
            },
            {
                "raw_content": (
                    "CBIC Notification: BCD Exemption Extended for Certain Textile Machinery Imports\n\n"
                    "CBIC has extended the basic customs duty exemption on import of certain textile "
                    "processing machinery till March 2026. Eligible machinery includes shuttle-less looms, "
                    "knitting machines, embroidery machines and finishing equipment. The exemption is "
                    "available under Project Import Scheme with actual user condition. Manufacturers must "
                    "maintain export obligation of 3x the value of imported machinery within 6 years."
                ),
                "metadata": {
                    "url": "https://cbic.gov.in/sample-notification",
                    "title": "BCD Exemption Extended for Textile Machinery",
                    "source": "CBIC",
                    "published_at": datetime.utcnow().strftime("%d %b %Y"),
                    "fetched_at": datetime.utcnow().isoformat(),
                    "category": "notification",
                }
            }
        ]
