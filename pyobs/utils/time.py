from datetime import datetime
import astropy.time


class Time(astropy.time.Time):
    _now_offset = astropy.time.TimeDelta(0)

    def __hash__(self):
        if self.ndim != 0:
            raise TypeError("unhashable type: '{}'".format(self.__class__.__name__))
        return hash((self.jd1, self.jd2, self.scale))

    @classmethod
    def set_offset_to_now(cls, delta: astropy.time.TimeDelta):
        cls._now_offset = delta

    @classmethod
    def now(cls):
        """
        Creates a new object corresponding to the instant in time this
        method is called.

        .. note::
            "Now" is determined using the `~datetime.datetime.utcnow`
            function, so its accuracy and precision is determined by that
            function.  Generally that means it is set by the accuracy of
            your system clock.

        Returns
        -------
        nowtime
            A new `Time` object (or a subclass of `Time` if this is called from
            such a subclass) at the current time.
        """
        # call `utcnow` immediately to be sure it's ASAP
        dtnow = datetime.utcnow()
        return cls(val=dtnow, format='datetime', scale='utc') + cls._now_offset


__all__ = ['Time']
