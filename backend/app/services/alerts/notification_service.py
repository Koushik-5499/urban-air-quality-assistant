"""Notification delivery service supporting In-App and Web Push channels adhering to SOLID."""

import json
import logging
from abc import ABC, abstractmethod

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


class BaseNotificationChannel(ABC):
    """Abstract interface defining delivery channels for environmental alerts (SOLID OCP & LSP)."""

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the unique channel identifier."""
        pass

    @abstractmethod
    async def dispatch(
        self,
        db: Session,
        recipient: str,
        title: str,
        body: str,
        data_payload: dict | None = None,
    ) -> int:
        """Dispatch notification payload to specified recipient channel."""
        pass


class WebPushNotificationChannel(BaseNotificationChannel):
    """Web Push notification channel delivering standards-compliant VAPID push messages."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def channel_name(self) -> str:
        return "web_push"

    async def dispatch(
        self,
        db: Session,
        recipient: str,
        title: str,
        body: str,
        data_payload: dict | None = None,
    ) -> int:
        """Deliver Web Push notifications to all active subscriptions for the given user."""
        if not self.settings.WEB_PUSH_ENABLED or not self.settings.VAPID_PRIVATE_KEY:
            logger.debug("Web push notifications disabled or VAPID_PRIVATE_KEY unconfigured.")
            return 0

        stmt = select(PushSubscription).where(PushSubscription.user_id == recipient)
        subs = list(db.execute(stmt).scalars().all())
        if not subs:
            return 0

        payload_json = json.dumps(
            {
                "title": title,
                "body": body,
                "data": data_payload or {},
            }
        )

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
                    logger.info("Pruning expired push subscription %d", sub.id)
                    db.delete(sub)
                else:
                    logger.warning("Web Push delivery failed: %s", exc)
            except Exception as exc:
                # Top-level notification channel boundary preventing individual push failure
                # from halting queue
                logger.exception("Unexpected error during web push: %s", exc)

        db.commit()
        return successful


class InAppNotificationChannel(BaseNotificationChannel):
    """In-app alert delivery channel for live UI alert streams (Liskov Substitution compliant)."""

    @property
    def channel_name(self) -> str:
        return "in_app"

    async def dispatch(
        self,
        db: Session,
        recipient: str,
        title: str,
        body: str,
        data_payload: dict | None = None,
    ) -> int:
        """Dispatch in-app notification (always succeeds for registered UI subscribers)."""
        logger.debug("In-app notification dispatched to %s: %s", recipient, title)
        return 1


class NotificationService:
    """Dispatches air quality alerts across registered channels adhering to DIP and OCP."""

    def __init__(
        self,
        settings: Settings | None = None,
        channels: list[BaseNotificationChannel] | None = None,
    ):
        self.settings = settings or get_settings()
        self.web_push_channel = WebPushNotificationChannel(settings=self.settings)
        self.in_app_channel = InAppNotificationChannel()
        self.channels: dict[str, BaseNotificationChannel] = {
            self.web_push_channel.channel_name: self.web_push_channel,
            self.in_app_channel.channel_name: self.in_app_channel,
        }
        if channels:
            for ch in channels:
                self.channels[ch.channel_name] = ch

    async def dispatch_web_push(
        self,
        db: Session,
        user_id: str,
        title: str,
        body: str,
        data_payload: dict | None = None,
    ) -> int:
        """Delegate Web Push dispatch to WebPushNotificationChannel."""
        return await self.web_push_channel.dispatch(
            db=db,
            recipient=user_id,
            title=title,
            body=body,
            data_payload=data_payload,
        )

    async def dispatch_all_channels(
        self,
        db: Session,
        user_id: str,
        title: str,
        body: str,
        data_payload: dict | None = None,
    ) -> dict[str, int]:
        """Broadcast alert to all registered notification channels."""
        results: dict[str, int] = {}
        for name, channel in self.channels.items():
            results[name] = await channel.dispatch(
                db=db,
                recipient=user_id,
                title=title,
                body=body,
                data_payload=data_payload,
            )
        return results
