# Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`

Status: draft

Repos: pyobs-gui (all implementation here)

See `specs/design/gui-standalone-binary.md` for how this fits into the bigger "ship one
compiled binary" goal.

## Problem

`pyobs-gui` supports per-deployment custom widgets via YAML:

```yaml
widgets:
  - module: guiding
    widget:
      class: mypackage.GuidingWidget
```

Resolved through `pyobs_gui/mainwindow.py:601-606` (and `:613-615` for sidebar widgets) →
`BaseWindow.create_widget()` (`pyobs_gui/base.py:75-92`) → pyobs-core's `create_object()`
(`pyobs/object.py:164-187`) → `get_class_from_string()` (`pyobs/object.py:146-161`), which does a
plain `parts = class_name.split("."); cls = __import__(".".join(parts[:-1]))` — a genuine runtime
import of whatever dotted path the YAML names, no allowlist, nothing static about it.

The **built-in** widgets (`DEFAULT_WIDGETS`, `mainwindow.py:51-64` — `ICamera` → `CameraWidget`,
`ITelescope` → `TelescopeWidget`, etc.) are a different, fully static mechanism: real Python
classes imported normally at the top of `mainwindow.py`, matched via `isinstance(proxy,
interface)`. `pyside6-deploy`/Nuitka can see and bundle these fine — static analysis of the app's
own import graph is exactly what they're good at.

Custom widgets are the opposite: **completely invisible to static analysis**, since the module name
only exists as a string inside a YAML file the compiler never sees. A naively compiled binary would
only ever support the built-in widget set. **Rejected as a fix:** recompiling a separate binary per
deployment — that defeats the entire point of shipping one binary that works everywhere.

This is actually two separate problems, not one. Checking a real deployment
(`pytel-dev/configs/gui-iagvt.yaml`) against the goal in `specs/design/gui-standalone-binary.md`
("no hand-edited YAML config") surfaced the second one: that file conflates connection credentials
(`comm:` — solved by `gui-login-window.md`) with the `widgets:` list deciding which widget class to
use for which module — and *that* is exactly the kind of local, user-side config the whole point of
this plan is to eliminate. So there are two questions, addressed separately below:

1. **How does a compiled binary load widget code it can't see at compile time?** (`## Decision`,
   right below.)
2. **How does the GUI decide *which* widget to load for a given module, if there's no local config
   file to say so?** (`## Deciding which widget to use, without user-side config`, further down —
   genuinely still open, decision postponed.)

## Decision

### Considered options

1. **Restrict compiled builds to `DEFAULT_WIDGETS` only; require a normal `pip install` (unfrozen
   interpreter) for any deployment needing custom widgets.** Rejected — this is just "don't ship a
   binary for that site," which fails the actual goal.
2. **External plugin directory on `sys.path`, resolved at startup, requiring no changes to
   `create_object`/`get_class_from_string` at all.** A configurable list of directories gets
   prepended to `sys.path` before any widget gets resolved. Whatever ends up deciding *which* widget
   class to use (see the still-open question below) can keep referring to it as
   `mypackage.GuidingWidget` — `mypackage` just needs to be an importable package/module sitting in
   one of those directories as plain, uncompiled `.py` files, not bundled into the binary. This part
   of the mechanism is settled regardless of how the selection question below resolves. This is the
   standard, Nuitka-endorsed
   way to make a compiled/frozen app extensible: `--standalone`/`--onefile` builds retain the full
   CPython import machinery, so `sys.path`-based imports of external files at runtime work exactly
   like an unfrozen interpreter — confirmed against the actual `pyside6-deploy` install in this repo
   (`.venv/lib/python3.13/site-packages/PySide6/scripts/deploy_lib/nuitka_helper.py`; Nuitka is the
   thing `pyside6-deploy` drives, and this is documented Nuitka behavior, not a guess).
3. **Single-file loading via `importlib.util.spec_from_file_location`** (load one `.py` file
   directly, no package or `sys.path` entry needed) — a possible convenience layered on top of
   option 2 later (e.g. `widget: {file: /path/to/widget.py, class: GuidingWidget}` for a single
   dropped-in file rather than a whole installable package). Not required for v1.

### Decision outcome

**Option 2.** Zero changes to the existing widget config format or to pyobs-core's `create_object`/
`get_class_from_string` — the entire fix is "where `sys.path` points before widget resolution
happens," which is additive and orthogonal to everything else.

### Consequences

- A plugin's own imports must resolve to something already present in the compiled binary: stdlib,
  PySide6, `pyobs`/`pyobs_gui` (all bundled anyway, since the base app needs them). A plugin that
  needs a brand-new third-party dependency has to bundle that dependency itself (e.g. vendor it
  alongside the plugin file, or the site adds it to the plugin directory too) — a real, statable
  limitation for plugin authors, not a blocker for the mechanism itself.
- **Open question, not yet decided:** where does the `sys.path` manipulation itself live?
  - *pyobs-gui-only* (leaning this way for v1): a `plugin_paths: list[str] | None = None` param on
    `pyobs_gui.GUI`/`MainWindow`, since `pyobs-gui` is the only consumer asking for this today —
    don't build a generic pyobs-core mechanism for a hypothetical second compiled consumer that
    doesn't exist yet.
  - *pyobs-core-generic*: any future compiled pyobs consumer with config-driven dynamic class
    loading has the identical tension, so a shared mechanism (e.g. in `Application` or
    `pyobs/object.py`) would generalize better. Revisit if/when a second consumer actually shows up.

## Deciding which widget to use, without user-side config

**Status: genuinely undecided, postponed until the loading mechanism above is built and there's a
real plugin package to test selection against.** Recorded here so the options and the reasoning
against two of them aren't lost, not as a settled design.

### The actual real-world case that grounds this

`pyobs-iagvt/pyobs_iagvt/widgets/*.py` (an existing, real custom-widget package, currently wired up
via `pytel-dev/configs/gui-iagvt.yaml`'s commented-out `widgets:` block) is more than "one file per
widget": `guidingwidget.py` imports `pyobs_iagvt.widgets.qt.widgetguiding` (a compiled Qt Designer
form) and `pyobs_iagvt.utils.wcstools`; `solartelescopewidget.py` and `diskdetectionwidget.py`
import `pyobs_iagvt.modules.fibercamera` — a different top-level subpackage entirely. The real unit
here is the whole `pyobs_iagvt` distribution (it already has its own `pyproject.toml`, hatch build
backend, real dependencies including a private git-sourced one, `pyftscontrol`), not a lone script —
which is good news for the loading mechanism above (`pip install --target=<dir> pyobs-iagvt` pulls
in the whole tree, internal structure intact, in one shot) but doesn't by itself answer "which
widget for which module."

That config also shows `GuidingWidget` is a **deliberate override**, not a gap-filler: the `guiding`
module is plain `pyobs.modules.pointing.AutoGuiding` (a stock `pyobs-core` class implementing
`IAutoGuiding`), and `DEFAULT_WIDGETS` already maps `IAutoGuiding → AutoGuidingWidget`. IAGVT wants
its own sun-grid-plotting widget instead, for this specific site's hardware. That's only safe to
resolve automatically *because* a plugin package is inherently site-scoped — nobody else's compiled
binary loads IAGVT's plugin, so "this interface always gets my custom widget" can't collide across
sites the way it would if `pyobs-gui` itself shipped that assumption.

### Considered options

1. **Server-side capability publishing.** Extend `IModule`'s `ModuleCapabilities`
   (`pyobs/interfaces/IModule.py`) with optional `gui_widget: str | None` / `gui_widget_kwargs: dict
   | None` fields, published by each module the same way `label`/`version`/`location` already are
   (`Module.open()`), read by the GUI the moment it creates a proxy (capabilities are already
   fetched automatically on connect). **Rejected.** Requires a real `pyobs-core` change, requires
   touching every module's own server-side config just to tell a GUI which widget to use, and
   couples a headless server module to a GUI-specific concern it has no other reason to know about.
2. **Self-declared metadata via a class attribute on each widget file**, e.g. `class
   GuidingWidget(BaseWidget): pyobs_interface = IAutoGuiding` — mirrors how `pyobs-core`'s own
   interfaces already do exactly this kind of declarative self-description (`IRunning.state =
   RunningState`, `IModule.capabilities = ModuleCapabilities`). `pyobs-gui` would walk the plugin
   package's submodules once at startup (`pkgutil.walk_packages`, importing each — the same
   technique used for the state-publishing discovery test in `pyobs-core`), collect every
   `BaseWidget` subclass declaring the attribute, and layer those into `DEFAULT_WIDGETS`. No
   `pyobs-core` changes, everything stays in the plugin package. Drawback: requires importing every
   file in the plugin package just to probe for the attribute, and a typo'd interface reference only
   fails wherever/whenever that widget is actually resolved, not at startup.
3. **A pre-defined manifest module inside the plugin package** — e.g. `pyobs_iagvt.gui_widgets`
   exporting a `WIDGETS: list[WidgetEntry]` that references widget classes and interfaces directly
   (real imports, not dotted-string class paths, since the plugin package can just reference its own
   classes):
   ```python
   # pyobs_iagvt/gui_widgets.py
   @dataclass
   class WidgetEntry:
       interface: type[Interface]
       widget: type[BaseWidget]

   WIDGETS = [WidgetEntry(interface=IAutoGuiding, widget=GuidingWidget), ...]
   ```
   `pyobs-gui` needs one new fixed convention: given a plugin package name (still the one thing
   that'd need naming somewhere — alongside the plugin-directory setting), `import
   <package>.gui_widgets` and read `WIDGETS`. One well-known file per plugin, real class references
   (a typo is an `ImportError` at startup, not a silent miss), only imports what's actually
   referenced — unlike option 2, doesn't need to import every file in the package speculatively.
   Currently the leaning recommendation, **not decided**.

None of these are needed to also solve the extra-kwargs case (today's config passes
`GuidingWidget(acquisition="acquisition", suncamera="suncamera")` — sibling module names to
cross-reference): a widget can discover those itself via `self.comm.clients_with_interface
(IAcquisition)`, the exact pattern `mainwindow.py`'s `_check_warnings()` already uses
(`clients_with_interface(IAutonomous)`) — unambiguous in practice since a plugin package is only
ever loaded by the one site that chose to include it.

## Packaging pipeline

`pyside6-deploy` (confirmed installed and runnable in this repo's venv) wraps Nuitka. Relevant,
verified-against-the-actual-tool details:

- `pyside6-deploy --init` generates a `pysidedeploy.spec` config file — should be generated once,
  committed to the repo, and treated as the reproducible build recipe rather than something
  regenerated ad hoc per release.
- The spec's `[nuitka] extra_args` field passes straight through to the underlying Nuitka
  invocation (`deploy_lib/config.py:279-284`, `deploy_lib/nuitka_helper.py:80-153`) — this is where
  any extra `--include-data-dir=SRC=DEST`/`--include-data-files=...` would go if static analysis
  misses a resource (see the `qtawesome` spike below).
- `--mode` is either `onefile` or `standalone` (confirmed via `pyside6-deploy --help`). Leaning
  **`standalone`** for v1: `onefile` self-extracts to a temp directory on every launch (slower cold
  start) and gives less of a stable, browsable directory layout to put a plugin directory next to;
  `standalone` produces a real directory. Flagged as a recommendation to revisit once an actual
  binary has been built and measured, not a settled decision.

### Spikes — done (2026-07-27), on `feature/standalone-binary`

Built a minimal, isolated PySide6 + `qasync`-shaped app (`spike_standalone/main.py`, `pysidedeploy.spec`
in that branch) through the real `pyside6-deploy` install in this repo's venv, in `--mode=standalone`,
and ran the resulting frozen binary directly (not via any Python from the venv). All four questions
this was meant to answer came back clean:

- **`qtawesome` icon fonts: OK, no changes needed.** `qta.icon("fa5s.camera")` returns a real
  (non-null) icon from inside the frozen binary. (First attempt reported a false `FAIL` — a bug in
  the spike script itself, which checked `qtawesome` before constructing the `QApplication`;
  qtawesome needs a live one. Not a Nuitka/freezing issue.)
- **`keyring` backend auto-discovery: OK, no changes needed.** Frozen binary discovers the exact
  same three backends as an unfrozen run (`keyring.backends.fail.Keyring` prio 0,
  `keyring.backends.SecretService.Keyring` prio 5, `keyring.backends.chainer.ChainerBackend` prio
  -1) and picks the same one (`SecretService`), with a working store/retrieve/delete roundtrip.
  `importlib.metadata` entry-point discovery survives freezing unmodified in this configuration.
- **The plugin mechanism itself: confirmed working, both directions.** A trivial widget module
  living *only* in an unrelated scratch directory (never copied near the build, never referenced by
  `main.py`'s own imports) loads correctly when its directory is prepended to `sys.path` at runtime
  from an environment variable read inside the frozen binary — proving Nuitka's static analysis
  never needed to see it. Confirmed both ways: `find` over the `.dist` output for the plugin
  module's filename returns nothing (never bundled), and running the exact same binary with that
  env var unset fails with a plain `ModuleNotFoundError` (proving the success case was real, not a
  stale cached import).
- **PySide6 itself survives freezing:** also confirmed as a baseline sanity check (`QApplication`
  constructs fine from inside the frozen binary).

**One real, unplanned finding: the default C compiler in this environment can't build this app.**
The very first standalone build attempt got most of the way through Nuitka's C compilation and then
hit `internal compiler error: Segmentation fault` in GCC 15.2.0, specifically while compiling
`cryptography.hazmat.primitives.asymmetric.ec` (a transitive dependency, reached via `keyring`'s
`SecretService`/`jeepney`/`cryptography` chain) — a GCC bug, not an app or Nuitka bug, most likely
GCC 15 being too new to have been widely exercised against Nuitka's generated code yet. Fixed by
adding `--clang` to the spec's `[nuitka] extra_args` and setting `CC=clang-21`/`CXX=clang++-21`
before invoking `pyside6-deploy` — clang-21 was already installed and compiled the exact same app
cleanly. **Action item, not yet done:** pin the compiler choice (`--clang` in `extra_args`, and
document the `CC`/`CXX` env vars) in whatever CI/build environment actually produces release
binaries, rather than relying on whatever the default system compiler happens to be — this failure
mode is compiler-version-specific and could reappear or disappear on a different machine/GCC version
without warning.

**Also found, unrelated to the four questions above but blocking any build at all in a fresh `uv`
venv:** `pyside6-deploy` shells out to `<venv>/python -m pip install Nuitka`/`patchelf` internally,
but a `uv`-created venv has no `pip` bootstrapped into it by default (`uv` normally manages packages
itself, without needing `pip` inside the venv). Fixed for this spike with `python -m ensurepip`
first. Also needed the venv's `bin/` directory on `PATH` (not just invoking tools by full path) —
`patchelf` gets `pip`-installed into `<venv>/bin/patchelf`, but Nuitka's own standalone-mode check
looks it up via `PATH`, not the venv it's running under, so it doesn't find a `PATH`-invisible venv
install. Both are one-time environment setup steps for whoever runs this build, not app changes.

### Real app build — done (2026-07-29), on `develop`

Built and ran the actual `pyobs_gui` app (not the isolated spike) through `pyside6-deploy`,
`--mode=standalone`, targeting `pyobs_gui/__main__.py`. Committed spec:
`pyobs-gui/pysidedeploy.spec`. The binary now launches, shows the login window, and shuts down
cleanly on signal — confirmed by running the frozen `.bin` directly, not via any venv Python. This
is a plain-generic-widgets run only; the plugin mechanism itself (`plugin_paths`, widget selection)
is still unimplemented, see checklist.

Three real problems surfaced that the isolated spike didn't hit, in order:

1. **`astropy.units` doesn't survive freezing at all** — a genuine, unresolved upstream Nuitka/PLY
   incompatibility ([astropy#15069](https://github.com/astropy/astropy/issues/15069),
   [Nuitka#2313](https://github.com/Nuitka/Nuitka/issues/2313), both open as of 2026-07), not
   something specific to this app. `astropy.units.format.generic` builds its grammar via
   `sys._getframe()` stack-walking to discover its own `tokens`/`p_*` locals; Nuitka-compiled
   frames don't populate `f_locals` the way CPython's do, so the walk finds nothing and the very
   first `import astropy.units` (unconditional, via pyobs-core's `pyobs.utils.enums`) crashes with
   `YaccError: Unable to build parser`. Two dead ends before landing the fix:
   - `--include-package=astropy.units.format(...)` (a workaround reported to work for a different,
     shallower app in the Nuitka issue thread) does not help here — `generic.py` is statically
     reachable through `astropy.units`'s own import graph regardless of the flag, so Nuitka compiles
     it either way; the flag only affects modules that were otherwise invisible to static analysis.
   - Monkeypatching `Generic._parser`/`_lexer` after a normal `import astropy.units.format.generic`
     deadlocks: that import is what triggers the crash in the first place (via
     `astropy.units.astrophys`'s eager unit-string parsing at import time), before a class-level
     patch could ever be installed.
   - **Working fix:** `pyobs-gui/pyobs_gui/_nuitka_astropy_patch.py` patches
     `astropy.extern.ply.yacc.get_caller_module_dict`/`...lex.get_caller_module_dict` (zero
     dependency on `astropy.units`, safe to patch before anything touches it) to fall back to a
     namespace rebuilt from the same grammar, copied verbatim from astropy's source, whenever the
     real frame walk comes back missing `tokens`. Installed at the very top of
     `pyobs_gui/__init__.py` (which Python always runs before `__main__.py`, even under
     `python -m pyobs_gui`). Scoped to the generic unit format only — the one format hit
     unconditionally at startup; cds/ogip/vounit and `astropy.coordinates.angles` use the same PLY
     pattern and aren't yet covered.
2. **Several packages need explicit `--include-package`/`--include-package-data`** because Nuitka's
   static analysis can't see dynamic string-based imports or `open()`-style data-file loads:
   `pyobs.vfs` (lazy backend loading via `__getattr__`, the same pattern as this doc's own
   widget-plugin problem), and package data for `asdf` (JSON schema files, needed transitively via
   `astropy.table`), `astropy`, `sunpy`, `matplotlib`, `qfitswidget`, `astropy_iers_data`, and
   `astroquery` (reads a `CITATION` file at import time). All added to the committed spec's
   `extra_args`.
3. The `--include-package=astropy.units.format.generic_parsetab`/`.generic_lextab`-style flags from
   the first dead end above turned out unnecessary once the `get_caller_module_dict` fix landed,
   but were left in the committed spec since they're harmless and already verified not to break
   anything.

**ccache location:** Nuitka's C-compile caching goes through `~/.cache/Nuitka/ccache` — a
*different* directory from the system default `~/.cache/ccache`, so plain `ccache -s` under-reports;
check with `CCACHE_DIR=~/.cache/Nuitka/ccache ccache -s`. Once `ccache` is installed and on `PATH`,
Nuitka picks it up automatically (no extra flag needed), and hit rates are high (~65%+ observed)
across rebuilds that only touch a couple of app-level files, since ccache keys on the generated C
content per translation unit, not "did anything anywhere change." Nuitka's separate Python→C
translation cache (`~/.cache/Nuitka/module-cache`) is far less effective for this app specifically,
since Nuitka does whole-program analysis and a change to a widely-imported file (e.g.
`pyobs_gui/__init__.py`) can invalidate more cached translation than a naive per-file cache would.

**venv gotcha, additional to the `ensurepip`/`PATH` ones found in the spike:** `uv sync` prunes
anything installed via `pip` that isn't a declared dependency — including `Nuitka`/`patchelf`/`pip`
itself. Running `uv sync` for an unrelated reason (e.g. picking up a new `[project.scripts]` entry)
mid-build silently corrupted an in-flight Nuitka compile the first time this was hit. Re-run
`python -m ensurepip` after any `uv sync` if a `pyside6-deploy` build is expected to work again.

## Non-goals

- Hot-reloading plugins while the GUI is running — load-once-at-startup is enough.
- A plugin marketplace/discovery UI.
- Solving this for other, non-GUI `pyobs` CLI consumers — scoped to `pyobs-gui`'s widget-loading
  path. A future compiled non-GUI consumer would need its own equivalent, informed by whatever's
  learned here (see the pyobs-core-generic open question above).
- Code signing, auto-update, or any distribution mechanism beyond producing the binary itself.

## Implementation checklist

- [ ] Decide `plugin_paths` location: `pyobs-gui`-only (leaning this way) vs. pyobs-core-generic
- [ ] Add `plugin_paths: list[str] | None = None` to `pyobs_gui.GUI`, prepending each to `sys.path`
      before `MainWindow` resolves any widget config
- [ ] **Decide the widget-selection mechanism** (see "Deciding which widget to use" above) — blocks
      the two items below being more than a proof of concept
- [ ] Document the plugin-author contract (what's guaranteed importable, what isn't; how selection
      works once decided) alongside the existing custom-widget example in
      `pyobs_gui/docs/source/index.rst`
- [x] Spike: `qtawesome` under a standalone Nuitka build — OK, no changes needed (2026-07-27,
      `feature/standalone-binary`, `spike_standalone/`)
- [x] Spike: `keyring` backend discovery under a standalone Nuitka build — OK, no changes needed,
      same result as unfrozen (2026-07-27, `feature/standalone-binary`, `spike_standalone/`)
- [x] Spike: plugin mechanism itself, end to end — confirmed working both directions (loads with
      the env var set, `ModuleNotFoundError`s without it) (2026-07-27, `feature/standalone-binary`)
- [x] Pin the compiler for real builds: add `--clang` to `[nuitka] extra_args` and document
      `CC=clang-<N>`/`CXX=clang++-<N>` — the spike's default-GCC build hit a GCC 15 internal
      compiler error partway through (compiler bug, not an app/Nuitka bug), clang built the same
      app cleanly (2026-07-29, committed in `pyobs-gui/pysidedeploy.spec`)
- [x] Produce and commit a real `pysidedeploy.spec` for `pyobs-gui` itself (2026-07-29,
      `pyobs-gui/pysidedeploy.spec`, targets `pyobs_gui/__main__.py`)
- [x] Document the environment prerequisites found during the spike: `python -m ensurepip` if the
      venv has no `pip` (as with a plain `uv venv`), and the venv's `bin/` on `PATH` (not just
      invoking tools by full path) so Nuitka's own `patchelf` lookup succeeds — see "Real app
      build" below for an additional `uv sync` gotcha found while building the real app
- [x] End-to-end smoke test: the real, compiled `pyobs-gui` binary boots and shows the login
      window, confirmed by running the frozen `.bin` directly (2026-07-29) — see "Real app build"
      below for the three real (non-plugin-related) problems this surfaced and how they were fixed
- [ ] End-to-end smoke test: real app + external plugin directory + chosen selection mechanism —
      blocked on the `plugin_paths`/selection items above, not yet attempted
- [ ] Update this doc's `Status:` to `implemented` once landed — not yet; the widget
      loading/selection mechanism (this doc's actual subject) is still unimplemented, only the
      packaging pipeline itself has been proven against the real app
