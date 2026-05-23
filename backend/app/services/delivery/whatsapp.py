"""Gupshup BSP WhatsApp delivery service."""
import logging
from typing import List, Dict, Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GUPSHUP_API_BASE = "https://api.gupshup.io/sm/api/v1"

SEVERITY_EMOJI = {
    "urgent": "🚨",
    "watch": "👀",
    "opportunity": "✅",
}


async def send_message(to_number: str, message: str) -> bool:
    """
    Send a plain text WhatsApp message via Gupshup BSP.
    Returns True if successful, False otherwise.
    """
    if not settings.GUPSHUP_API_KEY:
        logger.warning(f"WhatsApp: No API key configured, skipping message to {to_number}")
        return False

    # Normalize phone number
    to_number = to_number.replace("+", "").replace("-", "").replace(" ", "")
    if not to_number.startswith("91") and len(to_number) == 10:
        to_number = f"91{to_number}"

    payload = {
        "channel": "whatsapp",
        "source": settings.GUPSHUP_SOURCE_NUMBER,
        "destination": to_number,
        "src.name": settings.GUPSHUP_APP_NAME,
        "message": {
            "type": "text",
            "text": message[:4096],  # WhatsApp message limit
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{GUPSHUP_API_BASE}/msg",
                json=payload,
                headers={
                    "apikey": settings.GUPSHUP_API_KEY,
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            result = response.json()

            if result.get("status") == "submitted":
                logger.info(f"WhatsApp: Message sent to {to_number}")
                return True
            else:
                logger.warning(f"WhatsApp: Unexpected response: {result}")
                return False

    except httpx.HTTPStatusError as e:
        logger.error(f"WhatsApp: HTTP error sending to {to_number}: {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"WhatsApp: Error sending message to {to_number}: {e}")
        return False


async def send_template(
    to_number: str,
    template_name: str,
    params: List[str],
    language_code: str = "en",
) -> bool:
    """
    Send a template WhatsApp message via Gupshup BSP.
    Returns True if successful, False otherwise.
    """
    if not settings.GUPSHUP_API_KEY:
        logger.warning(f"WhatsApp: No API key configured, skipping template to {to_number}")
        return False

    to_number = to_number.replace("+", "").replace("-", "").replace(" ", "")
    if not to_number.startswith("91") and len(to_number) == 10:
        to_number = f"91{to_number}"

    payload = {
        "channel": "whatsapp",
        "source": settings.GUPSHUP_SOURCE_NUMBER,
        "destination": to_number,
        "src.name": settings.GUPSHUP_APP_NAME,
        "message": {
            "type": "template",
            "template": {
                "id": template_name,
                "params": params,
                "language": {"policy": "deterministic", "code": language_code},
            }
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{GUPSHUP_API_BASE}/msg",
                json=payload,
                headers={
                    "apikey": settings.GUPSHUP_API_KEY,
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            logger.info(f"WhatsApp: Template '{template_name}' sent to {to_number}")
            return True

    except Exception as e:
        logger.error(f"WhatsApp: Error sending template to {to_number}: {e}")
        return False


def format_weekly_digest(
    customer_name: str,
    intelligence_items: List[Dict[str, Any]],
) -> str:
    """Format a weekly digest message for WhatsApp."""
    urgent = [i for i in intelligence_items if i.get("severity") == "urgent"]
    watch = [i for i in intelligence_items if i.get("severity") == "watch"]
    opportunities = [i for i in intelligence_items if i.get("severity") == "opportunity"]

    lines = [
        f"*TradingIntel Weekly Brief* 📊",
        f"Hi {customer_name}! Here's your weekly trade intelligence update:\n",
    ]

    if urgent:
        lines.append(f"*🚨 URGENT ALERTS ({len(urgent)})*")
        for item in urgent[:3]:
            lines.append(f"• *{item['title'][:80]}*")
            lines.append(f"  {item['summary'][:150]}")
            if item.get("action_text"):
                lines.append(f"  _Action: {item['action_text'][:100]}_")
            lines.append("")

    if watch:
        lines.append(f"*👀 WATCH LIST ({len(watch)})*")
        for item in watch[:3]:
            lines.append(f"• *{item['title'][:80]}*")
            lines.append(f"  {item['summary'][:120]}")
            lines.append("")

    if opportunities:
        lines.append(f"*✅ OPPORTUNITIES ({len(opportunities)})*")
        for item in opportunities[:2]:
            lines.append(f"• *{item['title'][:80]}*")
            lines.append(f"  {item['summary'][:120]}")
            lines.append("")

    if not intelligence_items:
        lines.append("No new trade updates this week. Markets are stable.")

    lines.append("—")
    lines.append("Reply *CHECK HSN [code] TO [country]* for pre-shipment intelligence")
    lines.append("Reply *HELP* for commands | Reply *STOP* to unsubscribe")

    return "\n".join(lines)


def format_urgent_alert(intelligence_item: Dict[str, Any]) -> str:
    """Format an urgent alert message for WhatsApp."""
    severity = intelligence_item.get("severity", "watch")
    emoji = SEVERITY_EMOJI.get(severity, "📢")

    countries = ", ".join(intelligence_item.get("countries", [])[:3]) or "Multiple markets"
    hsn_codes = ", ".join(intelligence_item.get("hsn_codes", [])[:4]) or "Various"

    lines = [
        f"*{emoji} TradingIntel ALERT*",
        f"",
        f"*{intelligence_item.get('title', 'Trade Alert')}*",
        f"",
        f"{intelligence_item.get('summary', '')}",
        f"",
        f"📍 Affected Markets: {countries}",
        f"🏷️ HSN Codes: {hsn_codes}",
        f"",
    ]

    if intelligence_item.get("action_text"):
        lines.append(f"*What to do:*")
        lines.append(f"{intelligence_item['action_text']}")
        lines.append("")

    if intelligence_item.get("source_url"):
        lines.append(f"📎 Source: {intelligence_item['source_url']}")

    lines.append("")
    lines.append("Reply *ACK* to acknowledge | *CHECK [HSN] TO [Country]* for shipment check")

    return "\n".join(lines)


def format_shipment_check_response(check_result: Dict[str, Any], hsn_code: str, dest_country: str) -> str:
    """Format a shipment check result for WhatsApp."""
    tariff = check_result.get("tariff", {})
    documents = check_result.get("documents_required", [])
    fta_eligible = check_result.get("fta_eligible", False)
    duty_estimate = check_result.get("duty_estimate_inr", 0)

    lines = [
        f"*TradingIntel Pre-Shipment Check* 🔍",
        f"",
        f"*HSN {hsn_code} → {dest_country}*",
        f"",
        f"*Tariff Rates:*",
        f"• MFN Rate: {tariff.get('mfn_rate', 'N/A')}",
    ]

    if tariff.get("preferential_rate"):
        lines.append(f"• Preferential: {tariff.get('preferential_rate')}")

    lines.append(f"• Your Rate: *{tariff.get('applicable_rate', 'N/A')}*")

    if duty_estimate:
        lines.append(f"• Est. Duty: ₹{duty_estimate:,.0f}")

    lines.append("")

    if fta_eligible:
        lines.append(f"✅ *FTA ELIGIBLE* - {check_result.get('fta_details', 'Preferential duty available')}")
    else:
        lines.append(f"❌ FTA not applicable for this shipment")

    lines.append("")

    if documents:
        lines.append(f"*Documents Required ({len(documents)}):*")
        for doc in documents[:5]:
            lines.append(f"• {doc}")

    if check_result.get("optimization_tip"):
        lines.append(f"")
        lines.append(f"💡 *Tip:* {check_result['optimization_tip']}")

    lines.append("")
    lines.append("For full report, visit: dashboard.tradingintel.in")

    return "\n".join(lines)
