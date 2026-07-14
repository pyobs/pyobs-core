# Test coverage gaps

Measured with `coverage.py` via `pytest-cov`, running the full suite including integration and
XMPP tests against a local ejabberd (`pytest tests/ -m "integration or xmpp or (not integration
and not xmpp)" --cov=pyobs`). Overall: **60% line coverage, 18107 statements, 7220 missing.**
Running with vs. without integration/XMPP changed the total by only ~4 points (56% -> 60%) and
did not change *which* files sit at 0% at all -- the integration suite exercises more of the
comm/robotic code paths that already have some coverage, not new files entirely.

This is a survey, not a fix list -- writing tests for any of this is real, module-specific work
(understanding what each one does, what's mockable, what a meaningful assertion looks like), not
a mechanical pass like the other two audits. Categorized below so a decision on what (if
anything) to prioritize can be made per-category rather than per-file.

## 43 files at 0% coverage

### Category A -- Needs a live external service/credentials, same shape as XMPP/LCO (8 files, ~655 statements)

Telegram, Matrix, Stellarium, InfluxDB, SMB, SFTP bots/clients -- the same class of dependency
that makes the XMPP and LCO tests require `pytest.mark.integration`/`xmpp` and a live server.
Testable in principle (mock the client library), but same cost/value tradeoff as everything
already behind those markers.

- `pyobs/modules/utils/telegram.py` (274)
- `pyobs/modules/utils/matrix.py` (81)
- `pyobs/modules/utils/stellarium.py` (76)
- `pyobs/modules/utils/httpfilecache.py` (57)
- `pyobs/vfs/smbfile.py` (55)
- `pyobs/vfs/sftpfile.py` (48)
- `pyobs/utils/influxdb.py` (35)
- `pyobs/modules/utils/fluentlogger.py` (29)

### Category B -- GUI widgets, needs a display (9 files, ~368 statements)

PyQt-based camera control widgets. Not unit-testable without a display/Qt test harness; would
need `pytest-qt` or similar, a different kind of investment entirely.

- `pyobs/utils/gui/camera/datadisplaywidget.py` (96)
- `pyobs/utils/gui/camera/windowingwidget.py` (93)
- `pyobs/utils/gui/camera/exposewidget.py` (75)
- `pyobs/utils/modulegui.py` (31)
- `pyobs/utils/gui/camera/imageformatwidget.py` (19)
- `pyobs/utils/gui/camera/exposuretimewidget.py` (17)
- `pyobs/utils/gui/camera/binningwidget.py` (15)
- `pyobs/utils/gui/camera/listpickerdialog.py` (14)
- `pyobs/utils/gui/camera/__init__.py` (8)

### Category C -- CLI / app bootstrap (5 files, ~483 statements)

Argument parsing and process startup/orchestration. Usually exercised end-to-end (does the
daemon actually start and run a module) rather than unit tested; `pyobs/application.py` in
particular is the top-level object graph wiring, which is more naturally an integration-level
concern.

- `pyobs/cli/pyobsd.py` (256)
- `pyobs/application.py` (133)
- `pyobs/cli/pyobs.py` (42)
- `pyobs/cli/_cli.py` (38)
- `pyobs/cli/pyobsw.py` (14)

### Category D -- Dev/test-support tooling, not runtime logic (4 files, ~104 statements)

- `pyobs/robotic/storage/lco/mockobservationarchive.py` (84) -- a mock LCO server implementation
  for manual/interactive testing against a fake LCO API. Ironic to flag "needs tests" on
  something named Mock, but it's not itself business logic.
- `pyobs/vfs/filelists/testing.py` (12), `filelist.py` (5), `__init__.py` (3) -- also
  test-support tooling per the module name.

### Category E -- Real gaps: no external-service or GUI excuse (17 files, ~487 statements)

Core module/processor logic, same shape as plenty of code that *does* have good coverage
elsewhere (comm/vfs-mockable, no special hardware). The two standouts:

- ~~**The entire `pyobs/modules/flatfield/` subsystem**~~ -- **resolved**, see `TODO.md`.
  `flatfield.py` (112), `scheduler.py` (58), `pointing.py` (24), `__init__.py` (5) = 199
  statements, previously zero test files. Now covered by `tests/modules/flatfield/` (27 tests).
- ~~**`pyobs/modules/utils/dummymode.py`** (48) and **`pyobs/modules/camera/dummyvideo.py`**
  (35)~~ -- **resolved**, see `TODO.md`. Both are `Dummy*` simulator modules, the same family as
  `DummyRoof`/`DummyCamera`/`MockWeather`, all of which already had solid test coverage
  (`test_dummyroof.py`, `test_xmpp_dummy_camera.py`, `test_mockweather.py`). Now covered by
  `tests/modules/utils/test_dummymode.py` and `tests/modules/camera/test_dummyvideo.py`.

Rest of this category:
- `pyobs/modules/utils/kiosk.py` (87)
- `pyobs/modules/utils/autonomouswarning.py` (70)
- `pyobs/modules/utils/trigger.py` (50)
- `pyobs/comm/xmpp/xep_0009/binding.py` (137) -- low-level XMPP RPC extension binding; not hit by
  the current integration test scenarios even though other XMPP code is well covered.
- `pyobs/vfs/archivefile.py` (32)
- `pyobs/images/processors/modules/getfitsheaders.py` (28)
- `pyobs/images/processors/wcs/solarhelioprojective.py` (28)
- `pyobs/modules/utils/__init__.py` (9)
- `pyobs/modules/camera/adaptive.py` (1) -- trivially small, likely not worth a dedicated test.
- `pyobs/modules/flatfield/__init__.py`, `pyobs/images/processors/modules/__init__.py`,
  `pyobs/images/processors/wcs/__init__.py`, `pyobs/vfs/filelists/__init__.py` -- `__init__.py`
  files, usually just re-exports.

## Partially covered, worth a look (<30%, 15+ statements, 16 files)

Not "no test at all" but thin enough that large parts of the real logic are unexercised.
Several point at the same subsystems flagged above -- pointing/guiding and flatfields look like
the two areas with the broadest thin coverage, not just isolated files.

| File | Coverage | Statements |
|---|---|---|
| `pyobs/robotic/utils/skyflats/flatfielder.py` | 21.2% | 260 |
| `pyobs/modules/camera/basevideo.py` | 25.7% | 206 |
| `pyobs/mixins/fitsheader.py` | 27.7% | 177 |
| `pyobs/modules/robotic/scheduler.py` | 23.5% | 170 |
| `pyobs/modules/pointing/acquisition.py` | 22.2% | 144 |
| `pyobs/images/processors/offsets/spilled_light.py` | 24.5% | 143 |
| `pyobs/modules/pointing/_baseguiding.py` | 21.7% | 138 |
| `pyobs/robotic/storage/lco/scripts/default.py` | 19.4% | 134 |
| `pyobs/robotic/utils/archive/pyobs_archive.py` | 21.8% | 133 |
| `pyobs/utils/pipeline/night.py` | 16.8% | 119 |
| `pyobs/utils/focusseries/projection.py` | 21.7% | 115 |
| `pyobs/mixins/follow.py` | 22.0% | 100 |
| `pyobs/robotic/utils/archive/local_archive.py` | 29.2% | 89 |
| `pyobs/vfs/sshfile.py` | 21.9% | 73 |
| `pyobs/modules/pointing/autoguiding.py` | 29.2% | 72 |
| `pyobs/images/processors/annotation/text.py` | 29.7% | 37 |

## Recommendation

Categories A-D (GUI, CLI, external-service integrations, dev tooling) aren't worth chasing --
same reasoning that already put XMPP/LCO behind integration markers. Category E is where the
real, actionable gaps were; the flatfield subsystem and the two untested `Dummy*` modules (the
clearest "should just have tests and doesn't" gaps) are now resolved -- see `TODO.md`. The
pointing/guiding and flatfield-adjacent thin-coverage cluster in the table above (`flatfielder.py`
21.2%, `basevideo.py` 25.7%, `_baseguiding.py` 21.7%, `acquisition.py` 22.2%, etc.) is the natural
next candidate if this is worth continuing, since it overlaps with the same domain.
