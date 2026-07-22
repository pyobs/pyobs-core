# Plan: Systematic ejabberd throughput/latency benchmarking

Status: draft — headline number known, original methodology unrecoverable

**The magnitude is known: simultaneous state pushes took ~15x longer than sequential ones.** That
draft/test run was done on another machine and isn't retrievable — not in this repo, not in
session memory beyond the headline ratio, nor in `specs/design/pyobs_2_0_wire_protocol.md` (which
has a *different*, unrelated concurrency measurement: 5 simulated devices, `gather` vs. sequential,
0.5s vs 0.1s — not ejabberd, not state pushes). The remaining "Prior finding" checklist items below
are **not going to be recovered by more digging** — either they're recalled directly, or they stay
unknown and the scenarios below need to be run fresh to get real, reproducible numbers rather than
trying to match an unrecoverable prior run.

## Prior finding

- [x] What "slower" meant concretely: aggregate wall-clock time for a batch of concurrent pushes
      vs. the same batch done sequentially — **~15x** worse for the concurrent case.
- [ ] Exact scenario: how many concurrent pushes, to how many distinct PubSub nodes, what payload?
- [ ] Precise numbers behind the 15x ratio (absolute latencies, not just the ratio).
- [ ] Was concurrency via `asyncio.gather` on one client, or multiple independent clients/modules
      publishing at the same time?
- [ ] Local docker-compose ejabberd, or a different (production-like?) server?
- [ ] Any hypothesis already formed. The ejabberd shaper root-cause found separately for #664/#666
      (per-connection outbound byte/sec throttling with queuing rather than dropping, capable of
      minutes-long delay on a healthy-looking connection — see `state-freshness-max-age.md`'s
      Problem section) is a strong candidate mechanism for concurrent-worse-than-sequential too: a
      burst of simultaneous publishes from one connection would exhaust the shaper's burst
      allowance immediately, where the same publishes spread out sequentially might stay under it.
      Not yet confirmed as *the* cause of the 15x figure specifically — scenario 2 below plus the
      shaper-introspection step should confirm or rule it out.

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
- **`tests/xmpp/ejabberd.yml` declares no explicit shapers.** ejabberd applies its own built-in
  default shaper limits even when a config doesn't mention them — worth checking what those
  defaults actually are (`ejabberdctl` shaper introspection, or just reading the ejabberd docs for
  the version pinned by `ejabberd/ecs:latest`) before running anything, since a default shaper
  throttling bursts is a very plausible mechanism for "concurrent slower than sequential" and would
  change the story from "XMPP/PubSub doesn't handle concurrency well" to "this specific config
  throttles bursts, tune the shaper."
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
existing precedent for standalone XMPP tooling that isn't part of the pytest suite. Proposed:
`scripts/xmpp/benchmark_state_throughput.py`.

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
