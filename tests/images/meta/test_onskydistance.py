from astropy.coordinates import Angle
from pyobs.images.meta import OnSkyDistance


def test_onskydistance():
    distance = Angle(1.0, unit="deg")
    meta = OnSkyDistance(distance)

    assert meta.distance.unit == distance.unit
    assert meta.distance.value == distance.value
