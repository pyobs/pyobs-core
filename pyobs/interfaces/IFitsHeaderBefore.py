from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any

from .interface import Interface


@dataclass
class FitsHeaderEntry:
    value: int | float | str | None
    comment: str


class IFitsHeaderBefore(Interface, metaclass=ABCMeta):
    """The module provides some additional header entries for FITS headers before some event (usually the start of the
    exposure)."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_fits_header_before(
        self, namespaces: list[str] | None = None, **kwargs: Any
    ) -> dict[str, FitsHeaderEntry]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        ...


__all__ = ["FitsHeaderEntry", "IFitsHeaderBefore"]
