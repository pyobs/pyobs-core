import io
import logging
import os
import tarfile


log = logging.getLogger(__name__)


class TestingFileList:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, filename: str) -> list:
        return [
            __file__
        ]


__all__ = ['TestingFileList']
