from .IRoof import IRoof


class IDome(IRoof):
    """
    Interface for an observatory enclosure that has a direction when it is opened,
    e.g. a rotating dome or a partially closed clamshell.  The is_observable()
    method can then be used to determine if a telescope could look in a particular
    direction (given by RA,DEC) and not be blocked.
    """

    def is_observable(self, ra: float, dec: float, *args, **kwargs) -> bool:
        """whether and for long an object at the given coordinates is visible"""
        raise NotImplementedError


__all__ = ['IDome']
