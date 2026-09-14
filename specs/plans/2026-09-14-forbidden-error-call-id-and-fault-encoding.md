# Plan: route ACL-denial faults through the normal call_id/fault-encoding path (#899)

Status: implemented, closed — released in v2.8.9

Issue: pyobs-core#899

## Problem

`ForbiddenError` (raised by `Module.execute()`'s ACL check, `pyobs/modules/module.py:640-647`)
is special-cased all the way down the stack, and loses information at every hop that every other
domain exception keeps:

1. **`module.py:640-647`** raises `exc.ForbiddenError` *before* the `try` block
   (`module.py:671-699`) that stamps `call_id` (line 684), logs consistently, and calls
   `self._record_exception(e)`. An ACL denial gets none of that.
2. **`pyobs/comm/xmpp/rpc.py:239-241`** (`_on_jabber_rpc_method_call`) has its own
   `except exc.ForbiddenError` branch, separate from the generic `except Exception` branch
   (`rpc.py:243-251`) every other exception falls into. Instead of `send_fault(iq,
   fault_to_xml(e))` (a normal `iq type="result"` carrying a `<fault>`, which is what
   `_on_jabber_rpc_method_fault` on the caller side already knows how to reconstruct with the
   right type and `call_id`), it calls `xep_0009.forbidden(iq).send()` — a raw XEP-0009
   `<iq type="error"><error><forbidden/></error></iq>`.
3. **`pyobs/comm/xmpp/xmppcomm.py:662-670`** (`XmppComm.execute()`, the actual method every
   `Comm.execute()` caller goes through) catches `slixmpp.exceptions.IqError` for that raw IQ
   error and, for `condition == "forbidden"`, raises a fresh generic `exc.RemoteError` — not
   `exc.ForbiddenError` (already a `RemoteError` subclass, `exceptions.py:182`) — with no
   `call_id` at all. This is the *live* path (per the comment there: slixmpp's own `Iq.send()`
   future resolves on the error before `rpc.py`'s `jabber_rpc_error` event handler ever runs).
4. **`pyobs/comm/xmpp/rpc.py:313-337`** (`_on_jabber_rpc_error`) has the same lossy
   `"forbidden" -> generic RemoteError`, no-`call_id` mapping. Per the comment in (3), this branch
   likely never actually fires for calls made through `RPC.call()`/`Comm.execute()` — kept here as
   a secondary, lower-confidence fix (see Testing).

Net effect: a Python module-to-module caller sees a generic `RemoteError` (wrong type) with no
`call_id` (can't correlate to the origin-side log line). pyobs-web-client's JS caller sees this
as a raw XMPP-level error it can't even parse as an RPC fault at all — confirmed against its
`findRpcFault()` while verifying #54/#167 (which is what surfaced this issue).

## Design

Stop special-casing ACL denial and let it flow through the same call_id-stamping,
logging, and fault-encoding path every other domain exception already uses.

- **`module.py`**: widen the existing `try` (currently `module.py:671-699`) to also cover the ACL
  check and parameter binding (currently `module.py:640-663`, unprotected). The raise still
  happens before `func()` is ever called (line 672), so a denied caller still can't trigger the
  method's side effects — only the *handling* of the raise changes. `ForbiddenError` already
  `isinstance(..., exc.PyobsError)`, so it takes the existing `e = raised` branch (`module.py:679`
  today) with no new classification logic.
- **Log level**: today `rpc.py:240` logs ACL denials at `WARNING`. Folding into the shared path
  would default to `INFO` (the suppressible-exception branch, `module.py:691-695`) unless
  `ForbiddenError` is unsuppressible (`_UNSUPPRESSIBLE`, `module.py:215`, is `ERROR` — too loud;
  that tuple's contract is "always needs local attention," which isn't quite what an ACL denial
  is). Add a small level override in the classification step: `WARNING` for
  `isinstance(e, exc.ForbiddenError)`, `INFO` for every other suppressible exception — preserves
  today's visibility for what's arguably a security-relevant event without inventing a new bucket.
- **`rpc.py` (`_on_jabber_rpc_method_call`)**: delete the `except exc.ForbiddenError` branch
  (lines 239-241) entirely. `ForbiddenError` now falls into the existing generic
  `except Exception as e` branch (line 243), which already does the right thing:
  `isinstance(e, exc.PyobsError)` is `True`, so the `log.exception(...)` call there is skipped
  (`module.py` already logged it, once), and `send_fault(iq, fault_to_xml(e))` sends a normal
  fault. No new code needed here, only removal.
- **Caller side, real fault path (`_on_jabber_rpc_method_fault`, `rpc.py:283-311`)**: already
  correct today — resolves the exception via `exc.PyobsError.resolve(exc_name)`, which finds
  `ForbiddenError` by its fully-qualified name, and already sets `call_id = jid`
  (`rpc.py:308`). Once the server stops calling `xep_0009.forbidden()`, this handler is what
  actually fires for an ACL denial, and both problems (wrong type, missing `call_id`) are
  already solved by code that exists today. No change needed here.
- **`xmppcomm.py:662-670` (defensive/back-compat path)**: kept, but improved rather than deleted —
  a caller running this fix can still be talking to an un-upgraded peer (different repo/version,
  see `specs/steering/pyobs-project-tiers.md`'s version policy) that still sends the raw
  `forbidden` IQ error. For `condition == "forbidden"`, raise `exc.ForbiddenError` (not generic
  `RemoteError`) and stamp `call_id = e.iq["id"]` (the echoed request id, same value used as
  `call_id` everywhere else) if present, instead of leaving it unset.
- **`rpc.py:313-337` (`_on_jabber_rpc_error`)**: same treatment as `xmppcomm.py` above, for
  consistency, even though (3) means this branch is believed dead for the "forbidden" condition
  specifically today. Cheap to fix, and removes a second place carrying the same wrong mapping in
  case it's reachable through some path this plan didn't trace (e.g. a call made without going
  through `RPC.call()`).

### Considered and rejected

- **Leave `xep_0009.forbidden()` and only fix `call_id`/type on the caller side.** Rejected: the
  caller-side fixes in isolation still leave pyobs-web-client (and any other non-Python client)
  stuck parsing a raw XMPP IQ error instead of a normal RPC fault — the actual symptom #899 was
  filed for. The fault-encoding path has to change server-side for that to be fixed at all.
- **Keep the `except exc.ForbiddenError` special case in `rpc.py`, just add `call_id` stamping and
  switch it to call `send_fault` too.** Rejected in favor of deleting it outright: once it does the
  same thing as the generic `except Exception` branch, keeping a separate branch is dead
  duplication, not a real distinction.

## Testing

- `tests/integration/test_xmpp_acl.py` (needs a live ejabberd, `pytest.mark.xmpp`/`integration` —
  not run as part of this pass; syntax/lint/type-checked only): tightened all three
  `pytest.raises(exc.RemoteError)` call sites to `pytest.raises(exc.ForbiddenError)`, each now also
  asserting `exc_info.value.call_id is not None`. Updated the module docstring and
  `test_acl_deny_forbids_call`'s docstring, which used to claim the call "surfaces as
  `exc.RemoteError`" (still true, `ForbiddenError` *is* one, but no longer the precise/intended
  type).
- `tests/utils/test_exceptions.py`: unchanged, as expected — `ForbiddenError`'s registry/resolve
  behavior was already covered generically for `PyobsError` subclasses.
- `tests/modules/test/test_standalone.py`: three new unit tests added —
  `test_execute_forbidden_error_carries_call_id`, `test_execute_forbidden_error_logs_at_warning`,
  `test_execute_forbidden_error_records_exception` (the last verified indirectly, via a
  `_register_exception`/severity-handler callback actually firing). All call `Module.execute()`
  directly, no XMPP needed.
- **Found while running the existing suite, not anticipated in the design above**:
  `test_execute_allow_interface_name_sugar_permits_interface_methods` asserted
  `pytest.raises(TypeError)` for a call with missing required arguments — widening `execute()`'s
  `try` to also cover parameter binding (as designed above) means that `TypeError` is now
  classified like any other non-`PyobsError` escape, i.e. wrapped as `exc.UnclassifiedError`
  rather than left raw. Updated the test's assertion and comment to match. This is a real,
  intentional behavior change from this plan (a bad-argument call now also gets `call_id`/logging/
  `_record_exception` treatment it didn't have before), not a regression — flagging it explicitly
  here since it wasn't called out as its own bullet in the design.
- `docs/source/whatsnew-2.0.rst`: the 2.0 ACL section stated a denied call "maps to the XMPP
  IQ-level `forbidden` condition on the wire" — corrected to describe the normal-RPC-fault
  encoding this plan moves it to, so the public docs don't go stale.
- All non-`integration`/`xmpp`-marked tests pass (`uv run pytest tests/ -m "not integration and not
  xmpp"`: 1969 passed). `ruff check` and `black --check` clean on every touched file; `pyrefly
  check` reports 0 errors on the three touched source files.
- `rpc.py`'s `_on_jabber_rpc_error` fix for `condition == "forbidden"` (mapping to `ForbiddenError`
  + `call_id`) was applied but **not independently verified reachable** — per the design section,
  it's believed dead for this condition specifically (slixmpp's own `Iq.send()` future wins the
  race). Left in as cheap defensive coverage; worth a live-ejabberd check before claiming it's
  load-bearing, not before shipping it.

## Rollout

Pure `pyobs-core` internal change; no public API signature changes. Wire-protocol change: an ACL
denial now arrives as a normal RPC `<fault>` (`iq type="result"`) instead of an
`iq type="error"`/`condition="forbidden"`. Mixed-version safe in both directions:

- An **old server** talking to a **new client**: client's `xmppcomm.py`/`rpc.py` fallback paths
  (improved, not removed, by this plan) still handle the raw `forbidden` IQ error correctly.
- A **new server** talking to an **old client**: old client's existing `condition == "forbidden"`
  handling no longer fires (server stopped sending it), but the old client's generic `IqError`
  handling in the `except Exception`-shaped catch-all... actually doesn't apply here — a fault is
  never an `IqError` in the first place, old or new. An old client already knows how to parse a
  normal `<fault>` (that mechanism isn't new), it just resolves to whatever `ForbiddenError`
  registration it has locally (fine, it's been in `exceptions.py` a while) — no compatibility gap
  in this direction either.

Rollback is reverting the diff in `module.py`/`rpc.py`/`xmppcomm.py`.
