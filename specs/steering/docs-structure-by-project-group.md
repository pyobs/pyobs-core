# Sphinx docs and README should follow a shared per-group structure, enforced in CI

Companion to [[fleet-tooling-consistency]] — that doc covers lint/type-check/test/Dependabot
baseline, this one covers the fourth leg: docs (Sphinx under `docs/source/`) and, alongside it,
each repo's top-level `README.md`. Group membership below follows the categories in
`specs/steering/pyobs-project-tiers.md` (Cameras / Mounts-domes-focusers → **driver-module**,
Python User interfaces → **gui**, everything under Connected projects → **web-app**), plus one
group not in that doc's categories: **gui-nonpython** — the non-Python GUI clients (pyobs-polaris,
pyobs-web-client). pyobs-core itself is exempt — it's the framework's own reference manual,
already far larger than any template here should be, and stays bespoke.

Repos: pyobs-core (this doc), and every repo listed under "Current state" below.

## If you're an agent handed this doc to fix one repo's docs

1. Find the repo in "Current state" below to get its group (driver-module / gui / gui-nonpython /
   web-app).
2. Copy the matching skeleton(s) from `docs/templates/` in **this** repo (pyobs-core) —
   `driver-module-conf.py` + `driver-module-index.rst` + `driver-module-readme.md`,
   `gui-index.rst` + `gui-readme.md` (conf.py is the same driver-module one),
   `gui-nonpython-conf.py` + `gui-nonpython-index.rst` + `gui-nonpython-readme.md` (conf.py is
   **not** the driver-module one here — it drops the Python-only autodoc/napoleon/viewcode
   extensions), or the `web-app/` directory (includes `README.md`) — into the target repo's
   `docs/source/` and repo root respectively, replacing `CHANGEME` placeholders with real content.
   Don't invent new section names or drop required ones; if a section genuinely doesn't apply (e.g.
   no global shortcuts), say so in the PR description rather than silently omitting it.
3. Run `uv run sphinx-build -W -b html docs/source docs/build/html` locally and fix every warning
   before opening a PR — CI will eventually enforce this (see "Enforcement") but doesn't yet on
   most repos, so don't rely on it catching mistakes for you. For a `gui-nonpython` repo with a
   Doxygen `api/` page, also run `doxygen` then
   `doxysphinx build docs/source docs/build/html Doxyfile` first — see that group's section below.
4. Update this doc's "Current state" section for the repo you touched, in the same PR.

## Why this exists

A 2026-08-25 survey (see conversation, not re-derived here) found the driver-module repos'
`docs/source/conf.py` files are already **byte-identical modulo `project =` and `copyright =`**
— a real, unwritten convention nobody was enforcing. Meanwhile `pyobs-gui`'s docs hadn't been
touched since 2024-03-21 and `pyobs-archive`'s since 2022-01-19, despite both repos shipping
substantial user-facing features since. An unwritten convention with no CI backing it just rots
silently. This doc writes it down and says how to make CI catch drift instead of a periodic
manual survey.

## The baseline

### driver-module

Applies to: pyobs-aravis, pyobs-asi, pyobs-fli, pyobs-flipro, pyobs-qhyccd, pyobs-sbig, pyobs-tis,
pyobs-v4l, pyobs-alpaca, pyobs-brot, pyobs-gemini, pyobs-zaber, pyobs-zwoeaf.

- `docs/source/conf.py` — copy `docs/templates/driver-module-conf.py` verbatim, only `project` and
  `copyright` vary.
- `docs/source/index.rst` — copy `docs/templates/driver-module-index.rst`, single page, three
  sections in order: title + one-line blurb, `Example configuration` (one fenced YAML block
  covering the module's real options, not a stub), `Available classes` (one
  `.. autoclass:: <fqcn>` block per public class, `:members:` and `:show-inheritance:`).
- `docs/source/_static/pyobs.gif` — shared logo asset, copied verbatim.
- `README.md` — copy `docs/templates/driver-module-readme.md`. Already a real unwritten
  convention across pyobs-qhyccd/pyobs-fli/pyobs-zaber/pyobs-tis: RST-underline title reading
  `<Vendor> module for *pyobs*`, one-line blurb linking pyobs.org, optional `System dependencies`
  (only if there's a non-pip driver/package to install first), then `Install *pyobs-X*` with
  clone + `uv sync`. The README and `index.rst` blurbs should say the same thing, not drift into
  two descriptions of the same module.

No `api/`, no multi-page toctree. If a driver module grows enough surface area to need more than
one page, it's no longer a plain driver-module for docs purposes — flag it for a
one-off design doc rather than stretching this template.

### gui

Applies to: pyobs-gui. (pyobs-polaris and pyobs-web-client are UI clients too, but not Python —
C++/Qt/QML and TypeScript/Vue respectively — so they follow the **gui-nonpython** group below
instead of this one.)

Same `conf.py` template and `_static/pyobs.gif` as driver-module. `index.rst` — copy
`docs/templates/gui-index.rst`, which extends the driver-module shape with two more required
sections after "Available classes":

4. `Widgets` — one subsection per top-level widget the GUI ships, at minimum a screenshot and
   what module interface(s) it drives.
5. `Keyboard shortcuts` (if any are bound globally, not per-widget — delete the section if none).

pyobs-gui's docs today are the plain driver-module shape (title/blurb/example-config/autoclass
only) with no widget catalog at all — that's the gap, not a template mismatch to fix by relaxing
the template.

`README.md` — copy `docs/templates/gui-readme.md`: same driver-module shape (title, blurb,
optional system deps, install) plus a `Running` section (launch command + minimal fleet-connect
config), since a GUI is something you run, not just a class you configure into another module's
comm. pyobs-gui's current README is a one-line stub (`A GUI for pyobs....`) — biggest README gap
in the fleet.

### gui-nonpython

Applies to: pyobs-polaris (C++/Qt/QML), pyobs-web-client (TypeScript/Vue).

Both repos can use the same Sphinx + `sphinx_rtd_theme` + Read the Docs pipeline as every other
group — genuine visual parity with the rest of the fleet, not an approximation via a different
tool's theme. What differs from `gui` is only: no Python to autodoc, an `Available classes`
section that only applies where a Doxygen bridge exists, and a `Views` catalog instead of
`Widgets` (both repos already call their top-level screens "views" in their own source —
`qml/views/*.qml`, `src/views/*.vue` — this is their own vocabulary, not invented for the docs).

- `docs/source/conf.py` — copy `docs/templates/gui-nonpython-conf.py`. **Not** the driver-module
  conf.py — it drops `sphinx.ext.autodoc`/`napoleon`/`viewcode` (nothing to introspect), keeping
  `sphinx_rtd_theme`, the logo, and general config identical.
- `docs/source/index.rst` — copy `docs/templates/gui-nonpython-index.rst`: title/blurb →
  `Example configuration` → `Available classes` → `Views` → `Keyboard shortcuts`.
  - `Available classes`: **Doxygen-backed repos only.** For pyobs-polaris, generate it via
    [doxysphinx](https://github.com/boschglobal/doxysphinx) (Doxygen → HTML → doxysphinx converts
    to `.rst` → Sphinx renders it with the same theme as everything else): Doxyfile needs
    `OUTPUT_DIRECTORY` inside `docs/source/` (e.g. `docs/source/api/`), `GENERATE_TREEVIEW = NO`,
    `DISABLE_INDEX = NO`, `CREATE_SUBDIRS = NO`, `INPUT = src` (Doxygen doesn't parse QML — the
    `qml/` views are documented in the `Views` section instead, not generated). Build order:
    `doxygen` then `doxysphinx build docs/source docs/build/html Doxyfile`, then `sphinx-build`.
    For pyobs-web-client there's no such bridge and nothing to introspect (it's a thin XMPP
    client, not a library) — delete this section entirely rather than leaving a stub.
  - `Views`: one subsection per top-level view the client ships — screenshot + which module
    interface(s) it drives. Same shape as `gui`'s `Widgets` section.
  - `Keyboard shortcuts`: same optional/delete-if-none rule as `gui`.
- `docs/source/_static/pyobs.gif` — same shared logo asset as the other groups.
- `README.md` — copy `docs/templates/gui-nonpython-readme.md`: same `gui` shape (title, blurb,
  optional system deps, install/build in the repo's native toolchain, `Running`), plus a
  `Documentation` pointer to `docs.pyobs.org/projects/pyobs-<repo>/`.
- `.readthedocs.yml`: same `sphinx.configuration: docs/source/conf.py` /
  `python.install` (`sphinx`, `sphinx_rtd_theme`) pattern as the Python repos — pyobs-web-client's
  needs nothing else (no Node/JS tooling for docs at all, since the pages are hand-written, not
  generated from the app's own TS source). pyobs-polaris additionally needs
  `build.apt_packages: [doxygen]`, `python.install` adding `doxysphinx`, and a
  `build.jobs.pre_build` running `doxygen` then `doxysphinx build ...` before Sphinx builds.

Neither repo has any of this yet as of 2026-08-25 — see "Current state" below.

### web-app

Applies to: pyobs-portal, pyobs-web-admin, pyobs-archive, pyobs-pipeline, pyobs-astrometry,
pyobs-weather, pyobs-allsky-cloudcover, pyobs-dashboard-utils, pyobs-auth.

This group has no existing convention to codify — pyobs-web-admin is the only repo with a real
multi-page structure today (`architecture.rst`, `installation.rst`, `configuration.rst`,
`development.rst`, `api/`, plus feature subsections); pyobs-archive is a single stale page; the
rest have no docs at all. Required pages — copy the `docs/templates/web-app/` directory, using
pyobs-web-admin's shape as the reference:

- `index.rst` — overview + toctree linking the pages below.
- `installation.rst` — how to deploy/run it (Docker, env vars, migrations if Django).
- `configuration.rst` — settings this app reads, with defaults.
- `architecture.rst` — how it fits into the rest of the fleet (what it talks to, over what
  protocol).
- `development.rst` — running it locally, running its tests.
- `api/` — one page per REST/API surface, if the app exposes one (Django+DRF apps do; Flask-only
  ones like pyobs-astrometry may not). No skeleton provided — copy pyobs-web-admin's `api/`
  structure if/when a repo needs it.

`conf.py` is **not** forced to match the driver-module template verbatim here — `html_theme` and
extensions may legitimately differ for a Django app's docs — but still needs `project`,
`copyright`, `author` set and a working `sphinx-build`.

`README.md` — copy `docs/templates/web-app/README.md`: short overview (matching `index.rst`'s
opening paragraph) + a pointer into the real docs for installation/configuration, plus a brief
local-dev quickstart. Don't duplicate the configuration table or install steps in both places —
pyobs-archive's current README already has a full settings table that `docs/source/` doesn't;
once `configuration.rst` exists, the table's home is there and the README should link to it
instead of carrying its own copy that can drift out of sync.

## Enforcement

Three checks, in a `.github/workflows/docs.yml` copy-pasted into each repo (same pattern as
`ruff.yml`/`pyrefly.yml` in [[fleet-tooling-consistency]] — no shared/reusable workflow repo
exists for the fleet today, so this isn't centralized either):

1. **`sphinx-build -W -b html docs/source docs/build/html`** — warnings-as-errors. Catches broken
   `autoclass` refs, bad toctrees, malformed rst. Applies to all four groups (for pyobs-polaris,
   run the Doxygen/doxysphinx pre-build step first, same as locally).
2. **Required-files check** — a script asserting the group's required file set (above) exists
   under `docs/source/`, run with `--group driver-module|gui|gui-nonpython|web-app`. Doesn't exist
   yet; write it as `scripts/check_docs_structure.py` in pyobs-core and copy it into each repo the
   same way `ruff.yml` itself is copied, not imported as a package (the fleet has no
   shared-tooling package to import it from). Flags both missing required files and, for
   driver-module/gui/gui-nonpython, unexpected extra top-level pages (a second `.rst` file at the
   top level is a sign the repo drifted from the single-page shape without anyone deciding it
   should).
3. **`conf.py` template diff** — driver-module, gui, and gui-nonpython. Strip the `project =` and
   `copyright =` lines, diff the rest against pyobs-core's canonical `docs/templates/*-conf.py` for
   that repo's group (`driver-module-conf.py` for driver-module/gui, `gui-nonpython-conf.py` for
   gui-nonpython). Fails the build on any other line drifting. Not applied to web-app — its
   `conf.py`s are expected to differ.

`README.md` is **not** part of CI enforcement — it's prose, not a fixed set of files, so there's
nothing a script can usefully assert beyond "the file exists." Treat it as a documented convention
to follow by hand (and to check for in review), not something a failing build will catch.

## Current state (surveyed 2026-08-25)

**driver-module**: pyobs-aravis, pyobs-asi, pyobs-fli, pyobs-flipro, pyobs-qhyccd, pyobs-sbig,
pyobs-tis, pyobs-v4l, pyobs-alpaca, pyobs-brot, pyobs-zaber, pyobs-zwoeaf all have docs matching
the shape above (conf.py verified byte-identical modulo project/copyright on pyobs-qhyccd,
pyobs-fli, pyobs-zaber, pyobs-tis, pyobs-brot; the rest assumed conformant pending an actual CI
run once the checker exists — this was a spot-check, not an exhaustive audit). **pyobs-gemini**
had no docs/README at all — fixed 2026-08-25 (develop @ `a0d2f50`): full driver-module docs
scaffolding (conf.py/index.rst/Makefile/requirements.txt) plus README added from scratch, content
grounded in `GeminiFocuserRotator`'s actual constructor and driven by `docs/templates/`.

README.md across driver-module was spot-checked on pyobs-qhyccd, pyobs-fli, pyobs-zaber, pyobs-tis
and matches the convention above; not exhaustively audited beyond those four.

**gui**: pyobs-gui — fixed 2026-08-25 (develop @ `4fd6180`). Added the Widgets and Keyboard
shortcuts sections (all 14 `DEFAULT_CONFIG` pages, shortcuts table grounded in
`mainwindow.py`'s `_FIXED_SHORTCUTS`/`_ASSIGNABLE_SLOTS`; no screenshots — written from source,
not a running GUI, so add those as a follow-up) and rewrote the README (was a one-line stub) with
real install/running instructions.

**gui-nonpython**: neither repo had any docs/source/ or `.readthedocs.yml` before 2026-08-25.
**pyobs-web-client** — fixed 2026-08-25: `docs/source/` (hand-written `index.rst`, no `Available
classes` section — nothing to introspect), `.readthedocs.yml`, README pointer; `specs/` cleanup
(two new design docs, first ADR) and `DEVELOPMENT.md` trim done in the same pass — see that repo's
`specs/index.md`. **pyobs-polaris** — docs site (`Doxyfile`, `docs/source/`, `.readthedocs.yml`
with the Doxygen/doxysphinx pre-build job) done 2026-08-25; the much larger `DEVELOPMENT.md` →
`specs/` split (its `DEVELOPMENT.md` was 3187 lines/239K with no `specs/` at all beforehand) was
still in progress as of this writing — check that repo's `specs/index.md` for current status
before assuming it's finished. Neither repo's Doxygen/doxysphinx pipeline has been verified
against a real `doxygen`/`doxysphinx` install (not available in the environment this was written
in) — verify locally before relying on the RTD build succeeding.

**web-app**: **all nine repos in this group now have docs matching the shape above**, fixed
2026-08-25. pyobs-web-admin already met a reasonable version of the target shape beforehand.

- **pyobs-archive** (develop @ `7aad1dd`): split into
  index/installation/configuration/architecture/api/development, correcting the old single
  page's stale Docker Compose example and REST API errors (wrong auth header, a nonexistent
  `/api-token-auth/` endpoint) rather than just relocating them; README now points into `docs/`
  instead of carrying its own configuration table.
- **pyobs-weather** (develop @ `fd146c5`): same split, correcting a Redis+Celery+local_settings.py
  deployment description the app no longer uses and a stale REST API shape (`/api/history/`'s
  response shape had changed, several endpoints were undocumented). Also unpinned the dev-group
  Sphinx version (`Sphinx>=4.4,<5` couldn't even build — a transitive dependency needed Sphinx
  ≥5 — unrelated pre-existing breakage, fixed in the same commit) to match the rest of the fleet.
- **pyobs-portal** (develop @ `47f89dd`): had no docs at all; added
  index/installation/configuration/architecture/api/frontend/development (a `frontend.rst` beyond
  the base template, for the built-in web UI) reorganized from the repo's own already-current
  README, filling a few real gaps (`WEBADMIN_URL` wasn't documented anywhere; several `/api/`
  endpoints were missing from the README's table).
- **pyobs-auth** (develop @ `9af8e06`): had no docs at all; adapted the web-app shape for a
  library rather than a deployed service — `installation.rst` covers adding it to a Django
  project (not Docker Compose), `api.rst` is an autoclass Python API reference (not REST, since
  this repo has none).
- **pyobs-pipeline** (develop @ `91642c7`): had no docs at all; added
  index/installation/configuration/architecture/development (no `api.rst` — a server-rendered app
  with one JSON polling endpoint, not a REST-backed service). Preserved the README's hard-won
  `.env` `$`-escaping-under-Docker-Compose and reverse-proxy-CSRF gotchas verbatim; added the
  Site/Pipeline/PipelineStep/SitePipeline/ReductionPeriod domain model to `architecture.rst`,
  grounded in `reduction/models.py`. Added a `dependency-groups.dev` (none existed) with Sphinx.
- **pyobs-astrometry** (`master` renamed to `main` in the same session, then `develop` branched
  off it — see below; commit `f031320`): had no docs at all; one page, not a multi-page split —
  a single stateless Flask endpoint with no Python dependency management of its own (apt packages
  baked into the `Dockerfile`) doesn't warrant one.
- **pyobs-allsky-cloudcover** (`develop` branch created off `main` in the same session — see
  below; commit `c2e8d55`): had no docs at all; one page (driver-module shape, not web-app) since
  it's a pyobs `Module` (configured via `class:` in YAML, like the driver-module fleet) with a
  small bolted-on web query API, not a deployed multi-page service. No autoclass reference —
  this repo is Python+Rust (maturin/PyO3, Poetry, not uv) and building the Rust extension just to
  import it for docs wasn't worth the cost; classes are described in prose instead.
- **pyobs-dashboard-utils** (develop @ `f8f52b5`): had no docs at all; driver-module-shaped single
  page (bundles five independent `Module` classes, not one service) — ported the README's already
  solid per-module config docs into RST with autoclass for all five, and wrote a real LDP Plotter
  section from source (the README's was one line).

Two of these repos didn't have a `develop` branch before this session: **pyobs-astrometry** only
had `master` (renamed to `main` via the GitHub API, then `develop` branched off the new `main`)
and **pyobs-allsky-cloudcover** only had `main` (branch created off it). Both repos' docs commits
above landed on the new `develop`.

Also unpinned pyobs-gui's `Sphinx>=8.2.3,<9`/`sphinx-rtd-theme>=3.0.2,<4` caps (develop @
`d999ad9`) to match pyobs-core's floor-only convention — it was one version behind the rest of
the fleet for no reason found. The whole fleet now resolves to the same Sphinx major version
(9.x) wherever it isn't hard-pinned for a real reason.

None of the three enforcement checks exist yet anywhere in the fleet — this doc defines the
target, it doesn't claim any of it is live. No rollout plan has been written yet; when one is,
link it here the way [[fleet-tooling-consistency]] links
`core-tier-test-baseline-and-dependabot-automerge`.
