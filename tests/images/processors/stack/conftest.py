from __future__ import annotations

from typing import Any

import numpy as np
from astropy.table import Table

from pyobs.images import Image


def make_cube(data: Any, exptime: float | None = 2.0, frames: bool = True) -> Image:
    """Build a stack cube like IDataStack.grab_stack() produces."""
    data = np.asarray(data)
    count = data.shape[0]
    # start from Image(data)'s header, so NAXISn come first like in real products -- Image()
    # appends them at the end of a given header, which astropy then refuses to write
    header = Image(data).header
    header["CTYPE3"] = "FRAME"
    header["NFRAMES"] = count
    header["DATE-OBS"] = "2026-09-27T20:00:00.000"
    header["DATE-END"] = "2026-09-27T20:00:10.000"
    if exptime is not None:
        header["EXPTIME"] = exptime
    table = None
    if frames:
        table = Table(
            rows=[(i, "2026-09-27T20:00:00.000", exptime or 0.0) for i in range(count)],
            names=("FRAME", "DATE-OBS", "EXPTIME"),
        )
    return Image(data, header=header, frames=table)
