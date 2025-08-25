import logging
from typing import Any

from pyobs.events import NewImageEvent
from pyobs.interfaces import ICamera
from pyobs.mixins import ImageFitsHeaderMixin
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.images import Image
from pyobs.modules import Module
from pyobs.utils.enums import ImageType, ExposureStatus
from pyobs.utils.exceptions import GrabImageError

log = logging.getLogger(__name__)


class PipelineCamera(Module, ICamera, ImageFitsHeaderMixin, PipelineMixin):
    """A virtual camera based on an image pipeline."""

    __module__ = "pyobs.modules.camera"

    def __init__(self, **kwargs: Any):
        """Creates a new pipeline cammera."""
        Module.__init__(self, **kwargs)
        PipelineMixin.__init__(self, **kwargs)
        ImageFitsHeaderMixin.__init__(self, **kwargs)

    async def grab_data(self, broadcast: bool = True, **kwargs: Any) -> str:
        """Grabs an image and returns reference.

        Args:
            broadcast: Broadcast existence of image.

        Returns:
            Name of image that was taken.

        Raises:
            GrabImageError: If there was a problem grabbing the image.
        """

        # run pipeline
        image = Image()
        image = await self.run_pipeline(image)

        # add fits headers and format filename
        await self.add_fits_headers(image)
        filename = self.format_filename(image)
        if filename is None:
            raise GrabImageError("No filename given.")

        # upload file
        try:
            log.info("Uploading image to file server...")
            await self.vfs.write_image(filename, image)
        except FileNotFoundError:
            raise ValueError("Could not upload image.")

        # broadcast image path
        if broadcast and self.comm:
            log.info("Broadcasting image ID...")
            await self.comm.send_event(NewImageEvent(filename, ImageType.OBJECT))

        # return filename
        return filename

    async def get_exposure_status(self, **kwargs: Any) -> ExposureStatus:
        return ExposureStatus.IDLE

    async def get_exposure_progress(self, **kwargs: Any) -> float:
        return 0.0


__all__ = ["PipelineCamera"]
