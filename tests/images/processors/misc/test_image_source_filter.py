import numpy as np
import pytest
from astropy.table import Table

from pyobs.images import Image
from pyobs.images.processors.misc import ImageSourceFilter


def test_fits2numpy() -> None:
    table = Table()
    for k in ["x", "y", "xmin", "xmax", "ymin", "ymax", "xpeak", "ypeak"]:
        table[k] = [1]

    result = ImageSourceFilter._fits2numpy(table)
    assert all(map(lambda x: x == 0, result.values()))


def test_remove_sources_close_to_border() -> None:
    table = Table({"x": [1, 10, 19, 10, 10], "y": [10, 1, 10, 19, 10]})

    source_filter = ImageSourceFilter(2, 10, 10, 10)
    result = source_filter.remove_sources_close_to_border(table, (20, 20))
    np.testing.assert_array_equal(result["x"], [10])
    np.testing.assert_array_equal(result["y"], [10])


def test_remove_bad_sources() -> None:
    table = Table({
        "peak": [50000, 5001, 5002, 5003, 5004, 5005, 5006],
        "tnpix": [10, 2, 100, 10, 10, 10, 10],
        "ellipticity": [0.3, 0.3, 0.3, 0.5, 0.3, 0.3, 0.3],
        "background": [100, 100, 100, 100, -1, 50000, 100]
    })

    result = ImageSourceFilter(10, 10, 3, 0.4).remove_bad_sources(table)

    np.testing.assert_array_equal(result["peak"], [5006])
    np.testing.assert_array_equal(result["tnpix"], [10])
    np.testing.assert_array_equal(result["ellipticity"], [0.3])
    np.testing.assert_array_equal(result["background"], [100])


def test_select_brightest_sources() -> None:
    table = Table({"flux": list(range(3))})

    result = ImageSourceFilter(5.0, 2, 3, 2)._select_brightest_sources(table)
    np.testing.assert_array_equal(result["flux"], list(reversed(range(1, 3))))


@pytest.mark.asyncio
async def test_call() -> None:
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

    filter = ImageSourceFilter(2.0, 10, 3, 1)

    result = await filter(image)
    assert result.catalog == sources
