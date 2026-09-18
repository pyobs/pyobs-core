from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import StrEnum
from typing import Any

from .interface import Interface


class PushNotificationType(StrEnum):
    """Distinct alert kinds `PushNotifier` can emit, one opt-in/out toggle each.

    Extensible: future kinds (bad weather, roof open, guiding lost) become new members here.
    Stored preferences keep working across such an addition, since they are stored as the
    enum's string values -- a kind added later simply defaults to on, and a stored value with
    no matching member never compares equal to anything.
    """

    MODULE_ERROR = "module_error"
    LOG_ERROR = "log_error"
    LOG_CRITICAL = "log_critical"


class IPushNotifications(Interface, metaclass=ABCMeta):
    """The module accepts device registrations for push notifications."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def register_device(self, token: str, platform: str = "android", **kwargs: Any) -> None:
        """Register a device to receive push notifications.

        Args:
            token: FCM/APNs device token.
            platform: Device platform ("android" or "ios"). Stored as given; only "android"
                actually receives pushes in v1 (see specs/design/push-notification-module.md).
        """
        ...

    @abstractmethod
    async def set_preferences(self, types: list[PushNotificationType], **kwargs: Any) -> None:
        """Set which notification types this caller wants to receive.

        Keyed by the calling account (`sender`), not by device -- applies to every device that
        account has registered, present and future. A caller that never calls this receives all
        types (all-on default); calling it with an empty list opts out of everything.

        Args:
            types: Notification types the caller wants to receive.
        """
        ...


__all__ = ["IPushNotifications", "PushNotificationType"]
