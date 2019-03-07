from astropy.io import fits
import datetime

from pyobs import Environment
from pyobs.database import Database, Image, session_context, Night, Observation, Task, Project


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
    assert image is True

    # now check the database
    with session_context() as session:
        # we should have a Night object with a value of 2019-02-03
        night = session.query(Night).first()
        assert night is not None
        assert night.night == datetime.date(2019, 2, 3)

        # an observation with name Observation
        obs = session.query(Observation).first()
        assert obs is not None
        assert obs.name == 'Observation'

        # check some entries in image
        image = session.query(Image).first()
        assert image.exp_time == 100
        assert image.filter == 'clear'
