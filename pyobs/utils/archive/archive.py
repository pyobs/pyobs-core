from typing import List

from pyobs.interfaces import ICamera
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time


class FrameInfo:
    def __init__(self):
        self.id = None
        self.filename = None
        self.filter_name = None
        self.binning = None
        self.dateobs = None


class Archive:
    def list_options(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                     image_type: ImageType = None, binning: str = None, filter_name: str = None,
                    rlevel: int = None):
        raise NotImplementedError

    def list_frames(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                    image_type: ImageType = None, binning: str = None, filter_name: str = None,
                    rlevel: int = None) -> List[FrameInfo]:
        raise NotImplementedError

    def download_frames(self, frames: List[FrameInfo]) -> List['Image']:
        raise NotImplementedError

    def upload_frames(self, frames: List['Image']):
        raise NotImplementedError


__all__ = ['FrameInfo', 'Archive']
