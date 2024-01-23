import numpy as np
import pytest
from astropy.table import Table
from photutils.psf import EPSFStar
from pytest_mock import MockerFixture

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from pyobs.images.processors.offsets import NStarOffsets
from pyobs.images.processors.offsets._gaussian_fitter import GaussianFitter


@pytest.mark.asyncio
async def test_reset() -> None:
    offsets = NStarOffsets()
    offsets.ref_boxes = [np.ones((2, 2))]
    await offsets.reset()

    assert len(offsets.ref_boxes) == 0


def test_get_box_size() -> None:
    assert NStarOffsets._get_box_size(4, 2) == 8

    assert NStarOffsets._get_box_size(4, None) == 20


def test_fits2numpy() -> None:
    table = Table()
    for k in ["x", "y", "xmin", "xmax", "ymin", "ymax", "xpeak", "ypeak"]:
        table[k] = [1]

    result = NStarOffsets._fits2numpy(table)
    assert all(map(lambda x: x == 0, result.values()))


def test_remove_sources_close_to_border() -> None:
    table = Table({"x": [1, 10, 19, 10, 10], "y": [10, 1, 10, 19, 10]})

    result = NStarOffsets.remove_sources_close_to_border(table, (20, 20), 5)
    np.testing.assert_array_equal(result["x"], [10])
    np.testing.assert_array_equal(result["y"], [10])


def test_remove_bad_sources() -> None:
    table = Table({
        "peak": [50000, 5001, 5002, 5003, 5004, 5005, 5006],
        "tnpix": [10, 2, 100, 10, 10, 10, 10],
        "ellipticity": [0.3, 0.3, 0.3, 0.5, 0.3, 0.3, 0.3],
        "background": [100, 100, 100, 100, -1, 50000, 100]
    })

    result = NStarOffsets().remove_bad_sources(table)

    np.testing.assert_array_equal(result["peak"], [5006])
    np.testing.assert_array_equal(result["tnpix"], [10])
    np.testing.assert_array_equal(result["ellipticity"], [0.3])
    np.testing.assert_array_equal(result["background"], [100])


def test_select_brightest_sources() -> None:
    table = Table({"flux": list(range(3))})

    result = NStarOffsets._select_brightest_sources(2, table)
    np.testing.assert_array_equal(result["flux"], list(reversed(range(1, 3))))


def test_check_sources_count() -> None:
    table = Table()
    with pytest.raises(ValueError):
        NStarOffsets()._check_sources_count(table)


@pytest.mark.asyncio
async def test_boxes_from_ref(mocker: MockerFixture) -> None:
    sources = Table({
        "x": [10],
        "y": [10],
        "flux": [10],
        "peak": [100],
        "tnpix": [10],
        "ellipticity": [0.0],
        "background": [1.0]
    })

    image = Image(data=np.ones((20, 20)), catalog=sources)

    offsets = NStarOffsets()
    mocker.patch.object(offsets, "run_pipeline", return_value=image)

    result = await offsets._boxes_from_ref(image, 5)
    np.testing.assert_array_equal(result[0], np.ones((5, 5)))


def test_calculate_offsets_invalid_data() -> None:
    image = Image()

    offsets = NStarOffsets()

    assert offsets._calculate_offsets(image) == (None, None)


def test_calculate_offsets() -> None:
    data = np.array([
        [
            GaussianFitter._gauss2d([x, y], 1, 2, 10, 10, 1, 1) for x in range(21)
        ] for y in range(21)
    ])

    offsets = NStarOffsets()
    offsets.ref_boxes = [EPSFStar(data[7:14, 7:14], origin=(8, 8))]

    result = offsets._calculate_offsets(Image(data=data))
    np.testing.assert_almost_equal(result, (-1.0, -1.0), 2)


@pytest.mark.asyncio
async def test_call_init(mocker: MockerFixture) -> None:
    image = Image()
    offsets = NStarOffsets()

    boxes = [EPSFStar(np.ones((10, 10)), origin=(8, 8))]
    mocker.patch.object(offsets, "_boxes_from_ref", return_value=boxes)

    result = await offsets(image)
    assert result.get_meta(PixelOffsets).dx == 0.0
    assert result.get_meta(PixelOffsets).dy == 0.0

    assert offsets.ref_boxes == boxes


@pytest.mark.asyncio
async def test_call_invalid_init(mocker: MockerFixture) -> None:
    image = Image()
    image.set_meta(PixelOffsets(1.0, 1.0))
    offsets = NStarOffsets()
    mocker.patch.object(offsets, "_boxes_from_ref", side_effect=ValueError)

    result = await offsets(image)

    assert not result.has_meta(PixelOffsets)

    assert offsets.ref_boxes == []


@pytest.mark.asyncio
async def test_call(mocker: MockerFixture) -> None:
    image = Image()
    offsets = NStarOffsets()
    offsets.ref_boxes = [EPSFStar(np.ones((10, 10)), origin=(8, 8))]
    mocker.patch.object(offsets, "_calculate_offsets", return_value=(1.0, -1.0))

    result = await offsets(image)
    assert result.get_meta(PixelOffsets).dx == 1.0
    assert result.get_meta(PixelOffsets).dy == -1.0

