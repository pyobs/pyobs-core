import copy
import logging
from typing import List, Dict, Optional, Any, TypedDict
from astroplan import ObservingBlock
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.observation import Observation
from pyobs.utils.time import Time
from .task import LcoTask
from .taskschedule import LcoTaskSchedule
from .. import ObservationList

log = logging.getLogger(__name__)


class InstrumentConfig(TypedDict):
    optical_elements: dict[str, Any]
    mode: str
    exposure_time: float
    exposure_count: int
    bin_x: int
    bin_y: int


class AcquisitionConfig(TypedDict):
    mode: str


class GuidingConfig(TypedDict):
    mode: str


class Target(TypedDict):
    type: str
    name: str
    ra: float
    dec: float


class Configuration(TypedDict):
    constraints: dict[str, float]
    instrument_configs: list[InstrumentConfig]
    acquisition_config: AcquisitionConfig
    guiding_config: GuidingConfig
    target: Target
    instrument_type: str
    type: str
    priority: int
    configuration_status: dict[str, Any]


class Request(TypedDict):
    id: int
    configurations: list[Configuration]
    windows: list[str]
    duration: float | int
    acceptability_threshold: float


class RequestGroup(TypedDict):
    name: str
    observation_type: str
    request: Request
    start: str | None
    end: str | None


REQUEST: RequestGroup = {
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
                        "mode": "",
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
                "instrument_type": "",
                "type": "BIAS",
                "priority": 1,
                "configuration_status": {},
            }
        ],
        "windows": [],
        "duration": 10,
        "acceptability_threshold": 90.0,
    },
    "start": None,
    "end": None,
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
        self._task = self.get_object(LcoTask, LcoTask, tasks=self, **kwargs)

    async def _init_from_portal(self) -> None:
        pass

    async def last_scheduled(self) -> Optional[Time]:
        return self._last_schedule_time

    async def _update_schedule(self) -> None:
        pass

    async def update_now(self, force: bool = False) -> None:
        pass

    async def get_schedule(self) -> ObservationList:
        if self._task is None:
            return ObservationList()
        return ObservationList([Observation(self._task, Time.now(), Time.now() + TimeDelta(5.0 * u.minute))])

    async def get_task(self, time: Time) -> Observation | None:
        if self._task is None:
            return None
        return Observation(self._task, Time.now(), Time.now() + TimeDelta(5.0 * u.minute))

    async def send_update(self, status_id: int, status: Dict[str, Any]) -> None:
        pass

    async def set_schedule(self, blocks: List[ObservingBlock], start_time: Time) -> None:
        pass


__all__ = ["LcoDummyTaskSchedule"]
