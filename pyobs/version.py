import importlib.metadata
from typing import Tuple


__version__ = importlib.metadata.version('pyobs-core')


def version_tuple() -> Tuple[int, ...]:
    return tuple(map(int, (__version__.split("."))))


__all__ = ['__version__', 'version_tuple']
