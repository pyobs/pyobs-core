import logging
from typing import Union, Tuple, Dict, Any, Optional
import threading
import numpy as np
from numpy.typing import NDArray

from pyobs.interfaces import IAutoFocus
from pyobs.events import FocusFoundEvent
from pyobs.interfaces import IExposureTime, IImageType, IFocuser, IFilters, IData
from pyobs.object import get_object
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout, Module
from pyobs.utils.enums import ImageType
from pyobs.utils.focusseries import FocusSeries
from pyobs.utils import exceptions as exc

log = logging.getLogger(__name__)


class AutoFocusSeries(Module, CameraSettingsMixin, IAutoFocus):
    """Module for auto-focusing a telescope."""

    __module__ = "pyobs.modules.focus"

    def __init__(
        self,
        focuser: Union[str, IFocuser],
        camera: Union[str, IData],
        series: Union[Dict[str, Any], FocusSeries],
        offset: bool = False,
        filters: Optional[Union[str, IFilters]] = None,
        filter_name: Optional[str] = None,
        binning: Optional[int] = None,
        **kwargs: Any,
    ):
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

        # register exceptions
        if isinstance(camera, str):
            exc.register_exception(
                exc.RemoteError, 3, timespan=600, module=camera, callback=self._default_remote_error_callback
            )
        if isinstance(focuser, str):
            exc.register_exception(
                exc.RemoteError, 3, timespan=600, module=focuser, callback=self._default_remote_error_callback
            )

    async def open(self) -> None:
        """Open module"""
        await Module.open(self)

        # register event
        await self.comm.register_event(FocusFoundEvent)

        # check focuser and camera
        try:
            await self.proxy(self._focuser, IFocuser)
            await self.proxy(self._camera, IData)
        except ValueError:
            log.warning("Either camera or focuser do not exist or are not of correct type at the moment.")

    @timeout(600)
    async def auto_focus(self, count: int, step: float, exposure_time: float, **kwargs: Any) -> Tuple[float, float]:
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
        log.info("Performing auto-focus...")

        # get focuser
        log.info("Getting proxy for focuser...")
        focuser = await self.proxy(self._focuser, IFocuser)

        # get camera
        log.info("Getting proxy for camera...")
        camera = await self.proxy(self._camera, IData)

        # do camera settings
        await self._do_camera_settings(camera)

        # get filter wheel and current filter
        filter_name = "unknown"
        try:
            filter_wheel = await self.proxy(self._filters, IFilters)
            filter_name = await filter_wheel.get_filter()
        except ValueError:
            log.warning("Filter module is not of type IFilters. Could not get filter.")

        # get focus as first guess
        try:
            if self._offset:
                guess = 0.0
                log.info("Using focus offset of 0mm as initial guess.")
            else:
                guess = await focuser.get_focus()
                log.info("Using current focus of %.2fmm as initial guess.", guess)
        except exc.RemoteError:
            raise ValueError("Could not fetch current focus value.")

        # define array of focus values to iterate
        focus_values: NDArray[float] = np.linspace(guess - count * step, guess + count * step, 2 * count + 1)

        # reset
        self._series.reset()
        self._abort = threading.Event()

        # loop focus values
        log.info("Starting focus series...")
        for foc in focus_values:
            # set focus
            if self._offset:
                log.info("Changing focus offset to %.2fmm...", foc)
            else:
                log.info("Changing focus to %.2fmm...", foc)
            if self._abort.is_set():
                raise InterruptedError()
            try:
                if self._offset:
                    await focuser.set_focus_offset(float(foc))
                else:
                    await focuser.set_focus(float(foc))

            except exc.RemoteError:
                raise ValueError("Could not set new focus value.")

            # do exposure
            log.info("Taking picture...")
            if self._abort.is_set():
                raise InterruptedError()
            try:
                if isinstance(camera, IExposureTime):
                    await camera.set_exposure_time(exposure_time)
                if isinstance(camera, IImageType):
                    await camera.set_image_type(ImageType.FOCUS)
                filename = await camera.grab_data()
            except exc.RemoteError:
                log.error("Could not take image.")
                continue

            # download image
            log.info("Downloading image...")
            image = await self.vfs.read_image(filename)

            # analyse
            log.info("Analysing picture...")
            try:
                self._series.analyse_image(image, foc)
            except:
                # do nothing..
                log.error("Could not analyse image.")
                continue

        # fit focus
        if self._abort.is_set():
            raise InterruptedError()
        focus = self._series.fit_focus()

        # did focus series fail?
        if focus is None or focus[0] is None or np.isnan(focus[0]):
            log.warning("Focus series failed.")

            # reset to initial values
            if self._offset:
                log.info("Resetting focus offset to 0.", guess)
                await focuser.set_focus_offset(0)
            else:
                log.info("Resetting focus to initial guess of %.3f mm.", guess)
                await focuser.set_focus(guess)

            # raise error
            raise ValueError("Could not find best focus.")

        # log and set focus
        if self._offset:
            log.info("Setting new focus offset of (%.3f+-%.3f) mm.", focus[0], focus[1])
            absolute = focus[0] + await focuser.get_focus()
            await focuser.set_focus_offset(focus[0])
        else:
            log.info("Setting new focus value of (%.3f+-%.3f) mm.", focus[0], focus[1])
            absolute = focus[0] + await focuser.get_focus_offset()
            await focuser.set_focus(focus[0])

        # send event
        await self.comm.send_event(FocusFoundEvent(absolute, focus[1], filter_name))

        # return result
        return focus[0], focus[1]

    async def auto_focus_status(self, **kwargs: Any) -> Dict[str, Any]:
        """Returns current status of auto focus.

        Returned dictionary contains a list of focus/fwhm pairs in X and Y direction.

        Returns:
            Dictionary with current status.
        """
        return {}

    @timeout(20)
    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort.set()


__all__ = ["AutoFocusSeries"]
