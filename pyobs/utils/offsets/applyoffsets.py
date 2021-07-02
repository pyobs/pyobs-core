from astropy.coordinates import EarthLocation

from pyobs.images import Image
from pyobs.interfaces import ITelescope


class ApplyOffsets:
    """Apply offsets from a given image to a given telescope."""
    __module__ = 'pyobs.utils.offsets'

    def __call__(self, image: Image, telescope: ITelescope, location: EarthLocation) -> bool:
        """Take the pixel offsets stored in the meta data of the image and apply them to the given telescope.

        Args:
            image: Image to take offsets and WCS from.
            telescope: Telescope to apply offsets to.
            location: Observer location on Earth.

        Returns:
            Whether offsets have been applied successfully.
        """
        return False


__all__ = ['ApplyOffsets']
