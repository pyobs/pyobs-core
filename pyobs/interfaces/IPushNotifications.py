from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


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


__all__ = ["IPushNotifications"]
