# Module-specific `PyobsError` types arrive as `UnclassifiedError` on callers that never imported them

Status: implemented (step 1 PR #958, step 2 PR #960, step 3 as 3B in PR 3).

Repos: pyobs-core

## Context

#952 item 8. Checked against `develop` (`c6a20b0b`); line numbers below are for that commit, not
v2.14.2.

How a domain exception crosses the XMPP RPC boundary today:

- Callee: `fault_to_xml` (`pyobs/comm/xmpp/rpc.py:93-119`) writes exactly two things,
  `<exception>module.QualName</exception>` (or `original_type` if the exception carries one) and
  `<message>`. No base classes, no category.
- Caller: `xml_to_fault` (`rpc.py:122-139`) returns `(name, message)`;
  `_on_jabber_rpc_method_fault` (`rpc.py:280-307`) calls `exc.PyobsError.resolve(name)` and, if
  that returns `None`, raises `UnclassifiedError(msg, original_type=name, remote_module=sender)`
  (`rpc.py:301`).
- Registry: `PyobsError.__init_subclass__` (`utils/exceptions.py`) writes
  `_registry[f"{__module__}.{__qualname__}"] = cls`. A class is only registered once its defining
  module is imported. A clash silently overwrites (last definition wins); with fully-qualified keys
  that only happens on reload or redefinition.
- `LocalComm`/`DummyComm` pass exception objects directly and are not affected.

Reproduced on develop (`.venv/bin/python -I`, two processes): a plugin `class
AltLimit(exc.MotionError)` serialized in one process and resolved in another that never imported
the plugin arrives as `UnclassifiedError`, `isinstance(e, exc.MotionError)` is `False`. After
importing the plugin it resolves. A bare `import pyobs.interfaces, pyobs.comm.xmpp` registers 20
classes, none of the module-specific ones.

Module-specific `PyobsError` subclasses in core:

| Class | Defined in | Base | Resolves after (b)? |
|---|---|---|---|
| `MissingObserverError` | `modules/telescope/basetelescope.py:76` | `MotionError` | as `MotionError` |
| `AltitudeLimitError` | `basetelescope.py:82` | `PyobsError` | no |
| `BodyResolutionError` | `basetelescope.py:92` | `MotionError` | as `MotionError` |
| `InvalidOrbitalElementsError` | `basetelescope.py:99` | `MotionError` | as `MotionError` |
| `WeatherDataError` | `modules/focus/focusmodel.py:26` | `FocusError` | as `FocusError` |
| `FocusTimeoutError` | `focusmodel.py:32` | `FocusError` | as `FocusError` |
| `MissingSensorError` | `focusmodel.py:38` | `FocusError` | as `FocusError` |
| `WeatherResponseError` | `modules/weather/weather.py:23` | `PyobsError` | no |
| `ScriptError` | `robotic/scripts/exceptions.py:4` | `PyobsError` | no |

The interface docstrings name most of them as part of the contract (`IPointingRaDec`,
`IPointingAltAz`, `IPointingBody`, `IPointingOrbitalElements`, `IFocusModel`, `IWeather`,
`IRunnable`, `IScriptRunner`). No `except` clause and no `_register_exception` call for any of the
nine exists in pyobs-core, pyobs-gui or any other checkout under `~/code/pyobs`. No caller imports
`basetelescope` or `focusmodel` to get them.

This behaviour is deliberate: `specs/design/exception_handling.md` Assessment §D (about lines
634-703) and proposal §5 (lines 1043-1072) argue that "whoever needs the precise type already
imports it" and move these classes out of `exceptions.py` on purpose. §D rejects importing a module
named in a fault. What §D misses: a caller that writes `except exc.MotionError:` or
`except exc.FocusError:` never imports the leaf, so it loses the base-class catch too. No ADR
covers this.

## Decision table

| Option | What | Verdict |
|---|---|---|
| (a) Document better | Guide page, API reference, docstrings | Do, step 2 |
| (b) Ancestor fallback | Optional `<bases>` in the fault, caller resolves the first registered ancestor | Do first, step 1. Fixes 6 of 9 core errors and every driver error with a core ancestor |
| (c) Import on demand | Carry the module path, `importlib.import_module` on the caller | Reject. Import runs module top-level code, driver modules load vendor SDKs, so a GUI would get hardware side effects, and a forged or buggy fault becomes code execution. An allow-list (`pyobs.*`, entry points) still runs import-time code |
| (d) Move into core | Move the errors into `utils/exceptions.py` | Conditional, step 3, only the 3 that (b) leaves as `UnclassifiedError`. Alternative: small core base class (see step 3) |

## Step 1 (PR 1): `<bases>` ancestor fallback

### Proposed changes

- [ ] **`fault_to_xml`** (`rpc.py:93`): after `<message>`, append `<bases>` with one `<base>`
      per class in MRO order, using the fully-qualified name:
  - normal case: `type(e).__mro__[1:]`, keeping classes that subclass `PyobsError`, leaving out
    `PyobsError` itself;
  - `original_type` set and `type(e)` is not `UnclassifiedError` (an ancestor-resolved exception
    forwarded over a second hop): include `type(e)` first, then its ancestors, so the ancestor
    itself is not lost;
  - `type(e)` is `UnclassifiedError`: no `UnclassifiedError` in the list (empty `<bases/>`).
- [ ] **New helper `xml_to_fault_bases(fault_elem) -> list[str]`** in `rpc.py`: returns the
      `<base>` texts, `[]` if the element is missing. `xml_to_fault` keeps its 2-tuple return.
- [ ] **New pure function `reconstruct_fault(name, msg, bases, sender) -> exc.PyobsError`** in
      `rpc.py`, extracted from `_on_jabber_rpc_method_fault` so it can be unit-tested (today the
      caller-side branch is only mirrored in `tests/comm/test_rpc_serialization.py:74-75`, not
      tested):
  ```python
  cls = exc.PyobsError.resolve(name)
  if cls is not None:
      return cls(msg, remote_module=sender)
  for b in bases:
      anc = exc.PyobsError.resolve(b)
      if anc is not None and anc is not exc.UnclassifiedError:
          return anc(msg, remote_module=sender, original_type=name)
  return exc.UnclassifiedError(msg, original_type=name, remote_module=sender)
  ```
- [ ] **`_on_jabber_rpc_method_fault`** (`rpc.py:280`): call the two helpers, `call_id`
      handling unchanged.
- [ ] Update the comments at `rpc.py:99-106` and `rpc.py:299-301`.

Wire example, plugin `class MyDriverTimeout(exc.MotionError)` in package `plugin`:

```xml
<!-- before -->
<pyobs:fault><exception>plugin.MyDriverTimeout</exception><message>timeout</message></pyobs:fault>
<!-- after -->
<pyobs:fault><exception>plugin.MyDriverTimeout</exception><message>timeout</message>
  <bases><base>pyobs.utils.exceptions.MotionError</base></bases></pyobs:fault>
```

Namespace `urn:pyobs:rpc:1` stays. Old parsers use `find()` and ignore the extra element.

### What the caller sees (prototyped in a scratchpad, real output)

| Case | Type | `isinstance(e, MotionError)` | `original_type` | `str(e)` |
|---|---|---|---|---|
| Leaf with registered ancestor (`MyDriverTimeout`) | `MotionError` | True | `"plugin.MyDriverTimeout"` | `<MotionError> timeout` |
| Only ancestor is `PyobsError` (`AltitudeLimitError` today) | `UnclassifiedError` | False | set | `<UnclassifiedError> ...` |
| Old peer, no `<bases>` | `UnclassifiedError` | False | set | unchanged from today |
| Leaf imported on caller | the leaf | per leaf | not set | unchanged from today |

### Behaviour change

- **Caller-side `except` blocks**: `except exc.MotionError:` / `except exc.FocusError:` (or any
  core ancestor) around a proxy call now catches unregistered leaves of that ancestor. Before,
  those faults went past the block as `UnclassifiedError`. An `except exc.UnclassifiedError:`
  block no longer catches them. Grep found no such blocks around proxy calls in core today.
- **Caller-side `_register_exception(SomeDomainType, module="x", ...)` handlers**:
  `_store_exception` and `_exception_matches` (`modules/module.py:262-300`) work on
  `type(e).__mro__`, so an ancestor-resolved fault now counts towards a handler registered for that
  ancestor with `module=`. Handlers without `module=` only count locally raised exceptions
  (`_check_exception_severity`), so remote faults never reach them, before or after. No such
  caller-side handler exists in core today (`basetelescope.py:303`, `basecamera.py:150`,
  `basedome.py:24` are callee-side, on errors the module raises itself).
- **Escalation caveat, stated correctly**: `pointing/_base.py:49-55` and `flatfield.py:93-101`
  register `exc.RemoteError` with `module=camera/telescope/filters`. `_exception_matches` already
  counts every fault tagged with `remote_module` as `RemoteError`, whatever its type. These
  handlers are therefore unaffected by (b): they count every remote fault before and after.
- **Code reading `original_type`**: it is now also set on ancestor-resolved instances, not only
  on `UnclassifiedError`. Nothing in core reads it except `fault_to_xml`.

### Mixed-version matrix

| Callee \ Caller | Old caller | New caller |
|---|---|---|
| Old callee (no `<bases>`) | today | today (no bases, falls back to `UnclassifiedError`) |
| New callee (`<bases>`) | today (`<bases>` ignored) | ancestor fallback |

No combination is worse than today.

### Tests (all unit, no ejabberd), `tests/comm/test_rpc_serialization.py`

- [ ] `fault_to_xml` on a leaf of `MotionError` emits `<bases>` with `MotionError` only, not
      `PyobsError`.
- [ ] Multi-level leaf (`class X(exc.MoveError)`) lists `MoveError`, `MotionError` in that order.
- [ ] `UnclassifiedError(original_type="builtins.IndexError")` emits `<exception>builtins.IndexError`
      and an empty `<bases/>` (no `UnclassifiedError`).
- [ ] Ancestor-resolved instance (`MotionError(..., original_type="plugin.X")`) emits
      `<exception>plugin.X` and `MotionError` first in `<bases>` (second-hop case).
- [ ] `xml_to_fault` still returns a 2-tuple; `xml_to_fault_bases` returns `[]` without
      `<bases>`.
- [ ] `reconstruct_fault`: registered leaf returns the leaf without `original_type`; leaf popped
      from `_registry` (simulated missing import) with `MotionError` base returns `MotionError`
      with `original_type`, `remote_module` and the raw message; leaf with only `PyobsError`
      returns `UnclassifiedError`; old-peer fault (no bases) returns `UnclassifiedError`; a
      `<base>` naming `UnclassifiedError` is skipped.
- [ ] `tests/modules/test_exception_logging.py`: an ancestor-resolved `MotionError` with
      `remote_module` counts towards a `_register_exception(exc.MotionError, ...)` handler and,
      unchanged, towards a `RemoteError` handler with `module=`.
- [ ] Restore `_registry` in a fixture after popping, so tests do not leak state.

## Step 2 (PR 2): documentation

### Proposed changes

- [ ] **New guide page** `docs/source/recipes/exceptions.rst`, added to the Guides toctree in
      `docs/source/index.rst` (after `recipes/xmpp-diagnostics`). Sections:
  1. *Hierarchy and which class to catch*: domain errors vs `RemoteError` subtree,
     `UnclassifiedError`; catch the most specific core class you care about.
  2. *What crosses the wire and what the caller receives*: name, message, bases; the four
     cases from the table in step 1; `remote_module`, `call_id`, `original_type`.
  3. *Defining your own error in a driver*: subclass the closest core class (not `PyobsError`
     directly) so callers without your package still catch it; declare it with `@raises`.
  4. *Catching and escalating*: `except` around proxy calls, `Module._register_exception`
     (threshold, timespan, `module=`), `_disable_exception_logging`. Note: `handle_exception`
     no longer exists since 2.0, do not document it.
  5. *Mixed versions*: the matrix from step 1 (and from step 3 if it lands).
  6. *Worked examples*: a driver `MyDriverTimeout(MotionError)` caught by a scheduler as
     `MotionError`; `AltitudeLimitError` today (arrives as `UnclassifiedError`, check
     `original_type`) and after step 3 if it lands.
- [ ] **`docs/source/api/utils/exceptions.rst`**: add the missing `ArchiveError` (0 hits today);
      add the errors moved in step 3 if it lands.
- [ ] **`docs/source/whatsnew-2.0.rst:364-368`**: the claim that a domain exception "can live
      anywhere ... and still survive the wire" overstates it. Add a short `.. note::` that it
      only survives as its own type if the caller imported its module, and since 2.x (version of
      step 1) falls back to its nearest core ancestor. Do not rewrite the release history
      otherwise. Add an entry to the current changelog.
- [ ] **`specs/design/exception_handling.md` §D and §5**: add a dated "Revisited (#952 item 8)"
      paragraph: base-class catches were missed, (b) added, (c) rejected again, outcome of step 3.
- [ ] **Docstrings**: `utils/exceptions.py` module docstring and `UnclassifiedError` docstring
      describe the ancestor fallback; `PyobsError` docstring tells driver authors to subclass the
      closest core class.

### Rules

- No links from the guide, API pages, README or whatsnew to `specs/`.
- After `sphinx-build`, check the Guides sidebar in a browser. A clean build does not catch a
  missing or misplaced toctree entry.

### Tests

- [ ] `sphinx-build -W` (or the project's usual docs build) passes.
- [ ] Sidebar checked in a browser.

## Step 3 (PR 3, conditional): the three errors (b) does not fix

Decide after step 1 lands. Only `AltitudeLimitError`, `WeatherResponseError` and `ScriptError`
still arrive as `UnclassifiedError`, because their only ancestor is `PyobsError`. The other six
already arrive as `MotionError`/`FocusError` after (b).

### Option 3A: move the three into `utils/exceptions.py`

- [ ] Move the class bodies (docstrings included; `AltitudeLimitError` stays a direct
      `PyobsError` subclass, see `basetelescope.py:82-88`: nothing was attempted, so it must not
      feed the callee's `_register_exception(exc.MotionError, 3, timespan=600, ...)` at
      `basetelescope.py:303`).
- [ ] Re-export from the old modules with `from pyobs.utils.exceptions import AltitudeLimitError
      as AltitudeLimitError` (explicit re-export for pyrefly/ruff). Do not add them to the old
      modules' `__all__` (`basetelescope.py:918`, `weather.py:242` only list the module class), so
      Sphinx does not document them twice. Keep `robotic/scripts/exceptions.py` and
      `robotic/scripts/__init__.py` exporting `ScriptError`.
- [ ] Register aliases in `utils/exceptions.py`, after the class definitions, as string literals
      (registering them in the old modules would only take effect once those are imported, which
      defeats the purpose):
  ```python
  PyobsError._registry["pyobs.modules.telescope.basetelescope.AltitudeLimitError"] = AltitudeLimitError
  PyobsError._registry["pyobs.modules.weather.weather.WeatherResponseError"] = WeatherResponseError
  PyobsError._registry["pyobs.robotic.scripts.exceptions.ScriptError"] = ScriptError
  ```
- [ ] Update interface docstrings that name them, if they refer to the old location.
- [ ] Write the ADR (draft below).

Mixed versions for 3A, stated plainly:

| Callee \ Caller | Old caller | New caller |
|---|---|---|
| Old callee (old name) | today | resolves via alias |
| New callee (new name) | **regression**: `UnclassifiedError` even if the old caller imported the old module | resolves |

The regression hits exactly the callers that did import the class. Nothing catches these three
today (see Context), so the practical impact is near zero, but it is real until the fleet is
upgraded. (b) does not help: old callers ignore `<bases>`.

### Option 3B: one new core base class plus two rebases, classes stay where they are

One new public name, two rebases onto an existing class:

- [ ] **New `PointingLimitError(PyobsError)`** in `utils/exceptions.py`, next to `MotionError`
      (a sibling, not a subclass). Docstring meaning: "The requested destination is outside the
      configured pointing limits (today the minimum altitude; later e.g. sun distance or dome
      limits). Nothing was attempted, and the device is fine. An expected condition: defer or
      skip the target, don't alert and don't retry immediately." `AltitudeLimitError` becomes
      `class AltitudeLimitError(exc.PointingLimitError)`.
  - Caller that reacts differently: the scheduler/mastermind defers or skips the task instead of
    treating it as a failed observation; the GUI can show it as "below limit" instead of an
    error.
  - Must NOT subclass `MotionError`, so it never feeds `BaseTelescope`'s callee-side
    `_register_exception(exc.MotionError, 3, timespan=600, ...)` (`basetelescope.py:303`) or any
    caller's `except exc.MotionError:`, keeping the intent at `basetelescope.py:82-88`. No
    `_register_exception(exc.PointingLimitError, ...)` anywhere in core. It still counts towards
    caller-side `RemoteError` handlers with `module=` (separate issue below).
- [ ] **`WeatherResponseError(exc.GeneralError)`**: a weather station returned a malformed
      response. No caller branches on it (only `Weather.get_sensor_value` raises it, nothing
      catches it), so no new name; `GeneralError` already means "a dependency failed" in the
      interface docstrings (`IAcquisition`, `ISyncTarget`, `ICalibrate`).
- [ ] **`ScriptError(exc.GeneralError)`**: `ScriptRunner.run` wraps any non-`PyobsError` from a
      script (`scriptrunner.py:55-60`). No caller branches on it either; same reasoning.
  - Neither may go under `ModuleError`: `ModuleError` is in `Module._UNSUPPRESSIBLE`
    (`module.py:219`) and means "the module itself is broken", which neither is.
  - Checked: no `except exc.GeneralError`, no `@raises(GeneralError)`, no
    `_register_exception(exc.GeneralError, ...)` and no `_disable_exception_logging(GeneralError)`
    in core, so the rebase changes no local catch, logging or escalation behaviour.
- [ ] Rebase the three classes. Location, qualified name and wire name stay the same.
- [ ] Update the `Raises:` sections of `IPointingRaDec`, `IPointingAltAz` and the other pointing
      interfaces to mention `PointingLimitError` as the class to catch.
- [ ] No aliases, no re-exports, no mixed-version regression: old callers see exactly today's
      behaviour, new callers get the base class via (b).
- [ ] No ADR needed; §D and §5 stay valid. Add the "subclass the closest core class" rule to the
      guide (step 2, section 3).

### Recommendation

3B. It fixes the same three cases through the mechanism drivers need anyway, keeps §D/§5 intact,
has no mixed-version regression and no alias table to maintain. 3A only adds exact-leaf catching
without importing the module, which no caller does today. The earlier draft of this plan
preferred 3A (no new base class); if 3A is chosen, the ADR below is required.

### Tests (either option)

- [ ] A fault for each of the three, resolved in a test with the leaf popped from `_registry`,
      arrives as the core class (3A: the class itself; 3B: `PointingLimitError` or
      `GeneralError` with `original_type`).
- [ ] 3B only: `issubclass(AltitudeLimitError, exc.PointingLimitError)`, and
      `PointingLimitError` is not a `MotionError`; `WeatherResponseError` and `ScriptError` are
      `GeneralError` and not `ModuleError`.
- [ ] 3A only: `resolve()` of each old qualified name returns the moved class; importing from the
      old path gives the identical class object; existing tests that import from the old paths
      (`tests/modules/weather/test_weather.py:12`, `tests/modules/robotic/test_scriptrunner.py:7`)
      pass unchanged.
- [ ] `AltitudeLimitError` is still not a `MotionError` (guards `basetelescope.py:303`).
- [ ] pyrefly and ruff clean on the old modules (re-exports).

### Draft ADR (only for 3A): `specs/adrs/00NN-contract-errors-live-in-core-exceptions.md`

> **Errors that interfaces document live in `pyobs.utils.exceptions`**
>
> status: proposed. date: 2026-10-12
>
> **Context and Problem Statement.** Design §D/§5 moved module-specific errors next to the code
> that raises them, relying on "whoever needs the type imports it". The interfaces document these
> errors as their contract, but callers coded against an interface (GUI, scheduler) do not import
> the implementation module, so they receive `UnclassifiedError`. The `<bases>` fallback (#952
> item 8, step 1) fixes errors with a core ancestor, but not errors whose only ancestor is
> `PyobsError`.
>
> **Considered Options.** (1) Keep them in place, document only. (2) Keep them in place with a
> small core base class, resolved through `<bases>`. (3) Import the defining module on demand from
> the fault. (4) Move errors that an interface documents into `pyobs.utils.exceptions`, with
> re-exports and aliases for the old names.
>
> **Decision Outcome.** Option 4: errors core owns and an interface documents live in
> `pyobs.utils.exceptions`. Module-internal errors and driver errors stay where they are and
> subclass the closest core class. (3) is rejected because import runs arbitrary module code.
> (2) is rejected because [Tim's reason].
>
> **Consequences.** Good: callers catch the exact type with only core imports. Bad: reverses
> §D/§5; one-way mixed-version regression (new callee, old caller) until the fleet is upgraded;
> alias table in `exceptions.py` to keep until the oldest supported peer has the new names; the
> file grows again.

## Open questions

1. **Second-hop forwarding: include `type(e)` in `<bases>` only when `original_type` is set?**
   Recommend yes. Without `original_type` the exception is its real type and `type(e)` is
   already the `<exception>` name.
2. **Should an ancestor-resolved instance keep `original_type` in `str(e)`?** Recommend no, keep
   `__str__` as is; `original_type` is an attribute for code and logs. Add it to the
   caller-side log line if one is added later.
3. **Bump the namespace to `urn:pyobs:rpc:2`?** Recommend no. The element is optional and
   ignored by old parsers; a namespace bump would break old callers.
4. **Step 3: 3A or 3B?** Recommend 3B (see above). Decide after step 1 lands.
5. **Step 3A: how long to keep the aliases?** Recommend until the next major version, and list
   them in the changelog.
6. **Step 3B names: decided.**
   - `PointingLimitError` for `AltitudeLimitError`'s base: it names the condition (destination
     outside pointing limits), covers future sun/dome limits, and doesn't overlap with weather
     or daytime the way `TargetNotObservableError` would. Follows the `<Noun>Error` style of
     `MotionError`/`FocusError`.
   - `WeatherResponseError` and `ScriptError` go under `GeneralError`: no caller branches on
     either, and `GeneralError` already means "a dependency failed", so a new name would add
     public surface nothing uses.

## Separate issue to file (not part of this plan)

Caller-side escalation for expected conditions: `pointing/_base.py:52-54` and
`flatfield.py:97-99` register `exc.RemoteError` with `module=telescope`, and `_exception_matches`
(`module.py:275-282`) counts every remote-tagged fault as `RemoteError`. A target below the
altitude limit (`AltitudeLimitError`) therefore counts towards their 3-in-600 s escalation, which
contradicts the intent at `basetelescope.py:82-88` ("must not count towards ... escalation").
Inferred from code, not tested. Possible fix: let `_register_exception` take an `exclude` tuple,
or keep a small set of "expected condition" types that `_exception_matches` skips for the
`RemoteError` case.

## Not verified

- Live XMPP run with a plugin error between two modules; behaviour is from code reading plus a
  two-process scratchpad reproduction of `fault_to_xml`/`resolve`.
- Repos outside `~/code/pyobs` (other observatories' private plugins) that might import or catch
  the nine errors, or rely on `UnclassifiedError` for them.
- Whether Sphinx warns about duplicate objects for explicit re-exports outside `__all__` (3A).
- Whether pyrefly accepts `import X as X` as an explicit re-export without a config change.
- The exact behaviour of pyobs-gui when it receives an ancestor-resolved error (only the absence
  of imports and catch sites was checked).

## Out of scope

- (c) import on demand, rejected above.
- Moving the six errors that already resolve to `MotionError`/`FocusError` after (b).
- The escalation issue above (separate issue).
- Events: the same "class must be imported on the receiving side" limitation applies to `Event`
  subclasses (`2026-10-12-derived-events-for-module-event-classes.md`), by design.
