from abc import ABCMeta, abstractmethod
from typing import Any

from pyobs.images import Image
from pyobs.object import Object
from pyobs.utils.exceptions import ImageError


class ImageProcessor(Object, metaclass=ABCMeta):
    VALID_ERROR_MODES = frozenset(("raise", "error", "info", "ignore"))

    def __init__(self, on_error: str = "raise", **kwargs: Any):
        """Init new image processor.

        Args:
            on_error: How the pipeline should handle an ImageError raised by this step. One of:
                - "raise" (default): re-raise the exception, aborting the pipeline.
                - "error": call handle_error(), pass its return value downstream.
                - "info": log at INFO level, pass the pre-step image downstream unmodified.
                - "ignore": silently pass the pre-step image downstream unmodified.
        """
        Object.__init__(self, **kwargs)

        self._on_error = on_error
        if self._on_error not in self.VALID_ERROR_MODES:
            raise ValueError(f"on_error must be one of {sorted(self.VALID_ERROR_MODES)}, got {self._on_error!r}.")

    @property
    def on_error(self) -> str:
        """The error handling mode for this step."""
        return self._on_error

    @abstractmethod
    async def __call__(self, image: Image) -> Image:
        """Processes an image.

        Args:
            image: Image to process.

        Returns:
            Processed image.
        """

    def handle_error(self, image: Image, error: ImageError) -> Image:
        """Handle an ImageError raised by this step, when on_error == "error".

        Override this to customize error handling (e.g. tag the image with a FITS header).
        The default implementation re-raises the error.

        Args:
            image: The image that caused the error.
            error: The ImageError that was raised.

        Returns:
            The image to pass to the next pipeline step.
        """
        raise error

    async def reset(self) -> None:
        """Resets state of image processor"""


__all__ = ["ImageProcessor"]
