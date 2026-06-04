__title__ = "Source Detection"

from .daophot import DaophotSourceDetection
from .pysep import SepSourceDetection
from .simpledisk import SimpleDisk
from .sourcedetection import SourceDetection

__all__ = ["SourceDetection", "SepSourceDetection", "DaophotSourceDetection", "SimpleDisk"]
