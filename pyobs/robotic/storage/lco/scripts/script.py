import logging

from pyobs.robotic.scripts import Script
from pyobs.robotic.storage.lco._portal import LcoRequest

log = logging.getLogger(__name__)


class LcoScript(Script):
    """Script for LCO configs."""

    request: LcoRequest


__all__ = ["LcoScript"]
