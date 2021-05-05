from .event import Event


class TelescopeMovingEvent(Event):
    """Event to be sent when the telescope has started moving."""
    __module__ = 'pyobs.events'

    def __init__(self, ra: float = None, dec: float = None, alt: float = None, az: float = None):
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
    def ra(self):
        return self.data['ra']

    @property
    def dec(self):
        return self.data['dec']

    @property
    def alt(self):
        return self.data['alt']

    @property
    def az(self):
        return self.data['az']


__all__ = ['TelescopeMovingEvent']
