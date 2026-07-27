"""Tests for PyobsDaemon._start_service()'s command construction -- in particular, that
--log-file is opt-in via file_log rather than always passed (see specs/plans/pyobs_2_0_work_plan.md,
the pyobsd logging item)."""

from __future__ import annotations

from typing import Any

import pytest

from pyobs.cli.pyobsd import PyobsDaemon


def make_daemon(mocker, **kwargs: Any) -> PyobsDaemon:
    daemon = PyobsDaemon("config", "run", "log", **kwargs)
    daemon._pyobs_exec = "pyobs"
    # _start_service() polls _read_pid()/_is_alive() for the spawned process to confirm
    # itself -- fake immediate success so tests exercise command construction only.
    mocker.patch.object(PyobsDaemon, "_read_pid", return_value=12345)
    mocker.patch.object(PyobsDaemon, "_is_alive", return_value=True)
    return daemon


@pytest.mark.parametrize(
    "syslog,file_log,expect_log_file,expect_syslog_flag",
    [
        (False, False, False, False),
        (True, False, False, True),
        (False, True, True, False),
        (True, True, True, True),
    ],
)
def test_start_service_flags(mocker, syslog, file_log, expect_log_file, expect_syslog_flag) -> None:
    popen = mocker.patch("subprocess.Popen")
    mocker.patch("os.makedirs")

    daemon = make_daemon(mocker, syslog=syslog, file_log=file_log)
    daemon._start_service("telescope")

    cmd = popen.call_args[0][0]
    assert ("--log-file" in cmd) is expect_log_file
    assert ("--syslog" in cmd) is expect_syslog_flag
    assert "--pid-file" in cmd  # always present, unrelated to logging


def test_start_service_default_is_no_file_log(mocker) -> None:
    """file_log defaults to False -- --log-file is opt-in, not unconditional."""
    popen = mocker.patch("subprocess.Popen")
    mocker.patch("os.makedirs")

    daemon = make_daemon(mocker)
    daemon._start_service("telescope")

    cmd = popen.call_args[0][0]
    assert "--log-file" not in cmd


def test_start_service_creates_log_path_only_when_file_log_enabled(mocker) -> None:
    makedirs = mocker.patch("os.makedirs")
    mocker.patch("subprocess.Popen")

    daemon = make_daemon(mocker, file_log=False)
    daemon._start_service("telescope")

    assert makedirs.call_args_list == [mocker.call(daemon._run_path, exist_ok=True)]


def test_start_service_creates_log_path_when_file_log_enabled(mocker) -> None:
    makedirs = mocker.patch("os.makedirs")
    mocker.patch("subprocess.Popen")

    daemon = make_daemon(mocker, file_log=True)
    daemon._start_service("telescope")

    assert mocker.call(daemon._log_path, exist_ok=True) in makedirs.call_args_list
