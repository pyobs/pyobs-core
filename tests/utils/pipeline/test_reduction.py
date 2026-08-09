from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pyobs.images import Image
from pyobs.robotic.utils.archive import Archive, FrameInfo
from pyobs.robotic.utils.archive.local_archive import LocalArchive
from pyobs.utils.enums import ImageType
from pyobs.utils.pipeline import Pipeline, Reduction
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
