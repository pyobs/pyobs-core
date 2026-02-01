from pyobs.utils.grids.filters import GridFilterValue
from pyobs.utils.grids.grid import RegularSphericalGrid


def test_valuefilter() -> None:
    grid = RegularSphericalGrid(5, 5)
    grid2 = GridFilterValue(grid=grid, y_gte=0)
    points = list(grid2)
    assert len(points) == 15
    for p in points:
        assert p[0] >= 0.0
        assert p[1] >= 0.0
