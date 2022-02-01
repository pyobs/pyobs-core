import copy
import logging
from typing import List, Dict, Optional, Any
from astroplan import ObservingBlock
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from .task import LcoTask
from .taskschedule import LcoTaskSchedule

log = logging.getLogger(__name__)


REQUEST = {
    "name": "Test",
    "observation_type": "NORMAL",
    "request": {
        "id": 1,
        "configurations": [
            {
                "constraints": {},
                "instrument_configs": [
                    {
                        "optical_elements": {},
                        "mode": None,
                        "exposure_time": 0.0,
                        "exposure_count": 1,
                        "bin_x": 3,
                        "bin_y": 3,
                    }
                ],
                "acquisition_config": {
                    "mode": "OFF",
                },
                "guiding_config": {
                    "mode": "OFF",
                },
                "target": {
                    "type": "ICRS",
                    "name": "bias",
                    "ra": 0.0,
                    "dec": 0.0,
                },
                "instrument_type": None,
                "type": "BIAS",
                "priority": 1,
                "configuration_status": {},
            }
        ],
        "windows": [],
        "duration": 10,
        "acceptability_threshold": 90.0,
    },
}


class LcoDummyTaskSchedule(LcoTaskSchedule):
    """Dummy scheduler for using the LCO portal"""

    def __init__(
        self,
        instrument_type: str,
        mode: str,
        binning: str,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            mode: Instrument mode
            instrument_type: Instrument type
        """
        LcoTaskSchedule.__init__(self, **kwargs)

        # set some stuff
        self._last_schedule_time = Time.now()

        # instruments
        self.instruments = {
            instrument_type.lower(): {
                "modes": {
                    "readout": {
                        "modes": [
                            {
                                "code": mode,
                                "name": mode,
                                "validation_schema": {"bin_x": {"default": binning}, "bin_y": {"default": binning}},
                            }
                        ]
                    }
                }
            }
        }

        # create task config
        cfg = copy.deepcopy(REQUEST)
        cfg["request"]["configurations"][0]["instrument_configs"][0]["mode"] = mode
        cfg["request"]["configurations"][0]["instrument_type"] = instrument_type
        cfg["start"] = Time.now()
        cfg["end"] = Time.now() + TimeDelta(5.0 * u.minute)

        # create task
        self._task: Optional[LcoTask] = self._create_task(LcoTask, config=cfg)

    async def _init_from_portal(self) -> None:
        pass

    async def last_scheduled(self) -> Optional[Time]:
        return self._last_schedule_time

    async def _update_schedule(self) -> None:
        pass

    async def update_now(self, force: bool = False) -> None:
        pass

    async def get_schedule(self, start_before: Time, end_after: Time, include_running: bool = True) -> Dict[str, Task]:
        return {} if self._task is None else {"task": self._task}

    def get_task(self, time: Time) -> Optional[LcoTask]:
        task = self._task
        self._task = None
        return task

    async def send_update(self, status_id: int, status: Dict[str, Any]) -> None:
        pass

    async def update_schedule(self, blocks: List[ObservingBlock], start_time: Time) -> None:
        pass


__all__ = ["LcoDummyTaskSchedule"]
