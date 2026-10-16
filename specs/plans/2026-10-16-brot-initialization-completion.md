# Plan: wait for the complete BROT initialization operation

Date: 2026-10-16

Status: proposed; no implementation or deployment performed

Issue: [pyobs/pyobs-brot#91 — init() should wait for calibration and automatic go-home completion](https://github.com/pyobs/pyobs-brot/issues/91)

## Intended behavior

**Scope: the entire BROT telescope fleet.** IAG50 is one deployment, not the target architecture or the complete acceptance scope. Inventory every telescope using pyobs-brot and its actual controller, firmware version, mount type, optional axes, and initialization sequence before choosing the implementation or release requirements. Do not assume that IAG50 and MONET exhaust that inventory. Local source examples establish possible failure modes, not the deployed fleet list.

The [repository-backed fleet inventory](2026-10-16-brot-fleet-inventory.md) identifies MONET/N, MONET/S, and IAG50, two concrete controller families, supporting libraries, duplicate development configs, and unresolved runtime/version checks. MONET/N and MONET/S require separate configuration acceptance despite sharing MONETcommon. It also records an IAG50 MQTT-prefix discrepancy and a south deployment-recipe mismatch that must be resolved against installed configuration before rollout.

`BrotBaseTelescope.init()` succeeds only when the PLC has completed the initialization operation requested or joined by that call: required calibration, automatic mount home movement, and any focus movement started by that operation. Intermediate standstill, powered axes, and `READY_STATE == 1.0` are insufficient. A caller awaiting `init()` must then be able to start acquisition or movement without competing with unfinished initialization.

The same completion definition must govern published `IReady` and initialization motion status. Failure, rejection, interruption, stale telemetry, lost connectivity, controller restart, and timeout must never become successful returns. Preserve task cancellation. Keep stop and park available while initialization is pending.

This plan uses the issue description and local source inspection. It includes no deployment logs, operational history, or private deployment evidence.

## Findings that determine the design

| Source | Relevant behavior |
|---|---|
| `pyobs-brot/pyobs_brot/brottelescope.py`, `init()` | Returns immediately for `TelescopeStatus.ONLINE`; after `power_on()`, returns for raw readiness 1 before checking telemetry health. |
| Same file, `_update()` | Publishes ready=true whenever pybrotlib maps raw readiness to ONLINE, independently of an active `init()` call. |
| `pyobs-brot/pyobs_brot/_settle.py` | Health checks raise `MoveError`; the generic condition waiter checks its condition before health. Neither is an initialization completion contract. |
| `pyBROT/src/pybrotlib/components/telescope.py` | `status` maps readiness directly; `power_on()` publishes a trigger, without an operation acknowledgement or result. |
| `pyBROT/src/pybrotlib/transport/{transport,mqtttransport}.py` | `telemetry_age()` measures the last incoming message, including unrelated traffic. Telemetry fields arrive separately. Receipt age alone does not establish a coherent, current initialization result. |
| `IAG50cm/.../FB_TelescopeControl.TcPOU` | `_PowerOn` stage 100 clears `bPower`, sets `bIsPowered`, and requests `bGoHome`. Public readiness can become 1 during the automatic home operation. Home moves the mount axes sequentially, then its stage 100 assigns `focusHome` and clears `bGoHome` without waiting for focus arrival. Global stopped-motion excludes focus and can be true between mount movements. |
| `MONETcommon/.../FB_MonetTelescopeControl.TcPOU` | Initialization has a different structure: `bPower` keeps public readiness at 0.7 through calibration and the mount/derotator home move. Audit completion at its own final stage rather than transplanting the IAG state machine. |
| `pyobs-core/pyobs/modules/module.py`, `timeout()` | The decorator attaches RPC timeout metadata. It does not bound direct calls to `init()`. |
| `pyobs-core/pyobs/modules/telescope/basetelescope.py` | Public move methods check motion status before acquiring their motion lock and may silently return during INITIALIZING. Those checks do not alone provide atomic command exclusion. |

## Decision: a PLC-owned operation result

Implement a versioned initialization contract across PLC, pybrotlib, and pyobs-brot. Do not fix this by adding a sleep, waiting for one stopped-motion sample, requiring a sampled moving-to-stopped edge, comparing against guessed home coordinates, or interpreting disappearance of a busy flag as success.

### Request and result semantics

1. Introduce an initialization request carrying a unique client request ID in **one command message**. A proposed encoding is a new `initialize=<request-id>` command on the existing telescope SET channel; specify its grammar, length bound, and parser behavior before implementation. Do not send a token separately followed by the old `power=1` trigger: that permits mixed requests and depends on legacy multi-field parsing.
2. The PLC creates a boot/session identity and a monotonically increasing operation generation. Every accepted initialization path, including existing local/legacy power-on entry points, must enter the same operation lifecycle. New request IDs identify acknowledgements/results; `(boot_id, generation)` identifies the physical operation.
3. Lifecycle: `idle -> running -> succeeded | failed | interrupted`. A rejected request receives an explicit rejection associated with its request ID, without overwriting the outcome of an unrelated active operation. Include a bounded reason code; human-readable explanation is optional.
4. Acceptance clears previous success before starting work. Success is latched until a later lifecycle transition; it is not a one-scan pulse. Failures and interruptions have explicit terminal results. Merely clearing `bPower`, `bGoHome`, or command flags never means success.
5. A request while initialization is already running joins that operation; it must not restart calibration. A request while already fully initialized and currently operational receives an immediate successful acknowledgement for its own request ID without another power cycle or home move. The PLC, not cached Python readiness, decides this. Duplicate delivery of the same request ID is idempotent; a distinct request during an active operation must have an explicit join/busy response. Define bounded duplicate/result retention and never silently replay an old token as new work after eviction.
6. Stop, park, reset, safety interruption, command preemption, and internal timeouts must terminate the relevant pending operation with a non-success result. Decide these outcomes before clearing the state machine flags. Reboot invalidates all prior operation identities and completion state.
7. While an operation owns initialization, ordinary movement commands must not start or remain queued for surprise execution after completion. Reject them explicitly. Preserve safety and stop precedence. Define and implement park interruption explicitly: current MONET arbitration prioritizes power-on over park, while IAG's power branch clears pending park, so a uniform park-interrupt policy is a controller behavior change requiring tests. This protection belongs in the PLC as well as the client, because other clients can issue commands.

### Coherent, fresh publication

Publish a complete initialization status envelope in a single MQTT message, rather than assembling a success decision from independently updated fields. Proposed dedicated topic: `{site}/Telemetry/initialization`, handled before generic Influx telemetry parsing. Use a bounded versioned payload; JSON is the preferred encoding if the PLC communication layer supports it without truncation. The wire-format implementation must include payload-size and escaping tests.

Required envelope data: contract version, controller boot identity, publication sequence, operation generation, request acknowledgement/result identity, lifecycle state/reason, and current operational eligibility. Capture these together in one PLC scan after evaluating errors and interrupts. Keep historical operation success separate from current operational eligibility, so a successful previous init cannot make a now-parked or failed telescope ready. Joining clients must each receive a correlated acknowledgement, with the shared operation generation available for subsequent completion monitoring.

Publish on transitions and periodically at a documented cadence, including when stationary. Use a dedicated heartbeat cadence (proposed 1 s) and a configurable stale limit with comfortable jitter margin (proposed 5 s); do not reuse the existing stationary telemetry cadence of 5 s with a 5 s freshness limit. Define sequence handling for duplicates, out-of-order messages, reconnects, and rollover. Retained snapshots may populate diagnostics but cannot establish live completion. Track receive time only for validated envelopes from the selected site; unrelated telemetry must not refresh it. Invalidate live status on disconnect and require a new live snapshot after reconnect.

Freshness is checked **before** acceptance of success, including the already-online path. Request correlation prevents queued or retained results from an earlier run satisfying a new call. A controller restart or loss of liveness while waiting fails the call rather than silently attaching it to another operation. Do not claim that broker PUBACK proves PLC acceptance.

### Controller-specific completion boundaries

Define a shared semantic contract in BROTLib/pybrotlib and keep telescope-specific sequencing in the respective controller implementations. Audit `FB_BaseTelescopeControl`, `FB_AltAzTelescopeControl`, `FB_RaDecTelescopeControl`, derived implementations, and site-specific configuration. Calibration, automatic home, covers, focus, and derotator work count only where that telescope's initialization actually owns them; do not add IAG50 movements or axis requirements to other telescopes. The IAG and MONET notes below are initial case studies, not an exhaustive implementation list.

**IAG controller:** keep internal mechanical readiness available to the home state machine; simply withholding internal `bReady` would deadlock `_HomeTelescope` stage 0. Carry the initialization operation across `_PowerOn` stage 100 into the automatic `_HomeTelescope`. Add a final focus-completion stage after assigning `focusHome`, then latch initialization success only once the mount home sequence and required focus work have completed without error. Validate move-completion flags against the current command, not stale `MoveDone` values. A focus already at target may complete without a sampled moving state; otherwise use the focus block's actual completion/position contract and configured tolerance. Handle absent/optional focus according to the controller's supported configuration. Changing all manual home semantics is optional; proving the initialization-owned focus work complete is required.

**MONET controller:** attach the same operation lifecycle to its existing calibration and home sequence. Audit elevation, azimuth, derotator, and focus completion and cleanup at the terminal stage, including stale `MoveDone` flags and commands remaining asserted. Do not introduce an additional home move or an IAG-specific focus-home action where the controller does not request one.

Cover mode changes that stop MONET's conditional automatic-mode controller invocation, and IAG's pending-home expiry that can clear the request without raising an error. Neither condition may silently become initialization success. IAG's actual `focusPark` and `focusHome` values coincide in the inspected configuration; final focus target assignment is not evidence that a separate motion always occurs.

Audit common base interfaces, command dispatch, other derived telescope controllers, and all power entry points before advertising support. Each controller advertises the contract only after implementing and testing its terminal semantics. If public `READY_STATE` is also changed to stay at 0.7 through initialization, keep its error precedence and internal mechanical readiness separate; the versioned result remains authoritative.

## Implementation work packages

### 1. Specify and implement the controller protocol

- Start with a fleet compatibility matrix: telescope/site, controller family and version, initialization entry points and owned devices, authoritative completion/failure/interruption signals, protocol support, and validation status. Mark unknown deployments explicitly; source-directory discovery alone does not establish coverage.
- Document the request grammar, envelope schema, error/rejection codes, boot identity source, sequence rules, duplicate handling, joining behavior, and terminal-state rules in the controller/library repositories.
- Extend command dispatch and the communication interface for atomic requests/results. Check message/string limits and exact site routing.
- Add shared lifecycle support at the appropriate common layer, then implement and validate completion boundaries for every controller/configuration identified by the fleet inventory, including IAG and MONET. Publish state on every exit path. Keep hardware safety and command priority rules intact.
- Add controller tests or an executable state-machine harness using the repositories' existing PLC test conventions. Compile the affected TwinCAT projects; static source assertions alone do not verify scan ordering or motion completion.

### 2. Expose a typed pybrotlib API

Files: `src/pybrotlib/telemetry.py`, `transport/transport.py`, `transport/mqtttransport.py`, `components/telescope.py`, and corresponding tests/documentation.

- Add immutable typed initialization snapshots and request receipts with explicit unsupported/unknown states. Missing telemetry must not default to successful completion or idle.
- Parse and validate the atomic envelope, preserve site and boot identity, reject malformed/unsupported versions, and track initialization-specific freshness. Do not combine a new status with an old generation.
- Add `initialize(request_id)` and an accessor/wait interface for correlated acknowledgement and terminal outcome. Preserve existing `power_on()` for existing consumers; clearly document that publishing that trigger does not wait for initialization.
- Expose the complete/operational predicate to clients without requiring private `_telemetry` access. Preserve raw readiness status semantics where compatibility requires them; use the new predicate explicitly in pyobs-brot.
- Test same-run duplicates, stale/retained data, wrong site/request, reboot, joining, already-initialized acknowledgement, and completion before the first poll.

### 3. Update pyobs-brot initialization and readiness

Files: `pyobs_brot/brottelescope.py`, a small initialization helper if warranted, `tests/test_brottelescope.py` or a dedicated `tests/test_initialization.py`, `pyproject.toml`, and user documentation.

- Retain the weather precondition and existing meaningful initialization errors. Check connection, PLC presence, supported contract, and snapshot freshness before deciding anything can succeed. An unknown last-will state may be acceptable with fresh valid operation telemetry; explicit offline is not.
- Serialize/join concurrent local `init()` calls and set the local pending state plus ready=false before the first await that could expose the operation to another caller. Send one correlated request and wait for its acknowledged operation's terminal result. Remove both raw-readiness success exits.
- Add a real monotonic overall deadline encompassing publication, acceptance, and completion, including direct Python calls. Make the duration configurable and align the RPC timeout metadata with it plus delivery margin. Choose the default using documented worst-case calibration, home, and focus limits; do not assume the current 120 s covers the expanded operation.
- Raise `InitError` with a specific reason for rejection, PLC failure, stale/disconnected telemetry, restart, and deadline expiry. Use the established `AbortedError` convention for explicit interruption if compatible with callers; document and test it. Propagate `asyncio.CancelledError` unchanged. Do not leak the settling helper's `MoveError` as the initialization health error.
- On cancellation or local timeout, keep readiness false while hardware activity is unresolved. Request a bounded, operation-scoped abort if supported and the operation is still current; never let cleanup issue an unscoped late stop against a replacement operation. Preserve the original exception if cleanup fails. A local waiter finishing does not by itself clear the PLC's initializing state.
- `_update()` uses the same validated operation snapshot: pending locally or running in the PLC means INITIALIZING/ready=false; failed/unhealthy means ready=false with the appropriate error status; only a live operational snapshot after successful initialization may publish ready=true. This must also work after a pyobs restart or an initialization started by another client.
- Add a shared command-admission guard for local initialization and conflicting telescope/focus/offset movement, and recheck immediately before publishing commands. Inspect inherited move methods and their lock ordering; do not assume their pre-lock status checks close the race. Reject concurrent movement clearly rather than silently treating it as a completed move. Stop and park remain usable and interrupt the pending init. Avoid changing general pyobs-core motion behavior unless a narrowly justified shared hook is necessary.

### 4. Compatibility and release order

- Missing completion telemetry is **unsupported**, not completed. There is no general safe legacy fallback using readiness plus a motion sample or a settle delay.
- Proposed strict behavior requires the new completion contract for `init()` success and for ready=true, with an actionable unsupported-controller error before issuing a legacy power trigger. Keep a bounded initial capability/snapshot wait so module startup is distinguishable from an unsupported controller. This is a fleet-wide compatibility decision: do not ship it as the shared driver's default until the inventory and migration plan account for every operating BROT telescope. An IAG50-only firmware upgrade is not sufficient release coverage.
- Upgrade controller support and publish a pybrotlib release first, then raise pyobs-brot's minimum dependency and release the driver change. Document the controller prerequisite prominently. If maintainers require a legacy opt-in mode, describe it as lacking this issue's guarantee and implement it separately; do not silently enable it.
- Stage validation in simulation and a controlled hardware acceptance run for every operating controller family and materially different initialization configuration. Track staged rollout and rollback per telescope so a shared driver upgrade does not unexpectedly disable other BROT telescopes. The plan does not authorize a firmware deployment or hardware movement.

## Regression and acceptance matrix

Use deterministic event-driven telemetry fixtures and a fake monotonic clock; avoid long real sleeps. Assert task completion, exception type, command count, and every emitted readiness state.

| Scenario | Required assertion |
|---|---|
| Raw readiness reaches 1 while calibration/home remains active | `init()` stays pending; no ready=true. |
| Mount stops between axis moves, or before automatic home begins | Still pending, even if stopped spans several publications. |
| Mount home ends while initialization-owned focus is moving | Still pending until focus completion. |
| Fast operation completes before the next client poll | Correlated terminal result succeeds without requiring a sampled running or moving edge. |
| Already initialized, live operational controller | Correlated acknowledgement succeeds without power cycling or moving. |
| Cached ONLINE/success, no live contract | No early success; unsupported/unhealthy handling applies. |
| Rejection or failure during calibration, home, or focus | Error reaches caller; ready=false; no success log. |
| Stop/park/reset/preemption during each phase | Explicit interrupted outcome; no later false success; a subsequent init can start cleanly. |
| Broker disconnect, PLC offline, or initialization stream stalls | Fails even if cached readiness/result says success. Unrelated traffic cannot keep the wait alive. |
| Retained, duplicate, reordered, malformed, wrong-site or old-request result | Cannot satisfy the current call or refresh valid freshness. |
| PLC restart or reconnect while pending | Prior identity invalidated; no adoption of a different run as success. |
| Two local init callers; an external initialization | One physical operation, defined join behavior, readiness consistent for all callers. |
| New request delivered twice via QoS 1 | No repeated calibration/home and no reset of the operation deadline. |
| Move/focus/offset request races with initialization admission | No conflicting hardware command before initialization completion. Stop/park still work. |
| Local timeout, cancellation, or failed command publish | Bounded completion, correct error/cancellation propagation, no leaked lock/task, no premature ready=true. |
| Direct `await telescope.init()` | Real timeout enforced without RPC machinery. |
| Standalone home/park and every inventoried controller/configuration | Existing semantics preserved outside the explicitly changed initialization boundaries; no IAG50-specific movement assumptions leak into shared behavior. |

Run the targeted pybrotlib and pyobs-brot tests, then their normal lint/type/test checks. Compile and run the controller tests. Hardware acceptance should record phase transitions and request/result identities, demonstrate a movement issued immediately after successful `init()`, and exercise interruption safely. Source review and Python mocks cannot substitute for that controller validation.

## Completion criteria and decisions to close during implementation

The issue is complete when both return behavior and published readiness obey the operation contract, tests cover the early-ready regression and all non-success paths, the fleet matrix accounts for every operating BROT telescope, applicable controller builds/configurations are validated, and compatibility prerequisites and migration paths are documented. IAG50 validation alone does not close the issue. A Python-only poll change is not sufficient with the current telemetry.

Before coding the protocol, settle the exact bounded wire encoding, controller boot identity mechanism, multi-client acknowledgement retention, and operation-scoped abort representation. Before selecting timing defaults, confirm supported calibration/home/focus limits and publication jitter. Confirm the focus block's completion/tolerance contract and the exact supported controller/configuration list. These are implementation prerequisites, not reasons to weaken the success condition.
