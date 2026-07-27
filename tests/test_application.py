from __future__ import annotations

import pytest

from pyobs.application import Application
from pyobs.modules import Module


@pytest.mark.asyncio
async def test_init_config_path_no_comm_names_dummy_comm_after_stem(tmp_path, caplog) -> None:
    """A module with no comm of its own falls back to DummyComm -- give it the config
    file's stem as its name instead of the fixed placeholder, so it doesn't collide with
    every other comm-less module in PYOBS_MODULE log tagging and doesn't spuriously trip
    the stem-mismatch warning below."""
    config = tmp_path / "filecache.yaml"
    config.write_text("class: pyobs.modules.Module\n")

    app = Application(config=str(config))

    assert isinstance(app._module, Module)
    assert app._module.name == "filecache"
    assert "does not match module's own name" not in caplog.text
    app._loop.close()


@pytest.mark.asyncio
async def test_init_config_path_warns_on_real_comm_name_mismatch(tmp_path, caplog) -> None:
    config = tmp_path / "filecache.yaml"
    config.write_text(
        "class: pyobs.modules.Module\ncomm:\n  class: pyobs.comm.local.LocalComm\n  name: something_else\n"
    )

    app = Application(config=str(config))

    assert "does not match module's own name" in caplog.text
    app._loop.close()
