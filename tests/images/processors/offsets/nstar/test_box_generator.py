import numpy as np
import pytest
from astropy.table import Table

from pyobs.images import Image
from pyobs.images.processors.offsets.nstar._box_generator import _BoxGenerator


def test_check_sources_count() -> None:
    table = Table()
    with pytest.raises(ValueError):
        _BoxGenerator(5.0, 10)._check_sources_count(table)


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

    generator = _BoxGenerator(2.0, 1)

    result = generator(image)
    np.testing.assert_array_equal(result[0], np.ones((5, 5)))