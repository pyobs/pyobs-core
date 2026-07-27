# Plan: Systematic ejabberd throughput/latency benchmarking

Status: draft — headline number known, original methodology unrecoverable
Repos: pyobs-brot (the reconnect-storm investigation below concerns BrotDome/BrotRaDecTelescope
production behavior on pyobs-iag50)

**The magnitude is known: simultaneous state pushes took ~15x longer than sequential ones.** That
draft/test run was done on another machine and isn't retrievable — not in this repo, not in
session memory beyond the headline ratio, nor in `specs/design/pyobs_2_0_wire_protocol.md` (which
has a *different*, unrelated concurrency measurement: 5 simulated devices, `gather` vs. sequential,
0.5s vs 0.1s — not ejabberd, not state pushes). The remaining "Prior finding" checklist items below
are **not going to be recovered by more digging** — either they're recalled directly, or they stay
unknown and the scenarios below need to be run fresh to get real, reproducible numbers rather than
trying to match an unrecoverable prior run.

## Blockers found while getting the environment working (2026-07-27)

Getting *any* scenario runnable surfaced three real, previously-undiscovered problems, in order —
each one hid the next, because CI has never actually run these tests (see below):

1. **Fixed, pushed (`efca1f75`).** `ejabberdctl`'s `CTL_ON_CREATE` never fired: `ejabberd/ecs:latest`
   ships with `/home/ejabberd/database` (its Mnesia `SPOOL_DIR`) already present in the image layer,
   so the `FIRST_RUN` check ejabberdctl gates `CTL_ON_CREATE` on is always false, even in a brand-new
   container. `tests/xmpp/docker-compose.yml` now uses `CTL_ON_START` instead (runs unconditionally
   every start, not gated on `FIRST_RUN`), with each `register` command prefixed `!` so a
   "already registered" conflict on restart is logged and ignored instead of halting the whole
   ejabberd node.
2. **Fixed, committed and pushed to `develop` (`efca1f75`).** `pyobs/comm/xmpp/xmppcomm.py` set
   `unencrypted_scram` for non-TLS connections but never `unencrypted_plain`. Confirmed via isolated
   raw-slixmpp reproduction: SCRAM mechanisms fail unencrypted against ejabberd 26.4.0 with "Invalid
   channel binding", and without `unencrypted_plain` slixmpp refuses to even attempt PLAIN over a
   plaintext connection — so every non-TLS connection exhausted all mechanisms and failed with "No
   appropriate login method" / "Invalid credentials". This is why *no* xmpp-marked integration test
   could ever have passed against a fresh local ejabberd before this fix.
3. **Fixed, in `tests/xmpp/ejabberd.yml` / `docker-compose.yml`.** With (1) and (2) fixed, all 30
   xmpp-marked integration tests still failed (42 non-xmpp tests passed), but with a *different*
   symptom: no more auth errors, instead `"camera" in observer_comm.clients"` never became true
   (e.g. `test_xmpp_acl.py::test_acl_deny_forbids_call`). Isolated with a raw two-client slixmpp
   reproduction: `send_presence()` (no `to` attribute) is only echoed back to the sender's own
   resource — the other party never received it at all. Root cause: peer discovery in `XmppComm`
   depends entirely on receiving the other party's presence broadcast, which per XMPP spec requires
   a roster subscription (or a server-side shared-roster-group policy) between the two JIDs — and
   neither existed: `tests/xmpp/ejabberd.yml` loaded bare `mod_roster: {}` with no shared-roster-
   group config, and `xmppcomm.py` never sends or auto-accepts subscription requests.
   - Fixed server-side: `ejabberd.yml` now also loads `mod_admin_extra` (needed to expose the
     `srg_*` ejabberdctl commands at all) and `mod_shared_roster`, and `docker-compose.yml`'s
     `CTL_ON_START` runs `srg_create all localhost all all all` +
     `srg_user_add @all@ localhost all localhost` — putting every registered user in one shared
     roster group (`@all@` is ejabberd's wildcard for "all registered users on this host"), so they
     see each other's presence with no explicit subscription needed. Both commands are idempotent
     on rerun (unlike `register`), so no `!` prefix needed for those two.
   - Verified with the raw two-client presence reproduction (both sides now receive each other's
     presence) and with the full suite: **72 passed** (`pytest -m integration`, clean run, no manual
     intervention).
   - Still an open design question for *production* pyobs deployments, not just this test fixture:
     this only works because the test ejabberd is fully owned by pyobs's own accounts. A real
     observatory's ejabberd server would need the same shared-roster-group (or equivalent) set up by
     whoever administers it — `xmppcomm.py` never sends/auto-accepts subscription requests itself,
     so peer discovery has an undocumented server-config dependency beyond just "run ejabberd".
     Worth a follow-up: either document this requirement prominently, or move the fix client-side
     (`XmppComm` sending/auto-approving subscription requests) so it works against any standard
     ejabberd deployment with zero special config.
   - Aside: **CI's "Integration Tests" workflow has never actually exercised any of this.** Every run
     back through the workflow's history shows `72 skipped, 1323 deselected` — all of `-m
     integration` skipped in one shot, including tests with no xmpp dependency at all
     (`test_astroplanscheduler.py` etc.), despite the workflow setting `PYOBS_TEST_XMPP_HOST:
     localhost`. Not yet diagnosed why *non-xmpp* integration tests are skipped in CI when they
     aren't locally — a separate mystery from the three blockers above, flagged but not investigated.

All three environment blockers are now resolved — scenario 1 (and the rest) can actually be run.

## Prior finding

- [x] What "slower" meant concretely: aggregate wall-clock time for a batch of concurrent pushes
      vs. the same batch done sequentially — **~15x** worse for the concurrent case.
- [ ] Exact scenario: how many concurrent pushes, to how many distinct PubSub nodes, what payload?
- [ ] Precise numbers behind the 15x ratio (absolute latencies, not just the ratio).
- [ ] Was concurrency via `asyncio.gather` on one client, or multiple independent clients/modules
      publishing at the same time?
- [ ] Local docker-compose ejabberd, or a different (production-like?) server?
- [x] Any hypothesis already formed. The shaper hypothesis was tested and **refuted** — see
      "First real results" below: the shaper is not the mechanism.

## First real results (2026-07-27)

Ran `scripts/xmpp/benchmark_state_throughput.py` against all three shaper configs (default
3k/20k, 10x 30k/200k, fast-track 100k/no-cap — a 33x rate spread with one variant having no burst
cap at all). Local docker-compose, single container, `EJABBERD_HOST_PORT=25222` (see Environment
above). Raw per-message JSONL + full command log not committed (ephemeral local run) — numbers
below are the aggregated summary.

**The shaper hypothesis is refuted.** `concurrent-single` (one client, N=500 publishes fired via
`asyncio.gather`) gives statistically indistinguishable results across all three shaper configs:

| shaper config        | mean latency | p95    | aggregate wall time |
|-----------------------|-------------:|-------:|---------------------:|
| default (3k/20k)      |      329.9ms | 353.8ms | 0.64s |
| 10x (30k/200k)        |      346.0ms | 362.4ms | 0.64s |
| fast-track (100k/none)|      355.5ms | 376.5ms | 0.66s |

A 33x sustained-rate difference and removing the burst cap entirely produced no measurable
improvement. Whatever causes concurrent per-message latency to balloon at N=500, it isn't
ejabberd's c2s shaper — something else (client-side `_safe_send`/gather scheduling, slixmpp's IQ
result-callback handling, or server-side non-shaper PubSub/Mnesia serialization) is the real
mechanism. Not yet root-caused; a fresh investigation should start from there, not from the shaper.

**The original "concurrent ~15x slower in aggregate" framing doesn't reproduce either** — at
N=500 under any shaper config, `concurrent-single`'s *aggregate* wall time (0.64-0.66s) was
actually *faster* than `sequential`'s (0.95-1.09s for the same N), not slower. What's dramatically
worse for concurrent is *per-message* latency (mean ~330-355ms vs. sequential's ~1.5ms — a ~220x
per-message ratio), not the aggregate batch completion time the original observation was framed
around. This is a real, reproduced effect, just not the effect originally described — worth
keeping the distinction sharp: concurrent bursts pay dramatically worse tail latency per message
(classic head-of-line queuing signature) while the batch as a whole may finish comparably fast or
faster than doing the same N sequentially.

Effect only shows up at scale: at N=30 or N=100, `concurrent-single` mean latency (22.8ms, 60.2ms)
was nowhere near the N=500 numbers (~330ms+) — whatever the mechanism, it has a threshold/scaling
behavior worth characterizing (binary search between 100 and 500 would narrow it down).

`concurrent-many` (5 independent clients, N=30 each = 150 total), `sequential` (small/large
payload), and `rpc-baseline` all came back consistent and unremarkable across all three shaper
configs (single-digit-to-low-double-digit ms means) — no shaper sensitivity there either at these
scales.

## Deeper dig: isolating the real mechanism (2026-07-27, same day)

Went past the harness script to raw slixmpp reproductions (bypassing `XmppComm` entirely) to rule
candidate mechanisms in or out one at a time. Each step's result is what motivated the next step:

1. **pyobs's own code is not the cause.** A raw slixmpp script (no `XmppComm`, no `_safe_send`, no
   module wrapper — just `xep_0060.publish()` in a loop vs. via `asyncio.gather`) reproduces the
   same effect at the same magnitude (N=500 concurrent: mean 274.2ms, vs. sequential's 1.0ms).
   Whatever this is, it's in slixmpp's IQ handling and/or ejabberd's pubsub processing, not in
   pyobs's retry/module-wrapper logic.
2. **Scaling is worse than linear.** Per-item cost (wall time / N) at N=200/500/1000/3000:
   0.45ms → 0.68ms → 0.89ms → 2.29ms. Item cost keeps growing as N grows — not a fixed per-message
   overhead.
3. **Not same-node Mnesia contention.** Publishing all N items to one shared pubsub node vs. N
   distinct auto-created nodes barely changed anything (274ms → 232ms at N=500) — nowhere near
   ruling this in as the dominant mechanism.
4. **Not per-connection/session serialization either.** Splitting the same N=500 total across 2
   independent client connections (camera + observer, each firing 250 concurrently, both bursts
   running at the same time) gave per-connection means of 275ms and 219ms — essentially the same
   magnitude as one connection doing all 500, not the ~60-70ms you'd expect if halving the
   per-connection burst size linearly halved the effect. Two independent sessions don't insulate
   each other from whatever this is, so it isn't ejabberd doing one-process-per-c2s-session
   serialization.
5. **Not CPU-bound on either side.** During a long burst (N=3000, 6.9-8.1s wall), `docker stats`
   on the ejabberd container showed mostly near-0% CPU with occasional brief spikes (80-255%) —
   not a sustained compute bottleneck. Client-side `ps` sampling during the same burst showed the
   Python process at 0.4-1.5% CPU throughout — also not compute-bound. Both sides are mostly
   *idle*, not busy, while wall time balloons.
6. **Definitively not the shaper, even at N=3000.** Re-ran the raw N=3000 concurrent burst under
   the fast-track config (100000 B/s, no burst cap, camera specifically exempted from the throttled
   `normal` shaper) — result was statistically identical to the default (most restrictive) shaper:
   6.91s wall / 5330.6ms mean vs. default's 6.88s / 5343.1ms. A config with literally no rate cap
   produces the same multi-second delay as one capped at 3000 B/s. This closes the door on the
   shaper hypothesis at any scale tested, not just N=500.
7. **The original "concurrent slower in aggregate" framing *does* reproduce, at large enough N.**
   At N=3000: sequential wall time 2.71s (mean 0.9ms/item, flat) vs. concurrent wall time 6.88-6.91s
   (mean ~5.3s/item) — concurrent is now ~2.5x slower in aggregate, not faster as it was at N=500.
   So there's a real crossover somewhere between N=500 and N=3000 where concurrent bursts stop being
   an aggregate-throughput win and start being a net loss too, on top of the per-message latency
   that was already bad at N=500.

**Root cause confirmed**: it's client-side, CPU-bound, and quadratic. (The "TCP/asyncio
backpressure" idea floated in an earlier pass of this doc was wrong — see below for what
disproved it.)

Re-checked CPU on the client process specifically (the earlier "both sides mostly idle" reading was
a mistake — `ps`/`top` had latched onto the wrong PID, the `uv run` wrapper, not the actual `python3`
interpreter). Sampling the correct PID during an N=3000 burst shows it **pegged at 100% of one core
for the entire multi-second burst**, not idle at all.

That points straight at slixmpp's own stanza dispatch. `slixmpp/xmlstream/xmlstream.py:1434`:

```python
matched_handlers = [h for h in self.__handlers if h.match(stanza)]
```

Every `Iq.send()` registers a fresh one-shot handler matched by IQ id (`stanza/iq.py`'s
`Iq.send()`, `MatcherId`). `__handlers` is a plain per-connection Python list, and *every incoming
stanza* is dispatched by linearly scanning the *entire* list for a match. With N publishes fired
concurrently, up to N handlers are registered and pending at once — so each of the N incoming
replies costs an O(N) scan (checked against the full backlog, most of it not yet resolved), and N
replies × O(N) each is O(N²) total, done in Python, on the single-threaded asyncio event loop.
Nothing about the network, the server, or the shaper is involved — it's a linear-search-over-a-list
bug (well, design limitation — a dict keyed by IQ id would be O(1) per lookup instead) in slixmpp's
core dispatch path, triggered by having many IQs in flight on one connection at once.

This is a clean, complete explanation for every earlier observation: reproduces without pyobs code
(core slixmpp), grows worse than linearly with N (genuine O(N²), not a fixed overhead), doesn't
care about shaper config (the client's own CPU is the bottleneck, ejabberd barely gets a vote), and
splitting N across 2 connections in the *same process* only halved the work rather than eliminating
it (each connection's own `__handlers` list is smaller, but it's still the same one OS thread
grinding through the combined O((N/2)²) × 2 total comparisons).

**Confirmed and fixed.** Patched a fork (`~/code/3rdparty/slixmpp`, branch
`fix-o2-iq-handler-dispatch`) with exactly this: an id-keyed dict fast path for
`MatcherId`/`MatchIDSender` handlers in `register_handler`/`remove_handler`/`_spawn_event`. Re-ran
the same benchmarks with the patched slixmpp swapped into pyobs-core's venv (editable install,
`uv run --no-sync`): per-item cost went from growing with N (0.68ms → 2.29ms at N=500 → 3000, the
O(N²) signature) to flat (~0.45-0.50ms regardless of N) — genuinely O(N) now. ~2x faster at N=500,
~7.4x faster at N=3000. Full `pytest -m integration` suite (72 tests) still passes against the
patched fork — no correctness regression.

Filed upstream: [poezio/slixmpp#3786](https://codeberg.org/poezio/slixmpp/issues/3786).

**Practical implication for the wire protocol doc**: firing a large number of concurrent publishes
from a *single* connection is where this bites (`concurrent-single`); spreading the same total load
across independent connections (`concurrent-many`, one per module — already how the fleet model
works) stayed fast and unremarkable throughout every test in this session, and now we know why:
each connection's own O(N²) is bounded by its own (small, per-module) N, not the fleet's total
message count. The realistic fleet scenario (many modules, each its own connection, each publishing
at its own pace) doesn't hit this at all — it's specifically "one module bursting
hundreds-to-thousands of concurrent state pushes from itself on one connection" that's expensive,
which is an unusual pattern for a single device to begin with and not something the current design
does anywhere.

## Conclusion on the O(N²) finding: real bug, not a pyobs design problem

Filed upstream: [poezio/slixmpp#3786](https://codeberg.org/poezio/slixmpp/issues/3786), with a
draft fix and before/after numbers. Maintainer response was constructive; asked how many handlers
are actually registered under typical (non-benchmark) load, since the O(N²) cost only bites once
that count gets large.

Checked with a real client (not the synthetic burst script): a normal camera+observer session doing
sequential, human-cadence operations sits at a flat **~33 handlers** throughout — fixed plugin
registration overhead, not growing during normal use, since sequential/awaited IQs resolve before
the next one is sent (0-1 in flight at a time).

Also checked against a real production fleet: `pyobs-monet/config/south/` has ~30-35 distinct
module configs (one connection each, all on one ejabberd domain) — a real "fleet size" comparable
to the wire protocol doc's assumed 10-100 agents. Grepped `pyobs_monet`'s module code for
`asyncio.gather`-based concurrent state pushes or IQ bursts: **none found**.

Put together, this clarifies something worth stating plainly: **the bug is per-connection, not
fleet-size.** `__handlers`/`__id_handlers` are `XMLStream` instance attributes with zero sharing
across connections — the O(N²) cost depends only on how many IQs are in flight *on one connection
at once*, never on how many other connections exist elsewhere. A fleet of many well-behaved modules
(pyobs's actual design, and what the real MONET-south deployment runs) never touches this, because
no module fires a concurrent burst on its own connection — confirmed both by the `concurrent-many`
benchmark scenario (fast throughout every test this session) and by the real fleet's code having no
such pattern anywhere.

So: **this doesn't affect current pyobs usage, and isn't a reason to change the wire protocol
design.** It was still worth chasing down, for three reasons that held before we knew the answer:
it was explicitly on this benchmark plan's checklist (goal #4, confirm-or-refute the earlier "~15x
slower" observation); the leading hypothesis at the time (ejabberd's shaper) would have been
fleet-relevant had it been confirmed, so it had to be tested rather than assumed away; and an
unexplained 15x regression sitting under the wire protocol doc's unmeasured "XMPP scales fine"
assumption was worth resolving either way. The resolution is a real, previously-unknown library bug
(reported upstream, with a fix), not a pyobs design risk — a genuinely useful outcome, just not the
kind that changes this repo's code. If pyobs ever does need one module to fire many concurrent
state pushes at once (not true of anything today), the mitigation would be a client-side
concurrency cap (a semaphore around `set_state()`/`_safe_send()`), not a wire-protocol change.

## New scenario: reconnect-storm (2026-07-27, production incident follow-up)

**Motivation.** A production incident on `pyobs-iag50`: 3 modules (`telescope`, `imagewatcher`,
`imagewriter` — not a whole-fleet restart, and no BROT/MQTT-backed module involved on the
`imagewatcher`/`imagewriter` side) restarted within a few seconds of each other. Disco#info
(XEP-0030) capability-fetch queries between them (`Comm._get_client` → `_fetch_and_update_capabilities`
→ `XmppComm._get_capabilities`, triggered by the first proxy lookup between two modules) got no reply
at all for a full 10s timeout, three attempts in a row, for multiple module pairs — despite every peer
already being fully started (`Started successfully` logged) several seconds *before* the first fetch
attempt, ruling out "peer still booting." A per-module event-loop-lag watchdog (added to `Module`
specifically to catch a blocking call stalling one module's own comms) was confirmed present and
silent throughout, on both sides of one failing pair — ruling out a client-side stall as the cause too.

**Added `run_reconnect_storm`** (`scripts/xmpp/benchmark_state_throughput.py`): K independent clients
connect/auth/bind/publish-presence all at once (`asyncio.gather`), then every client fetches `IModule`
capabilities from every other client at once — modeling the connection-churn shape of the incident
(a handful of modules restarting together, immediately followed by mutual capability discovery), not a
whole-fleet burst and not a hardware/MQTT angle (ruled out already by the production log evidence
above).

**Local result (`--k 4`, fresh docker-compose ejabberd, single run):** 4 clients connected+ready in
1.33s, then 12 mutual capability fetches completed in 0.02s total (mean 19.4ms, max 21.7ms, 0 failed).
Does **not** reproduce the production silent-timeout behavior at this scale locally — this exact
connection-churn shape is fast and reliable against a fresh local ejabberd. Useful negative result:
whatever caused the incident isn't an inherent property of "a few clients reconnect and immediately
query each other" in general, so it's more likely specific to the production environment (real network
latency/config to `iag50srv`, its particular ejabberd version, load at that moment, or a stale-session/
routing race from the restart — see the open question already flagged elsewhere in this doc about
production peer-discovery/roster-subscription assumptions) than a universal client-library behavior.
**Next step, if pursued:** run the same scenario against `iag50srv` itself during a no-ops window —
production owner confirmed this is acceptable — to see whether it reproduces there where it didn't
locally.

### Full incident timeline and what's been ruled out (2026-07-27)

Written up in full because the next step (below) runs on a different computer than this
investigation happened on — nothing here should need to be re-derived from scratch.

**What happened.** On `pyobs-iag50` production, a handful of modules restarted within a few
seconds of each other. Two separate occurrences were observed:
- `dome`/`BrotDome` + `scheduler` + `autofocus` + `acquisition`/`mastermind` (larger batch, exact
  count unclear)
- `telescope`/`BrotRaDecTelescope` + `imagewatcher` + `imagewriter` (confirmed exactly 3 modules,
  **not** a whole-fleet restart, and no BROT/MQTT-backed module on the `imagewatcher`/`imagewriter`
  side)

In both cases, `xmppcomm.py:1020` logged `"Still failing to get capabilities for <IModule|IConfig>
from <peer> after 3 attempts (TimeoutError()), will keep retrying"` — the underlying mechanism is
`Comm._get_client` → `_fetch_and_update_capabilities` → `XmppComm._get_capabilities`, triggered by
the first proxy lookup between two modules (fires once per newly-created `Proxy`, for every
interface with `capabilities is not None` that the peer implements — `IModule`/`IConfig` always
qualify since every `Module` publishes both). `_get_capabilities` retries forever by design
(`asyncio.wait_for(get_info(...), timeout=10.0)` per attempt, capped exponential backoff between
attempts, only warns at attempt 3 — see ADR 0008), so the warning means 3 real 10-second timeouts
elapsed with **no server reply at all**, not that anything took 30 seconds to arrive late.

**Ruled out, with direct evidence, in this order** (each bullet is a real check performed, not just
a hypothesis floated):

1. **Peer still booting.** Working backward from the warning timestamp through the retry/backoff
   math (~10s × 3 attempts + ~1-4s backoff between each ≈ 33-35s total), the first fetch attempt for
   the `telescope`/`imagewatcher` incident had to have started around `18:02:37-39`. Both `telescope`
   (`Started successfully` at `18:02:29`) and `imagewatcher` (`18:02:32`) were already fully up several
   seconds before that. Ruled out.
2. **Client-side event-loop stall.** Added `Module._watch_event_loop_lag` (`pyobs/modules/module.py`)
   specifically to catch a blocking call freezing one module's own comms -- it times its own wakeups
   against how long it asked `asyncio.sleep()` for, so a synchronous block anywhere in that process
   delays its own wakeup right along with everything else and shows up retroactively. Logs once when
   a stall starts and once when it clears (not per check, to avoid spamming a sustained-but-
   fluctuating overload). Confirmed present in `imagewatcher`'s log (listed among cancelled
   background tasks at shutdown, alongside `_worker`/`_watch_inotify`) and **completely silent**
   through the entire incident window on both sides of the `telescope`↔`imagewatcher` pair. Ruled out.
3. **Inherent XMPP/slixmpp slowness.** Already measured in this doc (see "First real results" /
   "Deeper dig" above): realistic fleet traffic sits at low-single-digit-to-low-double-digit ms
   latency. A genuine 10s silent gap is ~1000x that baseline. Ruled out as "XMPP is just slow."
4. **A whole-fleet reconnect storm** (the scenario `_get_capabilities`'s retry-forever design and
   ADR 0008 explicitly target: "every module in the fleet reconnecting to ejabberd at once"). Only
   3-4 modules restarted, not the whole fleet -- too small an event to plausibly overload ejabberd the
   way "every module in the fleet at once" would. Weakened/ruled out as sufficient explanation on its
   own.
5. **Two BROT modules contending for the same MQTT broker on reconnect** (an earlier theory, once it
   looked like `dome` and `telescope` -- both BROT-backed, each opening their own independent
   `MQTTTransport`/`BROT()` connection at `open()` -- had restarted together). Directly contradicted:
   the `telescope` incident's restart set was confirmed to be `telescope` + `imagewatcher` +
   `imagewriter` -- `dome` was never restarted, and `imagewatcher`/`imagewriter` have no BROT/MQTT
   involvement at all. Ruled out.
6. **The `reconnect-storm` benchmark scenario itself, run locally** (see above): 4-5 clients
   connecting simultaneously then immediately firing mutual capability fetches, against a fresh
   docker-compose ejabberd, completed in ~20-45ms mean with zero failures. Does not reproduce the
   silent-timeout behavior at this scale locally.

**A real, separate bug *was* found and fixed along the way, but it is not the explanation for this
pattern:** `pybrotlib`'s `MQTTTransport.run()` subscribed to the MQTT wildcard `"#"` (every topic on
the broker, not just the dome's/telescope's own component) and processed each message with no
`await` in between -- a queued backlog (e.g. after a reconnect) could run through many messages
back-to-back without ever yielding to the event loop, which *could* have explained the earlier `dome`
incident. Fixed by adding `await asyncio.sleep(0)` after each message (`pybrotlib` 1.1.5,
`BROTLib/pyBROT@a104fe1`); `pyobs-brot`'s dependency floor bumped to match. Confirmed still running
`pybrotlib` 1.1.5 when the `telescope`/`imagewatcher`/`imagewriter` incident recurred -- so whatever
this second incident's cause is, it isn't this bug (which is also irrelevant to `imagewatcher`/
`imagewriter` anyway, since neither uses `pybrotlib` at all).

**Key remaining fact: the same kind of setup (BROT-backed telescope module + imaging modules, one
ejabberd fleet) works fine on `pyobs-monet`'s south site, but fails on iag50.** Combined with
everything ruled out above, this weighs heavily toward something specific to iag50's ejabberd
server/config/network -- e.g. a stale-session/routing race on restart, since every module reconnects
with the same fixed resource (`.../pyobs`, not randomized per connection) -- rather than a universal
client-library or pyobs-core/pyobs-brot code bug. If it were the latter, monet-south should show the
same symptom and doesn't.

### Runbook for tomorrow: run `reconnect-storm` against both `iag50srv` and monet-south

**Goal:** determine whether the `reconnect-storm` scenario (which came back clean locally) reproduces
the silent-capability-timeout behavior against either real server, and specifically whether it
reproduces on iag50 but not monet-south -- which would confirm "iag50-specific" as more than a
plausibility argument.

**Safety:** confirmed acceptable to run against both live production servers during a no-ops window
(no active observations). Uses throwaway `bench<N>` account names throughout, never the real module
JIDs (`telescope@...`, `imagewatcher@...`, etc.), so it can't collide with or interfere with anything
the real fleet is doing even outside a no-ops window -- but stick to the no-ops window anyway since
it's still real traffic against a server real operations depend on.

**Connection details** (from each repo's own shared comm config -- both use TLS, unlike this repo's
local test ejabberd):
- iag50: `domain: iag50srv.astro.physik.uni-goettingen.de` (`pyobs-iag50/config/iag50srv/comm.shared.yaml`)
- monet-south: `domain: monet.saao.ac.za` (`pyobs-monet/config/south/monet/comm.shared.yaml`,
  commented-out server hint: `monet.monets:5222`)
- Real account passwords aren't in either repo's checked-in config (only test/dummy passwords are
  committed anywhere) -- get the real ones separately before running; `PYOBS_TEST_XMPP_PASSWORD` is
  shared by every `bench<N>` account the script registers, so one password covers a whole run.

**Registration gotcha, already fixed:** the original `--register-via <container>` only knew
`docker exec <container> ejabberdctl register ...`, which assumes a dockerized ejabberd -- not a safe
assumption for a real production server. `register_accounts`/`maybe_register` now also support
`--register-via local`, which runs bare `ejabberdctl register ...` directly (needs `ejabberdctl` on
PATH -- run the script on the ejabberd host itself, or wherever has that binary and reaches the
server). Verified this refactor doesn't break the existing docker-based path (re-ran the local
docker-compose smoke test after the change, k=5, 20 fetches, 44.1ms mean, 0 failed).

**Commands** (run from a machine that can reach each server -- confirmed this will be a different
computer than this session):

```bash
# against iag50
PYOBS_TEST_XMPP_HOST=iag50srv.astro.physik.uni-goettingen.de \
PYOBS_TEST_XMPP_DOMAIN=iag50srv.astro.physik.uni-goettingen.de \
PYOBS_TEST_XMPP_PORT=5222 \
PYOBS_TEST_XMPP_TLS=1 \
PYOBS_TEST_XMPP_PASSWORD=<real password for bench accounts> \
python scripts/xmpp/benchmark_state_throughput.py reconnect-storm --k 4 \
    --register-via local --output iag50_reconnect_storm.jsonl

# against monet-south (same shape, different host/domain)
PYOBS_TEST_XMPP_HOST=monet.saao.ac.za \
PYOBS_TEST_XMPP_DOMAIN=monet.saao.ac.za \
PYOBS_TEST_XMPP_PORT=5222 \
PYOBS_TEST_XMPP_TLS=1 \
PYOBS_TEST_XMPP_PASSWORD=<real password for bench accounts> \
python scripts/xmpp/benchmark_state_throughput.py reconnect-storm --k 4 \
    --register-via local --output monet_south_reconnect_storm.jsonl
```

Match `--k` to the real incident shape (3-4) rather than pushing for scale -- this is a targeted
reproduction attempt, not a throughput ceiling test. Re-run a few times if the first attempt doesn't
show anything; the original incident may depend on timing/load conditions that don't hold on every
single run.

**What would actually settle this:**
- **Reproduces on iag50, clean on monet-south:** confirms iag50-specific (server config/network/
  stale-session-routing), not a `pyobs-core`/`pyobs-brot` code bug. Next step would be ejabberd's own
  server-side logs/session table on iag50 around the reproduction, not more client-side code changes.
- **Clean on both real servers too:** the local negative result generalizes -- whatever caused the
  original incident either needs a condition this scenario still doesn't capture (different timing,
  real fleet load at that moment, something about the *actual* restart sequence beyond "a few clients
  connect and query each other"), or was a one-off. Worth getting the exact ejabberd version/config
  from both sites to compare before concluding it's unreproducible.
- **Reproduces on both:** points back toward something in `pyobs-core`'s XMPP layer after all,
  and the "works fine on monet-south" premise from real operation would need re-examining --
  maybe monet-south just hasn't had 3-4 modules restart together recently, rather than being immune.

## Problem

There is currently no empirical throughput or latency data for pyobs's XMPP/PubSub transport.
`specs/design/pyobs_2_0_wire_protocol.md` assumes XMPP scales fine for a fleet of "10–100 agents"
(line 20) and leans further into PubSub for state (the whole "state/event model" section, lines
55-245+) without any measured numbers backing the assumption. Decisions that doc already makes or
will need to make — state-push frequency (e.g. `ITemperatures` sensors ticking every few seconds),
one PubSub node per interface per module (fan-out at fleet scale), RPC-vs-state boundaries for
status data — should be informed by real numbers, not intuition. The informal "concurrent pushes
are slower than sequential" observation is exactly the kind of thing that should either become a
documented, reproducible finding that shapes the protocol design, or get discarded if it doesn't
reproduce under a controlled test.

## Goals — questions this benchmark should answer

1. **Sustained throughput.** How many state-push messages/sec can a single client publish? How does
   aggregate throughput scale with number of concurrently-publishing clients (1, 5, 10, 25, 50, 100 —
   the fleet-size range the wire protocol doc already assumes)?
2. **Publish latency.** Round-trip time for a `set_state()` call (XEP-0060 `publish` IQ, awaited to
   ack) — mean/median/p95/p99/max, both at low load and at/near saturation.
3. **RPC latency** (XEP-0009, `execute()`) under the same load conditions — directly relevant to the
   wire protocol doc's "RPC overuse for status" concern (line 57): if state traffic degrades RPC
   latency, that's a real argument for the state/event model beyond just "fewer round trips."
4. **Concurrent vs. sequential, reproduced.** Fire N publishes via `asyncio.gather` vs. N publishes
   awaited one at a time — confirm or refute the earlier observation, and at what N (if any) does
   concurrency stop winning.
5. **PubSub node fan-out cost.** Publishing/subscribing across many distinct nodes (one per
   interface per module, as currently designed) vs. fewer nodes carrying more data — is per-node
   overhead measurable at fleet scale, or negligible?
6. **Payload size sensitivity.** Small state (e.g. `RunningState`, one bool) vs. larger state (e.g.
   a synthetic `TemperaturesState` with many `SensorReading`s) — separates serialization cost from
   fixed IQ/transport overhead.

## Non-goals

- Production ejabberd tuning — a possible follow-up once numbers exist, not part of this plan.
- Benchmarking `LocalComm` (in-process, not the transport in question).
- Re-litigating the wire protocol's XML encoding choice — already decided in the design doc; this
  is purely about connection/PubSub mechanics, not payload format.

## Test design

### Environment

- Baseline: the existing `tests/xmpp/docker-compose.yml` / `tests/xmpp/ejabberd.yml` — single
  container, already used by the `-m xmpp` integration suite, so results are reproducible by anyone
  running this repo.
- **Shaper defaults checked (2026-07-27) via `ejabberdctl dump_config` against the running
  `ejabberd/ecs:latest` (26.4.0) test container.** Confirmed `tests/xmpp/ejabberd.yml` was relying
  on ejabberd's built-in default: `shaper.normal = {rate: 3000, burst_size: 20000}`, and
  `shaper_rules.c2s_shaper = {none: admin, normal: all}` — since neither `camera` nor `observer`
  (the test accounts) is `admin@localhost`, every benchmark client is throttled to 3000 B/s
  sustained with only a 20000-byte burst allowance. At the time this was a strong, concrete
  candidate mechanism for the earlier 15x concurrent-vs-sequential finding — **since refuted by
  actual measurement, see "First real results" below**: a 33x rate spread across all three shaper
  configs produced no measurable difference in the observed concurrent-latency effect.
  - Made explicit in `tests/xmpp/ejabberd.yml` (was implicit) so the baseline is visible and
    reproducible rather than a silent default. This one stays under `tests/xmpp/` since it's the
    config the `-m xmpp` integration suite also loads.
  - The shaper *variants* below are benchmark-only (never used by the pytest integration suite), so
    they live under `scripts/xmpp/` next to the harness script itself, not `tests/xmpp/`:
    - `scripts/xmpp/ejabberd-shaper-10x.yml` (rate 30000, burst_size 200000 — 10x default, matching
      the multiplier the user runs in their own production ejabberd deployments) +
      `scripts/xmpp/docker-compose.shaper-10x.yml`.
    - `scripts/xmpp/ejabberd-fast-shaper.yml` — default rate values, but adds a `benchmark_clients`
      ACL (`camera@localhost`, `observer@localhost`) and routes it to the `fast` shaper (100000 B/s,
      no burst cap) instead of `normal`, via `shaper_rules.c2s_shaper: {none: admin, fast:
      benchmark_clients, normal: all}` + `scripts/xmpp/docker-compose.fast-shaper.yml`. Tests
      whether simply exempting benchmark clients from the throttled c2s track (as a production
      deployment might via ACL) removes the concurrent-vs-sequential slowdown — independent of, and
      complementary to, the 10x-rate question.
    - All three configs verified live (2026-07-27) via `ejabberdctl dump_config` against a
      throwaway container — each produces the expected effective `shaper`/`shaper_rules`/`acl`.
  - **Invocation order matters**: relative bind-mount paths in an override resolve against the
    *first* `-f` file's directory, so always pass `tests/xmpp/docker-compose.yml` first, the
    override second, e.g. from repo root:
    `docker compose -f tests/xmpp/docker-compose.yml -f scripts/xmpp/docker-compose.shaper-10x.yml up -d`
  - **Host port conflict**: this dev machine already runs an unrelated local ejabberd bound to host
    5222 — the benchmark must not touch it. `tests/xmpp/docker-compose.yml`'s port mapping is now
    `${EJABBERD_HOST_PORT:-5222}:5222` (defaults unchanged for CI/other users); set
    `EJABBERD_HOST_PORT=25222` (verified free) before `up` when 5222 is already taken locally, and
    point `PYOBS_TEST_XMPP_PORT`/the benchmark script's connection config at the same port.
  - **Benchmark plan now runs every scenario under all three shaper configs** (default 3k/20k
    normal-track, 10x 30k/200k normal-track, default-rate fast-track) to separate "shaper-throttling
    artifact" from "inherent XMPP/PubSub concurrency cost" — see Scenarios below.
- `docker-compose.yml`'s `CTL_ON_CREATE` currently registers only `camera` and `observer`
  (`tests/xmpp/docker-compose.yml:8-10`). A multi-client scenario needs N accounts — either extend
  `CTL_ON_CREATE` with a generated list, or register accounts programmatically via `ejabberdctl
  register` in the benchmark's own setup step.
- Flag explicitly in the results write-up: local single-container docker-compose numbers are a
  starting point, not necessarily representative of a production ejabberd deployment (different
  hardware, network latency, TLS, real shaper config). Re-running against a staging/production-like
  server, if one is available, is worth doing before numbers go into the wire protocol doc as
  load-bearing.

### Harness location

New script(s) under `scripts/xmpp/`, alongside the existing `list_pubsub_nodes.py` /
`check_ejabberd_notify.py` / `show_module_info.py` (`scripts/xmpp/`, added in 4bfec0c4) — matches
existing precedent for standalone XMPP tooling that isn't part of the pytest suite.

**Built**: `scripts/xmpp/benchmark_state_throughput.py` (2026-07-27). Implements sequential,
concurrent-single, concurrent-many, rpc (baseline and under concurrent-many background load), and
payload-size-sweep scenarios; JSONL output tagged with `--shaper-label`; `--register-via
<container>` auto-registers the extra `bench<N>` accounts concurrent-many/rpc need beyond
camera/observer. Smoke-tested live against a throwaway container — every scenario runs cleanly
end-to-end (`sequential`, `concurrent-single`, `concurrent-many`, `rpc`, `rpc --rpc-with-load`,
`payload`, `all`). Passes `black`/`ruff`/`pyrefly` clean. Not yet run for real, load-bearing numbers
across all three shaper configs — that's the next step, not part of building the harness itself.

Deliberately **not** added as a `pytest -m xmpp` integration test: these are long-running,
resource-heavy runs meant to be triggered manually and produce a data file for analysis, not fast
pass/fail assertions that should run in CI on every push. Reuse the *connection* logic from
`tests/integration/conftest.py` (`make_unopened_comm`/`make_xmpp_comm` patterns, `XmppConfig` env
vars) rather than duplicating it, but the script itself lives outside `tests/`.

### Measurement approach

Time around the public API (`comm.set_state(...)`, `proxy.execute(...)`) rather than reaching into
`XmppComm` internals (`_set_state`, `_safe_send`) — this measures what a real caller actually
experiences, including any queuing/retry inside `_safe_send`
(`pyobs/comm/xmpp/xmppcomm.py:919-924`), rather than an idealized lower bound.

```python
start = time.perf_counter()
await comm.set_state(SomeInterface, some_state)
latency = time.perf_counter() - start
```

### Scenarios

Run scenarios 1-3 (at minimum) under **all three** shaper configs, restarting the container with the
appropriate compose override between runs:

1. `tests/xmpp/ejabberd.yml` — default, normal-track (3000 B/s / 20000 B burst).
2. `scripts/xmpp/ejabberd-shaper-10x.yml` — 10x, normal-track (30000 B/s / 200000 B burst, matching
   production).
3. `scripts/xmpp/ejabberd-fast-shaper.yml` — default rates, but benchmark clients routed to the
   `fast` shaper (100000 B/s, no burst cap) instead of `normal`.

Tag every recorded data point with which shaper config produced it. Configs 1 vs. 2 isolate whether
raising the *rate* fixes it; 1 vs. 3 isolates whether simply moving clients off the throttled c2s
track fixes it. Together they answer whether the 15x concurrent-vs-sequential effect is
shaper-throttling at all (ratio should shrink or vanish under 2 and/or 3) or something else (ratio
persists regardless of shaper config).

1. **Sequential baseline.** One client, N publishes (to N distinct nodes, i.e. N different
   interfaces/modules — avoid conflating "same node repeatedly" with "realistic fleet traffic"),
   awaited one at a time. Record per-publish latency distribution and effective throughput
   (N / total wall time).
2. **Concurrent, single client.** Same client, same N publishes, fired via `asyncio.gather`. This is
   the scenario to directly compare against #1 for the "concurrent vs sequential" question.
3. **Concurrent, many clients.** K independent clients (each its own `XmppComm` connection, its own
   asyncio task), each publishing sequentially, all running at the same time. This is the realistic
   "fleet of modules each doing their own thing" case — distinct from #2 (one client bursting) and
   probably the more important number for the wire protocol doc's 10-100 agent assumption.
4. **RPC latency under state-traffic load.** Baseline RPC round-trip latency with no background
   traffic, then again while scenario 3 runs concurrently in the background — isolates whether state
   push volume degrades RPC responsiveness.
5. **Payload size sweep.** Repeat scenario 1 with a minimal state (`RunningState`) and a larger one
   (synthetic `TemperaturesState` with, say, 50 `SensorReading`s) to separate serialization cost
   from fixed per-publish overhead.

### Output

Each run appends raw per-message timings (timestamp, scenario, concurrency level, payload size,
latency) to a CSV/JSON file, plus a printed summary (mean/median/p95/p99/max latency, msgs/sec
throughput). Keep raw data, not just aggregates, so results can be re-plotted or re-analyzed without
re-running against a live server.

## What this feeds into

- Concrete numbers for `specs/design/pyobs_2_0_wire_protocol.md` to cite, replacing the current
  unqualified "10-100 agents, XMPP is fine" assumption with an actual measured envelope.
- Either reproduces the earlier "concurrent slower than sequential" finding with real numbers and a
  plausible mechanism (shaper throttling, connection-level head-of-line blocking, server-side pubsub
  contention — scenario 2 + the shaper check above should distinguish these), or shows it doesn't
  reproduce under a controlled test, in which case it should stop informing design decisions.
- If a real ceiling turns up well below fleet-scale needs (10-100 agents × several state-bearing
  interfaces each, some ticking every few seconds), that's a concrete, numbers-backed motivation for
  a follow-up wire-protocol change (batching/coalescing state updates, a different QoS for
  high-frequency sensor data) rather than a speculative one.

## Open questions

- Target environment: local docker-compose only, or also a staging/production-like ejabberd?
  (Needed before treating local numbers as load-bearing for the wire protocol doc.)
- Is "10-100 agents" (from the wire protocol doc) still the right ceiling to size scenario 3
  against, or is there a firmer real fleet-size number to test to?
- Constraints on run duration / how disruptive this can be — should stay confined to the disposable
  docker-compose instance and never point at a real observatory's live ejabberd server, unless
  explicitly intended as a one-off validation run.
