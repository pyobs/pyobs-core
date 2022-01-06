from __future__ import annotations
import logging
from typing import Union, cast, Optional, Any

from pyobs.interfaces import IBinning, IWindow, IFilters, IImageGrabber
from pyobs.modules import Module

log = logging.getLogger(__name__)


class CameraSettingsMixin:
    """Mixin for a device that should be able to set camera settings."""

    __module__ = "pyobs.mixins"

    def __init__(
        self,
        filters: Optional[Union[str, IFilters]] = None,
        filter_name: Optional[str] = None,
        binning: Optional[int] = None,
        **kwargs: Any,
    ):
        """Initializes the mixin.

        Args:
            filters: Filter wheel module.
            filter: Filter to set.
            binning: Binning to set.
        """

        # store
        self.__camerasettings_filters = filters
        self.__camerasettings_filter = filter_name
        self.__camerasettings_binning = binning

    async def _do_camera_settings(self, camera: Union[Module, IImageGrabber, IFilters, IBinning, IWindow]) -> None:
        """Do camera settings for given camera."""

        # check type
        if not isinstance(self, Module) or not isinstance(self, CameraSettingsMixin):
            raise ValueError("This is not a module")

        # filter
        if self.__camerasettings_filters is not None and self.__camerasettings_filter is not None:
            # get proxy
            log.info("Getting proxy for filter wheel...")
            filters = await cast(Module, self).proxy(self.__camerasettings_filters, IFilters)

            # set it
            log.info("Setting filter to %s...", self.__camerasettings_filter)
            await filters.set_filter(self.__camerasettings_filter)

        # camera settings
        if self.__camerasettings_binning is not None and isinstance(camera, IBinning):
            log.info("Setting binning to %dx%d...", self.__camerasettings_binning, self.__camerasettings_binning)
            await camera.set_binning(self.__camerasettings_binning, self.__camerasettings_binning)
        if isinstance(camera, IWindow):
            log.info("Set window to full frame...")
            full_frame = await camera.get_full_frame()
            if full_frame is not None:
                await camera.set_window(*full_frame)
            else:
                raise ValueError("Could not get full frame size.")


__all__ = ["CameraSettingsMixin"]
