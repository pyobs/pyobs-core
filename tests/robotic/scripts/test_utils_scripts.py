from __future__ import annotations

import logging

import pytest

from pyobs.robotic.scripts.utils.debugtrigger import DebugTriggerScript
from pyobs.robotic.scripts.utils.log import LogScript

# ── DebugTriggerScript ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_debug_trigger_can_run() -> None:
    script = DebugTriggerScript()
    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_debug_trigger_sets_triggered() -> None:
    script = DebugTriggerScript()
    assert script.triggered is False
    await script.run(None)
    assert script.triggered is True


# ── LogScript ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_can_run() -> None:
    script = LogScript(expression="'hello'")
    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_log_evaluates_expression(caplog) -> None:
    script = LogScript(expression="1 + 1")
    with caplog.at_level(logging.INFO):
        await script.run(None)
    assert "2" in caplog.text


@pytest.mark.asyncio
async def test_log_expression_with_now(caplog) -> None:
    """Expression has access to 'now' as a datetime."""
    script = LogScript(expression="now.year")
    with caplog.at_level(logging.INFO):
        await script.run(None)
    # current year should appear in log
    from datetime import UTC, datetime

    assert str(datetime.now(UTC).year) in caplog.text


@pytest.mark.asyncio
async def test_log_string_expression(caplog) -> None:
    script = LogScript(expression="'telescope ready'")
    with caplog.at_level(logging.INFO):
        await script.run(None)
    assert "telescope ready" in caplog.text
