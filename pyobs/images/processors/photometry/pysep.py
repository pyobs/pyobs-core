import logging
from typing import Any

from ._sep_aperture_photometry import _SepAperturePhotometry
from .aperture_photometry import AperturePhotometry

log = logging.getLogger(__name__)


class SepPhotometry(AperturePhotometry):
    """Perform photometry using SEP."""

    __module__ = "pyobs.images.processors.photometry"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(_SepAperturePhotometry(), **kwargs)


__all__ = ["SepPhotometry"]
