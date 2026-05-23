"""Pre-shipment intelligence checker using Claude API."""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.models import ShipmentCheck

logger = logging.getLogger(__name__)

SHIPMENT_SYSTEM_PROMPT = """You are an expert trade compliance advisor for Indian textile and apparel exporters.
You provide precise, accurate pre-shipment intelligence including:
- Applicable tariff rates (MFN and preferential under FTAs)
- Duty calculations
- Required documentation
- FTA eligibility assessment
- Port and compliance insights
- Optimization recommendations

Current FTAs India has:
- India-UAE CEPA: duty-free/reduced access for most textile goods (effective May 2022)
- India-UK FTA: significant duty reductions effective July 2025 (0% for most chapters 50-63)
- India-Australia ECTA: progressive duty elimination (effective Dec 2022)
- ASEAN FTA: preferential access to ASEAN markets
- India-Japan CEPA, India-South Korea CEPA

Always provide specific, actionable information. If unsure about exact rates, provide ranges and recommend verification."""


async def check_shipment(
    hsn_code: str,
    dest_country: str,
    quantity: Optional[float] = None,
    value_inr: Optional[float] = None,
    customer_id: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """
    Run a pre-shipment intelligence check using Claude API.
    Saves result to DB and returns structured response.
    """
    if settings.ANTHROPIC_API_KEY:
        result = await _check_with_claude(hsn_code, dest_country, quantity, value_inr)
    else:
        result = _check_with_mock(hsn_code, dest_country, quantity, value_inr)

    # Save to database if session provided
    if db is not None:
        try:
            check = ShipmentCheck(
                id=str(uuid.uuid4()),
                customer_id=customer_id,
                hsn_code=hsn_code,
                dest_country=dest_country,
                quantity=quantity,
                value_inr=value_inr,
                response=result,
                checked_at=datetime.utcnow(),
            )
            db.add(check)
            await db.commit()
            result["check_id"] = check.id
        except Exception as e:
            logger.error(f"Shipment check DB save failed: {e}")
            await db.rollback()

    return result


async def _check_with_claude(
    hsn_code: str,
    dest_country: str,
    quantity: Optional[float],
    value_inr: Optional[float],
) -> Dict[str, Any]:
    """Generate shipment check using Claude API."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    shipment_details = f"HSN Code: {hsn_code}\nDestination: {dest_country}"
    if quantity:
        shipment_details += f"\nQuantity: {quantity:,.0f} units"
    if value_inr:
        shipment_details += f"\nShipment Value: ₹{value_inr:,.2f}"

    prompt = f"""Provide pre-shipment trade intelligence for this Indian export:

{shipment_details}

Return a JSON object with exactly this structure:
{{
  "tariff": {{
    "mfn_rate": "percentage string e.g. 12%",
    "preferential_rate": "e.g. 0% (India-UK FTA) or null",
    "applicable_rate": "the rate that will actually apply",
    "tariff_chapter": "chapter description"
  }},
  "duty_estimate_inr": number or null,
  "documents_required": ["list", "of", "required", "documents"],
  "fta_eligible": true or false,
  "fta_details": "specific FTA and conditions",
  "recent_port_issues": ["any", "known", "issues", "at", "destination", "ports"],
  "optimization_tip": "specific actionable tip to save money or time",
  "compliance_notes": ["any", "compliance", "requirements"],
  "hs_code_chapter": "chapter 50-63 description for this HSN"
}}

Be specific about:
1. The exact MFN tariff rate for {dest_country}
2. Any applicable FTA between India and {dest_country}
3. Documents that are specifically required for {dest_country}
4. Any recent anti-dumping, safeguard, or quota issues

{f'For the duty estimate, calculate based on ₹{value_inr:,.2f} shipment value.' if value_inr else ''}

Return ONLY the JSON object."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=[
                {
                    "type": "text",
                    "text": SHIPMENT_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Clean up potential markdown
        if response_text.startswith("```"):
            parts = response_text.split("```")
            response_text = parts[1] if len(parts) > 1 else parts[0]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        data = json.loads(response_text)

        # Ensure required fields exist
        data.setdefault("tariff", {})
        data["tariff"].setdefault("mfn_rate", "Verify with customs broker")
        data["tariff"].setdefault("applicable_rate", data["tariff"]["mfn_rate"])
        data.setdefault("documents_required", _get_default_documents(dest_country))
        data.setdefault("fta_eligible", False)
        data.setdefault("recent_port_issues", [])
        data.setdefault("optimization_tip", "Verify all documentation before shipment")

        # Calculate duty estimate if not provided
        if value_inr and not data.get("duty_estimate_inr"):
            try:
                rate_str = data["tariff"]["applicable_rate"].replace("%", "").strip()
                rate = float(rate_str)
                data["duty_estimate_inr"] = (rate / 100) * value_inr
            except (ValueError, AttributeError):
                data["duty_estimate_inr"] = None

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Shipment check: JSON parse error: {e}")
        return _check_with_mock(hsn_code, dest_country, quantity, value_inr)
    except anthropic.APIError as e:
        logger.error(f"Shipment check: Anthropic API error: {e}")
        return _check_with_mock(hsn_code, dest_country, quantity, value_inr)
    except Exception as e:
        logger.error(f"Shipment check: Unexpected error: {e}")
        return _check_with_mock(hsn_code, dest_country, quantity, value_inr)


def _check_with_mock(
    hsn_code: str,
    dest_country: str,
    quantity: Optional[float],
    value_inr: Optional[float],
) -> Dict[str, Any]:
    """Generate mock shipment check data when API is not available."""
    country_lower = dest_country.lower()

    # FTA eligibility lookup
    fta_map = {
        "uk": ("India-UK FTA (effective July 2025)", "0%", True),
        "united kingdom": ("India-UK FTA (effective July 2025)", "0%", True),
        "uae": ("India-UAE CEPA (effective May 2022)", "0-5%", True),
        "united arab emirates": ("India-UAE CEPA", "0-5%", True),
        "australia": ("India-Australia ECTA", "0%", True),
        "japan": ("India-Japan CEPA", "0-10%", True),
        "south korea": ("India-South Korea CEPA", "5%", True),
        "asean": ("India-ASEAN FTA", "0-5%", True),
        "malaysia": ("India-ASEAN FTA", "0%", True),
        "thailand": ("India-ASEAN FTA", "0%", True),
    }

    # MFN rates by destination
    mfn_map = {
        "usa": "12%",
        "united states": "12%",
        "eu": "12%",
        "germany": "12%",
        "france": "12%",
        "italy": "12%",
        "uk": "12%",
        "united kingdom": "12%",
        "canada": "18%",
        "australia": "10%",
        "japan": "10.9%",
        "uae": "5%",
    }

    fta_info = fta_map.get(country_lower)
    mfn_rate = mfn_map.get(country_lower, "10-20%")

    if fta_info:
        fta_name, pref_rate, fta_eligible = fta_info
    else:
        fta_name = None
        pref_rate = None
        fta_eligible = False

    applicable_rate = pref_rate if fta_eligible else mfn_rate

    duty_estimate = None
    if value_inr and applicable_rate:
        try:
            rate_val = float(applicable_rate.replace("%", "").split("-")[0])
            duty_estimate = (rate_val / 100) * value_inr
        except ValueError:
            pass

    # HSN chapter detection
    chapter_map = {
        "50": "Silk",
        "51": "Wool and fine animal hair",
        "52": "Cotton",
        "53": "Other vegetable textile fibres",
        "54": "Man-made filaments",
        "55": "Man-made staple fibres",
        "56": "Wadding, felt and nonwovens",
        "57": "Carpets and other textile floor coverings",
        "58": "Special woven fabrics",
        "59": "Impregnated, coated textile fabrics",
        "60": "Knitted or crocheted fabrics",
        "61": "Knitted or crocheted clothing",
        "62": "Not knitted/crocheted clothing",
        "63": "Other made-up textile articles",
    }
    chapter = hsn_code[:2] if len(hsn_code) >= 2 else "62"
    chapter_desc = chapter_map.get(chapter, "Textile products")

    return {
        "tariff": {
            "mfn_rate": mfn_rate,
            "preferential_rate": f"{pref_rate} ({fta_name})" if fta_eligible else None,
            "applicable_rate": applicable_rate,
            "tariff_chapter": f"Chapter {chapter} - {chapter_desc}",
        },
        "duty_estimate_inr": duty_estimate,
        "documents_required": _get_default_documents(dest_country),
        "fta_eligible": fta_eligible,
        "fta_details": f"{fta_name} - duty-free/preferential access for qualifying Indian goods. Certificate of Origin required." if fta_eligible else f"No FTA between India and {dest_country}. MFN rates apply.",
        "recent_port_issues": [],
        "optimization_tip": (
            f"Claim {fta_name} benefits by obtaining Certificate of Origin from your local Export Promotion Council. "
            f"This could save you {mfn_rate} in import duties."
        ) if fta_eligible else (
            f"Consider restructuring shipment to qualify for GSP benefits if available. "
            f"Ensure HSN classification is optimized for {dest_country} tariff schedule."
        ),
        "compliance_notes": [
            f"Minimum value addition of 35-40% required for FTA benefits",
            f"BIS/Quality certificates may be required for certain product categories",
            f"DGFT Export License required for controlled goods",
        ],
        "hs_code_chapter": f"Chapter {chapter} - {chapter_desc}",
        "note": "This is an estimate. Verify with your customs broker before shipment."
    }


def _get_default_documents(dest_country: str) -> list:
    """Get default required documents for a destination country."""
    base_docs = [
        "Commercial Invoice",
        "Packing List",
        "Bill of Lading / Airway Bill",
        "Certificate of Origin",
        "GSTIN Declaration",
        "Shipping Bill",
    ]

    country_lower = dest_country.lower()

    if country_lower in ["usa", "united states"]:
        base_docs += ["ISF (Importer Security Filing)", "FDA Prior Notice (if applicable)"]
    elif country_lower in ["eu", "germany", "france", "italy", "uk"]:
        base_docs += ["EUR.1 Movement Certificate", "Export Health Certificate (if applicable)"]
    elif country_lower in ["uae", "united arab emirates"]:
        base_docs += ["Certificate of Origin (DGFT)", "Trade License of Importer"]
    elif country_lower == "australia":
        base_docs += ["AIFTA Certificate of Origin", "Fumigation Certificate"]
    elif country_lower == "japan":
        base_docs += ["Japan CEPA Certificate of Origin", "JIS Standard Compliance (if applicable)"]

    return base_docs
