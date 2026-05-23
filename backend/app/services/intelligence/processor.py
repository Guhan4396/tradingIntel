"""Intelligence processor using Claude API to extract structured insights from raw content."""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

# System prompt for intelligence extraction - cached for efficiency
SYSTEM_PROMPT = """You are an expert trade intelligence analyst specializing in Indian export markets,
particularly the textile and apparel sector. Your role is to analyze regulatory updates, policy changes,
and market intelligence from global trade sources and extract structured, actionable insights for
Indian exporters.

Context for analysis:
- Primary audience: Indian textile/apparel exporters (SMEs with turnover ₹5 Cr to ₹500 Cr+)
- Key markets: USA, EU, UK, UAE, Canada, Australia, Japan
- Key HSN chapters: 50-63 (textile raw materials through finished garments)
- Key concerns: tariff rates, duty changes, FTA benefits, quota restrictions,
  anti-dumping duties, regulatory compliance, port issues, certification requirements
- Key schemes: RoDTEP, EPCG, Advance Authorization, India-UAE CEPA, India-UK FTA, ASEAN FTA

When analyzing content:
1. Focus on what directly impacts Indian exporters
2. Identify specific HSN codes affected (4-8 digit where possible)
3. Identify specific destination/source countries affected
4. Assess time-sensitivity and business impact
5. Provide clear, actionable recommendations in plain language

Severity classification:
- urgent: Immediate action required (tariff increases effective soon, quota closures, port disruptions)
- watch: Monitor closely (policy reviews in progress, upcoming changes, market shifts)
- opportunity: Business opportunity (new FTAs, reduced duties, market openings, competitor disadvantages)"""


async def process_ingested_item(
    raw_content: str,
    source_name: str = "",
    source_url: str = "",
    ingested_item_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Process a raw ingested item through Claude to extract intelligence.
    Returns structured intelligence data or None if processing fails.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("No Anthropic API key configured, using mock intelligence")
        return _generate_mock_intelligence(raw_content, source_name, source_url, ingested_item_id)

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    user_prompt = f"""Analyze this trade intelligence content and extract structured information:

SOURCE: {source_name}
URL: {source_url}

CONTENT:
{raw_content[:8000]}

Return a JSON object with exactly these fields:
{{
  "title": "Clear, specific title (max 100 chars)",
  "summary": "2-3 sentence summary of what this means for Indian exporters specifically",
  "severity": "urgent|watch|opportunity",
  "hsn_codes": ["list", "of", "affected", "HSN", "codes"],
  "countries": ["list", "of", "affected", "countries"],
  "action_text": "Specific action Indian exporters should take right now",
  "is_relevant": true/false
}}

Rules:
- is_relevant: false if content is completely unrelated to Indian textile/apparel exports
- hsn_codes: use 4-digit codes from chapters 50-63 where applicable, empty array if not applicable
- countries: include both source and destination countries where relevant
- action_text: must be specific and actionable, not generic advice
- summary: must mention India or Indian exporters

Return ONLY the JSON object, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        response_text = response.content[0].text.strip()

        # Parse JSON response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        data = json.loads(response_text)

        if not data.get("is_relevant", True):
            logger.info(f"Item marked as not relevant: {source_name}")
            return None

        return {
            "id": str(uuid.uuid4()),
            "ingested_item_id": ingested_item_id,
            "title": data.get("title", "Trade Update")[:512],
            "summary": data.get("summary", ""),
            "severity": data.get("severity", "watch"),
            "hsn_codes": data.get("hsn_codes", []),
            "countries": data.get("countries", []),
            "action_text": data.get("action_text", ""),
            "source_url": source_url,
            "processed_at": datetime.utcnow(),
            "is_reviewed": False,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.debug(f"Response was: {response_text[:500]}")
        return None
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in intelligence processor: {e}")
        return None


def _generate_mock_intelligence(
    raw_content: str,
    source_name: str,
    source_url: str,
    ingested_item_id: Optional[str],
) -> Dict[str, Any]:
    """Generate mock intelligence data when API is not configured."""
    # Simple heuristic-based classification
    content_lower = raw_content.lower()

    if any(word in content_lower for word in ["urgent", "immediate", "effective immediately", "ban", "closure"]):
        severity = "urgent"
    elif any(word in content_lower for word in ["opportunity", "fta", "benefit", "reduction", "exemption"]):
        severity = "opportunity"
    else:
        severity = "watch"

    # Extract HSN codes from content
    import re
    hsn_codes = list(set(re.findall(r'\b6[0-3]\d{2}\b|\b5[0-9]\d{2}\b', raw_content)))[:5]

    # Extract country mentions
    countries_map = {
        "usa": "USA", "united states": "USA", "america": "USA",
        "eu": "EU", "european union": "EU", "europe": "EU",
        "uk": "UK", "united kingdom": "UK", "britain": "UK",
        "uae": "UAE", "dubai": "UAE",
        "china": "China", "bangladesh": "Bangladesh",
        "india": "India",
    }
    found_countries = []
    for key, value in countries_map.items():
        if key in content_lower and value not in found_countries:
            found_countries.append(value)

    # Generate title from first sentence
    first_line = raw_content.split("\n")[0][:100]
    if len(first_line) < 20:
        first_line = raw_content[:100]

    return {
        "id": str(uuid.uuid4()),
        "ingested_item_id": ingested_item_id,
        "title": first_line.replace("USTR ", "").replace("EU TARIC Update: ", "")
                           .replace("UK Trade Update: ", "").replace("DGFT Notification: ", "")
                           .replace("CBIC Customs Circular: ", "")[:512],
        "summary": f"Trade intelligence from {source_name}. " + raw_content[raw_content.find("\n\n")+2:][:300],
        "severity": severity,
        "hsn_codes": hsn_codes if hsn_codes else ["6101", "6201", "5208"],
        "countries": found_countries if found_countries else ["India"],
        "action_text": "Review this update and assess impact on your export operations. Consult with your customs broker if duty rates or documentation requirements are affected.",
        "source_url": source_url,
        "processed_at": datetime.utcnow(),
        "is_reviewed": False,
    }


async def process_pending_items(db) -> int:
    """Process all pending ingested items through the intelligence processor."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.models import IngestedItem, IntelligenceItem, Source

    result = await db.execute(
        select(IngestedItem)
        .options(selectinload(IngestedItem.source))
        .where(IngestedItem.status == "pending")
        .order_by(IngestedItem.ingested_at.asc())
        .limit(20)  # Process up to 20 at a time
    )
    pending_items = result.scalars().all()

    processed_count = 0

    for ingested_item in pending_items:
        try:
            source_name = ingested_item.source.name if ingested_item.source else "Unknown"
            source_url = ingested_item.metadata.get("url", "") if ingested_item.metadata else ""

            intelligence_data = await process_ingested_item(
                raw_content=ingested_item.raw_content,
                source_name=source_name,
                source_url=source_url,
                ingested_item_id=ingested_item.id,
            )

            if intelligence_data:
                intel_item = IntelligenceItem(
                    id=intelligence_data["id"],
                    ingested_item_id=intelligence_data["ingested_item_id"],
                    title=intelligence_data["title"],
                    summary=intelligence_data["summary"],
                    severity=intelligence_data["severity"],
                    hsn_codes=intelligence_data["hsn_codes"],
                    countries=intelligence_data["countries"],
                    action_text=intelligence_data["action_text"],
                    source_url=intelligence_data["source_url"],
                    processed_at=intelligence_data["processed_at"],
                    is_reviewed=False,
                )
                db.add(intel_item)
                ingested_item.status = "processed"
                processed_count += 1
            else:
                ingested_item.status = "failed"

        except Exception as e:
            logger.error(f"Error processing ingested item {ingested_item.id}: {e}")
            ingested_item.status = "failed"

    if pending_items:
        await db.commit()
        logger.info(f"Processed {processed_count}/{len(pending_items)} ingested items")

    return processed_count
