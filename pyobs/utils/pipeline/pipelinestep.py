from pyobs.images import Image


class PipelineStep:
    def __call__(self, image: Image) -> Image:
        """Processes an image.

        Args:
            image: Image to process.

        Returns:
            Processed image.
        """
        raise NotImplementedError


__all__ = ['PipelineStep']
