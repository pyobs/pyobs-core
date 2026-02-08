import io
from typing import Any

import pandas as pd
from astroplan import Observer
from astropy.coordinates import SkyCoord, EarthLocation

from pyobs.utils.grids.filters import GridFilterValue, FromList, ConvertGridToSkyCoord, ConvertGridFrame
from pyobs.utils.grids.grid import RegularSphericalGrid
from pyobs.utils.time import Time

mag2_stars_csv = """
RA_ICRS,DE_ICRS,Gmag
243.58621066034,-03.69496770833,2.016425
014.17745099821,+60.71672280471,2.064583
086.93912852502,-09.66960713755,2.077826
109.28559423279,-37.09744448528,2.083237
006.57215550146,-42.30782032569,2.089977
263.73419686427,+12.55900984328,2.108286
046.29487462678,+38.83980896875,2.111629
305.55710787667,+40.25667361143,2.113725
274.40609045185,-36.76242931759,2.116495
221.24648617077,+27.07431575777,2.183352
074.24843702624,+33.16601472319,2.197542
311.55475901193,+33.97170031236,2.210965
139.27236864316,-59.27517582046,2.213786
296.56498571047,+10.61325270383,2.223692
190.37799302256,-48.95978360110,2.227056
002.29906542823,+59.14897576410,2.232691
083.00165624930,-00.29907889258,2.248773
120.89585713760,-40.00307350941,2.254294
093.71906923879,+22.50675368193,2.262038
233.67254376294,+26.71429517475,2.269370
059.50764202201,-13.50901261093,2.270793
200.98237336533,+54.92525907860,2.282647
275.24868220695,-29.82822386701,2.296982
"""


def test_valuefilter() -> None:
    grid = RegularSphericalGrid(5, 5)
    grid2 = GridFilterValue(grid=grid, y_gte=0)
    points = list(grid2)
    assert len(points) == 15
    for p in points:
        assert p[0] >= 0.0
        assert p[1] >= 0.0


def test_fromlistfilter(mocker: Any) -> None:
    time = Time("2020-01-01T00:00:00")
    mocker.patch("astropy.time.Time.now", return_value=time)

    observer = Observer(location=EarthLocation.of_site("SAAO"))
    grid = RegularSphericalGrid(5, 5)
    grid2 = ConvertGridToSkyCoord(grid=grid, frame="altaz", observer=observer, location=observer.location)
    grid3 = ConvertGridFrame(grid=grid2, frame="icrs", observer=observer, location=observer.location)

    # first four points in grid3 are:
    # (300.74143117, 32.31848662)>, <SkyCoord (ICRS): (ra, dec) in deg
    # (301.11699682, 77.31697295)>, <SkyCoord (ICRS): (ra, dec) in deg
    # (120.51733394, 57.68253014)>, <SkyCoord (ICRS): (ra, dec) in deg
    # (120.64901723, 12.68148442)>, <SkyCoord (ICRS): (ra, dec) in deg

    grid4 = FromList(grid=grid3, csv_file="", max_distance=90)
    with io.StringIO(mag2_stars_csv) as sio:
        data = pd.read_csv(sio)

    grid4._data = SkyCoord(data["RA_ICRS"], data["DE_ICRS"], unit="deg", frame="icrs")
    data_points = list(grid4)

    # first four points in grid4 are:
    # (305.55710788, 40.25667361)>, <SkyCoord (ICRS): (ra, dec) in deg
    # (2.29906543, 59.14897576)>, <SkyCoord (ICRS): (ra, dec) in deg
    # (74.24843703, 33.16601472)>, <SkyCoord (ICRS): (ra, dec) in deg
    # (93.71906924, 22.50675368)>, <SkyCoord (ICRS): (ra, dec) in deg

    assert data_points[0] == grid4._data[7]
    assert data_points[1] == grid4._data[15]
    assert data_points[2] == grid4._data[10]
    assert data_points[3] == grid4._data[18]
