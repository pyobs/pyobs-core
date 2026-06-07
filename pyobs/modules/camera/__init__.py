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

__all__ = ["BaseCamera", "BaseVideo", "BaseSpectrograph", "DummyCamera", "DummySpectrograph", "PipelineCamera"]
