from sqlalchemy import Column, Integer, String

from .base import Base
from .table import GetByNameMixin


class Instrument(Base, GetByNameMixin):
    __tablename__ = 'pytel_instrument'

    id = Column(Integer, comment='Unique ID of instrument', primary_key=True)
    name = Column(String(30), comment='Name of instrument', unique=True, nullable=False)

    def __init__(self, name):
        self.name = name


__all__= ['Instrument']
