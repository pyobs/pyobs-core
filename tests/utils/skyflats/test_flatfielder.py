from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from pyobs.comm import Comm
from pyobs.images import Image
from pyobs.interfaces import ICamera, IExposureTime, IFilters, IImageType, IPointingAltAz, IWindow
from pyobs.interfaces.IWindow import WindowCapabilities
from pyobs.robotic.utils.skyflats.flatfielder import FlatFielder
from pyobs.robotic.utils.skyflats.pointing.base import SkyFlatsBasePointing
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time
from pyobs.vfs import VirtualFileSystem
from tests.helpers import make_proxy_cm


def make_observer(alt: float = 10.0) -> MagicMock:
    """Observer stub returning a constant solar altitude for every sun_altaz() call."""
    altaz = MagicMock()
    altaz.alt.degree = alt
    observer = MagicMock()
    observer.sun_altaz = MagicMock(return_value=altaz)
    return observer


def make_twilight_observer(alt_now: float, alt_future: float) -> MagicMock:
    """Observer stub distinguishing the first (now) vs second (+10min) sun_altaz() call,
    for the twilight-direction detection in _init_system()."""
    call_count = 0

    def sun_altaz(time: Time) -> MagicMock:
        nonlocal call_count
        call_count += 1
        altaz = MagicMock()
        altaz.alt.degree = alt_future if call_count >= 2 else alt_now
        return altaz

    observer = MagicMock()
    observer.sun_altaz = MagicMock(side_effect=sun_altaz)
    return observer


def make_flatfielder(functions: str | dict = "5.0", observer: MagicMock | None = None, **kwargs) -> FlatFielder:
    comm = MagicMock(spec=Comm)
    if observer is None:
        observer = make_observer()
    return FlatFielder(functions=functions, comm=comm, observer=observer, **kwargs)


# ── __init__ / properties ──────────────────────────────────────────────────


def test_init_defaults_test_and_counts_frame() -> None:
    ff = make_flatfielder()
    assert ff._test_frame == (45, 45, 10, 10)
    assert ff._counts_frame == (25, 25, 75, 75)
    assert ff._state == FlatFielder.State.INIT


def test_init_custom_frames() -> None:
    ff = make_flatfielder(test_frame=(1, 2, 3, 4), counts_frame=(5, 6, 7, 8))
    assert ff._test_frame == (1, 2, 3, 4)
    assert ff._counts_frame == (5, 6, 7, 8)


def test_init_with_pointing_instance() -> None:
    pointing = MagicMock(spec=SkyFlatsBasePointing)
    ff = make_flatfielder(pointing=pointing)
    assert ff._pointing is pointing


def test_has_filters_true_for_filter_based_functions() -> None:
    ff = make_flatfielder(functions={"clear": "5.0", "red": "6.0"})
    assert ff.has_filters is True


def test_has_filters_false_for_single_function() -> None:
    ff = make_flatfielder(functions="5.0")
    assert ff.has_filters is False


def test_image_count_and_total_exptime_reflect_progress() -> None:
    ff = make_flatfielder()
    ff._exposures_done = 3
    ff._exptime_done = 12.5
    assert ff.image_count == 3
    assert ff.total_exptime == 12.5


# ── reset ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reset_resets_state_and_counts() -> None:
    ff = make_flatfielder()
    ff._state = FlatFielder.State.RUNNING
    ff._exposures_done = 5
    ff._exptime_done = 12.3

    await ff.reset()

    assert ff._state == FlatFielder.State.INIT
    assert ff._exposures_done == 0
    assert ff._exptime_done == 0


@pytest.mark.asyncio
async def test_reset_resets_pointing_when_configured() -> None:
    pointing = AsyncMock(spec=SkyFlatsBasePointing)
    ff = make_flatfielder(pointing=pointing)

    await ff.reset()

    pointing.reset.assert_awaited_once()


# ── _eval_exptime ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "twilight_attr,exptime,expected",
    [
        ("DUSK", 2.0, 0),
        ("DUSK", 0.1, -1),
        ("DUSK", 10.0, 1),
        ("DAWN", 2.0, 0),
        ("DAWN", 10.0, -1),
        ("DAWN", 0.1, 1),
    ],
)
def test_eval_exptime(twilight_attr: str, exptime: float, expected: int) -> None:
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = getattr(FlatFielder.Twilight, twilight_attr)
    ff._exptime = exptime
    assert ff._eval_exptime() == expected


def test_eval_exptime_uses_explicit_range_over_defaults() -> None:
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 8.0
    # outside the instance defaults but inside an explicitly widened range
    assert ff._eval_exptime(min_exptime=0.1, max_exptime=10.0) == 0


# ── _calc_new_exptime ───────────────────────────────────────────────────────


def test_calc_new_exptime_scales_towards_target() -> None:
    ff = make_flatfielder(target_count=30000)
    ff._bias_level = 0
    ff._median = 15000  # half of target -> factor 2.0
    ff._exptime = 1.0
    ff._calc_new_exptime()
    assert ff._exptime == pytest.approx(2.0)


def test_calc_new_exptime_clamps_factor_low() -> None:
    ff = make_flatfielder(target_count=30000)
    ff._bias_level = 0
    ff._median = 300000  # factor would be << 0.1
    ff._exptime = 1.0
    ff._calc_new_exptime()
    assert ff._exptime == pytest.approx(0.1)


def test_calc_new_exptime_clamps_factor_high() -> None:
    ff = make_flatfielder(target_count=30000)
    ff._bias_level = 0
    ff._median = 100  # factor would be >> 10
    ff._exptime = 1.0
    ff._calc_new_exptime()
    assert ff._exptime == pytest.approx(10.0)


# ── _get_image_median ───────────────────────────────────────────────────────


def test_get_image_median_full_frame_without_trimsec() -> None:
    image = Image(data=np.full((10, 10), 500.0))
    assert FlatFielder._get_image_median(image) == 500.0


def test_get_image_median_restricts_to_frame() -> None:
    data = np.zeros((10, 10))
    data[2:8, 2:8] = 1000.0
    image = Image(data=data)
    # frame covers the 20%-80% region, matching the non-zero block above
    median = FlatFielder._get_image_median(image, frame=(20, 20, 60, 60))
    assert median == 1000.0


# ── _eval_function ──────────────────────────────────────────────────────────


def test_eval_function_returns_altitude_and_exptime() -> None:
    ff = make_flatfielder(functions="5.0", observer=make_observer(alt=12.5))
    sun_alt, exptime = ff._eval_function(Time.now())
    assert sun_alt == 12.5
    assert exptime == 5.0


def test_eval_function_raises_without_observer() -> None:
    ff = make_flatfielder()
    ff._observer = None
    with pytest.raises(ValueError):
        ff._eval_function(Time.now())


# ── _initial_check ──────────────────────────────────────────────────────────


def test_initial_check_true_when_still_time() -> None:
    ff = make_flatfielder(functions="2.0", min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    assert ff._initial_check() is True
    assert ff._state == FlatFielder.State.INIT


def test_initial_check_false_when_time_passed() -> None:
    ff = make_flatfielder(functions="100.0", min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    assert ff._initial_check() is False
    assert ff._state == FlatFielder.State.FINISHED


# ── __call__ ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_raises_without_exposure_time_support() -> None:
    ff = make_flatfielder()
    ff._comm.has_proxy = AsyncMock(return_value=False)
    with pytest.raises(ValueError):
        await ff("telescope", "camera")


@pytest.mark.asyncio
async def test_call_stores_filter_binning_and_count() -> None:
    ff = make_flatfielder()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._init_system = AsyncMock()

    await ff("telescope", "camera", filter_name="clear", count=7, binning=(2, 2))

    assert ff._cur_filter == "clear"
    assert ff._cur_binning == (2, 2)
    assert ff._exposures_total == 7


@pytest.mark.asyncio
async def test_call_dispatches_init_state() -> None:
    ff = make_flatfielder()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._init_system = AsyncMock()
    ff._state = FlatFielder.State.INIT

    await ff("telescope", "camera", filters="filters")

    ff._init_system.assert_awaited_once_with("telescope", "camera", "filters")


@pytest.mark.asyncio
async def test_call_dispatches_waiting_state() -> None:
    ff = make_flatfielder()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._wait = AsyncMock()
    ff._state = FlatFielder.State.WAITING

    await ff("telescope", "camera")

    ff._wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_call_dispatches_testing_state() -> None:
    ff = make_flatfielder()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._testing = AsyncMock()
    ff._state = FlatFielder.State.TESTING

    await ff("telescope", "camera")

    ff._testing.assert_awaited_once_with("camera")


@pytest.mark.asyncio
async def test_call_dispatches_running_state() -> None:
    ff = make_flatfielder()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._flat_field = AsyncMock()
    ff._state = FlatFielder.State.RUNNING

    await ff("telescope", "camera")

    ff._flat_field.assert_awaited_once_with("telescope", "camera")


@pytest.mark.asyncio
async def test_call_returns_current_state() -> None:
    ff = make_flatfielder()
    ff._comm.has_proxy = AsyncMock(return_value=True)
    ff._state = FlatFielder.State.FINISHED

    assert await ff("telescope", "camera") == FlatFielder.State.FINISHED


# ── _wait ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wait_transitions_to_testing_when_in_range() -> None:
    ff = make_flatfielder(functions="2.0", min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    await ff._wait()
    assert ff._state == FlatFielder.State.TESTING


@pytest.mark.asyncio
async def test_wait_finishes_when_time_passed() -> None:
    ff = make_flatfielder(functions="20.0", min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    await ff._wait()
    assert ff._state == FlatFielder.State.FINISHED


@pytest.mark.asyncio
async def test_wait_sleeps_when_not_yet_time(mocker) -> None:
    ff = make_flatfielder(functions="0.1", min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    fast_wait = mocker.patch("pyobs.robotic.utils.skyflats.flatfielder.event_wait", AsyncMock(return_value=False))

    await ff._wait()

    fast_wait.assert_awaited_once()
    assert ff._state == FlatFielder.State.INIT  # unchanged


# ── _testing ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_testing_transitions_to_running_when_good() -> None:
    # _testing() doesn't recompute _exptime itself (that's _analyse_image()'s job when
    # given a real image) -- it just evaluates whatever _exptime is already set to.
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 2.0
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="test.fits")
    ff._analyse_image = AsyncMock(return_value=True)

    await ff._testing("camera")

    ff._set_window.assert_awaited_once_with("camera", testing=True)
    ff._take_image.assert_awaited_once_with("camera", broadcast=False)
    ff._analyse_image.assert_awaited_once_with("test.fits")
    assert ff._state == FlatFielder.State.RUNNING


@pytest.mark.asyncio
async def test_testing_finishes_when_time_passed() -> None:
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 20.0
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="test.fits")
    ff._analyse_image = AsyncMock(return_value=True)

    await ff._testing("camera")

    assert ff._state == FlatFielder.State.FINISHED


@pytest.mark.asyncio
async def test_testing_sleeps_when_not_yet_time(mocker) -> None:
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 0.1
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="test.fits")
    ff._analyse_image = AsyncMock(return_value=True)
    fast_wait = mocker.patch("pyobs.robotic.utils.skyflats.flatfielder.event_wait", AsyncMock(return_value=False))

    await ff._testing("camera")

    fast_wait.assert_awaited_once()
    assert ff._state == FlatFielder.State.INIT  # unchanged


# ── _take_image ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_take_image_sets_exptime_type_and_grabs() -> None:
    ff = make_flatfielder()
    ff._exptime = 3.5
    camera = MagicMock(spec=[IExposureTime, IImageType, ICamera])
    camera.set_exposure_time = AsyncMock()
    camera.set_image_type = AsyncMock()
    camera.grab_data = AsyncMock(return_value="flat_001.fits")
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(camera))
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    filename = await ff._take_image("camera", broadcast=True)

    camera.set_exposure_time.assert_awaited_once_with(3.5)
    camera.set_image_type.assert_awaited_once_with(ImageType.SKYFLAT)
    camera.grab_data.assert_awaited_once_with(broadcast=True)
    assert filename == "flat_001.fits"


# ── _set_window ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_window_full_frame_when_not_testing() -> None:
    ff = make_flatfielder()
    camera = MagicMock(spec=[IWindow])
    camera.get_capabilities = MagicMock(
        return_value=WindowCapabilities(full_frame_x=0, full_frame_y=0, full_frame_width=1024, full_frame_height=1024)
    )
    camera.set_window = AsyncMock()
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(camera))

    await ff._set_window("camera", testing=False)

    camera.set_window.assert_awaited_once_with(0, 0, 1024, 1024)


@pytest.mark.asyncio
async def test_set_window_test_frame_when_testing() -> None:
    ff = make_flatfielder(test_frame=(45, 45, 10, 10))
    camera = MagicMock(spec=[IWindow])
    camera.get_capabilities = MagicMock(
        return_value=WindowCapabilities(full_frame_x=0, full_frame_y=0, full_frame_width=1000, full_frame_height=1000)
    )
    camera.set_window = AsyncMock()
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(camera))

    await ff._set_window("camera", testing=True)

    camera.set_window.assert_awaited_once_with(450, 450, 100, 100)


@pytest.mark.asyncio
async def test_set_window_skips_when_no_camera() -> None:
    ff = make_flatfielder()
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(None))

    # should not raise
    await ff._set_window("camera", testing=False)


# ── _analyse_image ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyse_image_returns_false_when_image_missing() -> None:
    vfs = AsyncMock(spec=VirtualFileSystem)
    vfs.read_image = AsyncMock(return_value=None)
    ff = make_flatfielder(vfs=vfs)

    assert await ff._analyse_image("file.fits") is False


@pytest.mark.asyncio
async def test_analyse_image_returns_false_when_counts_too_low() -> None:
    vfs = AsyncMock(spec=VirtualFileSystem)
    vfs.read_image = AsyncMock(return_value=Image(data=np.full((10, 10), 10.0)))
    ff = make_flatfielder(vfs=vfs, min_counts=100)

    assert await ff._analyse_image("file.fits") is False
    assert ff._median == 10.0


@pytest.mark.asyncio
async def test_analyse_image_returns_true_and_recalculates_exptime() -> None:
    vfs = AsyncMock(spec=VirtualFileSystem)
    vfs.read_image = AsyncMock(return_value=Image(data=np.full((10, 10), 1000.0)))
    ff = make_flatfielder(vfs=vfs, target_count=1000, min_counts=100)
    ff._bias_level = 0
    ff._exptime = 1.0

    assert await ff._analyse_image("file.fits") is True
    assert ff._median == 1000.0
    assert ff._exptime == pytest.approx(1.0)  # median already at target -> factor 1.0


@pytest.mark.asyncio
async def test_analyse_image_returns_false_when_deviation_too_large() -> None:
    vfs = AsyncMock(spec=VirtualFileSystem)
    vfs.read_image = AsyncMock(return_value=Image(data=np.full((10, 10), 500.0)))
    ff = make_flatfielder(vfs=vfs, target_count=1000, min_counts=100, allowed_offset_frac=0.2)
    ff._bias_level = 0
    ff._exptime = 1.0

    # frac = |1 - 500/1000| = 0.5, well outside the 0.2 allowed_offset_frac
    assert await ff._analyse_image("file.fits") is False


# ── _get_bias ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_bias_returns_median_and_configures_camera() -> None:
    vfs = AsyncMock(spec=VirtualFileSystem)
    vfs.read_image = AsyncMock(return_value=Image(data=np.full((10, 10), 250.0)))
    ff = make_flatfielder(vfs=vfs)

    camera = MagicMock(spec=[IWindow, IExposureTime, IImageType, ICamera])
    camera.get_capabilities = MagicMock(
        return_value=WindowCapabilities(full_frame_x=0, full_frame_y=0, full_frame_width=100, full_frame_height=100)
    )
    camera.set_window = AsyncMock()
    camera.set_exposure_time = AsyncMock()
    camera.set_image_type = AsyncMock()
    camera.grab_data = AsyncMock(return_value="bias.fits")
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(camera))
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    bias = await ff._get_bias("camera")

    assert bias == 250.0
    camera.set_window.assert_awaited_once_with(0, 0, 100, 100)
    camera.set_exposure_time.assert_awaited_once_with(0.0)
    camera.set_image_type.assert_awaited_once_with(ImageType.BIAS)
    camera.grab_data.assert_awaited_once_with(broadcast=False)


# ── _init_system ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_init_system_detects_dusk_and_transitions_to_waiting() -> None:
    observer = make_twilight_observer(alt_now=10.0, alt_future=5.0)  # getting darker -> DUSK
    ff = make_flatfielder(observer=observer)
    ff._initial_check = MagicMock(return_value=True)
    ff._get_bias = AsyncMock(return_value=123.0)
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(None))

    await ff._init_system("telescope", "camera")

    assert ff._twilight == FlatFielder.Twilight.DUSK
    assert ff._state == FlatFielder.State.WAITING
    assert ff._bias_level == 123.0


@pytest.mark.asyncio
async def test_init_system_detects_dawn() -> None:
    observer = make_twilight_observer(alt_now=5.0, alt_future=10.0)  # getting brighter -> DAWN
    ff = make_flatfielder(observer=observer)
    ff._initial_check = MagicMock(return_value=True)
    ff._get_bias = AsyncMock(return_value=0.0)
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(None))

    await ff._init_system("telescope", "camera")

    assert ff._twilight == FlatFielder.Twilight.DAWN


@pytest.mark.asyncio
async def test_init_system_returns_early_when_time_passed() -> None:
    observer = make_twilight_observer(alt_now=10.0, alt_future=5.0)
    ff = make_flatfielder(observer=observer)
    ff._initial_check = MagicMock(return_value=False)
    ff._get_bias = AsyncMock()

    await ff._init_system("telescope", "camera")

    ff._get_bias.assert_not_called()


@pytest.mark.asyncio
async def test_init_system_sets_binning() -> None:
    observer = make_twilight_observer(10.0, 5.0)
    ff = make_flatfielder(observer=observer)
    ff._initial_check = MagicMock(return_value=True)
    ff._get_bias = AsyncMock(return_value=0.0)
    ff._cur_binning = (2, 2)

    binning_cam = MagicMock(spec=["set_binning"])
    binning_cam.set_binning = AsyncMock()
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(binning_cam))

    await ff._init_system("telescope", "camera")

    binning_cam.set_binning.assert_awaited_once_with(2, 2)


@pytest.mark.asyncio
async def test_init_system_points_telescope_and_sets_filter_when_configured() -> None:
    observer = make_twilight_observer(10.0, 5.0)
    pointing = AsyncMock(spec=SkyFlatsBasePointing)
    ff = make_flatfielder(observer=observer, pointing=pointing)
    ff._initial_check = MagicMock(return_value=True)
    ff._get_bias = AsyncMock(return_value=0.0)
    ff._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(None))
    ff._cur_filter = "clear"

    telescope_proxy = MagicMock(spec=IPointingAltAz)
    filter_proxy = MagicMock(spec=IFilters)
    filter_proxy.set_filter = AsyncMock()

    def proxy_se(name: object, iface: object = None) -> MagicMock:
        if iface is IPointingAltAz:
            return make_proxy_cm(telescope_proxy)
        return make_proxy_cm(filter_proxy)

    ff._comm.proxy = MagicMock(side_effect=proxy_se)

    await ff._init_system("telescope", "camera", "filters")

    assert pointing.await_count == 1
    assert pointing.await_args.args == (telescope_proxy,)
    filter_proxy.set_filter.assert_awaited_once_with("clear")
    assert ff._state == FlatFielder.State.WAITING


# ── _flat_field ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_flat_field_finishes_after_last_exposure() -> None:
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 2.0
    ff._exposures_total = 1
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="flat.fits")
    ff._analyse_image = AsyncMock(return_value=True)

    await ff._flat_field("telescope", "camera")

    assert ff._exposures_done == 1
    assert ff._state == FlatFielder.State.FINISHED


@pytest.mark.asyncio
async def test_flat_field_continues_and_calls_callback() -> None:
    callback = AsyncMock()
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0, callback=callback)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 2.0
    ff._exposures_total = 2
    # _flat_field() is only ever entered while already RUNNING; the in-range branch is a
    # no-op (state simply isn't touched), so start from RUNNING to prove it stays there.
    ff._state = FlatFielder.State.RUNNING
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="flat.fits")
    ff._analyse_image = AsyncMock(return_value=True)

    await ff._flat_field("telescope", "camera")

    assert ff._exposures_done == 1
    assert ff._state == FlatFielder.State.RUNNING
    callback.assert_awaited_once()


@pytest.mark.asyncio
async def test_flat_field_skips_count_when_analysis_fails() -> None:
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 2.0
    ff._exposures_total = 2
    ff._state = FlatFielder.State.RUNNING
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="flat.fits")
    ff._analyse_image = AsyncMock(return_value=False)

    await ff._flat_field("telescope", "camera")

    assert ff._exposures_done == 0
    assert ff._state == FlatFielder.State.RUNNING


@pytest.mark.asyncio
async def test_flat_field_finishes_when_time_passed() -> None:
    ff = make_flatfielder(min_exptime=0.5, max_exptime=5.0)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 20.0
    ff._exposures_total = 100
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="flat.fits")
    ff._analyse_image = AsyncMock(return_value=False)

    await ff._flat_field("telescope", "camera")

    assert ff._state == FlatFielder.State.FINISHED


@pytest.mark.asyncio
async def test_flat_field_points_telescope_when_configured() -> None:
    pointing = AsyncMock(spec=SkyFlatsBasePointing)
    ff = make_flatfielder(pointing=pointing)
    ff._twilight = FlatFielder.Twilight.DUSK
    ff._exptime = 2.0
    ff._exposures_total = 5
    ff._set_window = AsyncMock()
    ff._take_image = AsyncMock(return_value="flat.fits")
    ff._analyse_image = AsyncMock(return_value=False)
    telescope_proxy = MagicMock(spec=IPointingAltAz)
    ff._comm.proxy = MagicMock(return_value=make_proxy_cm(telescope_proxy))

    await ff._flat_field("telescope", "camera")

    assert pointing.await_count == 1
    assert pointing.await_args.args == (telescope_proxy,)


# ── abort ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_abort_sets_event() -> None:
    ff = make_flatfielder()
    assert not ff._abort.is_set()
    await ff.abort()
    assert ff._abort.is_set()
