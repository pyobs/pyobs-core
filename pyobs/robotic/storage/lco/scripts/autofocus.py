import logging

from pyobs.interfaces import IAcquisition, IAutoFocus, IPointingRaDec, IReady, IRoof, ITelescope
from pyobs.robotic.task import TaskData
from pyobs.utils.logger import DuplicateFilter

from .script import LcoScript

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

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if the script can run now
        """

        # need everything
        if not await self.comm.has_proxy(self.roof, IRoof):
            cannot_run_logger.info("No roof found.")
            return False
        if not await self.comm.has_proxy(self.telescope, ITelescope):
            cannot_run_logger.info("No telescope found.")
            return False
        if not await self.comm.has_proxy(self.autofocus, IAutoFocus):
            cannot_run_logger.info("No acquisition found.")
            return False

        # acquisition?
        cfg = self.request.configurations[0]
        if (
            cfg.acquisition_config is not None
            and cfg.acquisition_config.mode == "ON"
            and not await self.comm.has_proxy(self.acquisition, IAcquisition)
        ):
            cannot_run_logger.info("Cannot run task, no acquisition found.")
            return False

        # we need an open roof and a working telescope
        async with self.comm.proxy(self.roof, IRoof) as roof, self.comm.proxy(self.telescope, ITelescope) as telescope:
            roof_ready = roof.get_state(IReady)
            if roof_ready is None or not roof_ready.ready:
                cannot_run_logger.info("Cannot run task, roof not ready.")
                return False
            tel_ready = telescope.get_state(IReady)
            if tel_ready is None or not tel_ready.ready:
                cannot_run_logger.info("Cannot run task, telescope not ready.")
                return False

        # seems alright
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # got a target?
        cfg = self.request.configurations[0]
        async with self.comm.proxy(self.telescope, IPointingRaDec) as telescope:
            log.info("Moving to target %s...", cfg.target.name)
            await telescope.move_radec(cfg.target.ra, cfg.target.dec)

        # acquisition?
        if cfg.acquisition_config is not None and cfg.acquisition_config.mode == "ON":
            # TODO: unfortunately this never happens, since the LCO portal forces acquisition mode to OFF, see:
            # observation_portal/requestgroups/serializers.py:288 in portal code:
            # if data['type'] in ['LAMP_FLAT', 'ARC', 'AUTO_FOCUS', 'NRES_BIAS', 'NRES_DARK', 'BIAS', 'DARK', 'SCRIPT']:
            #     These types of observations should only ever be set to guiding mode OFF, but the acquisition modes for
            #     spectrographs won't necessarily have that mode. Force OFF here.
            #     data['acquisition_config']['mode'] = AcquisitionConfig.OFF

            # do acquisition
            if self.acquisition is None:
                raise ValueError("No acquisition given.")
            log.info("Performing acquisition...")
            async with self.comm.proxy(self.acquisition, IAcquisition) as acquisition:
                await acquisition.acquire_target()

        # perform auto-focus
        if self.autofocus is None:
            raise ValueError("No autofocus given.")
        async with self.comm.proxy(self.autofocus, IAutoFocus) as autofocus:
            await autofocus.auto_focus(self.count, self.step, self.exptime)

        # finally, stop telescope
        async with self.comm.proxy(self.telescope, ITelescope) as telescope:
            log.info("Stopping telescope...")
            await telescope.stop_motion()


__all__ = ["LcoAutoFocusScript"]
