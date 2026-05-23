"""Postmark email delivery service."""
import logging
from typing import List, Dict, Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

POSTMARK_API_BASE = "https://api.postmarkapp.com"

SEVERITY_COLORS = {
    "urgent": "#EF4444",  # red
    "watch": "#F59E0B",   # amber
    "opportunity": "#10B981",  # green
}

SEVERITY_LABELS = {
    "urgent": "🚨 URGENT",
    "watch": "👀 WATCH",
    "opportunity": "✅ OPPORTUNITY",
}


def _build_digest_html(customer_name: str, company: str, items: List[Dict[str, Any]]) -> str:
    """Build HTML email body for weekly digest."""
    urgent = [i for i in items if i.get("severity") == "urgent"]
    watch = [i for i in items if i.get("severity") == "watch"]
    opportunities = [i for i in items if i.get("severity") == "opportunity"]

    sections_html = ""

    def render_items(section_items: List[Dict], label: str, color: str) -> str:
        if not section_items:
            return ""
        items_html = ""
        for item in section_items:
            countries = ", ".join(item.get("countries", [])[:3]) or "Multiple"
            hsn = ", ".join(item.get("hsn_codes", [])[:3]) or "Various"
            action = item.get("action_text", "")
            source = item.get("source_url", "#")

            items_html += f"""
            <div style="margin-bottom:20px;padding:16px;border-left:4px solid {color};background:#f9fafb;border-radius:4px;">
                <h3 style="margin:0 0 8px;font-size:16px;color:#111827;">{item.get('title', '')}</h3>
                <p style="margin:0 0 8px;color:#4b5563;font-size:14px;">{item.get('summary', '')}</p>
                <div style="font-size:12px;color:#6b7280;margin-bottom:8px;">
                    📍 Markets: {countries} &nbsp;|&nbsp; 🏷️ HSN: {hsn}
                </div>
                {f'<div style="background:#fffbeb;padding:8px 12px;border-radius:4px;font-size:13px;color:#92400e;"><strong>Action Required:</strong> {action}</div>' if action else ''}
                {f'<div style="margin-top:8px;"><a href="{source}" style="color:#2563eb;font-size:12px;">View Source →</a></div>' if source and source != "#" else ''}
            </div>
            """
        return f"""
        <div style="margin-bottom:24px;">
            <h2 style="color:{color};font-size:18px;border-bottom:2px solid {color};padding-bottom:8px;">{label}</h2>
            {items_html}
        </div>
        """

    sections_html += render_items(urgent, "🚨 Urgent Alerts", SEVERITY_COLORS["urgent"])
    sections_html += render_items(watch, "👀 Watch List", SEVERITY_COLORS["watch"])
    sections_html += render_items(opportunities, "✅ Opportunities", SEVERITY_COLORS["opportunity"])

    if not items:
        sections_html = """
        <div style="text-align:center;padding:40px;color:#6b7280;">
            <p>No new trade updates this week. Markets are stable for your subscribed segments.</p>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>TradingIntel Weekly Brief</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;background:#f3f4f6;">
    <div style="background:#0F172A;padding:24px;text-align:center;">
        <h1 style="color:#F59E0B;margin:0;font-size:24px;">TradingIntel</h1>
        <p style="color:#94a3b8;margin:4px 0 0;font-size:14px;">Weekly Trade Intelligence Brief</p>
    </div>
    <div style="background:#fff;padding:24px;">
        <p style="color:#374151;">Hi <strong>{customer_name}</strong> ({company}),</p>
        <p style="color:#4b5563;margin-bottom:24px;">Here's your weekly trade intelligence summary.
           Stay ahead of regulatory changes that affect your export business.</p>
        {sections_html}
        <div style="text-align:center;margin-top:32px;">
            <a href="{settings.FRONTEND_URL}/dashboard"
               style="background:#F59E0B;color:#0F172A;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
                View Full Dashboard →
            </a>
        </div>
    </div>
    <div style="background:#f9fafb;padding:16px;text-align:center;font-size:12px;color:#9ca3af;">
        <p>TradingIntel — AI-Powered Trade Intelligence for Indian Exporters</p>
        <p><a href="{settings.FRONTEND_URL}/dashboard/settings" style="color:#6b7280;">Manage Preferences</a>
           &nbsp;|&nbsp; <a href="{settings.FRONTEND_URL}/unsubscribe" style="color:#6b7280;">Unsubscribe</a></p>
    </div>
</body>
</html>
    """


def _build_alert_html(customer_name: str, item: Dict[str, Any]) -> str:
    """Build HTML email body for an urgent alert."""
    severity = item.get("severity", "watch")
    color = SEVERITY_COLORS.get(severity, "#F59E0B")
    label = SEVERITY_LABELS.get(severity, "Alert")
    countries = ", ".join(item.get("countries", [])[:3]) or "Multiple markets"
    hsn = ", ".join(item.get("hsn_codes", [])[:4]) or "Various"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>TradingIntel Alert</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;background:#f3f4f6;">
    <div style="background:{color};padding:24px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:22px;">{label}</h1>
        <p style="color:rgba(255,255,255,0.9);margin:4px 0 0;font-size:14px;">TradingIntel Trade Alert</p>
    </div>
    <div style="background:#fff;padding:24px;">
        <p style="color:#374151;">Hi <strong>{customer_name}</strong>,</p>
        <div style="background:#fef2f2;border:1px solid #fee2e2;border-radius:8px;padding:20px;margin:16px 0;">
            <h2 style="color:#991b1b;margin:0 0 12px;font-size:18px;">{item.get('title', '')}</h2>
            <p style="color:#4b5563;margin:0;">{item.get('summary', '')}</p>
        </div>
        <div style="margin:20px 0;padding:16px;background:#f9fafb;border-radius:8px;">
            <div style="margin-bottom:8px;"><strong>📍 Affected Markets:</strong> {countries}</div>
            <div style="margin-bottom:8px;"><strong>🏷️ HSN Codes:</strong> {hsn}</div>
        </div>
        {f'''
        <div style="background:#fffbeb;padding:16px;border-radius:8px;border-left:4px solid #F59E0B;">
            <strong style="color:#92400e;">Required Action:</strong>
            <p style="margin:8px 0 0;color:#78350f;">{item.get('action_text', '')}</p>
        </div>
        ''' if item.get('action_text') else ''}
        {f'<p><a href="{item["source_url"]}" style="color:#2563eb;">View Source Document →</a></p>' if item.get('source_url') else ''}
        <div style="text-align:center;margin-top:32px;">
            <a href="{settings.FRONTEND_URL}/dashboard/alerts"
               style="background:#EF4444;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
                View Alert in Dashboard →
            </a>
        </div>
    </div>
    <div style="background:#f9fafb;padding:16px;text-align:center;font-size:12px;color:#9ca3af;">
        <p>TradingIntel — AI-Powered Trade Intelligence for Indian Exporters</p>
    </div>
</body>
</html>
    """


async def send_digest_email(
    customer: Any,
    intelligence_items: List[Dict[str, Any]],
) -> bool:
    """Send weekly digest email via Postmark."""
    if not settings.POSTMARK_API_KEY:
        logger.warning(f"Email: No Postmark API key, skipping digest for {customer.email}")
        return False

    if not customer.email:
        logger.debug(f"Customer {customer.id} has no email address")
        return False

    html_body = _build_digest_html(
        customer_name=customer.name,
        company=customer.company,
        items=intelligence_items,
    )

    count = len(intelligence_items)
    urgent_count = sum(1 for i in intelligence_items if i.get("severity") == "urgent")
    subject = f"TradingIntel Weekly Brief: {count} updates"
    if urgent_count:
        subject = f"🚨 TradingIntel: {urgent_count} urgent alerts + {count - urgent_count} updates"

    return await _send_email(
        to_email=customer.email,
        subject=subject,
        html_body=html_body,
    )


async def send_alert_email(
    customer: Any,
    alert_item: Dict[str, Any],
) -> bool:
    """Send urgent alert email via Postmark."""
    if not settings.POSTMARK_API_KEY:
        logger.warning(f"Email: No Postmark API key, skipping alert for {customer.email}")
        return False

    if not customer.email:
        return False

    html_body = _build_alert_html(
        customer_name=customer.name,
        item=alert_item,
    )

    severity = alert_item.get("severity", "watch")
    prefix = "🚨" if severity == "urgent" else "👀"
    subject = f"{prefix} TradingIntel Alert: {alert_item.get('title', 'Trade Update')[:70]}"

    return await _send_email(
        to_email=customer.email,
        subject=subject,
        html_body=html_body,
    )


async def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via Postmark API."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{POSTMARK_API_BASE}/email",
                json={
                    "From": settings.POSTMARK_FROM_EMAIL,
                    "To": to_email,
                    "Subject": subject,
                    "HtmlBody": html_body,
                    "MessageStream": "outbound",
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Postmark-Server-Token": settings.POSTMARK_API_KEY,
                }
            )
            response.raise_for_status()
            result = response.json()

            if result.get("ErrorCode") == 0:
                logger.info(f"Email: Sent to {to_email}: {subject}")
                return True
            else:
                logger.warning(f"Email: Postmark error {result.get('ErrorCode')}: {result.get('Message')}")
                return False

    except httpx.HTTPStatusError as e:
        logger.error(f"Email: HTTP error sending to {to_email}: {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Email: Error sending to {to_email}: {e}")
        return False
