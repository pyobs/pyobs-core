from astropy.io import fits

from pytel import Environment
from pytel.database import Database, Image


def test_add_from_fits():
    # create sqlite database in memory
    Database.connect('sqlite://')

    # create environment
    env = Environment(timezone='utc', location={'longitude': 20.8, 'latitude': -32.4, 'elevation': 1798.})

    # create dummy header
    hdr = fits.Header({
        'DATE-OBS': '2019-02-04T00:37:00.000',
        'PROJECT': 'Project',
        'TASK': 'Task',
        'OBS': 'Observation',
        'NAXIS1': 100,
        'NAXIS2': 100,
        'OBJECT': 'Object',
        'EXPTIME': 100,
        'FILTER': 'clear',
        'DATAMEAN': 42.
    })

    # add image
    image = Image.add_from_fits('test.fits', hdr, env)

    # got something?
    assert image is not None

