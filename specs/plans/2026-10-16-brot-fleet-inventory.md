# BROT initialization: fleet inventory

Date: 2026-10-16. Scope: local deployment recipes, pyobs configuration, and PLC source inspection for [pyobs-brot issue 91](https://github.com/pyobs/pyobs-brot/issues/91).

Three distinct telescope deployments are evidenced in the checked-out configuration and PLC application sources: **MONET/N, MONET/S, and IAG50**. They use two concrete controller implementations. This is a repository-backed inventory, not a live runtime audit or a claim that no additional installation exists outside the inspected trees. Running firmware, resolved libraries, installed Python versions, and present operational status remain unverified. No live hardware commands or deployments were performed.

Related [implementation plan](2026-10-16-brot-initialization-completion.md).

## Telescope matrix

| Telescope | pyobs driver and configuration | Concrete PLC controller | Initialization-owned work and completion gap | Required acceptance coverage |
|---|---|---|---|---|
| MONET/N, McDonald Observatory | `BrotAltAzTelescope`; MQTT telescope name `MONETN`; [configuration](/home/husser/code/pyobs/pyobs-monet/config/north/monet/telescope.yaml:4) | `MONETN` application instantiates `MONETcommon.FB_MonetTelescopeControl`; inherits BROTLib AltAz/base controller and uses HalfBROT hardware blocks | Covers, hydraulic/brake prerequisites, azimuth/elevation calibration, derotator calibration, focus calibration, then mount/derotator home movement. `bPower` holds readiness at 0.7 through the existing power-on sequence. Validate the final READY_STATE=1 boundary and focus/cleanup; use the agreed 0.8 calibration state. | Test this site's actual calibration and home configuration; focus restoration and first calibration; cold/warm startup; stop, reset, failure, and park arbitration. Shared code does not replace site validation. |
| MONET/S, Sutherland | `BrotAltAzTelescope`; MQTT telescope name `MONETS`; [configuration](/home/husser/code/pyobs/pyobs-monet/config/south/monet/telescope.yaml:4) | `MONETS` application instantiates the same `MONETcommon.FB_MonetTelescopeControl`, with its own hardware/configuration | Same family of initialization work as MONET/N; different site targets/calibration and auxiliary configuration. Do not add IAG50's post-power go-home or focus-home sequence to this controller. | Separate site acceptance even when testing the same MONETcommon release; verify configured axes, covers, safety inputs, and home/calibration values. |
| IAG50, Göttingen | `BrotRaDecTelescope`; MQTT telescope name `IAG50`; [configuration](/home/husser/code/pyobs/pyobs-iag50/config/iag50srv/telescope.yaml:4) | Site-local `FB_TelescopeControl IMPLEMENTS I_RaDecTelescope, I_Telescope`; **does not inherit** BROTLib's `FB_RaDecTelescopeControl` | Optional cover-opening phase; HA/Dec calibration and focus enable/calibration; `_PowerOn` sets powered and requests automatic go-home; sequential HA/Dec home; final assignment of focus-home target. Readiness can be 1 before home finishes, and the home terminal stage does not wait for the focus move. | Keep pending across power-to-home handoff, intermediate standstill and final focus movement; test optional-axis/device behavior against supported configurations and all interruption/failure paths. |

The current three primary YAML files do not explicitly set `ra_in_hours`, `multi_field_commands`, `publish_dut1`, initialization deadlines, or a new calibration-state setting. Therefore local driver defaults apply when used with this checkout; that does not establish what an installed older driver does. MONET/S and IAG50 explicitly configure the pyobs weather module; MONET/N does not in its telescope YAML. These differences must not be erased by a common initialization change.

## Controller evidence and site differences

The concrete runtime instances are in:

- [MONET/N MAIN](/home/husser/code/brotlib/MONETN/MONETN/MONETNRuntime/POUs/MAIN.TcPOU:28).
- [MONET/S MAIN](/home/husser/code/brotlib/MONETS/MONETS/MONETSRuntime/POUs/MAIN.TcPOU:28).
- [IAG50 MAIN](/home/husser/code/brotlib/IAG50cm/IAG50cm/POUs/MAIN.TcPOU:11).

Source home targets illustrate why acceptance must be configuration-specific; these are inventory facts, not instructions to move hardware:

| Site | Mount home targets in local MAIN | Additional relevant configuration |
|---|---|---|
| MONET/N | azimuth 190°, elevation 40°, derotator −116.42° | Focus park 53.8; separate elevation/azimuth calibration offsets. [Source](/home/husser/code/brotlib/MONETN/MONETN/MONETNRuntime/POUs/MAIN.TcPOU:36). |
| MONET/S | azimuth 175°, elevation 40°, derotator 0° | Focus park 36.0; separate elevation/azimuth calibration offsets. [Source](/home/husser/code/brotlib/MONETS/MONETS/MONETSRuntime/POUs/MAIN.TcPOU:39). |
| IAG50 | hour angle 0°, declination 52° | Focus home and park both 16.3. [Source](/home/husser/code/brotlib/IAG50cm/IAG50cm/POUs/MAIN.TcPOU:21). |

MONET's implementation is [FB_MonetTelescopeControl](/home/husser/code/brotlib/MONETcommon/MONETcommon/MONETcommon/FB_MonetTelescopeControl.TcPOU:4). Its readiness selection prioritizes `bPower` over `bReady` (around line 473). IAG's [controller](/home/husser/code/brotlib/IAG50cm/IAG50cm/POUs/FB_TelescopeControl.TcPOU:4) instead publishes readiness from `bReady` (around line 772), while `_PowerOn` hands over to go-home (around line 1460). These are different sequences, not interchangeable implementations.

MONET's terminal stage checks mount/derotator `MoveDone`, not an extra focus-home movement. Its focus calibration can restore a stored position or physically home and resets its target to avoid an automatic subsequent move ([focus implementation](/home/husser/code/brotlib/HalfBROT/HalfBROT/HalfBROT/POUs/FB_FocusControl.TcPOU:116)). IAG's configured `focusPark == focusHome` means its final target assignment does not necessarily cause a distinct move; the guarantee still needs to cover any unfinished initialization-owned focus movement. Test actual controller semantics rather than requiring a moving edge for every device.

MONET's MAIN calls the telescope controller conditionally in automatic mode ([north](/home/husser/code/brotlib/MONETN/MONETN/MONETNRuntime/POUs/MAIN.TcPOU:97), [south](/home/husser/code/brotlib/MONETS/MONETS/MONETSRuntime/POUs/MAIN.TcPOU:99)). Mode changes during initialization therefore need explicit interruption/liveness handling. IAG has another non-success path: a go-home request that never starts can be cleared after two minutes without setting an error ([source](/home/husser/code/brotlib/IAG50cm/IAG50cm/POUs/FB_TelescopeControl.TcPOU:452)).

The agreed fix reuses READY_STATE, adds 0.8 for calibration/automatic startup positioning, and reserves 1.0 for complete startup. The earlier separate result/generation protocol is superseded; current pybrotlib still needs the 0.8 status mapping. Failure flags, command arbitration, and stage resets exist, but a disappearing command flag is not proof of successful completion. In particular, park is not currently a uniform initialization interrupt: MONET prioritizes power-on over park, and IAG's power branch clears a pending park request. Making park reliably interrupt startup requires an explicit controller behavior change and tests, not merely preserving an existing cross-fleet contract.

## Supporting projects and duplicate configurations

| Item | Classification | Inventory treatment |
|---|---|---|
| HalfBROT | Hardware abstraction library for Halfmann mount axes, focus, covers, hydraulics and pendant | Dependency of MONET telescopes, not an additional telescope. [README](/home/husser/code/brotlib/HalfBROT/README.md:1). |
| MONETcommon | Shared MONET telescope controller library | One implementation used by two separately configured sites. |
| BROTLib | Shared interfaces, base/AltAz/RaDec types, communication and telemetry | Audit shared protocol here; generic controller classes are not deployments. IAG's equatorial driver does not imply inheritance from the generic RaDec PLC block. |
| AstroBROT | Astronomy calculation library | Dependency, not a deployment. |
| MONETRoof | Enclosure-control library | Separate lifecycle; do not equate roof ready with telescope initialization complete. MONET/S has a configured `BrotRoof` consumer. |
| IAG50 `BrotDome` | Separate pyobs module sharing the telescope's PLC/site | Compatibility consumer, not an additional telescope. [Config](/home/husser/code/pyobs/pyobs-iag50/config/iag50srv/dome.yaml:4). |
| BROTgui | Another client capable of issuing power-on and closed-power-on commands | Include these entry points in PLC lifecycle support; client-only pyobs guards cannot enforce the contract. [Client](/home/husser/code/brot/BROTgui/BROTgui/qtelescopecontrol.py:220). |
| `pytel-dev/configs/mcdtel.yaml` | Legacy `BrotTelescope` configuration identifying MONET/N | Duplicate site; stale class/API, not evidence of a fourth deployment. |
| `pytel-dev/configs/brottelescope.yaml` | Development configuration identifying MONET/S | Duplicate site. |
| `pytel-dev/configs/brot-telescope.yaml` | Localhost development configuration using legacy `BrotTelescope` | No physical telescope identity established. |
| IAG50 `iag50cam/_telescope.yaml` | Older duplicate, MQTT name `50cm` instead of `IAG50` | Topology document describes it as disabled. Do not count as another telescope or silently use its namespace for acceptance. |
| STELLA1 labels in MONET projects | Historical naming in inherited project files | No independent STELLA deployment established by these sources. |
| Monti and IAGVT telescope configs | Different drivers (`Monti`, site `SolarTelescope`) | Not BROT telescope consumers in the inspected configurations. |
| TcUnit/controller test projects | Test fixtures | Not physical deployments. |

## Local version baseline

These are **checked-out source versions**, not versions read from operating PLCs or Python environments. Wildcard PLC library references do not pin a resolved build.

| Component | Local declared version | Local HEAD |
|---|---|---|
| pyobs-brot | 2.4.1; requires pybrotlib ≥1.7.0 | `3ae7d6f850fe` |
| pybrotlib (`brot/pyBROT`) | 1.7.0 | `f83896ad5445` |
| BROTLib | 0.7.0 | `6d6035dda0d3` |
| HalfBROT | 0.5.1 | `d343a4b555fb` |
| MONETcommon | 0.8.0 | `38b589662f42` |
| MONET/N application | 0.4.0 | `5f94f8986b4a` |
| MONET/S application | 1.4.0 | `67e683db6140` |
| IAG50cm application | 0.3.11 | `2196d38ef4ee` |
| pyobs-monet config repository | Repository snapshot | `6ff13cb48b13` |
| pyobs-iag50 config repository | Repository snapshot | `6d76a3f6692f` |
| Local fleet deployment recipes | Repository snapshot | `792b9b2edfa9` |

Application versions come from the actual `.plcproj` files, not README version tables. MONET/N and MONET/S reference BROTLib, HalfBROT, MONETcommon and other libraries with wildcard resolutions; IAG50 also has a wildcard BROTLib reference and a fixed AstroBROT 0.4.3 reference. Installed/resolved versions must be recorded separately before release acceptance.

## Deployment evidence and outstanding verification

The local fleet recipes reference the same pyobs-monet and pyobs-iag50 config trees, corroborating the three-site mapping. They do not prove current service state. Site topology documents contain dated observations; in particular the IAG50 status section is dated 2026-09-06 and must not be treated as today's operational status.

One concrete recipe discrepancy needs checking against the installed configuration: the south/monet installer links the **north/monet** YAML tree, whereas the site-specific south telescope YAML and topology identify MONET/S. This inventory does not infer that the live south telescope uses north configuration. Record the installed symlink target and rendered telescope settings before rollout. A portal image also contains an old pyobs-brot package pin; that image is not evidence of the telescope service's installed version.

**IAG50 namespace discrepancy:** the primary pyobs telescope YAML uses `name: IAG50`, but the checked-out PLC MAIN configures the MQTT prefix `50cm` ([source](/home/husser/code/brotlib/IAG50cm/IAG50cm/POUs/MAIN.TcPOU:72)). The older duplicate pyobs config also uses `50cm`. Do not resolve this by guessing which checkout is deployed or changing a prefix during this inventory. Confirm the installed module configuration and active PLC topic prefix before testing readiness telemetry and command routing. MONET's checked-out prefixes match their primary YAML names (`MONETN` and `MONETS`).

Remaining runtime fields for **each of MONET/N, MONET/S and IAG50**:

1. Installed telescope config path, actual MQTT site identity, active pyobs class, Python package versions and service state.
2. Active PLC application build identity, boot project, resolved BROTLib/HalfBROT/MONETcommon versions where applicable, and configuration differences from this source snapshot.
3. Enabled initialization devices, cover-opening policy, focus restoration/calibration path, controller-specific terminal conditions and timing limits.
4. Observed live telemetry fields/cadence, READY_STATE 0.8/1.0 semantics, disconnect/restart behavior and explicit non-success outcomes.
5. Per-site simulation/controller-test results and controlled hardware acceptance results before adopting a shared driver change.

No inspected source establishes an additional BROT telescope beyond these three. Any installation outside the local configuration/deployment trees remains an explicit inventory gap, not an assumed absence. Completion of this repository inventory does not mean hardware acceptance is complete.

## Consequences for issue 91

- Implement one shared semantic contract with separate completion boundaries for the MONET family and IAG50 implementation.
- Exercise both `BrotAltAzTelescope` and `BrotRaDecTelescope` and all three site configurations. MONET/N and MONET/S remain separate release acceptance rows despite sharing controller code.
- Do not change default driver compatibility based solely on an IAG50 firmware change. Account for controller support and migration at all three sites.
- Resolve park/interruption semantics explicitly and test every startup entry point, including non-pyobs clients.
- Do not publish local addresses, credentials, or private deployment evidence as part of the public issue; this inventory deliberately omits them.
