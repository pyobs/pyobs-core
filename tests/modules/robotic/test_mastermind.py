from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.interfaces import FitsHeaderEntry
from pyobs.modules.robotic.mastermind import Mastermind
from pyobs.robotic.storage.observationarchive import ObservationArchive
from pyobs.robotic.task import Task
from pyobs.robotic.taskrunner import TaskRunner


def make_mastermind(**kwargs) -> Mastermind:
    comm = MagicMock(spec=Comm)
    schedule = MagicMock(spec=ObservationArchive)
    runner = MagicMock(spec=TaskRunner)
    return Mastermind(comm=comm, schedule=schedule, runner=runner, **kwargs)


@pytest.mark.asyncio
async def test_get_fits_header_before_no_task_returns_empty() -> None:
    mm = make_mastermind()
    assert await mm.get_fits_header_before() == {}


@pytest.mark.asyncio
async def test_get_fits_header_before_includes_version_headers(mocker) -> None:
    mocker.patch(
        "pyobs.modules.robotic.mastermind.version_fits_headers",
        return_value={"HIERARCH TESTMASTERMIND VERSION PYOBS-CORE": FitsHeaderEntry("2.4.1", "")},
    )
    mm = make_mastermind()
    mm._task = Task(id=1, name="task1")

    hdr = await mm.get_fits_header_before()

    assert hdr["HIERARCH TESTMASTERMIND VERSION PYOBS-CORE"].value == "2.4.1"
