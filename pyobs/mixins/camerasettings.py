import logging
from typing import Union

from pyobs import Module
from pyobs.interfaces import ICamera, IFilters, ICameraWindow, ICameraBinning

log = logging.getLogger(__name__)


class CameraSettingsMixin:
    """Mixin for a device that should be able to set camera settings."""
    def __init__(self, filters: Union[str, IFilters] = None, filter_name: str = None, binning: int = None,
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

    def _do_camera_settings(self, camera: ICamera):
        """Do camera settings for given camera."""

        # I'm a module!
        self: Union[Module, CameraSettingsMixin]

        # filter
        if self.__camerasettings_filters is not None and self.__camerasettings_filter is not None:
            # get proxy
            log.info('Getting proxy for filter wheel...')
            filters: IFilters = self.proxy(self.__camerasettings_filters, IFilters)

            # set it
            log.info('Setting filter to %s...', self.__camerasettings_filter)
            filters.set_filter(self.__camerasettings_filter).wait()

        # camera settings
        if self.__camerasettings_binning is not None and isinstance(camera, ICameraBinning):
            log.info('Setting binning to %dx%d...', self.__camerasettings_binning, self.__camerasettings_binning)
            camera.set_binning(self.__camerasettings_binning, self.__camerasettings_binning).wait()
        if isinstance(camera, ICameraWindow):
            log.info('Set window to full frame...')
            full_frame = camera.get_full_frame().wait()
            camera.set_window(*full_frame).wait()


__all__ = ['CameraSettingsMixin']
