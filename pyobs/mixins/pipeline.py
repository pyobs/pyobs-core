from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

from pyobs.images import Image, ImageProcessor
from pyobs.object import Object, get_class_from_string
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
                same archive config in every step that needs one. Only injected into a
                step's config if that step's class actually declares an `archive`
                parameter (checked via signature inspection); steps that don't declare
                one never receive it, rather than receiving-then-silently-dropping it.
        """

        # store
        if isinstance(self, Object):
            steps = [] if steps is None else steps
            self.__pipeline_steps = [
                self.add_child_object(self._with_default_archive(step, archive), ImageProcessor) for step in steps
            ]

        else:
            raise ValueError("This class is no Object.")

        super().__init__(**kwargs)

    @staticmethod
    def _accepts_archive(class_name: str) -> bool:
        """Whether the given class declares an `archive` parameter anywhere in its `__init__` MRO."""
        try:
            klass = get_class_from_string(class_name)
        except Exception:
            return False
        for cls in klass.__mro__:
            init = cls.__dict__.get("__init__")
            if init is None:
                continue
            try:
                sig = inspect.signature(init)
            except (TypeError, ValueError):
                continue
            if "archive" in sig.parameters:
                return True
        return False

    @staticmethod
    def _with_default_archive(
        step: dict[str, Any] | ImageProcessor, archive: dict[str, Any] | Archive | None
    ) -> dict[str, Any] | ImageProcessor:
        if (
            archive is not None
            and isinstance(step, dict)
            and "archive" not in step
            and "class" in step
            and PipelineMixin._accepts_archive(step["class"])
        ):
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
