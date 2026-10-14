import pytest

from pyobs.robotic import Observation, Task
from pyobs.robotic.observation import ObservationList, ObservationState
from pyobs.robotic.scheduler import DataProvider
from pyobs.robotic.scheduler.merits import FollowMerit
from pyobs.utils.time import Time


def _obs(task: object, state: ObservationState = ObservationState.COMPLETED) -> Observation:
    now = Time.now()
    return Observation(task=task, start=now, end=now, state=state)


@pytest.mark.parametrize("task_id", [1, "abc"])
def test_task_id_for_task_and_plain_id(task_id: object) -> None:
    assert _obs(Task(id=task_id, name="t", duration=1)).task_id == task_id
    assert _obs(task_id).task_id == task_id


def test_filter_by_task_id_with_task_objects_and_plain_ids() -> None:
    observations = ObservationList([_obs(Task(id=1, name="t", duration=1)), _obs("abc"), _obs("xyz")])

    assert len(observations.filter(task_id=1)) == 1
    assert len(observations.filter(task_id="abc")) == 1
    assert len(observations.filter(task_id="abc", state=ObservationState.COMPLETED)) == 1
    assert len(observations.filter(task_id="nope")) == 0


def test_eq_and_str_with_plain_task_id() -> None:
    now = Time.now()
    a = Observation(task="abc", start=now, end=now)
    b = Observation(task="abc", start=now, end=now)
    c = Observation(task="xyz", start=now, end=now)

    assert a == b
    assert a != c
    assert "#abc" in str(a)


def test_str_with_task_object() -> None:
    assert "t (#1)" in str(_obs(Task(id=1, name="t", duration=1)))


@pytest.mark.asyncio
async def test_follow_merit_with_plain_task_ids() -> None:
    class _Archive:
        async def observations_for_night(self, night: object, *, time: Time | None = None) -> ObservationList:
            assert time is not None
            return ObservationList([_obs("abc")])

    class _Data(DataProvider):
        def __init__(self) -> None:
            self.archive = _Archive()  # type: ignore[assignment]

        def night(self, time: Time) -> object:  # type: ignore[override]
            return None

    task = Task(id=2, name="t", duration=1)
    time = Time.now()
    assert await FollowMerit(task_id="abc")(time, task, _Data()) == 1.0
    assert await FollowMerit(task_id="other")(time, task, _Data()) == 0.0
