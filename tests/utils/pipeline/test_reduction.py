from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pyobs.images import Image
from pyobs.robotic.utils.archive import Archive, FrameInfo
from pyobs.robotic.utils.archive.local_archive import LocalArchive
from pyobs.utils.enums import ImageType
from pyobs.utils.pipeline import MasterCalibCreated, Pipeline, ProgressEvent, Reduction, ScienceFrameProcessed
from pyobs.utils.time import Time


def write_fits(path: Path, **header: object) -> None:
    image = Image(data=np.zeros((2, 2)))
    for key, value in header.items():
        image.header[key] = value
    image.writeto(str(path))


def make_frame_headers(
    date_obs: str = "2024-01-01T03:00:00.000",
    day_obs: str = "2024-01-01",
    binning: tuple[int, int] = (1, 1),
    filter_name: str = "clear",
    image_type: str = "object",
    instrument: str = "cam1",
    site: str = "siteA",
    telescope: str = "tel1",
    rlevel: int = 0,
    fname: str = "raw.fits",
    exptime: float = 30.0,
) -> dict[str, object]:
    return {
        "DATE-OBS": date_obs,
        "DAY-OBS": day_obs,
        "XBINNING": binning[0],
        "YBINNING": binning[1],
        "FILTER": filter_name,
        "IMAGETYP": image_type,
        "INSTRUME": instrument,
        "SITEID": site,
        "TELID": telescope,
        "RLEVEL": rlevel,
        "FNAME": fname,
        "EXPTIME": exptime,
    }


# ── output routing ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_output_routes_to_different_archive_than_input(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    write_fits(in_dir / "raw.fits", **make_frame_headers(fname="raw.fits"))

    archive_in = LocalArchive(root=str(in_dir))
    archive_out = LocalArchive(root=str(out_dir))
    pipeline = Pipeline(steps=[])

    reduction = Reduction(
        archive=archive_in, pipeline=pipeline, output=archive_out, create_calibs=False, calib_science=True
    )
    await reduction("siteA", "2024-01-01")

    # calibrated frame landed in the output archive, not back into the input archive
    assert (out_dir / "raw.fits").exists()
    assert sorted(p.name for p in in_dir.glob("*.fits")) == ["raw.fits"]


@pytest.mark.asyncio
async def test_output_local_path_auto_creates_directory_and_writes_there(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    write_fits(in_dir / "raw.fits", **make_frame_headers(fname="raw.fits"))
    out_dir = tmp_path / "does" / "not" / "exist" / "yet"

    archive = LocalArchive(root=str(in_dir))
    pipeline = Pipeline(steps=[])

    reduction = Reduction(
        archive=archive, pipeline=pipeline, output=str(out_dir), create_calibs=False, calib_science=True
    )

    # directory should already exist after construction, before any write happens
    assert out_dir.is_dir()

    await reduction("siteA", "2024-01-01")

    assert (out_dir / "raw.fits").exists()
    # nothing new was written back into the input archive's directory
    assert sorted(p.name for p in in_dir.glob("*.fits")) == ["raw.fits"]


# ── unexpected kwargs ────────────────────────────────────────────────────────


def test_unexpected_kwarg_raises_type_error(tmp_path: Path) -> None:
    archive = LocalArchive(root=str(tmp_path))
    pipeline = Pipeline(steps=[])

    with pytest.raises(TypeError):
        Reduction(archive=archive, pipeline=pipeline, worker_procs=4)  # type: ignore[call-arg]


# ── calibration fault isolation ─────────────────────────────────────────────


class _FlakyCalibArchive(Archive):
    """Stub archive whose calibration-frame listing fails for one instrument only."""

    fail_instrument: str = "cam2"

    async def list_options(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> dict[str, list[Any]]:
        return {"instruments": ["cam1", "cam2"], "binnings": ["1x1"], "filters": ["clear"]}

    async def list_frames(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> list[FrameInfo]:
        if image_type == ImageType.OBJECT:
            info = FrameInfo()
            info.filename = f"{instrument}.fits"
            return [info]

        # calibration-frame lookup: blow up for one instrument, return too few for the other
        if instrument == self.fail_instrument:
            raise RuntimeError("boom: archive unreachable for this instrument")
        return []

    async def download_frames(self, frames: list[FrameInfo]) -> list[Image]:
        images = []
        for frame in frames:
            image = Image(data=np.zeros((2, 2)))
            if frame.filename is not None:
                image.header["FNAME"] = frame.filename
            images.append(image)
        return images


@pytest.mark.asyncio
async def test_calibration_failure_for_one_combination_does_not_abort_others(tmp_path: Path) -> None:
    archive = _FlakyCalibArchive()
    output = LocalArchive(root=str(tmp_path))
    pipeline = Pipeline(steps=[])

    reduction = Reduction(archive=archive, pipeline=pipeline, output=output, create_calibs=True, calib_science=True)

    # should not raise, despite cam2's calibration-frame lookup blowing up
    await reduction("siteA", "2024-01-01")

    # science calibration still ran (and uploaded) for both instruments
    assert (tmp_path / "cam1.fits").exists()
    assert (tmp_path / "cam2.fits").exists()


# ── progress callback ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_progress_callback_reports_calibs_and_cumulative_science_frames(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    for i in range(3):
        write_fits(in_dir / f"bias{i}.fits", **make_frame_headers(image_type="bias", fname=f"bias{i}.fits"))
        write_fits(in_dir / f"dark{i}.fits", **make_frame_headers(image_type="dark", fname=f"dark{i}.fits"))
    for i in range(3):
        write_fits(in_dir / f"flat{i}.fits", **make_frame_headers(image_type="skyflat", fname=f"flat{i}.fits"))
    write_fits(in_dir / "obj0.fits", **make_frame_headers(fname="obj0.fits"))
    write_fits(in_dir / "obj1.fits", **make_frame_headers(fname="obj1.fits"))

    archive = LocalArchive(root=str(in_dir))
    output = LocalArchive(root=str(tmp_path / "out"))
    pipeline = Pipeline(steps=[])

    events: list[ProgressEvent] = []
    reduction = Reduction(
        archive=archive,
        pipeline=pipeline,
        output=output,
        min_flats=1,
        progress_callback=events.append,
    )
    await reduction("siteA", "2024-01-01")

    calib_events = [e for e in events if isinstance(e, MasterCalibCreated)]
    frame_events = [e for e in events if isinstance(e, ScienceFrameProcessed)]

    assert {e.image_type for e in calib_events} == {ImageType.BIAS, ImageType.DARK, ImageType.SKYFLAT}

    # cumulative index/total across the whole night, not per-batch
    assert [e.index for e in frame_events] == [1, 2]
    assert all(e.total == 2 for e in frame_events)
    assert all(e.status == "ok" for e in frame_events)


# ── per-exptime dark masters ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_master_darks_groups_by_exptime(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    for i in range(3):
        write_fits(in_dir / f"bias{i}.fits", **make_frame_headers(image_type="bias", fname=f"bias{i}.fits"))
    for i in range(3):
        write_fits(
            in_dir / f"dark30_{i}.fits",
            **make_frame_headers(image_type="dark", fname=f"dark30_{i}.fits", exptime=30.0),
        )
    for i in range(3):
        write_fits(
            in_dir / f"dark600_{i}.fits",
            **make_frame_headers(image_type="dark", fname=f"dark600_{i}.fits", exptime=600.0),
        )

    archive = LocalArchive(root=str(in_dir))
    output = LocalArchive(root=str(tmp_path / "out"))
    pipeline = Pipeline(steps=[])

    events: list[ProgressEvent] = []
    reduction = Reduction(
        archive=archive, pipeline=pipeline, output=output, calib_science=False, progress_callback=events.append
    )
    await reduction._create_master_calib("2024-01-01", "cam1", ImageType.BIAS, "1x1")
    masters = await reduction._create_master_darks("2024-01-01", "cam1", "1x1")

    assert sorted(m.header["EXPTIME"] for m in masters) == [30.0, 600.0]
    # longest exptime first, matching DarkBiasScript's own series order
    assert [m.header["EXPTIME"] for m in masters] == [600.0, 30.0]

    dark_events = [e for e in events if isinstance(e, MasterCalibCreated) and e.image_type == ImageType.DARK]
    assert sorted(e.exptime for e in dark_events) == [30.0, 600.0]

    # two distinct master files landed in the output archive, one per exptime
    dark_files = sorted(p.name for p in (tmp_path / "out").glob("*-dark-*"))
    assert len(dark_files) == 2
    assert dark_files[0] != dark_files[1]


@pytest.mark.asyncio
async def test_create_master_darks_skips_under_populated_group_individually(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    for i in range(3):
        write_fits(in_dir / f"bias{i}.fits", **make_frame_headers(image_type="bias", fname=f"bias{i}.fits"))
    # enough at 30s, too few at 600s
    for i in range(3):
        write_fits(
            in_dir / f"dark30_{i}.fits",
            **make_frame_headers(image_type="dark", fname=f"dark30_{i}.fits", exptime=30.0),
        )
    for i in range(2):
        write_fits(
            in_dir / f"dark600_{i}.fits",
            **make_frame_headers(image_type="dark", fname=f"dark600_{i}.fits", exptime=600.0),
        )

    archive = LocalArchive(root=str(in_dir))
    output = LocalArchive(root=str(tmp_path / "out"))
    pipeline = Pipeline(steps=[])

    reduction = Reduction(archive=archive, pipeline=pipeline, output=output, calib_science=False)
    await reduction._create_master_calib("2024-01-01", "cam1", ImageType.BIAS, "1x1")
    masters = await reduction._create_master_darks("2024-01-01", "cam1", "1x1")

    assert [m.header["EXPTIME"] for m in masters] == [30.0]


@pytest.mark.asyncio
async def test_create_master_darks_no_bias_skips_all_groups(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    for i in range(3):
        write_fits(
            in_dir / f"dark30_{i}.fits",
            **make_frame_headers(image_type="dark", fname=f"dark30_{i}.fits", exptime=30.0),
        )

    archive = LocalArchive(root=str(in_dir))
    output = LocalArchive(root=str(tmp_path / "out"))
    pipeline = Pipeline(steps=[])

    reduction = Reduction(archive=archive, pipeline=pipeline, output=output, calib_science=False)
    masters = await reduction._create_master_darks("2024-01-01", "cam1", "1x1")

    assert masters == []


@pytest.mark.asyncio
async def test_create_master_darks_legacy_fallback_when_all_darks_lack_exptime(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    for i in range(3):
        write_fits(in_dir / f"bias{i}.fits", **make_frame_headers(image_type="bias", fname=f"bias{i}.fits"))
    for i in range(3):
        headers = make_frame_headers(image_type="dark", fname=f"dark{i}.fits")
        del headers["EXPTIME"]
        write_fits(in_dir / f"dark{i}.fits", **headers)

    archive = LocalArchive(root=str(in_dir))
    output = LocalArchive(root=str(tmp_path / "out"))
    pipeline = Pipeline(steps=[])

    events: list[ProgressEvent] = []
    reduction = Reduction(
        archive=archive, pipeline=pipeline, output=output, calib_science=False, progress_callback=events.append
    )
    await reduction._create_master_calib("2024-01-01", "cam1", ImageType.BIAS, "1x1")
    masters = await reduction._create_master_darks("2024-01-01", "cam1", "1x1")

    # one combined master, not zero -- and it's not tagged with a made-up exptime
    assert len(masters) == 1
    assert "EXPTIME" not in masters[0].header

    dark_events = [e for e in events if isinstance(e, MasterCalibCreated) and e.image_type == ImageType.DARK]
    assert len(dark_events) == 1
    assert dark_events[0].exptime is None

    # filename formatting didn't blow up despite the missing EXPTIME
    dark_files = list((tmp_path / "out").glob("*-dark-*"))
    assert len(dark_files) == 1
    assert "unknown" in dark_files[0].name


@pytest.mark.asyncio
async def test_create_master_darks_no_dark_frames_returns_empty(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    for i in range(3):
        write_fits(in_dir / f"bias{i}.fits", **make_frame_headers(image_type="bias", fname=f"bias{i}.fits"))

    archive = LocalArchive(root=str(in_dir))
    output = LocalArchive(root=str(tmp_path / "out"))
    pipeline = Pipeline(steps=[])

    reduction = Reduction(archive=archive, pipeline=pipeline, output=output, calib_science=False)
    masters = await reduction._create_master_darks("2024-01-01", "cam1", "1x1")

    assert masters == []


@pytest.mark.asyncio
async def test_progress_callback_error_in_callback_does_not_abort_reduction(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    write_fits(in_dir / "obj0.fits", **make_frame_headers(fname="obj0.fits"))

    archive = LocalArchive(root=str(in_dir))
    output = LocalArchive(root=str(tmp_path / "out"))
    pipeline = Pipeline(steps=[])

    def broken_callback(event: ProgressEvent) -> None:
        raise RuntimeError("boom")

    reduction = Reduction(
        archive=archive,
        pipeline=pipeline,
        output=output,
        create_calibs=False,
        progress_callback=broken_callback,
    )
    await reduction("siteA", "2024-01-01")

    assert (tmp_path / "out" / "obj0.fits").exists()
