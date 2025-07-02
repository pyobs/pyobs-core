import pytest

from pyobs.images.processors.astrometry._dotnet_request import _DotNetRequest


@pytest.mark.asyncio
async def test_generate_request_error_msg():
    request = _DotNetRequest({})
    request._response_data = {}
    assert request._generate_request_error_msg() == "Could not connect to astrometry service."

    request._response_data = {"error": "Could not find WCS file."}
    assert request._generate_request_error_msg() == "Could not determine WCS."

    request._response_data = {"error": "Test"}
    assert request._generate_request_error_msg() == "Received error from astrometry service: Test"
