# Plan: Comm.unregister_event() cancels already-scheduled handler tasks (#871)

Status: implemented

Issue: pyobs-core#871

## Problem

`Comm._send_event_to_module()` (`pyobs/comm/comm.py:678-693`) dispatches an event to each
registered handler by calling it to get a coroutine, then fire-and-forgets it via
`asyncio.create_task(ret)`. `create_task()` only schedules the coroutine — it doesn't run it
inline. If a handler's owner is torn down and calls `unregister_event()` in the same synchronous
stretch, before the scheduled task gets a turn, `unregister_event()` (`comm.py:458-485`) removes
the handler from `self._event_handlers` but has no record of the task already created for it. The
task still runs later, against whatever the handler is bound to.

Observed in pyobs-gui: `DataDisplayWidget._on_new_data` (a `NewImageEvent`/`NewSpectrumEvent`
handler, `pyobs_gui/datadisplaywidget.py:175`) touches `self.checkAutoUpdate` after the widget was
discarded on client disconnect, raising `RuntimeError: libshiboken: Internal C++ object
(PySide6.QtWidgets.QCheckBox) already deleted`. `_log_handler_exception` already catches and logs
this, so it isn't fatal, but it's log noise masking a real dispatch-ordering bug — and the same
race applies to any handler bound to an object destroyed on teardown.

## Design

Track in-flight dispatch tasks per `(event_class, handler)` and cancel them in
`unregister_event()`:

- Add `self._event_handler_tasks: dict[tuple[type[Event], Callable], set[asyncio.Task[Any]]] = {}`
  to `Comm.__init__`.
- In `_send_event_to_module()`, after `asyncio.create_task(ret)`, add the task to
  `self._event_handler_tasks.setdefault((event.__class__, handler), set())`, and have the existing
  `add_done_callback` (still calling `_log_handler_exception`) also discard the task from that set
  and remove the set once empty, so the dict doesn't grow unbounded over a long-running module.
- In `unregister_event()`'s existing per-`ev` loop (the one that mirrors `register_event()`'s
  derived-event expansion, `comm.py:474-480`), when a handler is actually removed for a given
  `ev`, pop `self._event_handler_tasks.get((ev, handler))` and cancel every task still pending —
  keying by the same `ev`, not the outer `event_class`, so a handler registered against several
  derived event types only loses tasks for the type actually being unregistered.
- Cancellation is `task.cancel()`, not awaiting it — `unregister_event()` doesn't need to block on
  the handler unwinding, and `_log_handler_exception`'s existing `task.cancelled()` check already
  no-ops for cancelled tasks.

No change to `register_event()`, `_register_events`/`_unregister_events` (XMPP pubsub
subscription teardown), or any other `create_task` site — `comm.py:83` and `comm.py:145` are
unrelated one-shot tasks, and this is the only fire-and-forget dispatch loop in the module.

## Testing

`tests/comm/test_comm.py` (or wherever `Comm` unit tests live):

- Register an async handler that raises if called, dispatch an event via
  `_send_event_to_module()`, immediately call `unregister_event()` before yielding control to the
  event loop (no `await` in between), then let the loop run one tick — assert the task was
  cancelled and the handler body never actually ran.
- A handler still registered for a *different* derived event type keeps its pending task when one
  event type is unregistered (keying-by-`ev` isn't overbroad).
- Existing dispatch/exception-logging tests continue to pass unchanged (`_log_handler_exception`
  behavior for non-cancelled exceptions is untouched).

## pyobs-gui note

The issue cites `StatusItem._state_subscriptions` and `MainWindow.discard_all_widgets()` as prior
workarounds for this race. Checked: only `discard_all_widgets()`/`BaseWidget.discard()`
(`pyobs_gui/base.py:260-293`, `pyobs_gui/mainwindow.py:712-727`) are on the affected event path,
and neither is removable — they're what calls `unregister_event()` at all. This fix just drops the
requirement that they run strictly before Qt destroys the widget. `_state_subscriptions`
(`pyobs_gui/statuswidget.py:304-321`) is unrelated — state updates dispatch synchronously, no
`create_task` involved — so it stays untouched. No pyobs-gui code changes follow from this plan;
at most a docstring update once pyobs-gui is pinned to a release with this fix.

## Rollout

Pure `pyobs-core` internal change, no public API change (`unregister_event()`'s signature is
unchanged). No server or XMPP protocol impact. Rollback is reverting the `comm.py` diff.
