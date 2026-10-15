# Plan: typed configuration choices and shared display labels

Status: implemented; release and deployment pending.
Repos: pyobs-core, pyobs-gui, pyobs-portal.
Issue: [pyobs-gui#211](https://github.com/pyobs/pyobs-gui/issues/211).
Companion plans: [GUI](../../../pyobs-gui/specs/2026-10-14-typed-config-choices.md),
[portal](../../../pyobs-portal/specs/plans/2026-10-14-typed-config-choices.md).

## Findings verified against the local source

- `pyobs/utils/config_schema.py::_pydantic_field_schema` converts every `Literal` member
  to `str`; `ConfigFieldSchema.options` is declared `list[str]`. Existing
  `tests/utils/test_config_schema.py` explicitly expects numeric literals as strings.
- `pyobs-gui/pyobs_gui/structuredconfigwidget.py::_build_editor` separately uses
  `addItems`, `currentText`, and `setCurrentText` for enum fields. Plain integer and float
  fields already use numeric Qt widgets. This is specifically a finite-choice type-loss
  problem, not evidence that every numerical editor needs conversion.
- The portal does not use `ConfigSchema`: `pyobs_portal/api/schema.py::_schema_for`
  calls `model_json_schema()`. Its enum values start typed, but `buildEnumControl`
  in `schemaform.js` returns the string-valued DOM `select.value`.
- Configuration model providers own literal domains and display labels. Public
  consumers use published schema metadata rather than provider implementation details.
- XMPP `serializer.py` explicitly coerces values whose hint is `str`, including list
  items. Changing only the producer's `options` payload leaves old receivers coercing
  it back to strings. Old Qt `addItems` also expects strings.

## Proposed contract

Keep `type="enum"` and the legacy `options: list[str] | None`. Add an optional
`choices: list[ConfigChoice] | None = None` field, appended to the dataclass to
preserve existing positional parameters. `ConfigChoice` has `value: str | int | float |
bool` and `label: str`. Use finite JSON scalar numbers; object/array enum values and
nullable-choice redesign are outside this fix. A choice's value is its submitted
value, never its label. `choices=None` means a legacy producer; an empty list means
an empty domain, never permission to fall back to the first option.

Both schema builders should populate `choices` for supported enum domains even when
there is no label metadata. Use literal values as declared; unwrap Python Enum
members to their supported scalar `.value`. Retain string `options` as the legacy
projection. The existing dataclass builder already emits raw Enum values despite
its string annotation; normalize this legacy projection and test numeric Enum
support through the new field. Normalize Enum defaults to scalar values as well.
Do not infer numerical types by parsing strings: `"001"` is a valid string choice.

Define Pydantic field metadata `json_schema_extra["x-pyobs-choices"]` as a list of
`{"value": <typed scalar>, "label": <string>}` records. A record list avoids JSON
object-key stringification and collisions between `1`, `true`, and `"1"`. It is a
presentation extension, not a replacement for `Literal`/JSON Schema `enum` validation.
For dataclasses accept the same key in field metadata. Match against the actual
allowed domain, retain domain order, and use the raw value's display string when
no usable label exists. Ignore out-of-domain or malformed label records; ambiguous
conflicting records for one value fall back to raw display rather than choosing
an arbitrary label. Duplicate display labels are allowed.

Identity must distinguish bool from number and number from string. In Python use
explicit scalar-kind checks rather than bare equality (`True == 1`). Treat integer
and floating representations of the same JSON number as one numerical identity
for cross-language consistency; do not promise distinguishable choices `1` and
`1.0` in JSON Schema. Retain the declared Python value in the core/Qt payload.
Tests must include numeric/string pairs and bool/number pairs. Non-finite values
are unsupported. Portal's existing JavaScript safe-integer limitation is not a
reason to alter the small example integer codes; document rather than silently claim
arbitrary-size integer support.

## Implementation checklist

- [x] Add/export `ConfigChoice` and append the optional `choices` field in
      `pyobs/utils/config_schema.py`; preserve old construction and missing-field defaults.
- [x] Populate typed choices for Pydantic Literals and dataclass Enums; share metadata
      normalization and scalar identity logic. Supporting Pydantic Enum annotations is
      appropriate if the same helper makes it small; otherwise explicitly defer it.
- [x] Carry descriptions, levels, nested schemas, scalar defaults and units through
      unchanged; ensure typed choices recurse under nested `main`.
- [x] Update `specs/design/istructuredconfig.md` with the new capability field and
      metadata contract. No `IConfig` change, instrument-specific import, or label table in core.
- [x] Audit XMPP capability decode, LocalComm and RPC/state round trips with the new
      nested dataclass list. Existing generic codecs should suffice; only change them
      if a regression test demonstrates a real limitation.
- [ ] Record the minimum version for full typed-choice behavior in release notes;
      keep older installations usable through feature detection.

## Provider metadata dependency and ownership

Model providers publish the metadata independently; deployment is required for readable labels:

- [x] Publish `x-pyobs-choices` from the same provider metadata used for each field's
      literal domain. Implement this in the model provider, without importing pyobs-core.
      Do not duplicate tables in core, GUI, or portal.
- [x] For bitmask fields, retain every legal combination generated by the model provider. Atomic labels are not
      the full allowed domain. Initially label exact table matches and use the raw
      number for unlabeled combinations/zero; composed labels can be a separate change.
- [x] Test metadata survives `model_json_schema()` under `$defs` and is available via
      `model_fields` to core. Existing access-level and description metadata must remain.
- [ ] Deploy the updated model-provider version in both the module environment and portal's
      extension environment. Rebuild/restart schema-producing processes because schemas
      and capabilities are cached/static. Confirm the actual extension/dependency versions,
      including standalone GUI bundles, rather than assuming sibling source edits are installed.
- [ ] Validate deployed module and observation-script environments after release. Changes there
      should normally be dependency/integration checks, not a second label implementation.

## Regression verification

- [x] Extend `tests/utils/test_config_schema.py`: integer, float, bool, string and mixed
      literal domains, nested fields, defaults, raw fallback, Unicode labels, duplicate
      labels, malformed/partial metadata and bitmask-like domains. Assert exact Python
      types, not just equality. Include `1`, `True`, `"1"`, `"001"` as identity cases.
- [x] XMPP XML round-trip a full nested `ConfigSchema` with `choices`; assert each
      scalar type survives. Check old payload without `choices` on the new decoder and
      new payload on an old-shape dataclass decoder (unknown field ignored, string options
      retained). This is stronger than only `dataclasses.asdict()` coverage.
- [x] Exercise typed config RPC/state in `tests/comm/local/test_istructuredconfig.py`
      and an XML serializer fixture; verify the numeric choice remains an integer through validation.
- [ ] Run the affected pytest suites, repository lint/type checks, and a coordinated
      configuration apply/reset + portal script save/reload check using installed candidate versions.
      Live XMPP testing requires the repository's ejabberd setup; report if unavailable.

## Rollout and compatibility limits

1. Release core's additive schema support, and the model provider metadata independently.
2. Release GUI support with feature detection for `choices`; upgrade
   the core dependency on both GUI and module sides. Deploy the schema producer and
   the model provider metadata. Restart the module to republish capabilities.
3. Release portal's typed selector independently; readable labels appear after its
   model-provider environment is upgraded and schema caches/processes refreshed.

Old GUI + new producer remains structurally compatible through string `options`, but
still has the old numeric-submission bug. New GUI + old producer can render legacy
string choices, but cannot generally reconstruct erased numeric types; it must not
pretend this pairing fixes numeric Literals. A new GUI using an old core decoder can
lose `choices` entirely; feature detection treats that configuration as legacy mode.
No interface-version bump is proposed for this optional capability addition, subject
to the explicit old-shape codec tests above. Do not ship a breaking in-place
`options: list[scalar]` change as though it were backwards compatible.

Completion requires both typed payloads and readable choice labels on the supported
updated stack. Application code and automated checks are implemented. Release/deployment steps remain pending.

Implementation note: no unreleased dependency floor is invented. The GUI can start with older
core installations using legacy options; typed choices require updated producer and decoder code.

## Implementation verification (2026-10-15)

- Standalone core suite: 2,481 passed, 26 skipped, 102 integration/XMPP cases
  deselected, one expected failure. Ruff and Pyrefly pass.
- Nested typed-choice XML round trips and LocalComm state pass. An installed older
  core decoder ignores `choices` while retaining legacy options.
- Candidate provider metadata and both clients were exercised without operating
  hardware. Live module/XMPP deployment remains a release-environment check.
- Changed Python sources pass Black. The repository-wide check reports existing
  differences confined to the ignored `.claude/scratch` tree.
