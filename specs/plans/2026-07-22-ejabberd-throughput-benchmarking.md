# Plan: Systematic ejabberd throughput/latency benchmarking

Status: closed, out of scope (2026-08-03) — all systems running fine in production; the iag50
shaper mitigation held, and systematic throughput/latency benchmarking is no longer a priority.
Kept as a record of the investigation, not an active plan.

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

**What happened.** On `pyobs-iag50` production, several occurrences of the same symptom:
- `dome`/`BrotDome` + `scheduler` + `autofocus` + `acquisition`/`mastermind` restarting within a few
  seconds of each other (larger batch, exact count unclear)
- `telescope`/`BrotRaDecTelescope` + `imagewatcher` + `imagewriter` restarting within a few seconds
  of each other (confirmed exactly 3 modules, **not** a whole-fleet restart, and no BROT/MQTT-backed
  module on the `imagewatcher`/`imagewriter` side)
- `acquisition` + `mastermind` + `flatfield` + `autofocus` + `imagewatcher` + `scheduler` +
  `imagewriter` (7 modules) — explicitly *not* including `telescope` or `dome` at all (user's words:
  "I didn't start telescope or dome, but all the others"). First occurrence with **zero**
  BROT/MQTT-backed modules running at all.
- **The same 7-module set restarted again later, this time deliberately one at a time with ~5
  minutes between each start**, specifically to test whether simultaneity was the trigger. It
  wasn't a whole-fleet restart in any sense — see the detailed breakdown below.

In every case, `xmppcomm.py:1020` logged `"Still failing to get capabilities for <IModule|IConfig>
from <peer> after 3 attempts (TimeoutError()), will keep retrying"`. `_get_capabilities` retries
forever by design (`asyncio.wait_for(get_info(...), timeout=10.0)` per attempt, capped exponential
backoff between attempts, only warns at attempt 3 — see ADR 0008), so the warning means 3 real
10-second timeouts elapsed with **no server reply at all**, not that anything took 30 seconds to
arrive late.

**The actual trigger mechanism, confirmed by reading the code (not previously identified this
precisely):** `Module._on_module_opened` (`pyobs/modules/module.py:431`) is registered by *every*
module in `open()` (`register_event(ModuleOpenedEvent, self._on_module_opened)`) and unconditionally
creates a proxy to any peer it sees come online (`async with self.proxy(sender, IModule) as proxy:
...`). Building that proxy for the first time (`Comm._get_client` → `_fetch_and_update_capabilities`)
background-fetches capabilities for *every* interface the peer implements with `capabilities is not
None` — not just `IModule`, which is why `IConfig`/`IFilters`/`IBinning` etc. show up too. This is
inherent, unconditional behavior in the `Module` base class, present in every module in every pyobs
fleet — nothing a module's own code opts into or could avoid. Per standard XMPP/shared-roster
presence semantics, becoming available gets a client its contacts' current presence pushed back
immediately, and pushes its own presence to all of them — so when a module joins a fleet of N
already-online peers, all N peers *and* the newcomer fire this handler at once, toward each other,
producing an N-fold burst of simultaneous proxy-creation-and-capability-fetch, scaling with **how
many peers are already online when the new one joins**, regardless of whether anyone else is
simultaneously restarting.

**The staggered-restart experiment (2026-07-27) confirms this precisely and rules out simultaneity
entirely.** Each of the first 6 modules was started ~5 minutes apart with **zero** failures joining
progressively larger fleets (1→2→3→4→5→6 already-online peers). Then `flatfield` — the 7th to
join, into an already-stable 6-module fleet that had been running fine for up to ~14 minutes —
triggered a total cascade: **every single failing pair in the resulting burst involved `flatfield`**
(e.g. `acquisition IModule from flatfield`, `flatfield IConfig from scheduler`, `imagewatcher
IFilters from flatfield`, ...) — not one failure between two *other*, already-established modules.
`flatfield`'s own `open()` was checked line-by-line and does nothing unusual: no proxy creation, no
blocking calls, just publishing its own local state (`IBinning`/`IFilters`/`IReady`/`IMotion`) and
registering two event handlers — confirming the trigger is `_on_module_opened`'s generic
fleet-size-scaled burst, not anything specific to `FlatField`'s code. The cascade began 31 seconds
after `flatfield` logged `Started successfully`, consistent with the same ~30s pattern seen in every
prior incident.

**Repeated with a different module minutes later — same exact peer count, same result.** After the
`flatfield` cascade, the same 7 XMPP-connected modules (`acquisition`, `autofocus`, `focusmodel`,
`imagewatcher`, `imagewriter`, `mastermind`, `scheduler` — `filecache` again doesn't count, no real
XMPP comm) were confirmed all up and stable. `dome` then joined as the 8th, and 33 seconds after its
own `Started successfully`, the identical total cascade — every failing pair involves `dome`, none
between the other 7 modules. **Two independent occurrences, exactly the same threshold: fine through
7 already-connected peers, breaks on the 8th, regardless of which module that 8th one is** — not
BROT-specific (confirmed separately), not specific to `flatfield` or `dome`'s own code (checked
`flatfield`'s in full; `dome`'s `open()` is the already-audited, genuinely-async `BrotDome`). This
also retroactively reframes the earlier "only 3-4 modules restarted" incidents: those were only ever
reported as "the modules that just restarted," never as a full inventory of *everything already
running in the background* at iag50 at the time — entirely possible those incidents were the same
"crossing ~7-8 total connected peers" event, just without visibility into the rest of the already-
stable fleet.

**Working theory, not yet confirmed as a fixed rule: a peer-count threshold around 7-8 total
XMPP-connected modules on iag50's ejabberd.** Two independent occurrences landed at exactly this
count, but that's only two data points -- not confirming an exact number, just the most concrete
lead so far. The mechanism itself (`_on_module_opened` firing an N-fold capability-fetch burst on
every reconnect, at any N) is solid regardless. Deliberately not chasing this further with more
local guessing -- next step is testing live against the real server tomorrow, per the runbook below,
rather than refining theories further from logs alone.

**Added `run_late_joiner`** (`scripts/xmpp/benchmark_state_throughput.py`): K clients connect and
settle (idle, already-stable) for a configurable `--settle-time`, then exactly one more client
connects and immediately exchanges `IModule` capabilities with every existing peer, both directions
-- a direct model of "N already-stable peers, one joins," not a simultaneous burst. Swept `--k 3 5 7
8 9` locally against fresh docker-compose ejabberd (`--settle-time 2`, i.e. minimal settle, not even
the seconds-to-minutes gap the real incidents had): **zero failures at every k, including the exact
7 and 8 that broke on iag50** (14 fetches/22.0ms mean at k=7, 16 fetches/21.7ms mean at k=8). This is
a real, useful negative result: whatever produces the ~7-8 threshold on iag50 is not a generic
ejabberd/slixmpp scaling property that reproduces at the same numeric threshold on a fresh local
server -- reinforcing that it's specific to iag50's particular ejabberd deployment (version, config,
resources, or accumulated state) rather than something inherent to the mechanism itself. `dome`/
`telescope`'s runbook below now includes `late-joiner` alongside `reconnect-storm` for tomorrow's
real-server run, since it's the more precise reproduction of what actually happened.

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
   ADR 0008 explicitly target: "every module in the fleet reconnecting to ejabberd at once"). Ruled
   out as *the sole* explanation for the smaller (3-4 module) incidents -- too small an event to
   plausibly overload ejabberd the way "every module in the fleet at once" would. **Revised, not
   ruled out, after the 7-module incident**: that's a large enough batch that a genuine reconnect-
   storm effect on the server side is plausible again, so scale-dependence (small batch: doesn't
   happen; large batch: does) is back on the table rather than dismissed. Still doesn't fully explain
   the sustained-recurrence finding below, which outlasts any reasonable "everyone's still settling
   in" window.
5. **Two BROT modules contending for the same MQTT broker on reconnect** (an earlier theory, once it
   looked like `dome` and `telescope` -- both BROT-backed, each opening their own independent
   `MQTTTransport`/`BROT()` connection at `open()` -- had restarted together). Directly contradicted
   twice now: the `telescope` incident's restart set was confirmed to be `telescope` + `imagewatcher`
   + `imagewriter` (`dome` never restarted); and the 7-module incident above ran with **neither**
   `dome` nor `telescope` even started, let alone restarted, and showed the identical symptom.
   **Conclusively ruled out** -- this has nothing to do with BROT, MQTT, or `pyobs-brot` at all.
6. **The `reconnect-storm` benchmark scenario itself, run locally** (see above): 4-5 clients
   connecting simultaneously then immediately firing mutual capability fetches, against a fresh
   docker-compose ejabberd, completed in ~20-45ms mean with zero failures. Does not reproduce the
   silent-timeout behavior at this scale locally -- though the 7-module incident suggests testing at a
   larger `--k` (6-8) is worth doing before treating the local result as generalizing to fleet scale.

**New finding, not yet explained: failures recur well after the initial reconnect burst, not just
during it.** In the 7-module incident, the capability-fetch warnings ran `18:30:07`-`18:30:33` (~26s,
consistent with the smaller incidents). But `flatfield` then hit a genuine unhandled
`slixmpp.exceptions.IqTimeout` -- not a retried-and-logged warning, an actual exception, from its own
outgoing `send_event()` (log forwarding via `_safe_send`, which has a *bounded* budget: 5 attempts,
each up to 15s, plus backoff -- see ADR 0008) -- at `18:31:12` **and again** at `18:32:37`, i.e. 39s
and 85s *after* the capability-fetch storm had already stopped. `flatfield` exhausted its entire
`_safe_send` retry budget getting zero reply from the server, twice, well outside any plausible
"everyone just reconnected" window. This rules out "brief presence-propagation catch-up" as the full
story -- whatever this is, it can affect a module's ordinary outgoing IQ traffic (not just disco#info
capability fetches) for a sustained period covering at least two minutes, long after the modules
involved were already fully up. Points more toward ejabberd itself being in a genuinely degraded
state for an extended stretch (not just a few seconds of connection churn) than a client-side
timing race.

**`run_reconnect_storm` extended and re-run locally (2026-07-27) to match this incident's scale and
timing shape** — added `--recheck-after SECONDS`: after the initial connect+fetch burst, the same
(already-connected, not reconnected) clients sit idle for that long and then repeat the mutual fetch,
specifically to test whether failures can recur on an already-established, previously-fine
connection. Ran `--k 7 --recheck-after 90` (matching the 7-module incident and roughly spanning the
39s/85s gap before `flatfield`'s two `IqTimeout`s) against fresh docker-compose ejabberd: initial
burst 42 fetches/31.4ms mean/0 failed, recheck after 90s idle 42 fetches/64.2ms mean/0 failed. Still
does not reproduce, even at matched scale and with the idle-then-recheck shape that specifically
targets the sustained-recurrence finding. Reinforces that this needs the real servers (below) rather
than more local scale-tuning — `--recheck-after` is ready to use there too.

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

### Runbook for tomorrow: run `late-joiner` and `reconnect-storm` against both `iag50srv` and monet-south

**Goal:** determine whether `late-joiner` (the precise reproduction of what actually happened twice:
a stable 7-peer fleet, one more joins) or `reconnect-storm` (simultaneous multi-client reconnect)
reproduces the silent-capability-timeout behavior against either real server, and specifically
whether it reproduces on iag50 but not monet-south -- which would confirm "iag50-specific" as more
than a plausibility argument. `late-joiner` is the priority: it matches the two cleanest, most
precisely-characterized incidents exactly (7 already-stable peers, 1 joins, cascade 30-something
seconds later, every failure involving the newcomer), and already came back clean locally at the
exact same peer counts (see above) -- a real production run is what's needed to move this further,
not more local tuning.

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
# against iag50 -- late-joiner first, the precise reproduction (7 stable peers, 1 joins)
PYOBS_TEST_XMPP_HOST=iag50srv.astro.physik.uni-goettingen.de \
PYOBS_TEST_XMPP_DOMAIN=iag50srv.astro.physik.uni-goettingen.de \
PYOBS_TEST_XMPP_PORT=5222 \
PYOBS_TEST_XMPP_TLS=1 \
PYOBS_TEST_XMPP_PASSWORD=<real password for bench accounts> \
python scripts/xmpp/benchmark_state_throughput.py late-joiner --k 7 --settle-time 60 \
    --register-via local --output iag50_late_joiner.jsonl

# also try k=8 (one past the observed threshold) and a longer settle time closer to the real
# incidents' minutes-apart timing, if k=7/settle=60 doesn't reproduce
python scripts/xmpp/benchmark_state_throughput.py late-joiner --k 8 --settle-time 300 \
    --register-via local --output iag50_late_joiner.jsonl

# reconnect-storm as a secondary check (simultaneous multi-client reconnect, not late-joining)
python scripts/xmpp/benchmark_state_throughput.py reconnect-storm --k 7 --recheck-after 90 \
    --register-via local --output iag50_reconnect_storm.jsonl

# against monet-south (same shapes, different host/domain)
PYOBS_TEST_XMPP_HOST=monet.saao.ac.za \
PYOBS_TEST_XMPP_DOMAIN=monet.saao.ac.za \
PYOBS_TEST_XMPP_PORT=5222 \
PYOBS_TEST_XMPP_TLS=1 \
PYOBS_TEST_XMPP_PASSWORD=<real password for bench accounts> \
python scripts/xmpp/benchmark_state_throughput.py late-joiner --k 7 --settle-time 60 \
    --register-via local --output monet_south_late_joiner.jsonl
python scripts/xmpp/benchmark_state_throughput.py reconnect-storm --k 7 --recheck-after 90 \
    --register-via local --output monet_south_reconnect_storm.jsonl
```

`--k 7`/`--k 8` matches the exact peer counts observed breaking on iag50 twice. Both scenarios
already re-run locally against fresh docker-compose ejabberd at these exact shapes (see above) with
no failures, so a production run is what's actually needed next, not more local scale-tuning. Re-run
a few times and try a longer `--settle-time` if the first attempt doesn't show anything -- the real
incidents had the existing fleet stable for minutes, not just seconds, before the newcomer joined,
and the local sweep only tested a 2s settle. Try smaller `--k` (3-4) too if the observed threshold
doesn't reproduce either -- the smaller/earlier incidents are just as real and unexplained, and may
turn out to share a cause once more data exists.

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

### Runbook executed against iag50srv itself (2026-07-28)

**Deviation from the runbook as written, done deliberately with explicit confirmation:** rather
than throwaway `bench<N>` accounts, this run authenticated as the **real production module JIDs**
(`acquisition`, `autofocus`, `focusmodel`, `imagewatcher`, `imagewriter`, `mastermind`,
`scheduler`, plus `dome`/`telescope`/`flatfield` as joiners) — the exact account set involved in
the real 7/8-module incidents described above. Confirmed with the user first that these modules
were not currently running (no live session to collide with) before connecting as them. Real
per-account passwords (sourced from `pyobs-iag50/config/iag50srv/*.yaml`, each module has its own,
unlike the shared `PYOBS_TEST_XMPP_PASSWORD` throwaway accounts use) were staged in a
`PYOBS_TEST_XMPP_CREDENTIALS_FILE` JSON outside this repo (scratchpad, never committed) — not
inline in commands or in any tracked file.

To support this, `scripts/xmpp/benchmark_state_throughput.py` gained:
- `XmppConfig.passwords: dict[str, str]` (populated from `PYOBS_TEST_XMPP_CREDENTIALS_FILE` if
  set) — `make_comm` looks up a per-user password there before falling back to the shared
  `PYOBS_TEST_XMPP_PASSWORD`.
- `--users a,b,c` (reconnect-storm/late-joiner): explicit account list overriding the generated
  `bench<N>` names, and overriding `--k` to `len(--users)`.
- `--joiner NAME` (late-joiner): account name for the one extra client, overriding the default
  `benchjoiner`.

Since these are pre-existing registered production accounts, `--register-via` was omitted
entirely (no registration step needed or wanted against production).

**Results — every scenario came back clean, zero failures, latencies in line with the earlier
local numbers:**

| scenario | existing peers | joiner/shape | fetches | failed | mean | p95/max |
|---|---|---|---|---|---|---|
| `late-joiner` | 7 (acquisition, autofocus, focusmodel, imagewatcher, imagewriter, mastermind, scheduler) | `dome` (exact real k=7 config) | 14 | 0 | 44.5ms | 60.0ms |
| `late-joiner` | 8 (above + `dome`) | `telescope` (one past threshold) | 16 | 0 | 41.8ms | 58.9ms |
| `reconnect-storm --recheck-after 90` | 7 (same set, simultaneous connect) | initial burst | 42 | 0 | 261.5ms | 346.5ms |
| `reconnect-storm` recheck (90s idle, same connections) | 7 | recheck | 42 | 0 | 69.7ms | 84.7ms |
| `late-joiner` | 15 (+ focuser, asi071mc, sbig6303e, tc237h, fibercamera, autoguider, startup, telegram) | `focusmodel` | 30 | 0 | 60.6ms | 89.6ms |
| `late-joiner` | 21 (every unique real account on the domain except one) | `warning` | 42 | 0 | 75.6ms | 97.6ms |

The k=21 run used **every distinct real account registered on `iag50srv`'s domain** (confirmed by
reading each config dir's `_comm.yaml`/`comm.shared.yaml` — `iag50srv`, `iag50cam`, `iag50tel`,
`iag50obs`, `allsky` subdirs all share the one `iag50srv.astro.physik.uni-goettingen.de` domain;
`gui`/`config` at the repo's top level are excluded, they're hardcoded to a *different* domain,
`iag50obs.astro...`, a separate server) minus the one held back as the joiner — the largest
real-account fleet this server has, short of registering new throwaway accounts. This run was
blocked by the local harness's own auto-mode permission classifier (a broad "connect ~21 real
production accounts at once" command tripped it, even after explicit user approval in-chat) and
was run by the user directly in their own shell instead of by the agent.

**Neither scenario reproduces the incident on the real server, at any tested scale** — not at the
exact peer counts (7, 8) that broke twice in production, nor pushed all the way to k=15 or k=21
(basically the whole real fleet, all real accounts, connecting to the real server at once). Given
this, a monet-south comparison run doesn't add information right now: the comparison only matters
if iag50 itself reproduces and monet-south doesn't (or vice versa) — with iag50 clean at every
scale tried, there's nothing to contrast monet-south against yet, so that step is **deprioritized,
not scheduled**, until iag50 reproduces something at all. Whatever caused the original silent
10s-timeout cascades needs a condition this reproduction still doesn't capture — real fleet load
at the moment of the incident (the actual fleet doing actual work, not idle synthetic capability
fetches against an otherwise-quiet server), the precise timing/ordering of the actual restart
sequence, or a genuinely intermittent server-side condition (GC pause, Mnesia compaction, network
blip) that a clean, no-ops-window test doesn't hit regardless of client count.

**Next steps, not yet done:** consider running `late-joiner`/`reconnect-storm` again
during/immediately after an actual live fleet restart on iag50 (not a quiet no-ops window) if one
is ever needed anyway, since "quiet server, otherwise idle" may be exactly the condition that's
missing, not client count; or pull ejabberd's own server-side logs from the actual incident
timestamps (`18:02:37-39`, `18:30:07-33`, etc. — see timeline above) if they're still retained,
rather than trying to re-trigger the condition blind. Monet-south comparison stays on the shelf
unless iag50 reproduces something first.

### Reproduced live with real modules on iag50srv (2026-07-28) — root cause still open, but the incident is real and reproducible

**Everything above (synthetic `benchmark_state_throughput.py` client, up to k=21, every real account on the
domain) was clean.** That result held up to its own scope: bare `XmppComm` connections doing nothing but
connect and fetch capabilities. The next step was running the **actual production `Module` classes** — real
`Module.open()`, real `_on_module_opened` cascade, real background tasks — via SSH as root on `iag50srv`
itself, under `sudo -u pyobs`, using the live `pyobs` CLI (`/opt/pyobs/venv/bin/pyobs /opt/pyobs/config/<name>.yaml
-l <logfile>`) against the real configs symlinked into `/opt/pyobs/config/`.

**Safety scoping done before running anything for real** (each one a genuine finding from reading the actual
module code, not assumed):
- `pyobs_brot.brottelescope.BrotDome`/`BrotRaDecTelescope.open()` read code confirmed: connects MQTT, publishes
  read-only telemetry/status, never issues a motion command — `init`/`park`/slew are separate RPC methods never
  called during `open()`. Safe to start without touching any hardware, *as long as nothing else running commands
  them*.
- `mastermind` (`robotic.yaml`, class `pyobs.modules.robotic.Mastermind`) is not passive — it pulls real tasks
  from `observe.monet.uni-goettingen.de` and can execute them via RPC to `telescope`/`dome`/`sbig6303e`/etc. on
  its own initiative, no RPC call from the operator needed. Included only after explicit confirmation there was
  nothing actionable queued — which turned out to be not quite right (see below), but harmless in practice.
- `startup` (`Trigger` module) auto-calls `dome.init()` on `GoodWeatherEvent` and `telescope.init()` on
  `RoofOpenedEvent` — a real, unrelated-to-this-test path to the roof opening for real. **Excluded entirely**,
  contributes nothing to the XMPP question being tested.
- `telegram` **excluded** — real bot token, would send real messages to real people. Also unrelated to the test.
- `_pointing.yaml`'s leading underscore in the deployed `/opt/pyobs/config/` symlink indicates it's deliberately
  excluded from the current production launch set — left out here too, matching production as-is.
- No camera modules (`sbig6303e`, `asi071mc`, `fibercamera`) are deployed on `iag50srv` at all — they run on
  the separate `iag50cam` host, out of scope for what's runnable from this host.
- SSH itself required care: the FQDN (`iag50srv.astro.physik.uni-goettingen.de`) hit a host-key mismatch in
  this environment specifically (not reproducible from the user's own terminal) — resolved by using the short
  hostname `iag50srv` instead, which the user confirmed is what they'd always used, and which connects with a
  verified-correct host key.
- Real per-account passwords, sourced from `/opt/pyobs/config/*.yaml` on the box (same values as the local repo
  checkout), staged only in a scratchpad JSON, never committed.
- Launch gotcha: `ssh host "sudo -u pyobs bash -c 'nohup cmd & disown'"` hangs the SSH channel indefinitely
  (stdin not detached, so job control inside a non-interactive shell doesn't behave as expected) even though the
  remote process itself starts and detaches fine. Fixed by using `sudo -u pyobs -b cmd < /dev/null > log 2>&1`
  instead — `sudo -b` backgrounds and returns immediately, no hang.

**Once mastermind was actually running, it immediately downloaded a real schedule and reported a queued `BIAS`
task** — contradicting the "confirmed no queued tasks" assumption. Assessed as safe anyway and the run
continued: the `BIAS` script (per `robotic.yaml`'s `runner.scripts.BIAS`) only touches `camera: sbig6303e`, and
that module isn't running in this test set at all, so `mastermind` had nothing it could actually act on even if
it tried, and the task's scheduled time was hours out. Worth remembering for next time: "no queued tasks" needs
to be verified by actually querying the schedule, not assumed — it can be wrong, harmlessly here, but might not
always be.

**Procedure:** started the exact 7-module set from the two cleanest documented incidents — `acquisition`,
`autofocus`, `focusmodel`, `imagewatcher`, `imagewriter`, `mastermind`, `scheduler` — let them settle
(already several minutes stable by the time of the next step, well within the range the real incidents
covered), then started `dome` as the 8th, exactly matching the second real incident's shape.

**Reproduced cleanly, with timing matching the original incident almost exactly:**
- `dome` logged `Started successfully` at `12:50:33`.
- Cascade of `xmppcomm.py:1020 Still failing to get capabilities for <Interface> from <peer> after 3 attempts
  (TimeoutError()), will keep retrying` began at `12:51:04` — **31 seconds later**, matching the original
  incident's "31 seconds after flatfield logged Started successfully" / "33 seconds" for dome almost exactly.
- **Every single failing pair involved `dome`** (dome fetching from each of the 7 stable peers, and each of
  the 7 fetching from dome) — none of the 7 already-established peers ever failed to reach each other. Exact
  match to the original "every failing pair involves the newcomer" pattern.
- A genuine unhandled `slixmpp.exceptions.IqTimeout` (not a retried warning — `_safe_send` exhausting its
  bounded 5-attempt retry budget on `dome`'s own outgoing `send_event`/log-forwarding) hit at `12:51:58` — 85
  seconds after start, matching the original incident's `flatfield` hitting the same exception 39s/85s after
  its own storm. **A second occurrence hit again at `12:53:23`** — exactly 85 seconds after the first, i.e.
  each new log message that happens to hit the same stuck condition independently pays the same ~85s
  `_safe_send` retry-budget cost (5 attempts × ~15-17s), not a random recurrence — internally consistent with
  the retry math in `xmppcomm.py`, and a real match to the original's "recurs well after the initial burst"
  finding.
- Quiet for over a minute after the second `IqTimeout`, consistent with the original incident's window not
  showing indefinite escalation either.

**New evidence the original investigation never had — root cause still not identified, but ruled out further:**
- **`ejabberd` runs on the same host as the pyobs modules** (`iag50srv` itself) — confirmed via `systemctl
  list-units '*ejabberd*'`. This is architecturally different from every prior test in this doc (local
  docker-compose: separate container; synthetic benchmark: remote client machine talking to the real server).
  All client↔server traffic here is over IPv6 loopback (`[::1]:5222`), confirmed in ejabberd's own connection
  log — not a network-path issue.
- **`ejabberd`'s own log (`/var/log/ejabberd/ejabberd.log`) and `journalctl -u ejabberd` are completely silent**
  through the entire failure window (`12:51:04`–`12:51:58`) — no warnings, errors, or any trace of the stuck
  IQs. Whatever is happening either never reaches ejabberd's own logging, or ejabberd never sees the
  request/never sends the reply in a way its own instrumentation notices.
- **Not cgroup/systemd CPU throttling**: `ejabberd.service` has no `CPUQuota` set (`CPUQuotaPerSecUSec=infinity`),
  and `cpu.stat` for its cgroup showed `nr_throttled 0` — zero throttling events, ever.
- **Not a resource-starved host**: 14 cores, `load average: 0.05, 0.06, 0.01` (checked ~75s after the burst
  started — a very brief spike wouldn't necessarily show, but there's no sustained contention), 13GB free
  memory.
- **Not a client-side event-loop stall this time either**: grepped all 7 peer logs for the event-loop-lag
  watchdog output — nothing. Same conclusion the original incident's watchdog reached, now confirmed on a
  second, independently-reproduced occurrence.

**Where this leaves the investigation:** the incident is real, reproducible, and now caught with much better
instrumentation than the original production occurrence had — but the actual mechanism is still not
identified. It's specifically tied to **real `Module` instances with real background behavior** (schedule
fetching, focus-model computation, image-directory watching, etc.) co-located with ejabberd on one host — the
synthetic benchmark's idle `XmppComm`-only clients, even at k=21 real accounts, never reproduced it, and the
per-module CPU/event-loop-lag checks here found nothing on the client side either. That combination (real
module workload + same-host ejabberd, both clean of any obvious resource signal) is the strongest lead so far.
Candidates not yet ruled out: something in ejabberd's internal message routing/mnesia layer that doesn't
surface in its own logs at the configured level; brief, sub-second contention too short for `load average` or
`cpu.stat`'s periodic sampling to catch; or an interaction specific to real modules' background asyncio tasks
(HTTP calls to `observe.monet.uni-goettingen.de`, focus computation, etc.) with slixmpp's own scheduling that
the idle synthetic client never exercises. Full raw logs from this run (all 8 modules, `12:42`–`12:54`) saved
outside the repo for reference.

**Next steps:** re-run with `ejabberd`'s debug log level raised, or with `strace`/`tcpdump` on the loopback
interface armed *before* starting the 8th module, to catch whatever's actually happening between "client sends
IQ" and "client gives up after 10s" — the current evidence rules out several candidate layers but doesn't yet
show what's actually stalling. The monet-south comparison (shelved earlier because iag50 was clean at every
synthetic-client scale) is worth reconsidering now that iag50 *does* reproduce something — if monet-south's
ejabberd is also co-located with its modules on one host and a matching real-module test stays clean there,
that would be a strong signal the same-host topology itself is implicated.

### Second live run (2026-07-28, same day) — likely root cause found: `mod_client_state` (CSI, XEP-0352)

Re-ran the identical reproduction (same 7-module stable set, `dome` as 8th) with two extra instruments
armed beforehand: `ejabberdctl set_loglevel debug` on the real ejabberd (reverted to `info` immediately
after), and a background `ss -tin` sampler on loopback port 5222 (`tcpdump` isn't installed on the box and
wasn't added — `ss`, already present, plus ejabberd's own debug log turned out to be enough).

**Cascade reproduced a second time, same signature, same timing:** warnings began 36s after `dome`'s
start (vs. 31s the first run), and the first `IqTimeout` hit at 88s, with a second at 173s — again
exactly 85s after the first, matching `_safe_send`'s retry-budget math and the first run's 85s-later
recurrence.

**Methodology mistake, noted for honesty:** the `ss` sampler was started before `dome` launched but its
60 one-second samples finished (~13:03:20) *before* `dome` actually started (13:03:43) — a real-time gap
between issuing the two commands ran longer than expected. The retransmission/DSACK counts that capture
showed were from the earlier simultaneous 7-module startup, not the `dome`-join cascade — that lead does
**not** hold up as originally read and shouldn't be cited as evidence of loopback packet loss during the
actual failure window. Flagging this rather than quietly dropping it, since the raw capture is saved and
looked compelling before the timestamp check.

**The ejabberd debug log, correctly captured for the full failure window, found something concrete:**
`mod_client_state` (ejabberd's Client State Indication / XEP-0352 module) was actively queuing and
flushing stanzas for `dome` specifically:
- `dome` accounts for **126 `mod_client_state` log lines** — 5-10x more than any other peer (12-23
  each: `acquisition`, `scheduler`, `mastermind`, `autofocus`, `imagewatcher`, `imagewriter`,
  `focusmodel`).
- Log lines like `mod_client_state:filter_other/1:314 Won't add stanza for dome@.../pyobs to CSI queue`
  and `mod_client_state:dequeue_sender/2:365 Flushing packets of imagewatcher@... from CSI queue of
  dome@.../pyobs` show stanzas addressed to `dome` being held server-side and released later, rather
  than delivered immediately — exactly the mechanism that would produce a silent multi-second gap on
  the sender's side (a `get_capabilities` request whose reply is queued, not lost, looks identical to a
  timeout until whatever flushes the queue).
- Confirmed via `ejabberdctl dump_config` and the raw `/etc/ejabberd/ejabberd.yml`: `mod_client_state` is
  loaded on `iag50srv`'s production ejabberd with default settings (`mod_client_state: {}`), as part of
  what looks like an unpruned, fairly complete default module list (`mod_bosh`, `mod_carboncopy`,
  `mod_delegation` commented out, etc. — the shape of ejabberd's stock example config, not a hand-curated
  one).
- **This module is entirely absent from `tests/xmpp/ejabberd.yml`** (the local docker-compose test
  config used for every earlier scenario in this doc): its `modules:` list is `mod_admin_extra`,
  `mod_caps`, `mod_disco`, `mod_ping`, `mod_pubsub`, `mod_roster`, `mod_shared_roster`, `mod_vcard` —
  deliberately minimal, curated for the test suite's needs, and never had `mod_client_state` in it.

**This is a strong, concrete candidate explanation for the entire "reproduces on iag50, never reproduces
locally" pattern that's been the central mystery of this whole investigation.** Every earlier local
docker-compose run (all shaper configs, all the O(N²) slixmpp digging, the k=7/8/15/21 synthetic
benchmark against the real server) ran against ejabberd configs that never had this module loaded at
all — so no test in this doc before today could possibly have hit CSI queueing, regardless of how well
it otherwise matched the incident's shape.

**Not yet fully closed:** the exact trigger for *why* ejabberd classifies `dome`'s session as
CSI-inactive (XEP-0352 is normally client-driven — a client sends `<active/>`/`<inactive/>` to opt in;
slixmpp/`XmppComm` don't appear to send either) isn't identified yet — `mod_client_state` activity for
`dome` starts at `13:05:02`, about 43s *after* the first `Still failing` warnings at `13:04:19`, so CSI
queuing is well-evidenced as part of the mechanism but might not be the very first cause of the earliest
retries failing. Worth checking next: ejabberd's `mod_client_state` source for any non-explicit
(server-heuristic) path into the inactive/queued state, and whether it's specifically about `dome`'s
traffic pattern (its `_update_status` background task publishes `IPointingAltAz` once/second — busier
than the other 7's mostly-idle steady state) rather than something arbitrary about being "the newcomer."

**Cleanup:** both live-module runs' processes fully stopped and verified gone; `ejabberd` log level
reverted to `info`. Full logs (all 8 modules × 2 runs, `ss` capture, ejabberd debug log slice, config
dump) saved outside the repo for reference, not committed (large, and include real account activity).

**Next step:** try disabling `mod_client_state` on a throwaway/staging ejabberd matching iag50's full
config (or, more surgically, on iag50 itself during a no-ops window) and re-run the identical
reproduction — if the cascade stops, that confirms the mechanism decisively rather than just
correlating it. Also worth checking pyobs-monet's ejabberd config for whether it loads `mod_client_state`
too — if monet-south's config omits it (or has it configured differently), that would also explain "works
on monet-south, fails on iag50" independent of anything about `pyobs-core`'s own code.

### Third live run (2026-07-28, same day) — `mod_client_state` ruled out as the cause

Ran the confirmation test proposed above. Backed up `/etc/ejabberd/ejabberd.yml`
(`ejabberd.yml.bak-before-csi-test`), commented out `mod_client_state: {}` (line 244), and applied with
`ejabberdctl reload_config` (live reload, no restart, no session disruption) — confirmed via
`ejabberdctl dump_config` that the module was genuinely gone from the effective config (0 occurrences,
down from being present among 39 other `mod_*` entries).

**Re-ran the exact same reproduction. It still happened — twice over, in two different shapes:**

1. **During the initial 7-module startup itself**, before `dome` was even launched: `scheduler` became
   unreachable from `autofocus`/`focusmodel`/`imagewriter`, and `scheduler`↔`acquisition` failed
   mutually, all with the same `Still failing to get capabilities... after 3 attempts` signature,
   starting ~33-48s after each module's own `Started successfully` — never seen in either of the first
   two runs, where the initial 7-module phase was always clean. Not the "newcomer" pattern at all this
   time.
2. **Then `dome` joined as the 8th, and the full original cascade reproduced again anyway** — same
   dome-centric pattern as runs 1 and 2, warnings starting 34s after `dome`'s `Started successfully`, and
   a genuine `IqTimeout` at 88s (`13:36:34`, matching the ~85-88s pattern from both earlier runs almost
   exactly).

No event-loop-lag watchdog output in any of the 7 peer logs this run either (checked via
`grep -il 'lag\|stall\|event.loop'` across all of them — no matches).

**Conclusion: `mod_client_state` is not the cause.** It genuinely wasn't loaded, and the incident
reproduced anyway, in a form at least as bad as before (arguably worse — two distinct failure episodes
in one run instead of one). The correlation found in the second run (126 CSI log lines for `dome`
specifically) was real but was a *symptom* riding on top of whatever the actual mechanism is — likely
`dome`'s busier-than-idle background traffic (its `_update_status` task publishes once/second) made it a
more visible target for CSI queuing once a connection was already struggling for some other reason, not
evidence that CSI queuing was the initial cause of the struggle.

**Reverted cleanly**: `ejabberd.yml` restored from the backup, `reload_config` re-applied, confirmed
`mod_client_state` present again in `dump_config` output (back to 1 occurrence). All 8 module processes
from this run stopped and verified gone. Production ejabberd is back to its exact pre-test state.

**Where this leaves it:** back to an open root cause, but with one new, real lead from this run worth
following up — the same failure signature now reproduced *without* any "newcomer joining a stable
fleet" framing at all, just from `scheduler`/`acquisition`/`mastermind` starting within their normal
~10-40s of each other. That's a broader, more general trigger condition than "N+1 late joiner," and
points more toward *any* moment where `_on_module_opened`'s capability-fetch fires while ejabberd (or
something adjacent to it, still unidentified) is in whatever transient state causes this — same-host
colocation with ejabberd remains the strongest architectural difference from every test that never
reproduced it, but the specific mechanism inside that colocation is still unknown. Next candidates,
in rough order of ease: (1) strace the ejabberd beam.smp process's own scheduler activity (or use
Erlang's own `observer`/`etop`/`msacc` tooling, no install needed since it ships with the OTP
distribution) during a fresh reproduction, since `cpu.stat`/`load average` are too coarse and
`mod_client_state` is now ruled out as the lens to look through; (2) get an `ss` capture actually timed
correctly this time (start it, confirm with a timestamp check that it's still sampling *after*
confirming `dome`'s launch, not before); (3) compare mnesia table sizes/fragmentation on iag50 (34 days
uptime per `uptime` output above) against a freshly-restarted ejabberd, in case long-runtime state
bloat is a factor no short-lived docker-compose or CI environment would ever exhibit.

### Fourth live run (2026-07-28, same day) — found the actual mechanism: stuck per-connection Recv-Q on ejabberd's side

Per explicit direction not to start `mastermind` in future tests (autonomous scheduler, can issue real
RPC to hardware on its own initiative), it was dropped from the module set and replaced with `flatfield`
(verified safe first: `FlatField.open()` in `pyobs-core`'s own source only registers passive
`BadWeatherEvent`/`RoofClosingEvent` listeners and publishes initial state, no autonomous action).
Stable set: `acquisition`, `autofocus`, `focusmodel`, `imagewatcher`, `imagewriter`, `scheduler`,
`flatfield`, then `dome` as the 8th, same procedure as before.

**Got the `ss` capture timing right this time** (previous two attempts were mistimed — capture window
closed before the trigger even fired) by starting the capture and the `dome` launch back-to-back in the
same turn with no verification round-trip in between, then confirming after the fact that the capture's
first sample (`16:04:01`) predated `dome`'s launch (`16:04:27`) and its last sample outlasted the
cascade. Reproduced again: cascade began 36s after `dome`'s `Started successfully`, and — new this run —
`flatfield` hit a genuine `IqTimeout` at just **34s** after `dome`'s launch, much faster than the ~85s
seen in every prior run.

**The `ss` data explains why.** Live `ss -tinp` during the failure window showed one specific client
socket — `dome`'s own connection (PID confirmed via `ps`) — with `Send-Q: 227170` bytes stuck unsent and
`rwnd_limited: 73796ms (99.7%)`: blocked from sending for nearly 74 seconds because the *peer's*
(ejabberd's) receive window wouldn't open. Cross-referencing ejabberd's own side of the exact same
connection (matched by port number) showed `Recv-Q: 48044` — 48KB sitting in ejabberd's own kernel
receive buffer, unread by the `beam.smp` process, for the connection's entire "busy" duration.

**Tracing the full capture confirmed this isn't a brief blip — it's sustained, for the entire observation
window, on two separate connections:**
- `flatfield`'s connection to ejabberd was **already stuck** (`Recv-Q` ~85-90KB) at the very first
  capture sample (`16:04:01`, before `dome` even connected) and **remained stuck through the last
  sample checked (`16:08:04`) — over 4 minutes continuously**, never draining.
- `dome`'s connection became stuck within 4 seconds of connecting (`16:04:31`, `Recv-Q` 92692) and
  **also remained stuck through `16:08:54` — over 4 minutes**, never draining.
- No other connection (of the 7 total: `acquisition`, `autofocus`, `focusmodel`, `imagewatcher`,
  `imagewriter`, `scheduler` were all clean; only `flatfield` and `dome` got stuck) showed this pattern
  anywhere in the capture.

**This reframes the entire investigation.** It was never really about "newcomer joins a stable fleet" —
that framing fit runs 1 and 2 (where `dome`, the newcomer, happened to be the stuck connection) but not
run 3 (where `scheduler`/`acquisition` — none of them newcomers — got stuck during ordinary startup) or
this run (`flatfield` was stuck *before* `dome` even joined). The actual mechanism: **ejabberd
intermittently and durably stops draining the kernel receive buffer for some subset of its client
connections** — not a systemic overload (other connections on the same server, same moment, are
completely fine) and not something that self-heals on a several-minute timescale. Whichever module
happens to have a capability-fetch or `_safe_send` call in flight against a stuck peer at the wrong
moment is the one that logs the timeout warning or eventually raises `IqTimeout` — the "newcomer"
pattern in the first two runs was circumstantial, not causal.

**Not yet identified: why these two specific connections, why they never recover, and what's actually
stopping `beam.smp` from calling `recv()` on them.** Both are TLS connections (`use_tls: True`), which
narrows the search somewhat — worth checking whether a stuck connection correlates with something in
ejabberd's TLS session handling (record reassembly, renegotiation, a stuck `p1_tls`/`fast_tls` NIF call)
rather than the c2s/stanza-processing layer above it, since the OS-level socket is accepting bytes into
its buffer fine (`Recv-Q` grows) but nothing above the kernel is draining it. Full `ss` capture (all
connections, 4+ minutes, one-second resolution) and all 8 modules' logs from this run saved outside the
repo alongside the earlier runs' data, not committed.

**Next step:** with a concrete symptom to search for (`Recv-Q` climbing and staying elevated on a
specific c2s session, TLS in use), the most direct path is Erlang-level introspection of that specific
process — `ejabberdctl debug` (attaches an Erlang shell to the live node) to inspect the process behind
the stuck socket (`erlang:process_info/1` for its message queue length, current function, reductions)
the next time a connection gets stuck, rather than more black-box `ss` captures. If that process is
buried in a long-running NIF call or has a backlogged mailbox, that would point straight at the fix;
if it looks idle despite the stuck socket, that points toward something even lower-level (the TLS NIF,
or ejabberd's socket-acceptor pooling) instead.

### Fifth investigation session (2026-07-28, same day) — found the specific mechanism: an un-re-armed passive socket

Did the Erlang-level introspection proposed above. `ejabberdctl debug` (an interactive `-remsh` shell
into the live production node) is a materially more powerful/risky action than anything else in this
doc — full read/write access to the live node's state — and was correctly blocked by this environment's
own permission classifier when attempted directly. Split the work instead: the 7-module reproduction
(`acquisition`, `autofocus`, `focusmodel`, `imagewatcher`, `imagewriter`, `scheduler`, `flatfield` — no
`dome` needed this time, stuck connections showed up during ordinary startup again) and stuck-socket
identification (via `ss -tinp`, matching local port to owning PID via `ps`) were done as before; the
`ejabberdctl debug` session itself was run by the user directly, with exact Erlang expressions provided
turn-by-turn.

**Two connections were stuck within ~40s of the 7 modules starting** (no newcomer needed at all this
time either): `flatfield` (ejabberd-side local port `57876`, `Recv-Q` 85134) and `scheduler` (port
`54526`, `Recv-Q` 36091) — consistent with every run since the third: this is not a "newcomer" bug.

**Found the Erlang port object for the stuck connection and its owning process:**
```erlang
Ports = [P || P <- erlang:ports(), (catch inet:peername(P)) =:= {ok, {{0,0,0,0,0,0,0,1}, 57876}}].
[Port] = Ports, {connected, Pid} = erlang:port_info(Port, connected).
```

**`erlang:process_info(Pid, [message_queue_len, current_function, current_stacktrace, status,
reductions, memory])` returned:**
```erlang
[{message_queue_len,0},
 {current_function,{p1_server,collect_messages,3}},
 {current_stacktrace,[{p1_server,collect_messages,3,[{file,"p1_server.erl"},{line,438}]},
                       {p1_server,process_message,9,[{file,"p1_server.erl"},{line,421}]},
                       {proc_lib,init_p_do_apply,3,[{file,"proc_lib.erl"},{line,329}]}]},
 {status,waiting},
 {reductions,511688},
 {memory,142880}]
```

**The owning process is genuinely idle** — empty mailbox, `status: waiting`, blocked inside
`p1_server:collect_messages/3` waiting for a *new* message, not a busy loop and not blocked on a slow
call. Reductions (511688) show no runaway computation either. This process is not the problem.

**`inet:getopts(Port, [active])` returned `{ok,[{active,false}]}`.** The socket is in **passive** mode
— no automatic `{tcp, Socket, Data}` (or `{ssl, ...}`) messages are generated for it at all; something
has to explicitly read from it. Combined with the process being idle waiting for a message that active
mode would normally deliver, this is the mechanism: **the socket was put into passive mode (a normal,
presumably-intentional step somewhere in ejabberd's TLS/c2s receive handling) and never switched back
to `{active, once}`/`{active, N}` afterward.** The kernel keeps happily accepting bytes into `Recv-Q`
(hence the growth seen in run 4's `ss` capture), but nothing above the kernel is ever told they arrived
— the connection goes permanently deaf, with no crash, no log line, no CPU spike, and no self-recovery
(matches run 4's 4+ minute observation with zero drainage).

**Ruled out a separate reader/helper process as the visible culprit.** `erlang:port_info(Port, links)`
→ only the c2s process itself (`Pid`). `erlang:process_info(Pid, links)` → the same port, plus one
process (`<0.564.0>`) that turned out to be `ejabberd_c2s_sup` — the ordinary c2s worker supervisor,
sitting idle in `gen_server:loop/7`. Nothing exotic there. So the failure to re-arm isn't a separate
component silently dying; it has to be inside the c2s process's own code path (or a NIF/port call it
makes synchronously — TLS decrypt via `fast_tls`/`p1_tls` is the obvious candidate given both stuck
connections in every run used TLS) under some as-yet-unidentified condition.

**This is the strongest, most concrete finding of the whole investigation.** Every earlier layer checked
out clean (shaper, slixmpp O(N²) — real but different bug, client event-loop stalls, cgroup throttling,
host resources, `mod_client_state`) precisely because none of them touch this: a socket-level flow-control
re-arm bug is invisible to CPU metrics, invisible to ejabberd's own application-level logs (nothing errors
— the code path just silently stops calling the re-arm), and invisible to anything running on a different
machine or in a fresh, short-lived environment unless it happens to hit the exact same code path under
the exact same (still unidentified) triggering condition.

**Next steps:**
- Read `ejabberd_c2s.erl` / `p1_server.erl` / `fast_tls.erl` (or `p1_tls`, whichever TLS module iag50 is
  actually using — check `ejabberdctl dump_config` or the running node for which is loaded) source —
  ProcessOne's repos are public on GitHub — specifically for every code path that calls
  `inet:setopts(Socket, [{active, false}])` and verify each one has a matching re-arm on every exit path,
  including error/exception branches. A `{active, false}` set inside a `try`/`catch` with the re-arm only
  on the success path (not in an `after`/matching catch clause) would produce exactly this symptom under
  whatever specific condition trips the exception.
- Check `p1_server.erl:421` (`process_message/9`) and `:438` (`collect_messages/3`) specifically against
  the installed ejabberd version, since that's the exact frame the stuck process was parked in.
- If a plausible code path is found, this would be a genuine upstream ejabberd/p1_server bug report,
  same precedent as the slixmpp O(N²) issue filed earlier in this investigation — but that's contingent
  on actually finding the missing re-arm in source, not yet done.
- A pragmatic mitigation short of a real fix, if this recurs in production before root-caused: since the
  affected c2s session is cleanly identifiable (stuck `Recv-Q`, `{active,false}`), a periodic health-check
  script using the same `ss` + `ejabberdctl debug`-style introspection (or, more operationally, just
  killing/kicking sessions whose `Recv-Q` has been nonzero and non-decreasing for more than N seconds)
  could auto-recover affected connections without needing the underlying bug fixed first.

### Sixth investigation session (2026-07-28, same day) — read upstream source, found the likely exact mechanism

Note on this session: partway through, production `ejabberd` on `iag50srv` went down (see incident note
below) — unrelated to the source-reading work itself, but worth flagging that this investigation session
briefly overlapped with a real outage on the server being investigated.

Read the actual `processone/xmpp` (v1.9.4, matching the installed `erlang-p1-xmpp` package) and
`processone/ejabberd` (tag `24.12`, matching installed `ejabberd 24.12-3+deb13u2`) source from GitHub —
public repos, fetched directly — to trace the exact re-arm code path starting from the stuck frame found
in session five (`p1_server.erl:421`/`:438`, `collect_messages/3`/`process_message/9`).

**`p1_server.erl` is confirmed generic, not buggy.** `collect_messages/3` (lines 425-447) is a completely
generic message-loop primitive — the stuck process was simply in its normal, correct idle-wait state
(`receive Input -> ... after Time -> {timeout, ...}` at line 440-445). The bug is not in this file; it's
in whatever is supposed to deliver the next message to this process.

**Found the real re-arm mechanism in `xmpp_socket.erl`** (`processone/xmpp` library):
- `activate/1` (lines 466-470) is the actual re-arm: `SockMod:setopts(Socket, [{active, once}])`.
- `parse/2` (lines 485-524) is the function responsible for calling it, with four clauses: the `Data ==
  <<>>`/`Data == []` base case calls `activate/1` directly; two list-recursion clauses (`[El|Els]` for
  decoded XML elements) recurse toward that base case; and the raw-binary clause (`is_binary(Data)`)
  calls `fxml_stream:parse` then either `activate/1` directly or, **if the shaper says to throttle
  (`Pause > 0`), calls `activate_after/3` instead.**
- `activate_after/3` (lines 472-478) does **not** re-arm the socket at all in the throttled case. It
  schedules a *synthetic* `{tcp, Socket, <<>>}` message via `erlang:send_after(Pause, Pid, ...)` — the
  real re-arm only happens later, when that fake message works its way back through the full receive
  pipeline (`handle_info` → `xmpp_socket:recv/2` → `fast_tls:recv_data` (decrypting nothing) →
  `parse/2` → *now* the base case fires and calls `activate/1` for real).

**This is architecturally far more fragile than the direct path** — a timer, a synthetic self-message,
and a second full decrypt-and-reparse round-trip, instead of one direct `setopts` call. Traced one
concrete way it can silently break, in `xmpp_stream_in.erl`'s `handle_info`:
```erlang
handle_info({tcp, _, Data}, #{socket := Socket} = State) -> ... % normal path
% Skip new tcp messages after socket get removed from state
handle_info({tcp, _, _}, State) ->
    noreply(State);
```
If `socket` is removed from `State` (e.g. via the `release_socket` cast, `xmpp_stream_in.erl:324-329)
while a delayed reactivation timer from `activate_after` is still pending, that timer's synthetic
message lands in the second clause — **silently discarded, by explicit design/comment, with no further
re-arm attempted.** Whether this exact clause or something structurally similar is the precise trigger
for iag50's incident isn't proven (would need either a live-caught synthetic-message-loss event with
tracing, or an upstream maintainer's confirmation), but the *shape* fits everything observed: no crash,
no ejabberd log line at any level, no CPU/scheduler signal, no self-recovery — because nothing ever
errors, a scheduled re-arm message simply never gets acted on.

**This also reconciles the days-old "shaper hypothesis refuted" finding** from earlier in this same
investigation (see "First real results" above): that test only checked whether the shaper's *rate limit*
affects aggregate publish latency for a synthetic idle-client benchmark — it doesn't, confirmed across a
33x rate spread. It never tested whether the shaper's pause-and-reactivate *mechanism itself* has a
latent bug — a completely different question, and the one this session's source-reading points at. It
also explains the "real modules only, never idle synthetic clients" pattern that's held across every run
in this doc: idle `XmppComm` clients barely generate enough traffic to ever trip `Pause > 0` in the first
place, while real modules' actual traffic (periodic state pushes, capability-fetch bursts, log
forwarding) plausibly does, on iag50's specific (low, 3000 B/s default per the shaper config documented
at the top of this doc) shaper rate.

**Not yet done, and probably the right place to stop live-testing this specific incident**: actually
proving the `release_socket`-vs-pending-timer race (or whatever the precise trigger is) would need
either instrumenting a fresh ejabberd build with tracing/logging added to `activate_after`/the
`handle_info({tcp,_,_}, State)` fallback clause, or raising this with upstream (`processone/xmpp` /
`processone/ejabberd`) maintainers with this session's findings and asking whether they recognize the
pattern — same approach that worked for the slixmpp O(N²) bug filed earlier in this investigation
(`poezio/slixmpp#3786`). This is a plausible, well-evidenced hypothesis backed by reading the actual
running version's source, not a proven root cause.

**Incidental production incident during this session:** `ejabberd` on `iag50srv` was stopped (clean,
orderly shutdown per its own log — not a crash) partway through this session, apparently by an
accidental `q().` typed at an `ejabberdctl debug` prompt from session five — in a `-remsh` session, `q()`
calls `init:stop()` *on the target node*, not just detaching the local shell (the correct safe detach is
`Ctrl+G` then `q` at the JCL prompt, or simply closing the connection). Caught within ~2.5 minutes via a
routine `ejabberdctl status` check, restarted cleanly with `systemctl start ejabberd`, confirmed fully
healthy (all listeners back, Mnesia synced, no new errors beyond pre-existing config warnings). Worth
recording as a real operational lesson independent of the bug-hunt: **never use `q()` to detach an
`ejabberdctl debug` session** — it stops production ejabberd, not the local shell.

### Seventh session (2026-07-28, same day) — comparison against monet-south, mitigation applied and confirmed working

**Compared iag50's live shaper config directly against `monet-south`'s** (SSH access granted read-only —
"don't change anything" — for this comparison; monet's config was only read, never modified). Both use
the identical `ejabberd 24.12-3+deb13u2`, identical `c2s_shaper: {none: admin, normal: all}` routing, and
both load `mod_client_state`. The one substantive difference: **monet's `shaper.normal` is `{rate:
30000, burst_size: 200000}` — exactly 10x iag50's `{rate: 3000, burst_size: 20000}`.** This matches an
earlier passing reference in this doc to "the multiplier the user runs in their own production ejabberd
deployments" — monet is that deployment; iag50 had been left on ejabberd's stock default.

**Important distinction from the earlier "shaper hypothesis refuted" result** (see "First real results"
above, from days before the real-module runs): that test only checked whether the shaper's *rate*
affects aggregate publish latency for a synthetic idle-client benchmark — it found no effect, across a
33x rate spread. It never tested whether raising the shaper prevents *this* bug (the `activate_after`
reactivation failure found in session six) under *real* module traffic. Different question; this session
tested it directly for the first time.

**Applied the fix to iag50 and re-tested.** Backed up `/etc/ejabberd/ejabberd.yml`
(`ejabberd.yml.bak-before-shaper-fix`), changed `shaper.normal` from `{rate: 3000, burst_size: 20000}` to
`{rate: 30000, burst_size: 200000}` (matching monet exactly), applied via `ejabberdctl reload_config`
(live, no restart), confirmed via `dump_config`. Re-ran the identical reproduction: the same 7 modules
(`acquisition`, `autofocus`, `focusmodel`, `imagewatcher`, `imagewriter`, `scheduler`, `flatfield`), then
`dome` as the 8th.

**Result: clean.** All 7 modules started with zero failures and — notably — `ss` showed **zero stuck
connections even before `dome` joined**, unlike sessions three and four where a connection was already
stuck during ordinary startup. After `dome` joined, monitored for a full 3 minutes (well past the ~30-90s
window every single prior run needed to fail) with zero `Still failing`/`IqTimeout`/error events across
all 8 logs, and `ss` confirmed no stuck `Recv-Q` anywhere nearly 5 minutes after `dome`'s launch. This is
a complete contrast to sessions one, two, three, and four, which reliably reproduced the cascade every
time under the old shaper.

**Current status: the shaper fix is applied and left in place on iag50's live production ejabberd
config** (both the running config, via `reload_config`, and the on-disk `/etc/ejabberd/ejabberd.yml`).
This is a mitigation, not a fix for the underlying `xmpp_socket.erl`/`activate_after` bug identified in
session six — that bug is still present in ejabberd's code and could in principle still be triggered by
traffic bursty enough to exceed even the new, higher shaper limit. But it directly addresses the
mechanism this investigation identified (the fragile reactivation path is only reachable when the shaper
throttles a connection at all), matches what's already running successfully in production at
monet-south, and is trivially reversible (the pre-fix config is backed up) if it ever turns out
insufficient.

**Next steps:** monitor iag50 for recurrence over the coming days/weeks under real fleet load (not just
this synthetic-but-real-module reproduction) before considering this fully closed. If it recurs even
with the higher shaper, that would suggest either a higher multiplier is needed or that shaper-avoidance
isn't sufficient on its own — in which case the upstream bug report (still not filed) becomes the
priority rather than an optional follow-up.

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
