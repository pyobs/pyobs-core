from typing import Any

import pytest

import pyobs.utils.exceptions as exc
from pyobs.images import Image, ImageProcessor
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.object import Object


class _TestPipeline(Object, PipelineMixin):
    def __init__(self, steps: list[dict[str, Any] | ImageProcessor], **kwargs: Any):
        Object.__init__(self, **kwargs)
        PipelineMixin.__init__(self, steps)


class _TagStep(ImageProcessor):
    """Marks the image with a header entry, so tests can tell whether a step ran."""

    def __init__(self, tag: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.tag = tag

    async def __call__(self, image: Image) -> Image:
        image.header[self.tag] = True
        return image


class _RaisingStep(ImageProcessor):
    def __init__(self, message: str = "boom", **kwargs: Any):
        super().__init__(**kwargs)
        self.message = message

    async def __call__(self, image: Image) -> Image:
        raise exc.ImageError(self.message)

    def handle_error(self, image: Image, error: exc.ImageError) -> Image:
        image.header["HANDLED"] = error.message
        return image


class _NonImageErrorStep(ImageProcessor):
    async def __call__(self, image: Image) -> Image:
        raise ValueError("not an ImageError")


@pytest.mark.asyncio
async def test_on_error_raise_aborts_pipeline():
    pipeline = _TestPipeline([_RaisingStep(on_error="raise"), _TagStep("AFTER")])

    with pytest.raises(exc.ImageError):
        await pipeline.run_pipeline(Image())


@pytest.mark.asyncio
async def test_on_error_error_dispatches_to_handle_error():
    pipeline = _TestPipeline([_RaisingStep(on_error="error"), _TagStep("AFTER")])

    result = await pipeline.run_pipeline(Image())

    assert result.header["HANDLED"] == "boom"
    assert result.header["AFTER"] is True


@pytest.mark.asyncio
async def test_on_error_info_passes_image_through(caplog):
    caplog.set_level("INFO")
    pipeline = _TestPipeline([_RaisingStep(on_error="info"), _TagStep("AFTER")])

    result = await pipeline.run_pipeline(Image())

    assert "HANDLED" not in result.header
    assert result.header["AFTER"] is True
    assert any("boom" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_on_error_ignore_passes_image_through_silently(caplog):
    pipeline = _TestPipeline([_RaisingStep(on_error="ignore"), _TagStep("AFTER")])

    result = await pipeline.run_pipeline(Image())

    assert "HANDLED" not in result.header
    assert result.header["AFTER"] is True
    assert not any("boom" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_non_image_error_always_propagates():
    pipeline = _TestPipeline([_NonImageErrorStep(on_error="ignore"), _TagStep("AFTER")])

    with pytest.raises(ValueError):
        await pipeline.run_pipeline(Image())


@pytest.mark.asyncio
async def test_handle_error_raising_repropagates():
    class _ReraisingStep(_RaisingStep):
        def handle_error(self, image: Image, error: exc.ImageError) -> Image:
            raise error

    pipeline = _TestPipeline([_ReraisingStep(on_error="error")])

    with pytest.raises(exc.ImageError):
        await pipeline.run_pipeline(Image())


def test_on_error_validation():
    with pytest.raises(ValueError):
        _TagStep("X", on_error="not-a-mode")


@pytest.mark.asyncio
async def test_astrometry_dotnet_exceptions_false_dispatches_to_handle_error():
    from pyobs.images.processors.astrometry import AstrometryDotNet

    astrometry = AstrometryDotNet("https://nova.astrometry.net", exceptions=False)
    pipeline = _TestPipeline([astrometry])

    result = await pipeline.run_pipeline(Image())

    assert result.header["WCSERR"] == 1
