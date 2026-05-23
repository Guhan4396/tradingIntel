"""Gupshup WhatsApp webhook router."""
import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.models.models import Customer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Simple conversation state store (production: use Redis)
_conversation_state: Dict[str, Dict] = {}


@router.get("/webhook")
async def verify_webhook(
    challenge: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
):
    """Gupshup webhook verification endpoint."""
    # Gupshup doesn't require challenge-response like Meta
    # Just return 200 to confirm webhook is live
    return {"status": "active", "service": "TradingIntel WhatsApp"}


@router.post("/webhook")
async def handle_incoming_message(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming WhatsApp messages from Gupshup."""
    try:
        body = await request.json()
    except Exception:
        try:
            form = await request.form()
            body = dict(form)
        except Exception:
            return Response(content="ok", status_code=200)

    logger.info(f"WhatsApp webhook received: {str(body)[:200]}")

    # Parse Gupshup webhook format
    try:
        await _process_gupshup_message(body, db)
    except Exception as e:
        logger.error(f"WhatsApp: Error processing message: {e}")

    # Always return 200 to Gupshup
    return Response(content="ok", status_code=200)


async def _process_gupshup_message(payload: Dict[str, Any], db: AsyncSession) -> None:
    """Process a Gupshup incoming message payload."""
    # Gupshup sends messages in this format
    # payload.type = "message"
    # payload.payload.source = sender's phone number
    # payload.payload.payload.text = message text

    msg_type = payload.get("type", "")

    if msg_type != "message":
        logger.debug(f"WhatsApp: Ignoring non-message type: {msg_type}")
        return

    inner_payload = payload.get("payload", {})
    sender_number = inner_payload.get("source", "")
    message_payload = inner_payload.get("payload", {})
    message_text = message_payload.get("text", "").strip()

    if not sender_number or not message_text:
        logger.debug("WhatsApp: Missing sender or message text")
        return

    logger.info(f"WhatsApp: Message from {sender_number}: {message_text[:100]}")

    # Find or create customer by WhatsApp number
    customer = await _get_or_create_customer_by_whatsapp(sender_number, db)

    # Route message based on content
    response_text = await _route_message(message_text, sender_number, customer, db)

    if response_text:
        from app.services.delivery.whatsapp import send_message
        await send_message(sender_number, response_text)


async def _route_message(
    text: str,
    sender_number: str,
    customer: Optional[Customer],
    db: AsyncSession,
) -> Optional[str]:
    """Route incoming message to appropriate handler."""
    text_lower = text.lower().strip()

    # HELP command
    if text_lower in ["help", "hi", "hello", "hey", "start"]:
        return _get_help_message(customer)

    # STOP/UNSUBSCRIBE
    if text_lower in ["stop", "unsubscribe", "cancel"]:
        return "You've been unsubscribed from TradingIntel alerts. Reply START to resubscribe."

    # ACK command - acknowledge latest alert
    if text_lower in ["ack", "acknowledge", "ok", "noted"]:
        return "Alert acknowledged. We'll continue monitoring this situation for you."

    # Pre-shipment check patterns:
    # "check shipment HSN 6101 to USA"
    # "check 6101 USA"
    # "6101 UK"
    shipment_match = re.search(
        r'(?:check\s+(?:shipment\s+)?|shipment\s+)?(?:hsn\s+)?(\d{4,8})\s+(?:to\s+)?([a-z\s]+)',
        text_lower
    )

    if shipment_match or text_lower.startswith("check"):
        return await _handle_shipment_check(text, sender_number, customer, db)

    # Intelligence query: "what about UK tariffs" / "tell me about USA"
    if any(keyword in text_lower for keyword in ["tariff", "duty", "fta", "what about", "tell me"]):
        return await _handle_intelligence_query(text, customer, db)

    # Onboarding flow
    state = _conversation_state.get(sender_number, {})
    if state.get("step") == "collecting_hsn":
        return await _handle_hsn_input(text, sender_number, customer, db)
    if state.get("step") == "collecting_market":
        return await _handle_market_input(text, sender_number, customer, db)

    # Setup/subscribe command
    if text_lower.startswith("setup") or text_lower.startswith("subscribe"):
        _conversation_state[sender_number] = {"step": "collecting_hsn"}
        return (
            "Let's set up your TradingIntel profile!\n\n"
            "Please share your HSN codes (e.g., 6101, 6202, 5208):\n"
            "You can enter up to 5 codes separated by commas."
        )

    # Default: show help
    return _get_help_message(customer)


async def _handle_shipment_check(
    text: str,
    sender_number: str,
    customer: Optional[Customer],
    db: AsyncSession,
) -> str:
    """Handle pre-shipment check request from WhatsApp."""
    # Extract HSN code and destination from message
    text_lower = text.lower()
    hsn_match = re.search(r'\b(\d{4,8})\b', text)
    country_match = re.search(
        r'(?:to\s+)?(usa|uk|uae|eu|australia|japan|canada|germany|france|'
        r'united states|united kingdom|united arab emirates|[a-z]{3,})',
        text_lower
    )

    if not hsn_match:
        return (
            "Please specify the HSN code for your shipment check.\n\n"
            "Format: *CHECK [HSN code] TO [Country]*\n"
            "Example: CHECK 6101 TO UK\n\n"
            "HSN codes are 4-8 digit numbers from your export documentation."
        )

    hsn_code = hsn_match.group(1)
    dest_country = country_match.group(1).title() if country_match else "USA"

    # Map common aliases
    country_map = {
        "Usa": "USA", "United States": "USA",
        "Uk": "UK", "United Kingdom": "UK",
        "Uae": "UAE", "United Arab Emirates": "UAE",
        "Eu": "EU",
    }
    dest_country = country_map.get(dest_country, dest_country)

    customer_id = customer.id if customer else None

    try:
        from app.services.shipment_checker import check_shipment
        from app.services.delivery.whatsapp import format_shipment_check_response

        result = await check_shipment(
            hsn_code=hsn_code,
            dest_country=dest_country,
            customer_id=customer_id,
            db=db,
        )

        return format_shipment_check_response(result, hsn_code, dest_country)

    except Exception as e:
        logger.error(f"WhatsApp shipment check error: {e}")
        return (
            f"Sorry, I couldn't process your shipment check for HSN {hsn_code} to {dest_country}.\n"
            "Please try again or visit dashboard.tradingintel.in for the full checker."
        )


async def _handle_intelligence_query(
    text: str,
    customer: Optional[Customer],
    db: AsyncSession,
) -> str:
    """Handle general intelligence queries."""
    text_lower = text.lower()

    # Extract country/market from query
    from app.models.models import IntelligenceItem
    from sqlalchemy import select

    # Try to find relevant intelligence items
    query = select(IntelligenceItem).order_by(
        IntelligenceItem.severity.desc(),
        IntelligenceItem.processed_at.desc()
    ).limit(3)

    result = await db.execute(query)
    items = result.scalars().all()

    if not items:
        return (
            "I don't have specific updates on that right now. "
            "For comprehensive trade intelligence, visit dashboard.tradingintel.in\n\n"
            "Try: *CHECK [HSN] TO [Country]* for pre-shipment checks."
        )

    lines = ["*Recent Trade Intelligence:*\n"]
    for item in items:
        emoji = {"urgent": "🚨", "watch": "👀", "opportunity": "✅"}.get(item.severity, "📢")
        lines.append(f"{emoji} *{item.title[:60]}*")
        lines.append(f"{item.summary[:120]}")
        lines.append("")

    lines.append("For full details: dashboard.tradingintel.in/intelligence")
    return "\n".join(lines)


async def _handle_hsn_input(text: str, sender_number: str, customer: Optional[Customer], db: AsyncSession) -> str:
    """Handle HSN code input during onboarding."""
    hsn_codes = [code.strip() for code in re.findall(r'\d{4,8}', text)]
    if not hsn_codes:
        return "Please enter valid HSN codes (4-8 digits). Example: 6101, 6202, 5208"

    _conversation_state[sender_number] = {
        "step": "collecting_market",
        "hsn_codes": hsn_codes[:5]
    }

    return (
        f"Got it! Tracking HSN codes: {', '.join(hsn_codes[:5])}\n\n"
        "Which markets do you export to? (e.g., USA, UK, UAE, EU)\n"
        "Enter up to 3 markets separated by commas:"
    )


async def _handle_market_input(text: str, sender_number: str, customer: Optional[Customer], db: AsyncSession) -> str:
    """Handle market input during onboarding."""
    state = _conversation_state.get(sender_number, {})
    hsn_codes = state.get("hsn_codes", [])

    markets = [m.strip().upper() for m in text.split(",") if m.strip()]
    markets = markets[:3]

    # Update subscription if customer exists
    if customer:
        from app.models.models import Subscription
        result = await db.execute(
            select(Subscription).where(Subscription.customer_id == customer.id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.hsn_codes = hsn_codes
            sub.dest_markets = markets
            await db.commit()

    # Clear conversation state
    _conversation_state.pop(sender_number, None)

    return (
        f"Profile set up!\n\n"
        f"• HSN Codes: {', '.join(hsn_codes)}\n"
        f"• Markets: {', '.join(markets)}\n\n"
        "You'll receive weekly intelligence digests and urgent alerts for your profile.\n\n"
        "Try now: *CHECK 6101 TO UK* for a pre-shipment check!"
    )


def _get_help_message(customer: Optional[Customer]) -> str:
    """Get help/welcome message."""
    name = customer.name if customer else "there"
    return (
        f"👋 Hi {name}! Welcome to *TradingIntel*\n\n"
        "AI-powered trade intelligence for Indian exporters.\n\n"
        "*Commands:*\n"
        "• *CHECK [HSN] TO [Country]* — Pre-shipment intelligence\n"
        "  _e.g., CHECK 6101 TO UK_\n\n"
        "• *SETUP* — Configure your HSN codes & markets\n\n"
        "• *HELP* — Show this menu\n\n"
        "• *STOP* — Unsubscribe from alerts\n\n"
        "📊 Full dashboard: dashboard.tradingintel.in\n\n"
        "_You're on TradingIntel's 30-day free trial_"
    )


async def _get_or_create_customer_by_whatsapp(
    phone_number: str,
    db: AsyncSession,
) -> Optional[Customer]:
    """Find existing customer or create a basic record for new WhatsApp users."""
    # Normalize number
    clean_number = phone_number.replace("+", "").replace("-", "").replace(" ", "")
    if len(clean_number) == 10:
        clean_number = f"91{clean_number}"

    result = await db.execute(
        select(Customer).where(Customer.whatsapp == clean_number)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        # Also try the original number format
        result2 = await db.execute(
            select(Customer).where(Customer.whatsapp == phone_number)
        )
        customer = result2.scalar_one_or_none()

    return customer
