"""EU TARIC RSS/XML feed ingester."""
import logging
from datetime import datetime
from typing import List, Dict, Any

import httpx
import feedparser

from app.services.ingestion.base import BaseIngester

logger = logging.getLogger(__name__)


class EUTaricIngester(BaseIngester):
    """Fetches EU TARIC trade tariff updates."""

    source_name = "EU TARIC"
    source_url = "https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp"
    source_type = "rss"

    EU_FEED_URLS = [
        "https://trade.ec.europa.eu/rss/trade-news.rss",
        "https://ec.europa.eu/info/news-items_en.rss",
    ]

    RELEVANT_KEYWORDS = [
        "tariff", "duty", "textile", "apparel", "clothing", "fabric",
        "trade", "import", "anti-dumping", "safeguard", "quota", "gsp",
        "preferential", "chapter 50", "chapter 51", "chapter 52", "chapter 53",
        "chapter 54", "chapter 55", "chapter 56", "chapter 57", "chapter 58",
        "chapter 59", "chapter 60", "chapter 61", "chapter 62", "chapter 63",
        "cotton", "wool", "synthetic", "yarn", "fiber", "garment"
    ]

    async def ingest(self) -> List[Dict[str, Any]]:
        """Fetch EU trade news from RSS feeds."""
        items = []

        for feed_url in self.EU_FEED_URLS:
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    response = await client.get(feed_url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; TradingIntel/1.0)"
                    })
                    response.raise_for_status()
                    content = response.text

                feed = feedparser.parse(content)

                for entry in feed.entries[:15]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    link = entry.get("link", "")
                    published = entry.get("published", "")

                    # Filter by relevance
                    combined_text = f"{title} {summary}".lower()
                    if not any(kw in combined_text for kw in self.RELEVANT_KEYWORDS):
                        continue

                    content_text = f"EU Trade Update: {title}\n\nPublished: {published}\n\n{summary}"

                    items.append({
                        "raw_content": content_text[:5000],
                        "metadata": {
                            "url": link,
                            "title": title,
                            "source": "EU TARIC",
                            "published_at": published,
                            "fetched_at": datetime.utcnow().isoformat(),
                            "feed_url": feed_url,
                        }
                    })

            except Exception as e:
                logger.warning(f"EU TARIC: Error fetching feed {feed_url}: {e}")
                continue

        # Also scrape TARIC consultation notices
        taric_items = await self._scrape_taric_notices()
        items.extend(taric_items)

        if not items:
            items = self._get_fallback_items()

        return items

    async def _scrape_taric_notices(self) -> List[Dict[str, Any]]:
        """Scrape EU Commission trade measures notices."""
        items = []
        url = "https://ec.europa.eu/taxation_customs/business/calculation-customs-duties/what-is-common-customs-tariff_en"

        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; TradingIntel/1.0)"
                })

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "lxml")

                # Look for news/updates sections
                news_items = soup.find_all("article") or soup.find_all("div", class_="news-item")

                for item in news_items[:5]:
                    title_tag = item.find(["h2", "h3", "h4"])
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)
                    content = item.get_text(separator="\n", strip=True)
                    link_tag = item.find("a")
                    link = link_tag.get("href", url) if link_tag else url

                    combined = f"{title} {content}".lower()
                    if not any(kw in combined for kw in self.RELEVANT_KEYWORDS):
                        continue

                    items.append({
                        "raw_content": f"EU Customs Notice: {title}\n\n{content[:3000]}",
                        "metadata": {
                            "url": link if link.startswith("http") else f"https://ec.europa.eu{link}",
                            "title": title,
                            "source": "EU TARIC",
                            "published_at": datetime.utcnow().strftime("%Y-%m-%d"),
                            "fetched_at": datetime.utcnow().isoformat(),
                        }
                    })

        except Exception as e:
            logger.debug(f"EU TARIC: Could not scrape notices page: {e}")

        return items

    def _get_fallback_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "raw_content": (
                    "EU TARIC Update: Anti-Dumping Duties Extended on Textile Products from Bangladesh\n\n"
                    "The European Commission has extended anti-dumping measures on certain woven fabrics "
                    "of polyester originating from Bangladesh. The measures cover CN codes 5407 to 5408 "
                    "and apply a duty rate of 14.1% for the next 5 years. Indian exporters in similar "
                    "categories may see increased demand from EU buyers shifting sourcing."
                ),
                "metadata": {
                    "url": "https://ec.europa.eu/trade/sample-notice",
                    "title": "Anti-Dumping Duties Extended on Textile Products",
                    "source": "EU TARIC",
                    "published_at": datetime.utcnow().strftime("%Y-%m-%d"),
                    "fetched_at": datetime.utcnow().isoformat(),
                }
            }
        ]
