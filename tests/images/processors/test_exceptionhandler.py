import logging
from unittest.mock import Mock

import pytest

from pyobs.images import ImageProcessor, Image
from pyobs.images.processors import ExceptionHandler

import pyobs.utils.exceptions as exc

class MockImageProcessor(ImageProcessor):

    async def __call__(self, image: Image) -> Image:
        return image


@pytest.mark.asyncio
async def test_exception_handler_no_exception() -> None:
    image = Image()
    exception_handler = ExceptionHandler(MockImageProcessor())

    result = await exception_handler(image)

    assert image == result


@pytest.mark.asyncio
async def test_exception_handler_exception(caplog) -> None:
    image = Image()
    exception_handler = ExceptionHandler(MockImageProcessor())
    exception_handler._processor = Mock(side_effect=exc.ImageError("Some error"))

    with caplog.at_level(logging.WARNING):
        result = await exception_handler(image)

    assert caplog.messages[0] == "Some error"

    assert image is not result


@pytest.mark.asyncio
async def test_exception_handler_exception_w_header() -> None:
    image = Image()
    exception_handler = ExceptionHandler(MockImageProcessor(), "WCSERR")
    exception_handler._processor = Mock(side_effect=exc.ImageError("Some error"))

    result = await exception_handler(image)

    assert result.header["WCSERR"] == 1