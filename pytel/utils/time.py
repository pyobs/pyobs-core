import astropy.time


class Time(astropy.time.Time):
    def __hash__(self):
        if self.ndim != 0:
            raise TypeError("unhashable type: '{}'".format(self.__class__.__name__))
        return hash((self.jd1, self.jd2, self.scale))


__all__ = ['Time']
