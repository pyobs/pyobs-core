from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.interfaces import MotionState
from pyobs.robotic.scripts import Script
from pyobs.robotic.scripts.control.cases import CasesRunner
from pyobs.robotic.scripts.control.conditional import ConditionalRunner
from pyobs.robotic.scripts.control.parallel import ParallelRunner
from pyobs.robotic.scripts.control.selector import SelectorScript
from pyobs.robotic.scripts.control.sequential import SequentialRunner
from pyobs.utils.enums import MotionStatus

# ── helper scripts ────────────────────────────────────────────────────────────


class AlwaysRunScript(Script):
    ran: bool = False

    async def can_run(self, data: Any) -> bool:
        return True

    async def run(self, data: Any) -> None:
        self.ran = True


class NeverRunScript(Script):
    ran: bool = False

    async def can_run(self, data: Any) -> bool:
        return False

    async def run(self, data: Any) -> None:
        self.ran = True


class TrackingScript(Script):
    """Records calls for ordering/parallel verification."""

    order: list[str] = []
    name: str = "unnamed"

    async def can_run(self, data: Any) -> bool:
        return True

    async def run(self, data: Any) -> None:
        self.order.append(self.name)
        await asyncio.sleep(0.01)


# ── SequentialRunner ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sequential_can_run_all_true() -> None:
    runner = SequentialRunner(scripts=[AlwaysRunScript(), AlwaysRunScript()])
    assert await runner.can_run(None) is True


@pytest.mark.asyncio
async def test_sequential_can_run_one_false() -> None:
    runner = SequentialRunner(scripts=[AlwaysRunScript(), NeverRunScript()])
    assert await runner.can_run(None) is False


@pytest.mark.asyncio
async def test_sequential_can_run_check_first_only() -> None:
    """check_all_can_run=False only checks the first script."""
    runner = SequentialRunner(
        scripts=[AlwaysRunScript(), NeverRunScript()],
        check_all_can_run=False,
    )
    assert await runner.can_run(None) is True


@pytest.mark.asyncio
async def test_sequential_runs_all_scripts() -> None:
    s1, s2 = AlwaysRunScript(), AlwaysRunScript()
    runner = SequentialRunner(scripts=[s1, s2])
    await runner.run(None)
    assert s1.ran
    assert s2.ran


@pytest.mark.asyncio
async def test_sequential_skips_scripts_that_cannot_run() -> None:
    s1, s2 = NeverRunScript(), AlwaysRunScript()
    runner = SequentialRunner(scripts=[s1, s2])
    await runner.run(None)
    assert not s1.ran
    assert s2.ran


@pytest.mark.asyncio
async def test_sequential_runs_in_order() -> None:
    order: list[str] = []

    class Ordered(Script):
        n: str

        async def can_run(self, data: Any) -> bool:
            return True

        async def run(self, data: Any) -> None:
            order.append(self.n)

    runner = SequentialRunner(scripts=[Ordered(n="1"), Ordered(n="2"), Ordered(n="3")])
    await runner.run(None)
    assert order == ["1", "2", "3"]


# ── ParallelRunner ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_parallel_can_run_all_true() -> None:
    runner = ParallelRunner(scripts=[AlwaysRunScript(), AlwaysRunScript()])
    assert await runner.can_run(None) is True


@pytest.mark.asyncio
async def test_parallel_can_run_one_false() -> None:
    runner = ParallelRunner(scripts=[AlwaysRunScript(), NeverRunScript()])
    assert await runner.can_run(None) is False


@pytest.mark.asyncio
async def test_parallel_can_run_any_with_check_false() -> None:
    """check_all_can_run=False: passes if any script can run."""
    runner = ParallelRunner(
        scripts=[NeverRunScript(), AlwaysRunScript()],
        check_all_can_run=False,
    )
    assert await runner.can_run(None) is True


@pytest.mark.asyncio
async def test_parallel_runs_all_scripts() -> None:
    s1, s2 = AlwaysRunScript(), AlwaysRunScript()
    runner = ParallelRunner(scripts=[s1, s2])
    await runner.run(None)
    assert s1.ran
    assert s2.ran


@pytest.mark.asyncio
async def test_parallel_skips_scripts_that_cannot_run() -> None:
    s1, s2 = NeverRunScript(), AlwaysRunScript()
    runner = ParallelRunner(scripts=[s1, s2])
    await runner.run(None)
    assert not s1.ran
    assert s2.ran


@pytest.mark.asyncio
async def test_parallel_runs_concurrently() -> None:
    """Scripts run concurrently — both start before either finishes."""
    started: list[str] = []
    finished: list[str] = []

    class Timed(Script):
        n: str

        async def can_run(self, data: Any) -> bool:
            return True

        async def run(self, data: Any) -> None:
            started.append(self.n)
            await asyncio.sleep(0.05)
            finished.append(self.n)

    runner = ParallelRunner(scripts=[Timed(n="A"), Timed(n="B")])
    await runner.run(None)

    assert set(started) == {"A", "B"}
    assert set(finished) == {"A", "B"}
    # both started before either finished (concurrency)
    assert len(started) == 2


@pytest.mark.asyncio
async def test_parallel_exception_does_not_stop_others() -> None:
    """Exception in one script is caught; other scripts still run."""

    class FailingScript(Script):
        async def can_run(self, data: Any) -> bool:
            return True

        async def run(self, data: Any) -> None:
            raise RuntimeError("intentional failure")

    s2 = AlwaysRunScript()
    runner = ParallelRunner(scripts=[FailingScript(), s2])
    await runner.run(None)  # should not raise
    assert s2.ran


# ── CasesRunner ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cases_selects_matching_case() -> None:
    s1, s2 = AlwaysRunScript(), AlwaysRunScript()
    runner = CasesRunner(expression="1", cases={1: s1, 2: s2})
    await runner.run(None)
    assert s1.ran
    assert not s2.ran


@pytest.mark.asyncio
async def test_cases_falls_through_to_else() -> None:
    s_else = AlwaysRunScript()
    runner = CasesRunner(expression="99", cases={1: AlwaysRunScript(), "else": s_else})
    await runner.run(None)
    assert s_else.ran


@pytest.mark.asyncio
async def test_cases_raises_on_no_match_no_else() -> None:
    runner = CasesRunner(expression="99", cases={1: AlwaysRunScript()})
    with pytest.raises(ValueError, match="Invalid choice"):
        await runner.run(None)


@pytest.mark.asyncio
async def test_cases_can_run_delegates_to_selected_script() -> None:
    runner = CasesRunner(expression="1", cases={1: AlwaysRunScript(), 2: NeverRunScript()})
    assert await runner.can_run(None) is True

    runner2 = CasesRunner(expression="2", cases={1: AlwaysRunScript(), 2: NeverRunScript()})
    assert await runner2.can_run(None) is False


@pytest.mark.asyncio
async def test_cases_get_fits_headers() -> None:
    class HeaderScript(Script):
        async def can_run(self, data: Any) -> bool:
            return True

        async def run(self, data: Any) -> None:
            pass

        def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, Any]:
            return {"KEY": ("value", "comment")}

    runner = CasesRunner(expression="1", cases={1: HeaderScript()})
    headers = runner.get_fits_headers()
    assert "KEY" in headers


# ── ConditionalRunner ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_conditional_runs_true_branch() -> None:
    s_true, s_false = AlwaysRunScript(), AlwaysRunScript()
    runner = ConditionalRunner(condition="True", true=s_true, false=s_false)
    await runner.run(None)
    assert s_true.ran
    assert not s_false.ran


@pytest.mark.asyncio
async def test_conditional_runs_false_branch() -> None:
    s_true, s_false = AlwaysRunScript(), AlwaysRunScript()
    runner = ConditionalRunner(condition="False", true=s_true, false=s_false)
    await runner.run(None)
    assert not s_true.ran
    assert s_false.ran


@pytest.mark.asyncio
async def test_conditional_no_false_branch_is_noop() -> None:
    s_true = AlwaysRunScript()
    runner = ConditionalRunner(condition="False", true=s_true)
    await runner.run(None)  # should not raise
    assert not s_true.ran


@pytest.mark.asyncio
async def test_conditional_can_run_true_branch() -> None:
    runner = ConditionalRunner(condition="True", true=AlwaysRunScript())
    assert await runner.can_run(None) is True

    runner2 = ConditionalRunner(condition="True", true=NeverRunScript())
    assert await runner2.can_run(None) is False


@pytest.mark.asyncio
async def test_conditional_can_run_no_script_returns_true() -> None:
    """When condition is False and no false branch, can_run returns True."""
    runner = ConditionalRunner(condition="False", true=NeverRunScript())
    assert await runner.can_run(None) is True


@pytest.mark.asyncio
async def test_conditional_get_fits_headers_no_script() -> None:
    runner = ConditionalRunner(condition="False", true=AlwaysRunScript())
    assert runner.get_fits_headers() == {}


# ── SelectorScript ────────────────────────────────────────────────────────────


def make_proxy_cm(value: object) -> MagicMock:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


@pytest.mark.asyncio
async def test_selector_can_run_when_parked() -> None:
    selector = MagicMock()
    selector.wait_for_state = AsyncMock(return_value=MotionState(status=MotionStatus.PARKED))

    script = SelectorScript(mode="imaging", selector="selector")
    script._comm = MagicMock()
    script._comm.has_proxy = AsyncMock(return_value=True)
    script._comm.proxy = MagicMock(return_value=make_proxy_cm(selector))

    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_selector_can_run_when_positioned() -> None:
    selector = MagicMock()
    selector.wait_for_state = AsyncMock(return_value=MotionState(status=MotionStatus.POSITIONED))

    script = SelectorScript(mode="imaging", selector="selector")
    script._comm = MagicMock()
    script._comm.has_proxy = AsyncMock(return_value=True)
    script._comm.proxy = MagicMock(return_value=make_proxy_cm(selector))

    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_selector_cannot_run_when_moving() -> None:
    selector = MagicMock()
    selector.wait_for_state = AsyncMock(return_value=MotionState(status=MotionStatus.SLEWING))

    script = SelectorScript(mode="imaging", selector="selector")
    script._comm = MagicMock()
    script._comm.has_proxy = AsyncMock(return_value=True)
    script._comm.proxy = MagicMock(return_value=make_proxy_cm(selector))

    assert await script.can_run(None) is False


@pytest.mark.asyncio
async def test_selector_run_sets_mode() -> None:
    selector = MagicMock()
    selector.set_mode = AsyncMock()

    script = SelectorScript(mode="spectroscopy", selector="selector")
    script._comm = MagicMock()
    script._comm.proxy = MagicMock(return_value=make_proxy_cm(selector))

    await script.run(None)
    selector.set_mode.assert_called_once_with("spectroscopy")
