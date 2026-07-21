# External interfaces registry

Status: implemented, closed. Originally two standalone documents,
`external-interfaces-spec.md` and `external-interfaces-implementation-plan.md`, folded
into `DEVELOPMENT.md` once implemented; restored here as its own design doc under the new
`specs/design/` convention.


### Problem

`Interface` (`pyobs/interfaces/interface.py`) was a plain ABC — nothing
technically stopped an external package from subclassing it, but resolution
silently dropped anything that did. Three chokepoints hardcoded lookups
against the `pyobs.interfaces` module namespace specifically:

1. `Module._get_interfaces_and_methods()` (`pyobs/modules/module.py`) — the
   **publishing** side, and the one that actually mattered most: it built
   `Module._interfaces` (what every comm backend reads — `LocalComm.get_interfaces()`
   returns it directly, `XmppComm` iterates it to add disco#info features) by
   scanning `inspect.getmembers(pyobs.interfaces, predicate=inspect.isclass)`.
   A module implementing an external interface never had it added here, so
   it was never advertised at all, over *any* backend — the other two
   chokepoints were moot without this one.
2. `XmppComm._get_interfaces()` (`pyobs/comm/xmpp/xmppcomm.py`) —
   `getattr(pyobs.interfaces, name, None)` to resolve a disco#info feature
   string back to a class.
3. `Comm._interface_names_to_classes()` (`pyobs/comm/comm.py`) — the same
   `inspect.getmembers` scan, for the same purpose, used only by `XmppComm`.

### Design: import-time registry via `__init_subclass__`

A module-level `_REGISTRY: dict[str, type[Interface]]` in `interface.py`,
populated by `Interface.__init_subclass__`. Registration happens at
class-definition time, which is exactly when it needs to be available: both
the module implementing an external interface and any code building a typed
proxy for it already have to import it, the same implicit constraint core
interfaces already rely on.

**The registry must only register genuine interface definitions, not every
concrete class that happens to subclass one.** Concrete module classes (e.g.
`BaseCamera(Module, ICamera, IExposureTime, IImageType)`) also transitively
subclass `Interface`. The filter: a base only counts as "pure" if it's
`Interface` itself or is *already in the registry*. Checking registry
membership (rather than the weaker `issubclass(base, Interface)`) matters
and was not obvious up front — the first version of this filter used the
weaker check and shipped a real bug: `BaseCamera` transitively satisfies
`issubclass(BaseCamera, Interface)` (via `ICamera`) despite mixing in
`Module`, which let `DummyCamera(BaseCamera, ...)` register itself as an
"interface" too. Caught by the existing test suite (`DummyCamera()`
instantiation crashed with `TypeError: None is not a callable object`, from
chokepoint 1's rewrite iterating `DummyCamera`'s own class dict for a
method that didn't exist) — not by design review. Checking registry
membership instead of `issubclass` propagates purity down the whole
inheritance chain for free, since `BaseCamera` itself never registers.

Two alternatives considered and rejected for the purity check, both with
concrete counter-examples in this exact domain: abstractness
(`ABCMeta`/`isabstract`) doesn't discriminate, since `BaseCamera` is
abstract too (`get_image_format` etc. deferred to concrete drivers); a
name-prefix convention (`cls.__name__.startswith("I")`, even tightened to
`I` + capital second letter like `ICamera`) breaks on real acronym-prefixed
driver names — **INDI** is a real astronomical device SDK, so `INDICamera`
(`I` + capital `N`) would misclassify, as would `IAGVTController` for a
`pyobs-iagvt`-style package.

**Collision handling**, increasing cost: (1) convention only — document a
naming prefix, zero mechanism; (2) **fail fast at import** (implemented) —
`__init_subclass__` raises `TypeError` immediately when two *distinct*
class objects claim the same name (re-importing the same module twice
resolves to the same object and is a no-op); (3) fully-qualified wire names
— change the disco#info feature string from bare `__name__` to
`module.qualname` for anything outside `pyobs.interfaces`. Tier 3 is
**explicitly not built** — no real external interface exists yet, and
committing to a wire-format change ahead of need is exactly the kind of
thing that's annoying to undo later. The purity filter also narrows what
can collide under tier 2: concrete module/driver classes — the far more
numerous, far less name-coordinated population across independent hardware
packages — never enter the registry, so the fail-fast only fires for
genuine interface-name clashes.

### Implementation

| File | Change |
|---|---|
| `pyobs/interfaces/interface.py` | `_REGISTRY`, purity-filtered `__init_subclass__`, `get_registered_interface()`, `registered_interfaces()` |
| `pyobs/modules/module.py` | `_get_interfaces_and_methods()` scans `registered_interfaces()` instead of `pyobs.interfaces` |
| `pyobs/comm/xmpp/xmppcomm.py` | `_get_interfaces()` uses `get_registered_interface(name)` |
| `pyobs/comm/comm.py` | `_interface_names_to_classes()` collapsed to a registry lookup, replacing the `inspect.getmembers` scan |

No changes needed to `pyobs/interfaces/__init__.py` (keeps re-exporting core
interfaces; resolution no longer depends on that module's namespace),
`LocalComm`/`DummyComm` (no string-based resolution of their own — though
both depended on the `module.py` fix to see external interfaces in
`.interfaces` at all), the disco#info wire format, or capabilities/state
pub-sub (already keyed by `type[Interface]`, not by name or origin).

A second real bug surfaced during implementation, unrelated to the registry
design itself: two test helpers (`tests/robotic/scripts/test_autofocus.py`,
`test_darkbias.py`) build a `MagicMock.__class__` from interface-only bases
via `type("Camera", tuple(interfaces), {})` to make `isinstance()` checks
pass — structurally indistinguishable from a real composite interface, so
it now legitimately registers. The old code reused the bare name
`"Camera"`/`"Telescope"` on every call, colliding with itself across
repeated test invocations (a fresh `type()` object each time, same name).
Fixed with a small `_isinstance_class()` helper that uniquely names each
throwaway mock class — the production equivalent (`Proxy.__init__`,
`pyobs/comm/proxy.py`) is unaffected, since its dynamic class always
includes the base `Proxy` class itself, which isn't an `Interface`
subclass and so fails the purity filter.

### Testing

- `tests/interfaces/test_interface_registry.py` — registration on
  subclassing, composite interfaces, the purity filter and its regression
  case (`ImpureBase`/`ImpureChild`, the exact `BaseCamera`/`DummyCamera`
  bug shape), re-registration of the same object, collision detection
  naming both offending classes.
- `tests/comm/test_comm_interface_resolution.py` — `Comm._interface_names_to_classes`
  resolving core and external interfaces, logging on unknown names.
- `tests/comm/test_version_mismatch.py` — added a case for
  `XmppComm._get_interfaces` resolving a genuinely external interface
  through the registry.
- `tests/modules/test_module_interfaces.py` — `Module._get_interfaces_and_methods`
  discovering an external interface, *not* registering the concrete module
  class itself, method collection, and a sanity check that core interface
  discovery still works.

### Status

✅ Implemented and merged to `develop`. Verified end-to-end against the
worked example from the original spec (an `ISiderostatAlignment`-style
external interface defined outside `pyobs.interfaces`, implemented by a
`Module` subclass, discovered via `.interfaces`, resolved by name through
`Comm._interface_names_to_classes`, with collision detection confirmed
separately) in addition to the test suite above. `ruff` and `pyrefly`
clean; full suite passing.

