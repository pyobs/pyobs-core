from __future__ import annotations

import abc

from pyobs.utils.serialization import PolymorphicBaseModel


class ExposureTimeProvider(PolymorphicBaseModel, metaclass=abc.ABCMeta):
    """Abstract base class for providers that determine camera exposure time."""

    default_exposure_time: float = 1.0

    @abc.abstractmethod
    async def __call__(self) -> float:
        """Determine and return the exposure time in seconds.

        Returns:
            Exposure time in seconds.
        """
        ...


__all__ = ["ExposureTimeProvider"]
