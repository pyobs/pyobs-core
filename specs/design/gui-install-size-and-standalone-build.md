# pyobs-gui install size and standalone build

Status: dependency slimming implemented and released (`pyobs-core` 2.14.0, `pyobs-gui` 2.6.1);
standalone binary builds and runs but is experimental; astropy unit formats in the binary open.
Repos: pyobs-core, pyobs-gui, qfitswidget

Date: 2026-10-04

## Problem

A `pyside6-deploy` (Nuitka) binary of pyobs-gui came out at several GB, and a plain install was
about 1.5 GB. `pyobs-core[gui]` was originally split out for pyobs-gui, but the base install of
`pyobs-core` still carried everything the module hosts need.

Follow-up to `gui-standalone-binary.md` (rejected 2026-09-14 because the build came out several GB).
With the slim dependencies the binary is 764 MB, so that reason no longer holds as stated. The status
of that doc is left as it was.

## What changed

**pyobs-gui (2.6.0, 2.6.1)**

- `sunpy[all]` became `sunpy`. The GUI only imports two coordinate frames from it, the extra pulled in
  dask, scikit-image, opencv-python, zeep and more.
- `pyside6` became `pyside6-essentials`. The meta-package installs the addons wheel (WebEngine and
  others), the GUI only needs Core, Gui, Widgets and Designer.
- `pandas` and `astroquery` are now declared. Both were imported directly
  (`temperaturesplotwidget.py`, `telescopewidget.py`) but only came in through `pyobs-core`.
- `BaseWidget.hideEvent` returns early when no event loop is running. At shutdown Qt hides widgets
  after the loop has stopped, `create_task` raised `RuntimeError` and left an unawaited coroutine.
- Requires `pyobs-core>=2.14.0`.

**pyobs-core 2.14.0**

The base dependencies now only hold what pyobs-gui needs. These moved to the `full` extra:
`scipy`, `pandas`, `astroquery`, `dbus-next`, `paramiko`, `influxdb-client`, `dacite`,
`astropydantic`, `tenacity`, `psutil`, `logging-journald`.

This breaks a bare `pip install pyobs-core` for anything that uses image processors, `robotic`,
focus series and similar. Hosts that run modules install `pyobs-core[full]`, so that is accepted.
An earlier attempt to move only `scipy` and `pandas` was rejected: 16 packages stopped importing
and the saving was small, because the GUI needs pandas itself. Moving everything the GUI does not
import is what makes the split worthwhile.

## Measured sizes

Installed size of `site-packages` without the dev group, from `uv sync --no-dev` or a fresh venv.

| State | Size | Packages |
|---|---|---|
| before | 1506 MB | 133 |
| sunpy and pyside6 trimmed, pandas declared | 865 MB | n/a |
| plus `pyobs-core` 2.14.0 (published) | 716 MB | 79 |

The dev venv stays larger because `pyside6-stubs` pulls in the full `pyside6`.

Largest remaining parts: PySide6 232 MB (essentials), OpenCV about 162 MB (qfitswidget), pandas
48 MB, astropy 42 MB, numpy about 60 MB, matplotlib 30 MB.

## OpenCV in qfitswidget

`qfitswidget` uses `cv2` in one place, `_debayer` (`cv2.cvtColor(..., COLOR_BayerGB2BGR)`). A numpy
bilinear demosaic with OpenCV's integer rounding matched it bit for bit everywhere except the
outermost 1 pixel ring (edge handling differs, at most about 1.3 percent of the range on a smooth
gradient). It was slower, 317 ms against 9 ms for a 6 MP image. Open question: OpenCV's `BayerGB`
constant corresponds to red at row 0, column 1 (GRBG in the usual naming), while the header value
handled is `GBRG`, so channels may already be swapped on real frames. Needs a real frame to check.
Tracked in qfitswidget issue #39.

## Standalone binary

`pysidedeploy.spec` (Nuitka 4.0 via `pyside6-deploy`) builds a working binary from the slim
dependencies: 764 MB, 20 minutes on 16 cores with gcc, login works.

Changes needed to the recipe, now in the repo:

- Removed the `asdf` and `scipy` entries (no longer installed) and the pinned `--clang`.
- Added `--include-package=pyobs_gui`.
- The build must run from a non-editable install of pyobs-gui. With an editable install the
  distribution's RECORD only lists a `.pth` file and Nuitka aborts with "including metadata for
  distribution 'pyobs-gui' without including related package". The README has the commands.

Size of the binary is about the same as the venv, so it saves no space, only the Python install.

### Known issue: astropy unit parsers

The existing `_nuitka_astropy_patch.py` only covers the generic unit format. In the binary, the
cds parser (and, by the same mechanism, ogip, vounit and the angle parser) still fails with
"Unable to build parser", logged as `UnitsWarning` plus `ERROR: No token list is defined`. The app
keeps running. Cause is the open astropy and Nuitka frame-introspection problem
(astropy #15069, Nuitka #2313).

A spike tried to keep `astropy.units.format` as plain source inside the binary (variants with and
without `astropy.extern.ply` and `astropy.utils.parsing` as source, `.py` files shipped as data,
`--no-deployment-flag=excluded-module-usage`). It failed: the binary raises
`ModuleNotFoundError: No module named 'astropy.units.format'`, Nuitka does not import plain source
from inside a package it compiled. A plain compile reproduces the original crash.

Remaining options, none implemented:

1. Vendor the cds, ogip and vounit grammars like generic (about 800 lines tied to astropy 7.2.2,
   each check needs a 20 minute rebuild).
2. A runtime fallback that loads astropy's shipped source by path and returns the interpreted
   frame's namespace to PLY. Covers all formats in one mechanism, untested.
3. Leave it. Nothing was found that breaks, only log noise.

Decision: option 3 until a feature actually fails.

## Open items

- qfitswidget #39 (drop OpenCV, about 68 MB in the binary, about 162 MB in a venv).
- Astropy unit formats in the binary, only if something fails (see above). Where the cds parses
  come from (FITS header units, telescope widget) was not traced.
- The packaging plan `2026-07-27-gui-widget-plugins-and-packaging.md` is still marked abandoned
  (2026-09-14) in the pyobs-gui `specs/index.md`, although the build recipe works again.
- Install docs: `uv tool install pyobs-gui` is the recommended path for users, the README still only
  shows `uv sync` from a clone.
