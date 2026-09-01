# Plan: `instruments` app for pyobs-portal — static instrument capability data for the script builder

Status: proposed (pyobs/pyobs-portal#116)

Repos: pyobs-portal only. No pyobs-core changes — this models *declared* capability data in the
portal's own DB; it does not touch `ICamera`/`IBinning`/etc. or any live RPC path. Conceptually
adjacent to `specs/plans/2026-08-24-script-field-interface-annotations.md` and
pyobs-portal's `2026-08-24-module-ref-dropdowns.md` (module-name fields → interface-filtered
dropdowns), which resolve *which module* can fill a field; this plan resolves *what that module's
hardware can do* once picked, for planning-time script composition. Live module queries remain
the source of truth for execution — this is out of scope to reconcile against (per the issue).

## Problem

The script builder needs static instrument capability data (camera pixel size, binning options,
ROI limits, filter sets, etc.) to help compose scripts offline. Today that data only exists live,
queryable from a running module's interface (`ICamera`, `IBinning`, ...) — fine for execution, not
for planning when modules aren't reachable, or for validating a script before any module needs to
be up at all.

## Existing conventions this follows

- Module identity in the portal is a **string** (module name), never a DB-side `Module` row —
  confirmed in `2026-08-24-module-ref-dropdowns.md`: pyobs-web-admin's
  `GET /api/modules/classes/` is the live source of `{module_name: class_fqcn}`, and the portal
  has no local `Module` model to FK against. `Instrument.module_name` below follows the same
  pattern: a plain, portal-local string, not a foreign key to anything live.
- The portal's existing single `api` app (`pyobs_portal/api/`) splits by concern into
  `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, with DRF
  `@api_view`/`permission_classes` view functions and `path()` routing mounted under `api/` in
  the project's top-level `pyobs_portal/urls.py`. The new `instruments` app mirrors this file
  split exactly, as its own Django app (per the issue's own framing and this plan's scoping
  decision — kept isolated from the already-large `api` app rather than added to its
  `models.py`/`admin.py`).
- Settings precedent for optional integrations: flat `os.environ.get(..., default)` pairs,
  documented inline (`ARCHIVE_URL`/`ARCHIVE_TOKEN`, `WEBADMIN_URL`/`WEBADMIN_TOKEN`) — not needed
  here since there's no outbound integration, but the admin-permission group below follows the
  same "provision automatically, degrade to a no-op if already present" spirit via a data
  migration.

## Design

### 1. New app: `pyobs_portal/instruments/`

```
pyobs_portal/instruments/
├── __init__.py
├── apps.py            # InstrumentsConfig
├── models.py
├── admin.py
├── serializers.py
├── views.py            # read-only DRF viewsets
├── urls.py
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_instrument_config_group.py   # data migration, see §4
└── tests.py
```

Add `"pyobs_portal.instruments"` to `INSTALLED_APPS` (`settings.py`, alongside
`"pyobs_portal.api"`).

### 2. Models — one per capability type, FK'd to an `Instrument` identity row

```python
class Instrument(models.Model):
    module_name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
```

`module_name` is the same string that appears in scripts' module-name fields and in
`GET /api/modules/classes/` — deliberately not validated against either live source (the issue's
"reconciliation is out of scope" point).

```python
class CameraCapability(models.Model):
    instrument = models.OneToOneField(Instrument, on_delete=models.CASCADE, related_name="camera")
    pixel_size_um = models.FloatField(null=True, blank=True)
    sensor_width_px = models.PositiveIntegerField(null=True, blank=True)
    sensor_height_px = models.PositiveIntegerField(null=True, blank=True)
    roi_min_width_px = models.PositiveIntegerField(null=True, blank=True)
    roi_min_height_px = models.PositiveIntegerField(null=True, blank=True)
    roi_step_px = models.PositiveIntegerField(null=True, blank=True)
    exposure_time_min_s = models.FloatField(null=True, blank=True)
    exposure_time_max_s = models.FloatField(null=True, blank=True)
    image_types = models.JSONField(default=list, blank=True)  # e.g. ["object", "bias", "dark", "flat"]

class BinningOption(models.Model):
    camera = models.ForeignKey(CameraCapability, on_delete=models.CASCADE, related_name="binnings")
    x = models.PositiveSmallIntegerField()
    y = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("camera", "x", "y")

class FilterWheelCapability(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="filter_wheels")
    name = models.CharField(max_length=255, blank=True)  # for instruments with >1 wheel

class Filter(models.Model):
    filter_wheel = models.ForeignKey(FilterWheelCapability, on_delete=models.CASCADE, related_name="filters")
    name = models.CharField(max_length=255)
    position = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position", "name"]

class TelescopeCapability(models.Model):
    instrument = models.OneToOneField(Instrument, on_delete=models.CASCADE, related_name="telescope")
    aperture_mm = models.FloatField(null=True, blank=True)
    focal_length_mm = models.FloatField(null=True, blank=True)
    mount_type = models.CharField(max_length=255, blank=True)
    slew_rate_deg_per_s = models.FloatField(null=True, blank=True)
```

Repeating data (binnings, filters) gets its own FK'd model per the "one model per capability
type" decision; fixed-shape scalar specs (pixel size, ROI step, aperture) stay as fields on the
owning capability row rather than one-row-per-field tables. **This field list is a strawman** —
Tim should adjust names/units/precision against what the script builder and real hardware
actually need before implementation; the shape (Instrument ← 1:1/1:N → per-type capability
models) is the part this plan is committing to.

All numeric fields are `null=True, blank=True`: an instrument entry can be created before every
spec is known, and partial data (e.g. filters known, ROI limits not yet) must not block saving.

### 3. Admin (`admin.py`)

`ModelAdmin`/`TabularInline` for each model — `BinningOption` and `Filter` as inlines on
`CameraCapability`/`FilterWheelCapability` respectively, so an instrument's full capability set
is editable from one admin page per `Instrument`. Standard Django admin, no custom views.

### 4. Permission group: `instrument-config`, provisioned by data migration

`0002_instrument_config_group.py` (`RunPython`, with a no-op reverse):

```python
def create_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    group, _ = Group.objects.get_or_create(name="instrument-config")
    models = ["instrument", "cameracapability", "binningoption",
              "filterwheelcapability", "filter", "telescopecapability"]
    perms = Permission.objects.filter(
        content_type__app_label="instruments",
        content_type__model__in=models,
        codename__startswith="add_",
    ) | Permission.objects.filter(
        content_type__app_label="instruments",
        content_type__model__in=models,
        codename__startswith="change_",
    )
    group.permissions.add(*perms)
```

`get_or_create` makes this idempotent against re-runs/redeploys. Deliberately **add/change
only**, not `delete_`/`view_` — matches the issue's "add/change permissions scoped to just these
models, not blanket `is_staff`"; `view_*` isn't needed since Django admin grants view implicitly
to anyone with change, and delete is intentionally withheld (deleting instrument rows the script
builder references is a heavier action than this plan scopes for — a follow-up if actually
needed). A user still needs `is_staff=True` to reach `/admin/` at all; this group only scopes
*which* models they can touch once there, same as any other Django admin group.

### 5. Read-only API (`serializers.py`, `views.py`, `urls.py`)

Nested DRF serializers (`Instrument` → `camera`/`telescope`/`filter_wheels`, each with their
nested `binnings`/`filters`) so the script builder can fetch one instrument's full capability set
in a single request:

```python
class InstrumentSerializer(serializers.ModelSerializer):
    camera = CameraCapabilitySerializer(read_only=True)
    telescope = TelescopeCapabilitySerializer(read_only=True)
    filter_wheels = FilterWheelCapabilitySerializer(many=True, read_only=True)

    class Meta:
        model = Instrument
        fields = ["module_name", "display_name", "notes", "camera", "telescope", "filter_wheels"]
```

`ReadOnlyModelViewSet` (DRF), `@permission_classes([IsAuthenticated])` matching the existing
`api` app's views — no write path via this API; all writes go through Django admin per the
issue. Routed via `DefaultRouter` in `instruments/urls.py`, mounted in the project's top-level
`pyobs_portal/urls.py`:

```python
path("api/instruments/", include("pyobs_portal.instruments.urls")),
```

giving `GET /api/instruments/` (list) and `GET /api/instruments/<module_name>/` (detail, via
`lookup_field = "module_name"` on the viewset — the script builder looks instruments up by module
name, not numeric PK).

### 6. Tests (`instruments/tests.py`)

- Model-level: `unique_together` on `BinningOption`, cascade deletes (deleting an `Instrument`
  removes its capability rows).
- Migration test: `0002` creates the `instrument-config` group with exactly the expected
  add/change permissions and no others; re-running is idempotent (`get_or_create`).
- API: `GET /api/instruments/` and `/api/instruments/<module_name>/` — 401 unauthenticated, 200 +
  expected nested shape authenticated; a partially-filled instrument (e.g. no `telescope` row)
  serializes with `"telescope": null`, not a 500.
- Admin: a user in `instrument-config` (without `is_staff` superuser rights) can add/change an
  `Instrument` and its nested capabilities via the admin site; cannot delete one.

## Acceptance criteria

- `Instrument` + per-type capability models exist, editable via Django admin with inlines for
  repeating data (binnings, filters).
- A user in the `instrument-config` group (provisioned automatically via migration) can add/edit
  these models without needing broader `is_staff`/superuser rights.
- `GET /api/instruments/` and `/api/instruments/<module_name>/` return nested, read-only
  capability data for authenticated API clients.
- No live-module querying, no reconciliation against `ICamera`/`IBinning` state — this is
  planning-time data only, entered by hand.

## Out of scope

- Reconciliation/validation against live module state (issue's own follow-up note).
- Any change to pyobs-core interfaces or the `Annotated`-tag mechanism from
  `2026-08-24-script-field-interface-annotations.md` — unrelated; that resolves *which module*,
  this resolves *what it can do*.
- Wiring the script builder frontend to actually *use* this data (e.g. constraining exposure-time
  fields to an instrument's min/max, or filtering filter dropdowns to a chosen instrument's filter
  set) — this plan only ships the data model + admin + read API. Frontend consumption is a
  follow-up once the shape here is validated against real data entry.
- Bulk-import/seed tooling — first-run population is manual admin entry, per the issue.
