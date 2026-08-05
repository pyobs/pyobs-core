# pyobs-gui stays on QtWidgets, not QML

status: accepted
date: 2026-07-06

Repos: pyobs-gui

## Context and Problem Statement

`pyobs-gui` is a PySide6/QtWidgets app. The `TelescopeWidget` width-floor investigation (see
`gui-telescopewidget-layout.md`) kept running into the same wall: QtWidgets has no declarative
equivalent of CSS media queries or flexbox wrapping. Getting responsive reflow requires
hand-written `resizeEvent()` logic and, for flex-wrap-style behavior, a custom `QLayout`
subclass. QML has this built in (`Flow`, `states` with `when:` guards, reactive property
bindings), which raised the question of whether QML would be a better foundation for the app
generally, not just for this one widget. This doc records that evaluation and the decision.

## Decision

**Stick with QWidgets.** QML's declarative/reactive model would genuinely fit this app's
state-driven UI better than QtWidgets' imperative one, but the migration cost is a full rewrite
of the Python-to-UI bridge across all 18 widgets, with no automated test suite to lean on, for a
benefit that's mostly about internal code quality rather than anything operators would notice.
See "Why not now" below.

## What QML would genuinely improve

- **Responsive layout.** `states`/`when:` is a real declarative equivalent
  of a CSS media query — no more manual "did we cross a width threshold"
  bookkeeping, no custom `FlowLayout` needed for wrap-style content.
- **The `update_gui()` relay pattern would mostly disappear.** Every widget
  today follows the same shape: cache state in an `_on_*_state()` callback,
  emit a Qt signal, then manually call `.setText()`/`.setValue()` on a dozen
  widgets in `update_gui()` (seen identically in `telescopewidget.py`,
  `focuswidget.py`, `filterwidget.py`, `temperatureswidget.py`). With a
  `QObject` backend exposing `Property`s, QML bindings update themselves —
  this whole manual relay collapses into declarative bindings.
- **Dynamic composition fits more naturally.** `add_to_sidebar()`
  (`base.py:187-204`) manually tracks a widget list and calls
  `insertWidget()` at a specific index to stay above a spacer. A `Repeater`
  bound to a capability model is closer to what that code is trying to do.
- **`TemperaturesWidget`'s per-sensor dynamic rows**
  (`layout.addRow(key + ":", widget)` per sensor, guarded by a `_widgets`
  dict to avoid duplicates, `temperatureswidget.py:44-52`) becomes a
  one-line `Repeater` bound to a model.
- **`VideoWidget`'s manual rescaling** — `ScaledLabel` overrides
  `resizeEvent()` to re-scale a cached `QPixmap` (`videowidget.py:29-37`) —
  is exactly what `Image { fillMode: Image.PreserveAspectFit }` gives for
  free.
- **Duplicated widget idioms could collapse into one reusable component.**
  `FilterWidget`, `FocusWidget`, and the offsets rows in `TelescopeWidget`
  all hand-implement the same "labeled value + optional set/reset" pattern
  in separate `.ui` files. One `PropertyRow.qml` reused via `Repeater` would
  replace all of them.

## What would stop working / need real re-engineering

All of the following are mechanisms baked into `BaseWidget`
(`pyobs_gui/base.py`) and used identically across all 18 widget types
(`telescopewidget.ui`, `camerawidget.ui`, `roofwidget.ui`, `weatherwidget.ui`,
etc.) — this is why the migration isn't "port 18 `.ui` files," it's "rewrite
how every widget talks to Qt":

- **The `Ui_*` mixin pattern is gone entirely.** Every widget is
  `class X(BaseWidget, Ui_X)`, calling `self.setupUi(self)` and then
  directly touching generated attributes (`self.textMoveRA.setText(...)`).
  QML has no equivalent — each widget needs a hand-written `QObject`
  backend exposing `Property`/`Signal`s instead.
- **Async lifecycle is a `QWidget` virtual-method pattern.**
  `showEvent`/`hideEvent` overrides drive `asyncio.create_task(self._init())`
  and the `_update_loop()` polling task (`base.py:206-233`). Quick `Item`s
  don't override show/hide the same way; the nearest equivalents
  (`Component.onCompleted`, bindings on `visible`) need deliberate
  remapping, and this pattern underlies every widget in the app.
- **`run_background()`'s disable/run/re-enable pattern** flips
  `.setEnabled()` directly on a list of Python `QWidget` references
  (`base.py:257-279`). Under QML this becomes another indirection layer
  through backend-exposed `enabled` properties — every call site needs
  rewriting.
- **`colorize_button()` manipulates a raw `QPalette`**
  (`base.py:305-321`, used ~10× in `telescopewidget.py` alone). Quick
  Controls buttons are styled via delegates or a style like
  Material/Universal, not `QPalette` — same visual result achievable,
  different API, another per-call-site rewrite.
- **`show_extract_button()`'s "pop this widget into its own window"**
  (`base.py:157-185`) reparents a live `QWidget` into a new `QDialog`.
  Reparenting a `QQuickItem` between two different `QQuickWindow`s isn't
  the same clean operation — each window has its own scene-graph root.
  This specific feature needs actual redesign, not a port.
- **`QAsyncMessageBox`** (the qasync-aware modal dialog used in
  `show_error()`) would need reimplementing against
  `QtQuick.Controls.Dialog`, with different modal/async semantics.
- **No automated GUI test suite exists.** `test/` has only YAML
  module-config fixtures (`telescope.yaml`, `camera.yaml`, etc.) for manual
  runs — no `pytest-qt`/`qtbot` tests found. A migration this size would be
  verified entirely by hand, against an app that controls real telescope
  hardware.
- **Rendering backend requirement.** Qt Quick needs a working
  GPU-composited context (OpenGL/Vulkan/Metal/D3D via RHI); the software
  fallback has real limitations. Worth checking against actual deployment
  (remote X11/VNC into control-room machines is a plausible scenario here)
  before committing further, if this is ever revisited.

## Comparison point: pyobs-web-client (Vue)

Investigated as a reference for "what would a reactive/declarative
telescope UI look like in practice." Two separate repos, worth not
confusing:

- `pyobs-web-admin` — Django + Bootstrap, no database, YAML-based module
  discovery. Not the relevant comparison.
- `pyobs-web-client` — Vue 3 + TypeScript, talks to modules over XMPP
  (`useXmpp.ts`, `pyobs-codec.ts`). This is the relevant one — almost
  certainly the reference client for the pyobs 2.0 state/capabilities
  pub-sub work.

Findings:

- **Generic capability/state rendering already exists there.**
  `KeyValueCard.vue` renders an arbitrary object as rows, recursing into
  nested values, with no knowledge of which module/interface it came from
  — a working example of the "generic capability-driven form" pattern
  discussed for `TelescopeWidget`.
- **Subscribe-on-mount / unsubscribe-on-unmount lifecycle.**
  `ModuleStateCard.vue` (19 lines) calls `subscribeState(jid, interfaceName,
  version)`, gets a reactive value back, and wires `onUnmounted(unsubscribe)`
  — component lifetime is subscription lifetime, no manual bookkeeping. A
  clean template for how a QML backend `QObject` should manage its own
  `subscribe_state` subscription, if a QML rewrite is ever revisited.
- **Schema-driven command execution.** `RoofView.vue` doesn't hardcode a
  proxy call per button — it looks up `mod.interfaces['IRoof'].commands[action]`
  and calls a generic `executeMethod(jid, action, params, schema)`. This is
  a materially better architecture than `TelescopeWidget`'s per-action
  hardcoded proxy calls (`_init_telescope()`, `_park_telescope()`,
  `_stop_telescope()` each independently doing
  `async with self.comm.proxy(...) as p: await p.init()`), and is worth
  adopting in `pyobs-gui` **independent of any UI framework decision**.
- **But `pyobs-web-client`'s views are deliberately generic**, not
  specialized. `RoofView` is its most specialized view, and even that is
  just schema lookup + three plain buttons + a `KeyValueCard` fallback.
  There's nothing resembling `pageMoveOrbitElements`'s field grid, the
  Simbad/JPL-Horizons lookup rows, or `CompassMoveWidget`'s coordinate-frame
  offset math. That's intentional — it's built to show *any* module
  generically, not to be a hand-crafted telescope operator console.

## Why pyobs-gui keeps a structural advantage regardless of framework

This isn't a QtWidgets-vs-QML point — it's Python-vs-browser, and it holds
regardless of what `pyobs-gui`'s UI layer is built with:

- **`GUI` is a real pyobs `Module`, not a client of one.**
  `class GUI(Module, IFitsHeaderBefore)` (`gui.py`) implements
  `get_fits_header_before()`, aggregating live FITS header contributions
  from every open widget (`gui.py:78-89` → `base.py:290-303`). Whatever's
  showing in the GUI can flow directly into an exposure's FITS header. A
  browser tab cannot be a module in that graph.
- **`TelescopeWidget` runs real astronomy computation in-process.** Direct
  imports of `astropy.coordinates`, `astropy.units`, `astroquery` (Simbad
  and JPL Horizons lookups happen directly from the GUI process, not
  through any pyobs module), and `sunpy.coordinates.frames` for
  Heliographic/Helioprojective transforms (`telescopewidget.py:8-13`).
  There's no mature JS equivalent of `sunpy`'s solar coordinate frames, and
  `astropy`'s coordinate-transform correctness isn't something to casually
  reimplement.
- **Could run without a network layer at all**, via the `LocalComm` backend
  from the pyobs 2.0 migration — a `GUI` module wired directly to in-process
  modules with zero serialization. A browser client is always, structurally,
  talking over some IPC/network channel to something else that holds the
  real `Comm` object.

## Alternative considered: drop pyobs-gui, wrap pyobs-web-client in Electron

Would solve the real duplication cost of maintaining two hand-built UIs
(one Vue, one QtWidgets/QML) for the same specialized widgets — one
codebase, two shells (browser + Electron window).

Would **not** provide any of the three advantages above, since Electron's
renderer is still JavaScript:

- Simbad/Horizons lookups and solar-frame transforms would need either a
  new server-side pyobs module/endpoint (new backend work, turns a local
  synchronous call into a network round-trip), or a bundled local Python
  process talked to over localhost IPC — which is, functionally, rebuilding
  a slimmed-down `pyobs-gui` backend anyway, just fronted differently.
- Electron can't make the app a `Module` with `LocalComm` or an
  `IFitsHeaderBefore` contributor — that requires being an actual Python
  process inside pyobs's module system.

## Consequences (decided: coexistence, not replacement)

- `pyobs-gui` stays the tool for anything that benefits from being *in* the
  Python/pyobs-core world: precise coordinate work (Simbad/Horizons lookups,
  orbit elements, solar-frame math), FITS header contribution, `LocalComm`
  for zero-network operation. This is also the hardest stuff to replicate
  in the web client, so it's the natural place to concentrate design effort
  if a UI rewrite (QML or otherwise) ever happens.
- `pyobs-web-client` stays the tool for remote/lightweight access:
  monitoring, common actions, emergency stop, generic `KeyValueCard`
  fallback for anything without a dedicated page. Not expected to reach
  Simbad/Horizons/solar-frame parity with `pyobs-gui` — that's an accepted
  scope boundary, not a gap to close.
- The Electron-wrapping idea is shelved unless the actual pain point turns
  out to be "we don't want to maintain a PySide6 build/packaging pipeline,"
  rather than a UI-parity concern.
- Worth doing regardless of this decision: adopt schema-driven command
  execution in `pyobs-gui` (`executeMethod`-style, looked up from interface
  command schemas) instead of per-action hardcoded proxy calls — this is a
  `pyobs-web-client`-derived improvement that has nothing to do with QML
  and is worth doing on its own merits.
- The near-term `TelescopeWidget` width-floor fixes from
  `gui-telescopewidget-layout.md` (the `QStackedWidget` `sizeHint()`
  override, `QFormLayout::setRowWrapPolicy()`, resize-driven reparenting)
  remain valid and unaffected by this decision — those are QtWidgets fixes
  for a QtWidgets app we're staying on.
