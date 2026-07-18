from unittest.mock import MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.modules.robotic.scriptrunner import ScriptRunner
from pyobs.robotic.scripts import Script, ScriptError
from pyobs.utils import exceptions as exc


class _RaisingScript(Script):
    exc_to_raise: str = "runtime"

    async def run(self, data) -> None:
        if self.exc_to_raise == "domain":
            raise exc.AbortedError("aborted")
        raise RuntimeError("boom")


def make_runner(exc_to_raise: str = "runtime") -> ScriptRunner:
    comm = MagicMock(spec=Comm)
    return ScriptRunner(
        script={"class": f"{_RaisingScript.__module__}._RaisingScript", "exc_to_raise": exc_to_raise}, comm=comm
    )


@pytest.mark.asyncio
async def test_run_wraps_untyped_exception_as_script_error() -> None:
    runner = make_runner("runtime")
    with pytest.raises(ScriptError):
        await runner.run()


@pytest.mark.asyncio
async def test_run_lets_domain_exception_through_unwrapped() -> None:
    runner = make_runner("domain")
    with pytest.raises(exc.AbortedError):
        await runner.run()
