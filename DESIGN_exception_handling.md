# Exception handling across the RPC boundary

Status: implemented (rolled out across #669 and follow-ups); the documentation sweep (rollout steps
6-8) and every known driver-repo companion fix have since landed too — `pyobs-brot` (silent
init/park failure), `pyobs-sbig`/`pyobs-fli` (`AbortedError` on abort), and `pyobs-sbig` again
(`InvalidArgumentError` on unknown filter name) — see the updated notes on those items below. Tracks
#446, closed. One known gap remains, deliberately unaddressed: `pyobs-iagvt`'s stale
`InvocationError` import (see "Resolved during design" below) — currently a hard `ImportError` at
module load, confirmed by direct import, not just a silently-degrading catch as originally
described. Left as-is per current decision, not because it isn't real.

## Problem

Issue #446, as filed: RPC methods raise exceptions that are sent to the caller *and* logged
locally by the raising module, and the local log is redundant since the caller already sees
the error. The issue sketches a fix: let a module declare exception types (e.g. `FocusError`)
that should not be logged locally, via something like `self._disable_exception_logging(FocusError)`.

Looking at the actual dispatch/serialization code broadens the problem. Almost all module code
is reachable from one of the small set of RPC-exposed interface methods that `Module.execute()`
dispatches to — a `raise ValueError(...)` several calls deep in a private helper is just as much
an RPC-boundary exception as one written directly in the interface method body, if that helper
only gets reached via an RPC call. Once you look at what actually crosses the wire today, three
distinct problems show up, not one:

1. **Redundant local logging** — the issue's original complaint.
2. **Silent type degradation** — an exception that isn't a `pyobs.utils.exceptions.PyObsError`
   subclass turns into a generic `RemoteError` on the caller's side, discarding the original type
   and any structured information, leaving only a string message.
3. **Drift between what's documented, what's declared, and what's actually raised** — several
   interfaces document a `Raises:` clause that doesn't match the implementation, and the one
   opt-in mechanism that exists (`@raises(...)`) is applied to two methods out of dozens.

All three affect the same code path, so it's worth designing them together rather than patching
#446 in isolation.

## Current state

### Exception hierarchy — `pyobs/utils/exceptions.py`

```
Exception
└── PyObsError                         (message, logged flag, .log() dedup helper)
    ├── ModuleError
    ├── GeneralError
    ├── ImageError
    ├── MotionError
    │   ├── InitError
    │   ├── ParkError
    │   └── MoveError
    ├── GrabImageError
    ├── AbortedError
    ├── FocusError
    ├── AcquisitionError
    ├── RemoteError                    (module: str, message: str | None)
    │   ├── RemoteTimeoutError
    │   ├── InvocationError            (module: str, exception: Exception) — non-standard ctor
    │   └── ForbiddenError             (sender: str, method: str) — non-standard ctor
    └── SevereError                    (exception: PyObsError, module: str | None) — non-standard ctor, no metaclass
```

`PyObsError.__init__(message=None, logged=False)` (`pyobs/utils/exceptions.py:18-20`) and
`.log(log, level, message, **kwargs)` (lines 28-32) are the existing "don't log twice"
mechanism: `.log()` is a no-op once `self.logged` is `True`. It's per-instance, not per-type —
it stops the *same* exception object from being logged at a second catch site in the same
process, but says nothing about whether a type should be logged at all, and a freshly
reconstructed exception on the far side of an RPC call starts with `logged=False` again.

A metaclass (`_Meta`, lines 35-41) intercepts construction of every `PyObsError` subclass and
feeds `register_exception()`/`handle_exception()` (lines 176-219), a frequency-based escalation
system: register that N occurrences of a type (optionally scoped to a module, optionally within
a timespan) should invoke a callback and/or escalate to `SevereError`. `AutoFocusSeries.__init__`
uses this (`pyobs/modules/focus/focusseries.py:80-88`) to watch for repeated `RemoteError` from
its camera/focuser dependencies. This is a different axis from logging verbosity — it's about
detecting *repeated* failures — but it's the existing precedent for "a module registers exception
policy in its constructor," which matters for how `_disable_exception_logging` should look.

### Where local logging happens

Two catch sites in the core dispatch path, both currently reachable regardless of transport:

**`Module.execute()`**, `pyobs/modules/module.py:396-469` — the single chokepoint every
transport (XMPP RPC, `LocalComm`, `MultiModule`) routes an interface-method call through:

```python
# pyobs/modules/module.py:452-467
try:
    response = await func(*func_args, **ba.arguments, **func_kwargs)
except Exception as e:
    # something else went wrong, but only log if not a ModuleError
    if isinstance(e, exc.PyObsError) and not isinstance(e, exc.ModuleError):
        level = (
            "INFO"
            if hasattr(func, "raises")
            and isinstance(getattr(func, "raises"), tuple)
            and type(e) in getattr(func, "raises")
            else "ERROR"
        )
        exc_info = level == "ERROR"
        e.log(log, level, f"Exception was raised in call to {method}: {e}", exc_info=exc_info)
    raise e
```

**`RPC._on_jabber_rpc_method_call()`**, `pyobs/comm/xmpp/rpc.py:222-227` — the XMPP-specific
dispatcher, which calls `Module.execute()` and, on exception, logs again before serializing a
fault back to the caller:

```python
except Exception as e:
    if isinstance(e, exc.PyObsError):
        e.log(log, "ERROR", f"Exception in call to {pmethod}: {e}", exc_info=True)
    else:
        log.exception("Unexpected exception in %s.", pmethod)
    self._client.plugin["xep_0009"].send_fault(iq, fault_to_xml(e))
```

Because `.log()` no-ops once `logged=True`, this second call is currently inert for the common
case of a `PyObsError` that isn't a `ModuleError` (already logged by `execute()`). Two
asymmetries worth noting: `ModuleError` is deliberately *skipped* in `execute()` (the `and not
isinstance(e, exc.ModuleError)` guard) so it only gets logged here instead, and a raw non-`PyObsError`
exception is *only* logged here, unconditionally, via `log.exception(...)` — it never passes
through `execute()`'s `isinstance(e, exc.PyObsError)` branch at all.

**The real redundancy** is elsewhere: a module that raises `FocusError` gets it logged once
locally via `execute()`. A *different* module that called it through a proxy typically wraps the
call in a blanket `except Exception: log.exception(...)` and logs the same failure a second time,
in a different process/log, because the reconstructed `InvocationError` on the caller's side has
`logged=False` — it's a new object. Concrete instances of this pattern in core (not user
processor code): `pyobs/modules/robotic/mastermind.py:172-174`, `scriptrunner.py:61`,
`pointing.py:77`, `scheduler.py:279`, `pyobs/modules/module.py:772`
(`MultiModule._run_module`). None of these consult `.logged` or any per-type suppression list —
they always log.

Also worth tracing precisely, since it's not what it first looks like: `Comm.open()` attaches a
`CommLoggingHandler` to the root logger at `INFO` (`pyobs/comm/comm.py:70-78`). Its `emit()`
(`pyobs/comm/commlogging.py:27-43`) fires for any record at or above that level — with zero
awareness of exception type, `@raises`, or anything else — and unconditionally calls
`self._comm.log_message(entry)` (queued, then published via `XmppComm.send_event()`,
`pyobs/comm/xmpp/xmppcomm.py:665-687`, which always calls
`self.client.plugin["xep_0163"].publish(...)`). This is PEP (XEP-0163) publish, not a blind
broadcast: `_register_events()` (`xmppcomm.py:703-718`) only calls `add_interest(...)` for a given
event type `if handler:` (line 712-714) — i.e., only modules that actually called
`register_event(LogEvent, handler=...)` (the GUI, `fluentlogger.py`, etc.) ever receive delivery;
the server filters by declared interest, so this is already correctly scoped to real consumers,
not everyone. The real, already-existing cost is on the *publish* side, not delivery: the
unconditional `xep_0163.publish()` call happens for every record ≥ INFO regardless of whether
anyone is interested, which means **every currently-logged domain exception already pays this
cost today** — nothing in the current code gates the network publish below a plain level
threshold, and since `ERROR` ≥ `INFO`, this has always been true for every domain exception this
doc discusses, not something a fix here would newly introduce.

### The existing partial mechanism: `@raises(...)`

```python
# pyobs/modules/module.py:87-100
def raises(*exceptions: type[exc.PyObsError]) -> Callable[[F], F]:
    """
    Decorates a method with information about which pyobs exceptions it raises. These exceptions are
    logged in this module, but as INFO without stacktrace.
    """
    def raises_decorator(func: F) -> F:
        setattr(func, "raises", exceptions)
        return func
    return raises_decorator
```

Used on exactly two methods: `AutoFocusSeries.auto_focus`
(`pyobs/modules/focus/focusseries.py:106`, `@raises(exc.AbortedError, exc.FocusError)`) and
`Acquisition.acquire_target` (`pyobs/modules/pointing/acquisition.py:116`,
`@raises(exc.AbortedError, exc.AcquisitionError)`). It demotes to INFO-without-traceback rather
than suppressing entirely (issue #446 asks for no local log at all), and its match is exact-type
(`type(e) in getattr(func, "raises")`), not `isinstance` — a subclass of a declared type would
still log at ERROR today.

Re-examining this while designing the fix (see proposal §1) changes its role rather than just its
match semantics: INFO-without-traceback is exactly what a *default* domain-exception log line
should look like, for *any* `PyObsError`, not just the two methods someone remembered to decorate.
Every other RPC-exposed method raising a domain exception gets no demotion today purely because
nobody wrote `@raises` on it — an omission bug, not a deliberate choice, and not something worth
preserving as an opt-in mechanism. Proposal §1 makes INFO-without-traceback the automatic default
for every domain exception and retires `@raises` as a logging mechanism entirely — it can still
carry documentation value (feeding §7's docstring-cross-check idea) but no longer controls log
level.

No `_disable_x`-style instance/class configuration method exists anywhere on `Module`/`Object`
today (grepped, no hits). The closest structural precedent for "an instance-level table consulted
inside `execute()`'s hot path" is the ACL system (`Module._parse_acl()`,
`pyobs/modules/module.py:292-336`, consulted at line 426) — config-driven via a constructor
kwarg rather than an imperative call, but the same shape.

### `register_exception` vs. the proposed `_disable_exception_logging` — not the same axis

It's worth being precise about this, because the two look superficially similar ("declare how a
module treats an exception type") but control entirely different things, and there's a real
interaction between them that the design needs to account for.

`register_exception(exc_type, limit, timespan=None, module=None, callback=None, throw=False)`
(`pyobs/utils/exceptions.py:176-184`) is a **frequency-based circuit breaker**, not a logging
control:

- It fires at **construction time**, not raise time — every `PyObsError` subclass goes through
  metaclass `_Meta` (`exceptions.py:35-41`), so the act of writing `exc.FocusError("...")`
  already invokes `handle_exception()` before the surrounding `raise` statement runs.
- Its state is **process-global**: `_handlers: list[ExceptionHandler]`, `_local_exceptions`, and
  `_remote_exceptions` (`exceptions.py:165-167`) are module-level dicts, not attached to any
  `Module` instance.
- It counts occurrences of a type — optionally scoped to a *remote* module name string, optionally
  within a timespan — and once a threshold is hit, invokes an async `callback` and/or, if
  `throw=True`, **substitutes the exception for a `SevereError`**
  (`handle_exception`, `exceptions.py:212-214`: `return SevereError(exception=exception,
  module=module)`). Because `_Meta.__call__` returns whatever `handle_exception` returns, writing
  `exc.FocusError("...")` can silently hand back a `SevereError` instance instead — the
  constructor call substitutes the runtime type. `AutoFocusSeries.__init__` uses this to watch its
  camera/focuser dependencies (`focusseries.py:80-88`): three `RemoteError`s from the camera
  within 600s escalates to something the module treats as unrecoverable.

`_disable_exception_logging` (proposed) is a **verbosity control**, nothing else:

- It's read at **`Module.execute()`'s catch block** — only once a call has actually raised and is
  about to return to a caller.
- It's scoped **per-`Module`-instance**, matched with `isinstance` against a declared list.
- Its only effect is whether `e.log(...)` runs locally. It never changes the exception's type,
  and never affects whether the caller sees it.

**The interaction**: because `register_exception`'s type substitution happens *before* the
exception is even raised, a module that calls `self._disable_exception_logging(FocusError)` can
still get a full ERROR-level log for what looks like the same failure — after enough repeats, the
object reaching `execute()`'s catch block is a `SevereError`, not a `FocusError`, and
`isinstance(e, (FocusError,))` is `False` for it. That's arguably the *right* outcome (a merely
expected failure that starts repeating is exactly what escalation exists to surface), but it's an
emergent interaction between two independently-built mechanisms, not something either one was
designed with the other in mind for. The design needs to state this explicitly as intended
behavior rather than leave it to be discovered later: **disabling logging for a type disables it
only until escalation substitutes a different type**, at which point normal logging resumes.

There's also an existing, independent bug worth fixing while touching this file: because the
severity state is process-global rather than instance-scoped, two `Module` instances in the same
process (e.g. under `MultiModule`, or two `AutoFocusSeries` instances watching the same camera)
share the same counters, keyed only by `(exc_type, remote_module_name)` — not by which instance
registered the handler. Two instances each calling `register_exception(RemoteError, 3,
module="camera1", ...)` would both be watching, and both firing their own callback off, one
shared count. Since this proposal is already adding a new instance-scoped exception-policy
attribute (`_disabled_exception_logging`) right next to this system, it's a natural point to move
`_handlers`/`_local_exceptions`/`_remote_exceptions` onto the `Module` instance itself (e.g. as
`self._exception_handlers`, populated by an instance method instead of a module-level function),
closing the cross-instance leakage as a side effect rather than a separate, unrelated PR.

### Wire serialization: does the type actually survive?

This is the sharper finding. `fault_to_xml()` (`pyobs/comm/xmpp/rpc.py:93-106`) serializes
**only** the class name and `str()`:

```python
exc_elem.text = type(exception).__name__
msg_elem.text = str(exception)
```

On the receiving side, `_on_jabber_rpc_method_fault()` (`pyobs/comm/xmpp/rpc.py:259-283`)
reconstructs by looking the name up in `pyobs.utils.exceptions` only:

```python
exception_class = getattr(exc, exc_name, None)
if exception_class is None or not issubclass(exception_class, Exception):
    exception_class = exc.RemoteError
...
if issubclass(exception_class, exc.RemoteError):
    exception = exception_class(message=msg, module=sender)
else:
    exception = exception_class(msg)
future.set_exception(exc.InvocationError(module=sender, exception=exception))
```

So: raise a `PyObsError` subclass that lives in `pyobs.utils.exceptions` (`FocusError`,
`GrabImageError`, `MoveError`, ...) and the caller genuinely gets that same type back, wrapped in
`InvocationError`, message intact — this mechanism works as designed. Raise anything else — a
builtin (`ValueError`, `TypeError`, `NotImplementedError`, ...) or an ad hoc non-`PyObsError`
class defined outside `exceptions.py` (e.g. `CameraException`,
`pyobs/modules/camera/basecamera.py:33`) — and the name lookup fails silently, falling back to
generic `exc.RemoteError`. The original class name is discarded; only the string message
survives. The constraint "must be a `PyObsError` subclass *and* live in
`pyobs.utils.exceptions`'s namespace" is real but implicit and undocumented — `CameraException`
is a purpose-built domain exception that doesn't get the benefit purely because of where it's
defined.

There's also a latent reconstruction bug in the same function: it assumes every `RemoteError`
subclass accepts `(module, message=None)` as keywords. `InvocationError.__init__(self, module,
exception)` and `ForbiddenError.__init__(self, sender, method)` don't match that signature — if
either were ever the type named in a fault (`ForbiddenError` currently bypasses this path via a
separate XEP-0009 IQ-error condition, but nothing prevents `InvocationError` from being re-raised
across a second RPC hop), `exception_class(message=msg, module=sender)` raises a `TypeError`
*inside the fault-reconstruction handler itself*. No live call path currently triggers this, but
it's a structural gap worth closing while touching this code.

### Concrete gaps found in module code

- `CameraException(Exception)` (`pyobs/modules/camera/basecamera.py:33`) — plain `Exception`,
  not `PyObsError`. Raised from `grab_data`/`grab_sequence` when the camera isn't idle
  (lines 354, 389). Loses the severity-tracking machinery in `exceptions.py` and degrades to
  generic `RemoteError` on the wire (per above).
- `FocusModel.set_optimal_focus` (`pyobs/interfaces/IFocusModel.py`'s sole abstract method,
  implemented in `pyobs/modules/focus/focusmodel.py`) raises bare `ValueError` for every failure
  mode — invalid/missing weather temperature (line 278), timed-out module temperature fetch
  (line 296), sensor missing from response data (line 307) — despite `FocusError` already
  existing in the same "focus" subsystem and being used correctly one file over in
  `focusseries.py`. `IFocusModel.py` documents no `Raises:` clause at all.
- `BaseTelescope` (`pyobs/modules/telescope/basetelescope.py`) mixes patterns on the same
  RPC-exposed methods (`move_radec`, `move_altaz`, `track_body`, `track_orbital_elements`):
  bare `NotImplementedError` for missing mixin capability (lines 295, 377, 521, 541), domain
  `ValueError`s for bad pointing/config state (lines 176, 303, 311, 385, 498, 543, 810 — "no
  observer given," "destination altitude below limit," "could not resolve body," ...), and one
  correctly-typed `exc.MoveError` (line 588). The `ValueError` cases read like good candidates
  for a typed exception (e.g. a `MoveError`/`AltitudeLimitError` distinction) rather than an
  undifferentiated `ValueError` that degrades to `RemoteError` on the wire.
- `ScriptRunner.run()` (`pyobs/modules/robotic/scriptrunner.py`, RPC-exposed via `IRunnable`)
  calls `await script.run(None)` with no surrounding `try`/`except` — whatever a `Script`
  subclass raises goes straight out over RPC unwrapped. `autofocus.py:60`,
  `transitimaging.py:64,86`, `callmodule.py:54,61,68`, `cases.py:32` all raise bare `ValueError`
  on this path, but not all are the same *kind* of gap. `callmodule.py:68` is worth flagging
  specifically — it catches an arbitrary exception from a proxied call and does
  `raise ValueError(str(e))`, collapsing whatever type the remote side had into a fresh
  `ValueError`, discarding it a second time on top of the RPC-boundary degradation already
  described above. `transitimaging.py:64,86`'s `"No TransitMerit found on task."` is a different
  case entirely: `TransitImagingScript.can_run()` (`transitimaging.py:30-49`) already checks for
  exactly this condition and reports it through the *real* skip mechanism — it sets
  `self._cant_run_reason` and returns `False`, which is how a scheduler is meant to find out a
  task isn't runnable *without* an exception. The `ValueError` inside `run()`/
  `_run_configurations()` only fires if something invokes `run()` without checking `can_run()`
  first — a caller-contract violation, not a domain failure — so it isn't actually a case of
  "this needs a nicer exception type," it's dead code in properly-scheduled operation. Contrast
  with `autofocus.py:60`'s `"No target given."`: `AutoFocusScript.can_run()`
  (`autofocus.py:25-48`) checks proxy availability and telescope readiness but has *no*
  equivalent check for a missing target, so that `ValueError` is a genuinely reachable runtime
  failure, not a redundant one. The real fix for the `transitimaging.py` case is to trust
  `can_run()`'s existing gate (or, if defense-in-depth is wanted, keep a minimal assertion there,
  not a rich exception type); the real fix for `autofocus.py` is arguably to extend `can_run()` to
  check for a target too, closing the gap at the same place `transitimaging.py` already closes it
  for its own precondition, rather than reporting the absence only after `run()` has started.
- Documentation/implementation mismatch: `IAutoFocus.py:56-57` documents
  `Raises: ValueError: If focus could not be obtained.` — but `AutoFocusSeries.auto_focus`
  raises `exc.FocusError`/`exc.AbortedError` (confirmed via its own `@raises(...)` decorator),
  never `ValueError`. Nothing cross-checks the docstring against either the decorator or the
  actual `raise` statements, so this drifted silently.
- Existing good pattern worth generalizing: `BaseCamera.__expose()`
  (`pyobs/modules/camera/basecamera.py:263-276`) already catches broad `Exception` from the
  actual hardware exposure call and re-wraps it as `exc.GrabImageError(str(e))` *before* it can
  reach the RPC layer — i.e., translate to a typed exception at the module boundary. This isn't
  done consistently (`basetelescope.py`, `focusmodel.py`, the `Script` subclasses don't do it),
  but it's exactly the shape a broader convention should formalize.

  This matters even more for **third-party/vendor SDK exceptions** than for plain Python builtins,
  and it's not just good hygiene there — it's structurally required. A `PyObsError` subclass
  survives the RPC round-trip because every pyobs module has `pyobs-core` installed; the type name
  always resolves on the receiving side. A vendor exception doesn't have that guarantee at all:
  `pyobs_aravis.aravis.AravisException` (a class vendored from a third-party library,
  `pyobs-aravis/pyobs_aravis/aravis.py:22-23`) is only importable in a process that happens to have
  `pyobs-aravis` installed — a scheduler or GUI process receiving a fault naming that type has no
  way to reconstruct it, with or without Assessment §D's registry improvement, because the
  defining class simply isn't available there. Vendor exceptions can't be handled better at the
  wire layer; they have to be converted to a `PyObsError` before they ever leave the module that
  raised them, because past that point no representation of them could possibly survive. Checked
  whether `pyobs-aravis` already does this: it doesn't. `araviscamera.py`'s only `try`/`except` is
  the unrelated background `_capture()` loop swallowing everything silently (see driver survey
  below); nothing catches `AravisException` where it's actually raised
  (`aravis.Camera(self._device_name)`, `araviscamera.py:69`). That call happens to sit inside
  `open()` (module startup), not an RPC-exposed method, so today it only crashes startup rather
  than leaking a vendor type over an active call — but that's incidental to where the vendor SDK
  is invoked, not a deliberate boundary, and the same SDK could just as easily raise mid-operation
  the way `BaseCamera.__expose()`'s hook already anticipates for its own vendor calls.

### Confirmed by a full interface docstring audit

Rather than assume the two known mismatches (`IAutoFocus`, `IFocusModel`) were the whole picture,
every file in `pyobs/interfaces/` (55 files) was checked against its concrete implementation(s):
every abstract method with a `Raises:` clause, plus every method without one that has a plausible
failure mode. Of 27 interfaces with a documented `Raises:` clause, **16 have at least one confirmed
mismatch** against what actually happens. This isn't a handful of typos — it's a systemic gap, and
several of the findings are more significant than anything found before this audit:

- **`InitError`/`ParkError` (`IMotion.py:34-48`) are never raised anywhere in the entire
  `pyobs/modules/` tree — zero call sites.** Not one implementation honors the documented
  contract. This directly explains the `pyobs-brot` bug found earlier: it isn't that `pyobs-brot`
  alone silently returns success instead of raising these types — none of pyobs-core's own
  reference/dummy implementations (`telescope/_dummytelescopebase.py`, `roof/dummyroof.py`,
  `flatfield/flatfield.py`, `utils/dummymode.py`) raise them either. What they raise instead, when
  they raise anything: `AcquireLockFailed` (`pyobs/utils/threads/lockwithabort.py:10,37`, via
  `LockWithAbort`) — a **plain `Exception` subclass, not a `PyObsError`** — leaking undocumented
  out of `move_radec`, `move_altaz`, `set_focus`, `park`, `stop_motion`, and roof `init`/`park`
  alike. `DummyRoof`'s own docstrings even document `AcquireLockFailed` locally, silently
  contradicting the base `IMotion` contract one level up.
- **`MoveError` is documented on roughly 13 different pointing/tracking/filter/mode interface
  methods** (`IPointingRaDec`, `IPointingAltAz`, `IPointingBody`, the three
  `IPointingHeliocentric*`/`IPointingHelio*` interfaces, `IPointingOrbitalElements`,
  `IOffsetsAltAz`, `IOffsetsRaDec`, `ITrackingRate`, `ITrackingMode`, `IFilters`, `IMode`) **but has
  exactly one raise site in the whole codebase** (`basetelescope.py:588`), and that site sits
  inside an internal background-refresh task, not synchronously reachable from any RPC call. For
  practical purposes, `MoveError` is a documented type an RPC caller essentially never receives —
  what actually happens on the routine, easily-triggered failure paths (no observer configured,
  destination below the altitude limit) is an undocumented bare `ValueError`
  (`basetelescope.py:~300-304,~385`), exactly the sites proposal §4 already targets with
  `MissingObserverError`/`AltitudeLimitError`/etc. This audit confirms those aren't just "nicer
  types to have" — they're closing a real, previously-undocumented gap between the interface
  contract and reality.
- **`IData.grab_data` documents `GrabImageError`, but two of the three camera-family base classes
  never raise it at all.** `BaseSpectrograph.grab_data` (`camera/basespectrograph.py:164-186`) and
  `BaseVideo.grab_data` (already flagged above for a different reason) both raise only bare
  `ValueError`; only `BaseCamera`/`PipelineCamera` honor the documented type. Most concrete camera
  types in this framework don't actually raise the interface's headline exception.
- Two **unconditional `NotImplementedError`s** contradict their documented types outright:
  `ScienceFrameGuiding.set_exposure_time` (`pointing/scienceframeguiding.py:47`, documents
  `ValueError`) and `_DummyTelescopeBase.set_focus_offset` (`telescope/_dummytelescopebase.py:361`,
  documents `ValueError`/`MoveError`) — every single call to either fails with a type nowhere near
  what's documented.
- `IAutoFocus`/`IAcquisition` (already known): both document `ValueError`, but their own
  `@raises(...)` decorators — pyobs's *own* machine-readable exception metadata — declare
  `AbortedError`/`FocusError`/`AcquisitionError`/`GeneralError` instead. The docstring and the
  code's own authoritative contract disagree with each other, not just with what actually happens.

Interfaces confirmed as a clean match: `IConfig`, `IPointingBody`/`IPointingOrbitalElements` (their
primary `ValueError` paths), `IAbortable`, `IImageType`, `IStartStop`, `IModule`. Several interfaces
(`ICalibrate`, `ISyncTarget`, `IMultiFiber.set_fiber`, `IPointingSeries`, `IRotation`,
`IScriptRunner.run_script`, `IStructuredConfig`) have zero concrete implementers anywhere in this
repo, so the doc gap itself is the finding — a future implementer has no contract to follow at all.

### Confirmed in downstream driver projects

Checked the real hardware-driver projects (`pyobs-sbig`, `-fli`, `-aravis`, `-v4l`, `-brot`) for
the same class of gap, rather than assuming `basecamera.py`/`basetelescope.py`'s issues are the
whole picture. They're not — one of these is more serious than anything found in-tree.

- **Abort signal gets lost, independently, in two projects.** `BaseCamera._expose()`'s docstring
  (`pyobs/modules/camera/basecamera.py:213-227`) documents only `Raises: GrabImageError` — it
  never mentions `AbortedError`, even though every implementation is handed an `abort_event` and
  is clearly expected to react to it. Three independent raise sites across two different driver
  projects all guessed the same wrong type instead: `sbigcamera.py:162`
  (`raise InterruptedError("Exposure aborted.")`), `sbigfiltercamera.py:168`
  (`raise InterruptedError("Filter change aborted.")`), `flicamera.py:169`
  (`raise InterruptedError("Aborted exposure.")`). Since `BaseCamera.__expose()`'s except block
  only passes `PyObsError` through unchanged and wraps everything else into
  `GrabImageError(str(e))` (`basecamera.py:268-276`), an aborted SBIG/FLI exposure surfaces to the
  RPC caller as `GrabImageError`, not `AbortedError` — code written against the documented
  contract (`except exc.AbortedError: # user cancelled, not a failure`) would misclassify every
  cancelled exposure as a hardware fault. The filter-wheel abort is worse: `set_filter()` isn't
  part of the `__expose()` pipeline at all, so that `InterruptedError` isn't even wrapped into
  `GrabImageError` — it's a raw builtin hitting the RPC layer directly, which degrades to generic
  `RemoteError` on the wire (per the wire-serialization findings above) with the fact that it was
  an abort lost entirely. This isn't "two sloppy drivers" — it's that nothing in pyobs-core ever
  told driver authors which type to use, and two independent people reached for the same
  reasonable-sounding builtin. Worth its own line item: document the `AbortedError` contract
  explicitly wherever an `abort_event`/similar is handed to a driver hook, and fix the three call
  sites.
- **`ModuleError` misuse confirms a real discoverability gap.** `flifilterwheel.py:89` raises
  `exc.ModuleError("Filter not found")` for a caller supplying an unknown filter name — but
  `ModuleError` specifically means "the module itself is in ERROR state, block all calls"
  (`Module.execute()`, `pyobs/modules/module.py:416-419`), an unrelated concept. The correct type
  per the already-documented `IFilters` convention is `ValueError`, used correctly one file over
  in `sbigfiltercamera.py:142` (`raise ValueError(f"Unknown filter: {filter_name}")`) for the
  identical condition. Real evidence that the convention isn't currently discoverable enough
  without something enforcing it (ties into goal 4 and the docstring-cross-check idea in §6).
- **Two more confirming instances of the `NotSupportedError` gap** (already proposed above, until
  now motivated only by in-tree `basetelescope.py` code): `sbigfiltercamera.py:137`
  (`raise NotImplementedError` — camera has no filter wheel) and `brottelescope.py:190`
  (`raise NotImplementedError` — mount doesn't support a custom tracking rate). Same
  capability-check shape in two more independent projects; no new proposal needed, just stronger
  evidence for the one already in §4.
- **`BaseVideo` (`pyobs-aravis`, `-v4l`) is missing `BaseCamera`'s exception-wrapping entirely, and
  this is a `pyobs-core` gap, not a driver one.** `AravisCamera`/`v4lCamera` extend `BaseVideo`
  (`pyobs/modules/camera/basevideo.py`), not `BaseCamera` — a different, continuous-capture-loop
  base class for streaming devices. `v4lCamera` has zero `raise`/`except` statements of its own; it
  inherits entirely from `BaseVideo`'s handling. That handling has two gaps: `_capture()`'s
  background loop (`araviscamera.py:117`, `except Exception: await asyncio.sleep(1)`) swallows
  every internal failure and just retries forever, so a persistently failing camera never surfaces
  anything to any caller at all; and `BaseVideo.grab_data()`'s own "no image" condition
  (`pyobs/modules/camera/basevideo.py:476`) raises a bare `ValueError("Could not take image.")`
  instead of `exc.GrabImageError`, inconsistent with `BaseCamera`'s equivalent path
  (`basecamera.py:266`). Worth folding into proposal §4 as a `BaseVideo`-specific fix, parallel to
  but separate from `BaseCamera`'s.
- **The significant one: `pyobs-brot`'s roof/dome/telescope never raise at all on hardware
  error.** `BrotRoof.init/park` (`brotroof.py:61-98`), `BrotDome.init/park` (`brotdome.py:76-153`),
  and `BrotBaseTelescope`'s status handling (`brottelescope.py:100-286`) all call a shared
  `_error_state(mess)` helper when the underlying hardware reports an error status — and that
  helper only does `log.error(mess)` plus setting the motion status to `ERROR`
  (`brotroof.py:102-104`, identical shape in `brotdome.py:161-163` and `brottelescope.py:149-151`).
  Every calling method then just `return`s normally. Confirmed across all three files, 8+ call
  sites. This means `init()`/`park()` **always return successfully to the RPC caller**, even when
  the roof/dome/telescope hardware genuinely failed to move — despite `IMotion.init()`/`park()`
  explicitly documenting `Raises: InitError`/`ParkError` (`pyobs/interfaces/IMotion.py:34-38,
  40-46`), types that already exist in the hierarchy for exactly this. This is a different, more
  serious class of gap than everything else in this doc: it's not that the wrong type crosses the
  RPC boundary, it's that *nothing* does — a caller has no way to learn the operation failed except
  by separately polling or subscribing to motion state, and any code written against the
  documented `except exc.InitError:`/`except exc.ParkError:` contract would never fire. This can't
  be fixed by this PR (it's a different repository) but is strong, concrete validation of why goal
  4 matters beyond tidiness: the documented contract already exists and a real production driver
  already silently doesn't honor it. Fix in `pyobs-brot`: `_error_state()` (or its callers) should
  `raise exc.InitError(mess)`/`raise exc.ParkError(mess)`/`exc.MoveError(mess)` as appropriate,
  instead of only logging.

## Assessment: what I'd design differently, given a free hand

The incremental fixes below (Proposed design §§1-10) all still make sense on their own, but stepping back,
the model has a structural problem none of them touch: **a caller can never actually catch a
specific domain exception around a proxy call today**, no matter how fine-grained the hierarchy
becomes. That undercuts goal 5 (add more, finer types) more than any of the individual gaps —
there's no point minting `CameraBusyError`/`WeatherDataError`/etc. if nothing can ever catch them
directly at the point they matter. This section is the "if I were redoing this" pass; it's more
invasive than the rest of the doc, so I'm keeping it separate rather than quietly folding it into
the proposal.

### A. Stop double-wrapping every remote domain exception in `InvocationError`

`_on_jabber_rpc_method_fault` (`pyobs/comm/xmpp/rpc.py:259-283`) does correctly reconstruct the
original type by name — but it never raises that type. It always wraps it one level down:

```python
future.set_exception(exc.InvocationError(module=sender, exception=exception))
```

So even though the reconstructed `exception` genuinely is a `FocusError` instance, what the
awaiting caller actually receives is `InvocationError`, with the real exception stashed in
`.exception`. I checked whether this is just a theoretical concern: grepping every
`except exc.<Type>` in `pyobs/modules/` and `pyobs/robotic/`, **not one call site in the codebase
catches a specific leaf domain type around a proxy call** — they catch `exc.PyObsError` (broad),
`exc.RemoteError` (the wrapper's base class), or `exc.InvocationError` itself with a manual
`isinstance(e.exception, ...)` unwrap (`pyobs/robotic/storage/lco/task.py:202-203`, the *only*
place in the codebase that does this unwrap). Writing `except exc.FocusError:` around a proxy
call today would simply never fire, regardless of what the remote side actually raised. Given
goal 5 leans on being able to add many new specific types, fixing this is more load-bearing than
any single new type.

**Proposed fix**: raise the reconstructed exception directly, and attach remote-origin context to
the instance itself rather than nesting it in a wrapper:

```python
exception = exception_class(msg)          # the real reconstructed type, e.g. FocusError
exception.remote_module = sender          # or: exception.__cause__ = <local marker with sender/call id>
future.set_exception(exception)
```

`except exc.FocusError:` around a proxy call then just works, the way it already silently doesn't
today. The fallback for "the remote type couldn't be resolved at all" doesn't need to be
`InvocationError` either — checking how `InvocationError` gets consumed elsewhere (see §E) turns up
that nothing needs it to survive at all once this fix lands; the fallback becomes the
`UnclassifiedError` safety net from proposal §2 below (known type → raise it directly, unknown
type → raise something that says "I don't know what this was, here's the name and message I did
get"), and `InvocationError` itself gets retired.

**This is not a free change** — five call sites currently rely on the old behavior and would need
auditing: `pyobs/modules/focus/focusseries.py:167,194,203` and `pyobs/modules/module.py:238` all
write `except exc.RemoteError:` around a proxy call, but reading them, none actually mean
"specifically a transport failure" — `focusseries.py:167`'s comment-equivalent intent is "however
this call failed, treat it as my own `FocusError`," and `module.py:238`'s is "however this failed,
just skip this module." They only work today because *every* remote failure, transport or domain,
currently arrives as some `RemoteError` subclass (`InvocationError`). A fifth,
`pyobs/robotic/storage/lco/task.py:202-203`, explicitly unwraps `InvocationError.exception` — the
only place in the codebase that does — and needs the same treatment once that wrapper is gone.
Once domain exceptions stop being wrapped, all five need to widen to `except exc.PyObsError:` (or
the specific type each one is actually looking for) to preserve their actual intent — a small,
enumerable migration (5 sites, not a sweep), but a real one, not just a config flip.

### B. Collapse the two catch/log sites into one

Right now, exception handling for an RPC call is split across two catch blocks in two files
(`Module.execute()` and `RPC._on_jabber_rpc_method_call`), coordinated only by the side-channel
`PyObsError.logged` flag — the second site's own logging is inert today purely because the first
site already flipped that flag, which is a fragile way for two catch blocks to agree "only one of
us actually logs this." It also means the safety net from proposal §2 (wrap unknown exceptions
before they degrade on the wire) only helps the XMPP transport, since it lives in `rpc.py` —
`LocalComm.execute()` (`pyobs/comm/local/localcomm.py:50-55`) has no equivalent second catch site
at all, so a raw `ValueError` making it out of an interface method there gets no wrapping,
whereas over XMPP it would at least get named in the fault (if not always correctly reconstructed).

Given `Module.execute()` is already the one transport-agnostic chokepoint every path goes through
(XMPP, `LocalComm`, `MultiModule`), I'd move all of it there: classification (is this a
`PyObsError`? if not, wrap it in `UnclassifiedError` right here, once, for every transport), the
`_disable_exception_logging` opt-out check, and the actual `log.log(...)` call. `rpc.py`
then does no independent logging or wrapping at all — its `except Exception` block (which, after
this change, is really always `except exc.PyObsError`, since `execute()` never lets anything else
through) purely serializes and sends the fault. This removes an entire redundant catch/log site
architecturally, instead of relying on an instance flag to make it inert after the fact, and gives
`LocalComm` the same wrapping guarantee XMPP calls get, for free.

### C. Decouple severity escalation from construction-time metaclass magic — and retire the substitution entirely

Already flagged in the `register_exception` comparison above: `raise exc.FocusError("...")` can
silently hand back a `SevereError` instance instead, because the metaclass intercepts
*construction*, not raising or catching. `isinstance` checks anywhere between the `raise` and the
eventual catch site can't be trusted to reflect the type actually named in the source — the object
can already have mutated into something else before the `raise` keyword even runs.

Checking how `SevereError` is actually consumed changes the fix, though. Grepped the whole
codebase, `pyobs-core` and every sibling project: **nothing anywhere catches `exc.SevereError`
specifically** — the only production consumer of "this got severe" is the `callback` parameter of
`register_exception`, and the one callback anyone actually uses,
`_default_remote_error_callback` (`pyobs/modules/module.py:642-658`), already does the meaningful
part itself:
```python
log.critical(error)
await self.set_state(ModuleState.ERROR)
```
The module already has a real, working way to say "I'm broken because of repeated failures" —
transitioning to `ModuleState.ERROR`, which `Module.execute()` already special-cases (blocks
further calls, raises `exc.ModuleError`, which per Design Goal 1's rule always logs
unconditionally). The `SevereError` substitution on the *original* raise site is ceremony on top
of a callback that already does the real thing. So rather than "move the substitution to a better
place," the fix is to **drop the substitution entirely**:

1. Move counting out of the metaclass into the same `Module.execute()` catch-time chokepoint as
   classification/logging (§B) — `self._record_exception(e)` replaces `_store_exception`, but
   writes to per-instance state (`self._exception_log`, `self._remote_exception_log`) instead of
   the module-level globals, closing the cross-instance leakage bug from the `register_exception`
   comparison in the same change.
2. Check thresholds right after recording, in the same spot — if a handler's threshold is
   crossed, fire its `callback` exactly as today (`asyncio.create_task(handler.callback(e))`), no
   behavior change for module authors relying on the callback.
3. `execute()` always re-raises `e` unchanged, full stop — no substitution branch at all.
   `raise exc.FocusError(...)` always raises `FocusError`.
4. `register_exception` becomes an instance method (`self._register_exception(...)`, called from
   `__init__`), mirroring `_disable_exception_logging`'s exact shape — same convention, same
   place.
5. Remove the `_Meta` metaclass entirely. Constructing a `PyObsError` — even without raising it —
   becomes side-effect-free, ordinary Python again.
6. Retire `SevereError` as a class. Nothing constructs it anymore, and its removal also drops one
   of the three non-standard constructors flagged in §E, leaving only `InvocationError`/
   `ForbiddenError` to fix there.

Migration cost is small and fully enumerable: ten in-tree call sites
(`basecamera.py:113`, `flatfield/flatfield.py:93,97,101`, `focusseries.py:82,86`,
`pointing/_base.py:52,56`, `roof/basedome.py:24`, `basetelescope.py:252`) plus one external
(`pyobs-alpaca/pyobs_alpaca/focuser.py:37`) need the free-function-to-instance-method rename —
mechanical, one line each. `tests/utils/test_exceptions.py`'s three
`isinstance(exc_info.value, exc.SevereError)` assertions (lines 80, 123, 151) need rewriting to
assert the callback fired / state transitioned instead of asserting the raised type changed.

### D. Serialize by registry, not by name-lookup into one hardcoded module

`getattr(exc, exc_name, None)` (`rpc.py:272`) only ever finds classes that live in
`pyobs.utils.exceptions`. That's an implicit constraint nobody had to think about while the
hierarchy was small and centralized, but goal 5 argues for many new, specific types — and the
natural place for e.g. `WeatherDataError`/`FocusTimeoutError`/`MissingSensorError` is next to
`FocusModel`, or `ScriptError` next to the `pyobs.robotic.scripts` package, not in a growing,
unrelated `exceptions.py` god-file. Those two pulls are in direct tension under the current
serialization scheme: put a type where it domain-belongs and it silently stops surviving the wire.

**Concrete mechanism**: `__init_subclass__` on `PyobsError` itself, not a decorator — every
subclass registers automatically the moment its defining module is imported, with zero extra code
at the declaration site (goal 5's "cost of a new leaf class is low" applies to the registry too,
not just to minting the type):

```python
class PyobsError(Exception):
    _registry: dict[str, type["PyobsError"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        PyobsError._registry[f"{cls.__module__}.{cls.__qualname__}"] = cls

    def __init__(self, message: str | None = None, **context: Any) -> None:
        self.message = message
        self.logged = False
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)

    @classmethod
    def resolve(cls, qualified_name: str) -> type["PyobsError"] | None:
        return cls._registry.get(qualified_name)
```

This also finishes what §C already started: with `_Meta` gone and this hook doing the only
remaining "runs automatically on every subclass" job, there's no metaclass left anywhere in the
hierarchy — constructing *or subclassing* a `PyobsError` is fully ordinary Python.

Two design decisions worth making explicit, not leaving implicit the way `getattr`'s constraint
was:

- **Key by fully-qualified name (`module.QualName`), not bare `__name__`**, and change
  `fault_to_xml`/`xml_to_fault` (`rpc.py:93-121`) to serialize/parse that instead of the bare class
  name. Goal 5 means many new types across many files — `pyobs-sbig`, `pyobs-aravis`, and
  `pyobs-core` itself could all plausibly define something called `TimeoutError`-adjacent or
  `CalibrationError`-adjacent independently, and a bare-name registry would let the second
  definition silently clobber the first at import time, with whichever one loaded last winning
  reconstruction for both. This isn't a new security exposure — resolution is still a dict lookup
  against classes already chosen and already loaded, never a live import driven by wire content —
  it's purely a correctness fix for a many-files, many-authors world that a single centralized
  file with unique names never had to worry about.
- **The real question this raises**: if `WeatherDataError` moves to
  `pyobs/modules/focus/focusmodel.py`, does `PyobsError._registry` actually contain it in a
  process that never imported that module — say, a scheduler that only ever talks to a camera?
  No. `__init_subclass__` only fires when the defining module is imported, and nothing forces a
  scheduler to import every domain module in the fleet just in case. This looks like a real
  regression at first — but tracing through who's actually affected shows it isn't: the only
  callers who'd notice are ones who never imported `WeatherDataError` in the first place, which
  means they never wrote `except exc.WeatherDataError:` either (you can't reference a name you
  haven't imported) — they were always going to handle this generically, not distinguish it. For
  them, receiving `UnclassifiedError(original_type="pyobs.modules.focus.focusmodel.WeatherDataError",
  ...)` instead of the real type is a graceful, inspectable fallback (the qualified name string
  survives even when the class doesn't), not a broken one — and it's already strictly better than
  today's behavior, where an unresolvable name is discarded entirely in favor of a bare
  `RemoteError`. The only callers who *do* care already import the type to write their `except`
  clause, and that import is exactly what makes `__init_subclass__` register it in their process
  before they'd ever need to resolve it. The mechanism self-selects correctly: whoever needs the
  precise type already has it loaded; whoever doesn't gets a reasonable fallback instead of being
  unable to construct anything at all.

### E. Standardize the constructor contract — and retire `InvocationError` entirely

Already-noted bug: the fault-reconstruction code assumes every `RemoteError` subclass accepts
`(message=.., module=..)` as keywords, which `InvocationError` and `ForbiddenError` don't — a
latent `TypeError`-inside-the-fault-handler waiting for the wrong name to show up
(`rpc.py:277-280`).

Checking whether §A's redesign actually closes this on its own (it doesn't, quite) turned up
something sharper: under §A, `_on_jabber_rpc_method_fault` never constructs `InvocationError` for
a resolved type anymore — it raises the real type directly, or `UnclassifiedError` for the
fallback. Grepping every use of `InvocationError` in the codebase confirms it has no remaining job:
the only construction site was the one §A replaces (`rpc.py:283`), and its only functional
consumer was the module-extraction check in `handle_exception` (`exceptions.py:189`), itself part
of the severity machinery §C already reworks to be catch-time and instance-scoped. **Retire the
class entirely**, the same call as `SevereError` in §C — one fewer non-standard constructor to
carry forward, and one fewer wrapper layer for a caller to think about.

That leaves exactly one call site depending on the old behavior that §A's audit didn't originally
catch: `pyobs/robotic/storage/lco/task.py:202-203`,
`except exc.InvocationError as e: if isinstance(e.exception, exc.AbortedError): ...` — this needs
the same treatment as the four `except exc.RemoteError:` sites already flagged in §A/proposal §2:
widen to catch the real type directly (`except exc.AbortedError:`) instead of unwrapping a type
that no longer gets constructed.

With `InvocationError` gone and `SevereError` gone (§C), the constructor-uniformity problem shrinks
to `RemoteError`/`RemoteTimeoutError` (currently `__init__(self, module: str, message: str | None
= None)`, module positional-first) and `ForbiddenError` (`__init__(self, sender: str, method:
str)`, never actually reached via the generic reconstruction path since forbidden calls take a
separate XEP-0009 IQ-error condition, but still worth fixing for consistency). Standardize on:
`PyObsError.__init__(self, message: str | None = None, **context: Any)`, storing every keyword
generically (`for key, value in context.items(): setattr(self, key, value)`) so existing attribute
reads (`exception.module`, a future `exception.sensor`, etc.) keep working without each subclass
needing its own `__init__` override at all. The RPC layer can then reconstruct *any* registered
subclass the same way (`cls(msg, **context)`), and adding a new structured field to a new
exception type never requires touching `rpc.py` again. Migration is mechanical and small: `10`
direct-construction call sites need their positional argument order updated to message-first —
`xmppcomm.py:506,507,509` (`RemoteError`/`RemoteTimeoutError`), `rpc.py:298-303` (six `RemoteError`
constructions, one per XEP-0009 error condition), and `module.py:428` (`ForbiddenError`).

### F. Add a correlation id instead of relying on suppressing one side's log

Goal 1 ("log once, where a human can act on it") is currently pursued entirely by *removing* a log
line on one side. An alternative that loses no information: tag the RPC call with a correlation id
(XEP-0009 already assigns `iq["id"]` per call, currently used only as the `Future` dict key,
`rpc.py:163-164`) and include it in both the origin-side ERROR log (with full traceback) and the
caller-side exception/log line. An operator debugging a caller-side `FocusError` can then jump
straight to the matching detailed log on the module that actually raised it, by id — genuinely
better for debugging than either double-logging or single-suppressing, since right now neither
side's log line points at the other. This is additive and doesn't conflict with
`_disable_exception_logging` — it's a good companion to it, since suppressing the *local* log
entirely relies more heavily on the origin side's log (with the correlation id) being the only
record that exists.

### G. Make the domain/transport split an explicit, named axis

The `RemoteError` subtree is implicitly "something about the call itself failed" (timeout,
forbidden, connection); everything else is implicitly "the operation you asked for failed for a
domain reason." That split already exists in practice but isn't documented as a deliberate
design axis anywhere, which is partly *why* call sites ended up catching `RemoteError` to mean
"anything failed" (§A) — the two concepts blurred together once domain exceptions started
arriving wrapped in a `RemoteError` subclass. Worth stating explicitly once fix A lands: transport
failures (`RemoteError`, `RemoteTimeoutError`, `ForbiddenError`) don't need to multiply into many
subtypes the way goal 5 argues domain exceptions should — "the call failed to even reach/return
from the remote module" doesn't usually benefit from finer granularity the way "the remote
operation failed for reason X vs. reason Y" does.

### Sequencing relative to the rest of this doc

All seven items (A-G) end up in the rollout below — none are left as someday-maybe, once each one
turned out to be smaller or more load-bearing than "just a nice-to-have" on closer inspection: A
because without it, goal 5's whole premise (callers reacting to specific types) doesn't hold; B
because it removes the fragile `.logged`-flag coordination this doc otherwise just documents and
works around; C because checking how `SevereError` is actually consumed (nothing does, directly)
turned it from "worth doing eventually" into a small, enumerable fix riding along with B's same
catch-time chokepoint change; D because §4's new leaf types need somewhere to physically live
other than a growing `exceptions.py`, and that's only possible once the registry exists; E because
checking whether A's fix alone closes the constructor-signature bug turned up that `InvocationError`
has no remaining job at all once A lands, so retiring it and standardizing the rest is a small,
concrete extension of the same change rather than separate follow-on work; F is small and purely
additive, and naturally rides along once A/C are already touching the same fault-path code; G is a
documentation/naming outcome of A, not separate implementation work. A/C/D/E/rpc.py migrations land
together as one PR (rollout step 2) since they touch the same two files and are tightly coupled;
B/F/G/the leaf-type sweep/docstring sweep can each go out on their own schedule after that.

## Design goals

1. An exception should be logged once, at the place a human can actually act on it — not
   re-logged at every hop it passes through on the way back to a caller. Concretely: creating a
   `PyObsError` subclass at all is already a deliberate act (goal 5 — module authors mint specific
   types on purpose, they don't reach for one by accident), so **every domain `PyObsError` logs as
   one quiet INFO line, without a traceback, automatically — no per-type opt-in required.** A
   module doesn't need to decide type-by-type whether something is "worth" a line; the only
   decision it makes is the rare opt-*out* (`_disable_exception_logging`) for a type that fires
   often enough that even a quiet line is too much (see below). Anything that *isn't* a
   `PyObsError` (a raw builtin, a third-party/vendor SDK exception) is, by definition, not part of
   that deliberate contract — it's unanticipated, which means the fix belongs in the code/hardware
   that produced it. Those always log loudly (ERROR, with a traceback), locally, where they
   happened, with no suppression possible; if a condition like that turns out to recur often
   enough that callers legitimately need to distinguish and react to it, that's the signal to
   promote it into a proper `PyObsError` subclass — not to keep passing it through as a string
   forever. A single occurrence of a domain exception never escalates to loud on its own — a
   *pattern* of them does, via the severity-escalation mechanism (Assessment §C) transitioning the
   module into `ModuleState.ERROR`, which raises the always-loud `ModuleError` for every
   subsequent call. That's the path to "this needs a human now"; an individual raise never needs
   to guess at its own severity.
2. Anything that crosses an RPC boundary should arrive as a meaningful, typed error on the other
   side, catchable directly as that type. A caller writing `except exc.FocusError:` around a
   proxy call should actually catch it — today it never does (see "Assessment" §A below: every
   remote domain exception arrives wrapped in `InvocationError` instead), which undercuts goal 5
   as much as the wire silently degrading to `RemoteError` does.
3. A module should be able to declare "these exception types (and their subclasses) fire often
   enough that even the default quiet INFO line is too much — suppress it entirely," without
   losing the ability to still see genuinely unexpected failures at ERROR with a traceback (goal 1
   already guarantees the latter is never suppressible).
4. What's documented (`Raises:` docstrings), what's declared (`@raises(...)`), and what's
   actually raised should not be free to drift independently.
5. Prefer adding a new, specific exception type over reusing a broad one or falling back to a
   generic builtin. We are not restricted to the current list in `exceptions.py` — a caller can
   only `except` what it can distinguish, and collapsing several distinguishable failure modes
   into one coarse type (or a bare `ValueError`) throws away exactly the information that would
   let a caller react differently to each. The cost of a new leaf class is low (one line); the
   cost of under-differentiating is that nobody can ever react to the specific failure without a
   later breaking change to split it out. Default to finer-grained unless there's a concrete
   reason a single type is enough (e.g. genuinely only one thing can go wrong at that call site).

## Proposed design

### 1. `_disable_exception_logging` on `Module`

Add an instance-level, constructor-callable method mirroring the shape of
`exc.register_exception(...)`'s call-in-`__init__` convention:

```python
class Module:
    def __init__(self, ...):
        ...
        self._disabled_exception_logging: tuple[type[exc.PyObsError], ...] = ()

    _UNSUPPRESSIBLE = (exc.ModuleError, exc.SevereError, exc.UnclassifiedError)

    def _disable_exception_logging(self, *exceptions: type[exc.PyObsError]) -> None:
        for e in exceptions:
            if issubclass(e, self._UNSUPPRESSIBLE):
                raise ValueError(f"{e.__name__} cannot be silenced — it always needs local attention.")
        self._disabled_exception_logging = self._disabled_exception_logging + exceptions
```

The type restriction isn't incidental — it follows directly from the same rule that decides which
exceptions are worth converting into a `PyObsError` in the first place: a `PyObsError` subclass is
the deliberate, caller-facing API of a failure mode, and the module author who raised it gets to
decide whether *that* is also worth a local line. `ModuleError`, `SevereError`, and
`UnclassifiedError` aren't part of that deliberate contract even though they're technically
`PyObsError` — they each mean, in their own way, "something happened here that wasn't anticipated
and needs a human's attention at the source," the same category raw builtin exceptions fall into.
`ModuleError` says the module itself is broken; `SevereError` says a normally-fine failure mode has
started repeating past a threshold; `UnclassifiedError` (proposal §2) is the wrapper for exactly
the exceptions this rule says should never have reached the RPC boundary unconverted in the first
place. Letting a module silence any of the three would undermine the reason they exist — they're
supposed to be the cases nobody gets to opt out of hearing about.

`Module.execute()`'s catch block consults the list with `isinstance`, so declaring a base class
covers its subclasses for free, and — per the reworked Design Goal 1 — INFO-without-traceback is
now the automatic default for any domain `PyObsError`, not something a method has to opt into:

```python
except Exception as e:
    if isinstance(e, exc.ModuleError) or isinstance(e, exc.UnclassifiedError):
        e.log(log, "ERROR", f"Exception was raised in call to {method}: {e}", exc_info=True)
    elif isinstance(e, exc.PyObsError):
        if not isinstance(e, self._disabled_exception_logging):
            e.log(log, "INFO", f"Exception was raised in call to {method}: {e}", exc_info=False)
        # else: caller already has it; nothing to log locally
    raise e
```

`@raises(...)` (`pyobs/modules/module.py:87-100`) is retired as a *logging* mechanism — its job
(deciding which types get a quiet line) is now automatic for every domain exception, not
per-method-declared. It can still survive purely as documentation metadata feeding §7's
docstring-cross-check idea, but it no longer affects `execute()`'s log level at all.

This also settles the `CommLoggingHandler` publish question by construction, not by choice: the
skipped-log branch above never calls `e.log(...)`, so no `LogRecord` is ever created — there's
nothing for `CommLoggingHandler.emit()` (`pyobs/comm/commlogging.py:27-43`) to pick up, so
`log_message()` never queues, and `send_event()`'s `xep_0163.publish()`
(`pyobs/comm/xmpp/xmppcomm.py:665-687`) never fires. "Skip the local write but still publish"
isn't a flag away; it would need a second, deliberate path (calling `comm.send_event(...)`
directly, bypassing `logging` entirely). There's no reason to build that: "don't call `e.log(...)`"
and "don't queue for `comm.log_message()`" are the same thing once traced through — one *is* the
other under the standard `logging` dispatch model, so the suppression point already gates the
publish itself, not just local severity.

That's also the accurate reason `_disable_exception_logging` matters, corrected from an earlier
draft of this section: it isn't guarding against some *new* publish-side cost this design
introduces (per the "Where local logging happens" discussion in Current State, that cost already
exists today, unconditionally, for every currently-logged domain exception — `CommLoggingHandler`
gates purely on level, and `ERROR` already clears the `INFO` threshold just as well as the new
default does). It's the *first* mechanism able to reduce a pre-existing cost that #446 never
touched before: a type firing repeatedly inside a tight internal retry loop already pays this
publish cost today (formatted, queued, and pushed to the XMPP server as a stanza every single
time, regardless of whether anyone declared interest via `register_event(..., handler=...)`, per
Current State) — `_disable_exception_logging` is how a module finally gets to say "stop paying
that cost for this specific type," not a defense against something this design would otherwise
make worse. One scope caveat regardless: this only touches the one log call inside `execute()`'s
catch block — any other `log.info`/`log.warning` a driver makes on its own (e.g. inside a retry
loop) is untouched either way; `_disable_exception_logging` was never a total-silence guarantee,
just a fix for this one redundant site.

### 2. Raise the real reconstructed type directly; `UnclassifiedError` is the only fallback

Per Assessment §A, `_on_jabber_rpc_method_fault` should stop wrapping every successfully
reconstructed exception in `InvocationError`:

```python
exception_class = exc.PyobsError.resolve(exc_name)  # see Assessment §D — __init_subclass__ registry
if exception_class is not None:
    exception = exception_class(msg, **context)   # real type, e.g. FocusError — raised as-is
    exception.remote_module = sender
else:
    exception = exc.UnclassifiedError(msg, original_type=exc_name, module=sender)
future.set_exception(exception)
```

(`exc_name` here is the fully-qualified `module.QualName` string `fault_to_xml` now serializes,
per §5.)

`UnclassifiedError` picks up the one remaining job the old `InvocationError` used to do for every
case — wrapping the unresolved fallback — which means `InvocationError` itself has no job left at
all. Retire it entirely (Assessment §E): that also removes the constructor-contract bug this
section's earlier draft flagged, since today's reconstruction assumed every `RemoteError`
subclass accepts `(message=.., module=..)`, which `InvocationError`/`ForbiddenError` don't, a
latent `TypeError`-inside-the-fault-handler (`rpc.py:277-280`) — with `InvocationError` gone, that
particular non-standard constructor no longer needs handling here at all (the residual
`RemoteError`/`RemoteTimeoutError`/`ForbiddenError` cleanup is §E's, not this section's).

**Required migration, not optional cleanup**: `pyobs/modules/focus/focusseries.py:167,194,203`
and `pyobs/modules/module.py:238` currently write `except exc.RemoteError:` specifically to catch
*any* failure from a proxy call (transport or domain) — they only work today because domain
exceptions arrive wrapped in an `InvocationError` (a `RemoteError` subclass). Once fixed, these
need to widen to `except exc.PyObsError:` (their actual intent, reading each one) or they'll stop
catching domain failures from the remote side entirely. A fifth site needs the same treatment for
the same reason, once `InvocationError` no longer exists: `pyobs/robotic/storage/lco/task.py:
202-203`'s `except exc.InvocationError as e: if isinstance(e.exception, exc.AbortedError):`
should become a direct `except exc.AbortedError:`. All five have to land in the same PR as the
unwrap fix, not after it.

### 3. Collapse the two catch/log sites into `Module.execute()`

Per Assessment §B: move classification (wrap non-`PyObsError` into `UnclassifiedError`), the
`_disable_exception_logging` opt-out check, and the actual `log.log(...)` call entirely
into `Module.execute()`. `RPC._on_jabber_rpc_method_call`'s catch block stops doing any logging or
wrapping of its own — by the time an exception reaches it, `execute()` has already classified and
logged it, so `rpc.py` purely serializes (`fault_to_xml`) and sends. This also closes the gap where
`LocalComm.execute()` (`pyobs/comm/local/localcomm.py:50-55`) currently gets none of the
XMPP-transport's (partial) safety net — after this change every transport gets the same
classification for free, since they all go through `execute()`.

### 4. Require RPC-reachable exceptions to be `PyObsError` subclasses defined in `exceptions.py`

Given the wire-serialization mechanics, this isn't a style preference — it's the difference
between a caller being able to `except exc.FocusError` meaningfully or not. Concrete fixes:

Per goal 5, default to a new, specific leaf class per distinguishable failure mode rather than
reusing the nearest existing coarse type — but "distinguishable" needs a concrete test, not just
"has a different message." A new leaf earns its existence if it passes at least one of: (1) some
caller would plausibly branch on it specifically (retry vs. give up vs. "this isn't even a failure,
just defer it"), or (2) the type name adds diagnostic value over the message string for someone
scanning logs, without needing to read the full text. Splitting further than that adds hierarchy
depth (and registry/reconstruction surface, per Assessment §D) that nothing ever uses.

- `CameraException` → both of its current call sites ("camera not idle" for a new exposure, and
  for a new sequence) mean *the caller sent a request the camera can't service right now*, which
  is a different condition from "I tried to grab and it failed" (`GrabImageError`'s actual
  meaning) — passes test 1 outright ("back off and retry" vs. "something actually broke"). The
  interface audit turned up the identical condition in a completely different device family:
  `AcquireLockFailed` (`pyobs/utils/threads/lockwithabort.py:10,37`), a plain `Exception` (not even
  `PyObsError`) that leaks out of `move_radec`/`move_altaz`/`set_focus`/`park`/`stop_motion`/roof
  `init`/`park` whenever `LockWithAbort` can't acquire its lock — i.e. the device is already
  busy handling another motion request. That's the same failure mode as `CameraException`'s, just
  on telescope/roof/focuser instead of camera. Rather than a camera-specific type, generalize to
  one reusable `DeviceBusyError(PyObsError)` in `exceptions.py` covering both — "this device is
  already busy, back off and retry" doesn't depend on which kind of device it is, and a single type
  lets a caller write one retry-loop `except` clause that works across camera, telescope, roof, and
  focuser modules alike. Deliberately *not* split further into e.g. a busy-for-exposure vs.
  busy-for-sequence vs. busy-for-lock variant — no caller would react differently to any of those.
- `FocusModel.set_optimal_focus`'s three failure modes map onto a real retry-vs-not axis: invalid
  weather reading and a timed-out temperature fetch are both plausibly transient (worth retrying),
  while a misconfigured sensor name in the response is a config bug that retrying never fixes.
  Three leaves under `FocusError`: `WeatherDataError(FocusError)` (line 278),
  `FocusTimeoutError(FocusError)` (line 296), `MissingSensorError(FocusError)` (line 307).
- `BaseTelescope`'s `ValueError` sites split the same way, and arguably more usefully:
  `AltitudeLimitError(MotionError)` isn't really a *failure* from a scheduler's point of view — a
  target below the altitude limit is an expected, deferrable condition, not something to alert on
  — while `BodyResolutionError(MotionError)` is transient/network-dependent (a Horizons query),
  and `MissingObserverError(MotionError)`/`InvalidOrbitalElementsError(MotionError)` are config/input
  bugs that should alert loudly and never auto-retry. Four genuinely different reactions, four
  types. The capability-check `NotImplementedError` sites are a separate, cross-cutting condition
  ("this module doesn't support this operation at all," not "this specific move failed") that
  shows up wherever a module optionally implements a mixin interface — a single reusable
  `NotSupportedError(PyObsError)` in `exceptions.py`, not a telescope-specific type, so other
  optional-capability modules can raise the same thing instead of a bare `NotImplementedError`.
- `ScriptRunner`/`Script` subclasses' `ValueError`s → a flat `ScriptError(PyObsError)` base earns
  its place (fixes real unwrapped `ValueError`s degrading on the wire today, e.g.
  `callmodule.py`'s), but per the closer look above, `transitimaging.py:64,86`'s "no merit found"
  isn't actually a domain error at all — it's a reachability gap in a caller-contract check, not a
  failure mode this hierarchy needs to represent, so it doesn't need any exception type, coarse or
  fine (fix: trust `can_run()`'s existing gate; at most keep a minimal assertion, not a rich type).
  `autofocus.py:60`'s "no target given" *is* a genuine runtime failure — worth wrapping as
  `ScriptError` — but the better fix is closing the same gap `transitimaging.py` already closed:
  extend `AutoFocusScript.can_run()` to check for a target too, so the scheduler finds out via the
  same non-exception path instead of only discovering it after `run()` has already started.
  Whatever residual cases remain after that (network/proxy failures inside a script's `run()`, say)
  wrap with the flat `ScriptError(PyObsError)` at the `ScriptRunner.run()` boundary, following the
  `BaseCamera.__expose()` pattern — no need to mint per-script leaves until a caller actually wants
  to distinguish them.
- `BaseVideo.grab_data()`'s "no image" condition (`pyobs/modules/camera/basevideo.py:476`,
  `raise ValueError("Could not take image.")`) → switch to `exc.GrabImageError`, matching
  `BaseCamera`'s equivalent path (`basecamera.py:266`) exactly. Confirmed via `pyobs-aravis`/
  `-v4l` (both build on `BaseVideo`, not `BaseCamera`) in the driver survey above — this is a
  `pyobs-core` fix, not a driver one, and belongs in this same sweep.
- `BaseSpectrograph.grab_data()` (`pyobs/modules/camera/basespectrograph.py:164-186`) has the
  identical gap, confirmed by the interface audit: it raises bare `ValueError` three times
  (lines 176, 182, 185) and never `exc.GrabImageError`, despite `IData.grab_data` documenting
  exactly that type. Same fix, same sweep.
- `InitError`/`ParkError` — confirmed by the interface audit to have **zero raise sites anywhere**
  in `pyobs/modules/`, despite `IMotion.init`/`park` documenting them. Unlike the `pyobs-brot`
  finding (a different repository this PR can't touch), the in-tree reference/dummy
  implementations *can* be fixed here: `telescope/_dummytelescopebase.py`, `roof/dummyroof.py`,
  and `flatfield/flatfield.py`'s `IMotion` methods should catch `AcquireLockFailed` (see the
  `DeviceBusyError` fix above — a lock-acquisition failure isn't the same condition as "the device
  failed to initialize/park," so it needs its own translation, not folding into `DeviceBusyError`)
  and any other failure reaching `init()`/`park()`, and raise `exc.InitError`/`exc.ParkError`
  respectively, matching the interface contract these two methods have documented all along.

Note: §2 above already gives every new type here a working fallback — anything not yet migrated
to a specific type still arrives as `UnclassifiedError` rather than degrading to an untyped
`RemoteError`, so this sweep can genuinely happen incrementally, type by type, without a
transitional period where unmigrated call sites are worse off than today.

### 5. Serialize by registry, and move domain-specific exceptions to where they belong

Per Assessment §D: `getattr(exc, exc_name, None)` (`rpc.py:272`) only resolves classes that live in
`pyobs.utils.exceptions`. That constraint was invisible while the hierarchy was small and
centralized, but §4 just proposed a dozen-plus new leaf types, several of which belong physically
near the code that raises them, not bolted onto a growing, unrelated `exceptions.py` — e.g.
`WeatherDataError`/`FocusTimeoutError`/`MissingSensorError` next to `FocusModel`
(`pyobs/modules/focus/focusmodel.py`), the deferred `ScriptError` next to the
`pyobs.robotic.scripts` package. Doing that under the current serialization scheme means those
types silently stop surviving the wire the moment they move.

The concrete mechanism — `__init_subclass__` on `PyobsError`, keyed by fully-qualified name, plus
the resolution of the cross-process-import question — is spelled out in full in Assessment §D
rather than duplicated here. Two changes it requires in `rpc.py`: `fault_to_xml`
(`rpc.py:93-106`) serializes `f"{type(exception).__module__}.{type(exception).__qualname__}"`
instead of the bare `type(exception).__name__`, and `_on_jabber_rpc_method_fault`
(`rpc.py:259-283`) calls `exc.PyobsError.resolve(exc_name)` instead of `getattr(exc, exc_name,
None)` — both already reflected in proposal §2's code sketch above.

With the registry in place, physically relocate the domain-specific types from §4 to where they
belong as part of the same sweep: `WeatherDataError`/`FocusTimeoutError`/`MissingSensorError` into
`pyobs/modules/focus/focusmodel.py` (or a small `pyobs/modules/focus/exceptions.py` if more than
one focus-adjacent file ends up needing them); `MissingObserverError`/`AltitudeLimitError`/
`InvalidOrbitalElementsError`/`BodyResolutionError` into `pyobs/modules/telescope/basetelescope.py`
or an equivalent telescope-local module; `ScriptError` (and any leaves minted later) into
`pyobs/robotic/scripts/__init__.py` or a dedicated exceptions module in that package. Cross-cutting
types that aren't tied to one domain file — `DeviceBusyError`, `NotSupportedError`,
`UnclassifiedError` — stay in `pyobs.utils.exceptions` alongside the existing hierarchy, since
they're infrastructure, not a specific module's concern.

### 6. Document (and fix) the `AbortedError` contract on abortable hooks

Per the driver survey above: `BaseCamera._expose()`'s docstring never mentions `AbortedError`,
and two independent driver projects both guessed `InterruptedError` instead — this isn't a
one-off mistake, it's a missing contract. Add `Raises: AbortedError: If the operation was
cancelled via abort_event.` (or equivalent) to `_expose()`'s docstring and any other
`abort_event`/`IAbortable`-adjacent hook signature in `pyobs-core`, and fix the three known
call sites this PR can reach: `pyobs-sbig/src/pyobs_sbig/sbigcamera.py:162`,
`sbigfiltercamera.py:168`, `pyobs-fli/pyobs_fli/flicamera.py:169` — each a one-line change
(`InterruptedError(...)` → `exc.AbortedError()`), but in a different repository, so it's a
companion PR alongside the core docstring fix, not something this repo's PR can do alone.

### 7. Keep documentation honest

The full interface audit (see "Confirmed by a full interface docstring audit" above) turned this
from "fix two known typos" into a real sweep: 16 of 27 documented interfaces have at least one
confirmed mismatch. The full per-interface findings, so whoever does this step doesn't have to
re-derive them:

| Interface (method) | Documents | Actually happens | Verdict | Fix |
|---|---|---|---|---|
| `IMotion.init` | `InitError` | Never raised anywhere; `AcquireLockFailed` (non-`PyobsError`) leaks instead | MISMATCH | Behavior (§4/§5) |
| `IMotion.park` | `ParkError` | Never raised anywhere; `AcquireLockFailed` leaks | MISMATCH | Behavior (§4/§5) |
| `IFocuser.set_focus` | `MoveError`, `InterruptedError` | `ValueError` (undocumented) + `InterruptedError` (matches) | PARTIAL | Doc: add `ValueError` |
| `IFocuser.set_focus_offset` | `ValueError`, `MoveError` | `_DummyTelescopeBase` unconditionally raises `NotImplementedError` | MISMATCH | Behavior: use `NotSupportedError` |
| `IAutoFocus.auto_focus` | `ValueError` | `FocusError`/`AbortedError` (per its own `@raises`) | MISMATCH | Doc only |
| `IAcquisition.acquire_target` | `ValueError` | `AbortedError`/`AcquisitionError`/`GeneralError` (per its own `@raises`) | MISMATCH | Doc only |
| `IData.grab_data` | `GrabImageError` | `BaseCamera`: `CameraException`(non-`PyobsError`)+`GrabImageError`+`ValueError`; `BaseSpectrograph`: `ValueError` only; `BaseVideo`: `ValueError` only; `PipelineCamera`: `GrabImageError`+`ValueError` | MISMATCH (3 of 4 implementers wrong) | Behavior (§4) |
| `IDataSequence.grab_sequence` | `GrabImageError` | `ValueError`/`CameraException`; `GrabImageError` never raised here | MISMATCH | Behavior (§4) |
| `IDataSequence.abort_sequence` | (none) | No raise | MATCH | — |
| `IExposureTime.set_exposure_time` | `ValueError` | Mostly no-throw; `ScienceFrameGuiding` unconditionally raises `NotImplementedError` | MISMATCH (`ScienceFrameGuiding` only) | Behavior: use `NotSupportedError` |
| `IFilters.set_filter` | `ValueError`, `MoveError` | `_DummyTelescopeBase`: `ValueError` matches; `MoveError` unused; `FlatField`'s own docstring has a copy-paste bug ("If binning could not be set") | PARTIAL | Doc: fix `FlatField`'s docstring |
| `IBinning`/`IGain`/`IImageFormat`/`IWindow`/`ICooling` (setters) | `ValueError` | No validation in any in-repo implementer — aspirational, unexercised | MATCH (weakly, unverifiable in this repo) | — |
| `IConfig.get_config_value`/`set_config_value` | `ValueError` | `ValueError`, consistently | MATCH (clean) | — |
| `IMode` (group-set method) | `ValueError`, `MoveError` | `ValueError` matches; `MoveError` unused | MATCH(`ValueError`)/unused(`MoveError`) | — |
| `ITrackingMode` (set method) | `MoveError`, `ValueError` | `ValueError` matches; `MoveError` unused | MATCH(`ValueError`)/unused(`MoveError`) | — |
| `ITrackingRate.set_tracking_rate` | `MoveError` | Exactly one raise site in the whole codebase (`basetelescope.py:588`), inside a background task, not synchronously RPC-reachable | MISMATCH (systemic) | Behavior (§4) |
| `IPointingRaDec.move_radec` | `MoveError` | Undocumented `ValueError` (no observer / altitude limit) + `NotImplementedError` + `AcquireLockFailed` | MISMATCH | Behavior (§4) then doc |
| `IPointingAltAz.move_altaz` | `MoveError` | Same as `move_radec` | MISMATCH | Behavior (§4) then doc |
| `IPointingBody.track_body` | `MoveError`, `ValueError` | `ValueError` (body resolution) matches; propagates `move_radec`'s undocumented exceptions | MATCH (primary) / gap (propagated) | Doc: note propagation |
| `IPointingOrbitalElements.track_orbital_elements` | `MoveError`, `ValueError` | `ValueError` (orbital elements) matches; propagates `move_radec`'s issues | MATCH (primary) / gap (propagated) | Doc: note propagation |
| `IPointingHeliocentricPolar` | `MoveError` only | Propagates `move_radec`'s undocumented `ValueError`/`AcquireLockFailed` | MISMATCH | Doc: note propagation, once `move_radec` is fixed |
| `IPointingHeliographicStonyhurst` | `MoveError` only | Same | MISMATCH | Same |
| `IPointingHelioprojective` | `MoveError` only | Same | MISMATCH | Same |
| `IOffsetsAltAz` (offset-set method) | `MoveError` | Unused (no raise in any dummy implementer) | MATCH (weakly) | — |
| `IOffsetsRaDec` (offset-set method) | `MoveError` | Unused | MATCH (weakly) | — |
| `IStructuredConfig.get/set` | `ValueError` | No implementers anywhere in this repo | Unverifiable | Doc-gap only |
| `IFocusModel.set_optimal_focus` | (none) | `ValueError` (three failure modes) | MISMATCH (known) | Both (§4 then doc) |
| `IFlatField.flat_field` | (none) | `ValueError("Already running.")` | MISMATCH | Doc: add clause |
| `IRunnable.run` | (none) | `ValueError("Already running.")` (`FlatFieldScheduler`, `flatfield/pointing.py`); arbitrary caller-defined exceptions propagate unwrapped via `ScriptRunner` | MISMATCH (moderate–significant) | Doc + §4's `ScriptError` |
| `IWeather.get_sensor_value` | (none) | `ValueError` (`weather.py`, `mockweather.py`) | MISMATCH | Doc: add clause |
| `IAbortable.abort` | (none) | No raise, across all 11 implementers checked | MATCH (no clause needed) | — |
| `ICalibrate`, `ISyncTarget`, `IMultiFiber.set_fiber`, `IPointingSeries`, `IRotation.set_rotation`, `IScriptRunner.run_script` | (none) | Zero concrete implementers anywhere in this repo | Unverifiable | Doc-gap only |
| `IImageType.set_image_type` | (none) | No raise | MATCH | — |
| `IModule.reset_error`/`get_permitted_methods` | (none) | No raise | MATCH (trivial) | — |
| `IStartStop.start`/`stop` | (none) | No raise, across every implementer checked | MATCH | — |

Grouped by what actually needs to change:

- **Docs need fixing to match already-correct behavior**: `IAutoFocus`, `IAcquisition` (as above),
  `IFocuser.set_focus` (add `ValueError`), `IFilters` (fix `FlatField`'s copy-paste bug),
  `IPointingBody`/`IPointingOrbitalElements` (note propagation from `move_radec`/`move_altaz`).
- **Behavior needs fixing to match already-correct docs** (pointers back to §4/§5, not new work):
  `IData.grab_data`, `IDataSequence.grab_sequence`, `IMotion.init`/`park`,
  `IPointingRaDec`/`IPointingAltAz`/`ITrackingRate`'s `MoveError`.
- **Both, together**: `IFocusModel` (add clause once `WeatherDataError`/etc. land),
  `IFocuser.set_focus_offset`/`IExposureTime.set_exposure_time` on `ScienceFrameGuiding` (raise
  `NotSupportedError` once it exists, then document it), `IFlatField`, `IRunnable`, `IWeather` (add
  a clause for the `ValueError` each already raises).
- **Doc-gap-only, no implementation to check yet**: `ICalibrate`, `ISyncTarget`,
  `IMultiFiber.set_fiber`, `IPointingSeries`, `IRotation`, `IScriptRunner.run_script`,
  `IStructuredConfig`. Add `Raises:`
  clauses consistent with whatever convention the rest of the sweep settles on (custom type vs.
  `ValueError` for bad input), so a future implementer — in this repo or a driver project — has a
  contract to follow instead of guessing, the same guess that produced the
  `InterruptedError`/`AcquireLockFailed` mismatches found elsewhere in this doc.
- Longer-term, low-priority idea: a lint/test that cross-checks `@raises(...)`/
  `_disable_exception_logging(...)` arguments against the types actually referenced in a method's
  docstring, so the two no longer drift independently. Not required for the initial rollout.

### 8. Standardize the `PyobsError` constructor contract

Per Assessment §E, once `InvocationError`/`SevereError` are retired (§2, §3), the remaining
non-uniform constructors are `RemoteError`/`RemoteTimeoutError` (`__init__(self, module: str,
message: str | None = None)`, module positional-first) and `ForbiddenError` (`__init__(self,
sender: str, method: str)`). Standardize the base class itself — shown here already renamed, since
this lands in the same PR as §11's rename:

```python
class PyobsError(Exception):
    def __init__(self, message: str | None = None, **context: Any):
        self.message = message
        self.logged = False
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
```

Every subclass drops its own `__init__` override — `module=`, `sensor=`, `original_type=`, and any
future structured field a new leaf type wants to carry all arrive as ordinary keyword arguments and
become ordinary attributes, generically, with no per-subclass reconstruction code needed in
`rpc.py` ever again (`cls(msg, **context)` works uniformly for anything the registry, §5, resolves).
Ten direct-construction call sites need their argument order updated to message-first:
`xmppcomm.py:506,507,509` (`RemoteError`/`RemoteTimeoutError`, `client` → `module=client`),
`rpc.py:298-303` (six `RemoteError` constructions, one per XEP-0009 error condition, `sender` →
`module=sender`), and `module.py:428` (`ForbiddenError`, computing the same message it does today
but passing `sender=`/`method=` as keywords instead of positionals).

### 9. Add a correlation id for cross-log debugging

Per Assessment §F: tag each RPC call with a correlation id — XEP-0009 already assigns `iq["id"]`
per call (`rpc.py:163-164`, currently used only as the `Future` dict key) — and include it in both
the origin-side ERROR log (with full traceback) and whatever reaches the caller (an attribute on
the exception itself, e.g. `exception.call_id`, following §8's generic-context mechanism — no
bespoke plumbing needed once §8 lands). An operator debugging a caller-side `FocusError` can then
jump straight to the matching detailed log on the module that actually raised it, by id. Purely
additive, no migration required, and a natural companion to `_disable_exception_logging`: the more
willing a module is to stay silent locally, the more useful a correlation id becomes as the way an
operator reconnects a caller-side symptom to its origin-side detail.

### 10. Document the domain/transport split as a deliberate axis

Per Assessment §G: once proposal §2 lands (callers actually receive real domain types directly,
not everything wrapped in `RemoteError`'s subtree), add a module-level comment to
`pyobs/utils/exceptions.py` stating the two-tier design explicitly: `RemoteError` and its subtree
(`RemoteTimeoutError`, `ForbiddenError`) mean "the call itself didn't reach/return" — transport
failures that don't need to multiply into fine-grained subtypes the way goal 5 argues domain
exceptions should, since "the call failed to even happen" doesn't usually benefit from
distinguishing *why* the way "the operation failed for reason X vs. reason Y" does. Everything
outside that subtree is domain-level and gets goal 5's finer-grained treatment. This is
documentation only — no behavior changes, just naming the axis that already exists once §2 stops
blurring it by wrapping domain exceptions in a transport-level type.

### 11. Rename `PyObsError` → `PyobsError` for naming consistency

Every other identifier in this codebase that embeds the project name already treats "pyobs" as a
single capitalized word: `PyobsArchive`, `PyobsCLI`, `PyobsDaemon`, `PyobsJournaldLogHandler`,
`PyobsWinCLI`, and a bare `Pyobs` class. `PyObsError` is the only place "Obs" gets its own capital
— an inconsistency, not a deliberate choice. Rename to `PyobsError`, matching the rest.

Mechanical, no logic changes, but real scope: 40 references across 6 files in `pyobs-core` (the
class declaration, every subclass's base-class reference, `isinstance`/`except` checks throughout
`pyobs/`, and the test suite), plus at least two downstream files
(`pyobs-gui/pyobs_gui/base.py`, `pyobs_gui/mainwindow.py`, both `except exc.PyObsError`) and two
`DEVELOPMENT.md` docs (`pyobs-gui`, `pyobs-iagvt`) referencing it by name. Since `exceptions.py`
is already being rewritten extensively in rollout step 2 (retiring `InvocationError`/
`SevereError`, adding `UnclassifiedError`, standardizing constructors), do the rename in the same
step rather than as separate churn — every new/renamed class in that PR gets declared against the
correct name from the start, instead of being touched twice.

## Rollout plan

Every assessment item (A-G) ends up somewhere in this plan — none are left as someday-maybe. Step 2
bundles everything that's tightly coupled enough it can't be split (it's one PR internally, see
its own bullets); steps 1, 3, and 4 are each independent and can go out on their own schedule
around it; the rest are incremental sweeps with no fixed order among themselves.

1. Make INFO-without-traceback the automatic default for every domain `PyObsError` in
   `Module.execute()`, add `_disable_exception_logging` as the opt-out for high-frequency types,
   and retire `@raises` as a logging mechanism (it keeps only documentary value, feeding §7's
   docstring-cross-check idea) — lands the part of #446 that was actually asked for. This *is* a
   small behavior change worth a changelog line: every RPC-exposed method raising a domain
   exception without an existing `@raises` now logs it at INFO instead of ERROR-with-traceback by
   default, which is the intended fix, not an accidental side effect.
2. **The `rpc.py`/`exceptions.py` core rework, as one PR** (proposals §2, §3 fault-path portion,
   §8, §11; Assessment §A, §C's reconstruction-adjacent parts, §D, §E):
   - Stop wrapping reconstructed exceptions in `InvocationError` — raise the real registered type
     directly, `UnclassifiedError` as the only fallback (§2). Retire `InvocationError` entirely
     (§E) — nothing constructs it under the new design.
   - Standardize the constructor contract (§8): `PyobsError.__init__(message=None, **context)`,
     generic attribute capture. Migrate ten direct-construction call sites
     (`xmppcomm.py:506,507,509`, `rpc.py:298-303`, `module.py:428`) to message-first argument
     order.
   - Rename `PyObsError` → `PyobsError` (§11) in the same pass, since every subclass declaration
     in `exceptions.py` is already being touched by the other changes here.
   - Build the exception registry (§5, Assessment §D) and switch `rpc.py`'s fault
     (de)serialization to consult it instead of `getattr` on `pyobs.utils.exceptions` — needed
     before any type can physically relocate out of that one module later.
   - Widen the five now-too-narrow call sites that relied on "everything remote arrives wrapped":
     `focusseries.py:167,194,203`, `module.py:238` (→ `except exc.PyObsError:`), and
     `lco/task.py:202-203` (→ `except exc.AbortedError:` directly, since `InvocationError` is
     gone). This is the one place in the rollout that isn't purely additive, so it can't be split
     further — all five have to move together with the unwrap fix.
   - `pyobs-monet`'s `searchpattern2.py:134-141` and `pyobs-iagvt`'s `sungrid.py:134` both have the
     same reliance on the old wrapping (see "Resolved during design" below) but are out of scope
     for now — deferred, not a blocker for this step.
3. Collapse the two catch/log sites into `Module.execute()` (proposal §3's classification/logging
   portion) — mechanical once (2) is in place, and extends the `UnclassifiedError` safety net to
   `LocalComm`/`MultiModule`, not just XMPP. Retire the `SevereError` substitution in the same pass
   (Assessment §C): move `register_exception`'s counting/threshold check into this same catch-time
   chokepoint as an instance method (`self._register_exception(...)`), fixing the cross-instance
   global-state bug as a byproduct, drop the type-substitution branch entirely, and remove the
   `_Meta` metaclass. Ten in-tree call sites plus one in `pyobs-alpaca` need the mechanical
   `exc.register_exception(...)` → `self._register_exception(...)` rename; three assertions in
   `tests/utils/test_exceptions.py` need rewriting to check the callback/state-transition instead
   of the (now-removed) type substitution.
4. Add the correlation id (proposal §9, Assessment §F) — purely additive, rides along naturally
   once (2)/(3) are already touching the same fault-path code, but doesn't block anything else.
5. Sweep the concrete gaps one at a time, each as its own small PR: `CameraException`/
   `AcquireLockFailed` → `DeviceBusyError`, `FocusModel` → `WeatherDataError`/`FocusTimeoutError`/
   `MissingSensorError` (relocated to `focusmodel.py`), `BaseTelescope`'s `ValueError` sites →
   `MissingObserverError`/`AltitudeLimitError`/`InvalidOrbitalElementsError`/`BodyResolutionError`
   (relocated to `basetelescope.py`), the capability-check `NotImplementedError` sites (including
   `ScienceFrameGuiding`/`_DummyTelescopeBase`, confirmed by the interface audit) →
   `NotSupportedError`, `InitError`/`ParkError` actually raised by the dummy/reference `IMotion`
   implementations, the `Script` subclasses' unwrapped `ValueError`s → `ScriptError` (relocated to
   `pyobs.robotic.scripts`), `BaseCamera`/`BaseSpectrograph`/`BaseVideo.grab_data()`'s `ValueError`
   → `GrabImageError`. These touch call sites other code may already `except`, so they go out
   separately rather than as one large diff. Since (2) already gives every unmigrated site a
   working `UnclassifiedError` fallback instead of a silent `RemoteError` degradation, there's no
   pressure to do this sweep all at once.
6. Document the domain/transport split explicitly in `pyobs/utils/exceptions.py` (proposal §10,
   Assessment §G) — documentation only, natural once (2) stops blurring the split by wrapping
   domain exceptions in a transport-level type. **Done.** The module docstring was, until this
   pass, a dead string literal placed after `from __future__ import annotations` — it was never
   actually `__doc__` (confirmed: `pyobs.utils.exceptions.__doc__` was `None`), so `docs/`'s
   `automodule` page rendered nothing. Moved to the true first statement in the file, and the
   split's rationale (previously a `#`-comment above `RemoteError`, invisible to
   `autoexception`/`automodule`) is now in the module docstring plus `RemoteError`'s own docstring.
7. Document the `AbortedError` contract on `_expose()`/abortable hooks (proposal §6) — purely
   additive to `pyobs-core`'s docstrings, doesn't depend on anything else in this rollout. **Done**
   in `pyobs-core` (`BaseCamera._expose()` documents `AbortedError`). The companion driver-repo
   fixes are now done too: `pyobs-sbig` (`sbigcamera.py:162`, `sbigfiltercamera.py:168`) and
   `pyobs-fli` (`flicamera.py:169`) all raise `exc.AbortedError` instead of bare `InterruptedError`
   now.
8. Docstring sweep across every interface flagged in the audit (proposal §7) — the mismatches that
   are pure documentation fixes (`IAutoFocus`, `IAcquisition`) can go immediately; the ones that
   need §4's behavior fixes first (`IData`, `IMotion`, the pointing/tracking `MoveError` family,
   `IFocusModel`) land alongside those; the doc-gap-only interfaces with no implementers
   (`ICalibrate`, `ISyncTarget`, etc.) can go any time. **Done** — spot-checked against the audit
   table above: `IAutoFocus`, `IData.grab_data`, `IPointingRaDec.move_radec`, and
   `FlatField.set_filter`/`flat_field` all match current behavior, and every doc-gap-only interface
   (`ICalibrate`, `ISyncTarget`, `IMultiFiber`, `IPointingSeries`, `IRotation`, `IScriptRunner`,
   `IStructuredConfig`) now has a `Raises:` clause using the new exception vocabulary
   (`GeneralError`/`InvalidArgumentError`/`MoveError`/`ScriptError`).

One item surfaced by the driver survey was explicitly **not** part of this rollout because it lives
in another repository and can't be fixed by a pyobs-core PR alone: `pyobs-brot`'s roof/dome/
telescope silently returning success instead of raising `InitError`/`ParkError` on hardware
failure — see "Confirmed in downstream driver projects" above. **Done** — `BrotRoof`/`BrotDome`/
`BrotBaseTelescope`'s `init()`/`park()` now raise the documented exception (in addition to the
existing logging/state-change) at every `_error_state(...)` call site reachable synchronously from
those two methods; background/status-polling call sites were left alone since nothing is waiting
on their result.

## Resolved during design

- `_disable_exception_logging`'s shape: an instance method called from `__init__`, matching
  `register_exception`'s existing convention (`self._disable_exception_logging(exc.FocusError)`),
  not a class-level decorator like the old `@raises`. Decided; see proposal §1.
- Cross-repo impact: checked every sibling `pyobs-*` project on the `2.0.0.devX` line
  (`pyobs-alpaca`, `-aravis`, `-asi`, `-brot`, `-fli`, `-flipro`, `-gui`, `-monet`, `-qhyccd`,
  `-sbig`, `-v4l`, `-zaber`, `-zwoeaf`) for `InvocationError`/`RemoteError`/`except exc.`.
  `pyobs-gui`'s two hits (`pyobs_gui/base.py:311`, `pyobs_gui/mainwindow.py:577`) catch the broad
  `exc.PyObsError` and don't touch `.exception`, so they're unaffected either way.
  `pyobs-monet/pyobs_monet/morisot/searchpattern2.py:134-141` relied on the old wrapping (a
  retry loop doing `except exc.InvocationError: pass` around a proxy call, to mean "any remote
  failure"). **Fixed**: once proposal §2 actually landed and retired `InvocationError`, this
  wasn't a quiet degradation as originally assumed — `exc.InvocationError` no longer resolves at
  all, so evaluating the `except` clause on the first acquisition miss raised `AttributeError` and
  killed the whole search-pattern run instead of retrying. Changed to `except exc.PyobsError:`,
  matching the same widening this repo did at its own five now-too-narrow call sites in step 2.
  Noted for later regardless: grepping can only find call sites that name the exception type
  explicitly — a bare `except Exception:` swallowing the same wrapped failure elsewhere wouldn't
  show up this way, so a changelog callout for proposal §2 is still worth doing independent of
  `searchpattern2.py` specifically.
- **`pyobs-iagvt` was missing from that cross-repo pass and has a worse version of the identical
  gap — confirmed still open, deliberately left unfixed.** `pyobs_iagvt/modules/sungrid.py:7` does
  `from pyobs.utils.exceptions import InvocationError` (a direct import, not an attribute access
  like `searchpattern2.py`'s), used at line 134 in
  `except (ValueError, InvocationError) as e: log.info(f"Something went wrong: {str(e)}")` around
  `_do_the_wiggle()` (`sungrid.py:91-106`), which itself does proxy calls to a telescope and camera
  (`sungrid.py:93`). This is not "silently stops catching" as originally assumed here — confirmed
  by actually importing the module: since `InvocationError` was fully removed rather than
  deprecated, the `from ... import InvocationError` line itself raises `ImportError` at module
  load, so anything importing `sungrid.py` currently fails to start outright. Explicitly deferred
  by current decision (told to ignore it for now) rather than fixed alongside the other three
  driver-repo companion fixes above — this note exists so the gap isn't rediscovered from scratch
  later.

## Bad-argument `ValueError`s: scoped and partially promoted after the rollout

Originally flagged as "still open" (below, kept for history): bad-argument-validation `ValueError`s
were deliberately left un-promoted during steps 5/8, but since `ValueError` is a builtin, never in
the `PyobsError` registry, a caller writing `except ValueError:` around a *remote* proxy call
doesn't catch it (arrives as `UnclassifiedError` instead) even though the identical code works
fine locally (`LocalComm`, direct calls, tests) -- a real "works in dev, breaks in prod" footgun,
raised by the project owner after the rollout closed.

Scoped it out before touching anything: of ~60 raw `raise ValueError` sites in `pyobs/modules/`,
most are constructor/config-time validation, internal event-handler checks, or background-task-only
code -- never reachable via RPC at all, irrelevant to this problem. What's actually left sorts into
three shapes:

1. **Genuine bad-argument validation on RPC-exposed methods** -- `IConfig.get_config_value`/
   `get_config_value_options`/`set_config_value` (`module.py`), `IDataSequence.grab_sequence`'s
   count/delay (`basecamera.py`), `ITrackingMode.set_tracking_mode`, `IFocuser.set_focus`,
   `IFilters.set_filter` (all `_dummytelescopebase.py`), `IMode.set_mode` (`dummymode.py`),
   `IWeather.get_sensor_value` (`mockweather.py`) -- 7 methods, ~16 sites. **Done**: new shared
   `InvalidArgumentError(PyobsError)`, one type reused everywhere (same shape as `DeviceBusyError`/
   `NotSupportedError`), not a bespoke leaf per method -- goal 5's own test says no caller reacts
   differently to "unknown filter" vs. "invalid focus value." Real driver repos likely have the
   identical pattern for real hardware (e.g. `pyobs-sbig/sbigfiltercamera.py`'s own
   `ValueError(f"Unknown filter: {filter_name}")` for the same `IFilters.set_filter` condition) --
   companion fix in those repos, not reachable from this PR, same shape as the `AbortedError`
   situation. **Done** — `pyobs-sbig/sbigfiltercamera.py`'s `set_filter()` now raises
   `exc.InvalidArgumentError`, and its `Raises:` clause (a copy-paste leftover, "If binning could
   not be set," on a filter-setting method) is fixed alongside it. Its `open()`'s own `ValueError`
   (filter-wheel-model setup) was left alone -- that one's local-lifecycle/startup code, not
   RPC-reachable, same scoping rule as the rest of this section.
2. **"Already busy/running" state preconditions, not actually bad arguments** --
   `FlatField.flat_field`, `FlatFieldScheduler.run`. **Done**: reused the *existing*
   `DeviceBusyError`, no new type needed.
3. **Malformed external data** (a weather station's API response, not a caller mistake) --
   `Weather.get_sensor_value`. **Done**: new `WeatherResponseError(PyobsError)` in
   `weather.py` (co-located, per §5's relocation convention), the same reasoning as
   `BodyResolutionError` -- plausibly transient, worth retrying, not the caller's fault.
   `WeatherState.status`'s setter (`weather_state.py:25`) turned out, on closer look, to be a
   mis-scoping on my part: it's only ever called from `_update()`'s background polling loop, which
   already wraps it in a broad `except Exception: log.warning(...)` -- it never reaches an RPC
   caller at all, so it's out of scope entirely (same shape as `focusmodel.py`'s
   `_on_focus_found`/`_calc_focus_model`), not something needing a type change.

### Original "still open" note, for history

- **Bad-argument-validation `ValueError`s are deliberately not promoted to `PyobsError` leaf
  types, but that means they still degrade to `UnclassifiedError` over RPC.** Steps 5/8's sweep
  only promotes *domain operation failures* (e.g. "camera is busy," "body not resolvable") to
  specific types; plain input validation (e.g. `IFilters.set_filter`'s "unknown filter name",
  `IFocuser.set_focus`'s "invalid focus value", `IMultiFiber.set_fiber`'s "invalid fiber name")
  intentionally stays as ordinary `ValueError`, matching Python's own convention for API misuse and
  matching how the interface audit already treated these as clean matches, not gaps. But since
  `ValueError` is a builtin, not a `PyobsError` subclass, it's never in the registry -- a caller
  writing `except ValueError:` around a *remote* proxy call does not catch it (it arrives as
  `UnclassifiedError` instead); only same-process callers (`LocalComm`) see a real `ValueError`.
  This was a deliberate scope call, not an oversight -- flagged explicitly per the project owner's
  request during the docstring sweep (step 8) so it's easy to find later, in case a future caller
  actually needs to distinguish "bad argument" domain-uniformly over RPC. Promoting these would be
  a much larger sweep (dozens of call sites across nearly every setter-shaped interface method) and
  is deliberately not part of this rollout.

  **Update**: `IMultiFiber.set_fiber` has zero concrete implementers anywhere in this repo (see
  step 8's audit), so there's no real raise site to migrate here the way there was for the 7
  methods above -- but its docstring's `ValueError` placeholder was updated to
  `InvalidArgumentError` anyway, so a future implementer follows the now-established convention
  instead of the retired one.

## Bug found and fixed after the rollout: `original_type` didn't actually survive the wire

Prompted by the project owner asking, after step 8, "are we catching ALL exceptions on the callee
side, what happens to `IndexError`/etc.?" -- tracing it through turned up a real gap `UnclassifiedError`
was supposed to close but didn't.

`Module.execute()` wraps any non-`PyobsError` into `UnclassifiedError(str(raised),
original_type=...)` *before* `rpc.py` ever sees it (that's the whole point of centralizing
classification in step 3). But `fault_to_xml` only ever serialized the wrapper's own class name --
`"pyobs.utils.exceptions.UnclassifiedError"` -- which *resolves successfully* on the caller's side
(it's a registered type!), so the caller reconstructed a fresh `UnclassifiedError(msg,
remote_module=sender)` with `original_type` never set at all. `original_type` is a local attribute,
not part of the two things that actually cross the wire (qualified class name + message), so it was
silently lost in transit every time -- a remote `IndexError` and a remote `ValueError` arrived as
indistinguishable `UnclassifiedError`s with no way to tell them apart, even in the message text.
(`LocalComm` never had this problem -- no serialization step, so the real attribute survives.)

**Fix**: `fault_to_xml` now serializes `original_type` instead of the wrapper's own class name,
whenever the exception carries one. The caller's own registry lookup then runs against the
*original* name -- for a builtin/vendor type that's never registered, it correctly falls back to
`UnclassifiedError` again, but this time with `original_type` actually populated, matching what the
class's own docstring already claimed.

Found and fixed in the same pass: `fault_to_xml` was also serializing `str(exception)`
(`"<ClassName> message"`) instead of the raw `.message` for the message field. Reconstruction
passes that string straight back in as the new instance's `message`, so the *caller's* own
`__str__` formatted it a second time on top -- every exception that ever crossed the wire arrived
with a doubled `"<ClassName> <ClassName> message"` once displayed. Now serializes the raw message.
