"""Tests for the IRobotic/IRoboticScheduler interfaces' state dataclasses."""

from __future__ import annotations

from pyobs.comm.xmpp.serializer import _dataclass_to_xml, _xml_to_dataclass
from pyobs.interfaces import (
    IRobotic,
    IRoboticScheduler,
    RoboticState,
    RoboticTask,
    SchedulerState,
)
from pyobs.robotic.observation import Observation, ObservationState
from pyobs.robotic.task import Task
from pyobs.utils.time import Time


def test_has_own_state() -> None:
    assert IRobotic.has_own_state() is True
    assert IRoboticScheduler.has_own_state() is True


def test_robotic_task_defaults() -> None:
    task = RoboticTask(id=1, name="foo")
    assert task.target is None
    assert task.start is None
    assert task.end is None
    assert task.obsnum is None
    assert task.state is None
    assert task.priority is None


def test_robotic_state_roundtrip_with_current_and_next() -> None:
    ns = f"urn:pyobs:state:IRobotic:{IRobotic.version}"
    current = RoboticTask(
        id=1, name="foo", target="M31", start=Time.now(), end=Time.now(), obsnum="20260830-001", state="in_progress"
    )
    next_task = RoboticTask(id=2, name="bar", state="pending")
    state = RoboticState(current=current, next=next_task, cant_run_reason="weather bad")

    xml = _dataclass_to_xml(state, ns)
    restored = _xml_to_dataclass(xml, RoboticState)

    # Time round-trips through isot text on the wire, which drops sub-millisecond precision --
    # compare that text form rather than the Time objects themselves.
    assert restored.current is not None
    assert current.start is not None and current.end is not None
    assert restored.current.start is not None and restored.current.end is not None
    assert restored.current.start.isot == current.start.isot
    assert restored.current.end.isot == current.end.isot
    restored.current.start = restored.current.end = current.start = current.end = None
    assert restored.current == current
    assert restored.next == next_task
    assert restored.cant_run_reason == "weather bad"


def test_robotic_state_roundtrip_with_none_current_and_next() -> None:
    ns = f"urn:pyobs:state:IRobotic:{IRobotic.version}"
    state = RoboticState()

    xml = _dataclass_to_xml(state, ns)
    restored = _xml_to_dataclass(xml, RoboticState)

    assert restored.current is None
    assert restored.next is None
    assert restored.cant_run_reason is None


def test_scheduler_state_roundtrip() -> None:
    ns = f"urn:pyobs:state:IRoboticScheduler:{IRoboticScheduler.version}"
    state = SchedulerState(last_reschedule=Time.now())

    xml = _dataclass_to_xml(state, ns)
    restored = _xml_to_dataclass(xml, SchedulerState)

    assert restored.last_reschedule is not None
    assert state.last_reschedule is not None
    assert restored.last_reschedule.isot == state.last_reschedule.isot


def test_scheduler_state_roundtrip_none_last_reschedule() -> None:
    ns = f"urn:pyobs:state:IRoboticScheduler:{IRoboticScheduler.version}"
    state = SchedulerState()

    xml = _dataclass_to_xml(state, ns)
    restored = _xml_to_dataclass(xml, SchedulerState)

    assert restored.last_reschedule is None


def test_robotic_task_from_observation() -> None:
    task = Task(id="t1", name="task1", priority=3.0)
    obs = Observation(
        id=1,
        task=task,
        start="2026-08-30T10:00:00",
        end="2026-08-30T10:05:00",
        state=ObservationState.PENDING,
        priority=3.0,
        obsnum="20260830-002",
    )

    rt = RoboticTask.from_observation(obs)

    assert rt.id == "t1"
    assert rt.name == "task1"
    assert rt.target is None
    assert rt.obsnum == "20260830-002"
    assert rt.state == "pending"
    assert rt.priority == 3.0
    assert isinstance(rt.start, Time)
    assert isinstance(rt.end, Time)


def test_robotic_task_from_observation_with_resolved_target() -> None:
    from pyobs.robotic.scheduler.targets.siderealtarget import SiderealTarget

    task = Task(id="t1", name="task1")
    target = SiderealTarget(name="M31", ra=10.68, dec=41.27)
    obs = Observation(
        id=1,
        task=task,
        start="2026-08-30T10:00:00",
        end="2026-08-30T10:05:00",
        state=ObservationState.PENDING,
        target=target,
    )

    rt = RoboticTask.from_observation(obs)

    assert rt.target == "M31"
