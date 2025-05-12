from pyobs.utils.grids.pipeline import GridPipeline


def test_pipeline() -> None:
    pipeline = GridPipeline([
        {
            'class': 'pyobs.utils.grids.spherical.RegularSphericalGrid',
            'n_lat': 5,
            'n_lon': 5
        },
        {
            'class': 'pyobs.utils.grids.filters.GridFilterValue',
            'y_gte': 0
        }
    ])

    points = list(pipeline)
    assert len(points) == 15
    for p in points:
        assert p[0] >= 0.
        assert p[1] >= 0.