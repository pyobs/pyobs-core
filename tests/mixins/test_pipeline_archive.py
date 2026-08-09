from typing import Any

import pytest

from pyobs.images import Image, ImageProcessor
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.object import Object


class _TestPipeline(Object, PipelineMixin):
    def __init__(self, steps: list[dict[str, Any] | ImageProcessor], archive: Any = None, **kwargs: Any):
        Object.__init__(self, **kwargs)
        PipelineMixin.__init__(self, steps, archive=archive)


class _ArchiveAwareStep(ImageProcessor):
    """Records whatever archive value it was constructed with, so tests can check it."""

    def __init__(self, archive: Any = "no-archive-given", **kwargs: Any):
        super().__init__(**kwargs)
        self.archive = archive

    async def __call__(self, image: Image) -> Image:
        return image


class _NoArchiveStep(ImageProcessor):
    """A step that doesn't declare an archive parameter at all -- confirms an
    unrequested archive is silently absorbed via **kwargs rather than erroring."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    async def __call__(self, image: Image) -> Image:
        return image


@pytest.mark.asyncio
async def test_step_without_own_archive_gets_pipeline_archive():
    pipeline = _TestPipeline(
        steps=[{"class": "tests.mixins.test_pipeline_archive._ArchiveAwareStep"}],
        archive={"class": "fake-archive-config"},
    )
    step = pipeline._PipelineMixin__pipeline_steps[0]
    assert step.archive == {"class": "fake-archive-config"}


@pytest.mark.asyncio
async def test_step_with_own_archive_is_not_overridden():
    pipeline = _TestPipeline(
        steps=[
            {
                "class": "tests.mixins.test_pipeline_archive._ArchiveAwareStep",
                "archive": {"class": "step-specific-archive"},
            }
        ],
        archive={"class": "pipeline-default-archive"},
    )
    step = pipeline._PipelineMixin__pipeline_steps[0]
    assert step.archive == {"class": "step-specific-archive"}


@pytest.mark.asyncio
async def test_step_without_archive_param_is_unaffected():
    """A step whose __init__ doesn't declare `archive` must not error just because a
    pipeline-level archive was configured -- it's absorbed and dropped via **kwargs."""
    pipeline = _TestPipeline(
        steps=[{"class": "tests.mixins.test_pipeline_archive._NoArchiveStep"}],
        archive={"class": "fake-archive-config"},
    )
    assert len(pipeline._PipelineMixin__pipeline_steps) == 1


@pytest.mark.asyncio
async def test_no_pipeline_archive_leaves_steps_unaffected():
    pipeline = _TestPipeline(steps=[{"class": "tests.mixins.test_pipeline_archive._ArchiveAwareStep"}])
    step = pipeline._PipelineMixin__pipeline_steps[0]
    assert step.archive == "no-archive-given"
