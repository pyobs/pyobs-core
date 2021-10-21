from __future__ import annotations
import logging
from typing import Union

from pyobs.interfaces.proxies import IBinningProxy, ICameraProxy, IWindowProxy, IFiltersProxy
from pyobs.modules import Module

log = logging.getLogger(__name__)


class CameraSettingsMixin:
    """Mixin for a device that should be able to set camera settings."""
    __module__ = 'pyobs.mixins'

    def __init__(self, filters: Union[str, IFiltersProxy] = None, filter_name: str = None, binning: int = None,
                 *args, **kwargs):
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

    def _do_camera_settings(self, camera: ICameraProxy):
        """Do camera settings for given camera."""

        # check type
        if not isinstance(self, Module) or not isinstance(self, CameraSettingsMixin):
            raise ValueError('This is not a module')

        # filter
        if self.__camerasettings_filters is not None and self.__camerasettings_filter is not None:
            # get proxy
            log.info('Getting proxy for filter wheel...')
            filters: IFiltersProxy = self.proxy(self.__camerasettings_filters, IFiltersProxy)

            # set it
            log.info('Setting filter to %s...', self.__camerasettings_filter)
            filters.set_filter(self.__camerasettings_filter).wait()

        # camera settings
        if self.__camerasettings_binning is not None and isinstance(camera, IBinningProxy):
            log.info('Setting binning to %dx%d...', self.__camerasettings_binning, self.__camerasettings_binning)
            camera.set_binning(self.__camerasettings_binning, self.__camerasettings_binning).wait()
        if isinstance(camera, IWindowProxy):
            log.info('Set window to full frame...')
            full_frame = camera.get_full_frame().wait()
            camera.set_window(*full_frame).wait()


__all__ = ['CameraSettingsMixin']
