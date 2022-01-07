from pathlib import Path
from single_source import get_version


__version__ = get_version(__name__, Path(__file__).parent.parent)


def version() -> str:
    return "0.0.0" if __version__ is None else __version__


__all__ = ["version", "__version__"]
