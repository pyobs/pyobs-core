# Plan: complete BROT initialization through READY_STATE

Date: 2026-10-16

Status: proposed; no implementation or deployment performed

Consumer issue: [pyobs-brot #91](https://github.com/pyobs/pyobs-brot/issues/91).
PLC issues: [BROTLib #68](https://github.com/BROTLib/BROTLib/issues/68), [MONETcommon #70](https://github.com/BROTLib/MONETcommon/issues/70), [IAG50cm #104](https://github.com/BROTLib/IAG50cm/issues/104).

## Agreed design

Use the existing `TELESCOPE.READY_STATE` as the authoritative public readiness state. Add `0.8` for **Calibrating** and publish `1.0` only after the entire startup sequence has completed successfully. This replaces the earlier proposal for a separate final-ready signal, request/result envelope, or initialization-generation protocol. Those additions are not prerequisites for this fix.

| Value | Meaning |
|---|---|
| `-1.0` | Error |
| `0.0` | Parked |
| `0.3` | Parking |
| `0.7` | Initializing: startup preparation and other pending startup work |
| `0.8` | Calibrating: calibration/homing and automatic startup positioning |
| `1.0` | Online: startup complete and operational |

Keep `0.8` through automatic home/positioning and remaining initialization-owned focus movement, including intermediate standstill. A controller may use `0.7` for preparation and `0.8` for the subsequent calibration/positioning phase. Neither state is ready. `1.0` must never appear between startup phases. Normal slew/tracking after completed startup remains online; motion is reported separately by `TELESCOPE.MOTION_STATE`.

Internal mechanical readiness remains distinct from this public state. Do not gate a home state machine on public `READY_STATE == 1.0` when that state machine must finish before publishing 1. Do not change `TELESCOPE.STATUS.GLOBAL`, which is a separate health/status field.

## Fleet scope and evidence

The [fleet inventory](2026-10-16-brot-fleet-inventory.md) identifies MONET/N, MONET/S, and IAG50. MONET sites share MONETcommon but require separate configuration acceptance; IAG50 has its own controller and implements telescope interfaces directly rather than inheriting the BROTLib RaDec controller. HalfBROT is a hardware library, not another site.

Current IAG `_PowerOn` clears `bPower`, marks powered, and requests automatic home. Public readiness can become 1 before sequential HA/Dec home finishes. The home terminal stage assigns focus-home without waiting for unfinished focus movement. The inspected site has identical focus park/home targets, so a separate final focus move does not necessarily occur.

MONET keeps `bPower` set through cover opening, calibration, and mount/derotator home movement. Audit its own final completion/cleanup rather than adding IAG-specific movements. Its focus calibration can restore a stored position or physically home; it does not request IAG's extra focus-home stage.

Resolve the inventory's IAG MQTT-name discrepancy and south configuration-link discrepancy against installed configuration before rollout. Local source versions do not establish running firmware or resolved PLC libraries. Public issues should contain public source findings, not private deployment evidence.

## PLC changes

1. Document the state table and full-startup meaning of 1.0 in BROTLib interfaces/telemetry. Keep the existing MQTT field, numeric wire type, and startup commands.
2. In each concrete controller, select public readiness from the complete startup lifecycle, not just powered axes or an instantaneous stopped condition. Set a pending state when initialization is accepted, before startup work can execute or telemetry can publish online.
3. Publish 0.8 during calibration/homing and automatic startup positioning. Carry it without a 1.0 gap across IAG's power-to-home handoff and until any remaining initialization-owned focus work finishes. Validate completion flags against the current commands, including already-at-target cases.
4. Preserve mechanical `bReady` for internal sequencing. Keep error reporting ahead of online selection. A stopped/failed/expired startup must not fall through to 1.0 merely because axes remain enabled or startup flags were cleared.
5. On error, publish the existing error state; on park, use parking/parked. Define a truthful non-online state for an aborted, partially initialized telescope and the existing diagnostic/status information that lets clients fail rather than report success. Do not label partially initialized hardware parked unless it actually is parked. A new public interrupted value is not assumed by this plan.
6. Check all startup entry points, including local controls and closed-cover power-on where supported. Repeated init must not unexpectedly restart a running startup; an already initialized telescope can remain online.
7. Preserve safety and stop priority and coordinate physical abort cleanup with existing issues. Park currently waits behind MONET power-on and is cleared by IAG power-on: any changed park-during-startup policy must be explicit and tested. Do not expand this change into an unrelated arbitration rewrite.
8. Handle IAG pending-home expiry without false online, and MONET mode changes that suspend conditional controller invocation without leaving a misleading public state.
9. Publish READY_STATE on changes and periodically while stationary. Document cadence, retained behavior, disconnect/restart handling, and compatible stale limits. If publishing is conditional, ensure paused control does not keep replaying a misleading online state as fresh.

Implementation tracking: BROTLib #68 defines the shared contract; MONETcommon #70 implements it for North and South; IAG50cm #104 implements the separate equatorial sequence. Broader controller inheritance migration is not required.

## Python changes: status mapping and regression coverage

The PLC fixes the early completion by delaying READY_STATE 1.0. Python continues using the existing field, command, and initialization loop.

**pybrotlib:** add `TelescopeStatus.CALIBRATING` and map raw 0.8 to it in `components/telescope.py`. Preserve the other mappings and test the new value. Check explicit enum consumers, including BROTgui, for compatibility with the added status.

**pyobs-brot:** map CALIBRATING alongside INITIALIZING to `MotionStatus.INITIALIZING` and `IReady=false` in `_update()`. The existing `init()` loop already stays pending for 0.7/0.8 and returns at 1.0; retain that behavior and the existing weather, error, telemetry-health, cancellation and RPC timeout handling. No new Python completion mechanism is needed.

Add focused regression tests proving that 0.7 and 0.8 keep `init()` pending, 1.0 completes it, and CALIBRATING publishes initializing/not-ready. Include the existing failure and cancellation paths to ensure the small mapping change does not regress them. Controller tests, rather than Python heuristics, prove that 1.0 cannot occur before startup finishes.

## Separate hardening follow-ups

Per-field telemetry freshness/retained-message tracking, post-command observation barriers, configurable direct-call deadlines, command acknowledgement, concurrent-init joining, movement-admission/lock redesign, and additional abort cleanup are independent hardening topics. They are not implementation work or acceptance prerequisites for this PLC readiness fix. No new request IDs, generation counters, result envelopes, telemetry topics, capability handshake, or legacy opt-in mode is planned.

The existing timeout decorator supplies RPC metadata rather than a direct-call deadline; this observation is retained for a separate follow-up, not a requirement to redesign `init()` here. Existing telemetry-health behavior remains in place; this change does not claim to fix every stale-cache or interruption-reporting limitation.

## Compatibility and rollout

Document that the corrected meaning of 1.0 requires updated controller behavior. The numeric field already exists, so no new telemetry-capability handshake is required. Firmware that publishes 1.0 early cannot provide this guarantee; do not describe a Python-only update as fixing it.

Release pybrotlib's 0.8 mapping before controllers expose the new state to consumers that cannot handle it. Coordinate PLC and pyobs-brot updates for both controller families and all three sites; record tested application/library versions and per-site rollback steps. Keep existing 0.7-only controllers understood during staged rollout, while making clear whether their 1.0 semantics have been validated. No unrelated compatibility break or extra legacy opt-in mode is needed solely to introduce 0.8.

## PLC and focused Python acceptance

| Scenario | Required result |
|---|---|
| Startup accepted; preparation begins | Readiness leaves online before work starts; 0.7/0.8 are not ready. |
| Calibration and automatic positioning | 0.8 remains pending through intermediate stops. |
| IAG power-to-home handoff | No transient 1.0; home can progress using internal readiness. |
| Mount finishes but startup-owned focus remains active | No 1.0 until required focus work finishes. |
| Startup finishes successfully | PLC publishes 1.0; the existing init loop returns and readiness becomes true. |
| Normal later slew/tracking | Remains online; separate motion telemetry describes movement. |
| Python status mapping | Raw 0.8 maps to CALIBRATING and publishes initializing/not-ready. |
| Python initialization loop | 0.7 and 0.8 remain pending; 1.0 completes; existing error/cancellation paths are preserved. |
| Failure, stop/reset/interruption, pending-home expiry | No false 1.0; correct error/non-online handling and cleanup. |
| Park request during each phase | Documented controller-specific policy; no premature online. |
| MONET mode change during startup | No misleading fresh online while control is paused. |
| MONET/N, MONET/S, IAG50 | Separate configuration validation; correct family-specific completion boundary. |

Run targeted pybrotlib/pyobs-brot tests and normal checks. Compile and test both controller implementations. Controlled hardware acceptance at all three sites should show 0.7/0.8 through startup, 1.0 only after completion, safe interruption, and movement immediately after a successful init without overlap. This plan does not itself authorize firmware deployment or hardware movement.
