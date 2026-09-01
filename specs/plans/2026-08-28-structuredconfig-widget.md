# Plan: generic `IStructuredConfig` widget for pyobs-gui

Status: implemented — pyobs-gui#154 closed. `StructuredConfigWidget` landed in pyobs-gui#158
(merged 2026-09-01). A `DummyStructuredConfig` module also landed in pyobs-core#841 (merged
2026-09-01, `pyobs/modules/utils/dummystructuredconfig.py`) purely so the widget has something to
manually verify against — not a change to the frozen interface below. Manually verified end-to-end
via `pyobs-gui/test/structuredconfig.yaml` (`MultiModule` + `LocalComm`, real Qt window).

Repos: pyobs-gui (widget), pyobs-core (`IStructuredConfig` itself — frozen, no changes; a new
`DummyStructuredConfig` dummy module was added as a verification fixture, see above)

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
- **Module not READY:** this plan's original claim that `BaseWidget._update_loop` auto-disables
  the widget was wrong — that loop only runs for widgets passed an `update_func` (today only
  `RoboticWidget`/`ScheduleWidget`). `CoolingWidget`/`FilterWidget`/`ModeWidget` don't get it
  either; they just `setEnabled(True)` on state arrival. PR pyobs-gui#158 matched that existing
  convention instead of inventing new gating logic.
- **Lists:** `ConfigValue` allows `list[...]` on the wire, but `ConfigFieldSchema` has no list
  type today — explicitly out of scope; unsupported fields render disabled with a tooltip.

### 2. Registration & placement (superseded by #150, landed 2026-09-01)

This section originally assumed `DEFAULT_WIDGETS` (`mainwindow.py:54-67`), a first-match-wins
dict. #150 replaced that with a `MAIN_WIDGETS` registry (PR pyobs-gui#157, merged into `develop`;
not yet on `main`) — update accordingly:

- Add `MainWidgetEntry(IStructuredConfig, StructuredConfigWidget, "Config", "fa5s.cog")` to
  `MAIN_WIDGETS`. Leave `sidebar_preferred` at its default `False` — this is a main page in its
  own right, not a sidebar demotion candidate. Registry order no longer matters for visibility
  (unlike the old dict, every matching entry now shows).
- No separate icon dict — `icon` is a field on the entry itself.
- **Behavior change vs. the original "fallback" framing:** because #150 turns *every* matching
  main-role interface into a tab rather than hiding all but the first, the FTS (`ISpectrograph` +
  `IStructuredConfig`) will now show **both** a "Spectrograph" and a "Config" tab automatically —
  not fallback-only. That collides with the FTS's existing hand-rolled config UI living *inside*
  its spectrograph page (`pyobs_iagvt/widgets/ftswidget.py`): once this widget ships, the FTS
  would show its config twice (bespoke block + generic tab). Worth deciding at implementation
  time whether to strip the hand-rolled block from `ftswidget.py` as part of this change, rather
  than leaving it as a someday follow-up.
- `ModuleWindow.open()` (`modulegui.py`) now shares the same assembly path
  (`collect_main_widgets()` / `ModulePage`) as the main window, so no separate registration is
  needed for standalone mode.

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

- No changes to `ConfigSchema`/`ConfigFieldSchema`/`IStructuredConfig` themselves (frozen); no
  list-type rendering; no YAML import/export (possible follow-up).
- #150 has since landed on `develop` (2026-09-01) — this plan no longer merely "slots into it
  later"; §2 now targets the `MAIN_WIDGETS` registry directly, and the FTS tab-duplication
  question above is a direct consequence of that landing, not a hypothetical.

## Known follow-ups (not done here)

- **FTS double-tab**: per §2, the FTS will show both "Spectrograph" and "Config" tabs once a
  siderostat- or FTS-style module widget lands alongside this one — the hand-rolled config block
  in `ftswidget.py` was deliberately left untouched (issue #154's "FTS unchanged" acceptance
  criterion).
- **pyobs-gui `test/*.yaml` fixture bug**: every fixture in `test/` (not just the new
  `structuredconfig.yaml`) has a stale top-level `name: <module>` key that current pyobs-core
  `develop` now rejects (`Object.__init__`'s stricter leftover-kwarg check has no `name`
  parameter anywhere in the `Module`/`Object` chain) — verified against the unmodified
  `roof.yaml`. Unrelated to this plan's scope; tracked as a follow-up fix directly on
  `develop` in pyobs-gui.
