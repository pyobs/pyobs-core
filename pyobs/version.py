import importlib.metadata
from typing import Tuple


def version() -> str:
    return importlib.metadata.version('pyobs-core')


__version__ = version()


def version_tuple(v: str = __version__) -> Tuple[int, ...]:
    return tuple(map(int, (v.split("."))))


__all__ = ['version', '__version__', 'version_tuple']
