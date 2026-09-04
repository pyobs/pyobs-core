# GUI access levels for Pydantic config fields

**Repos:** pyobs-core, pyftscontrol (pyobs-iagvt)

When a GUI renders a Pydantic model as a form and needs to hide advanced fields behind a
basic/expert toggle (or hide some fields entirely), tag each `Field` with an ordinal `level`
instead of inventing per-field booleans. A field is shown when its level is `<=` the GUI's
currently selected level.

```python
from pyobs.utils.enums import AccessLevel

class MyConfig(BaseModel):
    exposure_time: float = Field(
        default=1.0, json_schema_extra={"level": AccessLevel.BASIC}
    )
    gain: int = Field(
        default=0, json_schema_extra={"level": AccessLevel.EXPERT}
    )
    protocol_flag: int = Field(
        default=0, json_schema_extra={"level": AccessLevel.HIDDEN}
    )
```

`AccessLevel` (`pyobs/utils/enums.py`) has three members: `BASIC = 0`, `EXPERT = 1`,
`HIDDEN = 2`. A GUI's mode toggle only ever offers `BASIC`/`EXPERT` as selectable levels; `HIDDEN`
is above any selectable level, so those fields never appear regardless of mode — no separate
"hidden" flag needed.

## Why not two booleans

The pattern this replaces (`pyftscontrol`'s `FTSConfigMain`, before this convention existed) used
independent `show_basic`/`show_expert` booleans per field. In practice only three of the four
combinations ever occurred — `(False, False)` (hidden), `(False, True)` (expert-only), `(True,
True)` (always shown) — because "shown in basic mode but not expert mode" isn't a meaningful
state. That's an ordinal relationship wearing two-boolean clothing; `AccessLevel` names it
directly and extends to a future third UI tier (e.g. a debug mode) without a new field, whereas
booleans would need a third flag for every existing field.

## Why `AccessLevel` isn't shared by import everywhere

`AccessLevel` lives in pyobs-core because most consumers already depend on it. But standalone
tools with no pyobs-core dependency (e.g. `pyftscontrol`, a Qt tool that talks to an FTS
controller directly and has no reason to pull in pyobs-core's astropy/XMPP/etc. dependency chain)
should define their own local `IntEnum` with matching member values (`BASIC = 0`, `EXPERT = 1`,
`HIDDEN = 2`) rather than adding the dependency. `IntEnum` compares by value, so a structurally
identical local copy is interchangeable with `pyobs.utils.enums.AccessLevel` for every purpose
that matters here (`<=` comparisons against a GUI's current level) — the convention is the
contract, not a shared class.

## How this was decided

Came up 2026-09-04 while generalizing `pyftscontrol`'s `FTSConfigMain` basic/expert toggle
(`show_basic`/`show_expert` in `ftsconfig.py`, consumed by `gui_ftscontrol.py`) into something
other pyobs GUIs could reuse. `pyobs/utils/config.py` and `pyobs/utils/pydantic.py` were both
considered and rejected as the home for the enum: `config.py` already means YAML config-file
preprocessing (`pre_process_yaml` et al.) in this codebase, and a new `pydantic.py` would fork the
project's existing single enums module (`pyobs/utils/enums.py`) for no reason other than
`AccessLevel` being `IntEnum` rather than `StrEnum` like its neighbors — a real distinction (it
needs ordinal comparison; the others are wire-protocol `StrEnum`s) but not one worth a second
module for.
