import numpy as np
from astropy.table import Table

from pyobs.images.processors.offsets import NStarOffsets


def test_fits2numpy():
    table = Table()
    for k in ["x", "y", "xmin", "xmax", "ymin", "ymax", "xpeak", "ypeak"]:
        table[k] = [1]

    result = NStarOffsets._fits2numpy(table)
    assert all(map(lambda x: x == 0, result.values()))


def test_remove_sources_close_to_border():
    table = Table({"x": [1, 10, 10], "y": [10, 1, 10]})

    result = NStarOffsets.remove_sources_close_to_border(table, (20, 20), 5)
    np.testing.assert_array_equal(result["x"], [10])
    np.testing.assert_array_equal(result["y"], [10])


def test_remove_bad_sources():
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
