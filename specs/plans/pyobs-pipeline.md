# Plan: pyobs-pipeline-web

Status: draft

Issue: #741

Repos: new repo `pyobs-pipeline-web`

## Problem

The existing pipeline (the private project at `/home/husser/astro/monet/pipeline`) runs data reductions unattended via Celery Beat with no way to monitor what is running, view logs, retrigger failed nights, or configure pipeline steps without SSH access. The config is YAML on disk, loaded via `pyobs.createObject`.

The goal is a dedicated web project that provides full pipeline management through a browser interface: monitoring status, viewing logs, retriggering nights, and configuring the pipeline with a guided builder.

**Standalone Django project**, same layout as pyobs-web-admin:
- Bootstrap 5 dark theme, sidebar navigation, card-based dashboard
- Template-based frontend, no SPA
- Single-user cookie auth (`ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH`)

**Celery + RabbitMQ** for async task execution and scheduling. Celery Beat triggers at sunrise per site with configurable delay.

**Logs in database** — one log per pipeline run stored in `ObservationPeriod.logs`, a `Text` field on the `ObservationPeriod.model. Web app reads from DB. No shared filesystem needed.

## Django models

| Model | Fields | Purpose |
|---|---|---|
| `Site` | name, lat, lon, timezone, enabled, delay_hours, period_start_time | Observatory location, schedule config |
| `Pipeline` | name, description | Named pipeline definition, reusable across sites |
| `PipelineStep` | pipeline (FK), order, step_class, config (JSON) | Ordered steps in a pipeline |
| `SitePipeline` | site (FK), pipeline (FK), input_path, output_path | Assigns pipeline to site, configures I/O |
| `ObservationPeriod` | site (FK), date, status, logs (TextField), started_at, finished_at, task_id | One row per reduction run |

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

Celery Beat with `solar` schedule (`celery.schedules.solar`), same as the current pipeline. Triggered at sunrise per site, with configurable delay (default 3 hours). Sites have an `enabled` toggle in the web interface to skip scheduling for a site.

The sunrise event creates a `ObservationPeriod` row (status `QUEUED`), then dispatches the Celery task.

## Celery task

```
reduce_observation_period(site_id, period_id):
  1. Look up site + assigned pipeline from DB
  2. Build config dict from PipelineStep entries. Add I/O config from SitePipeline.
  3. Load pipeline via pyobs.createObject
  4. Run pipeline. Read from input source (local dir or PyobsArchive). Write to output destination (local dir or PyobsArchive).
  5. Update ObservationPeriod: status = "COMPLETED"/"FAILED", logs (append to TextField), finished_at
```

On failure, the task catches the exception, writes it to the log, and updates the ObservationPeriod status to `"FAILED"` for easy retriggering. On success, status becomes `"COMPLETED"`.

## Pages

| Route | Description |
|---|---|
| `/` | Dashboard: site status cards, last night, next scheduled run, recent nights table |
| `/sites/` | Site list, add/edit/delete |
| `/sites/<name>/` | Site detail: pipeline assignment, recent nights, retrigger buttons |
| `/pipelines/` | Pipeline list, create new |
| `/pipelines/<name>/` | Pipeline builder: step list with reorder, form per step, add/remove steps |
| `/nights/` | All nights across sites, filter by site/status, retrigger failed/aborted |
| `/nights/<id>/` | ObservationPeriod detail: status, timing, log viewer that tail the log file |

## Log viewing

Worker appends log lines to the `logs` TextField on the `ObservationPeriod` row during execution. Web app reads from DB. ObservationPeriod detail page shows the full log with auto-refresh (poll every 2s) while the reduction is running. When completed, log is static text.

## Observation period turnover

The current pipeline calculates "last night" from sunset + delay. The new project follows the same approach but supports solar telescopes too. Each site has a `period_start_time` (local time) that determines when a new observation period begins. For night telescopes, this defaults to sunrise + delay_hours. For solar telescopes, it's a configurable local time. A helper function calculates the next turnover, accounting for timezone.

## Steps to implement

1. **Scaffold Django project** — Django + gunicorn, Bootstrap 5 template layout, single-user auth
2. **Django models** — `Site`, `Pipeline`, `PipelineStep`, `SitePipeline`, `ObservationPeriod`
3. **Site management views** — create/edit/delete sites, enable/disable scheduling
4. **Pipeline builder views** — template registry, form rendering per step type, reorder, add, remove, save
5. **Celery + RabbitMQ integration** — broker config, `reduce_night` task, Beat sunrise schedule
6. **ObservationPeriod management views** — list, detail, retrigger, cancel in-progress runs
7. **Log viewer** — stream log file from disk with auto-refresh
8. **Dashboard** — site status cards, last night results, next scheduled run, recent nights table
9. **Dockerfile + deploy docs** — Dockerfile for Django + Celery workers
10. **Tests** — model tests, view tests, Celery task tests

### Step 1: Scaffold Django project

Create the new repo with:
- Django project structure (`pyobs_pipeline_web/` package with `settings.py`, `urls.py`, etc.)
- `pyproject.toml` with dependencies (Django, gunicorn, Celery, RabbitMQ)
- `templates/base.html` — sidebar layout, Bootstrap 5 dark theme, matching pyobs-web-admin pattern
- `templates/` — login page, base template with sidebar
- Settings: `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `DEBUG`, `ALLOWED_HOSTS`

### Step 2: Django models

```python
class Site(models.Model):
    name = models.CharField(unique=True)
    lat = models.FloatField()
    lon = models.FloatField()
    timezone = models.CharField()
    enabled = models.BooleanField(default=True)
    delay_hours = models.FloatField(default=3.0)
    period_start_time = models.TimeField(help_text="Local time when new observation period starts")

class Pipeline(models.Model):
    name = models.CharField(unique=True)
    description = models.TextField(blank=True)

class PipelineStep(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    order = models.IntegerField()
    step_class = models.CharField()  # dotted path, e.g. "pyobs.images.pipeline.BiasCalibration"
    config = models.JSONField(default=dict)

class SitePipeline(models.Model):
    site = models.OneToOnefk(Site, on_delete=models.CASCADE)
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    input_type = models.CharField(choices=[("local", "Local directory"), ("archive", "PyobsArchive")], default="local")
    input_config = models.JSONField(default=dict)  # e.g. {"path": "/data/raw"} or {"class": "pyobs.utils.archive.PyobsArchive", "url": "...", "token": "..."}
    output_type = models.CharField(choices=[("local", "Local directory"), ("archive", "PyobsArchive")], default="local")
    output_config = models.JSONField(default=dict)  # e.g. {"path": "/data/reduced"} or {"class": "pyobs.utils.archive.PyobsArchive", "url": "...", "token": "..."}

class ObservationPeriod(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(choices=[("QUEUED", ...), ("RUNNING", ...), ("COMPLETED", ...), ("FAILED", ...)])
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
  - recent periods list with retrigger buttons
- Site enable/disable controls whether Celery Beat schedules for that site

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
from pyobs.utils.classes import get_class_from_string

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

### Step 5: Celery + RabbitMQ integration

```python
# celery_app.py
from celery import Celery
from django.conf import settings

app = Celery("pipeline", broker="amqp://guest:guest@rabbitmq//")
app.conf.broker_transport_options = {"visibility_timeout": 86400}

@app.task
def reduce_night(site_id, night_id):
    # Look up models, build config, load pipeline via create_object, run, write logs, update status
    pass
```

Beat schedule:
```python
app.conf.beat_schedule = {
    "site-sunrise": {
        'task': 'tasks.reduce_night',
        'schedule': solar('sunrise', site.lat, site.lon),  # dynamic, refreshed from DB
        'args': (site.id, None),  # night_id set at runtime
        'enabled': site.enabled,
    },
}
```

Beat schedule is dynamic — read from DB on startup, refresh periodically.

### Observation period turnover calculation

For night telescopes, the period starts at sunset (or sunrise + delay). For solar telescopes, it starts at a configurable local time. The `Site.period_start_time` defines the turnover. A helper function calculates the next turn over for any site, accounting for timezone:

```python
def get_next_turnover(site: Site) -> datetime:
    """Get the next observation period turnover for a site.

    For night telescopes: uses sunrise + site.delay_hours
    For solar telescopes: uses site.period_start_time
    """
    # Implementation uses astroplan.O sun_set_time/astroplan.sunrise_time + delay
    # Or reads from site.period_start_time
```

### Step 6: ObservationPeriod management views

- `nights/` — list all nights across sites, filter by site/status
- `nights/<id>/` — night detail: status badges, timing, log viewer, full-size retrigger button
- Retrigger creates a new ObservationPeriod row and dispatches `reduce_night`

### Step 7: Log viewer

- ObservationPeriod detail page shows log output from DB
- Tail the `logs` TextField with auto-refresh while the reduction is running (poll every 2s)
- When completed, show the full log as static text
- No file path needed, logs are in the ObservationPeriod row

### Step 8: Dashboard

- Site status cards (enabled/disabled, last period result, next scheduled run)
- Input/output status per site (source type, destination type, archive health)
- Recent periods table (last 10, sortable by date, filterable by site/status)

### Step 9: Dockerfile + deploy docs

Dockerfile:
```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "pyobs_pipeline_web.asgi:application", "--bind", "0.0.0.0:8000", "--websocket"]
```

Celery workers:
```bash
celery -A pyobs_pipeline_web worker --loglevel=info --concurrency=4
celery -A pyobs_pipeline_web beat --loglevel=info
```

Deploy docs covering:
- RabbitMQ setup
- Django settings (`ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, log dir, RabbitMQ URL)
- Docker Compose for local dev

### Step 10: Tests

- Model tests: Site, Pipeline, PipelineStep, ObservationPeriod creation and retrieval
- View tests: site list, pipeline builder, night list, retrigger flow
- Celery task tests: reduce_night mock test, status updates, log writing
- Scheduler tests: Beat schedule generation from DB sites

## Consequences

- **Good:** One web interface replaces SSH + manual config editing for pipeline management
- **Good:** Named pipelines are reusable across sites — update the pipeline once, assign to multiple sites
- **Good:** Full pipeline builder with guided forms makes calibration steps, dark frames, flat fields, etc.
- **Neutral:** Requires RabbitMQ as a new dependency. RabbitMQ is well-established, widely available, and the standard broker for Celery at scale.
- **Neutral:** Logs in DB (TextField on `ObservationPeriod` row) — clean, no shared filesystem needed. But could grow the DB if logs are large. Could cap at reasonable size and keep last N lines if needed.
- **Open question:** where does reduced data live? Should the web interface know about it for linking/browsing, or is that outside scope?

## Implementation checklist

- [ ] Scaffold Django project with layout matching pyobs-web-admin
- [ ] Implement Django models (Site, Pipeline, PipelineStep, ObservationPeriod)
- [ ] Site management views (CRUD, enable/disable, scheduling control)
- [ ] Pipeline builder views (template registry, step forms, reorder, add/remove, save pipeline)
- [ ] Celery + RabbitMQ integration (reduce_night task, Beat sunrise schedule)
- [ ] ObservationPeriod management views (list, detail, retrigger, cancel)
- [ ] Log viewer (read logs from DB, auto-refresh while running)
- [ ] Dashboard (site status cards, last night, next scheduled run, recent nights table)
- [ ] Dockerfile + deploy documentation
- [ ] Tests (models, views, Celery tasks, scheduler)
- [ ] Update this doc's `Status:` to `implemented` once landed