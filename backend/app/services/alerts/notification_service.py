"""Notification delivery service supporting In-App, Resend Email, and Web Push."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
import httpx
from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.alert import Alert
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


class NotificationService:
    """Dispatches air quality alerts across active channels."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def dispatch_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> bool:
        """Send notification email via Resend API."""
        if not self.settings.EMAIL_NOTIFICATIONS_ENABLED or not self.settings.RESEND_API_KEY:
            logger.info("Email notifications disabled or RESEND_API_KEY unconfigured; skipping email to %s", recipient_email)
            return False

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": self.settings.ALERT_EMAIL_FROM,
            "to": [recipient_email],
            "subject": subject,
            "html": html_content,
            "text": text_content,
        }

        for attempt in range(self.settings.AQI_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code in (200, 201):
                        logger.info("Alert email successfully dispatched to %s", recipient_email)
                        return True
                    elif resp.status_code == 429:
                        logger.warning("Resend rate limited (attempt %d)", attempt + 1)
                    else:
                        logger.error("Resend delivery failed with status %d: %s", resp.status_code, resp.text)
                        return False
            except Exception as exc:
                logger.warning("Error dispatching email to %s (attempt %d): %s", recipient_email, attempt + 1, exc)

            if attempt < self.settings.AQI_MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))

        return False

    async def dispatch_web_push(
        self,
        db: Session,
        user_id: str,
        title: str,
        body: str,
        data_payload: Optional[Dict] = None,
    ) -> int:
        """Deliver Web Push notifications to all active subscriptions for the given user."""
        if not self.settings.WEB_PUSH_ENABLED or not self.settings.VAPID_PRIVATE_KEY:
            logger.debug("Web push notifications disabled or VAPID_PRIVATE_KEY unconfigured.")
            return 0

        stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
        subs = list(db.execute(stmt).scalars().all())
        if not subs:
            return 0

        payload_json = json.dumps({
            "title": title,
            "body": body,
            "data": data_payload or {},
        })

        successful = 0
        vapid_claims = {
            "sub": self.settings.VAPID_SUBJECT,
        }

        for sub in subs:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth,
                },
            }

            try:
                webpush(
                    subscription_info=sub_info,
                    data=payload_json,
                    vapid_private_key=self.settings.VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims,
                )
                successful += 1
            except WebPushException as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code in (404, 410):
                    # Subscription has expired or unsubscribed -> prune from DB
                    logger.info("Pruning expired push subscription %d", sub.id)
                    db.delete(sub)
                else:
                    logger.warning("Web Push delivery failed: %s", exc)
            except Exception as exc:
                logger.warning("Unexpected error during web push: %s", exc)

        db.commit()
        return successful

    @staticmethod
    def build_email_content(alert: Alert, city_name: str) -> Tuple[str, str, str]:
        """Generate structured subject, HTML body, and plain text content for an alert."""
        subject = f"[Air Quality Alert] {alert.title}"

        sim_note = (
            "<p style='color: #d97706; background: #fef3c7; padding: 8px; border-radius: 4px; font-weight: bold;'>"
            "DEMONSTRATION ALERT: This notification was generated from simulated data for demonstration purposes.</p>"
            if alert.is_simulated
            else ""
        )

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
            <h2 style="color: #1f2937; margin-top: 0;">Urban Air Quality Assistant</h2>
            {sim_note}
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0; color: #111827;">{alert.title}</h3>
                <p style="margin: 0; color: #4b5563; font-size: 15px;">{alert.description}</p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Location:</td>
                    <td style="padding: 8px 0; font-weight: bold; color: #111827;">{city_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Current AQI:</td>
                    <td style="padding: 8px 0; font-weight: bold; color: #111827;">{alert.current_aqi or 'N/A'} ({alert.aqi_category or 'N/A'})</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Dominant Pollutant:</td>
                    <td style="padding: 8px 0; font-weight: bold; color: #111827;">{alert.dominant_pollutant or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Recorded At:</td>
                    <td style="padding: 8px 0; color: #111827;">{alert.created_at.strftime('%Y-%m-%d %H:%M UTC')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Data Source:</td>
                    <td style="padding: 8px 0; color: #111827;">{alert.source}</td>
                </tr>
            </table>
            <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                Disclaimer: This notification is provided for educational and environmental awareness. It does not constitute professional medical advice.
            </p>
        </div>
        """

        text = f"""
Urban Air Quality Assistant - Alert
------------------------------------
{alert.title}

{alert.description}

Location: {city_name}
Current AQI: {alert.current_aqi or 'N/A'} ({alert.aqi_category or 'N/A'})
Dominant Pollutant: {alert.dominant_pollutant or 'N/A'}
Recorded At: {alert.created_at.strftime('%Y-%m-%d %H:%M UTC')}
Source: {alert.source}
Simulation Status: {'Simulated' if alert.is_simulated else 'Real observation'}

Disclaimer: This guidance is for environmental awareness and is not a substitute for professional medical advice.
        """.strip()

        return subject, html, text
