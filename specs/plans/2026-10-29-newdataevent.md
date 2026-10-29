# Plan: generic `NewDataEvent`

Status: step (a) implemented (pyobs-core#1025); step (c) proposed; step (b) undecided. Decisions of 2026-10-29
are in "Decisions"; remaining open items at the end.
Repos: pyobs-core, pyobs-gui, pyobs-iagvt

## Summary

Add `NewDataEvent(filename)` to `pyobs/events/` as a concrete event for data that is neither image nor
spectrum (e.g. FTS output), make `NewImageEvent` and `NewSpectrumEvent` subclasses of it, and fix
`BaseSpectrograph.open()` so it declares the events it sends. There is no `data_type` field: the event
class says what kind of data it is. Without it the subclassing adds nothing to the payload and does not
touch the `__init__` signatures, so wire format, disco#info schema and `version = 1` of the existing
events are unchanged and existing subscribers keep working.

Recommendation: do step (a). Step (b) (`BaseData` base class) is revisited after (a); the planned
modules that send `NewDataEvent` directly are the case for it, see below.

## Decisions (Tim, 2026-10-29)

- No `data_type` field and no `DataType` enum.
- `NewDataEvent` is concrete and sent directly by future `BaseData` implementations whose data is
  neither image nor spectrum. Image and spectrum modules keep sending their own subclass (a bare
  `NewDataEvent` would lose `image_type`, which several core subscribers need).
- `NewImageEvent`/`NewSpectrumEvent` stay at `version = 1`, signatures unchanged.
- The `from_dict` hard-coded-class bug is fixed in a separate commit, not in a2.
- `FileWrittenEvent` stays outside this hierarchy (different meaning: file archived vs. data produced).
- After release, as separate follow-ups: remove the pyobs-iagvt `fts.py:155-158` workaround and switch
  pyobs-gui `DataDisplayWidget` to one `NewDataEvent` handler.
- Step (b) is decided after (a).
- Sender-side registration is exact-class only (decided later on 2026-10-29): a handler-less
  `register_event(X)` declares only `X`, not its subclasses, so a module that sends both `NewDataEvent` and
  `NewImageEvent` registers both. No `derived` keyword. Registration with a handler keeps expanding to
  derived events (the point of the hierarchy, and covered by existing tests). See step (c).

## Verified facts

- `Comm.register_event()` (`pyobs/comm/comm.py:424`) expands to `_get_derived_events()` (`:413`), i.e.
  all classes in `registered_events()` that are `issubclass` of the given one. Handlers are stored per
  concrete class; duplicate handlers are skipped.
- The expansion applies to the sender side too (current behaviour, removed by step (c)): without a handler, `register_event()` puts the whole
  expanded list into `_events_sent` (`comm.py:450`) and passes it to `_register_events()` (`:454`).
  There is no non-expanding variant today. In `XmppComm._register_events()` (`xmppcomm.py:988`) every
  class in that list gets a disco feature `urn:pyobs:event:{name}:{version}` (`:995`) and, for a module,
  a pre-created pubsub node (`:1016`, each `_create_node` can take up to ~90s against an unresponsive
  pubsub service, per the comment there). disco#info then lists each one with `role="send"`
  (`xmppcomm.py:1306-1311`, `_event_role` at `:40`), and peers subscribe to every advertised event they
  have a handler for (`_got_online`, `xmppcomm.py:835-842`). So a module that declares
  `register_event(NewDataEvent)` without handler also advertises `NewImageEvent` and `NewSpectrumEvent`
  as sent: no wrong data is delivered, but peers (GUI, dashboards) subscribe to two empty nodes and
  pyobs-web-client shows the module as an image/spectrum producer. Existing sender registrations are not
  affected by a2: `NewImageEvent`/`NewSpectrumEvent` get no new subclasses, and nobody registers
  `NewDataEvent` as sender in step (a). Existing test of the sender path:
  `tests/comm/test_events.py:291` (`test_register_event_without_handler_declares_plugin_event_as_sent`).
- Dispatch is exact class match: `event.__class__ in self._event_handlers` (`comm.py:699`). Together with
  the expansion above, a handler registered for `NewDataEvent` receives `NewImageEvent` and
  `NewSpectrumEvent`, as long as those are imported at registration time. They are, since
  `pyobs/events/__init__.py` imports both. Old subscribers to `NewImageEvent` see no difference.
  Existing test proving the mechanism: `tests/comm/test_events.py:276`
  (`test_handler_for_core_event_also_covers_plugin_subclass`).
- XMPP node and feature names use `__name__` and `version`: `xmppcomm.py:1040`
  (`pyobs:event:{module}:{name}:{version}`), `:995` (`urn:pyobs:event:{name}:{version}`). Class names of
  the existing events do not change, so nodes do not change.
- Event registry (`pyobs/events/event.py`): `__init_subclass__` registers every subclass by `__name__`;
  a second class with the same name from a different module/qualname raises `TypeError`. `version`
  defaults to 1. Each class sets `__module__ = "pyobs.events"`. No other repo in `/home/husser/code/pyobs`
  defines a `NewDataEvent` (grepped).
- Wire payload is JSON: `send_event()` sends `json.dumps(event.to_json())` (`xmppcomm.py:954`),
  receiver calls `EventFactory.from_dict()` -> `cls.from_dict(data)`. Both existing `from_dict`s pick
  known keys and ignore extras.
- Disco#info event schema is generated from the `__init__` signature (`serializer.py:547`,
  `_event_schema_to_xml`). If `NewImageEvent.__init__`/`NewSpectrumEvent.__init__` keep their signature,
  their advertised schema is unchanged.
- `NewImageEvent.from_dict` and `NewSpectrumEvent.from_dict` construct the hard-coded class instead of
  `cls` (`newimage.py:53`, `newspectrum.py:34`). Pre-existing bug: a plugin subclass of `NewImageEvent`
  without its own `from_dict` deserializes as `NewImageEvent`. Not caused by this change.
- Not an issue now (no enum): both `newimage.py` and `newspectrum.py` define a module-level TypedDict called
  `DataType`.
- `BaseSpectrograph.open()` (`basespectrograph.py:64`) only calls `Module.open()`, `set_state(IExposure)`
  and `_datasequence_open()`. It registers neither `NewSpectrumEvent` nor `ExposureStatusChangedEvent`,
  although it sends both (`:164`, `:207`). `BaseCamera.open()` registers both (`basecamera.py:162-163`),
  `BaseVideo.open()` registers `NewImageEvent` (`basevideo.py:302`). CHANGELOG.md:431 documents the same
  bug class for BaseVideo (peers never subscribe if the sender does not advertise). pyobs-iagvt works
  around it: `pyobs_iagvt/modules/fts.py:155-158` registers both events itself.
- Finish paths:
  - `BaseCamera.__finish_product` (`basecamera.py:~420-470`): EXTNAME, IMAGETYP, custom + requested x2 +
    `add_fits_headers`, meridian flip, data pipeline, `format_filename` (None raises), `vfs.write_image`,
    event.
  - `BaseVideo._finish_image` (`basevideo.py:1170-1213`): data pipeline (name from image meta),
    `format_filename` (None falls back to `image.fits`), in-memory `_cache`, event. Headers are added
    elsewhere.
  - `BaseSpectrograph.__expose`/`store_spectrum` (`basespectrograph.py:~120-165`): EXTNAME, requested x2
    + `add_fits_headers`, `format_filename` (None returns without storing), `vfs.write_fits`, event.
    No pipeline.
- Mixins differ: BaseCamera/BaseVideo use `ImageFitsHeaderMixin`, BaseSpectrograph uses
  `SpectrumFitsHeaderMixin` (both subclass `FitsHeaderMixin`, `mixins/fitsheader.py:124/360/486`).
  `ICamera`, `IVideo`, `ISpectrograph` already derive from `IData`.

## Step (a): NewDataEvent, subclassing, spectrograph fix

Three separate commits, in this order.

### a1. Fix BaseSpectrograph event registration (bug fix, independent)

- `pyobs/modules/camera/basespectrograph.py`, `open()`: after `Module.open(self)`, add
  `if self._comm:` (pattern from `basecamera.py:161`, verify exact guard) register `NewSpectrumEvent`
  and `ExposureStatusChangedEvent` without handler.
- `CHANGELOG.md` `[Unreleased]` Fixed entry.
- Afterwards the workaround in `pyobs-iagvt/pyobs_iagvt/modules/fts.py:155-158` is redundant but harmless
  (register is idempotent for sets). Removal is a separate pyobs-iagvt change.

### a2. Add `NewDataEvent`

- New `pyobs/events/newdata.py`:
  - `class NewDataEvent(Event)`, `__module__ = "pyobs.events"`, `version = 1`.
  - `__init__(self, filename: str, **kwargs)`: `Event.__init__(self)`, `self.data = {"filename": filename}`.
  - `from_dict(cls, d)`: validate `filename` is str, return `cls(filename=...)` (use `cls`).
  - Property `filename`.
  - Docstring: subscribing to `NewDataEvent` also delivers `NewImageEvent` and `NewSpectrumEvent`;
    use `type(event) is NewDataEvent` to select only generic data. Also note the sender side: a
    handler-less `register_event(NewDataEvent)` advertises the subclasses as sent, too (as implemented in
    a2; step (c) removes this behaviour and that sentence).
  - Module-level `class DataType(TypedDict): filename: str` and `self.data: DataType = {"filename": ...}`,
    same convention as the other event modules.
- `pyobs/events/newimage.py`: `class NewImageEvent(NewDataEvent)`; keep
  `__init__(filename, image_type=None, raw=None, **kwargs)` unchanged, call
  `NewDataEvent.__init__(self, filename)`, then assign the complete dict as a literal in today's key
  order (`filename`, `image_type`, `raw`) rather than `.update()`-ing the base dict, so key order and
  type stay explicit. Drop the inherited `filename` property. Payload is byte-identical to today.
  `from_dict` untouched here (a3).
- `pyobs/events/newspectrum.py`: same pattern (payload stays `{"filename": ...}`); fix docstrings
  ("new image").
- Typing of `data`: `Event.data` is `Any` (`event.py:42`) and every event module redeclares
  `self.data: DataType` with its own module-level TypedDict. `newimage.py:9` (`filename`, `image_type`,
  `raw`) and `newspectrum.py:8` (`filename`) both define one called `DataType`; no rename needed (no
  enum, and nothing imports them). After subclassing, `filename` would be declared in three TypedDicts.
  Let the subclass TypedDicts inherit from the one in `newdata.py`
  (`from pyobs.events.newdata import DataType as NewDataType`, `class DataType(NewDataType)` adding
  `image_type`/`raw`; `newspectrum.py` can alias it or subclass without new keys), so `filename: str` is
  declared once and the subclass `data` type is a structural subtype of the base one. Run `pyrefly` on
  `pyobs/events/`: if it reports the redeclared `self.data` as an incompatible attribute override,
  annotate `data` once on `NewDataEvent` as a class-level declaration and use `cast`/narrowing
  properties in the subclasses instead. Payload is unaffected either way.
- `pyobs/events/__init__.py`: import `NewDataEvent` and add to `__all__`.
- `docs/source/api/events.rst`: add a `NewDataEvent` section before `NewImageEvent`.
- Optional: `docs/source/api/comm.rst:66` mention subscribing to `NewDataEvent` for "any data".
- `CHANGELOG.md` `[Unreleased]` Added entry.

### a3. Fix `from_dict` to use `cls` (separate commit)

`NewImageEvent.from_dict` (`newimage.py:53`) and `NewSpectrumEvent.from_dict` (`newspectrum.py:34`) build
the hard-coded class. Change to `cls(...)` so plugin subclasses deserialize as themselves. Add a test with
a plugin subclass. `CHANGELOG.md` Fixed entry.

### Follow-up (optional, outside core, not a step of this plan): use it in subscribers

Nothing in core needs it now. Candidate outside core: `pyobs-gui/pyobs_gui/datadisplaywidget.py:86-87,200`
could register one `NewDataEvent` handler instead of two and use `isinstance(event, NewDataEvent)`. That is
a pyobs-gui change and needs a pyobs-core release first. Not part of this plan.

## Step (c): exact-class sender registration

Decided 2026-10-29 instead of a `derived: bool` keyword (rejected: an opt-in flag would keep the
surprising default forever, and exact-class is what a sender should mean anyway).

- `Comm.register_event()` (`pyobs/comm/comm.py:424`): without a handler, register exactly
  `[event_class]` (`_events_sent` and `_register_events()`); with a handler, keep
  `_get_derived_events()`. `unregister_event()` is unchanged (it only deals with handlers).
- Why it is safe in core: every handler-less sender registration names the concrete class it sends
  (`BaseCamera`/`BaseVideo`/`ImageWriter` etc. register `NewImageEvent`, telescopes register
  `MoveRaDecEvent`/`MoveAltAzEvent`/`OffsetsRaDecEvent`/`OffsetsAltAzEvent`; nobody registers `MoveEvent`
  or `OffsetsEvent`). The only core hierarchy with a sendable base is `NewDataEvent`.
- Risk outside core, not verifiable from this repo: a plugin that sends a subclass of `NewImageEvent`
  and relied on `BaseCamera`'s `register_event(NewImageEvent)` expansion to advertise it. After this change
  it must call `register_event(MyImageEvent)` itself, otherwise peers stop subscribing to it silently.
  Grep sibling repos for subclasses of `NewImageEvent`, `NewSpectrumEvent` and other core events before
  release; mention it under `CHANGELOG.md` Changed.
- Tests: handler-less `register_event(NewDataEvent)` leaves `NewImageEvent`/`NewSpectrumEvent` out of
  `_events_sent`; handler-less `register_event(NewImageEvent)` no longer adds a plugin subclass;
  registration with a handler still expands (existing `test_handler_for_core_event_also_covers_plugin_subclass`
  and `test_register_event_still_covers_core_subclasses`); update
  `test_register_event_without_handler_declares_plugin_event_as_sent` if it relies on expansion; local and
  XMPP schema/role tests that assert the advertised set.
- Docstring of `register_event()` and of `NewDataEvent` updated (the NewDataEvent docstring currently says a
  handler-less registration advertises the subclasses: remove that sentence).
- Order: before or together with the first generic-data sender; independent of (b).

## Step (b): `BaseData` base class. Decided after step (a)

Not part of (a). Reasoning for the earlier no-go still holds for camera/video/spectrograph:

- The actually shared code across the three finish paths is: `format_filename` call (with three different
  None behaviours: raise / fallback / return early), and the 3-line
  `if broadcast and self._comm: await self.comm.send_event(...)`. Header handling differs (BaseVideo adds
  headers elsewhere, BaseCamera adds custom headers and meridian flip), pipeline exists only in
  camera/video, storage is VFS image / in-memory cache / VFS FITS. A template method would deduplicate
  roughly 10-15 lines and need several hooks to express the differences.
- The open() registration is 1-2 lines per class; after a1 it is consistent anyway.
- MRO: `BaseData(Module, FitsHeaderMixin, IData)` combined with `ImageFitsHeaderMixin`/
  `SpectrumFitsHeaderMixin` should linearize (C3 places `FitsHeaderMixin` after the specific mixin)
  (inferred, not tested). It adds one more level to already deep, cooperative-`__init__` hierarchies that
  have had kwargs-forwarding bugs before (issue #764, `tests/modules/camera/test_basespectrograph.py`,
  `pyobs-fli/tests/test_flicamera.py` regression test).
- External breakage: an abstract `_store` (or renaming/merging `_finish_image`/`store_spectrum`) breaks
  every external override listed below. `__finish_product` is name-mangled, so nobody overrides it, but
  `_finish_image` and `store_spectrum` are overridden in 5 external repos.

What changed: Tim plans further data modules (FTS-like) that send `NewDataEvent` directly. That is a
fourth data-producing class, which was the stated trigger for revisiting. The case for `BaseData` is then
for those new modules (and possibly FTS), not for refactoring camera/video. A `BaseData` used only by new
modules avoids the external breakage; making camera/video/spectrograph inherit from it is the costly part
and can be skipped. To be settled once (a) is in and the first such module exists.

If done, the least invasive form is a non-abstract helper, not a template method:

```python
class BaseData(Module, FitsHeaderMixin, IData, metaclass=ABCMeta):
    _data_event: ClassVar[type[NewDataEvent]]  # set by subclass

    async def open(self) -> None:
        await Module.open(self)
        if self._comm:
            # exact-class sender registration (step c): only the class actually sent is advertised
            await self.comm.register_event(self._data_event)

    async def _broadcast_data(self, event: NewDataEvent, broadcast: bool) -> None:
        if broadcast and self._comm:
            await self.comm.send_event(event)
```

Even this mostly moves 3 lines and adds a class. A free function or a small mixin would give the same
without touching the MRO of `Module`.

Whatever form (b) takes, and also for a generic-data sender written without `BaseData`, the first module
that sends a bare `NewDataEvent` needs step (c) first, otherwise it also advertises `NewImageEvent` and
`NewSpectrumEvent`.

## Compatibility and risks (external repos)

Step (a) changes no method signatures and no class names. Affected only in the sense "keeps working,
could be simplified":

Subscribers (unchanged behaviour):
- `pyobs-gui/pyobs_gui/datadisplaywidget.py:86-87,100-102,200` (both events), `camerawidget.py:45`
- `pyobs-iagvt/pyobs_iagvt/widgets/guidingwidget.py:97,108`
- `pyobs-allsky-cloudcover/pyobs_cloudcover/application.py:38,41`
- `pyobs-dashboard-utils/pyobs_dashboard/spectrograph_publisher/spectrograph_publisher.py:32,62`,
  `image_post_processor/image_post_processor.py:41,58`, `image_publisher/image_publisher.py:20,23`,
  `ldp_plotter/ldp_plotter.py` (imports `NewImageEvent`)
- Core: `modules/image/seeing.py:53`, `pipeline.py:57`, `imagewriter.py:46`,
  `modules/pointing/scienceframeguiding.py:36`
- `pyobs-web-client/src/views/CameraView.vue:144` matches `ev.type === 'NewImageEvent'` by name.
  Unaffected since the name stays. Payload unchanged.

Senders (unchanged, `NewImageEvent(filename)` still valid):
- Core: `basecamera.py:463`, `basevideo.py:1210`, `basespectrograph.py:164`, `pipelinecamera.py:58`,
  `images/processors/image/save.py:108`
- `pyobs-iagvt/pyobs_iagvt/modules/suncamera.py:77,180`
- `pyobs-allsky-cloudcover/pyobs_cloudcover/testing/module.py:73`
- `pyobs-dashboard-utils/.../image_importer/image_importer.py:34,47`, `image_post_processor.py:87`,
  `spectrograph_publisher/testing/test_spectrograph.py:33`

Overrides of the finish paths (relevant only for step b):
- `_finish_image`: `pyobs-aravis/pyobs_aravis/araviscamera.py:92`, `pyobs-tis/pyobs_tis/tiscamera.py:97`,
  `pyobs-asi/pyobs_asi/asivideo.py:331`, `pyobs-qhyccd/pyobs_qhyccd/qhyccdvideo.py:344`,
  `pyobs-iagvt/pyobs_iagvt/modules/fibercamera.py:81` (calls `AravisCamera._finish_image` directly);
  called by `pyobs-iagvt/pyobs_iagvt/modules/gregorycamera.py:154`.
- `store_spectrum`: `pyobs-iagvt/pyobs_iagvt/modules/fts.py:464` (calls
  `BaseSpectrograph.store_spectrum` explicitly).

Subclasses of the base classes (relevant only for step b, MRO):
- BaseCamera: pyobs-fli `flicamera.py:27`, pyobs-flipro `fliprocamera.py:42`, pyobs-asi `asicamera.py:55`,
  pyobs-qhyccd `qhyccdcamera.py:39`, pyobs-sbig `src/pyobs_sbig/sbigcamera.py:35`. Several call
  `BaseCamera.__init__/open` explicitly, not via `super()`.
- BaseVideo: pyobs-aravis `AravisCamera`, pyobs-tis `TisCamera`, pyobs-asi `AsiVideo`, pyobs-qhyccd
  `QHYCCDVideo`, pyobs-v4l `v4lCamera`; pyobs-iagvt `GregoryCamera`, `FiberCamera` via AravisCamera.
- BaseSpectrograph: pyobs-iagvt `FTS` (`fts.py:49`), pyobs-dashboard-utils `TestSpectrograph`.

Risks for step (a):
- Mixed versions: `NewImageEvent`/`NewSpectrumEvent` payloads are unchanged. A raw `NewDataEvent` sent
  by a new module is unknown to old peers; `EventFactory.from_dict` returns None there (`event.py`,
  `get_registered_event`), i.e. dropped. Nobody sends it in step (a); it matters once the first generic
  data module ships, so peers (GUI, dashboards) must be upgraded first.
- Release notes: the `CHANGELOG.md` Added entry for a2 (and the release announcement) states that
  every peer that should see generic data (pyobs-gui, pyobs-dashboard-utils, other subscribers) must run
  a pyobs-core with `NewDataEvent` before the first module sends a bare `NewDataEvent`; old peers drop
  it silently, without an error. The pyobs-gui `DataDisplayWidget` follow-up additionally needs that
  pyobs-gui release.
- Sender-side expansion: today a handler-less `register_event(NewDataEvent)` advertises `NewImageEvent` and
  `NewSpectrumEvent` as sent (see Verified facts). Not triggered in step (a); removed by step (c) before
  the first generic-data sender.
- A `NewDataEvent` handler also receives image/spectrum events. Handlers meant for generic data only must
  check `type(event) is NewDataEvent`.
- Subscribing to `NewDataEvent` only covers subclasses imported before `register_event()` (documented
  limitation of `_get_derived_events`). Plugin subclasses imported later are missed. Same as today for
  `NewImageEvent`.

## Tests

Add:
- `tests/test_events.py`: `NewDataEvent` round trip via `to_json`/`EventFactory.from_dict`; invalid
  `filename` raises `ValueError`; `isinstance(NewImageEvent(...), NewDataEvent)` and same for spectrum;
  registry contains `NewDataEvent`.
- `tests/test_events.py` (a2, payload pinning): `NewImageEvent(filename="a.fits",
  image_type=ImageType.OBJECT, raw="r.fits").data` equals
  `{"filename": "a.fits", "image_type": ImageType.OBJECT, "raw": "r.fits"}` and
  `list(...data) == ["filename", "image_type", "raw"]` (dict `==` ignores order, so check keys
  explicitly); same for the defaults (`image_type`/`raw` None); `to_json()["data"]` and
  `json.dumps(to_json()["data"])` identical to the pre-a2 string. Likewise `NewSpectrumEvent(...).data
  == {"filename": ...}` with keys `["filename"]`. Write these before a2 so they pass both before and
  after.
- `tests/comm/test_events.py`: next to `test_handler_for_core_event_also_covers_plugin_subclass`, a test
  that `register_event(NewDataEvent, handler)` puts `NewImageEvent` and `NewSpectrumEvent` in
  `_event_handlers` and dispatches both to the handler.
- `tests/comm/local/test_localcomm.py`: end-to-end over LocalComm, subscriber on `NewDataEvent` receives a
  `NewSpectrumEvent` and a plain `NewDataEvent` sent by another comm (pattern at `:146`).
- `tests/modules/camera/test_basespectrograph.py`: after `DummySpectrograph().open()`, `NewSpectrumEvent`
  and `ExposureStatusChangedEvent` are in `spectrograph.comm._events_sent` (pattern:
  `test_basecamera.py:52`). Fails before a1, passes after.
- a3: plugin subclass of `NewImageEvent` round-trips as the subclass.
- Optional: XMPP schema test (`tests/comm/test_xmpp_serializer_schema.py`) asserting
  `_event_schema_to_xml(NewImageEvent)` still lists only `filename`, `image_type`, `raw`.

Run the full suite plus `tests/integration/test_xmpp_event_subscriptions.py` if an XMPP server is
available. Existing `NewImageEvent`/`NewSpectrumEvent` tests (`tests/test_events.py:324-397`) should pass
unchanged.

## Open items

1. Step (b): which module is the first generic-data sender (FTS?), and does it justify `BaseData` for new
   modules only (without touching camera/video/spectrograph)? Decide after (a).
2. Do subscribers ever need to tell two generic data kinds apart? If so, an optional
   `data_type: str | None = None` can be added later (additive, no version bump needed).
3. Resolved: sender-side expansion of `register_event()` is removed (step (c)), no `derived` keyword.
   Remaining question: are there plugin subclasses outside core that depend on the expansion? Check the
   sibling repos before releasing (c).
