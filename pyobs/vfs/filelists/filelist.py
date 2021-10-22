from typing import List


class FileList:
    """Base class for file lists."""
    __module__ = 'pyobs.vfs.filelists'

    def __call__(self, filename: str) -> List[str]:
        pass
