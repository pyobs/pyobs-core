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

## pybrotlib changes

- Add `TelescopeStatus.CALIBRATING` and map raw 0.8 to it in `components/telescope.py`. Preserve all other documented mappings; unknown values remain unknown.
- Keep the existing `power_on()` command and READY_STATE telemetry schema. No new topic, request ID, generation, or final-ready boolean is required.
- Track validity/freshness of the selected telescope's READY_STATE. Missing/default values and retained snapshots alone are not proof of live readiness; unrelated telemetry must not refresh this field's age. Invalidate trust on disconnect/reconnect until fresh live readiness arrives.
- Test the added status, full sequence, unknown values, missing/retained/stale telemetry, and reconnect behavior. Audit other consumers, including BROTgui, for explicit handling of the added enum member.

## pyobs-brot changes

- In `_update()`, map INITIALIZING and CALIBRATING to `MotionStatus.INITIALIZING` and `IReady=false`. Publish ready=true only for fresh ONLINE. Keep PLC health/error checks before success decisions.
- `init()` retains weather checks and waits through both 0.7 and 0.8. For a healthy telescope already online, return without issuing a redundant power-on. For an already pending startup, wait rather than restarting it.
- For a newly issued power-on from a non-online state, evaluate only live READY_STATE publications received after issuing the command; do not let the pre-command cache or retained online value satisfy completion. A fresh 1.0 can complete a fast startup without requiring the client to have sampled 0.7 or 0.8. Readiness publication alone is not a general command acknowledgement; test broker delivery/reconnect behavior and fail on loss of liveness rather than silently claiming success.
- Use READY_STATE as the completion criterion, not mechanical motion samples. A healthy, live 1.0 now means the PLC has finished startup; Python must not add another guessed settle delay.
- Preserve failure and interruption handling using the corrected readiness lifecycle, existing diagnostics, and local stop/park state. If an interruption has no distinct terminal readiness value, the client still must not return success; retain a bounded wait and report interruption where existing signals identify it. Do not invent a separate result protocol to resolve this.
- Add a real configurable local deadline, including direct Python calls, and align RPC timeout metadata. The existing decorator attaches metadata rather than enforcing a direct-call deadline. Choose defaults from actual controller limits.
- Raise initialization-appropriate errors for hardware failure, telemetry loss and timeout; propagate task cancellation. A waiter ending must not publish ready=true while hardware startup remains unresolved. Avoid unconditional late stop cleanup that could affect another operation.
- Audit concurrent init and conflicting mount/focus/offset command admission, including inherited lock ordering. Pending startup must not overlap acquisition/movement; preserve available stop/park handling.

## Compatibility and rollout

Document that the corrected meaning of 1.0 requires updated controller behavior. The numeric field already exists, so no new telemetry-capability handshake is required. Firmware that publishes 1.0 early cannot provide this guarantee; do not describe a Python-only update as fixing it.

Release pybrotlib's 0.8 mapping before controllers expose the new state to consumers that cannot handle it. Coordinate PLC and pyobs-brot updates for both controller families and all three sites; record tested application/library versions and per-site rollback steps. Keep existing 0.7-only controllers understood during staged rollout, while making clear whether their 1.0 semantics have been validated. No unrelated compatibility break or extra legacy opt-in mode is needed solely to introduce 0.8.

## Regression and acceptance matrix

| Scenario | Required result |
|---|---|
| Startup accepted; preparation begins | Readiness leaves online before work starts; 0.7/0.8 are not ready. |
| Calibration and automatic positioning | 0.8 remains pending through intermediate stops. |
| IAG power-to-home handoff | No transient 1.0; home can progress using internal readiness. |
| Mount finishes but startup-owned focus remains active | No 1.0 until required focus work finishes. |
| Startup finishes successfully | PLC publishes 1.0; fresh state allows init to return and ready=true. |
| Normal later slew/tracking | Remains online; separate motion telemetry describes movement. |
| Already online or fast startup | No redundant restart and no requirement to sample a moving/pending edge. |
| Failure, stop/reset/interruption, pending-home expiry | No false 1.0; correct error/non-online handling and cleanup. |
| Park request during each phase | Documented controller-specific policy; no premature online. |
| MONET mode change during startup | No misleading fresh online while control is paused. |
| Stale/retained state, disconnect, PLC offline/restart | Cannot satisfy completion from cached online; fail or remain bounded appropriately. |
| Missing/unknown readiness, unrelated telemetry traffic | No inferred success or false freshness. |
| Concurrent init and conflicting movement | No restarted startup or overlapping hardware commands. |
| Direct call, timeout, cancellation | Bounded wait; correct exception/cancellation; no premature readiness. |
| MONET/N, MONET/S, IAG50 | Separate configuration validation; correct family-specific completion boundary. |

Run targeted pybrotlib/pyobs-brot tests and normal checks. Compile and test both controller implementations. Controlled hardware acceptance at all three sites should show 0.7/0.8 through startup, 1.0 only after completion, safe interruption, and movement immediately after a successful init without overlap. This plan does not itself authorize firmware deployment or hardware movement.
