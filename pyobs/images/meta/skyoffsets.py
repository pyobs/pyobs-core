from typing import Tuple

from astropy.coordinates import SkyCoord, BaseCoordinateFrame, Angle


class SkyOffsets:
    def __init__(self, coord0: SkyCoord, coord1: SkyCoord):
        self.coord0 = coord0
        self.coord1 = coord1

    def separation(self, frame: BaseCoordinateFrame = None) -> Angle:
        """Returns separatation between both coordinates, either in their own or a given frame.

        Args:
            frame: Coordinate frame to use, or None to use coordinates' own frames.

        Returns:
            Angle between coordinates.
        """

        # convert and return separation
        coord0, coord1 = self._to_frame(frame)
        return coord0.separation(coord1)

    def spherical_offsets(self, frame: BaseCoordinateFrame = None) -> Tuple[Angle, Angle]:
        """Calculates spherical offset from first coordinate to second.

        Args:
            frame: Coordinate frame to use, or None to use coordinates' own frames.

        Returns:
            Two angles for offset in lat and lon.
        """

        # convert and return offset
        coord0, coord1 = self._to_frame(frame)
        return coord0.spherical_offsets_to(coord1)

    def _to_frame(self, frame: BaseCoordinateFrame = None) -> Tuple[SkyCoord, SkyCoord]:
        """

        Args:
            frame: Coordinate frame to use, or None to use coordinates' own frames.

        Returns:
            Both coordinates converted to given frame (or originals, if no frame is given).
        """
        if frame is None:
            return self.coord0, self.coord1
        else:
            return self.coord0.transform_to(frame), self.coord1.transform_to(frame)


__all__ = ['SkyOffsets']
