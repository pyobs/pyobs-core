from pytel.database import Database
import sqlalchemy as sa


def test_create():
    # create sqlite database in memory
    Database.connect('sqlite://')

    # get all table names
    table_names = sa.inspect(Database.engine).get_table_names()

    # check a few
    assert 'pytel_image' in table_names
    assert 'pytel_task' in table_names
