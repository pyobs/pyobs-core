import logging
from typing import List, Dict, Optional, Any
from astroplan import (
    TimeConstraint,
    AirmassConstraint,
    ObservingBlock,
    FixedTarget,
    MoonSeparationConstraint,
    MoonIlluminationConstraint,
    AtNightConstraint,
)
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from .portal import Portal
from .task import LcoTask

log = logging.getLogger(__name__)


class LcoTaskArchive(TaskArchive):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        url: str,
        token: str,
        instrument_type: str,
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
        self._instrument_type = instrument_type

        # buffers in case of errors
        self._last_changed: Optional[Time] = None

        # task list
        self._tasks: Dict[str, LcoTask] = {}

    async def open(self) -> None:
        """Open scheduler."""
        await TaskArchive.open(self)

    async def last_changed(self) -> Optional[Time]:
        """Returns time when last time any blocks changed."""

        # try to update time
        try:
            # get data
            self._last_changed = await self._portal.last_changed()

        finally:
            # even in case of errors, return last time
            return self._last_changed

    async def get_schedulable_blocks(self) -> List[ObservingBlock]:
        """Returns list of schedulable blocks.

        Returns:
            List of schedulable blocks
        """

        # get data
        schedulable = await self._portal.schedulable_requests()

        # get proposal priorities
        proposals = await self._portal.proposals()
        tac_priorities = {p["id"]: p["tac_priority"] for p in proposals}

        # loop all request groups
        blocks = []
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
                    if instrument.lower() != self._instrument_type.lower():
                        continue

                    # target
                    t = cfg["target"]
                    target = SkyCoord(t["ra"] * u.deg, t["dec"] * u.deg, frame=t["type"].lower())

                    # constraints
                    c = cfg["constraints"]
                    constraints = []
                    if "max_airmass" in c and c["max_airmass"] is not None:
                        constraints.append(AirmassConstraint(max=c["max_airmass"], boolean_constraint=False))
                    if "min_lunar_distance" in c and c["min_lunar_distance"] is not None:
                        constraints.append(MoonSeparationConstraint(min=c["min_lunar_distance"] * u.deg))
                    if "max_lunar_phase" in c and c["max_lunar_phase"] is not None:
                        constraints.append(MoonIlluminationConstraint(max=c["max_lunar_phase"]))
                        # if max lunar phase <= 0.4 (which would be DARK), we also enforce the sun to be <-18 degrees
                        if c["max_lunar_phase"] <= 0.4:
                            constraints.append(AtNightConstraint.twilight_astronomical())

                    # priority is base_priority times duration in minutes
                    # priority = base_priority * duration.value / 60.
                    priority = base_priority

                    # create block
                    block = ObservingBlock(
                        FixedTarget(target, name=req["id"]),
                        duration,
                        priority,
                        constraints=[*constraints, *time_constraints],
                        configuration={"request": req},
                    )
                    blocks.append(block)

        # return blocks
        return blocks


__all__ = ["LcoTaskArchive"]
