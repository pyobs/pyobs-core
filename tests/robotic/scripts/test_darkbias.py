from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import astropy.units as u
import pytest

from pyobs.robotic.instruments import BinningOption, CameraCapability, Instrument, InstrumentCapabilities
from pyobs.robotic.scripts.calibration.darkbias import DarkBiasScript
from pyobs.robotic.task import TaskData
from pyobs.robotic.utils.archive import Archive, FrameInfo
from pyobs.robotic.utils.calibration import clear_cache
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time
from tests.helpers import isinstance_class, make_proxy_cm


@pytest.fixture(autouse=True)
def _clear_exptime_cache() -> None:
    clear_cache()


class _FakeArchive(Archive):
    """Stub archive returning fixed OBJECT frame exptimes, optionally per (instrument, binning).

    `exptimes` seeds a single "cam1"/"1x1" combination. `exptimes_by_binning` (binning string ->
    exptimes) overrides that for tests that need multiple instruments/binnings in play, to check
    that DarkBiasScript only picks up the combination matching its own configured binning.
    """

    exptimes: list[float] = []
    exptimes_by_binning: dict[str, list[float]] | None = None

    def _combos(self) -> dict[str, list[float]]:
        return self.exptimes_by_binning if self.exptimes_by_binning is not None else {"1x1": self.exptimes}

    async def list_options(
        self,
        start: Any = None,
        end: Any = None,
        night: Any = None,
        site: Any = None,
        telescope: Any = None,
        instrument: Any = None,
        image_type: Any = None,
        binning: Any = None,
        filter_name: Any = None,
        rlevel: Any = None,
        obsnum: Any = None,
        exptime: Any = None,
    ) -> dict[str, list[Any]]:
        return {"instruments": ["cam1"], "binnings": list(self._combos().keys())}

    async def list_frames(
        self,
        start: Any = None,
        end: Any = None,
        night: Any = None,
        site: Any = None,
        telescope: Any = None,
        instrument: Any = None,
        image_type: Any = None,
        binning: Any = None,
        filter_name: Any = None,
        rlevel: Any = None,
        obsnum: Any = None,
        exptime: Any = None,
    ) -> list[FrameInfo]:
        frames = []
        for e in self._combos().get(binning, []):
            info = FrameInfo()
            info.exptime = e
            frames.append(info)
        return frames

    async def download_frames(self, frames: list[FrameInfo]) -> list[Any]:
        return []


def make_script(**kwargs) -> DarkBiasScript:
    return DarkBiasScript.model_validate({"camera": "camera", **kwargs}, context={"comm": MagicMock()})


def make_camera(
    supports_binning=True, supports_window=True, supports_exptime=True, supports_imagetype=True
) -> MagicMock:
    """Create a mock camera supporting all or some interfaces."""
    from pyobs.interfaces import IBinning, ICamera, IData, IExposureTime, IImageType, IWindow

    interfaces = [ICamera, IData]
    if supports_binning:
        interfaces.append(IBinning)
    if supports_window:
        interfaces.append(IWindow)
    if supports_exptime:
        interfaces.append(IExposureTime)
    if supports_imagetype:
        interfaces.append(IImageType)

    from pyobs.interfaces.IWindow import WindowCapabilities

    camera = MagicMock(spec=interfaces)
    camera.set_binning = AsyncMock()
    camera.get_capabilities = MagicMock(
        return_value=WindowCapabilities(full_frame_x=0, full_frame_y=0, full_frame_width=1024, full_frame_height=1024)
    )
    camera.set_window = AsyncMock()
    camera.set_exposure_time = AsyncMock()
    camera.set_image_type = AsyncMock()
    camera.grab_data = AsyncMock()

    # make isinstance checks work
    camera.__class__ = isinstance_class("Camera", interfaces)
    return camera


def setup_run_comm(script: DarkBiasScript, camera: MagicMock, binning_cam=..., window_cam=...) -> None:
    """Wire up comm mocks for a DarkBiasScript.run call.

    safe_proxy is used for IBinning and IWindow (optional interfaces).
    proxy is used for IExposureTime, IImageType, and IData (required).

    Pass binning_cam=None or window_cam=None to simulate a camera that doesn't
    implement the corresponding interface.
    """
    from pyobs.interfaces import IBinning, IWindow

    binning_value = camera if binning_cam is ... else binning_cam
    window_value = camera if window_cam is ... else window_cam

    def safe_proxy_se(name, iface=None):
        if iface is IBinning:
            return make_proxy_cm(binning_value)
        if iface is IWindow:
            return make_proxy_cm(window_value)
        return make_proxy_cm(camera)

    script._comm.safe_proxy = MagicMock(side_effect=safe_proxy_se)
    script._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))


# ── can_run ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_true_when_camera_available() -> None:
    script = make_script()
    script._comm.has_proxy = AsyncMock(return_value=True)
    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_can_run_false_when_camera_unavailable() -> None:
    script = make_script()
    script._comm.has_proxy = AsyncMock(return_value=False)
    assert await script.can_run(None) is False


# ── bias vs dark ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_runs_bias_when_exptime_zero() -> None:
    script = make_script(count=3, exptime=0)
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)
    camera.set_image_type.assert_called_once_with(ImageType.BIAS)
    camera.set_exposure_time.assert_called_once_with(0)
    assert camera.grab_data.call_count == 3


@pytest.mark.asyncio
async def test_runs_dark_when_exptime_nonzero() -> None:
    script = make_script(count=2, exptime=30.0)
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)
    camera.set_image_type.assert_called_once_with(ImageType.DARK)
    camera.set_exposure_time.assert_called_once_with(30.0)
    assert camera.grab_data.call_count == 2


# ── interface checks ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sets_binning_when_supported() -> None:
    script = make_script(binning=(2, 2))
    camera = make_camera(supports_binning=True)
    setup_run_comm(script, camera)

    await script.run(None)
    camera.set_binning.assert_called_once_with(2, 2)


@pytest.mark.asyncio
async def test_skips_binning_when_not_supported() -> None:
    script = make_script(binning=(2, 2))
    camera = make_camera(supports_binning=False)
    setup_run_comm(script, camera, binning_cam=None)

    await script.run(None)
    camera.set_binning.assert_not_called()


@pytest.mark.asyncio
async def test_sets_full_frame_when_window_supported() -> None:
    script = make_script()
    camera = make_camera(supports_window=True)
    setup_run_comm(script, camera)

    await script.run(None)
    camera.get_capabilities.assert_called_once()
    camera.set_window.assert_called_once_with(0, 0, 1024, 1024)


@pytest.mark.asyncio
async def test_skips_window_when_not_supported() -> None:
    script = make_script()
    camera = make_camera(supports_window=False)
    setup_run_comm(script, camera, window_cam=None)

    await script.run(None)
    camera.set_window.assert_not_called()


@pytest.mark.asyncio
async def test_takes_correct_count() -> None:
    script = make_script(count=5)
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)
    assert camera.grab_data.call_count == 5


# ── mutual exclusivity validation ────────────────────────────────────────────


def test_exptimes_and_match_science_exptimes_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        make_script(exptimes=[30.0, 600.0], match_science_exptimes=True, archive=_FakeArchive(), site="siteA")


def test_exptime_and_exptimes_cannot_be_combined() -> None:
    with pytest.raises(ValueError, match="cannot be combined"):
        make_script(exptime=30.0, exptimes=[30.0, 600.0])


def test_exptime_and_match_science_exptimes_cannot_be_combined() -> None:
    with pytest.raises(ValueError, match="cannot be combined"):
        make_script(exptime=30.0, match_science_exptimes=True, archive=_FakeArchive(), site="siteA")


def test_exptimes_alone_is_valid() -> None:
    # should not raise
    make_script(exptimes=[30.0, 600.0])


def test_exptimes_cannot_include_zero() -> None:
    with pytest.raises(ValueError, match="cannot include 0"):
        make_script(exptimes=[0, 30.0])


# ── can_run: match_science_exptimes ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_false_without_archive_when_matching_science_exptimes() -> None:
    script = make_script(match_science_exptimes=True, site="siteA")
    script._comm.has_proxy = AsyncMock(return_value=True)

    assert await script.can_run(None) is False
    assert "archive" in script.cant_run_reason()


@pytest.mark.asyncio
async def test_can_run_false_without_site_when_matching_science_exptimes() -> None:
    script = make_script(match_science_exptimes=True, archive=_FakeArchive())
    script._comm.has_proxy = AsyncMock(return_value=True)

    assert await script.can_run(None) is False
    assert "archive" in script.cant_run_reason()


@pytest.mark.asyncio
async def test_can_run_false_without_night_or_observer() -> None:
    script = make_script(match_science_exptimes=True, archive=_FakeArchive(), site="siteA")
    script._comm.has_proxy = AsyncMock(return_value=True)

    assert await script.can_run(None) is False
    assert "observer" in script.cant_run_reason()


@pytest.mark.asyncio
async def test_can_run_true_with_explicit_night() -> None:
    script = make_script(match_science_exptimes=True, archive=_FakeArchive(), site="siteA", night="2024-01-01")
    script._comm.has_proxy = AsyncMock(return_value=True)

    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_can_run_true_with_observer_configured() -> None:
    from astroplan import Observer

    observer = Observer(longitude=9.94 * u.deg, latitude=51.56 * u.deg, elevation=150 * u.m)
    script = DarkBiasScript.model_validate(
        {"camera": "camera", "match_science_exptimes": True, "archive": _FakeArchive(), "site": "siteA"},
        context={"comm": MagicMock(), "observer": observer},
    )
    script._comm.has_proxy = AsyncMock(return_value=True)

    # Time.now() pulls in astropy's IERS auto-download; pin it to a fixed, bundled-IERS-coverage
    # instant like every other Observer-based test in the repo, so the suite stays standalone.
    with patch("pyobs.robotic.scripts.calibration.darkbias.Time") as mock_time:
        mock_time.now.return_value = Time("2026-07-16T15:45:50")
        assert await script.can_run(None) is True


# ── explicit exptimes list ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_runs_series_longest_first() -> None:
    script = make_script(count=2, exptimes=[30.0, 600.0, 60.0])
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)

    calls = [c.args[0] for c in camera.set_exposure_time.call_args_list]
    assert calls == [600.0, 60.0, 30.0]
    camera.set_image_type.assert_called_once_with(ImageType.DARK)
    assert camera.grab_data.call_count == 6  # 3 series * 2 exposures


@pytest.mark.asyncio
async def test_estimate_duration_sums_over_exptimes_list() -> None:
    script = make_script(count=2, exptimes=[30.0, 600.0])
    assert script.estimate_duration(None) == 2 * (30.0 + 5.0) + 2 * (600.0 + 5.0)


def _capabilities_with_readout(readout_time_s: float, binning: tuple[int, int] = (1, 1)) -> InstrumentCapabilities:
    camera = CameraCapability(
        module_name="camera",
        code="ef01",
        binnings=[BinningOption(x=binning[0], y=binning[1], readout_time_s=readout_time_s)],
    )
    return InstrumentCapabilities([Instrument(cameras=[camera])])


@pytest.mark.asyncio
async def test_estimate_duration_uses_real_readout_time_when_available() -> None:
    script = make_script(count=2, exptimes=[30.0, 600.0])
    data = TaskData(task=MagicMock(), instrument_capabilities=_capabilities_with_readout(3.5))
    assert script.estimate_duration(data) == 2 * (30.0 + 3.5) + 2 * (600.0 + 3.5)


@pytest.mark.asyncio
async def test_estimate_duration_falls_back_when_binning_not_declared() -> None:
    # capability data exists for the camera, but not for this script's binning (2x2) -- falls
    # back to the flat 5.0s fudge, same as if there were no capability data at all
    script = make_script(count=2, exptimes=[30.0], binning=(2, 2))
    data = TaskData(task=MagicMock(), instrument_capabilities=_capabilities_with_readout(3.5, binning=(1, 1)))
    assert script.estimate_duration(data) == 2 * (30.0 + 5.0)


# ── match_science_exptimes ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_runs_series_derived_from_science_exptimes() -> None:
    archive = _FakeArchive(exptimes=[45.0, 45.1, 600.0])
    script = make_script(count=1, match_science_exptimes=True, archive=archive, site="siteA", night="2024-01-01")
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)

    calls = [c.args[0] for c in camera.set_exposure_time.call_args_list]
    assert calls == [600.0, 45.05]
    camera.set_image_type.assert_called_once_with(ImageType.DARK)


@pytest.mark.asyncio
async def test_only_uses_exptimes_from_its_own_binning() -> None:
    # cam1 (this script's binning, 1x1) used 30s/600s; a different instrument/binning (2x2, not
    # this script's) used 90s -- 90 must not leak in just because science_exptimes_for_night
    # unions across every (instrument, binning) combination it found that night
    archive = _FakeArchive(exptimes_by_binning={"1x1": [30.0, 600.0], "2x2": [90.0]})
    script = make_script(count=1, match_science_exptimes=True, archive=archive, site="siteA", night="2024-01-01")
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)

    calls = [c.args[0] for c in camera.set_exposure_time.call_args_list]
    assert calls == [600.0, 30.0]


@pytest.mark.asyncio
async def test_no_science_exptimes_takes_nothing() -> None:
    archive = _FakeArchive(exptimes=[])
    script = make_script(count=1, match_science_exptimes=True, archive=archive, site="siteA", night="2024-01-01")
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)

    camera.set_image_type.assert_not_called()
    camera.set_exposure_time.assert_not_called()
    camera.grab_data.assert_not_called()


# ── match_science_exptimes: estimate_duration via can_run()'s cache warm-up ──


@pytest.mark.asyncio
async def test_estimate_duration_uses_cache_warmed_by_can_run() -> None:
    archive = _FakeArchive(exptimes=[30.0, 600.0])
    script = make_script(count=2, match_science_exptimes=True, archive=archive, site="siteA", night="2024-01-01")
    script._comm.has_proxy = AsyncMock(return_value=True)
    assert await script.can_run(None) is True

    # a fresh instance, as Task.create_script() would produce -- no shared state with `script`,
    # only the module-level cache can_run() warmed above
    other = make_script(count=2, match_science_exptimes=True, archive=archive, site="siteA", night="2024-01-01")

    assert other.estimate_duration(None) == 2 * (30.0 + 5.0) + 2 * (600.0 + 5.0)


@pytest.mark.asyncio
async def test_estimate_duration_falls_back_without_a_prior_can_run() -> None:
    archive = _FakeArchive(exptimes=[30.0, 600.0])
    script = make_script(count=2, match_science_exptimes=True, archive=archive, site="siteA", night="2024-01-01")

    # nothing cached yet -- placeholder estimate at _FALLBACK_MATCH_EXPTIME, not the real
    # archive-derived series (and not the always-0 configured exptime, which would badly
    # underestimate a real dark run)
    assert script.estimate_duration(None) == 2 * (DarkBiasScript._FALLBACK_MATCH_EXPTIME + 5.0)


@pytest.mark.asyncio
async def test_can_run_false_when_archive_query_raises() -> None:
    class _BrokenArchive(_FakeArchive):
        async def list_options(self, **kwargs: Any) -> dict[str, list[Any]]:
            raise RuntimeError("archive unreachable")

    script = make_script(match_science_exptimes=True, archive=_BrokenArchive(), site="siteA", night="2024-01-01")
    script._comm.has_proxy = AsyncMock(return_value=True)

    assert await script.can_run(None) is False
    assert "archive" in script.cant_run_reason()
