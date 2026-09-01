import asyncio
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest

from pyobs.comm import Comm
from pyobs.events import GoodWeatherEvent, TaskFailedEvent, TaskFinishedEvent, TaskStartedEvent
from pyobs.interfaces import IRoboticScheduler, IRunning
from pyobs.modules.robotic import Scheduler
from pyobs.modules.robotic.scheduler import _class_accepts_param
from pyobs.robotic import ObservationArchive, Task, TaskArchive
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.scheduler import TaskScheduler
from pyobs.robotic.scheduler.astroplanscheduler import AstroplanScheduler
from pyobs.robotic.scheduler.ondemandscheduler import OnDemandScheduler
from pyobs.robotic.storage.lco.observationarchive import LcoObservationArchive
from pyobs.robotic.storage.portal.observationarchive import PortalObservationArchive
from pyobs.robotic.task import TaskData
from pyobs.utils.time import Time


class DummyTask(Task):
    async def can_run(self, data: TaskData | None) -> bool:
        return True

    @property
    def can_start_late(self) -> bool:
        return False

    async def run(self, data: TaskData | None) -> None:
        pass

    def is_finished(self) -> bool:
        return False


def test_compare_block_lists() -> None:
    # create lists of tasks
    tasks: list[Task] = []
    for i in range(10):
        tasks.append(DummyTask(id=i, name=str(i), duration=100))

    # create two lists from these with some overlap
    tasks1 = tasks[:7]
    tasks2 = tasks[5:]

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(tasks1, tasks2)

    # names1 should contain 0, 1, 2, 3, 4
    assert set(unique1) == {0, 1, 2, 3, 4}

    # names2 should contain 7, 8, 9
    assert set(unique2) == {7, 8, 9}

    # create two lists from these with no overlap
    tasks1 = tasks[:5]
    tasks2 = tasks[5:]

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(tasks1, tasks2)

    # names1 should contain 0, 1, 2, 3, 4
    assert set(unique1) == {0, 1, 2, 3, 4}

    # names2 should contain 5, 6, 7, 8, 9
    assert set(unique2) == {5, 6, 7, 8, 9}

    # create two identical lists
    tasks1 = tasks
    tasks2 = tasks

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(tasks1, tasks2)

    # both lists should be empty
    assert len(unique1) == 0
    assert len(unique2) == 0


# ── helpers ──────────────────────────────────────────────────────────────────


def make_scheduler(**kwargs) -> Scheduler:
    comm = MagicMock(spec=Comm)
    task_archive = kwargs.pop("tasks", None)
    if task_archive is None:
        task_archive = AsyncMock(spec=TaskArchive)
    schedule_archive = kwargs.pop("schedule", None)
    if schedule_archive is None:
        schedule_archive = AsyncMock(spec=ObservationArchive)
    task_scheduler = kwargs.pop("scheduler", None)
    if task_scheduler is None:
        task_scheduler = MagicMock(spec=TaskScheduler)
    return Scheduler(scheduler=task_scheduler, tasks=task_archive, schedule=schedule_archive, comm=comm, **kwargs)


def make_obs(task: Task, start: str, end: str) -> Observation:
    return Observation(task=task, start=start, end=end, state=ObservationState.PENDING)


def make_async_gen(items):
    async def gen(*args, **kwargs):
        for item in items:
            yield item

    return gen


def _state_for(mock: AsyncMock, interface: object) -> object:
    for call in reversed(mock.await_args_list):
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


# ── __init__ ─────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    scheduler = make_scheduler()
    assert scheduler._running is True
    assert scheduler._initial_update_done is False
    assert scheduler._need_update is False
    assert scheduler._tasks == []
    assert scheduler._projects == []
    assert scheduler._safety_time == 300 * u.second


# ── _class_accepts_param (kwarg-injection matrix) ────────────────────────────
#
# Pins which schedule/scheduler classes get which auto-injected kwarg -- injecting
# unconditionally used to rely on the target silently absorbing an unwanted kwarg, which stopped
# being true once Object.__init__ started forwarding leftovers to object.__init__(). Regression
# coverage for the auto_update bug found in PR #776 review: dropping it unconditionally would have
# re-enabled PortalObservationArchive's polling loop in two live fleets.


@pytest.mark.parametrize(
    "class_path,param_name,expected",
    [
        ("pyobs.robotic.storage.portal.observationarchive.PortalObservationArchive", "auto_update", True),
        ("pyobs.robotic.storage.lco.observationarchive.LcoObservationArchive", "auto_update", False),
        ("pyobs.robotic.scheduler.ondemandscheduler.OnDemandScheduler", "observation_archive", True),
        ("pyobs.robotic.scheduler.astroplanscheduler.AstroplanScheduler", "observation_archive", False),
    ],
)
def test_class_accepts_param_dict_config(class_path: str, param_name: str, expected: bool) -> None:
    assert _class_accepts_param({"class": class_path}, param_name) is expected


@pytest.mark.parametrize(
    "klass,param_name,expected",
    [
        (PortalObservationArchive, "auto_update", True),
        (LcoObservationArchive, "auto_update", False),
        (OnDemandScheduler, "observation_archive", True),
        (AstroplanScheduler, "observation_archive", False),
    ],
)
def test_class_accepts_param_bare_class(klass: type, param_name: str, expected: bool) -> None:
    assert _class_accepts_param(klass, param_name) is expected


def test_class_accepts_param_dict_without_class_key_is_false() -> None:
    assert _class_accepts_param({}, "auto_update") is False


def test_class_accepts_param_unresolvable_class_path_is_false() -> None:
    assert _class_accepts_param({"class": "not.a.real.module.Class"}, "auto_update") is False


def test_init_injects_auto_update_false_for_backend_observation_archive() -> None:
    # regression test for the bug found in PR #776 review: dropping auto_update=False
    # unconditionally re-enabled this 5s polling loop in two live fleet configs
    scheduler = make_scheduler(
        schedule={
            "class": "pyobs.robotic.storage.portal.observationarchive.PortalObservationArchive",
            "url": "http://x",
            "token": "t",
        }
    )
    has_poller = any(bg._func.__name__ == "_check_for_changes" for bg, _ in scheduler._schedule._background_tasks)
    assert has_poller is False


# ── open ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_registers_events_and_publishes_state(mocker) -> None:
    from pyobs.modules import Module

    scheduler = make_scheduler()
    scheduler._comm.register_event = AsyncMock()
    scheduler._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await scheduler.open()

    registered = [c.args[0] for c in scheduler._comm.register_event.await_args_list]
    assert TaskStartedEvent in registered
    assert TaskFinishedEvent in registered
    assert TaskFailedEvent in registered
    assert GoodWeatherEvent in registered
    state = _state_for(scheduler._comm.set_state, IRunning)
    assert state.running is True


# ── start / stop ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_sets_running() -> None:
    scheduler = make_scheduler()
    scheduler._running = False
    scheduler._comm.set_state = AsyncMock()

    await scheduler.start()

    assert scheduler._running is True
    state = _state_for(scheduler._comm.set_state, IRunning)
    assert state.running is True


@pytest.mark.asyncio
async def test_stop_clears_running() -> None:
    scheduler = make_scheduler()
    scheduler._comm.set_state = AsyncMock()

    await scheduler.stop()

    assert scheduler._running is False
    state = _state_for(scheduler._comm.set_state, IRunning)
    assert state.running is False


# ── _update_schedule ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_schedule_downloads_tasks_and_projects() -> None:
    scheduler = make_scheduler()
    task = DummyTask(id=1, name="t1", duration=100)
    scheduler._task_archive.get_schedulable_tasks = AsyncMock(return_value=[task])
    scheduler._task_archive.get_projects = AsyncMock(return_value=[])

    await scheduler._update_schedule()

    assert scheduler._tasks == [task]
    assert scheduler._initial_update_done is True
    assert scheduler._need_update is True  # first update, list changed from [] to [task]


@pytest.mark.asyncio
async def test_update_schedule_no_change_skips_update() -> None:
    scheduler = make_scheduler()
    task = DummyTask(id=1, name="t1", duration=100)
    scheduler._tasks = [task]
    scheduler._task_archive.get_schedulable_tasks = AsyncMock(return_value=[task])
    scheduler._task_archive.get_projects = AsyncMock(return_value=[])

    await scheduler._update_schedule()

    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_update_schedule_detects_added_tasks() -> None:
    scheduler = make_scheduler()
    task1 = DummyTask(id=1, name="t1", duration=100)
    task2 = DummyTask(id=2, name="t2", duration=100)
    scheduler._tasks = [task1]
    scheduler._task_archive.get_schedulable_tasks = AsyncMock(return_value=[task1, task2])
    scheduler._task_archive.get_projects = AsyncMock(return_value=[])

    await scheduler._update_schedule()

    assert scheduler._need_update is True
    assert scheduler._tasks == [task1, task2]


@pytest.mark.asyncio
async def test_update_schedule_only_current_task_removed_skips_update() -> None:
    scheduler = make_scheduler()
    task1 = DummyTask(id=1, name="t1", duration=100)
    scheduler._tasks = [task1]
    scheduler._last_task_id = 1
    scheduler._task_archive.get_schedulable_tasks = AsyncMock(return_value=[])
    scheduler._task_archive.get_projects = AsyncMock(return_value=[])

    await scheduler._update_schedule()

    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_update_schedule_removed_task_triggers_update_without_consulting_schedule_cache() -> None:
    # PortalObservationArchive's get_schedule() is a permanently-empty cache by construction
    # (Scheduler drives it via auto_update=False) -- a removal must trigger a reschedule
    # regardless, and must not even consult the cache (the removed gate used to, and always found
    # it empty, which is exactly how this bug hid).
    scheduler = make_scheduler()
    task1 = DummyTask(id=1, name="t1", duration=100)
    scheduler._tasks = [task1]
    scheduler._last_task_id = None  # removed task is not the "current" one
    scheduler._task_archive.get_schedulable_tasks = AsyncMock(return_value=[])
    scheduler._task_archive.get_projects = AsyncMock(return_value=[])
    scheduler._schedule.get_schedule = AsyncMock(return_value=ObservationList())

    await scheduler._update_schedule()

    assert scheduler._need_update is True
    scheduler._schedule.get_schedule.assert_not_awaited()


# ── _schedule_worker ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_schedule_worker_skips_when_no_update_needed(mocker) -> None:
    scheduler = make_scheduler()
    scheduler._need_update = False
    scheduler._initial_update_done = True
    scheduler._schedule.clear_schedule = AsyncMock()

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    scheduler._schedule.clear_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_schedule_worker_skips_before_initial_update_done(mocker) -> None:
    scheduler = make_scheduler()
    scheduler._need_update = True
    scheduler._initial_update_done = False
    scheduler._schedule.clear_schedule = AsyncMock()

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    scheduler._schedule.clear_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_schedule_worker_schedules_and_submits_tasks(mocker) -> None:
    scheduler = make_scheduler(min_safety_time=1.0)
    scheduler._need_update = True
    scheduler._initial_update_done = True
    scheduler._schedule.get_current_observation = AsyncMock(return_value=None)
    scheduler._schedule.clear_schedule = AsyncMock()
    scheduler._schedule.add_observations = AsyncMock()

    task = DummyTask(id=1, name="t1", duration=100)
    obs1 = make_obs(task, "2024-01-01T00:00:00", "2024-01-01T00:05:00")
    obs2 = make_obs(task, "2024-01-01T00:05:00", "2024-01-01T00:10:00")
    scheduler._scheduler.schedule = make_async_gen([obs1, obs2])

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    scheduler._schedule.clear_schedule.assert_awaited_once()
    assert scheduler._schedule.add_observations.await_count == 2
    first_call_arg = scheduler._schedule.add_observations.await_args_list[0].args[0]
    assert list(first_call_arg) == [obs1]
    second_call_arg = scheduler._schedule.add_observations.await_args_list[1].args[0]
    assert list(second_call_arg) == [obs2]


@pytest.mark.asyncio
async def test_schedule_worker_uses_running_observation_end_as_start(mocker) -> None:
    scheduler = make_scheduler()
    scheduler._need_update = True
    scheduler._initial_update_done = True
    scheduler._safety_time = 0 * u.second
    scheduler._schedule_start = Time.now() + 3600 * u.second  # far in the future

    task = DummyTask(id=1, name="t1", duration=100)
    running_end = Time.now() + 60 * u.second  # ends before the scheduled start
    running_obs = make_obs(task, str(Time.now().isot), str(running_end.isot))
    scheduler._schedule.get_current_observation = AsyncMock(return_value=running_obs)
    scheduler._schedule.clear_schedule = AsyncMock()
    scheduler._schedule.add_observations = AsyncMock()
    scheduler._scheduler.schedule = make_async_gen([])

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    used_start = scheduler._schedule.clear_schedule.await_args.args[0]
    assert abs((used_start - running_end).sec) < 1.0


@pytest.mark.asyncio
async def test_schedule_worker_stops_early_when_update_requested_mid_loop(mocker) -> None:
    # First pass: yields obs1 (submitted as the first task), then obs2 -- but a concurrent
    # update request lands between the two, so obs2 gets appended to scheduled_tasks but the
    # loop breaks before it can be submitted as part of the "remaining tasks" batch. A second,
    # unaborted pass (triggered by the "continue") then runs to completion with nothing to
    # schedule. The key invariant: obs2 never appears in any add_observations() call.
    scheduler = make_scheduler()
    scheduler._need_update = True
    scheduler._initial_update_done = True
    scheduler._schedule.get_current_observation = AsyncMock(return_value=None)
    scheduler._schedule.clear_schedule = AsyncMock()
    scheduler._schedule.add_observations = AsyncMock()

    task = DummyTask(id=1, name="t1", duration=100)
    obs1 = make_obs(task, "2024-01-01T00:00:00", "2024-01-01T00:05:00")
    obs2 = make_obs(task, "2024-01-01T00:05:00", "2024-01-01T00:10:00")

    gen_call_count = 0

    async def gen(*args, **kwargs):
        nonlocal gen_call_count
        gen_call_count += 1
        if gen_call_count > 1:
            return
        yield obs1
        # simulate a concurrent request landing between the two yields
        scheduler._need_update = True
        yield obs2

    scheduler._scheduler.schedule = gen

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    for call in scheduler._schedule.add_observations.await_args_list:
        assert obs2 not in list(call.args[0])
    # the first task still got submitted before the abort was noticed
    assert any(list(call.args[0]) == [obs1] for call in scheduler._schedule.add_observations.await_args_list)


@pytest.mark.asyncio
async def test_schedule_worker_catches_exceptions_and_continues(mocker) -> None:
    scheduler = make_scheduler()
    scheduler._need_update = True
    scheduler._initial_update_done = True
    scheduler._schedule.get_current_observation = AsyncMock(side_effect=RuntimeError("boom"))

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    # should not raise RuntimeError -- caught and logged, then continues to the sleep
    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()


@pytest.mark.asyncio
async def test_schedule_worker_returns_on_cancelled_error_in_try_block(mocker) -> None:
    scheduler = make_scheduler()
    scheduler._need_update = True
    scheduler._initial_update_done = True
    scheduler._schedule.get_current_observation = AsyncMock(side_effect=asyncio.CancelledError())

    async def fake_sleep(t: float) -> None:
        return None

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    # returns cleanly, does not propagate CancelledError past _schedule_worker
    await scheduler._schedule_worker()


# ── run ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_sets_need_update() -> None:
    scheduler = make_scheduler()
    await scheduler.run()
    assert scheduler._need_update is True


# ── _on_task_started ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_on_task_started_ignores_wrong_event_type() -> None:
    scheduler = make_scheduler()
    result = await scheduler._on_task_started(GoodWeatherEvent(), "sender")
    assert result is False
    assert scheduler._current_task_id is None


@pytest.mark.asyncio
async def test_on_task_started_stores_ids() -> None:
    scheduler = make_scheduler()
    result = await scheduler._on_task_started(TaskStartedEvent(name="t", id=42), "sender")
    assert result is True
    assert scheduler._current_task_id == 42
    assert scheduler._last_task_id == 42


@pytest.mark.asyncio
async def test_on_task_started_does_not_trigger_by_default() -> None:
    scheduler = make_scheduler()
    await scheduler._on_task_started(TaskStartedEvent(name="t", id=1), "sender")
    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_on_task_started_triggers_when_configured() -> None:
    scheduler = make_scheduler(trigger_on_task_started=True)
    eta = Time.now() + 300 * u.second
    await scheduler._on_task_started(TaskStartedEvent(name="t", id=1, eta=eta), "sender")
    assert scheduler._need_update is True
    assert abs((scheduler._schedule_start - eta).sec) < 1.0


# ── _on_task_finished ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_on_task_finished_ignores_wrong_event_type() -> None:
    scheduler = make_scheduler()
    result = await scheduler._on_task_finished(GoodWeatherEvent(), "sender")
    assert result is False


@pytest.mark.asyncio
async def test_on_task_finished_resets_current_task() -> None:
    scheduler = make_scheduler()
    scheduler._current_task_id = 1
    result = await scheduler._on_task_finished(TaskFinishedEvent(name="t", id=1), "sender")
    assert result is True
    assert scheduler._current_task_id is None


@pytest.mark.asyncio
async def test_on_task_finished_handles_task_failed_event() -> None:
    """Regression test: _on_task_finished is registered for both TaskFinishedEvent and
    TaskFailedEvent, but TaskFailedEvent is not a subclass of TaskFinishedEvent -- make
    sure a failed task also clears _current_task_id instead of being silently ignored."""
    scheduler = make_scheduler()
    scheduler._current_task_id = 1
    result = await scheduler._on_task_finished(TaskFailedEvent(name="t", id=1), "sender")
    assert result is True
    assert scheduler._current_task_id is None


@pytest.mark.asyncio
async def test_on_task_finished_triggers_when_configured() -> None:
    scheduler = make_scheduler(trigger_on_task_finished=True)
    await scheduler._on_task_finished(TaskFinishedEvent(name="t", id=1), "sender")
    assert scheduler._need_update is True


@pytest.mark.asyncio
async def test_on_task_finished_does_not_trigger_by_default() -> None:
    scheduler = make_scheduler()
    await scheduler._on_task_finished(TaskFinishedEvent(name="t", id=1), "sender")
    assert scheduler._need_update is False


# ── _on_good_weather ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_on_good_weather_ignores_wrong_event_type() -> None:
    scheduler = make_scheduler()
    result = await scheduler._on_good_weather(TaskFinishedEvent(name="t", id=1), "sender")
    assert result is False
    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_on_good_weather_triggers_reschedule() -> None:
    scheduler = make_scheduler()
    eta = Time.now() + 120 * u.second
    result = await scheduler._on_good_weather(GoodWeatherEvent(eta=eta), "sender")
    assert result is True
    assert scheduler._need_update is True
    assert abs((scheduler._schedule_start - eta).sec) < 1.0


# ── abort ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_abort_is_noop() -> None:
    scheduler = make_scheduler()
    # should not raise
    await scheduler.abort()


# ── get_schedule ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_schedule_filters_to_pending_and_in_progress() -> None:
    scheduler = make_scheduler()
    task = DummyTask(id=1, name="t1", duration=100)
    pending = make_obs(task, "2024-01-01T00:00:00", "2024-01-01T00:05:00")
    in_progress = make_obs(task, "2024-01-01T00:05:00", "2024-01-01T00:10:00")
    in_progress.state = ObservationState.IN_PROGRESS
    completed = make_obs(task, "2024-01-01T00:10:00", "2024-01-01T00:15:00")
    completed.state = ObservationState.COMPLETED
    scheduler._schedule.get_schedule = AsyncMock(return_value=ObservationList([completed, pending, in_progress]))

    result = await scheduler.get_schedule()

    assert [r.state for r in result] == ["pending", "in_progress"]


@pytest.mark.asyncio
async def test_get_schedule_sorts_by_start_time() -> None:
    scheduler = make_scheduler()
    task = DummyTask(id=1, name="t1", duration=100)
    later = make_obs(task, "2024-01-01T01:00:00", "2024-01-01T01:05:00")
    earlier = make_obs(task, "2024-01-01T00:00:00", "2024-01-01T00:05:00")
    scheduler._schedule.get_schedule = AsyncMock(return_value=ObservationList([later, earlier]))

    result = await scheduler.get_schedule()

    assert all(r.start is not None for r in result)
    assert [r.start.isot for r in result if r.start is not None] == [earlier.start.isot, later.start.isot]


@pytest.mark.asyncio
async def test_get_schedule_respects_limit() -> None:
    scheduler = make_scheduler()
    task = DummyTask(id=1, name="t1", duration=100)
    obs_list = ObservationList(
        [make_obs(task, f"2024-01-01T{i:02d}:00:00", f"2024-01-01T{i:02d}:05:00") for i in range(5)]
    )
    scheduler._schedule.get_schedule = AsyncMock(return_value=obs_list)

    result = await scheduler.get_schedule(limit=2)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_schedule_caps_limit_at_hard_ceiling() -> None:
    scheduler = make_scheduler()
    task = DummyTask(id=1, name="t1", duration=100)
    base = Time("2024-01-01T00:00:00")
    obs_list = ObservationList(
        [
            Observation(
                task=task,
                start=base + i * u.minute,
                end=base + (i + 1) * u.minute,
                state=ObservationState.PENDING,
            )
            for i in range(scheduler._MAX_SCHEDULE_LIMIT + 10)
        ]
    )
    scheduler._schedule.get_schedule = AsyncMock(return_value=obs_list)

    # more candidates exist than the hard ceiling, so the clamp -- not just the sheer count
    # requested -- is what determines the result size
    result = await scheduler.get_schedule(limit=10_000)

    assert len(result) == scheduler._MAX_SCHEDULE_LIMIT


@pytest.mark.asyncio
async def test_get_schedule_rejects_negative_limit() -> None:
    scheduler = make_scheduler()
    with pytest.raises(ValueError):
        await scheduler.get_schedule(limit=-1)


@pytest.mark.asyncio
async def test_get_schedule_resolves_unresolved_task() -> None:
    """PortalObservationArchive.get_schedule() returns `task` as a bare id -- get_schedule()
    must resolve it via the task archive before mapping to RoboticTask."""
    scheduler = make_scheduler()
    resolved = DummyTask(id=42, name="resolved", duration=100)
    unresolved_obs = Observation(task=42, start="2024-01-01T00:00:00", end="2024-01-01T00:05:00", state="pending")
    scheduler._schedule.get_schedule = AsyncMock(return_value=ObservationList([unresolved_obs]))
    scheduler._task_archive.get_task = AsyncMock(return_value=resolved)

    result = await scheduler.get_schedule()

    scheduler._task_archive.get_task.assert_awaited_once_with(42)
    assert len(result) == 1
    assert result[0].name == "resolved"


@pytest.mark.asyncio
async def test_get_schedule_skips_unresolvable_task() -> None:
    scheduler = make_scheduler()
    unresolved_obs = Observation(task=99, start="2024-01-01T00:00:00", end="2024-01-01T00:05:00", state="pending")
    scheduler._schedule.get_schedule = AsyncMock(return_value=ObservationList([unresolved_obs]))
    scheduler._task_archive.get_task = AsyncMock(return_value=None)

    result = await scheduler.get_schedule()

    assert result == []


# ── SchedulerState publishing ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_scheduler_state(mocker) -> None:
    from pyobs.modules import Module

    scheduler = make_scheduler()
    scheduler._comm.register_event = AsyncMock()
    scheduler._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await scheduler.open()

    state = _state_for(scheduler._comm.set_state, IRoboticScheduler)
    assert state.last_reschedule is None


@pytest.mark.asyncio
async def test_schedule_worker_publishes_last_reschedule(mocker) -> None:
    scheduler = make_scheduler(min_safety_time=1.0)
    scheduler._need_update = True
    scheduler._initial_update_done = True
    scheduler._schedule.get_current_observation = AsyncMock(return_value=None)
    scheduler._schedule.clear_schedule = AsyncMock()
    scheduler._schedule.add_observations = AsyncMock()
    scheduler._comm.set_state = AsyncMock()

    task = DummyTask(id=1, name="t1", duration=100)
    obs1 = make_obs(task, "2024-01-01T00:00:00", "2024-01-01T00:05:00")
    scheduler._scheduler.schedule = make_async_gen([obs1])

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.scheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    state = _state_for(scheduler._comm.set_state, IRoboticScheduler)
    assert state.last_reschedule is not None
