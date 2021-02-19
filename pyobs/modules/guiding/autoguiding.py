import logging
import numpy as np

from pyobs.interfaces import ICamera, IImageType, ICameraExposureTime
from .base import BaseGuiding
from ...images.processors.exptime.star import StarExpTimeEstimator
from ...images.processors.photometry import SepPhotometry
from ...utils.enums import ImageType

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding):
    """An auto-guiding system."""

    def __init__(self, exposure_time: float = 1.,  *args, **kwargs):
        """Initializes a new auto guiding system.

        Args:
            exposure_time: Initial exposure time in seconds.
        """
        BaseGuiding.__init__(self, *args, **kwargs)

        # store
        self._initial_exposure_time = exposure_time
        self._exposure_time = None
        self._bias = None
        self._restart = True
        self._photometry = SepPhotometry()

        # add thread func
        self._add_thread_func(self._auto_guiding, True)

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        log.info('Setting exposure time to %ds...', exposure_time)
        self._initial_exposure_time = exposure_time
        self._exposure_time = None
        self._loop_closed = False
        self._restart = True
        self._guiding_offset.reset()

    def _init_guiding(self, camera: ICamera):
        """Init guiding after reset.

        Args:
            camera: Camera to use.
        """

        # take bias image
        log.info('Taking BIAS image...')
        if isinstance(camera, ICameraExposureTime):
            camera.set_exposure_time(0.)
        if isinstance(camera, IImageType):
            camera.set_image_type(ImageType.BIAS)
        filename = camera.expose(broadcast=False).wait()

        # download image and calculate median bias
        bias = self.vfs.read_image(filename)
        self._bias = float(np.median(bias.data))

    def _auto_guiding(self):
        # exposure time estimator
        exp_time_estimator = None

        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._enabled:
                self.closing.wait(1)
                self._restart = True
                continue

            try:
                # get camera
                camera: ICamera = self.proxy(self._camera, ICamera)

                # take image
                if isinstance(camera, ICameraExposureTime):
                    # did we restart guiding?
                    if self._restart:
                        self._init_guiding(camera)
                        exp_time_estimator = StarExpTimeEstimator(self._photometry, bias=self._bias)
                        self._restart = False

                    # set exposure time
                    exp_time = self._exposure_time if self._exposure_time is not None else self._initial_exposure_time
                    log.info('Taking image with an exposure time of %dms...', exp_time)
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
                    new_exp_time = exp_time_estimator(image)
                    print(new_exp_time, exp_time_estimator.coordinates)
                    self._exposure_time = max(min(new_exp_time, 5), 0.1)

                # process it
                log.info('Processing image...')
                self._process_image(image)

            except Exception as e:
                log.error('An error occurred: ', e)
                self.closing.wait(5)


__all__ = ['AutoGuiding']
