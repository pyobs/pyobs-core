import logging

from pyobs.robotic.lco._portal import LcoRequest
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class LcoScript(Script):
    """Script for LCO configs."""

    request: LcoRequest


__all__ = ["LcoScript"]
