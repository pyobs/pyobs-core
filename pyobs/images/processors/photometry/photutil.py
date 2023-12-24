import logging

from ._photutil_aperture_photometry import _PhotUtilAperturePhotometry
from .aperture_photometry import AperturePhotometry

log = logging.getLogger(__name__)


class PhotUtilsPhotometry(AperturePhotometry):
    """Perform photometry using PhotUtils."""

    __module__ = "pyobs.images.processors.photometry"

    def __init__(self, **kwargs):
        super().__init__(_PhotUtilAperturePhotometry(), **kwargs)


__all__ = ["PhotUtilsPhotometry"]
