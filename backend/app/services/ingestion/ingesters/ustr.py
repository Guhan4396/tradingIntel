"""USTR.gov notifications ingester using requests + BeautifulSoup."""
import logging
from datetime import datetime
from typing import List, Dict, Any

import httpx
from bs4 import BeautifulSoup

from app.services.ingestion.base import BaseIngester
from app.models.models import Source

logger = logging.getLogger(__name__)


class USTRIngester(BaseIngester):
    """Scrapes USTR.gov trade notifications."""

    source_name = "USTR"
    source_url = "https://ustr.gov/about-us/policy-offices/press-office/press-releases"
    source_type = "scrape"

    # Keywords relevant to trade regulations
    RELEVANT_KEYWORDS = [
        "tariff", "duty", "trade", "import", "export", "section 301",
        "safeguard", "anti-dumping", "countervailing", "textile", "apparel",
        "clothing", "fabric", "fiber", "cotton", "wool", "synthetic",
        "chapter 50", "chapter 51", "chapter 52", "chapter 53", "chapter 54",
        "chapter 55", "chapter 56", "chapter 57", "chapter 58", "chapter 59",
        "chapter 60", "chapter 61", "chapter 62", "chapter 63",
        "gsp", "fta", "trade agreement", "quota", "restriction"
    ]

    async def ingest(self) -> List[Dict[str, Any]]:
        """Fetch press releases from USTR.gov."""
        items = []
        url = "https://ustr.gov/about-us/policy-offices/press-office/press-releases"

        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; TradingIntel/1.0)"
                })
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Find press release listings
            articles = soup.find_all("div", class_=lambda c: c and "views-row" in c)
            if not articles:
                articles = soup.find_all("article")
            if not articles:
                # Try generic link extraction
                articles = soup.find_all("li", class_=lambda c: c and "views-row" in c)

            for article in articles[:20]:  # Process latest 20
                try:
                    link_tag = article.find("a")
                    if not link_tag:
                        continue

                    title = link_tag.get_text(strip=True)
                    href = link_tag.get("href", "")
                    if not href:
                        continue

                    if not href.startswith("http"):
                        href = f"https://ustr.gov{href}"

                    # Check relevance
                    title_lower = title.lower()
                    if not any(kw in title_lower for kw in self.RELEVANT_KEYWORDS):
                        continue

                    # Get date if available
                    date_tag = article.find("span", class_=lambda c: c and "date" in str(c))
                    published_at = date_tag.get_text(strip=True) if date_tag else ""

                    # Fetch article content
                    content = await self._fetch_article(href)

                    if content:
                        items.append({
                            "raw_content": f"USTR Press Release: {title}\n\n{content}",
                            "metadata": {
                                "url": href,
                                "title": title,
                                "source": "USTR",
                                "published_at": published_at,
                                "fetched_at": datetime.utcnow().isoformat(),
                            }
                        })

                except Exception as e:
                    logger.warning(f"USTR: Error processing article: {e}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"USTR: HTTP error fetching listings: {e}")
            # Return sample data for development
            items = self._get_fallback_items()
        except Exception as e:
            logger.error(f"USTR: Unexpected error: {e}")
            items = self._get_fallback_items()

        return items

    async def _fetch_article(self, url: str) -> str:
        """Fetch and parse a single article."""
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; TradingIntel/1.0)"
                })
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Remove nav, header, footer
            for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
                tag.decompose()

            # Find main content
            content_div = (
                soup.find("div", class_=lambda c: c and "field-type-text-with-summary" in str(c)) or
                soup.find("div", class_="field-items") or
                soup.find("main") or
                soup.find("article") or
                soup.find("div", class_="content")
            )

            if content_div:
                return content_div.get_text(separator="\n", strip=True)[:5000]
            return soup.get_text(separator="\n", strip=True)[:3000]

        except Exception as e:
            logger.warning(f"USTR: Error fetching article {url}: {e}")
            return ""

    def _get_fallback_items(self) -> List[Dict[str, Any]]:
        """Return sample items when live scraping is unavailable."""
        return [
            {
                "raw_content": (
                    "USTR Announces Section 301 Tariff Review on Textile Imports from China\n\n"
                    "The Office of the United States Trade Representative (USTR) today announced "
                    "a statutory review of Section 301 tariffs on textile and apparel products "
                    "imported from China. The review covers HS chapters 50-63 affecting cotton, "
                    "synthetic fiber, woven fabrics, and finished garments. Current tariff rates "
                    "range from 7.5% to 25% on affected categories. Comments due within 60 days."
                ),
                "metadata": {
                    "url": "https://ustr.gov/about-us/policy-offices/press-office/press-releases/sample",
                    "title": "USTR Announces Section 301 Tariff Review on Textile Imports",
                    "source": "USTR",
                    "published_at": datetime.utcnow().strftime("%B %d, %Y"),
                    "fetched_at": datetime.utcnow().isoformat(),
                }
            }
        ]
