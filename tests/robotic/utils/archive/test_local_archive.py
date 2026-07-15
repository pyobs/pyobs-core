from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from pyobs.images import Image
from pyobs.robotic.utils.archive.local_archive import LocalArchive
from pyobs.utils.enums import ImageType
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
    rlevel: int = 91,
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
    }


# ── model_post_init / _update_root ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_root_scans_directory_on_init(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers())
    write_fits(tmp_path / "b.fits", **make_frame_headers(filter_name="red"))

    archive = LocalArchive(root=str(tmp_path))

    assert len(archive._data) == 2
    assert set(archive._data["filter"]) == {"clear", "red"}


def test_update_root_handles_missing_headers_gracefully(tmp_path: Path) -> None:
    write_fits(tmp_path / "bare.fits")  # no headers at all

    archive = LocalArchive(root=str(tmp_path))

    assert len(archive._data) == 1
    row = archive._data.iloc[0]
    assert row["date-obs"] is None
    assert row["filter"] is None


def test_update_root_empty_directory(tmp_path: Path) -> None:
    archive = LocalArchive(root=str(tmp_path))
    assert len(archive._data) == 0


# ── list_options ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_options_returns_unique_values(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(filter_name="clear", site="siteA"))
    write_fits(tmp_path / "b.fits", **make_frame_headers(filter_name="red", site="siteB"))
    archive = LocalArchive(root=str(tmp_path))

    options = await archive.list_options()

    assert set(options["filters"]) == {"clear", "red"}
    assert set(options["sites"]) == {"siteA", "siteB"}


# ── list_frames / _filter_data ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_frames_returns_frame_infos(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers())
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames()

    assert len(frames) == 1
    assert frames[0].filename == str(tmp_path / "a.fits")
    assert frames[0].filter_name == "clear"


@pytest.mark.asyncio
async def test_list_frames_filters_by_filter_name(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(filter_name="clear"))
    write_fits(tmp_path / "b.fits", **make_frame_headers(filter_name="red"))
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames(filter_name="red")

    assert len(frames) == 1
    assert frames[0].filter_name == "red"


@pytest.mark.asyncio
async def test_list_frames_filters_by_site_and_telescope(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(site="siteA", telescope="tel1"))
    write_fits(tmp_path / "b.fits", **make_frame_headers(site="siteB", telescope="tel2"))
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames(site="siteB")
    assert len(frames) == 1

    frames = await archive.list_frames(telescope="tel1")
    assert len(frames) == 1


@pytest.mark.asyncio
async def test_list_frames_filters_by_instrument_and_binning(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(instrument="cam1", binning=(1, 1)))
    write_fits(tmp_path / "b.fits", **make_frame_headers(instrument="cam2", binning=(2, 2)))
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames(instrument="cam2")
    assert len(frames) == 1
    assert frames[0].binning == "2x2"

    frames = await archive.list_frames(binning="1x1")
    assert len(frames) == 1


@pytest.mark.asyncio
async def test_list_frames_filters_by_image_type_and_rlevel(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(image_type="object", rlevel=91))
    write_fits(tmp_path / "b.fits", **make_frame_headers(image_type="dark", rlevel=11))
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames(image_type=ImageType.DARK)
    assert len(frames) == 1

    frames = await archive.list_frames(rlevel=91)
    assert len(frames) == 1


@pytest.mark.asyncio
async def test_list_frames_filters_by_night(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(day_obs="2024-01-01"))
    write_fits(tmp_path / "b.fits", **make_frame_headers(day_obs="2024-01-02"))
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames(night="2024-01-02")

    assert len(frames) == 1


@pytest.mark.asyncio
async def test_list_frames_filters_by_start_and_end(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(date_obs="2024-01-01T00:00:00.000"))
    write_fits(tmp_path / "b.fits", **make_frame_headers(date_obs="2024-01-03T00:00:00.000"))
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames(start=Time("2024-01-02T00:00:00.000"))
    assert len(frames) == 1
    assert frames[0].filename == str(tmp_path / "b.fits")

    frames = await archive.list_frames(end=Time("2024-01-02T00:00:00.000"))
    assert len(frames) == 1
    assert frames[0].filename == str(tmp_path / "a.fits")


@pytest.mark.asyncio
async def test_list_frames_empty_when_nothing_matches(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(filter_name="clear"))
    archive = LocalArchive(root=str(tmp_path))

    frames = await archive.list_frames(filter_name="nonexistent")

    assert frames == []


# ── download_frames / download_headers ──────────────────────────────────────


@pytest.mark.asyncio
async def test_download_frames_loads_real_files(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers())
    archive = LocalArchive(root=str(tmp_path))
    frames = await archive.list_frames()

    images = await archive.download_frames(frames)

    assert len(images) == 1
    assert images[0].header["FILTER"] == "clear"


@pytest.mark.asyncio
async def test_download_frames_skips_frames_without_filename(tmp_path: Path) -> None:
    from pyobs.robotic.utils.archive.archive import FrameInfo

    archive = LocalArchive(root=str(tmp_path))
    info = FrameInfo()
    info.filename = None

    images = await archive.download_frames([info])

    assert images == []


@pytest.mark.asyncio
async def test_download_headers_returns_header_dicts(tmp_path: Path) -> None:
    write_fits(tmp_path / "a.fits", **make_frame_headers(filter_name="red"))
    archive = LocalArchive(root=str(tmp_path))
    frames = await archive.list_frames()

    headers = await archive.download_headers(frames)

    assert len(headers) == 1
    assert headers[0]["FILTER"] == "red"


# ── upload_frames ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_frames_is_noop(tmp_path: Path) -> None:
    archive = LocalArchive(root=str(tmp_path))
    # should not raise
    await archive.upload_frames([])
