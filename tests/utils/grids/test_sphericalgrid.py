from pyobs.utils.grids.spherical import RegularSphericalGrid, GraticuleSphericalGrid


def test_regularsphericalgrid() -> None:
    grid = RegularSphericalGrid(5, 5)
    points = list(grid)
    assert len(points) == 25
    assert (0.0, -90.0) in points
    assert (0.0, 0.0) in points


def test_regularsphericalgrid_append_last() -> None:
    """Reinsert one point back into the grid."""
    grid = RegularSphericalGrid(5, 5)
    x = True
    i = 0
    for p in grid:
        i += 1
        if p == (216.0, 45.0) and x:
            x = False
            grid.append_last()
    assert i == 26


def test_graticulesphericalgrid() -> None:
    grid = GraticuleSphericalGrid(100)
    points = list(grid)
    assert len(points) == 99
