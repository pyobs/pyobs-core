import logging
from typing import List, Any

from .filelist import FileList


log = logging.getLogger(__name__)


class TestingFileList(FileList):
    """File list for testing."""
    __module__ = 'pyobs.vfs.filelists'

    def __init__(self, *args: Any, **kwargs: Any):
        pass

    def __call__(self, filename: str) -> List[str]:
        return [
            __file__
        ]


__all__ = ['TestingFileList']
