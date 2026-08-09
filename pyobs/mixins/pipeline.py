from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pyobs.images import Image, ImageProcessor
from pyobs.object import Object
from pyobs.utils.exceptions import ImageError

if TYPE_CHECKING:
    from pyobs.robotic.utils.archive import Archive

log = logging.getLogger(__name__)


class PipelineMixin:
    """Mixin for a module that needs to implement an image pipeline."""

    __module__ = "pyobs.mixins"

    def __init__(
        self,
        steps: list[dict[str, Any] | ImageProcessor] | None = None,
        archive: dict[str, Any] | Archive | None = None,
        **kwargs: Any,
    ):
        """Initializes the mixin.

        Args:
            steps: Pipeline steps to run on images.
            archive: Default archive config/object for steps that accept one (e.g.
                Calibration) and don't already specify their own -- lets a pipeline's
                steps share the archive it was itself given, instead of repeating the
                same archive config in every step that needs one. Steps that don't
                declare an archive parameter just absorb and drop it via their own
                **kwargs, the same as any other unrecognized Object kwarg.
        """

        # store
        if isinstance(self, Object):
            steps = [] if steps is None else steps
            self.__pipeline_steps = [
                self.add_child_object(self._with_default_archive(step, archive), ImageProcessor) for step in steps
            ]

        else:
            raise ValueError("This class is no Object.")

    @staticmethod
    def _with_default_archive(
        step: dict[str, Any] | ImageProcessor, archive: dict[str, Any] | Archive | None
    ) -> dict[str, Any] | ImageProcessor:
        if archive is not None and isinstance(step, dict) and "archive" not in step:
            return {**step, "archive": archive}
        return step

    async def reset_pipeline(self) -> None:
        """Resets all previous state of the involved image processors."""
        for step in self.__pipeline_steps:
            await step.reset()

    async def run_pipeline(self, image: Image) -> Image:
        """Run the pipeline on the given image.

        Each step is run, and an ImageError it raises is handled according to the step's
        on_error setting (default "raise"): re-raised, dispatched to the step's handle_error(),
        logged, or ignored. Non-ImageError exceptions always propagate.

        Args:
            image: Image to run pipeline on.

        Returns:
            Image after pipeline run.
        """

        for step in self.__pipeline_steps:
            try:
                image = await step(image)
            except ImageError as e:
                if step.on_error == "raise":
                    raise
                elif step.on_error == "error":
                    image = step.handle_error(image, e)
                elif step.on_error == "info":
                    log.info("Step %s: %s", type(step).__name__, e)
                elif step.on_error == "ignore":
                    pass

        # finished
        return image


__all__ = ["PipelineMixin"]
