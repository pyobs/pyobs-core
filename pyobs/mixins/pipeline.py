import logging
from typing import Union, List
from pyobs.images import ImageProcessor, Image

from pyobs.object import get_object

log = logging.getLogger(__name__)


class PipelineMixin:
    """Mixin for a module that needs to implement an image pipeline."""
    __module__ = 'pyobs.mixins'

    def __init__(self, pipeline: List[Union[dict, ImageProcessor]]):
        """Initializes the mixin.

        Args:
            pipeline: Pipeline steps to run on images.
        """

        # store
        self.__pipeline_steps = [get_object(step, ImageProcessor) for step in pipeline]

    def run_pipeline(self, image: Image) -> Image:
        """Run the pipeline on the given image.

        Args:
            image: Image to run pipeline on.

        Returns:
            Image after pipeline run.
        """

        # loop steps
        for step in self.__pipeline_steps:
            try:
                image = step(image)
            except Exception as e:
                log.exception(f'Could not run pipeline step {step.__class__.__name__}: {e}')

        # finished
        return image


__all__ = ['PipelineMixin']
