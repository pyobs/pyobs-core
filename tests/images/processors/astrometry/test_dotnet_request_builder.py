from pyobs.images.processors.astrometry._dotnet_request_builder import _DotNetRequestBuilder
from tests.images.processors.astrometry.test_dotnet import mock_catalog


def test_filter_catalog():
    request_builder = _DotNetRequestBuilder(50, 3.0)

    catalog = mock_catalog(2)
    pandas_catalog = catalog.to_pandas()
    pandas_catalog.iloc[0]["peak"] = 60001
    request_builder._catalog = pandas_catalog
    request_builder._filter_catalog()

    assert True not in request_builder._catalog.isna()
    assert len(request_builder._catalog[request_builder._catalog["peak"] >= 6000]) == 0
