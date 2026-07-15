from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from pyobs.images import Image
from pyobs.robotic.utils.archive.pyobs_archive import PyobsArchive, PyobsArchiveFrameInfo
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time


class MockResponse:
    def __init__(
        self,
        json: Any = None,
        text: str = "",
        data: bytes = b"",
        status: int = 200,
        cookies: dict[str, Any] | None = None,
    ) -> None:
        self._json = json
        self._text = text
        self._data = data
        self.status = status
        self.cookies = cookies or {}

    async def json(self) -> Any:
        return self._json

    async def text(self) -> str:
        return self._text

    async def read(self) -> bytes:
        return self._data

    async def __aenter__(self) -> MockResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


def make_archive(**kwargs: object) -> PyobsArchive:
    return PyobsArchive(url="http://archive.example/", token="tok", **kwargs)


def make_frame_dict(id: int = 1, basename: str = "img.fits", url: str = "download/1/") -> dict[str, Any]:
    return {
        "id": id,
        "basename": basename,
        "DATE_OBS": "2024-01-01T03:00:00.000",
        "FILTER": "clear",
        "binning": "1x1",
        "url": url,
    }


# ── model_post_init ──────────────────────────────────────────────────────────


def test_init_sets_headers_and_timeout() -> None:
    archive = make_archive()
    assert archive._headers == {"Authorization": "Token tok"}
    assert archive._timeout.total == 30


# ── PyobsArchiveFrameInfo ────────────────────────────────────────────────────


def test_frame_info_parses_fields() -> None:
    info = PyobsArchiveFrameInfo(make_frame_dict(id=42, basename="x.fits"))

    assert info.id == 42
    assert info.filename == "x.fits"
    assert info.filter_name == "clear"
    assert info.binning == 1
    assert isinstance(info.dateobs, Time)
    assert info.url == "download/1/"


# ── _build_query ─────────────────────────────────────────────────────────────


def test_build_query_includes_all_given_params() -> None:
    params = PyobsArchive._build_query(
        start=Time("2024-01-01T00:00:00.000"),
        end=Time("2024-01-02T00:00:00.000"),
        night="2024-01-01",
        site="siteA",
        telescope="tel1",
        instrument="cam1",
        image_type=ImageType.OBJECT,
        binning="1x1",
        filter_name="clear",
        rlevel=91,
    )

    assert params["night"] == "2024-01-01"
    assert params["SITE"] == "siteA"
    assert params["TELESCOPE"] == "tel1"
    assert params["INSTRUMENT"] == "cam1"
    assert params["IMAGETYPE"] == ImageType.OBJECT
    assert params["binning"] == "1x1"
    assert params["FILTER"] == "clear"
    assert params["RLEVEL"] == 91
    assert params["start"] == "2024-01-01T00:00:00.000"
    assert params["end"] == "2024-01-02T00:00:00.000"


def test_build_query_empty_when_nothing_given() -> None:
    assert PyobsArchive._build_query() == {}


# ── list_options ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_options_returns_json_on_success(mocker) -> None:
    archive = make_archive()
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(json={"filters": ["clear"]}))

    result = await archive.list_options()

    assert result == {"filters": ["clear"]}


@pytest.mark.asyncio
async def test_list_options_raises_on_non_200(mocker) -> None:
    archive = make_archive()
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(text="server error", status=500))

    with pytest.raises(ValueError):
        await archive.list_options()


# ── list_frames ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_frames_single_page(mocker) -> None:
    archive = make_archive()
    response = MockResponse(json={"results": [make_frame_dict(id=1)], "count": 1})
    mocker.patch("aiohttp.ClientSession.get", return_value=response)

    frames = await archive.list_frames()

    assert len(frames) == 1
    assert frames[0].id == 1


@pytest.mark.asyncio
async def test_list_frames_paginates_across_multiple_pages(mocker) -> None:
    archive = make_archive()
    page1 = MockResponse(json={"results": [make_frame_dict(id=1)], "count": 2})
    page2 = MockResponse(json={"results": [make_frame_dict(id=2)], "count": 2})
    mocker.patch("aiohttp.ClientSession.get", side_effect=[page1, page2])

    frames = await archive.list_frames()

    assert [f.id for f in frames] == [1, 2]


@pytest.mark.asyncio
async def test_list_frames_raises_on_non_200(mocker) -> None:
    archive = make_archive()
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(status=404))

    with pytest.raises(ValueError):
        await archive.list_frames()


# ── download_frames ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_frames_returns_images(mocker) -> None:
    archive = make_archive()
    info = PyobsArchiveFrameInfo(make_frame_dict())
    image_bytes = Image(data=np.zeros((2, 2))).to_bytes()
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(data=image_bytes))

    images = await archive.download_frames([info])

    assert len(images) == 1


@pytest.mark.asyncio
async def test_download_frames_skips_wrong_info_type() -> None:
    from pyobs.robotic.utils.archive.archive import FrameInfo

    archive = make_archive()
    images = await archive.download_frames([FrameInfo()])

    assert images == []


@pytest.mark.asyncio
async def test_download_frames_skips_on_os_error(mocker) -> None:
    archive = make_archive()
    info = PyobsArchiveFrameInfo(make_frame_dict())
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(data=b"not a fits file"))

    images = await archive.download_frames([info])

    assert images == []


# ── download_headers ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_headers_builds_dict(mocker) -> None:
    archive = make_archive()
    info = PyobsArchiveFrameInfo(make_frame_dict())
    response = MockResponse(json={"results": [{"key": "FILTER", "value": "clear"}, {"key": "EXPTIME", "value": 1.0}]})
    mocker.patch("aiohttp.ClientSession.get", return_value=response)

    headers = await archive.download_headers([info])

    assert headers == [{"FILTER": "clear", "EXPTIME": 1.0}]


@pytest.mark.asyncio
async def test_download_headers_handles_missing_results_key(mocker) -> None:
    archive = make_archive()
    info = PyobsArchiveFrameInfo(make_frame_dict())
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(json={}))

    headers = await archive.download_headers([info])

    assert headers == [{}]


# ── upload_frames ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_frames_success(mocker) -> None:
    archive = make_archive()
    get_response = MockResponse(cookies={"csrftoken": mocker.MagicMock(value="csrf-token")})
    post_response = MockResponse(json={"created": 1})
    mocker.patch("aiohttp.ClientSession.get", return_value=get_response)
    mocker.patch("aiohttp.ClientSession.post", return_value=post_response)

    image = Image(data=np.zeros((2, 2)))
    image.header["FNAME"] = "img.fits"

    # should not raise
    await archive.upload_frames([image])


@pytest.mark.asyncio
async def test_upload_frames_raises_on_non_200(mocker) -> None:
    archive = make_archive()
    get_response = MockResponse(cookies={"csrftoken": mocker.MagicMock(value="csrf-token")})
    post_response = MockResponse(status=500)
    mocker.patch("aiohttp.ClientSession.get", return_value=get_response)
    mocker.patch("aiohttp.ClientSession.post", return_value=post_response)

    image = Image(data=np.zeros((2, 2)))
    image.header["FNAME"] = "img.fits"

    with pytest.raises(ValueError):
        await archive.upload_frames([image])


@pytest.mark.asyncio
async def test_upload_frames_raises_when_created_zero_with_errors(mocker) -> None:
    archive = make_archive()
    get_response = MockResponse(cookies={"csrftoken": mocker.MagicMock(value="csrf-token")})
    post_response = MockResponse(json={"created": 0, "errors": "bad file"})
    mocker.patch("aiohttp.ClientSession.get", return_value=get_response)
    mocker.patch("aiohttp.ClientSession.post", return_value=post_response)

    image = Image(data=np.zeros((2, 2)))
    image.header["FNAME"] = "img.fits"

    with pytest.raises(ValueError, match="bad file"):
        await archive.upload_frames([image])


@pytest.mark.asyncio
async def test_upload_frames_raises_when_created_zero_without_errors(mocker) -> None:
    archive = make_archive()
    get_response = MockResponse(cookies={"csrftoken": mocker.MagicMock(value="csrf-token")})
    post_response = MockResponse(json={"created": 0})
    mocker.patch("aiohttp.ClientSession.get", return_value=get_response)
    mocker.patch("aiohttp.ClientSession.post", return_value=post_response)

    image = Image(data=np.zeros((2, 2)))
    image.header["FNAME"] = "img.fits"

    with pytest.raises(ValueError):
        await archive.upload_frames([image])
