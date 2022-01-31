import logging
from typing import Union, Tuple, Optional, Any

from pyobs.interfaces import IRoof, ITelescope, IAcquisition, IAutoFocus
from pyobs.robotic import TaskRunner
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType
from pyobs.utils.logger import DuplicateFilter
from robotic import TaskSchedule, TaskArchive

log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ":cannot_run")
cannot_run_logger.addFilter(DuplicateFilter())


class LcoAutoFocusScript(Script):
    """Auto focus script for LCO configs."""

    def __init__(
        self,
        roof: Optional[Union[str, IRoof]] = None,
        telescope: Optional[Union[str, ITelescope]] = None,
        acquisition: Optional[Union[str, IAcquisition]] = None,
        autofocus: Optional[Union[str, IAutoFocus]] = None,
        count: int = 5,
        step: float = 0.1,
        exptime: float = 2.0,
        **kwargs: Any,
    ):
        """Initialize a new LCO auto focus script.

        Args:
            roof: Roof to use
            telescope: Telescope to use
            acquisition: Acquisition to use
            autofocus: Autofocus to use
        """
        Script.__init__(self, **kwargs)

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
        if self.configuration["type"] == "BIAS":
            self.image_type = ImageType.BIAS
        elif self.configuration["type"] == "DARK":
            self.image_type = ImageType.DARK

    async def _get_proxies(
        self,
    ) -> Tuple[Optional[IRoof], Optional[ITelescope], Optional[IAcquisition], Optional[IAutoFocus]]:
        """Get proxies for running the task

        Returns:
            Proxies for roof, telescope, acquisition, and autofocus

        Raises:
            ValueError: If could not get proxies for all modules
        """
        roof = await self.comm.safe_proxy(self.roof, IRoof)
        telescope = await self.comm.safe_proxy(self.telescope, ITelescope)
        acquisition = await self.comm.safe_proxy(self.acquisition, IAcquisition)
        autofocus = await self.comm.safe_proxy(self.autofocus, IAutoFocus)
        return roof, telescope, acquisition, autofocus

    async def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if script can run now
        """

        # get proxies
        roof, telescope, acquisition, autofocus = await self._get_proxies()

        # need everything
        if roof is None or telescope is None or autofocus is None:
            cannot_run_logger.info("Cannot run task, no roof, telescope, or auto-focusser found.")
            return False

        # acquisition?
        if (
            "acquisition_config" in self.configuration
            and "mode" in self.configuration["acquisition_config"]
            and self.configuration["acquisition_config"]["mode"] == "ON"
            and acquisition is None
        ):
            cannot_run_logger.info("Cannot run task, no acquisition found.")
            return False

        # we need an open roof and a working telescope
        if not await roof.is_ready():
            cannot_run_logger.info("Cannot run task, roof not ready.")
            return False
        if not await telescope.is_ready():
            cannot_run_logger.info("Cannot run task, telescope not ready.")
            return False

        # seems alright
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # get proxies
        roof, telescope, acquisition, autofocus = await self._get_proxies()
        if telescope is None:
            raise ValueError("No telescope given.")

        # got a target?
        target = self.configuration["target"]
        log.info("Moving to target %s...", target["name"])
        await telescope.move_radec(target["ra"], target["dec"])

        # acquisition?
        if (
            "acquisition_config" in self.configuration
            and "mode" in self.configuration["acquisition_config"]
            and self.configuration["acquisition_config"]["mode"] == "ON"
        ):
            # TODO: unfortunately this never happens, since the LCO portal forces acquisition mode to OFF, see:
            # observation_portal/requestgroups/serializers.py:288 in portal code:
            # if data['type'] in ['LAMP_FLAT', 'ARC', 'AUTO_FOCUS', 'NRES_BIAS', 'NRES_DARK', 'BIAS', 'DARK', 'SCRIPT']:
            #     These types of observations should only ever be set to guiding mode OFF, but the acquisition modes for
            #     spectrographs won't necessarily have that mode. Force OFF here.
            #     data['acquisition_config']['mode'] = AcquisitionConfig.OFF

            # do acquisition
            if acquisition is None:
                raise ValueError("No acquisition given.")
            log.info("Performing acquisition...")
            await acquisition.acquire_target()

        # do auto focus
        if autofocus is None:
            raise ValueError("No autofocus given.")
        await autofocus.auto_focus(self._count, self._step, self._exptime)


__all__ = ["LcoAutoFocusScript"]
