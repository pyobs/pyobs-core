from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyobs.robotic.scripts import Script
from pyobs.robotic.storage.lco._portal import LcoRequest

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class LcoScript(Script):
    """Script for LCO configs."""

    request: LcoRequest

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration based on the duration calculated by the LCO portal."""
        return float(self.request.duration)


__all__ = ["LcoScript"]
