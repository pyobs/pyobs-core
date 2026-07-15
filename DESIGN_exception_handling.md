# Exception handling across the RPC boundary

Status: proposed. Tracks #446.

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

Also worth a mention: `Comm.open()` attaches a `CommLoggingHandler` to the root logger at
`INFO` (`pyobs/comm/comm.py:70-78`), rebroadcasting every `INFO`+ log record to all other modules
as a `LogEvent`. Suppressing local logging for a type also suppresses this broadcast — that may
be the right call, or it may need its own knob; flagging it as a decision point below.

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
still log at ERROR today. Treating this as an oversight rather than a deliberate restriction: a
method decorated `@raises(exc.FocusError)` almost certainly means "anything in the `FocusError`
family," not "literally `FocusError` and nothing that subclasses it" — especially once goal 5 adds
leaf subclasses like `WeatherDataError(FocusError)` under types that are already declared in a
`@raises(...)`. Switching to `isinstance` (done in proposal §1 below) is a bugfix, not a behavior
change that needs a changelog callout beyond noting it fixes previously-under-caught subclasses.

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

The incremental fixes below (Proposed design §§1-6) all still make sense on their own, but stepping back,
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
today. `InvocationError` doesn't need to disappear — it keeps exactly one job, becoming the
fallback for the case where the remote type couldn't be resolved at all (i.e. it collapses into
the `UnclassifiedError` safety net from proposal §2 below: known type → raise it directly, unknown
type → raise something that says "I don't know what this was, here's the name and message I did
get").

**This is not a free change** — four call sites currently rely on the old behavior and would need
auditing: `pyobs/modules/focus/focusseries.py:167,194,203` and `pyobs/modules/module.py:238` all
write `except exc.RemoteError:` around a proxy call, but reading them, none actually mean
"specifically a transport failure" — `focusseries.py:167`'s comment-equivalent intent is "however
this call failed, treat it as my own `FocusError`," and `module.py:238`'s is "however this failed,
just skip this module." They only work today because *every* remote failure, transport or domain,
currently arrives as some `RemoteError` subclass (`InvocationError`). Once domain exceptions stop
being wrapped, these need to widen to `except exc.PyObsError:` (or even bare `Exception`) to
preserve their actual intent — a small, enumerable migration (4 sites, not a sweep), but a real
one, not just a config flip.

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
`_disable_exception_logging`/`@raises` level decision, and the actual `log.log(...)` call. `rpc.py`
then does no independent logging or wrapping at all — its `except Exception` block (which, after
this change, is really always `except exc.PyObsError`, since `execute()` never lets anything else
through) purely serializes and sends the fault. This removes an entire redundant catch/log site
architecturally, instead of relying on an instance flag to make it inert after the fact, and gives
`LocalComm` the same wrapping guarantee XMPP calls get, for free.

### C. Decouple severity escalation from construction-time metaclass magic

Already flagged in the `register_exception` comparison above, but worth restating as a standalone
design smell: `raise exc.FocusError("...")` can silently hand back a `SevereError` instance
instead, because the metaclass intercepts *construction*, not raising or catching. That means
`isinstance` checks anywhere between the `raise` and the eventual catch site can't be trusted to
reflect the type actually named in the source — the object can already have mutated into something
else before the `raise` keyword even runs. I'd move `handle_exception`'s escalation decision to a
catch site (natural fit: the same `Module.execute()` chokepoint from §B) rather than the
metaclass/constructor, so `raise X(...)` always genuinely raises `X`, and "this got severe, treat
it as `SevereError` instead" becomes an explicit, visible step in the one place that already
decides logging and wire-serialization, rather than invisible action-at-a-distance triggered by
merely constructing an exception object (which, notably, can happen without ever raising it at
all — e.g. constructing one to pass as `exception=` to something else).

### D. Serialize by registry, not by name-lookup into one hardcoded module

`getattr(exc, exc_name, None)` (`rpc.py:272`) only ever finds classes that live in
`pyobs.utils.exceptions`. That's an implicit constraint nobody had to think about while the
hierarchy was small and centralized, but goal 5 argues for many new, specific types — and the
natural place for e.g. `CameraBusyError` is next to `BaseCamera`, not in a growing, unrelated
`exceptions.py` god-file. Those two pulls are in direct tension under the current serialization
scheme: put `CameraBusyError` where it domain-belongs and it silently stops surviving the wire.

I'd replace the hardcoded single-module lookup with an explicit registry — a decorator (e.g.
`@exc.register` or reusing the existing `_Meta` machinery) that any `PyObsError` subclass opts
into regardless of which file defines it, populating a flat `name -> class` dict the fault
deserializer consults instead of `getattr` on one module. This is also a deliberate security
boundary, not just a convenience: the current design is *accidentally* safe because `getattr` can
only ever resolve names that exist in one fixed, trusted module — a naive fix ("serialize the
fully-qualified class path and import it") would trade that away for an open-ended dynamic import
driven by a value that arrived over the wire, which is a real hole (importing and instantiating an
arbitrary object based on untrusted network input). An explicit registry keeps the same "only
things we chose to expose are reconstructable" property the accident currently gives us, while
decoupling "reconstructable" from "physically defined in this one file."

### E. Standardize the constructor contract

Already-noted bug: the fault-reconstruction code assumes every `RemoteError` subclass accepts
`(message=.., module=..)` as keywords, which `InvocationError` and `ForbiddenError` don't — a
latent `TypeError`-inside-the-fault-handler waiting for the wrong name to show up
(`rpc.py:277-280`). More generally, as goal 5 adds more subclasses with their own structured
fields (a `MissingSensorError` might reasonably want to carry the sensor name; a
`BodyResolutionError` the body name that failed to resolve), each one either needs its own
special-cased reconstruction branch or a genuinely uniform contract. I'd standardize on: every
`PyObsError` subclass accepts `message: str | None` positionally/as its first argument, plus
arbitrary keyword-only structured fields that get captured generically (e.g. into a `self.context:
dict[str, Any]`) rather than becoming bespoke positional constructor parameters — so the RPC layer
can reconstruct *any* subclass the same way (`cls(msg, **context)`) without knowing its specific
shape in advance, and adding a new field to a new exception type never requires touching
`rpc.py` again.

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

A and B are the two I'd actually want to land alongside the incremental proposal below — A because
without it, goal 5's whole premise (callers reacting to specific types) doesn't hold, and B because
it removes the fragile `.logged`-flag coordination this doc otherwise just documents and works
around. C, D, E are real but more invasive and lower urgency — worth doing, but each is its own
PR-sized change and none blocks #446 itself. F is small and purely additive, worth including
opportunistically whenever `rpc.py` is being touched anyway. G is a documentation/naming outcome
of A, not separate work.

## Design goals

1. An exception should be logged once, at the place a human can actually act on it — not
   re-logged at every hop it passes through on the way back to a caller. Concretely: `PyObsError`
   subclasses are the deliberate, caller-facing API of a failure mode — the module author decided
   a caller should be able to distinguish and react to this, so the module gets to decide whether
   it's *also* worth a local line. Anything else (a raw builtin, a third-party/vendor SDK
   exception) is by definition not part of that deliberate contract — it's unanticipated, which
   means the fix belongs in the code/hardware that produced it. Those should always be logged
   loudly, locally, where they happened, with no suppression possible; if a condition like that
   turns out to recur often enough that callers legitimately need to distinguish and react to it,
   that's the signal to promote it into a proper `PyObsError` subclass — not to keep passing it
   through as a string forever.
2. Anything that crosses an RPC boundary should arrive as a meaningful, typed error on the other
   side, catchable directly as that type. A caller writing `except exc.FocusError:` around a
   proxy call should actually catch it — today it never does (see "Assessment" §A below: every
   remote domain exception arrives wrapped in `InvocationError` instead), which undercuts goal 5
   as much as the wire silently degrading to `RemoteError` does.
3. A module should be able to declare "these exception types (and their subclasses) are
   expected/already-handled — don't log them locally as errors," without losing the ability to
   still see genuinely unexpected failures at ERROR with a traceback.
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

`Module.execute()`'s catch block consults the list with `isinstance`, not exact-type match, so
declaring a base class covers its subclasses for free — closing the gap versus `@raises`'s exact
match:

```python
except Exception as e:
    if isinstance(e, exc.PyObsError) and not isinstance(e, exc.ModuleError):
        if isinstance(e, self._disabled_exception_logging):
            pass  # caller already has it; nothing to log locally
        else:
            level = "INFO" if isinstance(e, getattr(func, "raises", ())) else "ERROR"
            exc_info = level == "ERROR"
            e.log(log, level, f"Exception was raised in call to {method}: {e}", exc_info=exc_info)
    raise e
```

This subsumes `@raises(...)`'s INFO-demotion behavior (also switched to `isinstance` while we're
in there) rather than replacing it outright — `@raises` still exists for "log at INFO, I still
want a line," `_disable_exception_logging` is the new "log nothing, this is fully expected."
Both read from the same `isinstance` check shape, so the two decorators/methods stay consistent
with each other instead of one being exact-match and the other subclass-aware.

This also settles the `CommLoggingHandler` broadcast question by construction, not by choice: the
`pass` branch above never calls `e.log(...)`, so no `LogRecord` is created at all — there's nothing
for `CommLoggingHandler` (`pyobs/comm/comm.py:70-78`, just another handler on the root logger) to
pick up. "Suppress locally but still broadcast" isn't a flag away; it would need a second,
deliberate path (e.g. calling `comm.send_event(...)` directly, bypassing `logging` entirely) even
though the local write is skipped. Deliberately not building that: the two-tier split already
covers it without new plumbing — `@raises(...)` is "log at INFO, still emit a record" (which,
being INFO+, still gets picked up and broadcast), `_disable_exception_logging` is the stronger
"not worth a line to anyone" tier. A module author wanting "quiet locally but still visible to an
operator watching the fleet" already has `@raises` for that; giving
`_disable_exception_logging` the same broadcast-preserving behavior would just duplicate it. And
per Assessment §A, once the caller receives the real typed exception directly rather than buried
in `InvocationError`, it already has full fidelity — type, message, and (with the correlation id
from §F) a path back to the origin's detailed log if ever needed — so staying silent isn't losing
information, it's not re-announcing something the direct recipient already has in full. One scope
caveat regardless: this only touches the one log call inside `execute()`'s catch block — any other
`log.info`/`log.warning` a driver makes on its own (e.g. inside a retry loop) is untouched either
way; `_disable_exception_logging` was never a total-silence guarantee, just a fix for this one
redundant site.

### 2. Raise the real reconstructed type directly; `UnclassifiedError` is the only fallback

Per Assessment §A, `_on_jabber_rpc_method_fault` should stop wrapping every successfully
reconstructed exception in `InvocationError`:

```python
exception_class = registry.get(exc_name)  # see Assessment §D — registry, not getattr on one module
if exception_class is not None:
    exception = exception_class(msg, **context)   # real type, e.g. FocusError — raised as-is
    exception.remote_module = sender
else:
    exception = exc.UnclassifiedError(msg, original_type=exc_name, module=sender)
future.set_exception(exception)
```

`InvocationError` keeps exactly one job — the `else` branch above — rather than wrapping every
case. This also folds in the constructor-contract bug from the previous draft of this section:
today's reconstruction assumes every `RemoteError` subclass accepts `(message=.., module=..)`,
which `InvocationError`/`ForbiddenError` don't, a latent `TypeError`-inside-the-fault-handler
(`rpc.py:277-280`). Since `InvocationError` no longer needs to wrap arbitrary reconstructed types
under this design, that whole branch simplifies away rather than needing a separate fix.

**Required migration, not optional cleanup**: `pyobs/modules/focus/focusseries.py:167,194,203`
and `pyobs/modules/module.py:238` currently write `except exc.RemoteError:` specifically to catch
*any* failure from a proxy call (transport or domain) — they only work today because domain
exceptions arrive wrapped in an `InvocationError` (a `RemoteError` subclass). Once fixed, these
need to widen to `except exc.PyObsError:` (their actual intent, reading each one) or they'll stop
catching domain failures from the remote side entirely. This has to land in the same PR as the
unwrap fix, not after it.

### 3. Collapse the two catch/log sites into `Module.execute()`

Per Assessment §B: move classification (wrap non-`PyObsError` into `UnclassifiedError`), the
`_disable_exception_logging`/`@raises` level decision, and the actual `log.log(...)` call entirely
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
  meaning) — passes test 1 outright ("back off and retry" vs. "something actually broke"). Give it
  its own type in `exceptions.py`, e.g. `CameraBusyError(PyObsError)`, rather than either leaving
  it as a non-`PyObsError` class or folding it into `GrabImageError` where it would be
  indistinguishable from a genuine grab failure. Deliberately *not* split further into e.g. a
  busy-for-exposure vs. busy-for-sequence variant — no caller would react differently to those two.
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

Note: §2 above already gives every new type here a working fallback — anything not yet migrated
to a specific type still arrives as `UnclassifiedError` rather than degrading to an untyped
`RemoteError`, so this sweep can genuinely happen incrementally, type by type, without a
transitional period where unmigrated call sites are worse off than today.

### 5. Document (and fix) the `AbortedError` contract on abortable hooks

Per the driver survey above: `BaseCamera._expose()`'s docstring never mentions `AbortedError`,
and two independent driver projects both guessed `InterruptedError` instead — this isn't a
one-off mistake, it's a missing contract. Add `Raises: AbortedError: If the operation was
cancelled via abort_event.` (or equivalent) to `_expose()`'s docstring and any other
`abort_event`/`IAbortable`-adjacent hook signature in `pyobs-core`, and fix the three known
call sites this PR can reach: `pyobs-sbig/src/pyobs_sbig/sbigcamera.py:162`,
`sbigfiltercamera.py:168`, `pyobs-fli/pyobs_fli/flicamera.py:169` — each a one-line change
(`InterruptedError(...)` → `exc.AbortedError()`), but in a different repository, so it's a
companion PR alongside the core docstring fix, not something this repo's PR can do alone.

### 6. Keep documentation honest

- Fix the two confirmed mismatches: `IAutoFocus.py`'s `Raises:` clause (`ValueError` →
  `FocusError`, `AbortedError`), and add a `Raises:` clause to `IFocusModel.py` once (4)'s
  `FocusError` fix lands there.
- Longer-term, low-priority idea: a lint/test that cross-checks `@raises(...)`/
  `_disable_exception_logging(...)` arguments against the types actually referenced in a method's
  docstring, so the three no longer drift independently. Not required for the initial rollout.

## Rollout plan

1. `_disable_exception_logging` + switch `@raises` and the new check to `isinstance` — lands the
   part of #446 that was actually asked for, low risk, no behavior change for existing callers
   since nothing uses the new method yet.
2. Stop wrapping reconstructed exceptions in `InvocationError` (proposal §2) *together with*
   widening the four now-too-narrow `except exc.RemoteError:` call sites
   (`focusseries.py:167,194,203`, `module.py:238`) in the same change — this is the one place in
   the rollout that isn't purely additive, so it can't be split across separate PRs the way the
   rest can. Also fixes the `InvocationError`/`ForbiddenError` reconstruction-signature bug as a
   byproduct, since `InvocationError` no longer needs to handle arbitrary reconstructed types.
   `pyobs-monet`'s `searchpattern2.py:134-141` has the same reliance on the old wrapping (see Open
   questions) but is out of scope for now — deferred, not a blocker for this step.
3. Collapse the two catch/log sites into `Module.execute()` (proposal §3) — mechanical once (2) is
   in place, and extends the `UnclassifiedError` safety net to `LocalComm`/`MultiModule`, not just
   XMPP.
4. Sweep the concrete gaps one at a time, each as its own small PR: `CameraException`,
   `FocusModel`, `BaseTelescope`'s `ValueError` sites, the `Script` subclasses' unwrapped
   `ValueError`s, `BaseVideo.grab_data()`'s `ValueError` → `GrabImageError`. These touch call
   sites other code may already `except`, so they go out separately rather than as one large diff.
   Since (2) already gives every unmigrated site a working `UnclassifiedError` fallback instead of
   a silent `RemoteError` degradation, there's no pressure to do this sweep all at once.
5. Document the `AbortedError` contract on `_expose()`/abortable hooks (proposal §5) — purely
   additive to `pyobs-core`'s docstrings, doesn't depend on anything else in this rollout.
6. Docstring sweep (`IAutoFocus`, `IFocusModel`, and any others turned up while doing (4)).

Two items surfaced by the driver survey are explicitly **not** part of this rollout because they
live in other repositories and can't be fixed by a pyobs-core PR alone: the `AbortedError` fix in
`pyobs-sbig`/`pyobs-fli` (companion to step 5) and, more importantly, `pyobs-brot`'s roof/dome/
telescope silently returning success instead of raising `InitError`/`ParkError` on hardware
failure — see "Confirmed in downstream driver projects" above. The latter isn't blocking #446, but
it's a real, independent bug worth its own issue regardless of this design doc's fate.

Assessment items C (decouple severity escalation from construction), D (registry-based
serialization), E (uniform constructor contract — largely subsumed by step 2 above, but the
general-purpose version for future subclasses is separate), F (correlation id), and G (naming) are
not included in this rollout — each is its own PR-sized change, none blocks #446, and D in
particular only becomes urgent once the sweep in step 4 actually wants to define exception types
outside `pyobs/utils/exceptions.py` (currently proposed as living there anyway, per step 4's
listed types, precisely to sidestep needing D immediately).

## Open questions

- `_disable_exception_logging` as an instance method called in `__init__` (matches
  `register_exception`'s existing convention) vs. a class-level decorator like `@raises` — the
  issue text suggests the former (`self._disable_exception_logging(...)`); confirm that's still
  the preference now that `@raises` is being touched anyway.
- Checked every sibling `pyobs-*` project on the `2.0.0.devX` line (`pyobs-alpaca`, `-aravis`,
  `-asi`, `-brot`, `-fli`, `-flipro`, `-gui`, `-monet`, `-qhyccd`, `-sbig`, `-v4l`, `-zaber`,
  `-zwoeaf`) for `InvocationError`/`RemoteError`/`except exc.`. `pyobs-gui`'s two hits
  (`pyobs_gui/base.py:311`, `pyobs_gui/mainwindow.py:577`) catch the broad `exc.PyObsError` and
  don't touch `.exception`, so they're unaffected either way. `pyobs-monet/pyobs_monet/morisot/
  searchpattern2.py:134-141` does rely on the old wrapping (a retry loop doing
  `except exc.InvocationError: pass` around a proxy call, to mean "any remote failure") but that
  script is out of scope for now — not a current concern for this design, per the project owner.
  Noting for later regardless: grepping can only find call sites that name the exception type
  explicitly — a bare `except Exception:` swallowing the same wrapped failure elsewhere wouldn't
  show up this way, so a changelog callout for proposal §2 is still worth doing when it lands,
  independent of `searchpattern2.py` specifically.
- Should Assessment items C/D/E/F/G be tracked as their own follow-up issues now, so they don't
  get lost once #446 itself is closed out by steps 1-5?
