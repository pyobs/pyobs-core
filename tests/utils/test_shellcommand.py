from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import pyobs.utils.exceptions as exc
from pyobs.utils.shellcommand import ShellCommand, ShellCommandResponse

# ── ShellCommand.parse ────────────────────────────────────────────────────────


def test_parse_simple_command() -> None:
    cmd = ShellCommand.parse("camera.abort()")
    assert cmd.module == "camera"
    assert cmd.command == "abort"
    assert cmd.params == []


def test_parse_with_float_param() -> None:
    cmd = ShellCommand.parse("camera.set_exposure_time(30.0)")
    assert cmd.module == "camera"
    assert cmd.command == "set_exposure_time"
    assert cmd.params == [30.0]


def test_parse_with_int_param() -> None:
    cmd = ShellCommand.parse("camera.set_binning(2)")
    assert cmd.params == [2.0]


def test_parse_with_string_param() -> None:
    cmd = ShellCommand.parse('camera.set_filter("V")')
    assert cmd.params == ["V"]


def test_parse_with_multiple_params() -> None:
    cmd = ShellCommand.parse("camera.set_window(0, 0, 512, 512)")
    assert cmd.params == [0.0, 0.0, 512.0, 512.0]


def test_parse_with_negative_param() -> None:
    cmd = ShellCommand.parse("telescope.move_radec(83.82, -5.39)")
    assert cmd.params == [83.82, -5.39]


def test_parse_mixed_params() -> None:
    cmd = ShellCommand.parse('module.method(42, "hello", 3.14)')
    assert cmd.params == [42.0, "hello", 3.14]


def test_parse_preserves_command_string() -> None:
    cmd_str = "camera.abort()"
    cmd = ShellCommand.parse(cmd_str)
    assert cmd.command_string == cmd_str


def test_parse_invalid_no_dot() -> None:
    with pytest.raises(ValueError, match="Invalid command"):
        ShellCommand.parse("cameraabort()")


def test_parse_invalid_no_parens() -> None:
    with pytest.raises(ValueError, match="Invalid parameters"):
        ShellCommand.parse("camera.abort")


def test_parse_invalid_empty() -> None:
    with pytest.raises(ValueError):
        ShellCommand.parse("")


def test_parse_invalid_trailing_content() -> None:
    with pytest.raises(ValueError, match="end of command"):
        ShellCommand.parse("camera.abort() extra")


# ── ShellCommand properties ───────────────────────────────────────────────────


def test_command_number_increments() -> None:
    cmd1 = ShellCommand.parse("camera.abort()")
    cmd2 = ShellCommand.parse("camera.abort()")
    assert cmd2.command_number == cmd1.command_number + 1


def test_str_representation() -> None:
    cmd = ShellCommand.parse("camera.abort()")
    s = str(cmd)
    assert "camera.abort()" in s
    assert str(cmd.command_number) in s


# ── ShellCommand.execute ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_success() -> None:
    proxy = MagicMock()
    proxy.execute = AsyncMock(return_value=None)
    comm = MagicMock()
    comm.proxy = AsyncMock(return_value=proxy)

    cmd = ShellCommand.parse("camera.abort()")
    response = await cmd.execute(comm)

    assert not response.is_error
    assert response.response == "OK"


@pytest.mark.asyncio
async def test_execute_with_return_value() -> None:
    proxy = MagicMock()
    proxy.execute = AsyncMock(return_value=30.0)
    comm = MagicMock()
    comm.proxy = AsyncMock(return_value=proxy)

    cmd = ShellCommand.parse("camera.get_exposure_time()")
    response = await cmd.execute(comm)

    assert not response.is_error
    assert "30.0" in response.response


@pytest.mark.asyncio
async def test_execute_module_not_found() -> None:
    comm = MagicMock()
    comm.proxy = AsyncMock(side_effect=ValueError("module not found"))

    cmd = ShellCommand.parse("nonexistent.abort()")
    response = await cmd.execute(comm)

    assert response.is_error
    assert "nonexistent" in response.response


@pytest.mark.asyncio
async def test_execute_invalid_param() -> None:
    proxy = MagicMock()
    proxy.execute = AsyncMock(side_effect=ValueError("bad param"))
    comm = MagicMock()
    comm.proxy = AsyncMock(return_value=proxy)

    cmd = ShellCommand.parse("camera.set_exposure_time(30.0)")
    response = await cmd.execute(comm)

    assert response.is_error
    assert "Invalid parameter" in response.response


@pytest.mark.asyncio
async def test_execute_remote_error() -> None:
    proxy = MagicMock()
    proxy.execute = AsyncMock(side_effect=exc.RemoteError("something failed"))
    comm = MagicMock()
    comm.proxy = AsyncMock(return_value=proxy)

    cmd = ShellCommand.parse("camera.abort()")
    response = await cmd.execute(comm)

    assert response.is_error
    assert "Exception raised" in response.response


# ── ShellCommandResponse ──────────────────────────────────────────────────────


def test_response_str() -> None:
    cmd = ShellCommand.parse("camera.abort()")
    resp = ShellCommandResponse(cmd.command_number, cmd, "OK")
    assert "OK" in str(resp)
    assert str(cmd.command_number) in str(resp)


def test_response_color_ok() -> None:
    cmd = ShellCommand.parse("camera.abort()")
    resp = ShellCommandResponse(cmd.command_number, cmd, "OK", is_error=False)
    assert resp.color == "lime"


def test_response_color_error() -> None:
    cmd = ShellCommand.parse("camera.abort()")
    resp = ShellCommandResponse(cmd.command_number, cmd, "Error", is_error=True)
    assert resp.color == "red"


def test_response_bbcode() -> None:
    cmd = ShellCommand.parse("camera.abort()")
    resp = ShellCommandResponse(cmd.command_number, cmd, "OK")
    assert resp.bbcode.startswith("[lime]")
    assert resp.bbcode.endswith("[/lime]")
