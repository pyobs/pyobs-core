"""
Camera modules.
TODO: write doc
"""

__title__ = "Cameras"

from .basecamera import BaseCamera
from .basespectrograph import BaseSpectrograph
from .basevideo import BaseVideo
from .dummycamera import DummyCamera
from .dummyspectrograph import DummySpectrograph
from .pipelinecamera import PipelineCamera
from .videoframes import Frame, FrameRecord, StartSource

__all__ = [
    "BaseCamera",
    "BaseVideo",
    "BaseSpectrograph",
    "DummyCamera",
    "DummySpectrograph",
    "Frame",
    "FrameRecord",
    "PipelineCamera",
    "StartSource",
]
