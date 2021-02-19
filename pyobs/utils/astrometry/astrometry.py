from pyobs.images import Image


class Astrometry:
    def __init__(self, *args, **kwargs):
        pass

    def find_solution(self, image: Image) -> bool:
        """Find astrometric solution on given image.

        Args:
            image: Image to analyse.

        Returns:
            Success or not.
        """
        raise NotImplementedError


__all__ = ['Astrometry']
