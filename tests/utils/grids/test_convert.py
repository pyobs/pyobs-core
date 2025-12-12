from astropy.coordinates import SkyCoord

from pyobs.utils.grids.filters import ConvertGridToSkyCoord
from pyobs.utils.grids.grid import RegularSphericalGrid


def test_convertgridtoskycoord() -> None:
    grid = RegularSphericalGrid(5, 5)
    grid_all = [p for p in grid]

    grid = RegularSphericalGrid(5, 5)
    grid2 = ConvertGridToSkyCoord(grid=grid, frame="altaz")
    grid2_all = list(grid2)

    for i in range(len(grid_all)):
        sk = grid2_all[i]
        assert isinstance(sk, SkyCoord)
        assert hasattr(sk, "az")
        assert hasattr(sk, "alt")
        assert grid_all[i][0] == float(sk.az.degree)
        assert grid_all[i][1] == float(sk.alt.degree)
