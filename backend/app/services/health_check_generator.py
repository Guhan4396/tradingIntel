"""Health check report generator using Claude API."""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

HEALTH_CHECK_SYSTEM_PROMPT = """You are an expert trade intelligence analyst specializing in Indian exports.
You generate personalized Export Health Check reports for Indian textile and apparel exporters.
Your reports identify:
1. Current tariff exposure and risks
2. FTA benefits being missed
3. Upcoming regulatory risks
4. Market opportunities

Make reports specific, data-driven, and actionable. Use realistic figures for Indian textile exporters.
Be specific about:
- Dollar and rupee amounts
- Specific HS codes
- Specific market opportunities
- Named FTAs and schemes

The tone should be professional but alarming enough to drive action - help them understand the real cost
of not having trade intelligence."""


async def generate_health_check(
    name: str,
    company: str,
    products_exported: str,
    top_markets: str,
    turnover_range: str,
) -> Dict[str, Any]:
    """
    Generate personalized Export Health Check report using Claude API.
    Returns structured report data.
    """
    if settings.ANTHROPIC_API_KEY:
        return await _generate_with_claude(name, company, products_exported, top_markets, turnover_range)
    else:
        return _generate_mock_report(name, company, products_exported, top_markets, turnover_range)


async def _generate_with_claude(
    name: str,
    company: str,
    products_exported: str,
    top_markets: str,
    turnover_range: str,
) -> Dict[str, Any]:
    """Generate health check using Claude API."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"""Generate a personalized Export Health Check report for this Indian exporter:

Name: {name}
Company: {company}
Products Exported: {products_exported}
Top Markets: {top_markets}
Annual Turnover: {turnover_range}

Return a JSON object with exactly this structure:
{{
  "hero_metric": {{
    "potential_loss_min_lakhs": number,
    "potential_loss_max_lakhs": number,
    "primary_risk_description": "one-line description"
  }},
  "tariff_exposure": {{
    "title": "section title",
    "severity": "urgent|watch|opportunity",
    "items": [
      {{
        "risk": "specific risk description",
        "impact": "financial/operational impact",
        "markets_affected": ["list", "of", "markets"],
        "hsn_codes": ["relevant", "HSN", "codes"],
        "urgency": "urgent|watch|low"
      }}
    ]
  }},
  "fta_benefits_missed": {{
    "title": "section title",
    "annual_savings_min_lakhs": number,
    "annual_savings_max_lakhs": number,
    "items": [
      {{
        "fta_name": "name of FTA or scheme",
        "benefit": "specific benefit description",
        "eligibility": "how to qualify",
        "markets": ["applicable", "markets"],
        "savings_estimate": "estimated savings"
      }}
    ]
  }},
  "upcoming_risks": {{
    "title": "section title",
    "items": [
      {{
        "risk": "risk description",
        "timeline": "when this hits",
        "impact_level": "high|medium|low",
        "affected_products": "description"
      }}
    ]
  }},
  "market_opportunities": {{
    "title": "section title",
    "items": [
      {{
        "market": "country or region",
        "opportunity": "specific opportunity",
        "potential_revenue_lakhs": number,
        "timeframe": "when to act",
        "action_required": "what to do"
      }}
    ]
  }},
  "summary_metrics": {{
    "tariff_risks_count": number,
    "fta_opportunities_count": number,
    "upcoming_risks_count": number,
    "market_opportunities_count": number
  }}
}}

Make all figures realistic for a company with {turnover_range} turnover.
Focus on {products_exported} exported to {top_markets}.
Return ONLY the JSON object."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=[
                {
                    "type": "text",
                    "text": HEALTH_CHECK_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        if response_text.startswith("```"):
            parts = response_text.split("```")
            response_text = parts[1] if len(parts) > 1 else parts[0]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        data = json.loads(response_text)
        data["generated_at"] = datetime.utcnow().isoformat()
        data["company"] = company
        data["name"] = name
        return data

    except (json.JSONDecodeError, anthropic.APIError, Exception) as e:
        logger.error(f"Health check generation error: {e}")
        return _generate_mock_report(name, company, products_exported, top_markets, turnover_range)


def _generate_mock_report(
    name: str,
    company: str,
    products_exported: str,
    top_markets: str,
    turnover_range: str,
) -> Dict[str, Any]:
    """Generate mock health check report when API unavailable."""
    # Parse turnover to estimate loss ranges
    turnover_multipliers = {
        "<5 Cr": (5, 15),
        "5-50 Cr": (20, 60),
        "50-500 Cr": (50, 150),
        "500 Cr+": (200, 500),
    }
    loss_range = turnover_multipliers.get(turnover_range, (20, 60))

    markets_list = [m.strip() for m in top_markets.split(",")]
    primary_market = markets_list[0] if markets_list else "USA"

    return {
        "hero_metric": {
            "potential_loss_min_lakhs": loss_range[0],
            "potential_loss_max_lakhs": loss_range[1],
            "primary_risk_description": f"You may be paying excess duties and missing FTA benefits on exports to {primary_market}"
        },
        "tariff_exposure": {
            "title": "Current Tariff Risk Exposure",
            "severity": "urgent",
            "items": [
                {
                    "risk": f"Section 301 tariffs on {products_exported} exports to USA remain elevated at 12-25%",
                    "impact": f"₹{loss_range[0]//2}-{loss_range[1]//2} lakh annual additional cost vs pre-2018 rates",
                    "markets_affected": ["USA"],
                    "hsn_codes": ["6101", "6201", "6211", "6212"],
                    "urgency": "urgent"
                },
                {
                    "risk": "EU anti-dumping investigation on similar products from competing countries could shift buyer attention",
                    "impact": "Potential 20-30% demand increase from EU buyers if competitors face duties",
                    "markets_affected": ["EU", "Germany", "France"],
                    "hsn_codes": ["6201", "6202", "6203", "6204"],
                    "urgency": "watch"
                },
                {
                    "risk": "UK post-Brexit tariff schedule review pending for HS chapters 61-62",
                    "impact": "Potential duty increase from 0% to 12% if India-UK FTA benefits not claimed",
                    "markets_affected": ["UK"],
                    "hsn_codes": ["6101", "6102", "6201", "6202"],
                    "urgency": "urgent"
                }
            ]
        },
        "fta_benefits_missed": {
            "title": "FTA Benefits You May Not Be Claiming",
            "annual_savings_min_lakhs": loss_range[0] // 3,
            "annual_savings_max_lakhs": loss_range[1] // 2,
            "items": [
                {
                    "fta_name": "India-UK Free Trade Agreement",
                    "benefit": "0% import duty on most textile chapters 50-63 vs MFN rate of 12%",
                    "eligibility": "Obtain Certificate of Origin, meet 35% value addition requirement",
                    "markets": ["UK"],
                    "savings_estimate": f"₹{loss_range[0]//4}-{loss_range[1]//4} lakh annually"
                },
                {
                    "fta_name": "India-UAE CEPA",
                    "benefit": "0-5% duty vs standard 5% on textile goods, plus simplified customs",
                    "eligibility": "Form I Certificate of Origin from DGFT/EPCs",
                    "markets": ["UAE"],
                    "savings_estimate": f"₹{loss_range[0]//6}-{loss_range[1]//5} lakh annually"
                },
                {
                    "fta_name": "RoDTEP Scheme",
                    "benefit": f"3.8-4.2% refund on {products_exported} exports",
                    "eligibility": "Automatic for eligible exporters - file shipping bill with RoDTEP declaration",
                    "markets": ["All export markets"],
                    "savings_estimate": f"₹{loss_range[0]//5}-{loss_range[1]//4} lakh annually"
                },
                {
                    "fta_name": "India-Australia ECTA",
                    "benefit": "Preferential access with progressive duty elimination to 0% by 2026",
                    "eligibility": "Certificate of Origin, 35% value addition",
                    "markets": ["Australia"],
                    "savings_estimate": f"₹{loss_range[0]//8}-{loss_range[1]//6} lakh annually"
                }
            ]
        },
        "upcoming_risks": {
            "title": "Upcoming Regulatory Risks (Next 90 Days)",
            "items": [
                {
                    "risk": "US Section 301 tariff exclusion review - textile products currently at 12.5%",
                    "timeline": "Decision expected Q3 2026",
                    "impact_level": "high",
                    "affected_products": f"Most {products_exported} products exported to USA"
                },
                {
                    "risk": "EU Carbon Border Adjustment Mechanism (CBAM) expanding to textile sector",
                    "timeline": "Phased implementation 2026-2034",
                    "impact_level": "medium",
                    "affected_products": "All synthetic fabric and garment exports to EU"
                },
                {
                    "risk": "UK REACH compliance requirements for chemical treatments in garments",
                    "timeline": "New enforcement from January 2026",
                    "impact_level": "medium",
                    "affected_products": "Treated fabrics, dyed garments, flame-retardant textiles"
                },
                {
                    "risk": "India's updated RoDTEP rates notification pending - rates may change",
                    "timeline": "Expected notification in 30-60 days",
                    "impact_level": "medium",
                    "affected_products": f"All exported {products_exported}"
                }
            ]
        },
        "market_opportunities": {
            "title": "Untapped Market Opportunities",
            "items": [
                {
                    "market": "Australia",
                    "opportunity": "India-Australia ECTA making Indian textiles 10-15% cheaper than Chinese alternatives",
                    "potential_revenue_lakhs": loss_range[1] // 2,
                    "timeframe": "Act in next 3-6 months for best positioning",
                    "action_required": "Register with AEPC, obtain ECTA Certificate of Origin, contact Australian importers via India Australia Business Council"
                },
                {
                    "market": "UK",
                    "opportunity": "Post-Brexit UK buyers actively seeking India supply chain alternatives, 0% duty under India-UK FTA",
                    "potential_revenue_lakhs": loss_range[1] // 3,
                    "timeframe": "FTA fully effective - immediate opportunity",
                    "action_required": "Obtain India-UK FTA Certificate of Origin, list on UK trade platforms, contact UKIBC for buyer introductions"
                },
                {
                    "market": "Canada",
                    "opportunity": "India-Canada CEPA negotiations advancing - early mover advantage for Indian exporters",
                    "potential_revenue_lakhs": loss_range[0] // 2,
                    "timeframe": "6-12 months ahead of agreement",
                    "action_required": "Build buyer relationships now before competition increases post-FTA"
                }
            ]
        },
        "summary_metrics": {
            "tariff_risks_count": 3,
            "fta_opportunities_count": 4,
            "upcoming_risks_count": 4,
            "market_opportunities_count": 3
        },
        "generated_at": datetime.utcnow().isoformat(),
        "company": company,
        "name": name,
    }
