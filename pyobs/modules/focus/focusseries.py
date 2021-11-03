import logging
from typing import Union, Tuple, Dict, Any, Optional, cast
import threading
import numpy as np
from numpy.typing import NDArray

from pyobs.comm import RemoteException
from pyobs.interfaces import IAutoFocus
from pyobs.events import FocusFoundEvent
from pyobs.interfaces.proxies import IExposureTimeProxy, IImageTypeProxy, IFocuserProxy, IFiltersProxy, \
    IImageGrabberProxy
from pyobs.object import get_object
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout, Module
from pyobs.utils.enums import ImageType
from pyobs.utils.focusseries import FocusSeries

log = logging.getLogger(__name__)


class AutoFocusSeries(Module, CameraSettingsMixin, IAutoFocus):
    """Module for auto-focusing a telescope."""
    __module__ = 'pyobs.modules.focus'

    def __init__(self, focuser: Union[str, IFocuserProxy], camera: Union[str, IImageGrabberProxy], series: FocusSeries,
                 offset: bool = False, filters: Optional[Union[str, IFiltersProxy]] = None,
                 filter_name: Optional[str] = None, binning: Optional[int] = None, **kwargs: Any):
        """Initialize a new auto focus system.

        Args:
            focuser: Name of IFocuser.
            camera: Name of ICamera.
            filters: Name of IFilters, if any.
            filter_name: Name of filter to set.
            offset: If True, offsets are used instead of absolute focus values.
        """
        Module.__init__(self, **kwargs)

        # store focuser and camera
        self._focuser = focuser
        self._camera = camera
        self._filters = filters
        self._offset = offset
        self._abort = threading.Event()

        # create focus series
        self._series: FocusSeries = get_object(series, FocusSeries)

        # init camera settings mixin
        CameraSettingsMixin.__init__(self, filters=filters, filter_name=filter_name, binning=binning, **kwargs)

    def open(self) -> None:
        """Open module"""
        Module.open(self)

        # register event
        self.comm.register_event(FocusFoundEvent)

        # check focuser and camera
        try:
            self.proxy(self._focuser, IFocuserProxy)
            self.proxy(self._camera, IImageGrabberProxy)
        except ValueError:
            log.warning('Either camera or focuser do not exist or are not of correct type at the moment.')

    def close(self) -> None:
        """Close module."""

    @timeout(600)
    def auto_focus(self, count: int, step: float, exposure_time: float, **kwargs: Any) -> Tuple[float, float]:
        """Perform an auto-focus series.

        This method performs an auto-focus series with "count" images on each side of the initial guess and the given
        step size. With count=3, step=1 and guess=10, this takes images at the following focus values:
        7, 8, 9, 10, 11, 12, 13

        Args:
            count: Number of images to take on each side of the initial guess. Should be an odd number.
            step: Step size.
            exposure_time: Exposure time for images.

        Returns:
            Tuple of obtained best focus value and its uncertainty. Or Nones, if focus series failed.

        Raises:
            FileNotFoundException: If image could not be downloaded.
        """
        log.info('Performing auto-focus...')

        # get focuser
        log.info('Getting proxy for focuser...')
        focuser: IFocuserProxy = self.proxy(self._focuser, IFocuserProxy)

        # get camera
        log.info('Getting proxy for camera...')
        camera: IImageGrabberProxy = self.proxy(self._camera, IImageGrabberProxy)

        # do camera settings
        self._do_camera_settings(camera)

        # get filter wheel and current filter
        filter_name = 'unknown'
        try:
            filter_wheel: IFiltersProxy = self.proxy(self._filters, IFiltersProxy)
            filter_name = filter_wheel.get_filter().wait()
        except ValueError:
            log.warning('Filter module is not of type IFilters. Could not get filter.')

        # get focus as first guess
        try:
            if self._offset:
                guess = 0.
                log.info('Using focus offset of 0mm as initial guess.')
            else:
                guess = focuser.get_focus().wait()
                log.info('Using current focus of %.2fmm as initial guess.', guess)
        except RemoteException:
            raise ValueError('Could not fetch current focus value.')

        # define array of focus values to iterate
        focus_values: NDArray[float] = np.linspace(guess - count * step, guess + count * step, 2 * count + 1)

        # define set_focus method
        set_focus = focuser.set_focus_offset if self._offset else focuser.set_focus

        # reset
        self._series.reset()
        self._abort = threading.Event()

        # loop focus values
        log.info('Starting focus series...')
        for foc in focus_values:
            # set focus
            log.info('Changing focus to %.2fmm...', foc)
            if self._abort.is_set():
                raise InterruptedError()
            try:
                set_focus(float(foc)).wait()
            except RemoteException:
                raise ValueError('Could not set new focus value.')

            # do exposure
            log.info('Taking picture...')
            if self._abort.is_set():
                raise InterruptedError()
            try:
                if isinstance(camera, IExposureTimeProxy):
                    camera.set_exposure_time(exposure_time)
                if isinstance(camera, IImageTypeProxy):
                    camera.set_image_type(ImageType.FOCUS)
                filename = camera.grab_image().wait()
            except RemoteException:
                log.error('Could not take image.')
                continue

            # download image
            log.info('Downloading image...')
            image = self.vfs.read_image(filename)

            # analyse
            log.info('Analysing picture...')
            try:
                self._series.analyse_image(image)
            except:
                # do nothing..
                log.error('Could not analyse image.')
                continue

        # fit focus
        if self._abort.is_set():
            raise InterruptedError()
        focus = self._series.fit_focus()

        # did focus series fail?
        if focus is None or focus[0] is None or np.isnan(focus[0]):
            log.warning('Focus series failed.')

            # reset to initial values
            if self._offset:
                log.info('Resetting focus offset to initial guess of %.3f mm.', guess)
                focuser.set_focus_offset(focus[0]).wait()
            else:
                log.info('Resetting focus to initial guess of %.3f mm.', guess)
                focuser.set_focus(focus[0]).wait()

            # raise error
            raise ValueError('Could not find best focus.')

        # "absolute" will be the absolute focus value, i.e. focus+offset
        absolute = None

        # log and set focus
        if self._offset:
            log.info('Setting new focus offset of (%.3f+-%.3f) mm.', focus[0], focus[1])
            absolute = focus[0] + focuser.get_focus().wait()
            focuser.set_focus_offset(focus[0]).wait()
        else:
            log.info('Setting new focus value of (%.3f+-%.3f) mm.', focus[0], focus[1])
            absolute = focus[0] + focuser.get_focus_offset().wait()
            focuser.set_focus(focus[0]).wait()

        # send event
        self.comm.send_event(FocusFoundEvent(absolute, focus[1], filter_name))

        # return result
        return focus[0], focus[1]

    def auto_focus_status(self, **kwargs: Any) -> Dict[str, Any]:
        """Returns current status of auto focus.

        Returned dictionary contains a list of focus/fwhm pairs in X and Y direction.

        Returns:
            Dictionary with current status.
        """
        return {}

    @timeout(20)
    def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort.set()


__all__ = ['AutoFocusSeries']
