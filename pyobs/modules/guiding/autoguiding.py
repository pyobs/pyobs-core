import logging

from pyobs.interfaces import ICamera, IImageType, IExposureTime
from .base import BaseGuiding
from ...images.processors.exptime.star import StarExpTimeEstimator
from ...images.processors.detection import SepSourceDetection
from ...utils.enums import ImageType

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding):
    """An auto-guiding system."""
    __module__ = 'pyobs.modules.guiding'

    def __init__(self, exposure_time: float = 1.,  *args, **kwargs):
        """Initializes a new auto guiding system.

        Args:
            exposure_time: Initial exposure time in seconds.
        """
        BaseGuiding.__init__(self, *args, **kwargs)

        # store
        self._initial_exposure_time = exposure_time
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
        self._initial_exposure_time = exposure_time
        self._exposure_time = None
        self._loop_closed = False
        self._guiding_offset.reset()

    def _auto_guiding(self):
        # exposure time estimator
        exp_time_estimator = StarExpTimeEstimator(self._source_detection)

        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._enabled:
                self.closing.wait(1)
                continue

            try:
                # get camera
                camera: ICamera = self.proxy(self._camera, ICamera)

                # take image
                if isinstance(camera, IExposureTime):
                    # set exposure time
                    exp_time = self._exposure_time if self._exposure_time is not None else self._initial_exposure_time
                    log.info('Taking image with an exposure time of %.2fs...', exp_time)
                    camera.set_exposure_time(exp_time)
                else:
                    log.info('Taking image...')
                if isinstance(camera, IImageType):
                    camera.set_image_type(ImageType.OBJECT)
                filename = camera.expose(broadcast=False).wait()

                # download image
                image = self.vfs.read_image(filename)

                # need to estimate exposure time?
                if self._exposure_time is None and exp_time_estimator is not None:
                    exp_time_estimator(image)
                    new_exp_time = exp_time_estimator.exp_time
                    self._exposure_time = max(min(new_exp_time, 5), 0.1)

                # process it
                log.info('Processing image...')
                self._process_image(image)

            except Exception as e:
                log.error('An error occurred: ', e)
                self.closing.wait(5)


__all__ = ['AutoGuiding']
