import logging
from typing import Union, List, Dict, Any, Optional
from pyobs.images import ImageProcessor, Image

from pyobs.object import Object

log = logging.getLogger(__name__)


class PipelineMixin:
    """Mixin for a module that needs to implement an image pipeline."""

    __module__ = "pyobs.mixins"

    def __init__(self, steps: Optional[List[Union[Dict[str, Any], ImageProcessor]]] = None, **kwargs: Any):
        """Initializes the mixin.

        Args:
            steps: Pipeline steps to run on images.
        """

        # store
        if isinstance(self, Object):
            steps = [] if steps is None else steps
            self.__pipeline_steps = [self.add_child_object(step, ImageProcessor) for step in steps]

        else:
            raise ValueError("This class is no Object.")

    async def reset_pipeline(self) -> None:
        """Resets all previous state of the involved image processors."""
        for step in self.__pipeline_steps:
            await step.reset()

    async def run_pipeline(self, image: Image) -> Image:
        """Run the pipeline on the given image.

        Args:
            image: Image to run pipeline on.

        Returns:
            Image after pipeline run.
        """

        # loop steps, just let any exception pass
        for step in self.__pipeline_steps:
            image = await step(image)

        # finished
        return image


__all__ = ["PipelineMixin"]
