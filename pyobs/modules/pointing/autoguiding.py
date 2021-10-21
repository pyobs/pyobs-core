import logging

from ._baseguiding import BaseGuiding
from ...images.meta.exptime import ExpTime
from ...images.processors.detection import SepSourceDetection
from ...interfaces.proxies import IExposureTimeProxy, IImageTypeProxy, IImageGrabberProxy
from ...utils.enums import ImageType

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding):
    """An auto-guiding system."""
    __module__ = 'pyobs.modules.guiding'

    def __init__(self, exposure_time: float = 1., *args, **kwargs):
        """Initializes a new auto guiding system.

        Args:
            exposure_time: Initial exposure time in seconds.
        """
        BaseGuiding.__init__(self, *args, **kwargs)

        # store
        self._default_exposure_time = exposure_time
        self._exposure_time = None
        self._source_detection = SepSourceDetection()

        # add thread func
        self.add_thread_func(self._auto_guiding, True)

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        log.info('Setting exposure time to %ds...', exposure_time)
        self._default_exposure_time = exposure_time
        self._exposure_time = None
        self._loop_closed = False
        self._guiding_offset.reset()

    def _auto_guiding(self):
        # exposure time
        self._exposure_time = self._default_exposure_time

        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._enabled:
                self.closing.wait(1)
                continue

            try:
                # get camera
                camera: IImageGrabberProxy = self.proxy(self._camera, IImageGrabberProxy)

                # take image
                if isinstance(camera, IExposureTimeProxy):
                    # set exposure time
                    log.info('Taking image with an exposure time of %.2fs...', self._exposure_time)
                    camera.set_exposure_time(self._exposure_time).wait()
                else:
                    log.info('Taking image...')
                if isinstance(camera, IImageTypeProxy):
                    camera.set_image_type(ImageType.OBJECT).wait()
                filename = camera.grab_image(broadcast=False).wait()

                # download image
                image = self.vfs.read_image(filename)

                # process it
                log.info('Processing image...')
                processed_image = self._process_image(image)
                log.info('Done.')

                # new exposure time?
                if processed_image is not None and processed_image.has_meta(ExpTime):
                    self._exposure_time = processed_image.get_meta(ExpTime).exptime

                # sleep a little
                self.closing.wait(self._min_interval)

            except Exception as e:
                log.error('An error occurred: ', e)
                self.closing.wait(5)


__all__ = ['AutoGuiding']
