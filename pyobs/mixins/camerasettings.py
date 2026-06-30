from __future__ import annotations

import logging
from typing import Any, cast

from pyobs.interfaces import IBinning, IData, IFilters, IWindow
from pyobs.modules import Module

log = logging.getLogger(__name__)


class CameraSettingsMixin:
    """Mixin for a device that should be able to set camera settings."""

    __module__ = "pyobs.mixins"

    def __init__(
        self,
        filters: str | IFilters | None = None,
        filter_name: str | None = None,
        binning: int | None = None,
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

    async def _do_camera_settings(self, camera: Module | IData | IFilters | IBinning | IWindow) -> None:
        """Do camera settings for given camera."""

        # check type
        if not isinstance(self, Module) or not isinstance(self, CameraSettingsMixin):
            raise ValueError("This is not a module")

        # filter
        if self.__camerasettings_filters is not None and self.__camerasettings_filter is not None:
            # get proxy
            async with cast(Module, cast(object, self)).proxy(self.__camerasettings_filters, IFilters) as proxy:
                log.info("Setting filter to %s...", self.__camerasettings_filter)
                await proxy.set_filter(self.__camerasettings_filter)

        # camera settings
        if self.__camerasettings_binning is not None and isinstance(camera, IBinning):
            log.info("Setting binning to %dx%d...", self.__camerasettings_binning, self.__camerasettings_binning)
            await camera.set_binning(self.__camerasettings_binning, self.__camerasettings_binning)
        if isinstance(camera, IWindow):
            log.info("Set window to full frame...")
            cap = camera.get_capabilities(IWindow)
            if cap is not None:
                await camera.set_window(cap.full_frame_x, cap.full_frame_y, cap.full_frame_width, cap.full_frame_height)
            else:
                raise ValueError("Could not get full frame size.")


__all__ = ["CameraSettingsMixin"]
