import logging
from typing import cast

from pyobs.interfaces import IRoof, ITelescope, IAcquisition, IAutoFocus, IPointingRaDec
from pyobs.robotic.lco.scripts import LcoScript
from pyobs.robotic.task import TaskData
from pyobs.utils.logger import DuplicateFilter

log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ":cannot_run")
cannot_run_logger.addFilter(DuplicateFilter())


class LcoAutoFocusScript(LcoScript):
    """Auto focus script for LCO configs."""

    roof: str | None = None
    telescope: str | None = None
    acquisition: str | None = None
    autofocus: str | None = None
    count: int = 5
    step: float = 0.1
    exptime: float = 2.0

    async def _get_proxies(
        self, data: TaskData
    ) -> tuple[IRoof | None, ITelescope | None, IAcquisition | None, IAutoFocus | None]:
        """Get proxies for running the task

        Returns:
            Proxies for the roof, telescope, acquisition, and autofocus

        Raises:
            ValueError: Could not get proxies for all modules
        """
        comm = self.__comm(data)
        roof = await comm.safe_proxy(self.roof, IRoof)
        telescope = await comm.safe_proxy(self.telescope, ITelescope)
        acquisition = await comm.safe_proxy(self.acquisition, IAcquisition)
        autofocus = await comm.safe_proxy(self.autofocus, IAutoFocus)
        return roof, telescope, acquisition, autofocus

    async def can_run(self, data: TaskData) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if the script can run now
        """

        # get proxies
        roof, telescope, acquisition, autofocus = await self._get_proxies(data)

        # need everything
        if roof is None or telescope is None or autofocus is None:
            cannot_run_logger.info("Cannot run task, no roof, telescope, or auto-focusser found.")
            return False

        # acquisition?
        cfg = self.request.configurations[0]
        if cfg.acquisition_config is not None and cfg.acquisition_config.mode == "ON" and acquisition is None:
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

    async def run(self, data: TaskData) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # get proxies
        roof, telescope, acquisition, autofocus = await self._get_proxies(data)
        if telescope is None:
            raise ValueError("No telescope given.")

        # got a target?
        cfg = self.request.configurations[0]
        if isinstance(telescope, IPointingRaDec):
            log.info("Moving to target %s...", cfg.target.name)
            await telescope.move_radec(cfg.target.ra, cfg.target.dec)
        else:
            raise ValueError("Invalid telescope.")

        # acquisition?
        if cfg.acquisition_config is not None and cfg.acquisition_config.mode == "ON":
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

        # perform auto-focus
        if autofocus is None:
            raise ValueError("No autofocus given.")
        await autofocus.auto_focus(self.count, self.step, self.exptime)

        # finally, stop telescope
        await cast(ITelescope, telescope).stop_motion()


__all__ = ["LcoAutoFocusScript"]
