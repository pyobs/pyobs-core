from __future__ import annotations

import logging
from abc import ABCMeta
from typing import Any

from pyobs.events import NewDataEvent
from pyobs.interfaces import IData
from pyobs.mixins.datasequence import DataSequenceMixin
from pyobs.mixins.fitsheader import FitsHeaderMixin
from pyobs.modules import Module

log = logging.getLogger(__name__)


class BaseData(Module, FitsHeaderMixin, IData, DataSequenceMixin, metaclass=ABCMeta):
    """Base class for modules that grab data that is neither an image nor a spectrum.

    Provides the FITS header handling and file naming of :class:`~pyobs.mixins.FitsHeaderMixin`, grab sequences
    via :class:`~pyobs.mixins.DataSequenceMixin`, and sends a :class:`~pyobs.events.NewDataEvent` for new data.
    Derived classes implement ``grab_data()`` and ``_sequence_busy()``, call :meth:`_send_new_data` once the data
    is stored, and extend :meth:`abort` with the actual hardware abort.
    """

    __module__ = "pyobs.modules.camera"

    def __init__(
        self,
        fits_headers: dict[str, Any] | None = None,
        filenames: str = "/cache/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits.gz",
        fits_namespaces: list[str] | None = None,
        **kwargs: Any,
    ):
        """Creates a new BaseData.

        Args:
            fits_headers: Additional FITS headers.
            filenames: Template for file naming.
            fits_namespaces: List of namespaces for FITS headers that this module should request.
        """
        super().__init__(fits_namespaces=fits_namespaces, fits_headers=fits_headers, filenames=filenames, **kwargs)

        if self._comm is None:
            log.warning("No comm module given, will not be able to signal new data!")

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # declare the event we send, exactly this class (NewImageEvent and NewSpectrumEvent are not sent)
        if self._comm:
            await self.comm.register_event(NewDataEvent)

        # publish initial state
        await self._datasequence_open()

    async def _send_new_data(self, filename: str, broadcast: bool = True) -> None:
        """Send a NewDataEvent for stored data.

        Args:
            filename: VFS path of the stored data.
            broadcast: Whether to send the event at all.
        """
        if broadcast and self._comm:
            await self.comm.send_event(NewDataEvent(filename))

    async def abort(self, **kwargs: Any) -> None:
        """Aborts the current grab and sequence. Derived classes must implement the actual hardware abort and
        call this."""
        self._abort_data_sequence()


__all__ = ["BaseData"]
