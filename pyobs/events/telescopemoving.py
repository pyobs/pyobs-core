from typing import Optional

from .event import Event


class TelescopeMovingEvent(Event):
    """Event to be sent when the telescope has started moving."""
    __module__ = 'pyobs.events'

    def __init__(self, ra: Optional[float] = None, dec: Optional[float] = None,
                 alt: Optional[float] = None, az: Optional[float] = None):
        """Initializes a new telescope moving event.

        Either the pair ra/dec, or alt/az should be set, never both. The former implies tracking on the given
        coordinates.

        Args:
            ra: Right ascension of coordinates for tracking.
            dec: Declination of coordinates for tracking.
            alt: Altitude of fixed position to move to.
            az: Azimuth of fixed position to move to.
        """
        Event.__init__(self)
        self.data = {
            'ra': ra,
            'dec': dec,
            'alt': alt,
            'az': az
        }

    @property
    def ra(self) -> Optional[float]:
        return self.data['ra']

    @property
    def dec(self) -> Optional[float]:
        return self.data['dec']

    @property
    def alt(self) -> Optional[float]:
        return self.data['alt']

    @property
    def az(self) -> Optional[float]:
        return self.data['az']


__all__ = ['TelescopeMovingEvent']
