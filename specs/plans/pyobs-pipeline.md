# Plan: pyobs-pipeline-web

Status: draft

Issue: #741

Repos: new repo `pyobs-pipeline-web`

## Problem

The existing pipeline runs data reductions unattended via Celery Beat with no way to monitor what is running, view logs, retrigger failed nights, or configure pipeline steps without SSH access. The config is YAML on disk, loaded via `pyobs.object.create_object`.

The goal is a dedicated web project that provides full pipeline management through a browser interface: monitoring status, viewing logs, retriggering reduction periods, and configuring the pipeline with a guided builder.

**Standalone Django project**, same layout as pyobs-web-admin:
- Bootstrap 5 dark theme, sidebar navigation, card-based dashboard
- Template-based frontend, no SPA
- Single-user cookie auth (`ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH`)

**Celery + Redis** for async task execution and scheduling — Redis rather than RabbitMQ, since it's the broker already in use and running; no new broker dependency to stand up. Celery Beat triggers per site on a configurable schedule — sunrise, sunset, or a fixed time of day, each with an optional delay — not just sunrise as the current pipeline hardcodes.

**SQLite + Docker Compose** deployment — no Postgres. Four services (gunicorn, Celery worker, Celery beat, Redis) defined in one `docker-compose.yml`, all on one host. Compose handles startup ordering (`depends_on`) and unified logs across the four services — simpler than hand-writing that many systemd units, and matches the Dockerfile-based pattern the current pipeline already uses.

**Logs in database** — one log per pipeline run stored in `ReductionPeriod.logs`, a `Text` field on the `ReductionPeriod` model. Web app reads from DB. No shared filesystem needed.

## Django models

| Model | Fields | Purpose |
|---|---|---|
| `Site` | name, lat, lon, timezone, enabled, trigger_type, delay_hours, trigger_time | Observatory location, schedule config |
| `Pipeline` | name, description, period_config (JSON) | Named pipeline definition, reusable across sites |
| `PipelineStep` | pipeline (FK), order, step_class, config (JSON) | Ordered steps in a pipeline |
| `SitePipeline` | site (FK), pipeline (FK), input_path, output_path | Assigns pipeline to site, configures I/O |
| `ReductionPeriod` | site (FK), date, status, logs (TextField), started_at, finished_at, task_id | One row per reduction run |

Sites are extensible — add/remove from the web interface. Named pipelines are reusable — create a pipeline config, assign it to one or more sites.

## Pipeline builder

The builder auto-generates web forms by introspecting each processor's `__init__` signature at runtime. No static TEMPLATES registry needed — pyobs-core is importable, so we can inspect the class directly.

A helper function (`get_step_fields(step_class)`) uses `inspect.signature()` on the processor class to extract parameters, types, defaults, and annotations. It maps Python types to form field types:
- `bool` → checkbox
- `int` → number input
- `float` → number input
- `str` → text input
- `dict` or `list` → JSON editor textarea

Fields without type hints fall back to JSON editor. The builder renders a form per step, lets the operator reorder, add, remove, and configure steps.

## Scheduling

Per-site `trigger_type` selects what Celery Beat waits for: `celery.schedules.solar('sunrise', ...)` or `solar('sunset', ...)` (same `solar` schedule the current pipeline uses, generalized to either event) plus `delay_hours`, or a plain daily fixed local time (`trigger_time`) with no solar event involved at all. Sites have an `enabled` toggle in the web interface to skip automatic scheduling for a site entirely.

The trigger event **always** creates a `ReductionPeriod` row (status `PENDING`) — for every site, whether `enabled` or not. `enabled` only gates what happens next: if the site is enabled, the row is immediately advanced to `QUEUED` and the Celery task dispatched; if not, it's left `PENDING` for an operator to dispatch manually. Rows are never created by an operator picking a date in the UI — they only ever come from the trigger event (see "Manual control" below).

`Site.enabled = False` is a valid standing configuration, not just a temporary pause — a site can run manual-only indefinitely, with no automatic dispatch ever firing. Its `ReductionPeriod` rows still get created automatically every trigger event, just left `PENDING` until an operator starts them.

## Celery task

```
reduce_period(site_id, period_id):
  1. Look up site + assigned pipeline from DB
  2. Build nested config dict:
       {class: "pyobs.utils.pipeline.Reduction",   # see note below — pending rename + output param, currently still Night/store_local
        **pipeline.period_config,        # min_flats, filenames_calib, create_calibs, calib_science
        archive: <input archive config, or local-dir config>,
        output: <output archive config, or local dir string, per output_type>,
        pipeline: {class: "pyobs.utils.pipeline.Pipeline",
                   steps: [<PipelineStep entries, ordered, each {class: step_class, **config}>]}}
  3. Load via pyobs.object.create_object
  4. Run. Read raw frames + calib frames from the input source (local dir or PyobsArchive per SitePipeline).
     Write reduced frames to the output destination (local dir or PyobsArchive per SitePipeline) — independently configurable, either can be either.
  5. Update ReductionPeriod: status = "COMPLETED"/"FAILED", logs (append to TextField), finished_at
```

**Note:** `pyobs.utils.pipeline.Night` (pyobs-core) is being renamed to `pyobs.utils.pipeline.Reduction`, and gains a unified `output` constructor parameter (replacing `store_local`, type-discriminated between a local path string and an archive config) — same "night doesn't fit solar telescopes" reasoning as this project's own `ReductionPeriod` rename, plus the I/O gap that blocks this plan's `SitePipeline.input_type`/`output_type` model. Tracked in `specs/plans/night-archive-io-hardening.md` — a prerequisite for this project's Step 5, not just a naming nit.

On failure, the task catches the exception, writes it to the log, and updates the ReductionPeriod status to `"FAILED"` for easy retriggering. On success, status becomes `"COMPLETED"`.

**Manual control: start / stop / reset / restart.** Every action is available from the UI regardless of `Site.enabled` — a manual-only site (never auto-dispatched) is fully operable through these four actions alone. None of them let an operator invent a new site+date pair; they only ever act on a `ReductionPeriod` row that the trigger event already created (see "Scheduling" above) — an operator picking an arbitrary date is not a supported flow.

- **Start** — on an existing row whose status is `PENDING`, `FAILED`, or `CANCELLED`. Advances it to `QUEUED` and calls `reduce_period.delay(site_id, period_id)`. This is how a manual-only site's daily row actually runs, and how a failed/cancelled row gets retried in place.
- **Stop** — only valid on a `RUNNING` period. Calls `AsyncResult(task_id).revoke(terminate=True)` and sets status to `CANCELLED` with a log line noting manual cancellation. Requires the worker pool to support termination (`--pool=prefork`, not `solo`).
- **Reset** — for a period stuck in `QUEUED`/`RUNNING` whose `task_id` is no longer live (e.g. the worker crashed or was restarted without revoking cleanly). Sets status to `CANCELLED` without attempting a revoke — a manual escape hatch for orphaned state, not a normal-path action.
- **Restart** — Stop (if `RUNNING`) or Reset (if stuck) the current row, then Start a fresh row for the same site+date. The new row's site+date is copied from the row being restarted, not chosen by the operator, so this doesn't reopen the "no user-created periods" rule — it's the row-creation step of Start, replayed with a known date. Each restart is a new `ReductionPeriod`; the old row is kept for its log history.

Two rows for the same site+date can't both be dispatchable at once — Start is disabled in the UI while a `QUEUED`/`RUNNING` row for that site+date already exists, to avoid two workers processing the same date concurrently.

## Pages

| Route | Description |
|---|---|
| `/` | Dashboard: site status cards, last period, next scheduled run, recent periods table |
| `/sites/` | Site list, add/edit/delete |
| `/sites/<name>/` | Site detail: pipeline assignment, recent periods, start/restart buttons |
| `/pipelines/` | Pipeline list, create new |
| `/pipelines/<name>/` | Pipeline builder: step list with reorder, form per step, add/remove steps |
| `/periods/` | All reduction periods across sites, filter by site/status, start/restart failed/cancelled |
| `/periods/<id>/` | ReductionPeriod detail: status, timing, log viewer (auto-refreshes from DB while running), start/stop/reset/restart controls |

## Log viewing

Worker appends log lines to the `logs` TextField on the `ReductionPeriod` row during execution. Web app reads from DB. ReductionPeriod detail page shows the full log with auto-refresh (poll every 2s) while the reduction is running. When completed, log is static text.

## Reduction period turnover

Two distinct things are involved, which the current pipeline keeps separate and this plan keeps separate too:

- **Trigger time** — when Beat dispatches the reduction. Governed by `Site.trigger_type`: next sunrise or sunset (`astroplan`) + `delay_hours`, or the next daily occurrence of `trigger_time` with no solar event at all. The current pipeline only supports the sunrise+delay case (its `schedule` task does a fixed 3h wait after a `solar('sunrise', ...)` event); this plan generalizes it to sunset and fixed-time too, since not every site's natural boundary is a sunrise.
- **Period boundary** — which calendar date a given frame belongs to. Derived at trigger time as the local calendar date of the most recent occurrence of the *opposite* reference point before "now": for a `sunrise` trigger, the most recent sunset (`Observer.sun_set_time(..., which='previous')`, matching the current pipeline — a frame taken at 1am is attributed to the previous evening's date); for a `sunset` trigger, the most recent sunrise; for `fixed_time`, the most recent prior occurrence of that same local time.

`get_next_turnover` computes the *trigger* time per `Site.trigger_type` for the Beat scheduler to act on; a separate helper derives the period *label* at trigger time as described above.

## Steps to implement

1. **Scaffold Django project** — Django + gunicorn, Bootstrap 5 template layout, single-user auth
2. **Django models** — `Site`, `Pipeline`, `PipelineStep`, `SitePipeline`, `ReductionPeriod`
3. **Site management views** — create/edit/delete sites, enable/disable scheduling
4. **Pipeline builder views** — template registry, form rendering per step type, reorder, add, remove, save
5. **Celery + Redis integration** — broker config, `reduce_period` task, Beat trigger schedule (sunrise/sunset/fixed-time)
6. **ReductionPeriod management views** — list, detail, start/stop/reset/restart
7. **Log viewer** — read logs from DB with auto-refresh
8. **Dashboard** — site status cards, last period results, next scheduled run, recent periods table
9. **Dockerfile + Compose + deploy docs** — gunicorn, Celery worker, Celery beat, Redis as Compose services
10. **Tests** — model tests, view tests, Celery task tests

### Step 1: Scaffold Django project

Create the new repo with:
- Django project structure (`pyobs_pipeline_web/` package with `settings.py`, `urls.py`, etc.)
- `pyproject.toml` managed with `uv` (`uv init`, `uv add django gunicorn celery redis`), `uv.lock` committed — matching the uv workflow used elsewhere in the pyobs ecosystem. Redis itself is a separate system service (distro package), not a Python dependency.
- `templates/base.html` — sidebar layout, Bootstrap 5 dark theme, matching pyobs-web-admin pattern
- `templates/` — login page, base template with sidebar
- Settings: `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `DEBUG`, `ALLOWED_HOSTS`
- Database: SQLite (`db.sqlite3`), with WAL mode + a busy timeout set in `DATABASES["default"]["OPTIONS"]` (`{"init_command": "PRAGMA journal_mode=WAL;", "timeout": 20}`) — needed because gunicorn, the Celery worker, and Celery beat all open the same file concurrently. Feasible at this scale (a handful of sites, one run per site per day); revisit if run frequency or worker count grows significantly.

### Step 2: Django models

```python
class Site(models.Model):
    name = models.CharField(unique=True)
    lat = models.FloatField()
    lon = models.FloatField()
    timezone = models.CharField()
    enabled = models.BooleanField(default=True)
    trigger_type = models.CharField(choices=[("sunrise", "Sunrise"), ("sunset", "Sunset"), ("fixed_time", "Fixed local time")], default="sunrise")
    delay_hours = models.FloatField(default=3.0, help_text="Offset after the trigger event; ignored for fixed_time")
    trigger_time = models.TimeField(null=True, blank=True, help_text="Local time of day to trigger; used only when trigger_type is fixed_time")

class Pipeline(models.Model):
    name = models.CharField(unique=True)
    description = models.TextField(blank=True)
    period_config = models.JSONField(default=dict)  # kwargs for the top-level reduction object: min_flats, filenames_calib, create_calibs, calib_science

class PipelineStep(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    order = models.IntegerField()
    step_class = models.CharField()  # dotted path, e.g. "pyobs.images.processors.misc.Calibration"
    config = models.JSONField(default=dict)

class SitePipeline(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    input_type = models.CharField(choices=[("local", "Local directory"), ("archive", "PyobsArchive")], default="local")
    input_config = models.JSONField(default=dict)  # e.g. {"path": "/data/raw"} or {"class": "pyobs.utils.archive.PyobsArchive", "url": "...", "token": "..."}
    output_type = models.CharField(choices=[("local", "Local directory"), ("archive", "PyobsArchive")], default="local")
    output_config = models.JSONField(default=dict)  # e.g. {"path": "/data/reduced"} or {"class": "pyobs.utils.archive.PyobsArchive", "url": "...", "token": "..."}

class ReductionPeriod(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(choices=[("PENDING", ...), ("QUEUED", ...), ("RUNNING", ...), ("COMPLETED", ...), ("FAILED", ...), ("CANCELLED", ...)])  # PENDING: row exists, not yet dispatched (created by trigger event, awaiting auto- or manual dispatch). CANCELLED: manually stopped or reset
    logs = models.TextField(blank=True)  # one per pipeline run
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    task_id = models.CharField(blank=True)  # Celery task ID
```

### Step 3: Site management views

- `sites/` — list all sites, add/edit/delete
- `sites/<name>/` — site detail:
  - enabled toggle, delay_hours, timezone, pipeline assignment
  - I/O config: input source (local dir path or PyobsArchive URL/token), output destination (local dir path or PyobsArchive URL/token)
  - recent periods list with start/stop/reset/restart buttons — periods themselves are always created by the trigger event (see "Scheduling"), never by picking a date here
- Site enable/disable controls whether the trigger event auto-dispatches for that site; disabled sites still get their `PENDING` row created every trigger event, just not auto-dispatched — the operator dispatches it manually with Start

### Step 4: Pipeline builder views

- `pipelines/` — list all named pipelines, create new pipeline form
- `pipelines/<name>/` — pipeline builder:
  - Step list with drag-and-drop reorder
  - "Add step" button opens step type selector (dropdown of known templates)
  - Per-step form fields rendered from template
  - Save pipeline updates PipelineStep entries
  - Delete step removes it from pipeline

Form generation references pyobs-core's processor classes directly. A helper function (`get_step_fields(step_class)`) uses `inspect.signature()` to extract parameters, types, defaults, and annotations at runtime.

```python
# step_fields.py
import inspect
from pyobs.object import get_class_from_string

def get_step_fields(step_class_path: str) -> list[dict]:
    """Introspect a processor class and return form field definitions.

    Example:
        get_step_fields("pyobs.images.processors.calibration.Calibration")
        → [{"name": "archive", "type": "JSON", "default": None},
           {"name": "max_cache_size", "type": "integer", "default": 20},
           {"name": "require_bias", "type": "boolean", "default": True},
           ...]
    """
    cls = get_class_from_string(step_class_path)
    sig = inspect.signature(cls.__init__)
    fields = []
    for name, param in sig.parameters.items():
        if name in ("self", "kwargs"):
            continue
        field_type = _map_type(param.annotation)
        default = param.default if param.default is not inspect.Parameter.empty else None
        fields.append({
            "name": name,
            "type": field_type,
            "default": default,
            "label": name.replace("_", " ").title(),
        })
    return fields
```

### Step 5: Celery + Redis integration

```python
# celery_app.py
from celery import Celery

app = Celery("pipeline", broker="redis://localhost:6379/0")
app.conf.broker_transport_options = {"visibility_timeout": 86400}

@app.task
def reduce_period(site_id, period_id):
    # Look up models, build config, load pipeline via create_object, run, write logs, update status
    pass
```

`visibility_timeout` (seconds before an un-acked task is redelivered) matches the current pipeline's setting — kept generous since a reduction run can take hours.

**Beat schedule — dynamic per site, not a static dict.** A static `beat_schedule` dict is fixed at process start and can't hold one entry per DB row that changes at runtime. Instead, use a custom `celery.beat.Scheduler` subclass that overrides `get_schedule()`/`tick()` to read **all** `Site` rows from the DB on each tick (not just enabled ones — `enabled` gates dispatch, not row creation) and compute each site's next trigger time via `get_next_turnover` (per `Site.trigger_type` — see below), comparing against `now()` to decide whether the trigger event has occurred. Sketch:

```python
class DbScheduler(Scheduler):
    def tick(self):
        for site in Site.objects.all():
            next_turnover = get_next_turnover(site)
            if due(next_turnover):
                period = ReductionPeriod.objects.create(site=site, date=..., status="PENDING")
                if site.enabled:
                    period.status = "QUEUED"
                    period.save()
                    reduce_period.delay(site.id, period.id)
        return super().tick()
```

Run with `celery -A pyobs_pipeline_web beat --scheduler pyobs_pipeline_web.scheduler.DbScheduler`. This also means enabling/disabling a site in the web UI takes effect on the next tick, with no Beat restart needed — flipping `enabled` off stops auto-dispatch immediately, but `PENDING` rows keep appearing on schedule for manual start.

### Reduction period turnover calculation

`get_next_turnover` computes the next Beat *trigger* time for a site (see "Reduction period turnover" above for the trigger-vs-boundary distinction):

```python
def get_next_turnover(site: Site) -> datetime:
    """Get the next Beat trigger time for a site, accounting for timezone.

    site.trigger_type == "sunrise": next sunrise (astroplan.Observer.sun_rise_time) + site.delay_hours.
    site.trigger_type == "sunset":  next sunset (astroplan.Observer.sun_set_time) + site.delay_hours.
    site.trigger_type == "fixed_time": next daily occurrence of site.trigger_time in the site's local timezone.
    """
```

At trigger time, a second helper derives the period *label* (the `ReductionPeriod.date`) as the local calendar date of the most recent occurrence of the opposite reference point before now: most recent sunset for a `sunrise` trigger (`Observer.sun_set_time(Time.now(), which="previous")`, matching the current pipeline), most recent sunrise for a `sunset` trigger, or the most recent prior occurrence of `trigger_time` for `fixed_time`.

### Step 6: ReductionPeriod management views

- `periods/` — list all reduction periods across sites, filter by site/status
- `periods/<id>/` — period detail: status badges, timing, log viewer, start/stop/reset/restart controls (see "Manual control" above)
- Start dispatches `reduce_period` for an existing `PENDING`/`FAILED`/`CANCELLED` ReductionPeriod row (rows themselves come only from the trigger event, see "Scheduling"); Stop/Reset update the row's status (and revoke the task, for Stop); Restart is Stop-or-Reset followed by Start on a freshly-created row for the same site+date

### Step 7: Log viewer

- ReductionPeriod detail page shows log output from DB
- Tail the `logs` TextField with auto-refresh while the reduction is running (poll every 2s)
- When completed, show the full log as static text
- No file path needed, logs are in the ReductionPeriod row

### Step 8: Dashboard

- Site status cards (enabled/disabled, last period result, next scheduled run)
- Input/output status per site (source type, destination type, archive health)
- Recent periods table (last 10, sortable by date, filterable by site/status)

### Step 9: Dockerfile + Compose + deploy docs

Dockerfile (single image, shared by web/worker/beat — each Compose service just overrides the command):
```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "gunicorn", "pyobs_pipeline_web.wsgi:application", "--bind", "0.0.0.0:8000"]
```

`docker-compose.yml`:
```yaml
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    restart: unless-stopped

  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data  # db.sqlite3 lives here, persisted outside the container
    environment:
      - ADMIN_USERNAME
      - ADMIN_PASSWORD_HASH
    depends_on:
      - redis
    restart: unless-stopped

  worker:
    build: .
    command: uv run celery -A pyobs_pipeline_web worker --loglevel=info --concurrency=4 --pool=prefork
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    restart: unless-stopped

  beat:
    build: .
    command: uv run celery -A pyobs_pipeline_web beat --loglevel=info --scheduler pyobs_pipeline_web.scheduler.DbScheduler
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  redis-data:
```

`--pool=prefork` on the worker matters — it's what makes `revoke(terminate=True)` (Step 6 cancel) actually work.

`web`, `worker`, and `beat` all mount the same host `./data` directory so they share one `db.sqlite3` file across containers — the WAL-mode + busy-timeout config from Step 1 is what makes that safe.

Deploy docs covering:
- `docker compose up -d --build` to bring up all four services; `docker compose logs -f worker` / `beat` / `web` for logs
- `db.sqlite3` location (`./data/`), backup approach (single file — periodic `cp`/rsync is sufficient at this scale)
- `.env` file for `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`
- Deploy/update procedure: `git pull`, `docker compose up -d --build`, `docker compose exec web python manage.py migrate`

### Step 10: Tests

- Model tests: Site, Pipeline, PipelineStep, ReductionPeriod creation and retrieval
- View tests: site list, pipeline builder, period list, start/stop/reset/restart flows (including start on a manual-only/disabled site)
- Celery task tests: reduce_period mock test, status updates, log writing
- Scheduler tests: Beat schedule generation from DB sites

## Consequences

- **Good:** One web interface replaces SSH + manual config editing for pipeline management
- **Good:** Named pipelines are reusable across sites — update the pipeline once, assign to multiple sites
- **Good:** Full pipeline builder with guided forms makes calibration steps, dark frames, flat fields, etc.
- **Neutral:** Redis as broker — same broker the current pipeline already uses, so no new infrastructure to stand up (unlike RabbitMQ, which was considered but would have added a service with no offsetting benefit at this scale).
- **Neutral:** SQLite instead of Postgres — one file, no separate DB service/volume/credentials, trivial backup (`cp`). Requires WAL mode + busy timeout because web/worker/beat containers share the file concurrently via a bind mount (see Step 1). Fine at this scale (few sites, one run/site/day) on a Linux Docker host; SQLite-over-bind-mount can be flaky on Docker Desktop for Mac/Windows, not a concern for a Linux server deploy.
- **Neutral:** Docker Compose for deployment — four services (web, worker, beat, redis) in one `docker-compose.yml`, with `depends_on` for startup ordering and `docker compose logs` for unified logs. Matches the Dockerfile-based pattern the current pipeline already uses; simpler to operate here than hand-written systemd units once Celery worker + beat are in the picture.
- **Neutral:** Logs in DB (TextField on `ReductionPeriod` row) — clean, no shared filesystem needed. But could grow the DB if logs are large. Could cap at reasonable size and keep last N lines if needed.
- **Neutral:** `input_config`/`output_config` on `SitePipeline` store PyobsArchive tokens as plaintext JSON in the DB. Acceptable for a single-user internal tool behind the existing cookie auth, but means DB access = credential access; no separate secrets store.
- **Neutral:** `PipelineStep.step_class` stores a dotted class path as a plain string with no validation against the installed pyobs-core version. Renaming or removing a processor class silently breaks any saved pipeline referencing it (fails at task-run time, not save time). No migration path for this is designed; acceptable to defer, but flag it as a known gap.

## Open questions

- Where does reduced data live once written? Should the web interface know about it for linking/browsing from the ReductionPeriod detail page, or is that outside scope?
- Beat's custom `DbScheduler` (Step 5) reads `Site` rows every tick — what tick interval, and does a missed tick (beat down at turnover) need catch-up logic? This now matters more than a missed dispatch alone: since `ReductionPeriod` rows are only ever created by the trigger event (never by an operator picking a date), a missed tick with no catch-up means that date's row never exists at all, and there's no supported UI path to create it after the fact. Worth deciding whether `tick()` should backfill any date between a site's last known row and today when it next runs.
- Is `step_class` validated at pipeline-save time (import the class, check it's a known processor base) to catch typos/renames early, or only discovered at run time?
- Single Redis broker, single Celery worker pool assumed — is there a need to isolate pipeline runs per site (e.g. one site's stuck task shouldn't block another site's queue), or is a shared pool acceptable given the low run frequency (once per site per day)?
- ~~Should `pyobs.utils.pipeline.Night` be renamed in pyobs-core?~~ Decided — see `specs/plans/night-archive-io-hardening.md`. Remaining question: this project's `PipelineStep.step_class`/`Pipeline.period_config` fields reference the dotted path directly, so nothing here should be built against `Night` once that plan lands — worth sequencing pipeline-web's Step 5 after it rather than building against the old name and migrating saved pipelines later.

## Implementation checklist

- [ ] Scaffold Django project with layout matching pyobs-web-admin
- [ ] Implement Django models (Site, Pipeline, PipelineStep, ReductionPeriod)
- [ ] Site management views (CRUD, enable/disable, scheduling control)
- [ ] Pipeline builder views (template registry, step forms, reorder, add/remove, save pipeline)
- [ ] Celery + Redis integration (reduce_period task, Beat trigger schedule)
- [ ] ReductionPeriod management views (list, detail, start/stop/reset/restart)
- [ ] Log viewer (read logs from DB, auto-refresh while running)
- [ ] Dashboard (site status cards, last period, next scheduled run, recent periods table)
- [ ] Dockerfile + docker-compose.yml (web, worker, beat, redis) + deploy documentation
- [ ] Tests (models, views, Celery tasks, scheduler)
- [ ] Update this doc's `Status:` to `implemented` once landed