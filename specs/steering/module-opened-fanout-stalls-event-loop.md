# `_on_module_opened`'s unthrottled per-peer fan-out can saturate a client's event loop

Same underlying principle as
[blocking-sdk-calls-must-not-run-on-the-event-loop.md](blocking-sdk-calls-must-not-run-on-the-event-loop.md)
and [astropy-iers-event-loop-stalls.md](astropy-iers-event-loop-stalls.md) -- something eating
event-loop time without yielding -- but here the culprit isn't one blocking call, it's an
unthrottled N-fold burst of otherwise-normal async work, all landing in the same few seconds.
Documented separately because it's now been confirmed twice, in two different shapes, on two
different sites, and the first occurrence was closed as a site-specific mitigation rather than
fixed at the root.

## The mechanism

`Module._on_module_opened` (`pyobs/modules/module.py:431`) is registered by *every* module
(`pyobs/modules/module.py:338`) and reacts to a synthesized `ModuleOpenedEvent`. `XmppComm._got_online`
(`pyobs/comm/xmpp/xmppcomm.py`, presence handler) fires that event locally
(`xmppcomm.py:755`) for **every** peer whose presence arrives -- not just a genuinely-new
connection. Per normal XMPP/shared-roster semantics, a client that just connected gets its already-online
peers' presence pushed to it immediately, all at once. So a module (or the GUI) joining a fleet of
N already-online peers fires `_on_module_opened` N times, back to back, essentially concurrently.

Each firing does `async with self.proxy(sender, IModule) as proxy: ...`
(`module.py:438`), and if this is the first time that peer's proxy is being built,
`Comm._get_client` (`pyobs/comm/comm.py:114`) does real work per peer: a disco#info interfaces
fetch, a background capabilities fetch, and a pubsub state-subscribe for every stateful interface
that peer implements. None of this is individually wrong or unbounded in isolation -- it's the
**lack of any stagger/throttle across peers** that turns "N peers online" into "N concurrent
fetch-and-subscribe sequences," all sharing one XMPP connection and, for any single-threaded async
client, one event loop.

## Confirmed twice, same root cause, different symptom

**iag50 production (2026-07 investigation, see
[`specs/plans/2026-07-22-ejabberd-throughput-benchmarking.md`](../plans/2026-07-22-ejabberd-throughput-benchmarking.md)):**
a *module* (not GUI) joining a stable ~7-8 peer fleet reliably triggered a full capability-fetch
cascade -- `XmppComm._get_capabilities` got no reply for the full 10s timeout, three attempts in a
row, for every pair involving the newcomer. The plan was closed 2026-08-03 as "out of scope": "all
systems running fine in production; the iag50 shaper mitigation held." That mitigation is
operational (ejabberd-side traffic shaping on that one host), not a pyobs-core code change -- the
unthrottled fan-out in `_on_module_opened`/`_get_client` itself was never touched.

**pyobs-gui on `monet` (2026-09-02, this investigation):** the GUI (as `admin@monet.saao.ac.za`)
joining a **38**-peer fleet showed no failures, but a live ejabberd debug capture (`ejabberdctl
set_loglevel debug`, tailed during a live repro) showed a continuous flood of disco#info responses,
RPC responses, and pubsub `headline` state-update messages arriving from dozens of peers, sustained
for **over a minute** after connect. pyobs-gui runs Qt and asyncio on one shared loop
(`qasync.QEventLoop`, `pyobs_gui/gui.py`), and slixmpp parses/dispatches every incoming stanza on
that same loop, sequentially. A widget's own RPC call (e.g. `IModule.get_permitted_methods()`,
`pyobs_gui/base.py:407`) can arrive on the wire quickly and still sit queued for several seconds
behind that backlog -- confirmed by re-issuing the same call a second time immediately after
(fast, 0.2-0.4s) versus the first (5-7s), and by `module.py:205`'s `_watch_event_loop_lag`
watchdog (ADR
[0009](../adrs/0009-event-loop-lag-watchdog-lives-on-module-not-comm-or-application.md))
firing repeatedly during that window regardless of which widget the user happened to open first.

Same mechanism, different N and different transport pattern (module-to-module RPC timeouts vs.
single-process event-loop saturation), because pyobs-gui and a regular pyobs `Module` both go
through the identical `_on_module_opened`/`_get_client` path -- pyobs-gui has no special-cased
startup logic here, it just happens to also be a `pyobs.comm.Comm` client with a Qt UI sharing its
loop, which makes the same underlying burst user-visible as a frozen GUI instead of a background
log warning.

## How this was found (this occurrence)

1. GUI-side timing: instrumented `TelescopeWidget.open()`/`_init()` and
   `base.py::_fetch_permitted_methods()` with `time.monotonic()` around every `await`, narrowing
   the ~7-10s freeze down to one call (`get_permitted_methods()`), then to "first call only" by
   firing a second, throwaway call to the same method against the same module immediately after
   (fast).
2. Ruled out the client-side RPC library and pyobs's own handler code by reading
   `pyobs/comm/xmpp/rpc.py`'s `RPC.call()` and slixmpp's `xep_0009` plugin end to end -- no lazy
   first-call setup, no retry/backoff anywhere in that path.
3. Ruled out application-level logs on both ends: the telescope module's own log and ejabberd's
   default (`info`) log are both silent for ordinary RPC/stanza routing -- neither is instrumented
   for this.
4. `ejabberdctl set_loglevel debug` + a live filtered `tail -f` (started *before* the repro, since
   the debug-level log volume on this fleet evicts its own tail within about a minute -- a
   retrospective `grep` after the fact came back empty) caught the actual stanza flood in real
   time and made the mechanism visible directly, not inferred from timing alone.

## Fix status: not yet fixed

Neither occurrence has a code fix in pyobs-core. Options, not yet decided or attempted:

- Stagger/throttle `_on_module_opened`'s reaction to a burst of presence arrivals (e.g. a small
  per-newcomer queue with concurrency limit, rather than firing all N handlers unbounded).
- Rate-limit `Comm._get_client`'s per-peer fetch-and-subscribe sequence across concurrent callers.
- For pyobs-gui specifically: nothing GUI-side can fix the underlying fan-out, since the flood is
  legitimate traffic from `_on_module_opened`'s design, not a GUI bug -- any GUI-side mitigation
  (e.g. deferring widget-driven RPC calls until the initial connect burst has settled) would only
  paper over the symptom for this one client.

Until fixed, expect any pyobs client (module or GUI) joining a fleet above roughly 7-8 already-online
peers to show *some* symptom of this -- timeouts, elevated latency, or (for single-loop UI clients)
a visible freeze -- proportional to fleet size at connect time.
