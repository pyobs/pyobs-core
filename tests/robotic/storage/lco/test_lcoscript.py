from __future__ import annotations

import json
from typing import Any

import pytest

from pyobs.object import Object
from pyobs.robotic.scripts import Script
from pyobs.robotic.storage.lco._portal import LcoRequest
from pyobs.robotic.storage.lco.scripts import LcoScript
from pyobs.robotic.task import TaskData

from .test_task import REQUEST_CONFIG


class FakeScript(Script):
    """Minimal script used to verify LcoScript's dispatch."""

    can_run_result: bool = True

    async def can_run(self, data: TaskData | None) -> bool:
        return self.can_run_result

    async def run(self, data: TaskData | None) -> None:
        self.exptime_done = 42.0


def make_request(script_name: str | None) -> LcoRequest:
    config = json.loads(REQUEST_CONFIG)
    request = config["requests"][0]
    request["configurations"][0]["type"] = "SCRIPT"
    request["configurations"][0]["extra_params"] = {} if script_name is None else {"script_name": script_name}
    return LcoRequest.model_validate(request)


def make_lco_script(script_name: str | None, scripts: dict[str, dict[str, Any]] | None = None) -> LcoScript:
    if scripts is None:
        scripts = {"skyflats": {"class": f"{__name__}.FakeScript"}}
    request = make_request(script_name)
    return Object().pyobs_model_validate(LcoScript, {"request": request, "scripts": scripts}, by_alias=True)


# ── dispatch ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_dispatches_to_named_script() -> None:
    """can_run() resolves and delegates to the script named in extra_params.script_name."""
    script = make_lco_script("skyflats", {"skyflats": {"class": f"{__name__}.FakeScript", "can_run_result": False}})
    assert await script.can_run(None) is False


@pytest.mark.asyncio
async def test_run_dispatches_and_copies_exptime_done() -> None:
    """run() delegates to the named script and copies its exptime_done back."""
    script = make_lco_script("skyflats")
    await script.run(None)
    assert script.exptime_done == 42.0


def test_get_fits_headers_dispatches_to_named_script() -> None:
    """get_fits_headers() delegates to the named script."""
    script = make_lco_script("skyflats")
    assert script.get_fits_headers() == {}


# ── errors ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_raises_without_script_name() -> None:
    """Missing extra_params.script_name raises a clear error."""
    script = make_lco_script(None)
    with pytest.raises(ValueError, match="No script_name given"):
        await script.can_run(None)


@pytest.mark.asyncio
async def test_can_run_raises_for_unknown_script_name() -> None:
    """A script_name with no matching entry in scripts raises a clear error."""
    script = make_lco_script("does_not_exist")
    with pytest.raises(ValueError, match='No script found for script_name "does_not_exist"'):
        await script.can_run(None)


# ── context propagation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_propagates_comm_to_sub_script() -> None:
    """The comm/observer/etc. context on the LcoScript is propagated to the resolved sub-script."""
    parent = Object()
    request = make_request("skyflats")
    script = parent.pyobs_model_validate(
        LcoScript,
        {"request": request, "scripts": {"skyflats": {"class": f"{__name__}.FakeScript"}}},
        by_alias=True,
    )
    sub_script = script._create_script()
    assert sub_script.comm is parent.comm
