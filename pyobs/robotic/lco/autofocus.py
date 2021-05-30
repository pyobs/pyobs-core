import logging
import threading
from typing import Union, Tuple

from pyobs.interfaces import ICamera, IRoof, ITelescope, IAcquisition, IAutoFocus
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType
from pyobs.utils.logger import DuplicateFilter

log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ':cannot_run')
cannot_run_logger.addFilter(DuplicateFilter())


class LcoAutoFocusScript(Script):
    """Auto focus script for LCO configs."""

    def __init__(self, roof: Union[str, IRoof] = None, telescope: Union[str, ITelescope] = None,
                 acquisition: Union[str, IAcquisition] = None, autofocus: Union[str, IAutoFocus] = None,
                 count: int = 5, step: float = 0.1, exptime: float = 2.,
                 *args, ** kwargs):
        """Initialize a new LCO auto focus script.

        Args:
            roof: Roof to use
            telescope: Telescope to use
            acquisition: Acquisition to use
            autofocus: Autofocus to use
        """
        Script.__init__(self, *args, **kwargs)

        # store
        self.roof = roof
        self.telescope = telescope
        self.acquisition = acquisition
        self.autofocus = autofocus
        self._count = count
        self._step = step
        self._exptime = exptime

        # get image type
        self.image_type = ImageType.OBJECT
        if self.configuration['type'] == 'BIAS':
            self.image_type = ImageType.BIAS
        elif self.configuration['type'] == 'DARK':
            self.image_type = ImageType.DARK

    def _get_proxies(self) -> Tuple[IRoof, ITelescope, IAcquisition, IAutoFocus]:
        """Get proxies for running the task

        Returns:
            Proxies for roof, telescope, acquisition, and autofocus

        Raises:
            ValueError: If could not get proxies for all modules
        """
        roof: IRoof = self._get_proxy(self.roof, IRoof)
        telescope: ITelescope = self._get_proxy(self.telescope, ITelescope)
        acquisition: IAcquisition = self._get_proxy(self.acquisition, IAcquisition)
        autofocus: IAutoFocus = self._get_proxy(self.autofocus, IAutoFocus)
        return roof, telescope, acquisition, autofocus

    def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if script can run now
        """

        # get proxies
        roof, telescope, acquisition, autofocus = self._get_proxies()

        # need everything
        if roof is None or telescope is None or autofocus is None:
            cannot_run_logger.info('Cannot run task, no roof, telescope, or auto-focusser found.')
            return False

        # acquisition?
        if 'acquisition_config' in self.configuration and 'mode' in self.configuration['acquisition_config'] and \
                self.configuration['acquisition_config']['mode'] == 'ON' and acquisition is None:
            cannot_run_logger.info('Cannot run task, no acquisition found.')
            return False

        # we need an open roof and a working telescope
        if roof.is_ready().wait():
            cannot_run_logger.info('Cannot run task, roof not ready.')
            return False
        if telescope.is_ready().wait():
            cannot_run_logger.info('Cannot run task, telescope not ready.')
            return False

        # seems alright
        return True

    def run(self, abort_event: threading.Event):
        """Run script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """

        # get proxies
        roof, telescope, acquisition, autofocus = self._get_proxies()

        # got a target?
        target = self.configuration['target']
        log.info('Moving to target %s...', target['name'])
        telescope.move_radec(target['ra'], target['dec']).wait()

        # acquisition?
        if 'acquisition_config' in self.configuration and 'mode' in self.configuration['acquisition_config'] and \
                self.configuration['acquisition_config']['mode'] == 'ON':
            # TODO: unfortunately this never happens, since the LCO portal forces acquisition mode to OFF, see:
            # observation_portal/requestgroups/serializers.py:288 in portal code:
            # if data['type'] in ['LAMP_FLAT', 'ARC', 'AUTO_FOCUS', 'NRES_BIAS', 'NRES_DARK', 'BIAS', 'DARK', 'SCRIPT']:
            #     These types of observations should only ever be set to guiding mode OFF, but the acquisition modes for
            #     spectrographs won't necessarily have that mode. Force OFF here.
            #     data['acquisition_config']['mode'] = AcquisitionConfig.OFF

            # get exposure time
            acq = self.configuration['acquisition_config']
            exp_time = acq['exposure_time'] if 'exposure_time' in acq else 2.

            # do acquisition
            log.info('Performing acquisition...')
            acquisition.acquire_target(exp_time).wait()

        # do auto focus
        autofocus.auto_focus(self._count, self._step, self._exptime).wait()


__all__ = ['LcoAutoFocusScript']
