# Sphinx docs and README should follow a shared per-group structure, enforced in CI

Companion to [[fleet-tooling-consistency]] — that doc covers lint/type-check/test/Dependabot
baseline, this one covers the fourth leg: docs (Sphinx under `docs/source/`) and, alongside it,
each repo's top-level `README.md`. Group membership below follows the categories in
`specs/steering/pyobs-project-tiers.md` (Cameras / Mounts-domes-focusers → **driver-module**,
Python User interfaces → **gui**, everything under Connected projects → **web-app**). pyobs-core
itself is exempt — it's the framework's own reference manual, already far larger than any
template here should be, and stays bespoke.

Repos: pyobs-core (this doc), and every repo listed under "Current state" below.

## If you're an agent handed this doc to fix one repo's docs

1. Find the repo in "Current state" below to get its group (driver-module / gui / web-app).
2. Copy the matching skeleton(s) from `docs/templates/` in **this** repo (pyobs-core) —
   `driver-module-conf.py` + `driver-module-index.rst` + `driver-module-readme.md`,
   `gui-index.rst` + `gui-readme.md` (conf.py is the same driver-module one), or the `web-app/`
   directory (includes `README.md`) — into the target repo's `docs/source/` and repo root
   respectively, replacing `CHANGEME` placeholders with real content. Don't invent new section
   names or drop required ones; if a section genuinely doesn't apply (e.g. no global shortcuts),
   say so in the PR description rather than silently omitting it.
3. Run `uv run sphinx-build -W -b html docs/source docs/build/html` locally and fix every warning
   before opening a PR — CI will eventually enforce this (see "Enforcement") but doesn't yet on
   most repos, so don't rely on it catching mistakes for you.
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

Applies to: pyobs-gui. (pyobs-polaris and pyobs-web-client are UI clients too, but not
Python/Sphinx — C++/Qt and TypeScript/Vue respectively. Out of scope for this doc; if they get
authored docs at all it's via their own toolchain's convention, not Sphinx.)

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
   `autoclass` refs, bad toctrees, malformed rst. Applies to all three groups.
2. **Required-files check** — a script asserting the group's required file set (above) exists
   under `docs/source/`, run with `--group driver-module|gui|web-app`. Doesn't exist yet; write it
   as `scripts/check_docs_structure.py` in pyobs-core and copy it into each repo the same way
   `ruff.yml` itself is copied, not imported as a package (the fleet has no shared-tooling
   package to import it from). Flags both missing required files and, for driver-module/gui,
   unexpected extra top-level pages (a second `.rst` file at the top level is a sign the repo
   drifted from the single-page shape without anyone deciding it should).
3. **`conf.py` template diff** — driver-module and gui only. Strip the `project =` and
   `copyright =` lines, diff the rest against pyobs-core's canonical
   `docs/templates/driver-module-conf.py`. Fails the build on any other line drifting. Not applied
   to web-app — its `conf.py`s are expected to differ.

`README.md` is **not** part of CI enforcement — it's prose, not a fixed set of files, so there's
nothing a script can usefully assert beyond "the file exists." Treat it as a documented convention
to follow by hand (and to check for in review), not something a failing build will catch.

## Current state (surveyed 2026-08-25)

**driver-module**: pyobs-aravis, pyobs-asi, pyobs-fli, pyobs-flipro, pyobs-qhyccd, pyobs-sbig,
pyobs-tis, pyobs-v4l, pyobs-alpaca, pyobs-brot, pyobs-zaber, pyobs-zwoeaf all have docs matching
the shape above (conf.py verified byte-identical modulo project/copyright on pyobs-qhyccd,
pyobs-fli, pyobs-zaber, pyobs-tis, pyobs-brot; the rest assumed conformant pending an actual CI
run once the checker exists — this was a spot-check, not an exhaustive audit). **pyobs-gemini has
no docs at all** — biggest gap in this group.

README.md across driver-module was spot-checked on pyobs-qhyccd, pyobs-fli, pyobs-zaber, pyobs-tis
and matches the convention above; not exhaustively audited beyond those four.

**gui**: pyobs-gui has the driver-module docs shape, not the gui shape — no widget catalog, no
shortcuts page — and hasn't been touched since 2024-03-21 despite #141/#142 shipping since. Its
README is worse: a one-line stub (`A GUI for pyobs....`), no install/running instructions at all.

**web-app**: pyobs-web-admin is the only repo meeting a reasonable version of the target docs
shape already; its README also already roughly matches the target (overview + Features), though
it doesn't yet link out to `docs/source/` the way the template asks. pyobs-archive has docs but
single-page and untouched since 2022-01-19 (predates its auth/admin-sync/IdP-login features
entirely); its README carries its own full configuration table, which should move to
`configuration.rst` once that exists. pyobs-weather has docs, stale since 2023-07-03.
pyobs-portal, pyobs-auth, pyobs-pipeline, pyobs-astrometry, pyobs-allsky-cloudcover,
pyobs-dashboard-utils have no Sphinx docs at all; README presence/shape on these wasn't checked.

None of the three enforcement checks exist yet anywhere in the fleet — this doc defines the
target, it doesn't claim any of it is live. No rollout plan has been written yet; when one is,
link it here the way [[fleet-tooling-consistency]] links
`core-tier-test-baseline-and-dependabot-automerge`.
