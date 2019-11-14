import logging
from typing import Union

from pyobs import PyObsModule
from pyobs.interfaces import ITelescope, IAutoGuiding, ICamera
from pyobs.object import get_object
from pyobs.utils.guiding.base import BaseGuider


log = logging.getLogger(__name__)


class AutoGuider(PyObsModule, IAutoGuiding):
    """An auto-guiding system."""

    def __init__(self, camera: Union[str, ICamera], telescope: Union[str, ITelescope], guider: Union[dict, BaseGuider],
                 *args, **kwargs):
        """Initializes a new auto guiding system.

        Args:
            camera: Camera to use.
            telescope: Telescope to use.
            guider: Auto-guider to use
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store
        self._camera = camera
        self._telescope = telescope
        self._enabled = False
        self._exp_time = 1000

        # add thread func
        self._add_thread_func(self._auto_guiding, True)

        # create auto-guiding system
        self._guider: BaseGuider = get_object(guider, BaseGuider)

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # check camera
        try:
            self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Given camera does not exist or is not of correct type at the moment.')

        # check telescope
        try:
            self.proxy(self._telescope, ITelescope)
        except ValueError:
            log.warning('Given telescope does not exist or is not of correct type at the moment.')

    def set_exposure_time(self, exp_time: int):
        """Set the exposure time for the auto-guider.

        Args:
            exp_time: Exposure time in ms.
        """
        self._exp_time = exp_time
        self._guider.reset()

    def start(self, *args, **kwargs):
        """Starts/resets auto-guiding."""
        self._enabled = True
        self._guider.reset()

    def stop(self, *args, **kwargs):
        """Stops auto-guiding."""
        self._enabled = False

    def is_running(self, *args, **kwargs) -> bool:
        """Whether auto-guiding is running.

        Returns:
            Auto-guiding is running.
        """
        return self._enabled

    def _auto_guiding(self):
        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._enabled:
                self.closing.wait(1)
                continue

            try:
                # get telescope and camera
                telescope: ITelescope = self.proxy(self._telescope, ITelescope)
                camera: ICamera = self.proxy(self._camera, ICamera)

                # take image
                log.info('Taking image with an exposure time of %dms...', self._exp_time)
                filenames = camera.expose(self._exp_time, ICamera.ImageType.OBJECT, 1, False).wait()

                # download image
                image = self.vfs.download_image(filenames[0])

                # process it
                log.info('Processing image...')
                self._guider(image, telescope, self.location)

            except Exception as e:
                log.error('An error occurred: ', e)
                self.closing.wait(5)


__all__ = ['AutoGuider']
