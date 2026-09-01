# Plan: generic `IStructuredConfig` widget for pyobs-gui

Status: proposed (pyobs/pyobs-gui#154)

Repos: pyobs-gui (widget), pyobs-core (`IStructuredConfig` — frozen, no changes)

## Problem

`IStructuredConfig` landed in pyobs-core 2.x (`pyobs/interfaces/IStructuredConfig.py`; design:
`specs/design/istructuredconfig.md`, commits `374fb358`/`a07fb3f0`) but pyobs-gui has no widget for
it. The only consumer anywhere is pyobs-iagvt's FTS, which hand-rolls a file-picker + YAML +
pydantic construction (`pyobs_iagvt/widgets/ftswidget.py`) instead of using the schema. The next
module to adopt `IStructuredConfig` (e.g. the siderostat, with its nested pointing-model config)
would otherwise need another bespoke UI.

Recap of the interface (unchanged, frozen for this plan):

- **`capabilities`** — a `ConfigSchema` (`fields: dict[str, ConfigFieldSchema]`), fetched via the
  existing generic `comm.get_capabilities(module, IStructuredConfig)` path. Shape-only, no values.
- **`state`** — `ConfigAppliedState(config: dict[str, ConfigValue], time)`, published over the
  existing pub-sub mechanism; values only ever come from here.
- **`set_config(config)`** — the single RPC; validates and applies the whole nested dict at once.

`ConfigFieldSchema` (`pyobs/utils/config_schema.py`): `type` ∈
`"str" | "int" | "float" | "bool" | "enum" | "object"`, plus `unit` (`pyobs.utils.enums.Unit`),
`options` (for `enum`), `default`, and `nested` (for `object`). Schemas are auto-derived from
dataclasses (`dataclass_to_schema`) or pydantic models (`pydantic_to_schema`) — module authors
never hand-write them, and unsupported field types raise `TypeError` deliberately.

## Design

### 1. New widget: `pyobs_gui/structuredconfigwidget.py` → `StructuredConfigWidget(BaseWidget)`

Two-phase `_init()` (one-shot, per `BaseWidget` conventions in `base.py`):

1. Fetch `ConfigSchema` once via `comm.get_capabilities(module, IStructuredConfig)` (cached —
   it's static) and build the editor tree.
2. `comm.subscribe_state(module, IStructuredConfig, cb)` — delivers the current
   `ConfigAppliedState` immediately on subscribe, then on every change; populate editors from
   `state.config`.

**Field-type → editor mapping** (recursive; `object` → `QGroupBox` + `QFormLayout`):

| Schema `type` | Editor | Notes |
|---|---|---|
| `str` | `QLineEdit` | |
| `int` | `QSpinBox` | |
| `float` | `QDoubleSpinBox` | `unit` → suffix text (e.g. `arcsec`), decimals tuned to magnitude |
| `bool` | `QCheckBox` | |
| `enum` | `QComboBox` | items from `options`; exact string values used in the payload |
| `object` w/ `nested` | `QGroupBox` + recursion | e.g. `setup` / `main` in the FTS config |
| `object` w/o `nested` (pydantic freeform `dict`) | read-only placeholder | no schema to render; flag rather than guess (mirrors `config_schema.py`'s loud-failure philosophy) |

- **Defaults:** `ConfigFieldSchema.default` pre-fills editors before the first state arrives;
  state always wins afterwards.
- **Dirty tracking:** assemble the nested `dict[str, ConfigValue]` from the editors and compare
  against the last-applied state; "Apply" enabled only when changed. Provide "Reset" to restore
  last-applied values.
- **Apply:** `self.run_background(...)` → `comm.proxy(module, IStructuredConfig).set_config(payload)`;
  errors surface through the existing `show_remote_error` path (`base.py`). Disable Apply when
  `self.permitted("set_config")` is `False` (existing ACL machinery) and while the call is in
  flight (`_enable_buttons`).
- **Module not READY:** `BaseWidget._update_loop` already disables the whole widget — nothing
  extra needed.
- **Lists:** `ConfigValue` allows `list[...]` on the wire, but `ConfigFieldSchema` has no list
  type today — explicitly out of scope; unsupported fields render disabled with a tooltip.

### 2. Registration & placement (see also #150)

`DEFAULT_WIDGETS` (`mainwindow.py:54-67`) is first-match-wins, and so is the standalone
`ModuleWindow.open()` (`modulegui.py:28-32`). Therefore:

- Add `IStructuredConfig: StructuredConfigWidget` to `DEFAULT_WIDGETS` **after** the specialized
  interfaces (`ISpectrograph`, …) so e.g. the FTS keeps its `SpectrographWidget` and the generic
  form acts as a fallback.
- Add a `DEFAULT_ICONS` entry (e.g. `fa5s.cog`).
- The FTS also shows the overlap: it already ships a bespoke config UI *inside* its spectrograph
  page. Long-term the generic form could replace that hand-rolled block, or sit alongside it once
  issue #150 (tab pages for multi-widget modules) lands — the widget should be written as a plain
  `BaseWidget` so it works both as a main page and as a sidebar/tab component.

### 3. Tests (`tests/`, headless offscreen `QApplication` already set up in `conftest.py`)

- Schema → editors: each field type maps to the right editor class, incl. nesting, units as
  suffixes, enum options, defaults.
- Assemble: widget tree → payload dict round-trips against a known schema; `set_config` receives
  the expected payload (fake comm proxy).
- Dirty/Apply/Reset logic; Apply disabled when unchanged or not permitted; remote error path shows
  the messagebox.

## Acceptance criteria

- A module implementing `IStructuredConfig` gets an editable, nested form automatically — no
  widget code per module.
- Current values arrive from `ConfigAppliedState` immediately on open and track updates; defaults
  fill in until then.
- Apply sends the assembled dict via `set_config`, is gated by ACL + module state, and reports
  failures via the standard error path.
- FTS (pyobs-iagvt) unchanged; generic widget appears as fallback page for `IStructuredConfig`
  modules.

## Out of scope

- No changes to pyobs-core (`ConfigSchema`/`ConfigFieldSchema`/`IStructuredConfig` are frozen); no
  list-type rendering; no YAML import/export (possible follow-up).
- Not depending on #150 — but designed to slot into it later.
