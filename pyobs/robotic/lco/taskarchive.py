import logging
from typing import Dict, Optional, Any
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from .portal import Portal
from .task import LcoTask
from .. import Task
from ..scheduler.constraints import (
    Constraint,
    AirmassConstraint,
    MoonIlluminationConstraint,
    MoonSeparationConstraint,
    TimeConstraint,
    SolarElevationConstraint,
)
from ..scheduler.targets import SiderealTarget

log = logging.getLogger(__name__)


class LcoTaskArchive(TaskArchive):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        url: str,
        token: str,
        instrument_type: str | list[str],
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            token: Authorization token for portal
            instrument_type: Type of instrument to use.
            scripts: External scripts
        """
        TaskArchive.__init__(self, **kwargs)

        # portal
        self._portal = Portal(url, token)

        # store stuff
        self._url = url
        self._token = token
        instrument_type = [instrument_type] if isinstance(instrument_type, str) else instrument_type
        self._instrument_type = [it.lower() for it in instrument_type]

        # buffers in case of errors
        self._last_changed: Optional[Time] = None

        # task list
        self._tasks: Dict[str, LcoTask] = {}

    async def last_changed(self) -> Optional[Time]:
        """Returns time when last time any blocks changed."""

        # try to update time
        try:
            # get data
            self._last_changed = await self._portal.last_changed()

        finally:
            # even in case of errors, return last time
            return self._last_changed

    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """

        # get data
        schedulable = await self._portal.schedulable_requests()

        # get proposal priorities
        proposals = await self._portal.proposals()
        tac_priorities = {p["id"]: p["tac_priority"] for p in proposals}

        # loop all request groups
        tasks: list[Task] = []
        for group in schedulable:
            # get base priority, which is tac_priority * ipp_value
            proposal = group["proposal"]
            if proposal not in tac_priorities:
                log.error('Could not find proposal "%s".', proposal)
                continue
            base_priority = group["ipp_value"] * tac_priorities[proposal]

            # loop all requests in group
            for req in group["requests"]:
                # still pending?
                if req["state"] != "PENDING":
                    continue

                # duration
                duration = req["duration"] * u.second

                # time constraints
                time_constraints = [TimeConstraint(Time(wnd["start"]), Time(wnd["end"])) for wnd in req["windows"]]

                # loop configs
                for cfg in req["configurations"]:
                    # get instrument and check, whether we schedule it
                    instrument = cfg["instrument_type"]
                    if instrument.lower() not in self._instrument_type:
                        continue

                    # target
                    t = cfg["target"]
                    if "ra" in t and "dec" in t:
                        target = SkyCoord(t["ra"] * u.deg, t["dec"] * u.deg, frame=t["type"].lower())
                        target_name = t["name"]
                    else:
                        log.warning("Unsupported coordinate type.")
                        continue

                    # constraints
                    c = cfg["constraints"]
                    constraints: list[Constraint] = []
                    if "max_airmass" in c and c["max_airmass"] is not None:
                        constraints.append(AirmassConstraint(c["max_airmass"]))
                    if "min_lunar_distance" in c and c["min_lunar_distance"] is not None:
                        constraints.append(MoonSeparationConstraint(c["min_lunar_distance"]))
                    if "max_lunar_phase" in c and c["max_lunar_phase"] is not None:
                        constraints.append(MoonIlluminationConstraint(c["max_lunar_phase"]))
                        # if max lunar phase <= 0.4 (which would be DARK), we also enforce the sun to be <-18 degrees
                        if c["max_lunar_phase"] <= 0.4:
                            constraints.append(SolarElevationConstraint(-18.0))

                    # priority is base_priority times duration in minutes
                    # priority = base_priority * duration.value / 60.
                    priority = base_priority

                    # create task
                    task = LcoTask(
                        id=req["id"],
                        name=group["name"],
                        duration=duration,
                        priority=priority,
                        constraints=[*constraints, *time_constraints],
                        config={"request": req},
                        target=SiderealTarget(target_name, target),
                    )
                    tasks.append(task)

        # return blocks
        return tasks


__all__ = ["LcoTaskArchive"]
