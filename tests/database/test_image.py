from astroplan import Observer
from astropy.io import fits
import datetime

from pyobs.database import Database, Image, session_context


def test_add_from_fits():
    # create sqlite database in memory
    Database.connect('sqlite://')

    # create observer
    observer = Observer.at_site('SAAO', timezone='utc')

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
    image = Image.add_from_fits('test.fits', hdr, observer)

    # got something?
    assert image is True

    # now check the database
    with session_context() as session:
        # check some entries in image
        image = session.query(Image).first()
        assert image.exp_time == 100
        assert image.filter == 'clear'
