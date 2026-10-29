# Plan: generic `NewDataEvent`

Status: proposed. Decisions of 2026-10-29 are in "Decisions"; remaining open items at the end.
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

## Verified facts

- `Comm.register_event()` (`pyobs/comm/comm.py:424`) expands to `_get_derived_events()` (`:413`), i.e.
  all classes in `registered_events()` that are `issubclass` of the given one. Handlers are stored per
  concrete class; duplicate handlers are skipped.
- Dispatch is exact class match: `event.__class__ in self._event_handlers` (`comm.py:693`). Together with
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
    use `type(event) is NewDataEvent` to select only generic data.
- `pyobs/events/newimage.py`: `class NewImageEvent(NewDataEvent)`; keep
  `__init__(filename, image_type=None, raw=None, **kwargs)` unchanged, call
  `NewDataEvent.__init__(self, filename)` and extend `self.data` with `image_type`, `raw`. Drop the
  inherited `filename` property. Payload is byte-identical to today. `from_dict` untouched here (a4).
- `pyobs/events/newspectrum.py`: same pattern; fix docstrings ("new image").
- The module-level TypedDicts called `DataType` in `newimage.py`/`newspectrum.py` need no rename now
  (no enum).
- `pyobs/events/__init__.py`: import `NewDataEvent` and add to `__all__`.
- `docs/source/api/events.rst`: add a `NewDataEvent` section before `NewImageEvent`.
- Optional: `docs/source/api/comm.rst:66` mention subscribing to `NewDataEvent` for "any data".
- `CHANGELOG.md` `[Unreleased]` Added entry.

### a3. Fix `from_dict` to use `cls` (separate commit)

`NewImageEvent.from_dict` (`newimage.py:53`) and `NewSpectrumEvent.from_dict` (`newspectrum.py:34`) build
the hard-coded class. Change to `cls(...)` so plugin subclasses deserialize as themselves. Add a test with
a plugin subclass. `CHANGELOG.md` Fixed entry.

### a4. (Optional, outside core) Use it in subscribers

Nothing in core needs it now. Candidate outside core: `pyobs-gui/pyobs_gui/datadisplaywidget.py:86-87,200`
could register one `NewDataEvent` handler instead of two and use `isinstance(event, NewDataEvent)`. That is
a pyobs-gui change and needs a pyobs-core release first. Not part of this plan.

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
            await self.comm.register_event(self._data_event)

    async def _broadcast_data(self, event: NewDataEvent, broadcast: bool) -> None:
        if broadcast and self._comm:
            await self.comm.send_event(event)
```

Even this mostly moves 3 lines and adds a class. A free function or a small mixin would give the same
without touching the MRO of `Module`.

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
- A `NewDataEvent` handler also receives image/spectrum events. Handlers meant for generic data only must
  check `type(event) is NewDataEvent`.
- Subscribing to `NewDataEvent` only covers subclasses imported before `register_event()` (documented
  limitation of `_get_derived_events`). Plugin subclasses imported later are missed. Same as today for
  `NewImageEvent`.

## Tests

Add:
- `tests/test_events.py`: `NewDataEvent` round trip via `to_json`/`EventFactory.from_dict`; invalid
  `filename` raises `ValueError`; `isinstance(NewImageEvent(...), NewDataEvent)` and same for spectrum;
  `NewImageEvent(...).data` unchanged from today; registry contains `NewDataEvent`.
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
