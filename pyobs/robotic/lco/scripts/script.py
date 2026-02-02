import logging
from typing import Any

from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class LcoScript(Script):
    """Script for LCO configs."""

    exptime_done: float = 0.0
    config: dict[str, Any]


__all__ = ["LcoScript"]
