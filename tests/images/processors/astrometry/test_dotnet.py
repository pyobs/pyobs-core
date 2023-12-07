import json
import logging

import numpy as np
import pytest
from astropy.io.fits import Header
from astropy.table import QTable
from astropy.wcs import WCS

import pyobs.utils.exceptions as exc
from pyobs.images import Image
from pyobs.images.processors.astrometry import AstrometryDotNet


def test_init_default():
    url = "https://nova.astrometry.net"

    astrometry = AstrometryDotNet(url)

    assert astrometry.url == url
    assert astrometry._request_builder._source_count == 50
    assert astrometry._request_builder._radius == 3.0
    assert astrometry.timeout == 10
    assert astrometry.exceptions is True


def test_init_w_values():
    url = "https://nova.astrometry.net"
    source_count = 100
    radius = 10.0
    timeout = 60
    exceptions = False

    astrometry = AstrometryDotNet(url, source_count, radius, timeout, exceptions)

    assert astrometry._request_builder._source_count == source_count
    assert astrometry._request_builder._radius == radius
    assert astrometry.timeout == timeout
    assert astrometry.exceptions == exceptions


def check_astrometry_header_exist(image, inverse=False) -> bool:
    keywords = [
        "CTYPE1",
        "CTYPE2",
        "CRPIX1",
        "CRPIX2",
        "CRVAL1",
        "CRVAL2",
        "CD1_1",
        "CD1_2",
        "CD2_1",
        "CD2_2",
    ]

    keyword_in_hdr = [x in image.header for x in keywords]

    if inverse:
        return not any(keyword_in_hdr)
    else:
        return all(keyword_in_hdr)


@pytest.mark.asyncio
async def test_call_n_catalog_n_exception():
    image = Image()
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=False)

    result_img = await astrometry(image)
    assert check_astrometry_header_exist(result_img, True)


@pytest.mark.asyncio
async def test_call_n_catalog_w_exception():
    image = Image()
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=True)

    with pytest.raises(exc.ImageError):
        await astrometry(image)


def mock_catalog(size: int):
    x = [0.0] * size + [np.nan, np.nan]
    y = [0.0] * size + [np.nan, np.nan]
    flux = [1.0] * size + [np.nan, np.nan]
    peak = [1.0] * size + [np.nan, np.nan]

    cat = QTable([x, y, flux, peak], names=("x", "y", "flux", "peak"))

    return cat


@pytest.mark.asyncio
async def test_call_small_catalog_n_exception():
    image = Image()
    image.catalog = mock_catalog(2)
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=False)

    result_img = await astrometry(image)
    assert check_astrometry_header_exist(result_img, True)
    assert result_img.header["WCSERR"] == 1


@pytest.mark.asyncio
async def test_call_small_catalog_w_exception():
    image = Image()
    image.catalog = mock_catalog(2)
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=True)

    with pytest.raises(exc.ImageError):
        await astrometry(image)


@pytest.mark.asyncio
async def test_call_cdelt_n_exception():
    image = Image()
    image.catalog = mock_catalog(5)
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=False)

    result_img = await astrometry(image)
    assert check_astrometry_header_exist(result_img, True)
    assert result_img.header["WCSERR"] == 1


@pytest.mark.asyncio
async def test_call_cdelt_w_exception():
    image = Image()
    image.catalog = mock_catalog(5)
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=True)

    with pytest.raises(exc.ImageError):
        await astrometry(image)


class MockResponse:
    """https://stackoverflow.com/questions/57699218/how-can-i-mock-out-responses-made-by-aiohttp-clientsession"""

    def __init__(self, text, status):
        self._text = text
        self.status = status

    async def text(self):
        return self._text

    async def json(self):
        return json.loads(self._text)

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.mark.asyncio
async def test_call_post_error_n_exception(mocker, mock_header):
    image = Image()
    image.header = mock_header
    image.catalog = mock_catalog(5)
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=False)

    resp = MockResponse(json.dumps({}), 404)
    mock = mocker.patch("aiohttp.ClientSession.post", return_value=resp)

    result_image = await astrometry(image)
    assert result_image.header["WCSERR"] == 1

    assert mock.call_args_list[0].args[0] == url
    assert mock.call_args_list[0].kwargs["timeout"] == 10

    data = mock.call_args_list[0].kwargs["json"]

    assert data == {
        "crpix-x": image.header["CRPIX1"],
        "crpix-y": image.header["CRPIX2"],
        "ra": image.header["TEL-RA"],
        "dec": image.header["TEL-DEC"],
        "scale_low": 3600 * 0.9,
        "scale_high": 3600 * 1.1,
        "radius": 3.0,
        "nx": image.header["NAXIS1"],
        "ny": image.header["NAXIS2"],
        "x": [0.0, 0.0, 0.0, 0.0, 0.0],
        "y": [0.0, 0.0, 0.0, 0.0, 0.0],
        "flux": [1.0, 1.0, 1.0, 1.0, 1.0],
    }


@pytest.mark.asyncio
async def test_call_post_error_w_exception(mocker, mock_header):
    image = Image()
    image.header = mock_header
    image.catalog = mock_catalog(5)
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=True)

    resp = MockResponse(json.dumps({}), 404)
    mocker.patch("aiohttp.ClientSession.post", return_value=resp)

    with pytest.raises(exc.ImageError):
        await astrometry(image)


@pytest.fixture()
def mock_response_data():
    keywords = [
        "CRPIX1",
        "CRPIX2",
        "CRVAL1",
        "CRVAL2",
        "CD1_1",
        "CD1_2",
        "CD2_1",
        "CD2_2",
    ]

    data = {x: 0.0 for x in keywords}
    data["CTYPE1"] = "RA"
    data["CTYPE2"] = "DEC"

    return data


@pytest.mark.asyncio
async def test_call_success(mocker, mock_response_data, mock_header):
    image = Image()
    image.header = mock_header
    image.catalog = mock_catalog(5)
    url = "https://nova.astrometry.net"
    astrometry = AstrometryDotNet(url, exceptions=False)

    resp = MockResponse(json.dumps(mock_response_data), 200)
    mocker.patch("aiohttp.ClientSession.post", return_value=resp)

    result_image = await astrometry(image)
    assert result_image.header["WCSERR"] == 0
    assert all(result_image.header[x] == mock_response_data[x] for x in mock_response_data.keys())
