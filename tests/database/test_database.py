from pyobs.database import Database
import sqlalchemy as sa


def test_create():
    # create sqlite database in memory
    Database.connect('sqlite://')

    # get all table names
    table_names = sa.inspect(Database.engine).get_table_names()

    # check a few
    assert 'pyobs_image' in table_names
