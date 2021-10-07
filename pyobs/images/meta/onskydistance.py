from astropy.coordinates import Angle


class OnSkyDistance:
    def __init__(self, distance: Angle):
        self.distance = distance


__all__ = ['OnSkyDistance']
