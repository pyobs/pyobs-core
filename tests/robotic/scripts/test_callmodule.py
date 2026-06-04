import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

from pyobs.interfaces import IExposureTime
from pyobs.robotic.scripts.utils.callmodule import CallModuleScript


@pytest.fixture
def script() -> CallModuleScript:
    s = CallModuleScript(
        module="camera",
        interface="pyobs.interfaces.IExposureTime",
        method="set_exposure_time",
        params={"exposure_time": 30.0},
    )
    s._comm = MagicMock()
    return s


# ── param validation ──────────────────────────────────────────────────────────


def test_valid_params_pass_validation() -> None:
    s = CallModuleScript(
        module="camera",
        interface="pyobs.interfaces.IExposureTime",
        method="set_exposure_time",
        params={"exposure_time": 30.0},
    )
    assert s.params["exposure_time"] == 30.0


def test_unknown_param_raises() -> None:
    with pytest.raises(ValidationError, match="Unknown parameter 'nonexistent'"):
        CallModuleScript(
            module="camera",
            interface="pyobs.interfaces.IExposureTime",
            method="set_exposure_time",
            params={"nonexistent": 30.0},
        )


def test_wrong_type_raises() -> None:
    with pytest.raises(ValidationError, match="Parameter 'exposure_time'"):
        CallModuleScript(
            module="camera",
            interface="pyobs.interfaces.IExposureTime",
            method="set_exposure_time",
            params={"exposure_time": "not_a_float"},
        )


def test_unknown_method_raises() -> None:
    with pytest.raises(ValidationError, match="Method 'nonexistent_method' not found"):
        CallModuleScript(
            module="camera",
            interface="pyobs.interfaces.IExposureTime",
            method="nonexistent_method",
            params={},
        )


def test_interface_is_required() -> None:
    with pytest.raises(ValidationError):
        CallModuleScript(module="camera", method="set_exposure_time", params={})


def test_empty_params_always_valid() -> None:
    s = CallModuleScript(
        module="camera",
        interface="pyobs.interfaces.IExposureTime",
        method="set_exposure_time",
        params={},
    )
    assert s.params == {}


def test_default_params_is_empty_dict() -> None:
    s = CallModuleScript(
        module="camera",
        interface="pyobs.interfaces.IExposureTime",
        method="set_exposure_time",
    )
    assert s.params == {}


# ── can_run ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_true_when_module_available(script: CallModuleScript) -> None:
    script._comm.proxy = AsyncMock(return_value=MagicMock())
    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_can_run_false_when_module_unavailable(script: CallModuleScript) -> None:
    script._comm.proxy = AsyncMock(side_effect=ValueError("module not found"))
    assert await script.can_run(None) is False


@pytest.mark.asyncio
async def test_can_run_uses_interface_for_proxy(script: CallModuleScript) -> None:
    script._comm.proxy = AsyncMock(return_value=MagicMock())
    await script.can_run(None)
    assert script._comm.proxy.call_args[0][1] is IExposureTime


# ── run ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_calls_method_with_named_params(script: CallModuleScript) -> None:
    proxy = MagicMock()
    proxy.execute = AsyncMock()
    script._comm.proxy = AsyncMock(return_value=proxy)

    await script.run(None)
    proxy.execute.assert_called_once_with("set_exposure_time", exposure_time=30.0)


@pytest.mark.asyncio
async def test_run_uses_interface_for_proxy(script: CallModuleScript) -> None:
    proxy = MagicMock()
    proxy.execute = AsyncMock()
    script._comm.proxy = AsyncMock(return_value=proxy)

    await script.run(None)
    assert script._comm.proxy.call_args[0][1] is IExposureTime


# ── yaml round-trip ───────────────────────────────────────────────────────────


def test_yaml_roundtrip() -> None:
    config = {
        "class": "pyobs.robotic.scripts.utils.CallModuleScript",
        "module": "camera",
        "interface": "pyobs.interfaces.IExposureTime",
        "method": "set_exposure_time",
        "params": {"exposure_time": 30.0},
    }
    s = CallModuleScript.model_validate(config)
    assert s.module == "camera"
    assert s.interface == "pyobs.interfaces.IExposureTime"
    assert s.method == "set_exposure_time"
    assert s.params == {"exposure_time": 30.0}
