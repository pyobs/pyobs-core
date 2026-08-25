from __future__ import annotations

import pytest

from pyobs.robotic.scripts.calibration.darkbias import DarkBiasScript
from pyobs.robotic.scripts.calibration.pointing import PointingScript
from pyobs.robotic.scripts.calibration.skyflats import SkyFlatsScript
from pyobs.robotic.scripts.control.cases import CasesRunner
from pyobs.robotic.scripts.control.conditional import ConditionalRunner
from pyobs.robotic.scripts.control.parallel import ParallelRunner
from pyobs.robotic.scripts.control.selector import SelectorScript
from pyobs.robotic.scripts.control.sequential import SequentialRunner
from pyobs.robotic.scripts.imaging.autofocus import AutoFocusScript
from pyobs.robotic.scripts.imaging.imaging import (
    AcquisitionConfig,
    Configuration,
    GuidingConfig,
    ImagingScript,
    InstrumentConfig,
)
from pyobs.robotic.scripts.script import Script
from pyobs.robotic.scripts.utils.callmodule import CallModuleScript
from pyobs.robotic.scripts.utils.debugtrigger import DebugTriggerScript
from pyobs.robotic.scripts.utils.log import LogScript
from pyobs.robotic.utils.skyflats.priorities.archive import ArchiveSkyflatPriorities
from pyobs.robotic.utils.skyflats.priorities.const import ConstSkyflatPriorities

# Every Script subclass and nested config model that pyobs-robotic-backend's script builder
# can render as a form, per the survey in issue #811.
MODELS = [
    Script,
    DarkBiasScript,
    PointingScript,
    SkyFlatsScript,
    CasesRunner,
    ConditionalRunner,
    ParallelRunner,
    SequentialRunner,
    SelectorScript,
    AutoFocusScript,
    ImagingScript,
    AcquisitionConfig,
    GuidingConfig,
    InstrumentConfig,
    Configuration,
    CallModuleScript,
    DebugTriggerScript,
    LogScript,
    ArchiveSkyflatPriorities,
    ConstSkyflatPriorities,
]


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__qualname__)
def test_all_fields_have_a_description(model: type) -> None:
    """Regression guard for issue #811: pyobs-robotic-backend's script builder renders each
    field's JSON-schema `description` as form help text, so every field on every model that can
    end up in that form must have one, not just a default."""
    missing = [name for name, info in model.model_fields.items() if not info.description]
    assert not missing, f"{model.__qualname__} field(s) missing Field(description=...): {missing}"
