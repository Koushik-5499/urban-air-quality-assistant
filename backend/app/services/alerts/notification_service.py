"""Notification delivery service supporting In-App and Web Push."""

import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


class NotificationService:
    """Dispatches air quality alerts across active channels."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    async def dispatch_web_push(
        self,
        db: Session,
        user_id: str,
        title: str,
        body: str,
        data_payload: dict | None = None,
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


